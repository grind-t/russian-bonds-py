from datetime import datetime

from t_tech.invest import GetOperationsByCursorRequest, _grpc_helpers
from t_tech.invest.async_services import AsyncServices
from t_tech.invest.grpc import operations_pb2

from russian_bonds._entities.t_invest_operation import TInvestOperation


async def fetch_t_invest_operations(
    client: AsyncServices, account_id: str, from_: datetime | None
) -> list[TInvestOperation]:
    """All account operations, newest first."""
    items: list[TInvestOperation] = []
    cursor: str | None = None
    while True:
        # the stub is called directly to get raw items that still carry the ticker
        res = await client.operations.stub.GetOperationsByCursor(
            request=_grpc_helpers.dataclass_to_protobuf(
                GetOperationsByCursorRequest(
                    account_id=account_id,
                    from_=from_,
                    cursor=cursor,
                    limit=1000,  # API maximum
                ),
                operations_pb2.GetOperationsByCursorRequest(),
            ),
            metadata=client.operations.metadata,
        )
        items.extend(
            _grpc_helpers.protobuf_to_dataclass(raw, TInvestOperation)
            for raw in res.items
        )
        if not res.has_next:
            return items
        cursor = res.next_cursor
