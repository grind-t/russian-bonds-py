from dataclasses import dataclass
from typing import Protocol

from t_tech.invest import OperationType
from toolkit.boolean import ensure

_SUPPORTED_TYPES = frozenset(
    {
        OperationType.OPERATION_TYPE_BUY,
        OperationType.OPERATION_TYPE_BUY_CARD,
        OperationType.OPERATION_TYPE_BUY_MARGIN,
        OperationType.OPERATION_TYPE_SELL,
        OperationType.OPERATION_TYPE_SELL_CARD,
        OperationType.OPERATION_TYPE_SELL_MARGIN,
        OperationType.OPERATION_TYPE_BOND_REPAYMENT_FULL,
        OperationType.OPERATION_TYPE_COUPON,
        OperationType.OPERATION_TYPE_BOND_REPAYMENT,
    }
)


class _Operation(Protocol):
    type: OperationType
    quantity_delta: int


@dataclass
class FifoPosition:
    """Position split into the bonds held before the operations and bought within them.

    FIFO: sells consume the initial bonds first.
    """

    initial: int
    bought: int = 0
    # carries over to payments after the position is closed
    bought_share: float = 0.0

    def kept_fraction(self, operation: _Operation) -> float:
        """Applies an operation and returns the fraction of it to keep."""
        ensure(
            operation.type in _SUPPORTED_TYPES,
            f"Unsupported operation type: {operation.type}",
        )
        quantity_delta = operation.quantity_delta
        if quantity_delta == 0:
            # the share is taken at the payment date, not the record date,
            # so it is approximate if a deal falls between the two
            return self.bought_share
        if quantity_delta > 0:
            self.bought += quantity_delta
            fraction = 1.0
        else:
            abs_delta = -quantity_delta
            initial_sold = min(self.initial, abs_delta)
            bought_sold = abs_delta - initial_sold
            self.initial -= initial_sold
            self.bought -= bought_sold
            fraction = bought_sold / abs_delta
        if (total := self.initial + self.bought) > 0:
            self.bought_share = self.bought / total
        return fraction
