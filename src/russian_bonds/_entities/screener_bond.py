from datetime import date, timedelta

from cbr_ratings import KraCode
from pydantic import BaseModel

from russian_bonds._entities.credit_rating import CreditRating

# screener thresholds, ytm in percent
_MIN_MATURITY = timedelta(days=91)
_MAX_MATURITY = timedelta(days=730)
_RUB_MIN_YTM = 15.0
# floaters pay off only if rates stay high, so a longer one needs a higher yield
_FLOATER_YTM_PER_DAY = 0.00275
_MAX_ISSUER_INVESTMENT = 100_000
_FOREIGN_CURRENCY_MIN_YTM = 7.0


class ScreenerBond(BaseModel):
    isin: str
    name: str
    maturity_date: date | None
    ytm: float | None
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

    def is_rub_candidate(self, issuer_investment: float, today: date) -> bool:
        if self.currency != "rub" or not self._fits_common_filters(_RUB_MIN_YTM, today):
            return False
        assert self.ytm is not None
        assert self.maturity_date is not None
        if self.is_floater:
            days = (self.maturity_date - today).days
            if self.ytm < _RUB_MIN_YTM + days * _FLOATER_YTM_PER_DAY:
                return False
        return issuer_investment < _MAX_ISSUER_INVESTMENT

    def is_foreign_currency_candidate(self, today: date) -> bool:
        return self.currency != "rub" and self._fits_common_filters(
            _FOREIGN_CURRENCY_MIN_YTM, today
        )

    def _fits_common_filters(self, min_ytm: float, today: date) -> bool:
        return (
            self.maturity_date is not None
            and today + _MIN_MATURITY < self.maturity_date < today + _MAX_MATURITY
            and self.ytm is not None
            and self.ytm >= min_ytm
            and not self.has_offer
            and self._has_acceptable_rating()
        )

    def _has_acceptable_rating(self) -> bool:
        # an ifrs or a t-invest rating alone is enough, but a poor ifrs one rules
        # the bond out even with good agency ratings
        ifrs = self.ifrs_rating
        has_ifrs = ifrs is not None and ifrs.value is not None
        has_rating = (
            any(rating.is_acceptable() for rating in self.agency_ratings.values())
            or (self.t_invest_rating is not None and self.t_invest_rating > 1)
            or has_ifrs
        )
        return has_rating and (ifrs is None or not has_ifrs or ifrs.is_acceptable())
