import pytest

from russian_bonds._stateless_computations.quantity_by_payment import (
    quantity_by_payment,
)


def test_quantity_by_payment_returns_whole_quantity():
    assert quantity_by_payment(5000, 1000) == 5


def test_quantity_by_payment_rejects_abnormal_quantity(subtests):
    cases = {"zero quantity": 0, "fractional quantity": 1500}
    for name, payment in cases.items():
        with (
            subtests.test(name),
            pytest.raises(ValueError, match="Abnormal full repayment quantity"),
        ):
            quantity_by_payment(payment, 1000)


def test_quantity_by_payment_tolerates_float_rounding_error():
    assert quantity_by_payment(0.3, 0.1) == 3
