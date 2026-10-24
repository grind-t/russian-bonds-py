from fractions import Fraction

from t_tech.invest import OperationType

from russian_bonds._entities.account_bond_history import AccountBondHistory
from russian_bonds._entities.account_operation import AccountOperation
from russian_bonds._entities.rub_money import RubMoney
from russian_bonds._stateful_computations.fifo_position import FifoPosition

_BROKER_FEE = OperationType.OPERATION_TYPE_BROKER_FEE


def without_initial_bonds(history: AccountBondHistory) -> AccountBondHistory:
    position = FifoPosition(initial=history.initial_quantity)
    op_fractions: dict[str, Fraction] = {}  # fraction of each operation to keep
    # a stable sort keeps operations with the same date in order
    for op in sorted(history.operations, key=lambda op: op.date):
        if op.type != _BROKER_FEE:
            op_fractions[op.id] = position.apply(op)

    operations: list[AccountOperation] = []
    for op in history.operations:
        # a fee follows its deal and is dropped with a deal outside the operations
        deal_id = op.parent_operation_id if op.type == _BROKER_FEE else op.id
        op_fraction = op_fractions.get(deal_id, Fraction(0))
        if op_fraction == 0:
            continue
        op_copy = op.model_copy(
            update={
                "payment": RubMoney(
                    amount=op.payment.amount
                    * op_fraction.numerator
                    / op_fraction.denominator
                ),
                "quantity_delta": round(op.quantity_delta * op_fraction),
            }
        )
        operations.append(op_copy)
    return AccountBondHistory(bond=history.bond, operations=operations)
