import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime

import httpx
from t_tech.invest import OperationType
from t_tech.invest.async_services import AsyncServices

from ..account_bond_histories import get_account_bond_histories_from_operations
from .account_operations import (
    fetch_account_operations_from_t_invest,
    fetch_virtual_operations_from_t_invest,
)
from .payment_ratios import get_payment_ratios


@dataclass(frozen=True)
class BondCashFlow:
    ticker: str
    name: str
    description: str
    type: OperationType
    value: float
    face_unit: str
    date: datetime
    virtual: bool


async def get_account_bond_cash_flows(
    t_invest_client: AsyncServices,
    moex_client: httpx.AsyncClient,
    account_id: str,
    from_: datetime | None = None,
) -> list[BondCashFlow]:
    now = datetime.now(UTC)

    account_operations, virtual_operations = await asyncio.gather(
        fetch_account_operations_from_t_invest(
            t_invest_client, moex_client, account_id, from_
        ),
        fetch_virtual_operations_from_t_invest(t_invest_client, account_id, now),
    )

    histories = await get_account_bond_histories_from_operations(
        account_operations + virtual_operations, moex_client
    )

    cash_flows: list[BondCashFlow] = []
    for history in histories.values():
        operations = history.operations
        # only the bonds bought in the window are counted
        ratio_by_operation_id = get_payment_ratios(operations)
        cash_flows.extend(
            BondCashFlow(
                ticker=op.ticker,
                name=op.name,
                description=op.description,
                type=op.type,
                value=op.payment * ratio_by_operation_id[op.id],
                face_unit=history.bond.face_unit,
                date=op.date,
                virtual=op.virtual,
            )
            for op in operations
            if ratio_by_operation_id[op.id] != 0
        )
    return cash_flows
