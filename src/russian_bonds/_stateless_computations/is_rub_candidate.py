from datetime import date

from russian_bonds._entities.screener_bond import ScreenerBond
from russian_bonds._stateless_computations.fits_common_screener_filters import (
    fits_common_screener_filters,
)

# ytm in percent
_MIN_YTM = 15.0
# floaters pay off only if rates stay high, so a longer one needs a higher yield
_FLOATER_YTM_PER_DAY = 0.00275
_MAX_ISSUER_INVESTMENT = 100_000


def is_rub_candidate(bond: ScreenerBond, issuer_investment: float, today: date) -> bool:
    if bond.currency != "rub" or not fits_common_screener_filters(
        bond, _MIN_YTM, today
    ):
        return False
    assert bond.ytm is not None
    assert bond.maturity_date is not None
    if bond.is_floater:
        days = (bond.maturity_date - today).days
        if bond.ytm < _MIN_YTM + days * _FLOATER_YTM_PER_DAY:
            return False
    return issuer_investment < _MAX_ISSUER_INVESTMENT
