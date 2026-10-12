import asyncio
import logging
from datetime import UTC, date, datetime, timedelta

import brotli
import httpx
from cbr_ratings import KraCode, Prediction, RatingItem
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
from pydantic import BaseModel, TypeAdapter
from t_tech.invest import Bond as TInvestBond
from t_tech.invest import PortfolioPosition
from t_tech.invest.async_services import AsyncServices
from t_tech.invest.utils import money_to_decimal, quotation_to_decimal

logger = logging.getLogger(__name__)

BOND_RATINGS_URL = "https://raw.githubusercontent.com/grind-t/cbr-ratings-py/refs/heads/main/exports/bonds.json.br"
ISSUER_RATINGS_URL = "https://raw.githubusercontent.com/grind-t/cbr-ratings-py/refs/heads/main/exports/issuers.json.br"
IFRS_RATINGS_URL = "https://raw.githubusercontent.com/grind-t/e-disclosure-py/refs/heads/main/exports/ratings.json.br"

# screener thresholds, ytm in percent
MIN_MATURITY = timedelta(days=91)
MAX_MATURITY = timedelta(days=730)
RUB_MIN_YTM = 15.5
# floaters pay off only if rates stay high, so a longer one needs a higher yield
FLOATER_YTM_PER_DAY = 0.00275
MAX_ISSUER_INVESTMENT = 100_000
FOREIGN_CURRENCY_MIN_YTM = 7.0

# the SDK returns an epoch timestamp instead of a missing date
_EPOCH = datetime(1970, 1, 1, tzinfo=UTC)


class IfrsRating(BaseModel):
    value: int | None = None
    outlook: Prediction | None = None


# keyed by isin (bonds) or inn (issuers), then by agency
CbrRatings = dict[str, dict[KraCode, RatingItem]]
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

    def is_rub_candidate(self, issuer_investment: float) -> bool:
        if self.currency != "rub" or not self._fits_common_filters(RUB_MIN_YTM):
            return False
        assert self.ytm is not None
        assert self.maturity_date is not None
        if self.is_floater:
            days = (self.maturity_date - datetime.now(UTC).date()).days
            if self.ytm < RUB_MIN_YTM + days * FLOATER_YTM_PER_DAY:
                return False
        return issuer_investment < MAX_ISSUER_INVESTMENT

    def is_foreign_currency_candidate(self) -> bool:
        return self.currency != "rub" and self._fits_common_filters(
            FOREIGN_CURRENCY_MIN_YTM
        )

    def _fits_common_filters(self, min_ytm: float) -> bool:
        today = datetime.now(UTC).date()
        return (
            self.maturity_date is not None
            and today + MIN_MATURITY < self.maturity_date < today + MAX_MATURITY
            and self.ytm is not None
            and self.ytm >= min_ytm
            and not self.has_offer
            and self._has_acceptable_rating()
        )

    def _has_acceptable_rating(self) -> bool:
        # an ifrs or a t-invest rating alone is enough, but a poor ifrs one rules
        # the bond out even with good agency ratings
        has_rating = (
            any(
                _is_acceptable_rating(rating, prediction)
                for rating, prediction in (
                    (self.rating_akra, self.prediction_akra),
                    (self.rating_nkr, self.prediction_nkr),
                    (self.rating_expert_ra, self.prediction_expert_ra),
                    (self.rating_nra, self.prediction_nra),
                )
            )
            or (self.rating_t_invest is not None and self.rating_t_invest > 1)
            or self.rating_ifrs is not None
        )
        return has_rating and (
            self.rating_ifrs is None
            or _is_acceptable_rating(self.rating_ifrs, self.prediction_ifrs)
        )


def _is_acceptable_rating(rating: int | None, prediction: Prediction | None) -> bool:
    # a missing prediction counts as the best one each threshold allows
    if rating is None:
        return False
    return (
        rating > 18
        or (rating > 15 and prediction in (None, "STA", "POS"))
        or (rating > 14 and prediction in (None, "POS"))
    )


async def get_issuer_investments(
    *, t_invest_client: AsyncServices, account_id: str, bonds: list[ScreenerBond]
) -> dict[str, float]:
    portfolio = await t_invest_client.operations.get_portfolio(account_id=account_id)
    return build_issuer_investments(positions=portfolio.positions, bonds=bonds)


def build_issuer_investments(
    *, positions: list[PortfolioPosition], bonds: list[ScreenerBond]
) -> dict[str, float]:
    # sums prices as is, without converting currencies
    issuer_inn_by_isin = {bond.isin: bond.issuer_inn for bond in bonds}
    result: dict[str, float] = {}
    for pos in positions:
        if pos.instrument_type != "bond":
            continue
        # t-invest bond tickers are isins
        issuer_inn = issuer_inn_by_isin.get(pos.ticker)
        if issuer_inn is None:
            continue
        investment = quotation_to_decimal(pos.quantity) * money_to_decimal(
            pos.average_position_price
        )
        result[issuer_inn] = result.get(issuer_inn, 0.0) + float(investment)
    return result


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
        self,
        of_bond: dict[KraCode, RatingItem],
        of_issuer: dict[KraCode, RatingItem],
    ) -> None:
        self._of_bond = of_bond
        self._of_issuer = of_issuer

    def rating(self, kra: KraCode) -> int | None:
        record = self._record(kra)
        return record.rating_number if record else None

    def prediction(self, kra: KraCode) -> Prediction | None:
        record = self._record(kra)
        return record.prediction if record else None

    def _record(self, kra: KraCode) -> RatingItem | None:
        # the whole bond record wins over the issuer one, so a bond without
        # a prediction does not borrow the issuer's
        return self._of_bond.get(kra) or self._of_issuer.get(kra)


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
