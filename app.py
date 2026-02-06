import json
from datetime import datetime
from typing import Dict, List, Tuple

import altair as alt
import pandas as pd
import requests
import streamlit as st

st.set_page_config(page_title="NBU Open Data Dashboard", layout="wide")

CATEGORIES: Dict[str, List[Dict[str, str]]] = {
    "Макро індикатори": [
        {
            "name": "Офіційні курси валют (щоденно)",
            "url": "https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?json",
        },
        {
            "name": "Облікова ставка НБУ",
            "url": "https://bank.gov.ua/NBUStatService/v1/statdirectory/discount?json",
        },
        {
            "name": "Ставки за операціями НБУ",
            "url": "https://bank.gov.ua/NBUStatService/v1/statdirectory/interest?json",
        },
    ],
    "Фінансові ринки": [
        {
            "name": "Кредити за класами",
            "url": "https://bank.gov.ua/NBUStatService/v1/statdirectory/credit?json",
        },
        {
            "name": "Депозити",
            "url": "https://bank.gov.ua/NBUStatService/v1/statdirectory/deposit?json",
        },
    ],
    "Банки": [
        {
            "name": "Реєстр банків",
            "url": "https://bank.gov.ua/NBUStatService/v1/statdirectory/bank?json",
        }
    ],
    "Міжнародні фінанси": [
        {
            "name": "Офіційні резерви",
            "url": "https://bank.gov.ua/NBUStatService/v1/statdirectory/res?json",
        }
    ],
    "Ринки капіталу": [
        {
            "name": "Цінні папери (реєстр)",
            "url": "https://bank.gov.ua/NBUStatService/v1/statdirectory/securities?json",
        }
    ],
}

st.title("NBU Open Data Dashboard")
st.markdown(
    """
Цей дашборд автоматично підтягує відкриті дані НБУ та будує базову аналітику.
Оберіть декілька наборів даних, щоб отримати порівняльну статистику й графіки.
"""
)


@st.cache_data(ttl=900)
def fetch_data(url: str) -> Tuple[pd.DataFrame, str]:
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    text = response.text
    try:
        payload = response.json()
    except json.JSONDecodeError:
        payload = json.loads(text)
    df = pd.json_normalize(payload)
    return df, datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")


def detect_date_column(df: pd.DataFrame) -> str | None:
    for col in df.columns:
        if "date" in col.lower() or col.lower().endswith("dt"):
            return col
    return None


def render_dataset(name: str, df: pd.DataFrame) -> None:
    st.subheader(name)
    st.write(f"Записів: **{len(df):,}**, Полів: **{len(df.columns)}**")

    date_col = detect_date_column(df)
    numeric_cols = df.select_dtypes(include="number").columns.tolist()

    if date_col:
        df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
        if numeric_cols:
            metric = st.selectbox(
                "Показник для динаміки",
                numeric_cols,
                key=f"metric_{name}",
            )
            chart = (
                alt.Chart(df.dropna(subset=[date_col, metric]))
                .mark_line(point=True)
                .encode(
                    x=alt.X(f"{date_col}:T", title="Дата"),
                    y=alt.Y(f"{metric}:Q", title=metric),
                    tooltip=[date_col, metric],
                )
                .properties(height=260)
            )
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("У цьому наборі немає числових полів для побудови графіка.")
    else:
        if numeric_cols:
            metric = st.selectbox(
                "Показник для розподілу",
                numeric_cols,
                key=f"dist_{name}",
            )
            chart = (
                alt.Chart(df.dropna(subset=[metric]))
                .mark_bar()
                .encode(x=alt.X(f"{metric}:Q", bin=True), y="count()")
                .properties(height=260)
            )
            st.altair_chart(chart, use_container_width=True)

    if numeric_cols:
        st.write("**Описова статистика**")
        st.dataframe(df[numeric_cols].describe().T, use_container_width=True)

    st.write("**Приклад даних**")
    st.dataframe(df.head(50), use_container_width=True)


with st.sidebar:
    st.header("Налаштування")
    st.markdown("Оберіть набори даних за категоріями.")
    selected_urls = []
    for category, datasets in CATEGORIES.items():
        with st.expander(category, expanded=False):
            for item in datasets:
                if st.checkbox(item["name"], key=item["url"]):
                    selected_urls.append((item["name"], item["url"]))

    st.divider()
    st.markdown("**Додатковий набір**")
    custom_name = st.text_input("Назва набору")
    custom_url = st.text_input("URL JSON")
    if custom_url:
        selected_urls.append((custom_name or "Custom dataset", custom_url))


if not selected_urls:
    st.info("Оберіть хоча б один набір у бічному меню, щоб побачити аналітику.")
    st.stop()

summary_rows = []

for name, url in selected_urls:
    with st.spinner(f"Завантаження: {name}"):
        try:
            df, fetched_at = fetch_data(url)
        except Exception as exc:  # noqa: BLE001
            st.error(f"Не вдалося завантажити {name}: {exc}")
            continue

    summary_rows.append(
        {
            "Набір": name,
            "URL": url,
            "Записів": len(df),
            "Полів": len(df.columns),
            "Оновлено": fetched_at,
        }
    )

st.markdown("## Зведення по вибраних наборах")
st.dataframe(pd.DataFrame(summary_rows), use_container_width=True)

st.divider()

for name, url in selected_urls:
    with st.spinner(f"Аналітика: {name}"):
        try:
            df, _ = fetch_data(url)
        except Exception:
            continue
    render_dataset(name, df)
