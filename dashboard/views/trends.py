# dashboard/views/trends.py
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st


CORE_COLS = ["temp_out", "out_hum", "bar", "rain_rate", "solar_rad", "uv_index"]


def _available_cols(dfc):
    return [c for c in CORE_COLS if c in dfc.columns]


def render(dfc):
    st.title("Trends")
    st.caption("Explore seasonality and relationships between key weather variables (correlation = association, not causality).")

    cols = _available_cols(dfc)
    if len(cols) < 2:
        st.warning("Not enough columns available in this range.")
        return

    tab1, tab2, tab3 = st.tabs(["Seasonality", "Correlation Heatmap", "Relationships (Impact-style)"])

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

    # -----------------------------
    # Tab 3: Relationship-focused plots
    # -----------------------------
    with tab3:
        st.subheader("Relationship explorer")
        st.caption("Use this to show expected weather relationships (e.g., humidity often decreases as temperature increases).")

        left, right = st.columns([1.2, 1], gap="small")

        with left:
            x_var = st.selectbox("X variable", cols, index=cols.index("temp_out") if "temp_out" in cols else 0)
            y_var = st.selectbox("Y variable", cols, index=cols.index("out_hum") if "out_hum" in cols else 1)

            # sample for performance if huge
            df_xy = dfc[["ts", x_var, y_var]].dropna()
            if len(df_xy) > 5000:
                df_xy = df_xy.sample(5000, random_state=42)

            # Pearson r for annotation
            r = df_xy[[x_var, y_var]].corr(numeric_only=True).iloc[0, 1]
            r_txt = "—" if pd.isna(r) else f"{r:.2f}"

            fig_scatter = px.scatter(
                df_xy,
                x=x_var,
                y=y_var,
                trendline="ols",
                title=f"{y_var} vs {x_var} (trendline) | Pearson r = {r_txt}",
            )
            st.plotly_chart(fig_scatter, use_container_width=True)

        with right:
            st.subheader("Correlation strength (ranking)")
            st.caption("Ranks variables by |correlation| with a chosen target. This is 'association strength', not causality.")

            target = st.selectbox("Target variable", cols, index=cols.index("temp_out") if "temp_out" in cols else 0)

            df_num = dfc[cols].dropna()
            if len(df_num) < 10:
                st.warning("Not enough complete rows to compute correlation ranking.")
            else:
                c = df_num.corr(numeric_only=True)[target].drop(target).dropna()
                out = pd.DataFrame({
                    "feature": c.index,
                    "corr_r": c.values,
                    "abs_r": np.abs(c.values),
                    "direction": np.where(c.values >= 0, "positive", "negative"),
                }).sort_values("abs_r", ascending=False)

                fig_rank = px.bar(
                    out,
                    x="abs_r",
                    y="feature",
                    orientation="h",
                    color="direction",
                    title=f"Association strength with {target} (|r|)",
                )
                st.plotly_chart(fig_rank, use_container_width=True)

                st.dataframe(
                    out[["feature", "corr_r", "abs_r", "direction"]].round(3),
                    use_container_width=True,
                )

        st.divider()

        st.subheader("How to interpret (write in report)")
        st.markdown(
            """
- **Pearson correlation (r)** measures **linear association** between two variables.
- **r < 0**: as X increases, Y tends to decrease (e.g., humidity vs temperature often negative).
- **r > 0**: as X increases, Y tends to increase.
- High **|r|** indicates a stronger association, but **does not prove causality**.
            """
        )
