from datetime import UTC, date, datetime

from cbr_ratings import KraCode, Prediction, RatingItem
from moex import MoexBond, MoexBondMarketData, MoexBondMarketYield, MoexSecurity
from t_tech.invest import Bond as TInvestBond
from t_tech.invest.utils import money_to_decimal

from russian_bonds._core.screener.ratings import CbrRatings, IfrsRatings
from russian_bonds._core.screener.screener_bond import ScreenerBond

# the SDK returns an epoch timestamp instead of a missing date
_EPOCH = datetime(1970, 1, 1, tzinfo=UTC)


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
) -> tuple[list[ScreenerBond], list[str]]:
    """Returns the bonds and the isins of the bonds missing from moex."""
    moex_security_by_isin = {v.isin: v for v in moex_securities}
    moex_bond_by_board = _by_board(moex_bonds)
    market_data_by_board = _by_board(moex_market_data)
    market_yield_by_board = _by_board(moex_market_yields)

    result: list[ScreenerBond] = []
    missing_moex: list[str] = []
    for bond in t_invest_bonds:
        if not bond.buy_available_flag or not bond.api_trade_available_flag:
            continue

        moex_security = moex_security_by_isin.get(bond.isin)
        if moex_security is None:
            is_spb_exchange = bond.class_code.startswith(("SPB", "PS"))
            if not is_spb_exchange:
                missing_moex.append(bond.isin)
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

    return result, missing_moex


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
