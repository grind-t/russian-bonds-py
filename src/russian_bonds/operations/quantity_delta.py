BUY_TYPES = frozenset({15, 16, 17, 20})  # BUY, BUY_CARD, INPUT_SECURITIES, BUY_MARGIN
SELL_TYPES = frozenset({3, 7, 18, 22})  # OUTPUT_SECURITIES, SELL_CARD, SELL_MARGIN, SELL
BOND_REPAYMENT_FULL = 6


def quantity_delta(type: int, quantity: float) -> float:
    if type in BUY_TYPES:
        return quantity
    if type in SELL_TYPES or type == BOND_REPAYMENT_FULL:
        return -quantity
    return 0
