# analytics/compute_features.py
import os
import pandas as pd
from sqlalchemy import text
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

from database.db import get_engine

FEATURE_COLS = [
    "temp_out", "out_hum", "bar", "wind_speed", "rain_rate", "solar_rad", "uv_index"
]

def load_curated() -> pd.DataFrame:
    eng = get_engine()
    df = pd.read_sql(text(f"""
        SELECT
          ts,
          {", ".join(FEATURE_COLS)}
        FROM bradford.weather_curated
        ORDER BY ts ASC;
    """), eng)
    df["ts"] = pd.to_datetime(df["ts"], utc=True, errors="coerce")
    return df.dropna(subset=["ts"])

def build_features(df: pd.DataFrame) -> pd.DataFrame:
    # Coerce numeric + handle missing safely
    for c in FEATURE_COLS:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    # Simple imputation for continuity (justify in report)
    df = df.sort_values("ts")
    df[FEATURE_COLS] = df[FEATURE_COLS].interpolate(limit_direction="both")

    # Standardise
    X = df[FEATURE_COLS].astype(float).values
    scaler = StandardScaler()
    Xs = scaler.fit_transform(X)

    # PCA 3D (for projector & 3D visualisation)
    pca = PCA(n_components=3, random_state=42)
    Z = pca.fit_transform(Xs)

    # KMeans on PCA space
    k = int(os.getenv("KMEANS_K", "4"))
    km = KMeans(n_clusters=k, n_init="auto", random_state=42)
    labels = km.fit_predict(Z)

    sil = silhouette_score(Z, labels) if k > 1 else None
    evr = pca.explained_variance_ratio_

    model_version = os.getenv("MODEL_VERSION", "pca3_kmeans_v1")

    out = pd.DataFrame({
        "ts": df["ts"],
        "f_temp_out": df["temp_out"],
        "f_out_hum": df["out_hum"],
        "f_bar": df["bar"],
        "f_wind_speed": df["wind_speed"],
        "f_rain_rate": df["rain_rate"],
        "f_solar_rad": df["solar_rad"],
        "f_uv_index": df["uv_index"],
        "pc1": Z[:, 0],
        "pc2": Z[:, 1],
        "pc3": Z[:, 2],
        "cluster_label": labels.astype(int),
        "model_version": model_version,
    })

    print("PCA explained variance ratio:", [round(x, 4) for x in evr])
    if sil is not None:
        print("Silhouette score:", round(float(sil), 4))

    return out

def upsert_weather_features(df_feat: pd.DataFrame) -> None:
    eng = get_engine()
    rows = df_feat.to_dict(orient="records")

    with eng.begin() as conn:
        conn.execute(text("""
            INSERT INTO bradford.weather_features (
              ts,
              f_temp_out, f_out_hum, f_bar, f_wind_speed, f_rain_rate, f_solar_rad, f_uv_index,
              pc1, pc2, pc3,
              cluster_label,
              model_version
            )
            VALUES (
              :ts,
              :f_temp_out, :f_out_hum, :f_bar, :f_wind_speed, :f_rain_rate, :f_solar_rad, :f_uv_index,
              :pc1, :pc2, :pc3,
              :cluster_label,
              :model_version
            )
            ON CONFLICT (ts) DO UPDATE SET
              f_temp_out = EXCLUDED.f_temp_out,
              f_out_hum = EXCLUDED.f_out_hum,
              f_bar = EXCLUDED.f_bar,
              f_wind_speed = EXCLUDED.f_wind_speed,
              f_rain_rate = EXCLUDED.f_rain_rate,
              f_solar_rad = EXCLUDED.f_solar_rad,
              f_uv_index = EXCLUDED.f_uv_index,
              pc1 = EXCLUDED.pc1,
              pc2 = EXCLUDED.pc2,
              pc3 = EXCLUDED.pc3,
              cluster_label = EXCLUDED.cluster_label,
              model_version = EXCLUDED.model_version,
              computed_at = NOW();
        """), rows)

    print(f"Upserted {len(rows)} rows into bradford.weather_features")

def main():
    df = load_curated()
    if df.empty:
        raise RuntimeError("No rows found in bradford.weather_curated. Run preprocessing first.")
    df_feat = build_features(df)
    upsert_weather_features(df_feat)

if __name__ == "__main__":
    main()
