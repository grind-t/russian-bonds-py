from factories import account_operation
from t_tech.invest import OperationType

from russian_bonds._stateless_computations.group_operations_by_ticker import (
    group_operations_by_ticker,
)


def test_groups_operations_by_ticker():
    a1 = account_operation(id="a1", ticker="A")
    b1 = account_operation(id="b1", ticker="B")
    a2 = account_operation(
        id="a2", ticker="A", type=OperationType.OPERATION_TYPE_COUPON
    )
    assert group_operations_by_ticker([a1, b1, a2]) == {"A": [a1, a2], "B": [b1]}
