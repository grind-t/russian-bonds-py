from collections.abc import Awaitable, Callable

from russian_bonds._entities.portfolio_bond_position import PortfolioBondPosition
from russian_bonds._entities.screener_bond import ScreenerBond
from russian_bonds._stateless_computations.build_issuer_investments import (
    build_issuer_investments,
)


async def get_issuer_investments(
    account_id: str,
    bonds: list[ScreenerBond],
    *,
    fetch_portfolio_bond_positions: Callable[
        [str], Awaitable[list[PortfolioBondPosition]]
    ],
) -> dict[str, float]:
    positions = await fetch_portfolio_bond_positions(account_id)
    return build_issuer_investments(positions=positions, bonds=bonds)
