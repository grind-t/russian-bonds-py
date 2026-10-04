import asyncio
import os
from datetime import UTC, datetime, timedelta

import httpx
import streamlit as st
from pyxirr import xirr
from t_tech.invest import AsyncClient

from russian_bonds import BondCashFlow, get_account_bond_cash_flows

PERIOD = timedelta(days=365)
TAX_RATE = 0.13
MIN_HOLDING_DAYS = 60


async def fetch_cash_flows(from_: datetime) -> list[BondCashFlow]:
    async with (
        AsyncClient(os.environ["T_INVEST_READONLY_TOKEN"]) as t_invest_client,
        httpx.AsyncClient(
            limits=httpx.Limits(max_connections=10),
            timeout=httpx.Timeout(10.0, pool=None),
        ) as moex_client,
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


st.title("Облигации")

if st.button("Обновить"):
    load_cash_flows.clear()

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
        [row.date for row in currency_rows], [row.value for row in currency_rows]
    )
    column.metric(f"Номинал {currency}", "—" if value is None else f"{value:.2%}")

total = sum(row.value for row in rows)
# tax is only due on a profit
net = total * (1 - TAX_RATE) if total > 0 else total

st.subheader("Доход за последние 365 дней")
income, income_after_tax = st.columns(2)
income.metric("Сумма денежных потоков", f"{total:,.2f} ₽".replace(",", " "))
income_after_tax.metric(
    f"После налога {TAX_RATE:.0%}", f"{net:,.2f} ₽".replace(",", " ")
)


def holding_days(bond_rows: list[BondCashFlow]) -> int:
    dates = [row.date for row in bond_rows]
    return (max(dates) - min(dates)).days


by_bond: dict[tuple[str, str], list[BondCashFlow]] = {}
for row in rows:
    by_bond.setdefault((row.bond_name, row.face_unit), []).append(row)

bond_xirrs = {
    key: xirr(
        [row.date for row in bond_rows],
        [row.value for row in bond_rows],
        silent=True,
    )
    for key, bond_rows in by_bond.items()
}

bond_stats = [
    {
        "Наименование": name,
        "Итог, ₽": round(sum(row.value for row in bond_rows), 2),
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
