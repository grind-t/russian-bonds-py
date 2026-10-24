from datetime import date

from russian_bonds._entities.screener_bond import ScreenerBond
from russian_bonds._stateless_computations.screening.default_rub_bullet_criterion import (
    default_rub_bullet_criterion,
)

# ytm in percent
_MIN_YTM = 15.0
# floaters pay off only if rates stay high, so a longer one needs a higher yield
_YTM_PER_DAY = 0.0022


def default_rub_floater_screener(bond: ScreenerBond, today: date) -> bool:
    if (
        not bond.is_floater
        or not default_rub_bullet_criterion(bond, today)
        or bond.maturity_date is None
        or bond.ytm is None
    ):
        return False
    days = (bond.maturity_date - today).days
    return bond.ytm >= _MIN_YTM + days * _YTM_PER_DAY
