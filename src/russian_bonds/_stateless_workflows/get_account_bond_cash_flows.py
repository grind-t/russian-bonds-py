import asyncio
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from itertools import chain

from moex import MoexBondAmortization
from t_tech.invest import OperationState, PortfolioPosition

from russian_bonds._entities.account_bond_history import AccountBondHistory
from russian_bonds._entities.account_operation import AccountOperation
from russian_bonds._entities.bond import Bond
from russian_bonds._entities.bond_cash_flow import BondCashFlow
from russian_bonds._entities.t_invest_operation import TInvestOperation
from russian_bonds._stateless_computations.group_operations_by_ticker import (
    group_operations_by_ticker,
)
from russian_bonds._stateless_computations.money_to_float import money_to_float
from russian_bonds._stateless_computations.quantity_by_payment import (
    quantity_by_payment,
)
from russian_bonds._stateless_computations.quantity_delta import BOND_REPAYMENT_FULL
from russian_bonds._stateless_computations.to_account_operation import (
    to_account_operation,
)
from russian_bonds._stateless_computations.to_bought_bond_cash_flows import (
    to_bought_bond_cash_flows,
)
from russian_bonds._stateless_computations.to_virtual_account_operation import (
    to_virtual_account_operation,
)

type _FetchBondAmortizations = Callable[[str], Awaitable[list[MoexBondAmortization]]]


async def get_account_bond_cash_flows(
    account_id: str,
    from_: datetime | None,
    *,
    fetch_t_invest_operations: Callable[
        [str, datetime | None], Awaitable[list[TInvestOperation]]
    ],
    fetch_portfolio_positions: Callable[[str], Awaitable[list[PortfolioPosition]]],
    fetch_bond_amortizations: _FetchBondAmortizations,
    fetch_bond: Callable[[str], Awaitable[Bond]],
) -> list[BondCashFlow]:
    t_invest_operations, positions = await asyncio.gather(
        fetch_t_invest_operations(account_id, from_),
        fetch_portfolio_positions(account_id),
    )
    account_operations = await _to_account_operations(
        t_invest_operations, fetch_bond_amortizations
    )
    now = datetime.now(UTC)
    virtual_operations = [
        to_virtual_account_operation(pos, now)
        for pos in positions
        if pos.instrument_type == "bond"
    ]
    by_ticker = group_operations_by_ticker(account_operations + virtual_operations)
    bonds = await asyncio.gather(*(fetch_bond(ticker) for ticker in by_ticker))
    histories = (
        AccountBondHistory(bond=bond, operations=ops)
        for bond, ops in zip(bonds, by_ticker.values(), strict=True)
    )
    return list(chain.from_iterable(to_bought_bond_cash_flows(h) for h in histories))


async def _to_account_operations(
    operations: list[TInvestOperation],
    fetch_bond_amortizations: _FetchBondAmortizations,
) -> list[AccountOperation]:
    # the API returns operations newest first
    executed_operations = [
        op
        for op in reversed(operations)
        if op.instrument_type == "bond"
        and op.state == OperationState.OPERATION_STATE_EXECUTED
    ]
    # sequential requests to spare moex
    for op in executed_operations:
        await _fill_missing_quantity(op, fetch_bond_amortizations)
    return [to_account_operation(op) for op in executed_operations]


async def _fill_missing_quantity(
    op: TInvestOperation, fetch_bond_amortizations: _FetchBondAmortizations
) -> None:
    if op.type != BOND_REPAYMENT_FULL or op.quantity_done > 0:
        return
    amortizations = await fetch_bond_amortizations(op.ticker)
    final_amortization_rub = amortizations[-1].value_rub if amortizations else None
    if final_amortization_rub is None:
        raise ValueError(f"No final amortization for {op.ticker}")
    # the payment is in rubles even for currency bonds
    op.quantity_done = quantity_by_payment(
        money_to_float(op.payment), final_amortization_rub
    )
