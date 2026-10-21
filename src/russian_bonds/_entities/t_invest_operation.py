from dataclasses import dataclass

from t_tech.invest import OperationItem, _grpc_helpers


# the SDK schema omits the ticker field that the API does return
@dataclass(eq=False, repr=True)
class TInvestOperation(OperationItem):
    ticker: str = _grpc_helpers.string_field(36)
