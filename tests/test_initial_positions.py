from dataclasses import dataclass

import pytest
from t_tech.invest import OperationType

from russian_bonds.operations.initial_positions import get_initial_positions

BOND_REPAYMENT_FULL = OperationType.OPERATION_TYPE_BOND_REPAYMENT_FULL
BUY = OperationType.OPERATION_TYPE_BUY
SELL = OperationType.OPERATION_TYPE_SELL


@dataclass
class Op:
    ticker: str
    type: OperationType
    quantity: int


def test_returns_quantities_held_before_operations():
    operations = [
        Op("A", BUY, 10),
        Op("A", SELL, 10),
        Op("B", BUY, 5),
        Op("B", BOND_REPAYMENT_FULL, 8),
    ]
    assert get_initial_positions(operations) == {"A": 0, "B": 3}


def test_unclosed_position_raises():
    with pytest.raises(ValueError, match="Unclosed position for A"):
        get_initial_positions([Op("A", BUY, 5)])
