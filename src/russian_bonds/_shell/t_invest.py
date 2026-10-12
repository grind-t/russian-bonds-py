from datetime import UTC, datetime

import httpx
from moex import get_moex_bond_amortizations
from t_tech.invest import GetOperationsByCursorRequest, OperationState, _grpc_helpers
from t_tech.invest.async_services import AsyncServices
from t_tech.invest.grpc import operations_pb2
from t_tech.invest.utils import money_to_decimal

from russian_bonds._core.cash_flows.account_operation import AccountOperation
from russian_bonds._core.cash_flows.operation_quantity import (
    BOND_REPAYMENT_FULL,
    quantity_by_payment,
)
from russian_bonds._core.cash_flows.t_invest_operation import (
    TInvestOperation,
    to_virtual_account_operation,
)


async def fetch_account_operations(
    t_invest_client: AsyncServices,
    moex_client: httpx.AsyncClient,
    account_id: str,
    from_: datetime | None,
) -> list[AccountOperation]:
    operations = await _fetch_t_invest_operations(t_invest_client, account_id, from_)
    # the API returns operations newest first
    executed_operations = [
        op
        for op in reversed(operations)
        if op.instrument_type == "bond"
        and op.state == OperationState.OPERATION_STATE_EXECUTED
    ]
    # sequential requests to spare moex
    for op in executed_operations:
        await _fill_missing_quantity(op, moex_client)
    return [op.to_account_operation() for op in executed_operations]


async def _fill_missing_quantity(
    op: TInvestOperation, moex_client: httpx.AsyncClient
) -> None:
    if op.type != BOND_REPAYMENT_FULL or op.quantity_done > 0:
        return
    amortizations = await get_moex_bond_amortizations(op.ticker, client=moex_client)
    final_amortization_rub = amortizations[-1].value_rub if amortizations else None
    if final_amortization_rub is None:
        raise ValueError(f"No final amortization for {op.ticker}")
    # the payment is in rubles even for currency bonds
    op.quantity_done = quantity_by_payment(
        float(money_to_decimal(op.payment)), final_amortization_rub
    )


async def fetch_virtual_account_operations(
    client: AsyncServices, account_id: str
) -> list[AccountOperation]:
    now = datetime.now(UTC)
    portfolio = await client.operations.get_portfolio(account_id=account_id)
    return [
        to_virtual_account_operation(pos, now)
        for pos in portfolio.positions
        if pos.instrument_type == "bond"
    ]


async def _fetch_t_invest_operations(
    client: AsyncServices, account_id: str, from_: datetime | None
) -> list[TInvestOperation]:
    """All account operations, newest first."""
    items: list[TInvestOperation] = []
    cursor: str | None = None
    while True:
        # the stub is called directly to get raw items that still carry the ticker
        res = await client.operations.stub.GetOperationsByCursor(
            request=_grpc_helpers.dataclass_to_protobuf(
                GetOperationsByCursorRequest(
                    account_id=account_id,
                    from_=from_,
                    cursor=cursor,
                    limit=1000,  # API maximum
                ),
                operations_pb2.GetOperationsByCursorRequest(),
            ),
            metadata=client.operations.metadata,
        )
        items.extend(
            _grpc_helpers.protobuf_to_dataclass(raw, TInvestOperation)
            for raw in res.items
        )
        if not res.has_next:
            return items
        cursor = res.next_cursor
