# dashboard/app.py
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd
import streamlit as st
from sqlalchemy import text

from database.db import get_engine
from dashboard.components import inject_theme

from dashboard.views import overview, daily_snapshot, trends, pca_regimes, extremes, projector_export, andrews_curves

st.set_page_config(page_title="Bradford Weather Dashboard", layout="wide")
inject_theme()

@st.cache_data(ttl=300)
def load_curated_range(date_start: str, date_end: str) -> pd.DataFrame:
    eng = get_engine()
    df = pd.read_sql(
        text("""
            SELECT *
            FROM bradford.weather_curated
            WHERE ts >= :tmin AND ts < :tmax
            ORDER BY ts ASC;
        """),
        eng,
        params={"tmin": date_start, "tmax": date_end},
    )
    df["ts"] = pd.to_datetime(df["ts"], utc=True, errors="coerce")
    return df.dropna(subset=["ts"])

@st.cache_data(ttl=300)
def load_features_range(date_start: str, date_end: str) -> pd.DataFrame:
    eng = get_engine()
    df = pd.read_sql(
        text("""
            SELECT *
            FROM bradford.weather_features
            WHERE ts >= :tmin AND ts < :tmax
            ORDER BY ts ASC;
        """),
        eng,
        params={"tmin": date_start, "tmax": date_end},
    )
    df["ts"] = pd.to_datetime(df["ts"], utc=True, errors="coerce")
    return df.dropna(subset=["ts"])

@st.cache_data(ttl=300)
def get_date_bounds():
    eng = get_engine()
    df = pd.read_sql(text("SELECT MIN(ts) AS min_ts, MAX(ts) AS max_ts FROM bradford.weather_curated;"), eng)
    min_ts = pd.to_datetime(df.loc[0, "min_ts"], utc=True)
    max_ts = pd.to_datetime(df.loc[0, "max_ts"], utc=True)
    return min_ts, max_ts

# Sidebar navigation
st.sidebar.title("🌦️ Bradford Weather")
page = st.sidebar.radio(
    "Navigation",
    ["Overview", "Daily Snapshot", "Trends", "PCA & Regimes", "Andrews Curves", "Extremes", "Projector Export"],
    index=1,
)

min_ts, max_ts = get_date_bounds()
st.sidebar.caption(f"Data range: {min_ts.date()} → {max_ts.date()}")

with st.sidebar.expander("Global filters", expanded=True):
    date_start = st.date_input("Start date", value=min_ts.date(), min_value=min_ts.date(), max_value=max_ts.date())
    date_end = st.date_input("End date (inclusive)", value=max_ts.date(), min_value=min_ts.date(), max_value=max_ts.date())

date_start_ts = pd.Timestamp(date_start).tz_localize("UTC")
date_end_ts = pd.Timestamp(date_end).tz_localize("UTC") + pd.Timedelta(days=1)
range_start, range_end = date_start_ts.isoformat(), date_end_ts.isoformat()

dfc = load_curated_range(range_start, range_end)
dff = load_features_range(range_start, range_end)

# Router
if page == "Overview":
    overview.render(dfc)
elif page == "Daily Snapshot":
    daily_snapshot.render(min_ts, max_ts, load_curated_range)
elif page == "Trends":
    trends.render(dfc)
elif page == "PCA & Regimes":
    pca_regimes.render(dff)
elif page == "Extremes":
    extremes.render(dfc)
elif page == "Andrews Curves":
    andrews_curves.render(dfc, dff)
else:
    projector_export.render(dff)
