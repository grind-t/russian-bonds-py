from datetime import date

from russian_bonds._entities.screener_bond import ScreenerBond
from russian_bonds._stateless_computations.default_agency_rating_criterion import (
    default_agency_rating_criterion,
)
from russian_bonds._stateless_computations.default_maturity_criterion import (
    default_maturity_criterion,
)


def fits_common_screener_filters(
    bond: ScreenerBond, min_ytm: float, today: date
) -> bool:
    """Filters shared by the ruble and foreign currency screeners, ytm in percent."""
    return (
        default_maturity_criterion(bond, today)
        and bond.ytm is not None
        and bond.ytm >= min_ytm
        and not bond.has_offer
        and default_agency_rating_criterion(bond)
    )
