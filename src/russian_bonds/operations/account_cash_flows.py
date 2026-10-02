import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime

import httpx
from moex import get_moex_bonds
from t_tech.invest import OperationType
from t_tech.invest.async_services import AsyncServices

from .last_amortization import get_last_amortization
from .normalized_operations import NormalizedOperations, get_normalized_operations
from .payment_ratios import get_payment_ratios
from .virtual_operations import get_virtual_operations


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


@dataclass(frozen=True)
class _Nominal:
    value: float
    unit: str


async def get_account_bond_cash_flows(
    t_invest_client: AsyncServices,
    moex_client: httpx.AsyncClient,
    account_id: str,
    from_: datetime | None = None,
) -> list[BondCashFlow]:
    now = datetime.now(UTC)

    (
        normalized_operations,
        virtual_operations,
        nominal_by_ticker,
    ) = await asyncio.gather(
        get_normalized_operations(t_invest_client, moex_client, account_id, from_),
        get_virtual_operations(t_invest_client, account_id, now),
        _get_nominal_by_ticker(moex_client),
    )

    operations = NormalizedOperations([*normalized_operations, *virtual_operations])

    for op in operations:
        if op.ticker in nominal_by_ticker:
            continue
        amortization = await get_last_amortization(op.ticker, client=moex_client)
        if amortization is None:
            raise ValueError(f"No final amortization for {op.ticker}")
        nominal_by_ticker[op.ticker] = _Nominal(
            amortization.facevalue, amortization.faceunit
        )

    # only the bonds bought in the window are counted
    ratio_by_operation_id = get_payment_ratios(operations.root)

    return [
        BondCashFlow(
            ticker=op.ticker,
            name=op.name,
            description=op.description,
            type=op.type,
            value=op.payment * ratio_by_operation_id[op.id],
            face_unit=nominal_by_ticker[op.ticker].unit,
            date=op.date,
            virtual=op.virtual,
        )
        for op in operations
        if ratio_by_operation_id[op.id] != 0
    ]


async def _get_nominal_by_ticker(moex_client: httpx.AsyncClient) -> dict[str, _Nominal]:
    bonds = await get_moex_bonds(primary_board=1, client=moex_client)
    return {bond.SECID: _Nominal(bond.FACEVALUE, bond.FACEUNIT) for bond in bonds}
