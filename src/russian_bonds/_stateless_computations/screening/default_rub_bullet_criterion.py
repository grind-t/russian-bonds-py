from datetime import date

from russian_bonds._entities.screener_bond import ScreenerBond
from russian_bonds._stateless_computations.screening.default_agency_rating_criterion import (
    default_agency_rating_criterion,
)
from russian_bonds._stateless_computations.screening.default_maturity_criterion import (
    default_maturity_criterion,
)


def default_rub_bullet_criterion(bond: ScreenerBond, today: date) -> bool:
    # a bullet bond repays the whole face value at maturity: no amortization,
    # no offer
    return (
        bond.currency == "rub"
        and default_maturity_criterion(bond, today)
        and not bond.has_amortization
        and not bond.has_offer
        and default_agency_rating_criterion(bond)
    )
