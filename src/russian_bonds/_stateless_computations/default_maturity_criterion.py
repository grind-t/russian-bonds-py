from datetime import date, timedelta

from russian_bonds._entities.screener_bond import ScreenerBond

_MIN_MATURITY = timedelta(days=91)
_MAX_MATURITY = timedelta(days=730)


def default_maturity_criterion(bond: ScreenerBond, today: date) -> bool:
    return (
        bond.maturity_date is not None
        and today + _MIN_MATURITY < bond.maturity_date < today + _MAX_MATURITY
    )
