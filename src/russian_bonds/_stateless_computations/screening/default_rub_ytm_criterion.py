from datetime import date

from russian_bonds._entities.screener_bond import ScreenerBond

# ytm in percent
_MIN_YTM = 15.0
# floaters pay off only if rates stay high, so a longer one needs a higher yield
_FLOATER_YTM_PER_DAY = 0.00275


def default_rub_ytm_criterion(bond: ScreenerBond, today: date) -> bool:
    if bond.ytm is None:
        return False
    if not bond.is_floater:
        return bond.ytm >= _MIN_YTM
    if bond.maturity_date is None:
        return False
    days = (bond.maturity_date - today).days
    return bond.ytm >= _MIN_YTM + days * _FLOATER_YTM_PER_DAY
