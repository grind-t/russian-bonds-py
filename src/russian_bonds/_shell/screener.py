import asyncio
import logging

import brotli
import httpx
from moex import (
    get_moex_bond_securities,
    get_moex_bonds,
    get_moex_bonds_market_data,
    get_moex_bonds_market_yield,
)
from pydantic import TypeAdapter
from t_tech.invest.async_services import AsyncServices

from russian_bonds._core.screener.build_screener_bonds import build_screener_bonds
from russian_bonds._core.screener.issuer_investments import build_issuer_investments
from russian_bonds._core.screener.ratings import CbrRatings, IfrsRatings
from russian_bonds._core.screener.screener_bond import ScreenerBond

_logger = logging.getLogger(__name__)

_BOND_RATINGS_URL = "https://raw.githubusercontent.com/grind-t/cbr-ratings-py/refs/heads/main/exports/bonds.json.br"
_ISSUER_RATINGS_URL = "https://raw.githubusercontent.com/grind-t/cbr-ratings-py/refs/heads/main/exports/issuers.json.br"
_IFRS_RATINGS_URL = "https://raw.githubusercontent.com/grind-t/e-disclosure-py/refs/heads/main/exports/ratings.json.br"


async def get_issuer_investments(
    *, t_invest_client: AsyncServices, account_id: str, bonds: list[ScreenerBond]
) -> dict[str, float]:
    portfolio = await t_invest_client.operations.get_portfolio(account_id=account_id)
    return build_issuer_investments(positions=portfolio.positions, bonds=bonds)


async def list_screener_bonds(
    *, t_invest_client: AsyncServices, http_client: httpx.AsyncClient
) -> list[ScreenerBond]:
    # a task group keeps result types that gather loses beyond six awaitables
    async with asyncio.TaskGroup() as tg:
        t_invest_bonds = tg.create_task(t_invest_client.instruments.bonds())
        moex_securities = tg.create_task(get_moex_bond_securities(client=http_client))
        moex_bonds = tg.create_task(get_moex_bonds(client=http_client))
        market_data = tg.create_task(get_moex_bonds_market_data(client=http_client))
        market_yields = tg.create_task(get_moex_bonds_market_yield(client=http_client))
        bond_ratings = tg.create_task(
            _fetch_brotli_json(_BOND_RATINGS_URL, CbrRatings, http_client)
        )
        issuer_ratings = tg.create_task(
            _fetch_brotli_json(_ISSUER_RATINGS_URL, CbrRatings, http_client)
        )
        ifrs_ratings = tg.create_task(
            _fetch_brotli_json(_IFRS_RATINGS_URL, IfrsRatings, http_client)
        )
    bonds, missing_moex = build_screener_bonds(
        t_invest_bonds=t_invest_bonds.result().instruments,
        moex_securities=moex_securities.result(),
        moex_bonds=moex_bonds.result(),
        moex_market_data=market_data.result(),
        moex_market_yields=market_yields.result(),
        bond_ratings=bond_ratings.result(),
        issuer_ratings=issuer_ratings.result(),
        ifrs_ratings=ifrs_ratings.result(),
    )
    for isin in missing_moex:
        _logger.warning("Missing moex data for bond %s", isin)
    return bonds


async def _fetch_brotli_json[T](
    url: str, type_: type[T], client: httpx.AsyncClient
) -> T:
    response = await client.get(url)
    response.raise_for_status()
    return TypeAdapter(type_).validate_json(brotli.decompress(response.content))
