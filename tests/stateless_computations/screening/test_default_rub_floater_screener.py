from datetime import timedelta

from factories import TODAY, screener_bond

from russian_bonds._stateless_computations.screening.default_rub_floater_screener import (
    default_rub_floater_screener,
)


def test_rub_floater(subtests):
    floater = {"is_floater": True, "maturity_date": TODAY + timedelta(400)}
    cases = {
        # a floater maturing in 400 days needs 15 + 400 * 0.00275 = 16.1
        "ytm at minimum": (floater | {"ytm": 16.1}, True),
        "ytm below minimum": (floater | {"ytm": 16.0}, False),
        "no ytm": (floater | {"ytm": None}, False),
        "fixed coupon": (floater | {"is_floater": False, "ytm": 20.0}, False),
        "not a bullet": (floater | {"has_offer": True, "ytm": 20.0}, False),
    }
    for name, (fields, expected) in cases.items():
        with subtests.test(name):
            bond = screener_bond(**fields)
            assert default_rub_floater_screener(bond, TODAY) is expected
