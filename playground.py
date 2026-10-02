import asyncio
import os
import pickle
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
from pyxirr import xirr
from t_tech.invest import AsyncClient

from russian_bonds import get_account_bond_cash_flows

CACHE_DIR = Path.cwd() / ".analytics"


async def cache[T](key: str, fn: Callable[[], Awaitable[T]]) -> T:
    path = CACHE_DIR / f"{key}.pkl"
    if path.exists():
        return pickle.loads(path.read_bytes())
    value = await fn()
    CACHE_DIR.mkdir(exist_ok=True)
    path.write_bytes(pickle.dumps(value))
    return value


async def fetch_cash_flows():
    from_ = datetime.now(UTC) - timedelta(days=365 * 2)
    async with (
        AsyncClient(os.environ["T_INVEST_READONLY_TOKEN"]) as t_invest_client,
        httpx.AsyncClient() as moex_client,
    ):
        return await get_account_bond_cash_flows(
            t_invest_client=t_invest_client,
            moex_client=moex_client,
            account_id=os.environ["T_INVEST_ACCOUNT_ID"],
            from_=from_,
        )


async def main():
    rows = await cache("t-invest-bond-cash-flows", fetch_cash_flows)

    print("XIRR:", xirr([row.date for row in rows], [row.value for row in rows]))

    for row in sorted(rows, key=lambda row: (row.ticker, row.date)):
        print(
            row.date.date(),
            row.ticker,
            row.type,
            round(row.value, 2),
            row.face_unit,
            row.virtual,
        )


asyncio.run(main())
