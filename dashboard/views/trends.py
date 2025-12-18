# dashboard/views/trends.py
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st


CORE_COLS = ["temp_out", "out_hum", "bar", "rain_rate", "solar_rad", "uv_index", "dew_pt"]


def _available_cols(dfc):
    return [c for c in CORE_COLS if c in dfc.columns]


def render(dfc):
    st.title("Trends")
    st.caption("Explore seasonality and relationships between key weather variables (correlation = association, not causality).")

    cols = _available_cols(dfc)
    if len(cols) < 2:
        st.warning("Not enough columns available in this range.")
        return

    tab1, tab2 = st.tabs(["Seasonality", "Correlation Heatmap"])

    # -----------------------------
    # Tab 1: Seasonality
    # -----------------------------
    with tab1:
        metric = st.selectbox("Metric", cols, index=0)
        if metric in dfc.columns:
            d = dfc.set_index("ts")[metric].resample("D").mean().reset_index()
            fig = px.line(d, x="ts", y=metric, title=f"Daily mean: {metric}")
            st.plotly_chart(fig, use_container_width=True)

    # -----------------------------
    # Tab 2: Correlation heatmap (overall view)
    # -----------------------------
    with tab2:
        pick = st.multiselect("Columns", cols, default=cols)
        if len(pick) >= 2:
            corr = dfc[pick].corr(numeric_only=True)
            fig = px.imshow(corr, text_auto=True, aspect="auto", title="Correlation heatmap (Pearson r)")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Pick at least 2 columns.")
