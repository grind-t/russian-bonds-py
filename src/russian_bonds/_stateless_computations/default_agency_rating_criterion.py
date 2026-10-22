from russian_bonds._entities.credit_rating import CreditRating
from russian_bonds._entities.screener_bond import ScreenerBond


def default_agency_rating_criterion(bond: ScreenerBond) -> bool:
    # an ifrs or a t-invest rating alone is enough, but a poor ifrs one rules
    # the bond out even with good agency ratings
    ifrs = bond.ifrs_rating
    has_ifrs = ifrs is not None and ifrs.value is not None
    has_rating = (
        any(_is_reliable_rating(rating) for rating in bond.agency_ratings.values())
        or (bond.t_invest_rating is not None and bond.t_invest_rating > 1)
        or has_ifrs
    )
    return has_rating and (ifrs is None or not has_ifrs or _is_reliable_rating(ifrs))


def _is_reliable_rating(rating: CreditRating) -> bool:
    # a missing prediction counts as the best one each threshold allows
    if rating.value is None:
        return False
    return (
        rating.value > 18
        or (rating.value > 15 and rating.prediction in (None, "STA", "POS"))
        or (rating.value > 14 and rating.prediction in (None, "POS"))
    )
