from collections.abc import Awaitable, Callable

from t_tech.invest import PortfolioPosition

from russian_bonds._entities.screener_bond import ScreenerBond
from russian_bonds._stateless_computations.build_issuer_investments import (
    build_issuer_investments,
)


async def get_issuer_investments(
    account_id: str,
    bonds: list[ScreenerBond],
    *,
    fetch_portfolio_positions: Callable[[str], Awaitable[list[PortfolioPosition]]],
) -> dict[str, float]:
    positions = await fetch_portfolio_positions(account_id)
    return build_issuer_investments(positions=positions, bonds=bonds)
