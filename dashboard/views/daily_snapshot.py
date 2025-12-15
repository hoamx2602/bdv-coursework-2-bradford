# dashboard/views/daily_snapshot.py
import pandas as pd
import plotly.express as px
import streamlit as st

from dashboard.components import kpi_card, gauge, weather_icon, temp_icon, fmt


def _day_slice_to_range(day: pd.Timestamp):
    start = pd.Timestamp(day).tz_localize("UTC")
    end = start + pd.Timedelta(days=1)
    return start.isoformat(), end.isoformat()


def _summarize_day(df_day: pd.DataFrame) -> dict:
    out = {}
    if df_day.empty:
        return out

    out["temp_mean"] = df_day["temp_out"].mean() if "temp_out" in df_day else None
    out["temp_max"] = df_day["temp_out"].max() if "temp_out" in df_day else None
    out["temp_min"] = df_day["temp_out"].min() if "temp_out" in df_day else None

    out["hum_mean"] = df_day["out_hum"].mean() if "out_hum" in df_day else None
    out["bar_mean"] = df_day["bar"].mean() if "bar" in df_day else None

    out["rain_total"] = (
        df_day["rain"].max() - df_day["rain"].min()
        if "rain" in df_day and df_day["rain"].notna().any()
        else None
    )
    out["rain_rate_max"] = df_day["rain_rate"].max() if "rain_rate" in df_day else None

    out["solar_peak"] = df_day["solar_rad"].max() if "solar_rad" in df_day else None
    out["uv_peak"] = df_day["uv_index"].max() if "uv_index" in df_day else None

    # wind is unavailable -> pass None
    out["icon"], out["condition"] = weather_icon(out.get("rain_rate_max"), out.get("solar_peak"), None)
    return out


def render(min_ts, max_ts, load_curated_range):
    st.title("Daily Snapshot")
    st.caption("Daily summary layout (wind excluded due to sensor unavailability).")

    day = st.date_input(
        "Select a day",
        value=min(max_ts.date(), (min_ts + pd.Timedelta(days=7)).date()),
        min_value=min_ts.date(),
        max_value=max_ts.date(),
    )

    d0, d1 = _day_slice_to_range(pd.Timestamp(day))
    df_day = load_curated_range(d0, d1)
    summary = _summarize_day(df_day)

    if df_day.empty:
        st.warning("No data found for this day.")
        return

    # -----------------------------
    # Header
    # -----------------------------
    icon = summary.get("icon", "🌦️")
    cond = summary.get("condition", "—")
    st.markdown(f"### {icon} {cond} — {pd.Timestamp(day).strftime('%A, %d %b %Y')}")

    st.divider()

    # -----------------------------
    # Row 1: 5 KPI blocks (single row)
    # -----------------------------
    c1, c2, c3, c4 = st.columns(4, gap="small")

    with c1:
        kpi_card(
            "Outdoor Temperature",
            fmt(summary.get("temp_mean"), "°C"),
            f"max {fmt(summary.get('temp_max'),'°C')} | min {fmt(summary.get('temp_min'),'°C')}",
            icon=temp_icon(summary.get("temp_mean")),
        )

    with c2:
        kpi_card("Humidity", fmt(summary.get("hum_mean"), "%"), "Daily mean", icon="💧")

    with c3:
        kpi_card("Pressure", fmt(summary.get("bar_mean"), " hPa"), "Daily mean", icon="🧱")

    with c4:
        kpi_card("Rain total", fmt(summary.get("rain_total"), " mm"), "Daily accumulation (delta)", icon="🌧️")

    st.divider()

    # -----------------------------
    # Row 2: 3 Gauges (single row)
    # -----------------------------
    g1, g2, g3 = st.columns(3, gap="large")

    with g1:
        st.plotly_chart(gauge("Max rain rate", summary.get("rain_rate_max"), 0, 20, "mm/h"), use_container_width=True)

    with g2:
        st.plotly_chart(gauge("Solar peak", summary.get("solar_peak"), 0, 1200, ""), use_container_width=True)

    with g3:
        st.plotly_chart(gauge("UV peak", summary.get("uv_peak"), 0, 12, ""), use_container_width=True)

    st.divider()

    # -----------------------------
    # Detail tabs (unchanged)
    # -----------------------------
    tab_a, tab_b, tab_c = st.tabs(["Hourly curves", "Rain detail", "Raw table"])

    with tab_a:
        cols = ["temp_out", "out_hum", "bar", "solar_rad", "uv_index", "rain_rate"]
        cols = [c for c in cols if c in df_day.columns]
        default_pick = [c for c in ["temp_out", "out_hum", "bar"] if c in cols]
        pick = st.multiselect("Select series", cols, default=default_pick)

        if pick:
            df_long = df_day[["ts"] + pick].melt(id_vars=["ts"], var_name="metric", value_name="value")
            fig = px.line(df_long, x="ts", y="value", color="metric", title="Within-day evolution")
            st.plotly_chart(fig, use_container_width=True)

    with tab_b:
        if "rain_rate" in df_day.columns:
            fig = px.bar(df_day, x="ts", y="rain_rate", title="Rain rate")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("rain_rate not available for this day.")

    with tab_c:
        st.dataframe(df_day, use_container_width=True)
