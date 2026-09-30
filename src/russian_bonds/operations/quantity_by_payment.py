import math


def get_quantity_by_payment(payment: float, face_value_rub: float) -> int:
    quantity = payment / face_value_rub
    rounded = round(quantity)
    if rounded <= 0 or not math.isclose(quantity, rounded):
        raise ValueError("Abnormal full repayment quantity")
    return rounded
