# analytics/export_projector_tsv.py
import os
import sys
import pandas as pd
from sqlalchemy import text

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from database.db import get_engine  # noqa: E402


def main():
    eng = get_engine()

    df = pd.read_sql(
        text("""
            SELECT
              ts, cluster_label, model_version,
              pc1, pc2, pc3,
              f_temp_out, f_out_hum, f_bar, f_rain_rate, f_solar_rad, f_uv_index
            FROM bradford.weather_features
            ORDER BY ts ASC;
        """),
        eng,
    )

    if df.empty:
        raise RuntimeError("No rows in bradford.weather_features. Run: python -m analytics.compute_features")

    out_dir = os.getenv("PROJECTOR_OUT_DIR", "data/processed")
    os.makedirs(out_dir, exist_ok=True)

    vecs_path = os.path.join(out_dir, "vecs.tsv")
    meta_path = os.path.join(out_dir, "meta.tsv")

    # Vectors
    df[["pc1", "pc2", "pc3"]].to_csv(vecs_path, sep="\t", index=False, header=False)

    # Metadata
    meta_cols = [
        "ts", "cluster_label", "model_version",
        "f_temp_out", "f_out_hum", "f_bar", "f_rain_rate", "f_solar_rad", "f_uv_index"
    ]
    meta = df[meta_cols].copy()
    meta["ts"] = meta["ts"].astype(str)
    meta.to_csv(meta_path, sep="\t", index=False)

    print("✅ Exported TensorFlow Projector files")
    print(f"Vectors:   {vecs_path}")
    print(f"Metadata:  {meta_path}")


if __name__ == "__main__":
    main()
