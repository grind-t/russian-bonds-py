from factories import agency, ifrs, screener_bond

from russian_bonds._stateless_computations.screening.g_spread_excess import (
    g_spread_excess,
)


def test_g_spread_excess():
    a_peers = [
        screener_bond(isin=f"A{i}", g_spread=g_spread, **agency("AKRA", 18))
        for i, g_spread in enumerate([2.0, 3.0, 4.0, 5.0])
    ]
    bonds = [
        *a_peers,
        # the ifrs rating wins over the agency one
        screener_bond(isin="IFRS", g_spread=9.0, **agency("AKRA", 23), **ifrs(18)),
        # the lowest agency rating counts
        screener_bond(
            isin="LOWEST",
            g_spread=1.0,
            agency_ratings={"AKRA": {"value": 23}, "NKR": {"value": 18}},
        ),
        # too few peers
        *(
            screener_bond(isin=f"AAA{i}", g_spread=1.0, **agency("AKRA", 23))
            for i in range(4)
        ),
        # no spread or no rating
        screener_bond(isin="NO_SPREAD", g_spread=None, **agency("AKRA", 18)),
        screener_bond(isin="UNRATED", g_spread=4.0, agency_ratings={}),
    ]
    # median of 1, 2, 3, 4, 5, 9 is 3.5
    assert g_spread_excess(bonds) == {
        "A0": -1.5,
        "A1": -0.5,
        "A2": 0.5,
        "A3": 1.5,
        "IFRS": 5.5,
        "LOWEST": -2.5,
    }
