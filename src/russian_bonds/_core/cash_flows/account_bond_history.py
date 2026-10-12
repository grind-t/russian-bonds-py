from typing import Self

from pydantic import BaseModel, computed_field, model_validator
from t_tech.invest import OperationType
from toolkit.boolean import ensure

from russian_bonds._core.cash_flows.account_operation import AccountOperation
from russian_bonds._core.cash_flows.bond import Bond
from russian_bonds._core.cash_flows.bond_cash_flow import BondCashFlow
from russian_bonds._core.cash_flows.fifo_position import FifoPosition

_BROKER_FEE = OperationType.OPERATION_TYPE_BROKER_FEE


class AccountBondHistory(BaseModel):
    bond: Bond
    operations: list[AccountOperation]

    @model_validator(mode="after")
    def _check_tickers(self) -> Self:
        for op in self.operations:
            ensure(
                op.ticker == self.bond.ticker,
                f"Operation {op.id} of {op.ticker} for {self.bond.ticker}",
            )
        return self

    @model_validator(mode="after")
    def _check_closed(self) -> Self:
        net = sum(op.quantity_delta for op in self.operations)
        ensure(net <= 0, f"Unclosed position for {self.bond.ticker}")
        return self

    @computed_field
    @property
    def initial_bond_quantity(self) -> int:
        # history always ends at zero (virtual sell or full repayment),
        # so a negative sum is the quantity held before the operations
        return -sum(op.quantity_delta for op in self.operations)

    def without_initial_bonds(self) -> Self:
        position = FifoPosition(initial=self.initial_bond_quantity)
        op_fractions: dict[str, float] = {}  # fraction of each operation to keep
        # a stable sort keeps operations with the same date in order
        for op in sorted(self.operations, key=lambda op: op.date):
            if op.type != _BROKER_FEE:
                op_fractions[op.id] = position.kept_fraction(op)

        operations: list[AccountOperation] = []
        for op in self.operations:
            # a fee follows its deal and is dropped with a deal outside the operations
            id = op.parent_operation_id if op.type == _BROKER_FEE else op.id
            op_fraction = op_fractions.get(id, 0.0)
            if op_fraction == 0:
                continue
            op_copy = op.model_copy(
                update={
                    "payment": op.payment * op_fraction,
                    "quantity_delta": round(op.quantity_delta * op_fraction),
                }
            )
            operations.append(op_copy)
        return type(self)(bond=self.bond, operations=operations)

    def to_cash_flows(self) -> list[BondCashFlow]:
        """Cash flows of the bonds bought within the history."""
        return [
            BondCashFlow(
                ticker=op.ticker,
                bond_name=self.bond.name,
                name=op.name,
                description=op.description,
                type=op.type,
                value=op.payment,
                face_unit=self.bond.face_unit,
                date=op.date,
                virtual=op.virtual,
            )
            for op in self.without_initial_bonds().operations
        ]
