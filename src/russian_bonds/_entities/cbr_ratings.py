from cbr_ratings import KraCode, RatingItem

# keyed by isin (bonds) or inn (issuers), then by agency
CbrRatings = dict[str, dict[KraCode, RatingItem]]
