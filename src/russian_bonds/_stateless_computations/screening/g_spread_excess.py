from statistics import median

from toolkit.array import group_by

from russian_bonds._entities.screener_bond import ScreenerBond

# a median of fewer bonds is too noisy to compare against
_MIN_PEERS = 5


def g_spread_excess(bonds: list[ScreenerBond]) -> dict[str, float]:
    """G-spread over the median of bonds with the same rating, by isin."""
    spreads = [
        (bond.isin, bond.g_spread, rating)
        for bond in bonds
        if bond.g_spread is not None and (rating := _rating(bond)) is not None
    ]
    result: dict[str, float] = {}
    for peers in group_by(spreads, lambda item: item[2]).values():
        if len(peers) < _MIN_PEERS:
            continue
        peer_median = median(g_spread for _, g_spread, _ in peers)
        for isin, g_spread, _ in peers:
            result[isin] = g_spread - peer_median
    return result


def _rating(bond: ScreenerBond) -> int | None:
    # the ifrs rating goes first; among agencies the lowest one keeps
    # the comparison conservative
    if bond.ifrs_rating is not None and bond.ifrs_rating.value is not None:
        return bond.ifrs_rating.value
    values = [r.value for r in bond.agency_ratings.values() if r.value is not None]
    return min(values, default=None)
