import dataclasses
import json
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import httpx
import pytest
import time_machine
from google.protobuf import json_format
from syrupy.extensions.json import JSONSnapshotExtension
from t_tech.invest import PortfolioResponse, _grpc_helpers
from t_tech.invest.grpc import operations_pb2

from russian_bonds import get_account_bond_cash_flows

# recorded from a real account on 2026-10-03 with ids anonymized
FIXTURES = Path(__file__).parent / "fixtures" / "account_cash_flows"
ACCOUNT_ID = "test-account"
NOW = datetime(2026, 10, 3, tzinfo=UTC)
FROM = datetime(2024, 10, 3, tzinfo=UTC)


class _FakeOperationsStub:
    def __init__(self) -> None:
        pages = json.loads((FIXTURES / "t_invest" / "operations.json").read_text())
        self._pages = [
            json_format.ParseDict(page, operations_pb2.GetOperationsByCursorResponse())
            for page in pages
        ]

    async def GetOperationsByCursor(  # noqa: N802
        self, request: operations_pb2.GetOperationsByCursorRequest, metadata
    ) -> operations_pb2.GetOperationsByCursorResponse:
        assert request.account_id == ACCOUNT_ID
        assert getattr(request, "from").ToDatetime(UTC) == FROM
        page = int(request.cursor.removeprefix("cursor-")) if request.cursor else 0
        return self._pages[page]


async def _get_portfolio(*, account_id: str) -> PortfolioResponse:
    assert account_id == ACCOUNT_ID
    data = json.loads((FIXTURES / "t_invest" / "portfolio.json").read_text())
    return _grpc_helpers.protobuf_to_dataclass(
        json_format.ParseDict(data, operations_pb2.PortfolioResponse()),
        PortfolioResponse,
    )


def _moex_handler(request: httpx.Request) -> httpx.Response:
    # /iss/securities/X/bondization.json -> securities__X__bondization.json
    name = request.url.path.removeprefix("/iss/").replace("/", "__")
    return httpx.Response(200, content=(FIXTURES / "moex" / name).read_bytes())


@pytest.fixture
def snapshot(snapshot):
    return snapshot.use_extension(JSONSnapshotExtension)


@time_machine.travel(NOW, tick=False)
async def test_account_bond_cash_flows(snapshot):
    t_invest_client = SimpleNamespace(
        operations=SimpleNamespace(
            stub=_FakeOperationsStub(), metadata=[], get_portfolio=_get_portfolio
        )
    )
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(_moex_handler)
    ) as moex_client:
        rows = await get_account_bond_cash_flows(
            t_invest_client=t_invest_client,  # ty: ignore[invalid-argument-type]
            moex_client=moex_client,
            account_id=ACCOUNT_ID,
            from_=FROM,
        )
    assert [
        {
            **dataclasses.asdict(row),
            "type": row.type.name,
            "date": row.date.isoformat(),
        }
        for row in rows
    ] == snapshot
