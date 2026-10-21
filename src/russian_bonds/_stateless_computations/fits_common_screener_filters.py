from datetime import date, timedelta

from russian_bonds._entities.screener_bond import ScreenerBond
from russian_bonds._stateless_computations.is_reliable_rating import (
    is_reliable_rating,
)

_MIN_MATURITY = timedelta(days=91)
_MAX_MATURITY = timedelta(days=730)


def fits_common_screener_filters(
    bond: ScreenerBond, min_ytm: float, today: date
) -> bool:
    """Filters shared by the ruble and foreign currency screeners, ytm in percent."""
    return (
        bond.maturity_date is not None
        and today + _MIN_MATURITY < bond.maturity_date < today + _MAX_MATURITY
        and bond.ytm is not None
        and bond.ytm >= min_ytm
        and not bond.has_offer
        and _has_reliable_rating(bond)
    )


def _has_reliable_rating(bond: ScreenerBond) -> bool:
    # an ifrs or a t-invest rating alone is enough, but a poor ifrs one rules
    # the bond out even with good agency ratings
    ifrs = bond.ifrs_rating
    has_ifrs = ifrs is not None and ifrs.value is not None
    has_rating = (
        any(is_reliable_rating(rating) for rating in bond.agency_ratings.values())
        or (bond.t_invest_rating is not None and bond.t_invest_rating > 1)
        or has_ifrs
    )
    return has_rating and (ifrs is None or not has_ifrs or is_reliable_rating(ifrs))
