import pandas as pd
from sqlalchemy import text
from database.db import get_engine
from configs.columns import CSV_TO_CURATED

# Columns in curated table (must match schema.sql)
CURATED_COLS = [
    "ts", "csv_date", "csv_time",
    "temp_out", "hi_temp", "low_temp", "dew_pt", "wind_chill", "heat_index", "thw_index", "thsw_index",
    "out_hum",
    "wind_speed", "wind_dir", "wind_run", "hi_speed", "hi_dir", "wind_samp", "wind_tx",
    "bar",
    "rain", "rain_rate",
    "solar_rad", "solar_energy", "hi_solar_rad",
    "uv_index", "uv_dose", "hi_uv",
    "heat_dd", "cool_dd",
    "in_temp", "in_hum", "in_dew", "in_heat", "in_emc", "inair_density",
    "et",
    "iss_recept", "arc_int"
]

NUMERIC_COLS = [c for c in CURATED_COLS if c not in ("ts", "csv_date", "csv_time")]

def load_raw() -> pd.DataFrame:
    eng = get_engine()
    df = pd.read_sql("SELECT ts, payload FROM bradford.weather_raw ORDER BY ts ASC;", eng)
    payload = pd.json_normalize(df["payload"])
    out = pd.concat([df[["ts"]], payload], axis=1)
    return out

def build_curated(raw: pd.DataFrame) -> pd.DataFrame:
    curated = pd.DataFrame()
    curated["ts"] = pd.to_datetime(raw["ts"], utc=True, errors="coerce")

    # Keep original Date/Time for traceability
    # Date format is dd/mm/yyyy in your dataset
    if "Date" in raw.columns:
        curated["csv_date"] = pd.to_datetime(raw["Date"], dayfirst=True, errors="coerce").dt.date
    else:
        curated["csv_date"] = pd.NaT

    if "Time" in raw.columns:
        curated["csv_time"] = pd.to_datetime(raw["Time"], format="%H:%M", errors="coerce").dt.time
    else:
        curated["csv_time"] = pd.NaT

    # Map all dataset fields to curated columns
    for csv_col, curated_col in CSV_TO_CURATED.items():
        curated[curated_col] = raw[csv_col] if csv_col in raw.columns else pd.NA

    # Coerce numeric fields (Wind_Dir sometimes '---', becomes NaN)
    for c in NUMERIC_COLS:
        curated[c] = pd.to_numeric(curated[c], errors="coerce")

    curated = curated.dropna(subset=["ts"]).drop_duplicates(subset=["ts"]).sort_values("ts")

    # Optional: light imputation (safe for dashboard continuity)
    curated[NUMERIC_COLS] = curated[NUMERIC_COLS].interpolate(limit_direction="both")

    # Ensure exact column order
    for c in CURATED_COLS:
        if c not in curated.columns:
            curated[c] = pd.NA
    curated = curated[CURATED_COLS]

    return curated

def upsert_curated(curated: pd.DataFrame) -> None:
    eng = get_engine()
    rows = curated.to_dict(orient="records")

    with eng.begin() as conn:
        # Assumes you've run schema.sql; but keep idempotent safety:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS bradford;"))

        # Upsert (explicit list for correctness)
        conn.execute(text("""
            INSERT INTO bradford.weather_curated (
              ts, csv_date, csv_time,
              temp_out, hi_temp, low_temp, dew_pt, wind_chill, heat_index, thw_index, thsw_index,
              out_hum,
              wind_speed, wind_dir, wind_run, hi_speed, hi_dir, wind_samp, wind_tx,
              bar,
              rain, rain_rate,
              solar_rad, solar_energy, hi_solar_rad,
              uv_index, uv_dose, hi_uv,
              heat_dd, cool_dd,
              in_temp, in_hum, in_dew, in_heat, in_emc, inair_density,
              et,
              iss_recept, arc_int
            )
            VALUES (
              :ts, :csv_date, :csv_time,
              :temp_out, :hi_temp, :low_temp, :dew_pt, :wind_chill, :heat_index, :thw_index, :thsw_index,
              :out_hum,
              :wind_speed, :wind_dir, :wind_run, :hi_speed, :hi_dir, :wind_samp, :wind_tx,
              :bar,
              :rain, :rain_rate,
              :solar_rad, :solar_energy, :hi_solar_rad,
              :uv_index, :uv_dose, :hi_uv,
              :heat_dd, :cool_dd,
              :in_temp, :in_hum, :in_dew, :in_heat, :in_emc, :inair_density,
              :et,
              :iss_recept, :arc_int
            )
            ON CONFLICT (ts) DO UPDATE SET
              csv_date = EXCLUDED.csv_date,
              csv_time = EXCLUDED.csv_time,

              temp_out = EXCLUDED.temp_out,
              hi_temp = EXCLUDED.hi_temp,
              low_temp = EXCLUDED.low_temp,
              dew_pt = EXCLUDED.dew_pt,
              wind_chill = EXCLUDED.wind_chill,
              heat_index = EXCLUDED.heat_index,
              thw_index = EXCLUDED.thw_index,
              thsw_index = EXCLUDED.thsw_index,

              out_hum = EXCLUDED.out_hum,

              wind_speed = EXCLUDED.wind_speed,
              wind_dir = EXCLUDED.wind_dir,
              wind_run = EXCLUDED.wind_run,
              hi_speed = EXCLUDED.hi_speed,
              hi_dir = EXCLUDED.hi_dir,
              wind_samp = EXCLUDED.wind_samp,
              wind_tx = EXCLUDED.wind_tx,

              bar = EXCLUDED.bar,

              rain = EXCLUDED.rain,
              rain_rate = EXCLUDED.rain_rate,

              solar_rad = EXCLUDED.solar_rad,
              solar_energy = EXCLUDED.solar_energy,
              hi_solar_rad = EXCLUDED.hi_solar_rad,

              uv_index = EXCLUDED.uv_index,
              uv_dose = EXCLUDED.uv_dose,
              hi_uv = EXCLUDED.hi_uv,

              heat_dd = EXCLUDED.heat_dd,
              cool_dd = EXCLUDED.cool_dd,

              in_temp = EXCLUDED.in_temp,
              in_hum = EXCLUDED.in_hum,
              in_dew = EXCLUDED.in_dew,
              in_heat = EXCLUDED.in_heat,
              in_emc = EXCLUDED.in_emc,
              inair_density = EXCLUDED.inair_density,

              et = EXCLUDED.et,

              iss_recept = EXCLUDED.iss_recept,
              arc_int = EXCLUDED.arc_int,

              updated_at = NOW();
        """), rows)

    print(f"Upserted {len(rows)} rows into bradford.weather_curated")

def main():
    raw = load_raw()
    curated = build_curated(raw)
    upsert_curated(curated)

if __name__ == "__main__":
    main()
