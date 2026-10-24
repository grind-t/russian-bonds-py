import asyncio
import os
from datetime import UTC, date, datetime, timedelta

import httpx
import streamlit as st
from cbr_ratings import KraCode
from pyxirr import xirr
from t_tech.invest import AsyncClient
from toolkit.array import group_by

from russian_bonds import (
    CashFlow,
    CreditRating,
    ScreenerBond,
    default_rub_fixed_screener,
    default_rub_floater_screener,
    get_account_cash_flows,
    get_issuer_investments,
    get_screener_bonds,
)

PERIOD = timedelta(days=365)
TAX_RATE = 0.13
MIN_HOLDING_DAYS = 60
YEAR = timedelta(days=365.25)


def http_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        limits=httpx.Limits(max_connections=10),
        timeout=httpx.Timeout(10.0, pool=None),
    )


async def fetch_cash_flows(from_: datetime) -> list[CashFlow]:
    async with (
        AsyncClient(os.environ["T_INVEST_READONLY_TOKEN"]) as t_invest_client,
        http_client() as moex_client,
    ):
        return await get_account_cash_flows(
            t_invest_client=t_invest_client,
            moex_client=moex_client,
            account_id=os.environ["T_INVEST_ACCOUNT_ID"],
            from_=from_,
        )


@st.cache_data(ttl=timedelta(hours=1), show_spinner="Загрузка операций...")
def load_cash_flows() -> list[CashFlow]:
    return asyncio.run(fetch_cash_flows(datetime.now(UTC) - PERIOD))


async def fetch_screener() -> tuple[list[ScreenerBond], dict[str, float]]:
    async with (
        AsyncClient(os.environ["T_INVEST_READONLY_TOKEN"]) as t_invest_client,
        http_client() as client,
    ):
        bonds = await get_screener_bonds(
            t_invest_client=t_invest_client, http_client=client
        )
        issuer_investments = await get_issuer_investments(
            t_invest_client=t_invest_client,
            account_id=os.environ["T_INVEST_ACCOUNT_ID"],
            bonds=bonds,
        )
    return bonds, issuer_investments


@st.cache_data(ttl=timedelta(hours=1), show_spinner="Загрузка облигаций...")
def load_screener() -> tuple[list[ScreenerBond], dict[str, float]]:
    return asyncio.run(fetch_screener())


def holding_days(bond_rows: list[CashFlow]) -> int:
    dates = [row.date for row in bond_rows]
    return (max(dates) - min(dates)).days


AGENCY_LABELS: dict[KraCode, str] = {
    "AKRA": "АКРА",
    "NKR": "НКР",
    "EXPERT_RA": "Эксперт РА",
    "NRA": "НРА",
}


def rating(credit_rating: CreditRating | None) -> str:
    if credit_rating is None:
        return ""
    parts = (credit_rating.value, credit_rating.prediction)
    return " ".join(str(v) for v in parts if v is not None)


def _ytm_rank(bond: ScreenerBond) -> tuple[bool, float]:
    # bonds without a yield go last
    return bond.ytm is not None, bond.ytm or 0.0


def by_issuer_yield(bonds: list[ScreenerBond]) -> list[ScreenerBond]:
    # issuers by their best yield, so bonds of one issuer stay together;
    # a bond without an issuer inn is an issuer of its own
    by_issuer = group_by(bonds, lambda bond: bond.issuer_inn or bond.isin)
    issuer_bonds = [
        sorted(group, key=_ytm_rank, reverse=True) for group in by_issuer.values()
    ]
    issuer_bonds.sort(key=lambda group: _ytm_rank(group[0]), reverse=True)
    return [bond for group in issuer_bonds for bond in group]


def identity_columns(
    bond: ScreenerBond, issuer_investments: dict[str, float]
) -> dict[str, object]:
    return {
        "Наименование": bond.name,
        "ISIN": bond.isin,
        "ИНН эмитента": bond.issuer_inn,
        "Вложено в эмитента, ₽": round(
            issuer_investments.get(bond.issuer_inn or "", 0.0), 2
        ),
    }


def fixed_coupon_columns(bond: ScreenerBond) -> dict[str, object]:
    return {
        "YTM по предложению": bond.ask_ytm,
        "G-спред, п.п.": bond.g_spread,
        "Дюрация, лет": None if bond.duration is None else bond.duration / YEAR,
    }


def price_columns(bond: ScreenerBond) -> dict[str, object]:
    return {
        "Последняя цена": bond.last_price,
        "Лучшее предложение": bond.best_ask_price,
    }


def profile_columns(bond: ScreenerBond, today: date) -> dict[str, object]:
    # terms, ratings and sector
    return {
        "Для квалов": bond.is_for_qualified_investors,
        "До погашения, лет": round((bond.maturity_date - today) / YEAR, 2)
        if bond.maturity_date
        else None,
        "T-Invest": bond.t_invest_rating,
        **{
            label: rating(bond.agency_ratings.get(agency))
            for agency, label in AGENCY_LABELS.items()
        },
        "МСФО": rating(bond.ifrs_rating),
        "Сектор": bond.sector,
    }


COLUMN_CONFIG = {
    "YTM": st.column_config.NumberColumn(format="%.2f%%"),
    "Последняя цена": st.column_config.NumberColumn(format="%.2f"),
    "Лучшее предложение": st.column_config.NumberColumn(format="%.2f"),
}

FIXED_COUPON_COLUMN_CONFIG = {
    "YTM по предложению": st.column_config.NumberColumn(format="%.2f%%"),
    "G-спред, п.п.": st.column_config.NumberColumn(format="%.2f"),
    "Дюрация, лет": st.column_config.NumberColumn(format="%.2f"),
}


def fixed_screener_table(
    bonds: list[ScreenerBond], today: date, issuer_investments: dict[str, float]
) -> None:
    st.dataframe(
        [
            {
                **identity_columns(bond, issuer_investments),
                "YTM": bond.ytm,
                **fixed_coupon_columns(bond),
                **price_columns(bond),
                **profile_columns(bond, today),
            }
            for bond in by_issuer_yield(bonds)
        ],
        column_config=COLUMN_CONFIG | FIXED_COUPON_COLUMN_CONFIG,
        hide_index=True,
    )


def floater_screener_table(
    bonds: list[ScreenerBond], today: date, issuer_investments: dict[str, float]
) -> None:
    # floaters have no ask yield, spread or duration
    st.dataframe(
        [
            {
                **identity_columns(bond, issuer_investments),
                "YTM": bond.ytm,
                **price_columns(bond),
                **profile_columns(bond, today),
            }
            for bond in by_issuer_yield(bonds)
        ],
        column_config=COLUMN_CONFIG,
        hide_index=True,
    )


st.title("Облигации")

if st.button("Обновить"):
    load_cash_flows.clear()
    load_screener.clear()

portfolio_tab, fixed_tab, floater_tab = st.tabs(["Портфель", "Фикс ₽", "Флоатеры ₽"])

with portfolio_tab:
    rows = load_cash_flows()

    st.subheader("XIRR за последние 365 дней")
    st.caption(
        "Учитываются только облигации, купленные за период; "
        "текущие позиции оцениваются виртуальной продажей по рыночной цене. "
        "Все суммы в рублях, разбивка по валюте номинала."
    )

    by_currency = group_by(rows, lambda row: row.face_unit)

    for column, (currency, currency_rows) in zip(
        st.columns(max(len(by_currency), 1)), sorted(by_currency.items()), strict=False
    ):
        value = xirr(
            [row.date for row in currency_rows], [row.payment for row in currency_rows]
        )
        column.metric(f"Номинал {currency}", "—" if value is None else f"{value:.2%}")

    total = sum(row.payment for row in rows)
    # tax is only due on a profit
    net = total * (1 - TAX_RATE) if total > 0 else total

    st.subheader("Доход за последние 365 дней")
    income, income_after_tax = st.columns(2)
    income.metric("Сумма денежных потоков", f"{total:,.2f} ₽".replace(",", " "))
    income_after_tax.metric(
        f"После налога {TAX_RATE:.0%}", f"{net:,.2f} ₽".replace(",", " ")
    )

    held_bonds = [
        bond_rows
        for bond_rows in group_by(rows, lambda row: row.ticker).values()
        if holding_days(bond_rows) >= MIN_HOLDING_DAYS
    ]
    bond_xirrs = [
        xirr(
            [row.date for row in bond_rows],
            [row.payment for row in bond_rows],
            silent=True,
        )
        for bond_rows in held_bonds
    ]

    bond_stats = [
        {
            "Наименование": bond_rows[0].bond_name,
            "Итог, ₽": round(sum(row.payment for row in bond_rows), 2),
            "XIRR": bond_xirr,
            "Дней в портфеле": holding_days(bond_rows),
            "Номинал": bond_rows[0].face_unit,
        }
        for bond_rows, bond_xirr in sorted(
            zip(held_bonds, bond_xirrs, strict=True),
            # bonds without a solvable XIRR go last
            key=lambda item: (item[1] is None, item[1] or 0.0),
        )
    ]

    with st.expander(f"Итог по облигациям в портфеле от {MIN_HOLDING_DAYS} дней"):
        st.dataframe(
            bond_stats,
            column_config={"XIRR": st.column_config.NumberColumn(format="percent")},
            hide_index=True,
        )

screener_bonds, issuer_investments = load_screener()
today = datetime.now(UTC).date()

with fixed_tab:
    fixed_screener_table(
        [bond for bond in screener_bonds if default_rub_fixed_screener(bond, today)],
        today,
        issuer_investments,
    )

with floater_tab:
    floater_screener_table(
        [bond for bond in screener_bonds if default_rub_floater_screener(bond, today)],
        today,
        issuer_investments,
    )
