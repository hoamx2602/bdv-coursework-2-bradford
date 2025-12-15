# dashboard/views/eda_explorer.py
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st


def render(dfc: pd.DataFrame):
    st.title("Data Explorer (EDA)")
    st.caption("Explore any variable: time-series, distribution, and summary statistics.")

    if dfc is None or dfc.empty:
        st.warning("No data available in the selected range. Adjust Global filters.")
        return

    if "ts" not in dfc.columns:
        st.error("Column 'ts' not found in curated data.")
        return

    # Pick numeric columns only (exclude ts)
    numeric_cols = []
    for c in dfc.columns:
        if c == "ts":
            continue
        if pd.api.types.is_numeric_dtype(dfc[c]):
            numeric_cols.append(c)

    if not numeric_cols:
        st.warning("No numeric columns found to explore.")
        return

    # Controls
    colA, colB, colC = st.columns([2, 1, 1], gap="small")
    with colA:
        var = st.selectbox("Select variable", numeric_cols, index=0)
    with colB:
        agg = st.selectbox("Time aggregation", ["Raw", "Hourly mean", "Daily mean"], index=0)
    with colC:
        max_points = st.selectbox("Max points (plot performance)", [2000, 5000, 10000, "All"], index=1)

    # Build series
    d = dfc[["ts", var]].copy()
    d = d.dropna(subset=["ts"])
    d["ts"] = pd.to_datetime(d["ts"], utc=True, errors="coerce")
    d = d.dropna(subset=["ts"]).sort_values("ts")

    # Apply aggregation
    if agg != "Raw":
        freq = "H" if agg == "Hourly mean" else "D"
        d = d.set_index("ts")[var].resample(freq).mean().reset_index()

    # Optional downsample for plotting
    if max_points != "All" and len(d) > int(max_points):
        d = d.iloc[:: max(1, len(d) // int(max_points)), :]

    # Summary stats (use original dfc column, not aggregated)
    s = dfc[var]
    n_total = len(s)
    n_missing = int(s.isna().sum())
    missing_pct = (n_missing / n_total * 100.0) if n_total else 0.0

    s_clean = s.dropna()
    stats = {
        "count": int(s_clean.shape[0]),
        "missing_%": round(missing_pct, 2),
        "mean": float(s_clean.mean()) if len(s_clean) else np.nan,
        "median": float(s_clean.median()) if len(s_clean) else np.nan,
        "std": float(s_clean.std()) if len(s_clean) else np.nan,
        "min": float(s_clean.min()) if len(s_clean) else np.nan,
        "max": float(s_clean.max()) if len(s_clean) else np.nan,
    }

    # Layout
    topL, topR = st.columns([3, 1], gap="small")

    with topL:
        st.subheader("Time series")
        fig_ts = px.line(d, x="ts", y=var, title=f"{var} over time ({agg})")
        st.plotly_chart(fig_ts, use_container_width=True)

    with topR:
        st.subheader("Summary")

        st.markdown(
            f"""
            <div style="
            padding:12px;
            border-radius:14px;
            background: rgba(255,255,255,0.06);
            border: 1px solid rgba(255,255,255,0.10);
            font-size:0.85rem;
            ">
            <table style="width:100%; border-collapse:collapse;">
            <tr><td>Count</td><td style="text-align:right;"><b>{stats['count']:,}</b></td></tr>
            <tr><td>Missing (%)</td><td style="text-align:right;">{stats['missing_%']:.2f}</td></tr>
            <tr><td>Mean</td><td style="text-align:right;">{stats['mean']:.3f}</td></tr>
            <tr><td>Median</td><td style="text-align:right;">{stats['median']:.3f}</td></tr>
            <tr><td>Std</td><td style="text-align:right;">{stats['std']:.3f}</td></tr>
            <tr><td>Min</td><td style="text-align:right;">{stats['min']:.3f}</td></tr>
            <tr><td>Max</td><td style="text-align:right;">{stats['max']:.3f}</td></tr>
            </table>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.divider()

    b1, b2 = st.columns(2, gap="small")
    with b1:
        st.subheader("Distribution")
        # Use cleaned values for distribution
        dist = s_clean
        if len(dist) == 0:
            st.info("No non-missing values for distribution.")
        else:
            # Light sampling for performance
            if len(dist) > 20000:
                dist = dist.sample(20000, random_state=42)
            fig_hist = px.histogram(dist, nbins=40, title=f"Histogram of {var}")
            st.plotly_chart(fig_hist, use_container_width=True)

    with b2:
        st.subheader("Box plot (outliers)")
        dist = s_clean
        if len(dist) == 0:
            st.info("No non-missing values for box plot.")
        else:
            if len(dist) > 20000:
                dist = dist.sample(20000, random_state=42)
            fig_box = px.box(dist, points="outliers", title=f"Box plot of {var}")
            st.plotly_chart(fig_box, use_container_width=True)

    with st.expander("Show data (sample)", expanded=False):
        st.dataframe(dfc[["ts", var]].head(2000), use_container_width=True)
