from datetime import date, timedelta

from cbr_ratings import Prediction
from pydantic import BaseModel

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
    # in the nominal currency, None without trades or quotes
    last_price: float | None
    best_offer: float | None
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
