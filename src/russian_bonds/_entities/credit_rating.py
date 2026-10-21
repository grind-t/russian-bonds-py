from cbr_ratings import Prediction
from pydantic import BaseModel


class CreditRating(BaseModel):
    value: int | None
    prediction: Prediction | None

    def is_acceptable(self) -> bool:
        # a missing prediction counts as the best one each threshold allows
        if self.value is None:
            return False
        return (
            self.value > 18
            or (self.value > 15 and self.prediction in (None, "STA", "POS"))
            or (self.value > 14 and self.prediction in (None, "POS"))
        )
