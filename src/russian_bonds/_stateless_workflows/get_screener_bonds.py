import asyncio
from collections.abc import Callable, Coroutine
from typing import Any

from cbr_ratings import KraCode, RatingItem
from moex import MoexBond, MoexBondMarketData, MoexBondMarketYield, MoexSecurity
from t_tech.invest import BondsResponse

from russian_bonds._entities.credit_rating import CreditRating
from russian_bonds._entities.screener_bond import ScreenerBond
from russian_bonds._stateless_computations.screening.build_screener_bonds import (
    build_screener_bonds,
)

# coroutines rather than awaitables, as task groups require
type _Fetch[T] = Callable[[], Coroutine[Any, Any, T]]


async def get_screener_bonds(
    *,
    fetch_t_invest_bonds: _Fetch[BondsResponse],
    fetch_moex_securities: _Fetch[list[MoexSecurity]],
    fetch_moex_bonds: _Fetch[list[MoexBond]],
    fetch_moex_market_data: _Fetch[list[MoexBondMarketData]],
    fetch_moex_market_yields: _Fetch[list[MoexBondMarketYield]],
    fetch_cbr_ratings_by_isin: _Fetch[dict[str, dict[KraCode, RatingItem]]],
    fetch_cbr_ratings_by_inn: _Fetch[dict[str, dict[KraCode, RatingItem]]],
    fetch_ifrs_rating_by_inn: _Fetch[dict[str, CreditRating]],
) -> list[ScreenerBond]:
    # a task group keeps result types that gather loses beyond six awaitables
    async with asyncio.TaskGroup() as tg:
        t_invest_bonds = tg.create_task(fetch_t_invest_bonds())
        moex_securities = tg.create_task(fetch_moex_securities())
        moex_bonds = tg.create_task(fetch_moex_bonds())
        market_data = tg.create_task(fetch_moex_market_data())
        market_yields = tg.create_task(fetch_moex_market_yields())
        cbr_ratings_by_isin = tg.create_task(fetch_cbr_ratings_by_isin())
        cbr_ratings_by_inn = tg.create_task(fetch_cbr_ratings_by_inn())
        ifrs_rating_by_inn = tg.create_task(fetch_ifrs_rating_by_inn())
    return build_screener_bonds(
        t_invest_bonds=t_invest_bonds.result().instruments,
        moex_securities=moex_securities.result(),
        moex_bonds=moex_bonds.result(),
        moex_market_data=market_data.result(),
        moex_market_yields=market_yields.result(),
        cbr_ratings_by_isin=cbr_ratings_by_isin.result(),
        cbr_ratings_by_inn=cbr_ratings_by_inn.result(),
        ifrs_rating_by_inn=ifrs_rating_by_inn.result(),
    )
