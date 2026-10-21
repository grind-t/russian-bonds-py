from cbr_ratings import Prediction
from pydantic import AliasChoices, BaseModel, Field


class CreditRating(BaseModel):
    value: int | None = None
    # ifrs ratings name the prediction an outlook
    prediction: Prediction | None = Field(
        default=None, validation_alias=AliasChoices("prediction", "outlook")
    )
