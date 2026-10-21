from datetime import datetime
from functools import partial

import httpx
from cbr_ratings import KraCode, RatingItem
from moex import (
    get_moex_bond_amortizations,
    get_moex_bond_securities,
    get_moex_bonds,
    get_moex_bonds_market_data,
    get_moex_bonds_market_yield,
)
from t_tech.invest.async_services import AsyncServices

from russian_bonds._entities.account_bond_history import AccountBondHistory
from russian_bonds._entities.account_operation import AccountOperation
from russian_bonds._entities.bond import Bond
from russian_bonds._entities.cash_flow import CashFlow
from russian_bonds._entities.credit_rating import CreditRating
from russian_bonds._entities.rub_money import RubMoney
from russian_bonds._entities.screener_bond import ScreenerBond
from russian_bonds._stateless_computations.is_foreign_currency_candidate import (
    is_foreign_currency_candidate,
)
from russian_bonds._stateless_computations.is_rub_candidate import is_rub_candidate
from russian_bonds._stateless_computations.quantity_delta import BUY_TYPES, SELL_TYPES
from russian_bonds._stateless_effects.fetch_bond import fetch_bond
from russian_bonds._stateless_effects.fetch_brotli_json import fetch_brotli_json
from russian_bonds._stateless_effects.fetch_portfolio_bond_positions import (
    fetch_portfolio_bond_positions,
)
from russian_bonds._stateless_effects.fetch_t_invest_operations import (
    fetch_t_invest_operations,
)
from russian_bonds._stateless_workflows.get_account_cash_flows import (
    get_account_cash_flows as _get_account_cash_flows,
)
from russian_bonds._stateless_workflows.get_issuer_investments import (
    get_issuer_investments as _get_issuer_investments,
)
from russian_bonds._stateless_workflows.get_screener_bonds import (
    get_screener_bonds as _get_screener_bonds,
)

_BOND_RATINGS_URL = "https://raw.githubusercontent.com/grind-t/cbr-ratings-py/refs/heads/main/exports/bonds.json.br"
_ISSUER_RATINGS_URL = "https://raw.githubusercontent.com/grind-t/cbr-ratings-py/refs/heads/main/exports/issuers.json.br"
_IFRS_RATINGS_URL = "https://raw.githubusercontent.com/grind-t/e-disclosure-py/refs/heads/main/exports/ratings.json.br"


async def get_account_cash_flows(
    t_invest_client: AsyncServices,
    moex_client: httpx.AsyncClient,
    account_id: str,
    from_: datetime | None = None,
) -> list[CashFlow]:
    return await _get_account_cash_flows(
        account_id,
        from_,
        fetch_t_invest_operations=partial(fetch_t_invest_operations, t_invest_client),
        fetch_portfolio_bond_positions=partial(
            fetch_portfolio_bond_positions, t_invest_client
        ),
        fetch_amortizations=partial(get_moex_bond_amortizations, client=moex_client),
        fetch_bond=partial(fetch_bond, client=moex_client),
    )


async def get_issuer_investments(
    *, t_invest_client: AsyncServices, account_id: str, bonds: list[ScreenerBond]
) -> dict[str, float]:
    return await _get_issuer_investments(
        account_id,
        bonds,
        fetch_portfolio_bond_positions=partial(
            fetch_portfolio_bond_positions, t_invest_client
        ),
    )


async def get_screener_bonds(
    *, t_invest_client: AsyncServices, http_client: httpx.AsyncClient
) -> list[ScreenerBond]:
    return await _get_screener_bonds(
        fetch_t_invest_bonds=t_invest_client.instruments.bonds,
        fetch_moex_securities=partial(get_moex_bond_securities, client=http_client),
        fetch_moex_bonds=partial(get_moex_bonds, client=http_client),
        fetch_moex_market_data=partial(get_moex_bonds_market_data, client=http_client),
        fetch_moex_market_yields=partial(
            get_moex_bonds_market_yield, client=http_client
        ),
        fetch_cbr_ratings_by_isin=partial(
            fetch_brotli_json,
            _BOND_RATINGS_URL,
            dict[str, dict[KraCode, RatingItem]],
            http_client,
        ),
        fetch_cbr_ratings_by_inn=partial(
            fetch_brotli_json,
            _ISSUER_RATINGS_URL,
            dict[str, dict[KraCode, RatingItem]],
            http_client,
        ),
        fetch_ifrs_rating_by_inn=partial(
            fetch_brotli_json, _IFRS_RATINGS_URL, dict[str, CreditRating], http_client
        ),
    )


__all__ = [
    "BUY_TYPES",
    "SELL_TYPES",
    "AccountBondHistory",
    "AccountOperation",
    "Bond",
    "CashFlow",
    "CreditRating",
    "RubMoney",
    "ScreenerBond",
    "get_account_cash_flows",
    "get_issuer_investments",
    "get_screener_bonds",
    "is_foreign_currency_candidate",
    "is_rub_candidate",
]
