from datetime import date

from russian_bonds._entities.screener_bond import ScreenerBond
from russian_bonds._stateless_computations.default_agency_rating_criterion import (
    default_agency_rating_criterion,
)
from russian_bonds._stateless_computations.default_maturity_criterion import (
    default_maturity_criterion,
)

_MIN_YTM = 7.0  # percent


def is_foreign_currency_candidate(bond: ScreenerBond, today: date) -> bool:
    return (
        bond.currency != "rub"
        and default_maturity_criterion(bond, today)
        and bond.ytm is not None
        and bond.ytm >= _MIN_YTM
        and not bond.has_offer
        and default_agency_rating_criterion(bond)
    )
