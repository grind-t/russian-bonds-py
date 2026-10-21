from datetime import UTC, date, datetime

from moex import MoexBond, MoexBondMarketData, MoexBondMarketYield, MoexSecurity
from t_tech.invest import Bond as TInvestBond

from russian_bonds._entities.cbr_ratings import CbrRatings
from russian_bonds._entities.credit_rating import CreditRating
from russian_bonds._entities.ifrs_ratings import IfrsRatings
from russian_bonds._entities.screener_bond import ScreenerBond
from russian_bonds._stateless_computations.money_to_float import money_to_float

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
        # the whole bond record wins over the issuer one, so a bond without
        # a prediction does not borrow the issuer's
        agency_records = {
            **(issuer_ratings.get(issuer_inn, {}) if issuer_inn else {}),
            **bond_ratings.get(bond.isin, {}),
        }
        ifrs_rating = ifrs_ratings.get(issuer_inn) if issuer_inn else None

        nominal = bond.nominal
        has_nominal = bool(nominal.currency or nominal.units or nominal.nano)

        result.append(
            ScreenerBond(
                isin=bond.isin,
                name=bond.name,
                maturity_date=_t_invest_date(bond.maturity_date),
                ytm=ytm,
                last_price=_price(md.LAST if md else None, mb),
                best_offer=_price(md.OFFER if md else None, mb),
                t_invest_rating=3 - bond.risk_level if bond.risk_level >= 1 else None,
                agency_ratings={
                    kra: CreditRating(
                        value=record.rating_number, prediction=record.prediction
                    )
                    for kra, record in agency_records.items()
                },
                ifrs_rating=CreditRating(
                    value=ifrs_rating.value, prediction=ifrs_rating.outlook
                )
                if ifrs_rating
                else None,
                nominal=money_to_float(nominal) if has_nominal else None,
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


def _by_board[T: MoexBond | MoexBondMarketData | MoexBondMarketYield](
    rows: list[T],
) -> dict[tuple[str, str | None], T]:
    result: dict[tuple[str, str | None], T] = {}
    for row in rows:
        result.setdefault((row.SECID, row.BOARDID), row)  # first match, like find
    return result


def _price(percent: float | None, moex_bond: MoexBond | None) -> float | None:
    # moex quotes prices in percent of the current, possibly amortized, face value
    if percent is None or moex_bond is None:
        return None
    return percent * moex_bond.FACEVALUE / 100


def _t_invest_date(value: datetime | None) -> date | None:
    if value is None or value == _EPOCH:
        return None
    return value.date()
