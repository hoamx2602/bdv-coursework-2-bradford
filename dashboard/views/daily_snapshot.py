# dashboard/views/daily_snapshot.py
import pandas as pd
import plotly.express as px
import streamlit as st

from dashboard.components import kpi_card, gauge, weather_icon, temp_icon, fmt

def _day_slice_to_range(day: pd.Timestamp):
    start = pd.Timestamp(day).tz_localize("UTC")
    end = start + pd.Timedelta(days=1)
    return start.isoformat(), end.isoformat()

def _summarize_day(df_day):
    out = {}
    if df_day.empty:
        return out

    out["temp_mean"] = df_day["temp_out"].mean()
    out["temp_max"] = df_day["temp_out"].max()
    out["temp_min"] = df_day["temp_out"].min()

    out["hum_mean"] = df_day["out_hum"].mean()
    out["bar_mean"] = df_day["bar"].mean()

    out["wind_mean"] = df_day["wind_speed"].mean()
    out["wind_max"] = df_day["wind_speed"].max()
    out["wind_dir_mode"] = df_day["wind_dir"].dropna().mode().iloc[0] if df_day["wind_dir"].dropna().size else None

    out["rain_total"] = df_day["rain"].max() - df_day["rain"].min() if df_day["rain"].notna().any() else None
    out["rain_rate_max"] = df_day["rain_rate"].max()

    out["solar_peak"] = df_day["solar_rad"].max()
    out["uv_peak"] = df_day["uv_index"].max()

    out["icon"], out["condition"] = weather_icon(out.get("rain_rate_max"), out.get("solar_peak"), out.get("wind_max"))
    return out

def render(min_ts, max_ts, load_curated_range):
    st.title("Daily Snapshot")
    st.caption("Professional daily weather summary with balanced layout (hero + gauges + KPI cards).")

    day = st.date_input(
        "Select a day",
        value=min(max_ts.date(), (min_ts + pd.Timedelta(days=7)).date()),
        min_value=min_ts.date(),
        max_value=max_ts.date()
    )

    d0, d1 = _day_slice_to_range(pd.Timestamp(day))
    df_day = load_curated_range(d0, d1)
    summary = _summarize_day(df_day)

    if df_day.empty:
        st.warning("No data found for this day.")
        return

    # -----------------------------
    # Row 1: HERO (balanced 3 columns)
    # -----------------------------
    h1, h2, h3 = st.columns([2.2, 1.2, 1.2], gap="large")

    with h1:
        icon = summary.get("icon", "🌦️")
        cond = summary.get("condition", "—")
        st.markdown(f"## {icon} {cond}")
        st.markdown(f"**{pd.Timestamp(day).strftime('%A, %d %b %Y')}**")

        # Big headline temperature
        st.markdown(
            f"""
            <div style="margin-top:10px; padding:16px; border-radius:18px;
                        border:1px solid rgba(255,255,255,0.12);
                        background: rgba(255,255,255,0.06);">
              <div style="font-size:0.95rem; color: rgba(255,255,255,0.78); font-weight:600;">
                {temp_icon(summary.get("temp_mean"))} Outdoor temperature (mean)
              </div>
              <div style="font-size:2.4rem; font-weight:900; color: rgba(255,255,255,0.98); line-height:1.1; margin-top:6px;">
                {fmt(summary.get("temp_mean"), "°C")}
              </div>
              <div style="margin-top:6px; color: rgba(255,255,255,0.75);">
                Max: <b>{fmt(summary.get("temp_max"), "°C")}</b> &nbsp;&nbsp;|&nbsp;&nbsp;
                Min: <b>{fmt(summary.get("temp_min"), "°C")}</b>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with h2:
        st.subheader("Wind")
        st.plotly_chart(gauge("Max wind", summary.get("wind_max"), 0, 25, "m/s"), use_container_width=True)
        st.caption(f"Direction (mode): {fmt(summary.get('wind_dir_mode'), '°', nd=0)}")

    with h3:
        st.subheader("Rain & UV")
        st.plotly_chart(gauge("Max rain rate", summary.get("rain_rate_max"), 0, 20, "mm/h"), use_container_width=True)
        st.plotly_chart(gauge("UV peak", summary.get("uv_peak"), 0, 12, ""), use_container_width=True)

    st.divider()

    # -----------------------------
    # Row 2: KPI CARDS (uniform height feel)
    # -----------------------------
    k1, k2, k3, k4, k5 = st.columns(5, gap="large")
    with k1:
        kpi_card("Humidity", fmt(summary.get("hum_mean"), "%"), "Daily mean", icon="💧")
    with k2:
        kpi_card("Pressure", fmt(summary.get("bar_mean"), " hPa"), "Daily mean", icon="🧱")
    with k3:
        kpi_card("Rain total", fmt(summary.get("rain_total"), " mm"), "Daily accumulation (delta)", icon="🌧️")
    with k4:
        kpi_card("Solar peak", fmt(summary.get("solar_peak"), ""), "Peak solar radiation", icon="☀️")
    with k5:
        # wind mean as a card (wind max already gauge)
        kpi_card("Wind (mean)", fmt(summary.get("wind_mean"), " m/s"), "Daily mean", icon="🧭")

    st.divider()

    # -----------------------------
    # Row 3: Detailed tabs
    # -----------------------------
    tab_a, tab_b, tab_c = st.tabs(["Hourly curves", "Wind & Rain detail", "Raw table"])

    with tab_a:
        cols = ["temp_out", "out_hum", "bar", "solar_rad", "uv_index", "wind_speed", "rain_rate"]
        cols = [c for c in cols if c in df_day.columns]
        pick = st.multiselect("Select series", cols, default=[c for c in ["temp_out", "out_hum", "bar"] if c in cols])
        if pick:
            df_long = df_day[["ts"] + pick].melt(id_vars=["ts"], var_name="metric", value_name="value")
            fig = px.line(df_long, x="ts", y="value", color="metric", title="Within-day evolution")
            st.plotly_chart(fig, use_container_width=True)

    with tab_b:
        left, right = st.columns(2, gap="large")
        with left:
            if "wind_speed" in df_day.columns:
                fig = px.line(df_day, x="ts", y="wind_speed", title="Wind speed")
                st.plotly_chart(fig, use_container_width=True)
        with right:
            if "rain_rate" in df_day.columns:
                fig = px.bar(df_day, x="ts", y="rain_rate", title="Rain rate")
                st.plotly_chart(fig, use_container_width=True)

    with tab_c:
        st.dataframe(df_day, use_container_width=True)
