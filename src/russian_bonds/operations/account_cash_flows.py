import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone

import httpx
from moex import get_moex_bonds
from t_tech.invest import OperationState
from t_tech.invest.async_services import AsyncServices
from t_tech.invest.utils import money_to_decimal, quotation_to_decimal

from ..account_bonds import get_account_bonds
from .account_operations import BondOperationItem, get_account_bond_operations
from .last_amortization import get_last_amortization
from .net_quantities import get_net_quantities_by_ticker
from .quantity_by_payment import get_quantity_by_payment
from .quantity_delta import BOND_REPAYMENT_FULL


@dataclass(frozen=True)
class BondCashFlow:
    ticker: str
    name: str
    description: str
    type: int
    value: float
    face_unit: str
    date: datetime
    virtual: bool


@dataclass
class _Operation:
    ticker: str
    name: str
    description: str
    type: int
    payment: float
    quantity_done: float
    date: datetime
    virtual: bool


@dataclass(frozen=True)
class _Nominal:
    value: float
    unit: str


OPERATION_TYPE_SELL = 22


async def get_account_bond_cash_flows(
    client: AsyncServices,
    account_id: str,
    from_: datetime | None = None,
    to: datetime | None = None,
) -> list[BondCashFlow]:
    now = datetime.now(timezone.utc)

    async with httpx.AsyncClient() as moex_client:
        executed_operations, virtual_operations, nominal_by_ticker = await asyncio.gather(
            _get_executed_operations(client, account_id, from_, to),
            _get_virtual_operations(client, account_id, now),
            _get_nominal_by_ticker(moex_client),
        )

        operations = [*executed_operations, *virtual_operations]

        repayment_operations = [op for op in operations if op.type == BOND_REPAYMENT_FULL]
        rest_operations = [op for op in operations if op.type != BOND_REPAYMENT_FULL]

        for op in repayment_operations:
            amortization = await get_last_amortization(op.ticker, client=moex_client)
            if amortization is None or amortization.value_rub is None:
                raise ValueError(f"No final amortization for {op.ticker}")
            nominal_by_ticker[op.ticker] = _Nominal(
                amortization.facevalue, amortization.faceunit
            )
            # full repayment comes with zero quantity, so derive it from the payment,
            # which is in rubles even for currency bonds
            op.quantity_done = get_quantity_by_payment(op.payment, amortization.value_rub)

        for op in rest_operations:
            if op.ticker in nominal_by_ticker:
                continue
            amortization = await get_last_amortization(op.ticker, client=moex_client)
            if amortization is None:
                raise ValueError(f"No final amortization for {op.ticker}")
            nominal_by_ticker[op.ticker] = _Nominal(
                amortization.facevalue, amortization.faceunit
            )

    # history always ends at zero (virtual sell or full repayment), so a nonzero sum
    # means the ticker was held before the operations window
    net_quantities = get_net_quantities_by_ticker(operations)

    return [
        BondCashFlow(
            ticker=op.ticker,
            name=op.name,
            description=op.description,
            type=op.type,
            value=op.payment,
            face_unit=nominal_by_ticker[op.ticker].unit,
            date=op.date,
            virtual=op.virtual,
        )
        for op in operations
        if net_quantities[op.ticker] == 0
    ]


async def _get_executed_operations(
    client: AsyncServices,
    account_id: str,
    from_: datetime | None,
    to: datetime | None,
) -> list[_Operation]:
    return [
        _to_operation(op)
        for op in await get_account_bond_operations(client, account_id, from_, to)
        if op.state == OperationState.OPERATION_STATE_EXECUTED
    ]


def _to_operation(op: BondOperationItem) -> _Operation:
    return _Operation(
        ticker=op.ticker,
        name=op.name,
        description=op.description,
        type=int(op.type),
        payment=float(money_to_decimal(op.payment)),
        quantity_done=op.quantity_done,
        date=op.date,
        virtual=False,
    )


async def _get_virtual_operations(
    client: AsyncServices, account_id: str, now: datetime
) -> list[_Operation]:
    operations = []
    for pos in await get_account_bonds(client, account_id):
        quantity = float(quotation_to_decimal(pos.quantity))
        current_price = float(money_to_decimal(pos.current_price))
        current_nkd = float(money_to_decimal(pos.current_nkd))
        operations.append(
            _Operation(
                ticker=pos.ticker,
                name="Продажа",
                description="Виртуальная продажа по рыночной цене",
                type=OPERATION_TYPE_SELL,
                payment=(current_price + current_nkd) * quantity,
                quantity_done=quantity,
                date=now,
                virtual=True,
            )
        )
    return operations


async def _get_nominal_by_ticker(moex_client: httpx.AsyncClient) -> dict[str, _Nominal]:
    bonds = await get_moex_bonds(primary_board=1, client=moex_client)
    return {bond.SECID: _Nominal(bond.FACEVALUE, bond.FACEUNIT) for bond in bonds}
