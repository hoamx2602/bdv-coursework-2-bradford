import os
import json
import pandas as pd
from sqlalchemy import text
from database.db import get_engine

def build_ts(df: pd.DataFrame, date_col: str, time_col: str, dayfirst: bool) -> pd.Series:
    # Combine Date + Time into a UTC timestamp
    # Your CSV Date looks like "13/11/2024" => dayfirst=True
    dt = pd.to_datetime(
        df[date_col].astype(str) + " " + df[time_col].astype(str),
        errors="coerce",
        dayfirst=dayfirst,
        utc=True,
    )
    return dt

def main():
    csv_path = os.getenv("CSV_PATH", "data/raw/Bradford_Weather_Data.csv")
    date_col = os.getenv("DATE_COLUMN", "Date")
    time_col = os.getenv("TIME_COLUMN", "Time")
    dayfirst = os.getenv("DATE_FORMAT_DAYFIRST", "true").lower() == "true"
    source_file = os.getenv("SOURCE_FILE", os.path.basename(csv_path))

    df = pd.read_csv(csv_path)

    if date_col not in df.columns or time_col not in df.columns:
        raise ValueError(f"CSV must contain columns '{date_col}' and '{time_col}'")

    df["ts"] = build_ts(df, date_col, time_col, dayfirst=dayfirst)
    df = df.dropna(subset=["ts"]).copy()
    df = df.drop_duplicates(subset=["ts"]).sort_values("ts")

    # Build JSON payload (keep ALL original columns for lineage)
    payload_cols = [c for c in df.columns if c != "ts"]
    rows = []
    for _, r in df.iterrows():
        payload = {c: r[c] for c in payload_cols}
        rows.append({"ts": r["ts"], "payload": json.dumps(payload), "source_file": source_file})

    eng = get_engine()
    with eng.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS bradford;"))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS bradford.weather_raw (
              ts          TIMESTAMPTZ PRIMARY KEY,
              payload     JSONB NOT NULL,
              source_file TEXT NULL,
              ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
            );
        """))

        conn.execute(text("""
            INSERT INTO bradford.weather_raw (ts, payload, source_file)
            VALUES (:ts, CAST(:payload AS JSONB), :source_file)
            ON CONFLICT (ts) DO UPDATE SET
              payload = EXCLUDED.payload,
              source_file = EXCLUDED.source_file,
              ingested_at = NOW();
        """), rows)

    print(f"Upserted {len(rows)} rows into bradford.weather_raw")

if __name__ == "__main__":
    main()
