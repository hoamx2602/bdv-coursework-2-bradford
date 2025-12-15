import plotly.express as px
import streamlit as st

def render(dfc):
    st.title("Extremes")
    st.caption("Identify extreme weather moments (top-N peaks by selected metric).")

    metric = st.selectbox("Extreme metric", ["rain_rate","wind_speed","temp_out","solar_rad","uv_index"], index=0)
    n = st.slider("Top N", 5, 50, 15)

    if metric not in dfc.columns:
        st.warning(f"{metric} not available.")
        return

    top = dfc[["ts", metric]].dropna().sort_values(metric, ascending=False).head(n)
    st.dataframe(top, use_container_width=True)
    fig = px.bar(top.sort_values("ts"), x="ts", y=metric, title=f"Top {n} extremes: {metric}")
    st.plotly_chart(fig, use_container_width=True)
