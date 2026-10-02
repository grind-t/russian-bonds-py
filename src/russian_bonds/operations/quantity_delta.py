from t_tech.invest import OperationType

BUY_TYPES = frozenset(
    {
        OperationType.OPERATION_TYPE_BUY,
        OperationType.OPERATION_TYPE_BUY_CARD,
        OperationType.OPERATION_TYPE_INPUT_SECURITIES,
        OperationType.OPERATION_TYPE_BUY_MARGIN,
    }
)
SELL_TYPES = frozenset(
    {
        OperationType.OPERATION_TYPE_OUTPUT_SECURITIES,
        OperationType.OPERATION_TYPE_SELL_CARD,
        OperationType.OPERATION_TYPE_SELL_MARGIN,
        OperationType.OPERATION_TYPE_SELL,
    }
)
BOND_REPAYMENT_FULL = OperationType.OPERATION_TYPE_BOND_REPAYMENT_FULL
NEUTRAL_TYPES = frozenset(
    {
        OperationType.OPERATION_TYPE_INPUT,
        OperationType.OPERATION_TYPE_BOND_TAX,
        OperationType.OPERATION_TYPE_OVERNIGHT,
        OperationType.OPERATION_TYPE_TAX,
        OperationType.OPERATION_TYPE_DIVIDEND_TAX,
        OperationType.OPERATION_TYPE_OUTPUT,
        OperationType.OPERATION_TYPE_BOND_REPAYMENT,
        OperationType.OPERATION_TYPE_TAX_CORRECTION,
        OperationType.OPERATION_TYPE_SERVICE_FEE,
        OperationType.OPERATION_TYPE_BENEFIT_TAX,
        OperationType.OPERATION_TYPE_MARGIN_FEE,
        OperationType.OPERATION_TYPE_BROKER_FEE,
        OperationType.OPERATION_TYPE_DIVIDEND,
        OperationType.OPERATION_TYPE_COUPON,
        OperationType.OPERATION_TYPE_SUCCESS_FEE,
        OperationType.OPERATION_TYPE_DIVIDEND_TRANSFER,
        OperationType.OPERATION_TYPE_ACCRUING_VARMARGIN,
        OperationType.OPERATION_TYPE_WRITING_OFF_VARMARGIN,
        OperationType.OPERATION_TYPE_TRACK_MFEE,
        OperationType.OPERATION_TYPE_TRACK_PFEE,
        OperationType.OPERATION_TYPE_TAX_PROGRESSIVE,
        OperationType.OPERATION_TYPE_BOND_TAX_PROGRESSIVE,
        OperationType.OPERATION_TYPE_DIVIDEND_TAX_PROGRESSIVE,
        OperationType.OPERATION_TYPE_BENEFIT_TAX_PROGRESSIVE,
        OperationType.OPERATION_TYPE_TAX_CORRECTION_PROGRESSIVE,
        OperationType.OPERATION_TYPE_TAX_REPO_PROGRESSIVE,
        OperationType.OPERATION_TYPE_TAX_REPO,
        OperationType.OPERATION_TYPE_TAX_REPO_HOLD,
        OperationType.OPERATION_TYPE_TAX_REPO_REFUND,
        OperationType.OPERATION_TYPE_TAX_REPO_HOLD_PROGRESSIVE,
        OperationType.OPERATION_TYPE_TAX_REPO_REFUND_PROGRESSIVE,
        OperationType.OPERATION_TYPE_DIV_EXT,
        OperationType.OPERATION_TYPE_TAX_CORRECTION_COUPON,
        OperationType.OPERATION_TYPE_CASH_FEE,
        OperationType.OPERATION_TYPE_OUT_FEE,
        OperationType.OPERATION_TYPE_OUT_STAMP_DUTY,
        OperationType.OPERATION_TYPE_OUTPUT_SWIFT,
        OperationType.OPERATION_TYPE_INPUT_SWIFT,
        OperationType.OPERATION_TYPE_OUTPUT_ACQUIRING,
        OperationType.OPERATION_TYPE_INPUT_ACQUIRING,
        OperationType.OPERATION_TYPE_OUTPUT_PENALTY,
        OperationType.OPERATION_TYPE_ADVICE_FEE,
        OperationType.OPERATION_TYPE_OUT_MULTI,
        OperationType.OPERATION_TYPE_INP_MULTI,
        OperationType.OPERATION_TYPE_OVER_PLACEMENT,
        OperationType.OPERATION_TYPE_OVER_COM,
        OperationType.OPERATION_TYPE_OVER_INCOME,
        OperationType.OPERATION_TYPE_OTHER_FEE,
    }
)


def quantity_delta(type: OperationType, quantity: int) -> int:
    if type in BUY_TYPES:
        return quantity
    if type in SELL_TYPES or type == BOND_REPAYMENT_FULL:
        return -quantity
    if type in NEUTRAL_TYPES:
        return 0
    raise ValueError(f"Unsupported operation type: {type}")
