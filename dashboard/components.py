# dashboard/components.py
import math
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

def weather_icon(rain_rate, solar_rad, wind_speed):
    rain_rate = _safe_float(rain_rate)
    solar_rad = _safe_float(solar_rad)
    wind_speed = _safe_float(wind_speed)

    if rain_rate is not None and rain_rate >= 1.0:
        return "🌧️", "Rain"
    if rain_rate is not None and rain_rate > 0:
        return "🌦️", "Light rain"
    if solar_rad is not None and solar_rad >= 300:
        return "☀️", "Sunny"
    if wind_speed is not None and wind_speed >= 8:
        return "💨", "Windy"
    return "☁️", "Cloudy"

def wind_icon(wind_speed):
    ws = _safe_float(wind_speed)
    if ws is None:
        return "🧭"
    if ws >= 12:
        return "🌪️"
    if ws >= 8:
        return "💨"
    return "🧭"

def temp_icon(temp_out):
    t = _safe_float(temp_out)
    if t is None:
        return "🌡️"
    if t >= 25:
        return "🔥"
    if t <= 2:
        return "❄️"
    return "🌡️"

def fmt(v, unit="", nd=2):
    if v is None or (isinstance(v, float) and (math.isnan(v) or math.isinf(v))):
        return "—"
    try:
        return f"{float(v):.{nd}f}{unit}"
    except Exception:
        return "—"

def kpi_card(title: str, value: str, subtitle: str = "", icon: str = "•"):
    st.markdown(
        f"""
        <div style="
          padding:16px;
          border-radius:18px;
          border:1px solid rgba(255,255,255,0.12);
          background: rgba(255,255,255,0.08);
          backdrop-filter: blur(10px);
          -webkit-backdrop-filter: blur(10px);
          box-shadow: 0 10px 30px rgba(0,0,0,0.18);
        ">
          <div style="display:flex; align-items:center; gap:10px; margin-bottom:6px;">
            <div style="
              width:34px;height:34px;border-radius:10px;
              display:flex;align-items:center;justify-content:center;
              background: rgba(255,255,255,0.12);
              font-size:18px;
            ">{icon}</div>
            <div style="font-size:0.95rem; color: rgba(255,255,255,0.85); font-weight:600;">
              {title}
            </div>
          </div>

          <div style="font-size:1.75rem; font-weight:800; color: rgba(255,255,255,0.96); line-height:1.15;">
            {value}
          </div>

          <div style="font-size:0.9rem; color: rgba(255,255,255,0.72); margin-top:6px;">
            {subtitle}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def gauge(title: str, value, vmin: float, vmax: float, suffix: str = ""):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        value = 0.0
    value = float(value)

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        number={"suffix": f" {suffix}"},
        title={"text": title},
        gauge={"axis": {"range": [vmin, vmax]}, "bar": {"thickness": 0.25}},
    ))
    fig.update_layout(
        height=210,
        margin=dict(l=10, r=10, t=40, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"),
    )
    return fig

def inject_theme():
    st.markdown(
        """
        <style>
          .stApp {
            background: radial-gradient(1200px 600px at 15% 10%, rgba(80,130,255,0.25), transparent 60%),
                        radial-gradient(900px 500px at 85% 20%, rgba(255,170,80,0.18), transparent 60%),
                        radial-gradient(1000px 600px at 40% 90%, rgba(90,255,170,0.14), transparent 65%),
                        #0b0f1a;
          }
          .stMarkdown, .stText, .stCaption, .stDataFrame { color: rgba(255,255,255,0.92); }
        </style>
        """,
        unsafe_allow_html=True,
    )

def _safe_float(x):
    try:
        if x is None:
            return None
        v = float(x)
        if math.isnan(v) or math.isinf(v):
            return None
        return v
    except Exception:
        return None
