import os
import streamlit as st

def render(dff):
    st.title("Projector Export")
    st.caption("Export vecs.tsv + meta.tsv for https://projector.tensorflow.org/ (3D PCA vectors).")

    if dff.empty:
        st.warning("No features to export. Run: python -m analytics.compute_features")
        return

    out_dir = os.getenv("PROJECTOR_OUT_DIR", "data/processed")
    os.makedirs(out_dir, exist_ok=True)
    vecs_path = f"{out_dir}/vecs.tsv"
    meta_path = f"{out_dir}/meta.tsv"

    if st.button("Generate TSV files"):
        dff[["pc1","pc2","pc3"]].to_csv(vecs_path, sep="\t", index=False, header=False)
        meta_cols = ["ts","cluster_label","model_version","f_temp_out","f_out_hum","f_bar","f_wind_speed","f_rain_rate","f_solar_rad","f_uv_index"]
        meta = dff[meta_cols].copy()
        meta["ts"] = meta["ts"].astype(str)
        meta.to_csv(meta_path, sep="\t", index=False)

        st.success("Exported TSV files.")
        st.code(f"Vectors: {vecs_path}\nMetadata: {meta_path}")

        with open(vecs_path, "rb") as f:
            st.download_button("Download vecs.tsv", data=f, file_name="vecs.tsv")
        with open(meta_path, "rb") as f:
            st.download_button("Download meta.tsv", data=f, file_name="meta.tsv")

    st.info("Upload both files to projector.tensorflow.org/ (Vectors + Metadata).")
