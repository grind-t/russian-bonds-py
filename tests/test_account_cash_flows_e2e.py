import os
from datetime import UTC, datetime, timedelta

import httpx
import pytest
from t_tech.invest import AsyncClient

from russian_bonds import Clients, get_account_bond_cash_flows

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.skipif(
        not os.environ.get("T_INVEST_READONLY_TOKEN")
        or not os.environ.get("T_INVEST_ACCOUNT_ID"),
        reason="T_INVEST_READONLY_TOKEN and T_INVEST_ACCOUNT_ID are required",
    ),
]


async def test_cash_flows_net_to_zero_per_ticker():
    from_ = datetime.now(UTC) - timedelta(days=365 * 2)
    async with (
        AsyncClient(os.environ["T_INVEST_READONLY_TOKEN"]) as t_invest,
        httpx.AsyncClient() as moex,
    ):
        rows = await get_account_bond_cash_flows(
            Clients(t_invest, moex), os.environ["T_INVEST_ACCOUNT_ID"], from_
        )
    assert rows
    assert all(row.ticker and row.face_unit for row in rows)
