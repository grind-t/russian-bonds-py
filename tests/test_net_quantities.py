from dataclasses import dataclass

from russian_bonds.operations.net_quantities import get_net_quantities_by_ticker


@dataclass
class Op:
    ticker: str
    type: int
    quantity_done: float


def test_sums_quantities_by_ticker():
    operations = [
        Op("A", 15, 10),
        Op("A", 23, 0),
        Op("A", 22, 10),
        Op("B", 15, 5),
    ]
    assert get_net_quantities_by_ticker(operations) == {"A": 0, "B": 5}
