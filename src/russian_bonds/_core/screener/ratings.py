from cbr_ratings import KraCode, Prediction, RatingItem
from pydantic import BaseModel


class _IfrsRating(BaseModel):
    value: int | None = None
    outlook: Prediction | None = None


# keyed by isin (bonds) or inn (issuers), then by agency
CbrRatings = dict[str, dict[KraCode, RatingItem]]
IfrsRatings = dict[str, _IfrsRating]  # keyed by inn
