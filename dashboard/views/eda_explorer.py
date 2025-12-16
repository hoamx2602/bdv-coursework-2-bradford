# dashboard/views/eda_explorer.py
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


def render(dfc: pd.DataFrame):
    st.title("Data Explorer (EDA)")
    st.caption("Explore any variable: time-series, distribution, and advanced physical relationships.")

    if dfc is None or dfc.empty:
        st.warning("No data available in the selected range. Adjust Global filters.")
        return

    if "ts" not in dfc.columns:
        st.error("Column 'ts' not found in curated data.")
        return

    # Create 3 tabs: existing + 2 new
    tab_var, tab_diurnal, tab_lag = st.tabs(
        ["Variable Explorer", "Diurnal Cycle", "Thermal Lag"]
    )

    # =====================================================
    # TAB 1: Variable Explorer (KEEP YOUR CURRENT LOGIC)
    # =====================================================
    with tab_var:
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
            dist = s_clean
            if len(dist) == 0:
                st.info("No non-missing values for distribution.")
            else:
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

    # =====================================================
    # TAB 2: Diurnal Cycle (Average by Hour)
    # =====================================================
    with tab_diurnal:
        st.subheader("Diurnal Cycle (Average by Hour)")
        st.caption(
            "Average 24-hour profiles reveal daily forcing effects. "
            "Compare shapes rather than absolute magnitudes."
        )

        # Select numeric variables
        numeric_cols = [
            c for c in dfc.columns
            if c != "ts" and pd.api.types.is_numeric_dtype(dfc[c])
        ]

        if len(numeric_cols) < 1:
            st.warning("No numeric variables available.")
        else:
            vars_sel = st.multiselect(
                "Select variables to compare",
                options=numeric_cols,
                default=[c for c in ["solar_rad", "temp_out"] if c in numeric_cols],
                help="Choose 1–3 variables for clarity."
            )

            if len(vars_sel) == 0:
                st.info("Select at least one variable.")
            elif len(vars_sel) > 4:
                st.warning("Please select no more than 4 variables for readability.")
            else:
                d = dfc[["ts"] + vars_sel].dropna(subset=["ts"]).copy()
                d["ts"] = pd.to_datetime(d["ts"], utc=True, errors="coerce")
                d = d.dropna(subset=["ts"])

                d["hour"] = d["ts"].dt.hour
                g = d.groupby("hour")[vars_sel].mean(numeric_only=True).reset_index()

                fig = go.Figure()
                for v in vars_sel:
                    fig.add_trace(
                        go.Scatter(
                            x=g["hour"],
                            y=g[v],
                            mode="lines+markers",
                            name=v
                        )
                    )

                fig.update_layout(
                    title="Diurnal Cycle (Average by Hour)",
                    xaxis_title="Hour of day (0–23)",
                    yaxis_title="Average value",
                    legend_title="Variable",
                )

                st.plotly_chart(fig, use_container_width=True)

                st.info(
                    "This plot supports interpretation of diurnal structure. "
                    "In the report, Solar_Rad and Temp_Out are used to justify the physical meaning of PC1."
                )

    # =====================================================
    # TAB 3: Thermal Lag (Cross-Correlation)
    # =====================================================
    with tab_lag:
        st.subheader("Thermal Lag (Cross-Correlation)")
        st.caption("Cross-correlation between Solar_Rad and Indoor Temperature to quantify lag.")

        # Handle naming differences for indoor temperature
        # Your dataset/schema may use temp_in OR in_temp OR in_temp
        indoor_candidates = [c for c in ["temp_in", "in_temp", "in_temp_in", "in_temperature"] if c in dfc.columns]
        if "solar_rad" not in dfc.columns:
            st.warning("Missing required column: solar_rad")
            return
        if not indoor_candidates:
            st.warning("No indoor temperature column found. Expected one of: temp_in / in_temp")
            return

        indoor_col = st.selectbox("Indoor temperature column", indoor_candidates, index=0)
        max_lag = st.slider("Max lag (hours)", 1, 24, 12)

        # Prepare data: resample to hourly mean to stabilise signal
        d = dfc[["ts", "solar_rad", indoor_col]].dropna(subset=["ts"]).copy()
        d["ts"] = pd.to_datetime(d["ts"], utc=True, errors="coerce")
        d = d.dropna(subset=["ts"]).sort_values("ts")

        d = d.set_index("ts")[["solar_rad", indoor_col]].resample("H").mean()

        # Compute cross-correlation Solar_Rad(t) vs Indoor(t+lag)
        lags = list(range(-max_lag, max_lag + 1))
        corrs = []
        for lag in lags:
            corrs.append(d["solar_rad"].corr(d[indoor_col].shift(lag)))

        fig = px.line(
            x=lags,
            y=corrs,
            labels={"x": "Lag (hours)", "y": "Pearson correlation"},
            title=f"Cross-Correlation: Solar_Rad vs {indoor_col}",
        )
        st.plotly_chart(fig, use_container_width=True)

        # Peak lag (ignore NaNs safely)
        if all(pd.isna(c) for c in corrs):
            st.warning("Unable to compute correlation (insufficient overlap after resampling).")
        else:
            idx = int(np.nanargmax(corrs))
            peak_lag = lags[idx]
            peak_corr = corrs[idx]
            st.success(f"Peak correlation at lag = {peak_lag} hours (r = {peak_corr:.2f})")
            st.info("In the report, interpret positive peak lag as indoor temperature responding after solar forcing.")
