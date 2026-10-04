from dataclasses import dataclass

import pytest
from t_tech.invest import OperationType

from russian_bonds.operations.fifo_position import FifoPosition


@dataclass
class _Op:
    type: OperationType
    quantity_delta: int = 0


def _buy(quantity: int) -> _Op:
    return _Op(OperationType.OPERATION_TYPE_BUY, quantity)


def _sell(quantity: int) -> _Op:
    return _Op(OperationType.OPERATION_TYPE_SELL, -quantity)


COUPON = _Op(OperationType.OPERATION_TYPE_COUPON)


def test_buy_is_kept():
    position = FifoPosition(initial=10)
    assert position.kept_fraction(_buy(5)) == 1.0
    assert position == FifoPosition(initial=10, bought=5, bought_share=5 / 15)


def test_sell_consumes_initial_bonds_first():
    position = FifoPosition(initial=10, bought=5)
    assert position.kept_fraction(_sell(4)) == 0.0
    assert position.initial == 6
    assert position.bought == 5


def test_sell_across_initial_and_bought_bonds():
    position = FifoPosition(initial=10, bought=10)
    assert position.kept_fraction(_sell(15)) == 5 / 15
    assert position.initial == 0
    assert position.bought == 5


def test_sell_of_bought_bonds_is_kept():
    position = FifoPosition(initial=0, bought=10)
    assert position.kept_fraction(_sell(4)) == 1.0
    assert position.bought == 6


def test_payment_keeps_bought_share():
    position = FifoPosition(initial=10)
    position.kept_fraction(_buy(30))
    assert position.kept_fraction(COUPON) == 0.75


def test_payment_without_bought_bonds_is_dropped():
    position = FifoPosition(initial=10)
    assert position.kept_fraction(COUPON) == 0.0


def test_payment_does_not_change_position():
    position = FifoPosition(initial=10, bought=10, bought_share=0.5)
    position.kept_fraction(COUPON)
    assert position == FifoPosition(initial=10, bought=10, bought_share=0.5)


def test_bought_share_carries_over_after_close():
    position = FifoPosition(initial=10)
    position.kept_fraction(_buy(10))
    position.kept_fraction(_sell(20))
    assert position.initial == 0
    assert position.bought == 0
    assert position.kept_fraction(COUPON) == 0.5


def test_partial_repayment_keeps_bought_share():
    position = FifoPosition(initial=10, bought=10, bought_share=0.5)
    repayment = _Op(OperationType.OPERATION_TYPE_BOND_REPAYMENT)
    assert position.kept_fraction(repayment) == 0.5


def test_full_repayment_consumes_initial_bonds_first():
    position = FifoPosition(initial=10, bought=10)
    repayment = _Op(OperationType.OPERATION_TYPE_BOND_REPAYMENT_FULL, -20)
    assert position.kept_fraction(repayment) == 0.5
    assert position.initial == 0
    assert position.bought == 0


@pytest.mark.parametrize(
    "type_",
    [
        OperationType.OPERATION_TYPE_BROKER_FEE,
        OperationType.OPERATION_TYPE_INPUT_SECURITIES,
        OperationType.OPERATION_TYPE_OUTPUT_SECURITIES,
        OperationType.OPERATION_TYPE_BOND_TAX,
    ],
)
def test_unsupported_type_raises(type_: OperationType):
    position = FifoPosition(initial=10)
    with pytest.raises(ValueError, match="Unsupported operation type"):
        position.kept_fraction(_Op(type_))
