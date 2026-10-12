import asyncio
from datetime import UTC, datetime

import httpx
from moex import get_moex_bond_amortizations, get_moex_security_description
from t_tech.invest import GetOperationsByCursorRequest, _grpc_helpers
from t_tech.invest.async_services import AsyncServices
from t_tech.invest.grpc import operations_pb2

from russian_bonds._core.cash_flows.account_bond_history import AccountBondHistory
from russian_bonds._core.cash_flows.account_operation import (
    AccountOperation,
    group_operations_by_ticker,
)
from russian_bonds._core.cash_flows.bond import Bond
from russian_bonds._core.cash_flows.bond_cash_flow import BondCashFlow, bond_cash_flows
from russian_bonds._core.cash_flows.operation_quantity import BOND_REPAYMENT_FULL
from russian_bonds._core.cash_flows.t_invest_operations import (
    account_operation_from_t_invest_item,
    executed_bond_operation_items,
    virtual_sells,
)


async def get_account_bond_cash_flows(
    t_invest_client: AsyncServices,
    moex_client: httpx.AsyncClient,
    account_id: str,
    from_: datetime | None = None,
) -> list[BondCashFlow]:
    now = datetime.now(UTC)
    account_operations, portfolio = await asyncio.gather(
        _fetch_account_operations(t_invest_client, moex_client, account_id, from_),
        t_invest_client.operations.get_portfolio(account_id=account_id),
    )
    operations = account_operations + virtual_sells(portfolio.positions, now)
    by_ticker = group_operations_by_ticker(operations)
    bonds = await asyncio.gather(
        *(_fetch_bond(ticker, moex_client) for ticker in by_ticker)
    )
    return bond_cash_flows(
        AccountBondHistory(bond=bond, operations=ops)
        for bond, ops in zip(bonds, by_ticker.values(), strict=True)
    )


async def _fetch_account_operations(
    t_invest_client: AsyncServices,
    moex_client: httpx.AsyncClient,
    account_id: str,
    from_: datetime | None,
) -> list[AccountOperation]:
    raw_items: list[operations_pb2.OperationItem] = []
    cursor: str | None = None
    while True:
        # the stub is called directly to get raw items that still carry the ticker
        res = await t_invest_client.operations.stub.GetOperationsByCursor(
            request=_grpc_helpers.dataclass_to_protobuf(
                GetOperationsByCursorRequest(
                    account_id=account_id,
                    from_=from_,
                    cursor=cursor,
                    limit=1000,  # API maximum
                ),
                operations_pb2.GetOperationsByCursorRequest(),
            ),
            metadata=t_invest_client.operations.metadata,
        )
        raw_items.extend(res.items)
        if not res.has_next:
            break
        cursor = res.next_cursor

    items = executed_bond_operation_items(raw_items)
    repaid_tickers = {item.ticker for item in items if item.type == BOND_REPAYMENT_FULL}
    final_amortizations = dict(
        zip(
            repaid_tickers,
            await asyncio.gather(
                *(_fetch_final_amortization(t, moex_client) for t in repaid_tickers)
            ),
            strict=True,
        )
    )
    return [
        account_operation_from_t_invest_item(item, final_amortizations.get(item.ticker))
        for item in items
    ]


async def _fetch_final_amortization(
    ticker: str, client: httpx.AsyncClient
) -> float | None:
    # the last amortization is the final repayment
    amortizations = await get_moex_bond_amortizations(ticker, client=client)
    return amortizations[-1].value_rub if amortizations else None


async def _fetch_bond(ticker: str, client: httpx.AsyncClient) -> Bond:
    description = await get_moex_security_description(ticker, client=client)
    # validation rejects the fields moex leaves empty
    return Bond.model_validate(
        {
            "ticker": ticker,
            "name": description.SHORTNAME,
            "face_value": description.FACEVALUE,
            "face_unit": description.FACEUNIT,
        }
    )
