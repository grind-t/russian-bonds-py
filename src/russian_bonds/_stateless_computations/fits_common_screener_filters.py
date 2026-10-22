from datetime import date, timedelta

from russian_bonds._entities.screener_bond import ScreenerBond
from russian_bonds._stateless_computations.default_agency_rating_criterion import (
    default_agency_rating_criterion,
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
        and default_agency_rating_criterion(bond)
    )
