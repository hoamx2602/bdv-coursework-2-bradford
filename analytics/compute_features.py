# analytics/compute_features.py
import os
import sys
import pandas as pd
from sqlalchemy import text
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans

# Add project root to path so we can import 'database'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.db import get_engine  # noqa: E402


# Feature set used for multivariate analysis (NO WIND)
FEATURE_COLS = ["temp_out", "out_hum", "bar", "rain_rate", "solar_rad", "uv_index"]

MODEL_VERSION = os.getenv("MODEL_VERSION", "pca3_kmeans_v1_nowind")
KMEANS_K = int(os.getenv("KMEANS_K", "4"))


def load_curated(eng) -> pd.DataFrame:
    df = pd.read_sql(
        text("""
            SELECT ts, temp_out, out_hum, bar, rain_rate, solar_rad, uv_index
            FROM bradford.weather_curated
            ORDER BY ts ASC;
        """),
        eng,
    )
    df["ts"] = pd.to_datetime(df["ts"], utc=True, errors="coerce")
    return df.dropna(subset=["ts"])


def ensure_features_table(eng) -> None:
    ddl = [
        "CREATE SCHEMA IF NOT EXISTS bradford;",
        """
        CREATE TABLE IF NOT EXISTS bradford.weather_features (
            ts TIMESTAMPTZ PRIMARY KEY,
            model_version TEXT NOT NULL,
            cluster_label INT,
            pc1 DOUBLE PRECISION,
            pc2 DOUBLE PRECISION,
            pc3 DOUBLE PRECISION,
            f_temp_out DOUBLE PRECISION,
            f_out_hum DOUBLE PRECISION,
            f_bar DOUBLE PRECISION,
            f_rain_rate DOUBLE PRECISION,
            f_solar_rad DOUBLE PRECISION,
            f_uv_index DOUBLE PRECISION
        );
        """,
    ]
    # SQLAlchemy 2.x: use connection
    with eng.begin() as conn:
        for stmt in ddl:
            conn.execute(text(stmt))


def upsert_features(eng, df_out: pd.DataFrame) -> None:
    sql = text("""
        INSERT INTO bradford.weather_features (
            ts, model_version, cluster_label, pc1, pc2, pc3,
            f_temp_out, f_out_hum, f_bar, f_rain_rate, f_solar_rad, f_uv_index
        )
        VALUES (
            :ts, :model_version, :cluster_label, :pc1, :pc2, :pc3,
            :f_temp_out, :f_out_hum, :f_bar, :f_rain_rate, :f_solar_rad, :f_uv_index
        )
        ON CONFLICT (ts) DO UPDATE SET
            model_version = EXCLUDED.model_version,
            cluster_label = EXCLUDED.cluster_label,
            pc1 = EXCLUDED.pc1,
            pc2 = EXCLUDED.pc2,
            pc3 = EXCLUDED.pc3,
            f_temp_out = EXCLUDED.f_temp_out,
            f_out_hum = EXCLUDED.f_out_hum,
            f_bar = EXCLUDED.f_bar,
            f_rain_rate = EXCLUDED.f_rain_rate,
            f_solar_rad = EXCLUDED.f_solar_rad,
            f_uv_index = EXCLUDED.f_uv_index;
    """)

    records = df_out.to_dict(orient="records")
    with eng.begin() as conn:
        conn.execute(sql, records)


def main():
    eng = get_engine()
    ensure_features_table(eng)

    df = load_curated(eng)

    # Need complete vectors for PCA/Clustering
    df_feat = df[["ts"] + FEATURE_COLS].dropna().copy()
    if df_feat.empty:
        raise RuntimeError("No complete rows found for selected FEATURE_COLS in weather_curated.")

    X = df_feat[FEATURE_COLS].astype(float).values

    scaler = StandardScaler()
    Xz = scaler.fit_transform(X)

    pca = PCA(n_components=3, random_state=42)
    pcs = pca.fit_transform(Xz)

    km = KMeans(n_clusters=KMEANS_K, n_init=10, random_state=42)
    labels = km.fit_predict(pcs)

    # IMPORTANT: pass tz-aware timestamps as python datetime (best for TIMESTAMPTZ)
    df_out = pd.DataFrame({
        "ts": df_feat["ts"].dt.to_pydatetime(),
        "model_version": MODEL_VERSION,
        "cluster_label": labels.astype(int),
        "pc1": pcs[:, 0],
        "pc2": pcs[:, 1],
        "pc3": pcs[:, 2],
        "f_temp_out": Xz[:, 0],
        "f_out_hum": Xz[:, 1],
        "f_bar": Xz[:, 2],
        "f_rain_rate": Xz[:, 3],
        "f_solar_rad": Xz[:, 4],
        "f_uv_index": Xz[:, 5],
    })

    upsert_features(eng, df_out)

    explained = (pca.explained_variance_ratio_ * 100).round(2)
    print("✅ weather_features updated")
    print(f"Model: {MODEL_VERSION} | KMeans K={KMEANS_K}")
    print(f"PCA explained variance (%): PC1={explained[0]}, PC2={explained[1]}, PC3={explained[2]}")
    print(f"Rows written: {len(df_out)}")


if __name__ == "__main__":
    main()
