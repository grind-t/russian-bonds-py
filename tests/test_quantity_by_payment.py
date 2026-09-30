import pytest

from russian_bonds.operations.quantity_by_payment import get_quantity_by_payment


def test_returns_whole_quantity():
    assert get_quantity_by_payment(5000, 1000) == 5


@pytest.mark.parametrize("payment", [0, -1000, 1500])
def test_rejects_abnormal_quantity(payment):
    with pytest.raises(ValueError):
        get_quantity_by_payment(payment, 1000)


def test_tolerates_float_rounding_error():
    assert get_quantity_by_payment(0.3, 0.1) == 3
