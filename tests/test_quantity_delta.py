import pytest
from t_tech.invest import OperationType

from russian_bonds.operations.quantity_delta import quantity_delta


def test_buy_adds_quantity():
    assert quantity_delta(OperationType.OPERATION_TYPE_BUY, 10) == 10


def test_sell_subtracts_quantity():
    assert quantity_delta(OperationType.OPERATION_TYPE_SELL, 10) == -10


def test_full_repayment_subtracts_quantity():
    assert quantity_delta(OperationType.OPERATION_TYPE_BOND_REPAYMENT_FULL, 10) == -10


def test_other_types_do_not_change_quantity():
    assert quantity_delta(OperationType.OPERATION_TYPE_COUPON, 10) == 0


def test_unknown_type_raises():
    with pytest.raises(ValueError):
        # transfer between accounts
        quantity_delta(OperationType.OPERATION_TYPE_TRANS_BS_BS, 10)
