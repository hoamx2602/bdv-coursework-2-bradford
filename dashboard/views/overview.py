import plotly.express as px
import streamlit as st
from dashboard.components import kpi_card, weather_icon, fmt

def render(dfc):
    st.title("Overview")

    c1, c2, c3, c4 = st.columns(4)

    icon, cond = weather_icon(
        dfc["rain_rate"].max() if "rain_rate" in dfc else None,
        dfc["solar_rad"].max() if "solar_rad" in dfc else None,
        dfc["wind_speed"].max() if "wind_speed" in dfc else None,
    )

    with c1:
        kpi_card("Condition (range)", f"{icon} {cond}", "Heuristic from rain/solar/wind", icon="🛰️")
    with c2:
        kpi_card("Avg temp", fmt(dfc["temp_out"].mean(), "°C"), "Mean outdoor temperature", icon="🌡️")
    with c3:
        kpi_card("Max wind", fmt(dfc["wind_speed"].max(), " m/s"), "Peak wind speed", icon="💨")
    with c4:
        rain_total = (dfc["rain"].max() - dfc["rain"].min()) if dfc["rain"].notna().any() else None
        kpi_card("Total rain", fmt(rain_total, " mm"), "Delta of cumulative rain", icon="🌧️")

    st.divider()

    st.subheader("Quick time-series")
    metric = st.selectbox("Metric", ["temp_out", "out_hum", "bar", "wind_speed", "rain_rate", "solar_rad", "uv_index"])
    if metric in dfc.columns:
        fig = px.line(dfc, x="ts", y=metric, title=f"{metric} over time")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info(f"{metric} not available in selected range.")