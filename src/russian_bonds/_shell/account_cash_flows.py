import asyncio
from datetime import datetime
from itertools import chain

import httpx
from t_tech.invest.async_services import AsyncServices

from russian_bonds._core.cash_flows.account_bond_history import AccountBondHistory
from russian_bonds._core.cash_flows.account_operation import group_operations_by_ticker
from russian_bonds._core.cash_flows.bond_cash_flow import BondCashFlow
from russian_bonds._shell.moex import fetch_bond
from russian_bonds._shell.t_invest import (
    fetch_account_operations,
    fetch_virtual_account_operations,
)


async def get_account_bond_cash_flows(
    t_invest_client: AsyncServices,
    moex_client: httpx.AsyncClient,
    account_id: str,
    from_: datetime | None = None,
) -> list[BondCashFlow]:
    account_operations, virtual_operations = await asyncio.gather(
        fetch_account_operations(t_invest_client, moex_client, account_id, from_),
        fetch_virtual_account_operations(t_invest_client, account_id),
    )
    operations = account_operations + virtual_operations
    by_ticker = group_operations_by_ticker(operations)
    bonds = await asyncio.gather(
        *(fetch_bond(ticker, moex_client) for ticker in by_ticker)
    )
    histories = (
        AccountBondHistory(bond=bond, operations=ops)
        for bond, ops in zip(bonds, by_ticker.values(), strict=True)
    )
    return list(chain.from_iterable(h.to_cash_flows() for h in histories))
