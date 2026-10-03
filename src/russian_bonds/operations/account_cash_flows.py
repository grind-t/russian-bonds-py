import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime

import httpx
from moex import get_moex_bonds, get_moex_security_description
from t_tech.invest import OperationType
from t_tech.invest.async_services import AsyncServices
from toolkit.boolean import ensure

from .account_operation_groups import group_account_operations_by_ticker
from .account_operations import fetch_account_operations_from_t_invest
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
        account_operations,
        virtual_operations,
        nominal_by_ticker,
    ) = await asyncio.gather(
        fetch_account_operations_from_t_invest(
            t_invest_client, moex_client, account_id, from_
        ),
        get_virtual_operations(t_invest_client, account_id, now),
        _get_nominal_by_ticker(moex_client),
    )

    groups = group_account_operations_by_ticker(account_operations + virtual_operations)

    for ticker in groups:
        if ticker in nominal_by_ticker:
            continue
        description = await get_moex_security_description(ticker, client=moex_client)
        nominal_by_ticker[ticker] = _Nominal(
            ensure(description.FACEVALUE, f"No face value for {ticker}"),
            ensure(description.FACEUNIT, f"No face unit for {ticker}"),
        )

    cash_flows: list[BondCashFlow] = []
    for ticker, group in groups.items():
        # only the bonds bought in the window are counted
        ratio_by_operation_id = get_payment_ratios(group.operations)
        nominal = nominal_by_ticker[ticker]
        cash_flows.extend(
            BondCashFlow(
                ticker=op.ticker,
                name=op.name,
                description=op.description,
                type=op.type,
                value=op.payment * ratio_by_operation_id[op.id],
                face_unit=nominal.unit,
                date=op.date,
                virtual=op.virtual,
            )
            for op in group.operations
            if ratio_by_operation_id[op.id] != 0
        )
    return cash_flows


async def _get_nominal_by_ticker(moex_client: httpx.AsyncClient) -> dict[str, _Nominal]:
    bonds = await get_moex_bonds(primary_board=1, client=moex_client)
    return {bond.SECID: _Nominal(bond.FACEVALUE, bond.FACEUNIT) for bond in bonds}
