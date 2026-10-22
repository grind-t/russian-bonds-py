from datetime import date

from russian_bonds._entities.screener_bond import ScreenerBond
from russian_bonds._stateless_computations.screening.default_agency_rating_criterion import (
    default_agency_rating_criterion,
)
from russian_bonds._stateless_computations.screening.default_maturity_criterion import (
    default_maturity_criterion,
)
from russian_bonds._stateless_computations.screening.default_ytm_criterion import (
    default_ytm_criterion,
)


def default_rub_screener(bond: ScreenerBond, today: date) -> bool:
    return (
        bond.currency == "rub"
        and default_maturity_criterion(bond, today)
        and default_ytm_criterion(bond, today)
        and not bond.has_offer
        and default_agency_rating_criterion(bond)
    )
