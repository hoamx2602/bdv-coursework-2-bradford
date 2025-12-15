# dashboard/views/trends.py
import plotly.express as px
import streamlit as st


def render(dfc):
    st.title("Trends")
    st.caption("Explore longer-term patterns (seasonality, correlations, distributions).")

    t1, t2 = st.tabs(["Seasonality", "Correlation"])

    with t1:
        metric = st.selectbox(
            "Metric",
            ["temp_out", "out_hum", "bar", "rain_rate", "solar_rad", "uv_index"],
            index=0
        )
        if metric in dfc.columns:
            d = dfc.set_index("ts")[metric].resample("D").mean().reset_index()
            fig = px.line(d, x="ts", y=metric, title=f"Daily mean: {metric}")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(f"{metric} not available.")

    with t2:
        numeric_cols = ["temp_out", "out_hum", "bar", "rain_rate", "solar_rad", "uv_index"]
        numeric_cols = [c for c in numeric_cols if c in dfc.columns]
        pick = st.multiselect("Columns", numeric_cols, default=numeric_cols)

        if len(pick) >= 2:
            corr = dfc[pick].corr(numeric_only=True)
            fig = px.imshow(corr, text_auto=True, aspect="auto", title="Correlation heatmap")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Pick at least 2 columns.")
