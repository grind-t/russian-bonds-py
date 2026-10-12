import pytest
from t_tech.invest import OperationType

from russian_bonds._core.cash_flows.operation_quantity import (
    quantity_by_payment,
    quantity_delta,
)


def test_buy_adds_quantity():
    assert quantity_delta(OperationType.OPERATION_TYPE_BUY, 10) == 10


def test_sell_subtracts_quantity():
    assert quantity_delta(OperationType.OPERATION_TYPE_SELL, 10) == -10


def test_full_repayment_subtracts_quantity():
    assert quantity_delta(OperationType.OPERATION_TYPE_BOND_REPAYMENT_FULL, 10) == -10


def test_other_types_do_not_change_quantity():
    assert quantity_delta(OperationType.OPERATION_TYPE_COUPON, 10) == 0


def test_unknown_type_raises():
    with pytest.raises(ValueError, match="Unsupported operation type"):
        # transfer between accounts
        quantity_delta(OperationType.OPERATION_TYPE_TRANS_BS_BS, 10)


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
