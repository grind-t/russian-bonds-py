import asyncio
import os
from datetime import UTC, datetime, timedelta

import httpx
import streamlit as st
from cbr_ratings import KraCode
from pyxirr import xirr
from t_tech.invest import AsyncClient

from russian_bonds import (
    BondCashFlow,
    CreditRating,
    ScreenerBond,
    get_account_bond_cash_flows,
    get_issuer_investments,
    get_screener_bonds,
    is_foreign_currency_candidate,
    is_rub_candidate,
)

PERIOD = timedelta(days=365)
TAX_RATE = 0.13
MIN_HOLDING_DAYS = 60
DAYS_PER_YEAR = 365.25


def http_client() -> httpx.AsyncClient:
    return httpx.AsyncClient(
        limits=httpx.Limits(max_connections=10),
        timeout=httpx.Timeout(10.0, pool=None),
    )


async def fetch_cash_flows(from_: datetime) -> list[BondCashFlow]:
    async with (
        AsyncClient(os.environ["T_INVEST_READONLY_TOKEN"]) as t_invest_client,
        http_client() as moex_client,
    ):
        return await get_account_bond_cash_flows(
            t_invest_client=t_invest_client,
            moex_client=moex_client,
            account_id=os.environ["T_INVEST_ACCOUNT_ID"],
            from_=from_,
        )


@st.cache_data(ttl=timedelta(hours=1), show_spinner="Загрузка операций...")
def load_cash_flows() -> list[BondCashFlow]:
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


def holding_days(bond_rows: list[BondCashFlow]) -> int:
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


def screener_table(
    bonds: list[ScreenerBond], issuer_investments: dict[str, float] | None = None
) -> None:
    # issuers by their best yield, so bonds of one issuer stay together
    max_ytm_by_issuer: dict[str | None, float] = {}
    for bond in bonds:
        assert bond.ytm is not None
        max_ytm_by_issuer[bond.issuer_inn] = max(
            bond.ytm, max_ytm_by_issuer.get(bond.issuer_inn, bond.ytm)
        )
    bonds = sorted(
        bonds,
        key=lambda bond: (
            max_ytm_by_issuer[bond.issuer_inn],
            bond.issuer_inn or "",
            bond.ytm,
        ),
        reverse=True,
    )
    today = datetime.now(UTC).date()
    st.dataframe(
        [
            {
                "Наименование": bond.name,
                "ISIN": bond.isin,
                "ИНН эмитента": bond.issuer_inn,
                **(
                    {}
                    if issuer_investments is None
                    else {
                        "Вложено в эмитента, ₽": round(
                            issuer_investments.get(bond.issuer_inn or "", 0.0), 2
                        )
                    }
                ),
                "YTM": bond.ytm,
                "Последняя цена": bond.last_price,
                "Лучшее предложение": bond.best_ask_price,
                "Валюта": bond.currency.upper(),
                "Флоатер": bond.is_floater,
                "Амортизация": bond.has_amortization,
                "Для квалов": bond.is_for_qualified_investors,
                "До погашения, лет": round(
                    (bond.maturity_date - today).days / DAYS_PER_YEAR, 2
                )
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
            for bond in bonds
        ],
        column_config={
            "YTM": st.column_config.NumberColumn(format="%.2f%%"),
            "Последняя цена": st.column_config.NumberColumn(format="%.2f"),
            "Лучшее предложение": st.column_config.NumberColumn(format="%.2f"),
        },
        hide_index=True,
    )


st.title("Облигации")

if st.button("Обновить"):
    load_cash_flows.clear()
    load_screener.clear()

portfolio_tab, rub_tab, foreign_currency_tab = st.tabs(
    ["Портфель", "Скринер ₽", "Скринер валютных"]
)

with portfolio_tab:
    rows = load_cash_flows()

    st.subheader("XIRR за последние 365 дней")
    st.caption(
        "Учитываются только облигации, купленные за период; "
        "текущие позиции оцениваются виртуальной продажей по рыночной цене. "
        "Все суммы в рублях, разбивка по валюте номинала."
    )

    by_currency: dict[str, list[BondCashFlow]] = {}
    for row in rows:
        by_currency.setdefault(row.face_unit, []).append(row)

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

    by_bond: dict[tuple[str, str], list[BondCashFlow]] = {}
    for row in rows:
        by_bond.setdefault((row.bond_name, row.face_unit), []).append(row)

    bond_xirrs = {
        key: xirr(
            [row.date for row in bond_rows],
            [row.payment for row in bond_rows],
            silent=True,
        )
        for key, bond_rows in by_bond.items()
    }

    bond_stats = [
        {
            "Наименование": name,
            "Итог, ₽": round(sum(row.payment for row in bond_rows), 2),
            "XIRR": bond_xirrs[name, currency],
            "Дней в портфеле": holding_days(bond_rows),
            "Номинал": currency,
        }
        for (name, currency), bond_rows in sorted(
            # bonds without a solvable XIRR go last
            by_bond.items(),
            key=lambda item: (bond_xirrs[item[0]] is None, bond_xirrs[item[0]] or 0.0),
        )
        if holding_days(bond_rows) >= MIN_HOLDING_DAYS
    ]

    with st.expander(f"Итог по облигациям в портфеле от {MIN_HOLDING_DAYS} дней"):
        st.dataframe(
            bond_stats,
            column_config={"XIRR": st.column_config.NumberColumn(format="percent")},
            hide_index=True,
        )

screener_bonds, issuer_investments = load_screener()
today = datetime.now(UTC).date()

with rub_tab:
    st.caption(
        "Рублёвые облигации без оферты, погашение через 3 месяца – 2 года, "
        "доходность от 15.5% (у флоатеров выше с ростом срока), "
        "вложения в эмитента до 100 000 ₽, надёжный рейтинг."
    )
    screener_table(
        [
            bond
            for bond in screener_bonds
            if is_rub_candidate(
                bond, issuer_investments.get(bond.issuer_inn or "", 0.0), today
            )
        ],
        issuer_investments,
    )

with foreign_currency_tab:
    st.caption(
        "Валютные облигации без оферты, погашение через 3 месяца – 2 года, "
        "доходность от 7%, надёжный рейтинг."
    )
    screener_table(
        [bond for bond in screener_bonds if is_foreign_currency_candidate(bond, today)]
    )
