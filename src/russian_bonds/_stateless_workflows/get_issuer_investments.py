from collections.abc import Awaitable, Callable

from russian_bonds._entities.account_position import AccountPosition
from russian_bonds._entities.screener_bond import ScreenerBond
from russian_bonds._stateless_computations.build_issuer_investments import (
    build_issuer_investments,
)


async def get_issuer_investments(
    account_id: str,
    bonds: list[ScreenerBond],
    *,
    fetch_account_positions: Callable[[str], Awaitable[list[AccountPosition]]],
) -> dict[str, float]:
    positions = await fetch_account_positions(account_id)
    return build_issuer_investments(positions=positions, bonds=bonds)
