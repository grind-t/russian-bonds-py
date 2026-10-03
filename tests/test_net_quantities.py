from dataclasses import dataclass

from t_tech.invest import OperationType

from russian_bonds.operations.net_quantities import get_net_quantities_by_ticker

BUY = OperationType.OPERATION_TYPE_BUY
SELL = OperationType.OPERATION_TYPE_SELL
COUPON = OperationType.OPERATION_TYPE_COUPON


@dataclass
class Op:
    ticker: str
    type: OperationType
    quantity_delta: int


def test_sums_quantities_by_ticker():
    operations = [
        Op("A", BUY, 10),
        Op("A", COUPON, 0),
        Op("A", SELL, -10),
        Op("B", BUY, 5),
    ]
    assert get_net_quantities_by_ticker(operations) == {"A": 0, "B": 5}
