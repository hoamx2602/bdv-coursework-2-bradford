# analytics/export_projector_tsv.py
import os
import pandas as pd
from sqlalchemy import text
from database.db import get_engine

def main():
    out_dir = os.getenv("PROJECTOR_OUT_DIR", "data/processed")
    os.makedirs(out_dir, exist_ok=True)

    eng = get_engine()
    df = pd.read_sql(text("""
        SELECT ts, pc1, pc2, pc3, cluster_label,
               f_temp_out, f_out_hum, f_bar, f_wind_speed, f_rain_rate, f_solar_rad, f_uv_index,
               model_version
        FROM bradford.weather_features
        WHERE pc1 IS NOT NULL AND pc2 IS NOT NULL AND pc3 IS NOT NULL
        ORDER BY ts ASC;
    """), eng)

    if df.empty:
        raise RuntimeError("No PCA rows in bradford.weather_features. Run compute_features.py first.")

    # vecs.tsv: numeric vectors only, tab-separated, NO header safest for projector
    df[["pc1", "pc2", "pc3"]].to_csv(f"{out_dir}/vecs.tsv", sep="\t", index=False, header=False)

    # meta.tsv: include header for readability + colouring by cluster_label in projector
    meta_cols = ["ts", "cluster_label", "model_version",
                 "f_temp_out", "f_out_hum", "f_bar", "f_wind_speed", "f_rain_rate", "f_solar_rad", "f_uv_index"]
    meta = df[meta_cols].copy()
    meta["ts"] = meta["ts"].astype(str)
    meta.to_csv(f"{out_dir}/meta.tsv", sep="\t", index=False)

    print("Wrote:")
    print(f"  {out_dir}/vecs.tsv")
    print(f"  {out_dir}/meta.tsv")
    print("Upload both files to https://projector.tensorflow.org/ (Vectors + Metadata).")

if __name__ == "__main__":
    main()
