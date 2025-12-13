# database/init_db.py
from sqlalchemy import text
from database.db import get_engine

SCHEMA_SQL = """
CREATE SCHEMA IF NOT EXISTS bradford;

-- RAW
CREATE TABLE IF NOT EXISTS bradford.weather_raw (
  ts          TIMESTAMPTZ PRIMARY KEY,
  payload     JSONB NOT NULL,
  source_file TEXT NULL,
  ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_weather_raw_ingested_at
  ON bradford.weather_raw (ingested_at);

-- CURATED
CREATE TABLE IF NOT EXISTS bradford.weather_curated (
  ts           TIMESTAMPTZ PRIMARY KEY,
  csv_date     DATE NULL,
  csv_time     TIME NULL,

  temp_out     DOUBLE PRECISION NULL,
  hi_temp      DOUBLE PRECISION NULL,
  low_temp     DOUBLE PRECISION NULL,
  dew_pt       DOUBLE PRECISION NULL,
  wind_chill   DOUBLE PRECISION NULL,
  heat_index   DOUBLE PRECISION NULL,
  thw_index    DOUBLE PRECISION NULL,
  thsw_index   DOUBLE PRECISION NULL,

  out_hum      DOUBLE PRECISION NULL,

  wind_speed   DOUBLE PRECISION NULL,
  wind_dir     DOUBLE PRECISION NULL,
  wind_run     DOUBLE PRECISION NULL,
  hi_speed     DOUBLE PRECISION NULL,
  hi_dir       DOUBLE PRECISION NULL,
  wind_samp    DOUBLE PRECISION NULL,
  wind_tx      DOUBLE PRECISION NULL,

  bar          DOUBLE PRECISION NULL,

  rain         DOUBLE PRECISION NULL,
  rain_rate    DOUBLE PRECISION NULL,

  solar_rad     DOUBLE PRECISION NULL,
  solar_energy  DOUBLE PRECISION NULL,
  hi_solar_rad  DOUBLE PRECISION NULL,
  uv_index      DOUBLE PRECISION NULL,
  uv_dose       DOUBLE PRECISION NULL,
  hi_uv         DOUBLE PRECISION NULL,

  heat_dd      DOUBLE PRECISION NULL,
  cool_dd      DOUBLE PRECISION NULL,

  in_temp       DOUBLE PRECISION NULL,
  in_hum        DOUBLE PRECISION NULL,
  in_dew        DOUBLE PRECISION NULL,
  in_heat       DOUBLE PRECISION NULL,
  in_emc        DOUBLE PRECISION NULL,
  inair_density DOUBLE PRECISION NULL,

  et           DOUBLE PRECISION NULL,

  iss_recept   DOUBLE PRECISION NULL,
  arc_int      DOUBLE PRECISION NULL,

  updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_weather_curated_ts
  ON bradford.weather_curated (ts);

-- FEATURES
CREATE TABLE IF NOT EXISTS bradford.weather_features (
  ts            TIMESTAMPTZ PRIMARY KEY,

  f_temp_out     DOUBLE PRECISION NULL,
  f_out_hum      DOUBLE PRECISION NULL,
  f_bar          DOUBLE PRECISION NULL,
  f_wind_speed   DOUBLE PRECISION NULL,
  f_rain_rate    DOUBLE PRECISION NULL,
  f_solar_rad    DOUBLE PRECISION NULL,
  f_uv_index     DOUBLE PRECISION NULL,

  pc1           DOUBLE PRECISION NULL,
  pc2           DOUBLE PRECISION NULL,
  pc3           DOUBLE PRECISION NULL,

  cluster_label INTEGER NULL,

  model_version TEXT NOT NULL,
  computed_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_weather_features_cluster
  ON bradford.weather_features (cluster_label);

CREATE INDEX IF NOT EXISTS idx_weather_features_computed_at
  ON bradford.weather_features (computed_at);
"""

def main():
    eng = get_engine()
    with eng.begin() as conn:
        # Execute as a single batch; Postgres accepts multiple statements.
        conn.execute(text(SCHEMA_SQL))
    print("Database initialised: schema/tables/indexes are ready.")

if __name__ == "__main__":
    main()
