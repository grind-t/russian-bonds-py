from datetime import timedelta

from factories import TODAY, agency, ifrs, screener_bond

from russian_bonds._stateless_computations.screening.default_rub_bullet_criterion import (
    default_rub_bullet_criterion,
)


def test_rub_bullet(subtests):
    cases = {
        "fits all conditions": ({}, True),
        "non-ruble currency": ({"currency": "usd"}, False),
        "has offer": ({"has_offer": True}, False),
        "has amortization": ({"has_amortization": True}, False),
        "no maturity date": ({"maturity_date": None}, False),
        "matures too soon": ({"maturity_date": TODAY + timedelta(days=91)}, False),
        "matures soon enough": ({"maturity_date": TODAY + timedelta(days=92)}, True),
        "matures late enough": ({"maturity_date": TODAY + timedelta(days=729)}, True),
        "matures too late": ({"maturity_date": TODAY + timedelta(days=730)}, False),
    }
    for name, (fields, expected) in cases.items():
        with subtests.test(name):
            bond = screener_bond(**fields)
            assert default_rub_bullet_criterion(bond, TODAY) is expected


def test_ratings(subtests):
    no_agency = {"agency_ratings": {}}
    cases = {
        "no rating": (no_agency, False),
        "high rating with stable prediction": (
            agency("AKRA", 18, "STA"),
            True,
        ),
        "high rating with negative prediction": (
            agency("AKRA", 18, "NEG"),
            False,
        ),
        "medium rating with positive prediction": (
            agency("AKRA", 16, "POS"),
            True,
        ),
        "medium rating under review": (
            agency("AKRA", 16, "DEV"),
            False,
        ),
        # a missing prediction counts as the best one the rating allows
        "low rating without prediction": (agency("AKRA", 15), True),
        "low rating with stable prediction": (
            agency("AKRA", 15, "STA"),
            False,
        ),
        "low rating with positive prediction": (
            agency("AKRA", 15, "POS"),
            True,
        ),
        "too low rating": (agency("AKRA", 14), False),
        "top nkr rating with negative prediction": (
            agency("NKR", 19, "NEG"),
            True,
        ),
        "expert ra rating": (agency("EXPERT_RA", 17), True),
        "nra rating": (agency("NRA", 16, "STA"), True),
        "acceptable t-invest rating": (
            no_agency | {"t_invest_rating": 2},
            True,
        ),
        "poor t-invest rating": (no_agency | {"t_invest_rating": 1}, False),
        # an ifrs rating alone is enough
        "acceptable ifrs rating alone": (no_agency | ifrs(15), True),
        "poor ifrs rating alone": (no_agency | ifrs(14), False),
        # a poor ifrs rating rules out good agency ratings
        "poor ifrs rating with agency rating": (
            ifrs(16, "NEG"),
            False,
        ),
        "top ifrs rating with negative prediction": (
            ifrs(19, "NEG"),
            True,
        ),
    }
    for name, (ratings, expected) in cases.items():
        with subtests.test(name):
            assert (
                default_rub_bullet_criterion(screener_bond(**ratings), TODAY)
                is expected
            )
