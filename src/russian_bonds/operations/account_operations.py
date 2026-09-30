from dataclasses import dataclass
from datetime import datetime

from t_tech.invest import GetOperationsByCursorRequest, OperationItem, _grpc_helpers
from t_tech.invest.async_services import AsyncServices
from t_tech.invest.grpc import operations_pb2


# the SDK schema omits the ticker field that the API does return
@dataclass(eq=False, repr=True)
class BondOperationItem(OperationItem):
    ticker: str = _grpc_helpers.string_field(36)


async def get_account_bond_operations(
    client: AsyncServices,
    account_id: str,
    from_: datetime | None = None,
    to: datetime | None = None,
) -> list[BondOperationItem]:
    items: list[operations_pb2.OperationItem] = []
    cursor: str | None = None
    while True:
        # the stub is called directly to get raw items that still carry the ticker
        res = await client.operations.stub.GetOperationsByCursor(
            request=_grpc_helpers.dataclass_to_protobuf(
                GetOperationsByCursorRequest(
                    account_id=account_id,
                    from_=from_,
                    to=to,
                    cursor=cursor,
                    limit=1000,  # API maximum
                ),
                operations_pb2.GetOperationsByCursorRequest(),
            ),
            metadata=client.operations.metadata,
        )
        items.extend(res.items)
        if not res.has_next:
            break
        cursor = res.next_cursor

    # API has no instrument type filter, so bonds are picked client-side
    return [
        _grpc_helpers.protobuf_to_dataclass(op, BondOperationItem)
        for op in items
        if op.instrument_type == "bond"
    ]
