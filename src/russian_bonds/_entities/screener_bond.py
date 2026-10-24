from datetime import date, timedelta

from cbr_ratings import KraCode
from pydantic import BaseModel

from russian_bonds._entities.credit_rating import CreditRating


class ScreenerBond(BaseModel):
    isin: str
    name: str
    maturity_date: date | None
    ytm: float | None
    # over the ofz curve at the same duration, in the units of ytm;
    # None for floaters, whose coupons moex does not forecast
    g_spread: float | None
    # None for floaters
    duration: timedelta | None
    # in the face value currency, None without trades or quotes
    last_price: float | None
    best_ask_price: float | None
    t_invest_rating: int | None
    # only the agencies that rated the bond or its issuer
    agency_ratings: dict[KraCode, CreditRating]
    ifrs_rating: CreditRating | None
    face_value: float | None
    currency: str
    sector: str
    issuer_inn: str | None
    is_floater: bool
    has_amortization: bool
    has_offer: bool
    is_for_qualified_investors: bool
