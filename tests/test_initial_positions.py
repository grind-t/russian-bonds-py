from dataclasses import dataclass

import pytest

from russian_bonds.operations.initial_positions import get_initial_positions


@dataclass
class Op:
    ticker: str
    type: int
    quantity_done: int


def test_returns_quantities_held_before_operations():
    operations = [
        Op("A", 15, 10),
        Op("A", 22, 10),
        Op("B", 15, 5),
        Op("B", 6, 8),
    ]
    assert get_initial_positions(operations) == {"A": 0, "B": 3}


def test_unclosed_position_raises():
    with pytest.raises(ValueError, match="Unclosed position for A"):
        get_initial_positions([Op("A", 15, 5)])
