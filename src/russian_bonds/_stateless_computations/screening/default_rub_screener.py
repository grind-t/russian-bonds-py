from datetime import date

from russian_bonds._entities.screener_bond import ScreenerBond
from russian_bonds._stateless_computations.screening.default_agency_rating_criterion import (
    default_agency_rating_criterion,
)
from russian_bonds._stateless_computations.screening.default_maturity_criterion import (
    default_maturity_criterion,
)

# ytm in percent
_MIN_YTM = 15.0
# floaters pay off only if rates stay high, so a longer one needs a higher yield
_FLOATER_YTM_PER_DAY = 0.00275


def default_rub_screener(bond: ScreenerBond, today: date) -> bool:
    if (
        bond.currency != "rub"
        or not default_maturity_criterion(bond, today)
        or bond.ytm is None
        or bond.ytm < _MIN_YTM
        or bond.has_offer
        or not default_agency_rating_criterion(bond)
    ):
        return False
    assert bond.maturity_date is not None
    if not bond.is_floater:
        return True
    days = (bond.maturity_date - today).days
    return bond.ytm >= _MIN_YTM + days * _FLOATER_YTM_PER_DAY
