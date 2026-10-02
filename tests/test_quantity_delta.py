import pytest

from russian_bonds.operations.quantity_delta import BOND_REPAYMENT_FULL, quantity_delta


def test_buy_adds_quantity():
    assert quantity_delta(15, 10) == 10


def test_sell_subtracts_quantity():
    assert quantity_delta(22, 10) == -10


def test_full_repayment_subtracts_quantity():
    assert quantity_delta(BOND_REPAYMENT_FULL, 10) == -10


def test_other_types_do_not_change_quantity():
    assert quantity_delta(23, 10) == 0  # coupon


def test_unknown_type_raises():
    with pytest.raises(ValueError):
        quantity_delta(58, 10)  # transfer between accounts
