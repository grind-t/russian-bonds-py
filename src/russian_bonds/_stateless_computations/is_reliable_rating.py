from russian_bonds._entities.credit_rating import CreditRating


def is_reliable_rating(rating: CreditRating) -> bool:
    # a missing prediction counts as the best one each threshold allows
    if rating.value is None:
        return False
    return (
        rating.value > 18
        or (rating.value > 15 and rating.prediction in (None, "STA", "POS"))
        or (rating.value > 14 and rating.prediction in (None, "POS"))
    )
