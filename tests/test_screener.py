import logging
from datetime import date

import pytest
from cbr_ratings import Prediction, RatingItem
from google.protobuf import json_format
from moex import MoexBond, MoexBondMarketData, MoexBondMarketYield, MoexSecurity
from syrupy.extensions.json import JSONSnapshotExtension
from t_tech.invest import Bond, _grpc_helpers
from t_tech.invest.grpc import instruments_pb2

from russian_bonds.screener import CbrRatings, IfrsRating, build_screener_bonds


def t_invest_bond(isin: str, **fields) -> Bond:
    # go through protobuf so missing fields get the same defaults as from the API
    pb = json_format.ParseDict(
        {
            "isin": isin,
            "name": f"Облигация {isin}",
            "classCode": "TQCB",
            "currency": "rub",
            "sector": "financial",
            "nominal": {"currency": "rub", "units": "1000"},
            "buyAvailableFlag": True,
            "apiTradeAvailableFlag": True,
            "riskLevel": "RISK_LEVEL_MODERATE",
            "maturityDate": "2030-06-15T00:00:00Z",
            **fields,
        },
        instruments_pb2.Bond(),
    )
    return _grpc_helpers.protobuf_to_dataclass(pb, Bond)


def moex_security(isin: str, inn: str | None, type_: str = "corporate_bond"):
    return MoexSecurity.model_construct(
        isin=isin,
        secid=isin,
        primary_boardid="TQCB",
        emitent_inn=inn,
        type=type_,
    )


def moex_bond(secid: str, board: str = "TQCB", **fields) -> MoexBond:
    defaults = {
        "CALLOPTIONDATE": None,
        "PUTOPTIONDATE": None,
        "YIELDATPREVWAPRICE": None,
    }
    return MoexBond.model_construct(SECID=secid, BOARDID=board, **defaults | fields)


def market_data(secid: str, board: str = "TQCB", **fields) -> MoexBondMarketData:
    defaults = {"YIELDTOOFFER": None, "YIELD": None, "YIELDATWAPRICE": None}
    return MoexBondMarketData.model_construct(
        SECID=secid, BOARDID=board, **defaults | fields
    )


def cbr(rating_code: str, prediction: Prediction | None) -> RatingItem:
    # the screener reads only these fields, rating_number is computed from the code
    return RatingItem.model_construct(rating_code=rating_code, prediction=prediction)


T_INVEST_BONDS = [
    # ofz floater: effective yield, low t-invest risk
    t_invest_bond(
        "OFZ_FLOAT",
        floatingCouponFlag=True,
        riskLevel="RISK_LEVEL_LOW",
        sector="government",
    ),
    # offer from moex, bond rating overrides issuer one
    t_invest_bond("PUT_OFFER", amortizationFlag=True, forQualInvestorFlag=True),
    # offer from t-invest call date, zero offer yield falls through to yield
    t_invest_bond("CALL_OFFER", callDate="2027-01-01T00:00:00Z"),
    # no market data: previous weighted average price yield, issuer-only rating
    t_invest_bond(
        "PREV_YIELD",
        riskLevel="RISK_LEVEL_HIGH",
        maturityDate=None,
        nominal=None,
        currency="usd",
    ),
    # moex rows on a non-primary board are ignored
    t_invest_bond("OTHER_BOARD", riskLevel="RISK_LEVEL_UNSPECIFIED"),
    # skipped: not available to buy
    t_invest_bond("NOT_BUYABLE", buyAvailableFlag=False),
    # skipped silently: spb exchange
    t_invest_bond("SPB_ONLY", classCode="SPBBND"),
    # skipped with a warning: missing moex data
    t_invest_bond("NO_MOEX"),
]

MOEX_SECURITIES = [
    moex_security("OFZ_FLOAT", "7710168360", type_="ofz_bond"),
    moex_security("PUT_OFFER", "7700000001"),
    moex_security("CALL_OFFER", "7700000002"),
    moex_security("PREV_YIELD", "7700000003"),
    moex_security("OTHER_BOARD", None),
    moex_security("NOT_BUYABLE", "7700000001"),
]

MOEX_BONDS = [
    moex_bond("OFZ_FLOAT", YIELDATPREVWAPRICE=14.0),
    moex_bond("PUT_OFFER", PUTOPTIONDATE=date(2027, 3, 1)),
    moex_bond("CALL_OFFER"),
    moex_bond("PREV_YIELD", YIELDATPREVWAPRICE=21.5),
    moex_bond("OTHER_BOARD", board="TQIR", YIELDATPREVWAPRICE=30.0),
]

MOEX_MARKET_DATA = [
    market_data("OFZ_FLOAT", YIELD=15.0),
    market_data("PUT_OFFER", YIELDTOOFFER=19.2, YIELD=18.0),
    market_data("CALL_OFFER", YIELDTOOFFER=0.0, YIELD=17.3),
    market_data("OTHER_BOARD", board="TQIR", YIELD=30.0),
]

MOEX_MARKET_YIELDS = [
    MoexBondMarketYield.model_construct(
        SECID="OFZ_FLOAT", BOARDID="TQCB", EFFECTIVEYIELD=16.1
    ),
]

BOND_RATINGS: CbrRatings = {
    "PUT_OFFER": {"AKRA": cbr("AA-", None)},
}

ISSUER_RATINGS: CbrRatings = {
    "7700000001": {
        "AKRA": cbr("A", "POS"),
        "EXPERT_RA": cbr("A+", "STA"),
    },
    "7700000003": {
        "NKR": cbr("BB+", "NEG"),
        "NRA": cbr("BBB", "DEV"),
    },
}

IFRS_RATINGS = {
    "7700000001": IfrsRating(value=17, outlook="STA"),
}


@pytest.fixture
def snapshot(snapshot):
    return snapshot.use_extension(JSONSnapshotExtension)


def build():
    return build_screener_bonds(
        t_invest_bonds=T_INVEST_BONDS,
        moex_securities=MOEX_SECURITIES,
        moex_bonds=MOEX_BONDS,
        moex_market_data=MOEX_MARKET_DATA,
        moex_market_yields=MOEX_MARKET_YIELDS,
        bond_ratings=BOND_RATINGS,
        issuer_ratings=ISSUER_RATINGS,
        ifrs_ratings=IFRS_RATINGS,
    )


def test_screener_bonds(snapshot):
    assert [bond.model_dump(mode="json") for bond in build()] == snapshot


def test_warns_about_missing_moex_data(caplog):
    with caplog.at_level(logging.WARNING):
        build()
    assert caplog.messages == ["Missing moex data for bond NO_MOEX"]
