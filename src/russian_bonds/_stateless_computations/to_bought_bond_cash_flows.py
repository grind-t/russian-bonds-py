from russian_bonds._entities.account_bond_history import AccountBondHistory
from russian_bonds._entities.cash_flow import CashFlow
from russian_bonds._stateless_computations.without_initial_bonds import (
    without_initial_bonds,
)


def to_bought_bond_cash_flows(history: AccountBondHistory) -> list[CashFlow]:
    """Cash flows of the bonds bought within the history."""
    return [
        CashFlow(
            ticker=op.ticker,
            bond_name=history.bond.name,
            operation_name=op.name,
            description=op.description,
            type=op.type,
            payment=op.payment.float_amount,
            face_unit=history.bond.face_unit,
            date=op.date,
            virtual=op.virtual,
        )
        for op in without_initial_bonds(history).operations
    ]
