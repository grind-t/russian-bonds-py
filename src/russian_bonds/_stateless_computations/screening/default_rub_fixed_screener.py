from datetime import date

from russian_bonds._entities.screener_bond import ScreenerBond
from russian_bonds._stateless_computations.screening.default_rub_bullet_criterion import (
    default_rub_bullet_criterion,
)

_MIN_YTM = 15.0  # percent


def default_rub_fixed_screener(bond: ScreenerBond, today: date) -> bool:
    return (
        not bond.is_floater
        and default_rub_bullet_criterion(bond, today)
        and bond.ytm is not None
        and bond.ytm >= _MIN_YTM
    )
