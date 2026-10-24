from factories import TODAY, screener_bond

from russian_bonds._stateless_computations.screening.default_rub_fixed_screener import (
    default_rub_fixed_screener,
)


def test_rub_fixed(subtests):
    cases = {
        "fits all filters": ({}, True),
        "floater": ({"is_floater": True}, False),
        "not a bullet": ({"has_amortization": True}, False),
        "ytm at minimum": ({"ytm": 15.0}, True),
        "ytm below minimum": ({"ytm": 14.9}, False),
        "no ytm": ({"ytm": None}, False),
    }
    for name, (fields, expected) in cases.items():
        with subtests.test(name):
            bond = screener_bond(**fields)
            assert default_rub_fixed_screener(bond, TODAY) is expected
