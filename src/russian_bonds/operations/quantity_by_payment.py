import math

from toolkit.boolean import ensure


def get_quantity_by_payment(payment: float, face_value_rub: float) -> int:
    quantity = payment / face_value_rub
    rounded = round(quantity)
    ensure(
        rounded > 0 and math.isclose(quantity, rounded),
        "Abnormal full repayment quantity",
    )
    return rounded
