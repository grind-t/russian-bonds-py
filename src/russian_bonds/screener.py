import asyncio
import logging
from datetime import UTC, date, datetime

import brotli
import httpx
from moex import (
    MoexBond,
    MoexBondMarketData,
    MoexBondMarketYield,
    MoexSecurity,
    get_moex_bond_securities,
    get_moex_bonds,
    get_moex_bonds_market_data,
    get_moex_bonds_market_yield,
)
from pydantic import BaseModel, Field, TypeAdapter
from t_tech.invest import Bond as TInvestBond
from t_tech.invest.async_services import AsyncServices
from t_tech.invest.utils import money_to_decimal

from .cbr_ratings import Kra, Prediction, convert_prediction, rating_value_to_number

logger = logging.getLogger(__name__)

BOND_RATINGS_URL = "https://raw.githubusercontent.com/grind-t/cbr-ratings/refs/heads/main/exports/bonds.json.br"
ISSUER_RATINGS_URL = "https://raw.githubusercontent.com/grind-t/cbr-ratings/refs/heads/main/exports/issuers.json.br"
IFRS_RATINGS_URL = "https://raw.githubusercontent.com/grind-t/e-disclosure-py/refs/heads/main/exports/ratings.json.br"

# the SDK returns an epoch timestamp instead of a missing date
_EPOCH = datetime(1970, 1, 1, tzinfo=UTC)


class CbrRating(BaseModel):
    rating_value: str = Field(alias="ratingValue")
    prediction: str


class IfrsRating(BaseModel):
    value: int | None = None
    outlook: Prediction | None = None


# keyed by isin (bonds) or inn (issuers), then by agency
CbrRatings = dict[str, dict[str, CbrRating]]
IfrsRatings = dict[str, IfrsRating]  # keyed by inn


class ScreenerBond(BaseModel):
    isin: str
    name: str
    maturity_date: date | None
    ytm: float | None
    rating_t_invest: int | None
    rating_akra: int | None
    rating_nkr: int | None
    rating_expert_ra: int | None
    rating_nra: int | None
    rating_ifrs: int | None
    prediction_akra: Prediction | None
    prediction_nkr: Prediction | None
    prediction_expert_ra: Prediction | None
    prediction_nra: Prediction | None
    prediction_ifrs: Prediction | None
    nominal: float | None
    currency: str
    sector: str
    issuer_inn: str | None
    is_floater: bool
    has_amortization: bool
    has_offer: bool
    for_qual: bool


async def list_screener_bonds(
    *, t_invest_client: AsyncServices, http_client: httpx.AsyncClient
) -> list[ScreenerBond]:
    # a task group keeps result types that gather loses beyond six awaitables
    async with asyncio.TaskGroup() as tg:
        bonds = tg.create_task(t_invest_client.instruments.bonds())
        moex_securities = tg.create_task(get_moex_bond_securities(client=http_client))
        moex_bonds = tg.create_task(get_moex_bonds(client=http_client))
        market_data = tg.create_task(get_moex_bonds_market_data(client=http_client))
        market_yields = tg.create_task(get_moex_bonds_market_yield(client=http_client))
        bond_ratings = tg.create_task(
            _fetch_brotli_json(BOND_RATINGS_URL, CbrRatings, http_client)
        )
        issuer_ratings = tg.create_task(
            _fetch_brotli_json(ISSUER_RATINGS_URL, CbrRatings, http_client)
        )
        ifrs_ratings = tg.create_task(
            _fetch_brotli_json(IFRS_RATINGS_URL, IfrsRatings, http_client)
        )
    return build_screener_bonds(
        t_invest_bonds=bonds.result().instruments,
        moex_securities=moex_securities.result(),
        moex_bonds=moex_bonds.result(),
        moex_market_data=market_data.result(),
        moex_market_yields=market_yields.result(),
        bond_ratings=bond_ratings.result(),
        issuer_ratings=issuer_ratings.result(),
        ifrs_ratings=ifrs_ratings.result(),
    )


async def _fetch_brotli_json[T](
    url: str, type_: type[T], client: httpx.AsyncClient
) -> T:
    response = await client.get(url)
    response.raise_for_status()
    return TypeAdapter(type_).validate_json(brotli.decompress(response.content))


def build_screener_bonds(
    *,
    t_invest_bonds: list[TInvestBond],
    moex_securities: list[MoexSecurity],
    moex_bonds: list[MoexBond],
    moex_market_data: list[MoexBondMarketData],
    moex_market_yields: list[MoexBondMarketYield],
    bond_ratings: CbrRatings,
    issuer_ratings: CbrRatings,
    ifrs_ratings: IfrsRatings,
) -> list[ScreenerBond]:
    moex_security_by_isin = {v.isin: v for v in moex_securities}
    moex_bond_by_board = _by_board(moex_bonds)
    market_data_by_board = _by_board(moex_market_data)
    market_yield_by_board = _by_board(moex_market_yields)

    result: list[ScreenerBond] = []
    for bond in t_invest_bonds:
        if not bond.buy_available_flag or not bond.api_trade_available_flag:
            continue

        moex_security = moex_security_by_isin.get(bond.isin)
        if moex_security is None:
            is_spb_exchange = bond.class_code.startswith(("SPB", "PS"))
            if not is_spb_exchange:
                logger.warning("Missing moex data for bond %s", bond.isin)
            continue

        key = (moex_security.secid, moex_security.primary_boardid)
        moex_bond = moex_bond_by_board.get(key)
        market_data = market_data_by_board.get(key)
        market_yield = market_yield_by_board.get(key)

        is_ofz = moex_security.type == "ofz_bond"
        is_floater = bond.floating_coupon_flag
        has_offer = (
            bool(moex_bond and moex_bond.CALLOPTIONDATE)
            or bool(moex_bond and moex_bond.PUTOPTIONDATE)
            or _t_invest_date(bond.call_date) is not None
        )
        md, my, mb = market_data, market_yield, moex_bond
        # `or` chain mirrors the TS version, so a zero yield falls through
        ytm = (
            (md.YIELDTOOFFER if md and has_offer else None)
            or (my.EFFECTIVEYIELD if my and is_ofz and is_floater else None)
            or (md.YIELD if md else None)
            or (md.YIELDATWAPRICE if md else None)
            or (mb.YIELDATPREVWAPRICE if mb else None)
            or None
        )

        issuer_inn = moex_security.emitent_inn
        ratings = _KraRatings(
            bond_ratings.get(bond.isin, {}),
            issuer_ratings.get(issuer_inn, {}) if issuer_inn else {},
        )
        ifrs_rating = ifrs_ratings.get(issuer_inn) if issuer_inn else None

        nominal = bond.nominal
        has_nominal = bool(nominal.currency or nominal.units or nominal.nano)

        result.append(
            ScreenerBond(
                isin=bond.isin,
                name=bond.name,
                maturity_date=_t_invest_date(bond.maturity_date),
                ytm=ytm,
                rating_t_invest=3 - bond.risk_level if bond.risk_level >= 1 else None,
                rating_akra=ratings.rating("AKRA"),
                rating_nkr=ratings.rating("NKR"),
                rating_expert_ra=ratings.rating("EXPERT_RA"),
                rating_nra=ratings.rating("NRA"),
                rating_ifrs=ifrs_rating.value if ifrs_rating else None,
                prediction_akra=ratings.prediction("AKRA"),
                prediction_nkr=ratings.prediction("NKR"),
                prediction_expert_ra=ratings.prediction("EXPERT_RA"),
                prediction_nra=ratings.prediction("NRA"),
                prediction_ifrs=ifrs_rating.outlook if ifrs_rating else None,
                nominal=float(money_to_decimal(nominal)) if has_nominal else None,
                currency=nominal.currency if has_nominal else bond.currency,
                sector=bond.sector,
                issuer_inn=issuer_inn,
                is_floater=is_floater,
                has_amortization=bond.amortization_flag,
                has_offer=has_offer,
                for_qual=bond.for_qual_investor_flag,
            )
        )

    return result


class _KraRatings:
    def __init__(
        self, of_bond: dict[str, CbrRating], of_issuer: dict[str, CbrRating]
    ) -> None:
        self._of_bond = of_bond
        self._of_issuer = of_issuer

    def rating(self, kra: Kra) -> int | None:
        rating = self._field(kra, "rating_value")
        return rating_value_to_number(rating) if rating else None

    def prediction(self, kra: Kra) -> Prediction | None:
        # a bond prediction like "NA" wins over the issuer one, as in the TS version
        return convert_prediction(self._field(kra, "prediction"))

    def _field(self, kra: Kra, name: str) -> str | None:
        bond_rating = self._of_bond.get(kra)
        issuer_rating = self._of_issuer.get(kra)
        return (getattr(bond_rating, name) if bond_rating else None) or (
            getattr(issuer_rating, name) if issuer_rating else None
        )


def _by_board[T: MoexBond | MoexBondMarketData | MoexBondMarketYield](
    rows: list[T],
) -> dict[tuple[str, str | None], T]:
    result: dict[tuple[str, str | None], T] = {}
    for row in rows:
        result.setdefault((row.SECID, row.BOARDID), row)  # first match, like find
    return result


def _t_invest_date(value: datetime | None) -> date | None:
    if value is None or value == _EPOCH:
        return None
    return value.date()
