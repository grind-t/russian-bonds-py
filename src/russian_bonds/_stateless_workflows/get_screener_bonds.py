import asyncio
import logging
from collections.abc import Callable, Coroutine
from typing import Any

from moex import MoexBond, MoexBondMarketData, MoexBondMarketYield, MoexSecurity
from t_tech.invest import BondsResponse

from russian_bonds._entities.cbr_ratings import CbrRatings
from russian_bonds._entities.ifrs_ratings import IfrsRatings
from russian_bonds._entities.screener_bond import ScreenerBond
from russian_bonds._stateless_computations.build_screener_bonds import (
    build_screener_bonds,
)

_logger = logging.getLogger(__name__)

# coroutines rather than awaitables, as task groups require
type _Fetch[T] = Callable[[], Coroutine[Any, Any, T]]


async def get_screener_bonds(
    *,
    fetch_t_invest_bonds: _Fetch[BondsResponse],
    fetch_moex_securities: _Fetch[list[MoexSecurity]],
    fetch_moex_bonds: _Fetch[list[MoexBond]],
    fetch_moex_market_data: _Fetch[list[MoexBondMarketData]],
    fetch_moex_market_yields: _Fetch[list[MoexBondMarketYield]],
    fetch_bond_ratings: _Fetch[CbrRatings],
    fetch_issuer_ratings: _Fetch[CbrRatings],
    fetch_ifrs_ratings: _Fetch[IfrsRatings],
) -> list[ScreenerBond]:
    # a task group keeps result types that gather loses beyond six awaitables
    async with asyncio.TaskGroup() as tg:
        t_invest_bonds = tg.create_task(fetch_t_invest_bonds())
        moex_securities = tg.create_task(fetch_moex_securities())
        moex_bonds = tg.create_task(fetch_moex_bonds())
        market_data = tg.create_task(fetch_moex_market_data())
        market_yields = tg.create_task(fetch_moex_market_yields())
        bond_ratings = tg.create_task(fetch_bond_ratings())
        issuer_ratings = tg.create_task(fetch_issuer_ratings())
        ifrs_ratings = tg.create_task(fetch_ifrs_ratings())
    bonds, missing_moex_isins = build_screener_bonds(
        t_invest_bonds=t_invest_bonds.result().instruments,
        moex_securities=moex_securities.result(),
        moex_bonds=moex_bonds.result(),
        moex_market_data=market_data.result(),
        moex_market_yields=market_yields.result(),
        bond_ratings=bond_ratings.result(),
        issuer_ratings=issuer_ratings.result(),
        ifrs_ratings=ifrs_ratings.result(),
    )
    for isin in missing_moex_isins:
        _logger.warning("Missing moex data for bond %s", isin)
    return bonds
