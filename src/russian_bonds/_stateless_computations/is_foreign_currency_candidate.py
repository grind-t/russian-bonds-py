from datetime import date

from russian_bonds._entities.screener_bond import ScreenerBond
from russian_bonds._stateless_computations.fits_common_screener_filters import (
    fits_common_screener_filters,
)

_MIN_YTM = 7.0  # percent


def is_foreign_currency_candidate(bond: ScreenerBond, today: date) -> bool:
    return bond.currency != "rub" and fits_common_screener_filters(
        bond, _MIN_YTM, today
    )
