# dashboard/app.py
import os
import sys
# Add project root to path so we can import 'database'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd
import streamlit as st
import plotly.express as px
from sqlalchemy import text

from database.db import get_engine

st.set_page_config(page_title="Bradford Weather Visual Analytics", layout="wide")

@st.cache_data(ttl=300)
def load_curated(time_min=None, time_max=None) -> pd.DataFrame:
    eng = get_engine()
    base = "SELECT * FROM bradford.weather_curated"
    conds, params = [], {}
    if time_min:
        conds.append("ts >= :tmin")
        params["tmin"] = time_min
    if time_max:
        conds.append("ts <= :tmax")
        params["tmax"] = time_max
    if conds:
        base += " WHERE " + " AND ".join(conds)
    base += " ORDER BY ts ASC;"
    return pd.read_sql(text(base), eng, params=params)

@st.cache_data(ttl=300)
def load_features(time_min=None, time_max=None) -> pd.DataFrame:
    eng = get_engine()
    base = "SELECT * FROM bradford.weather_features"
    conds, params = [], {}
    if time_min:
        conds.append("ts >= :tmin")
        params["tmin"] = time_min
    if time_max:
        conds.append("ts <= :tmax")
        params["tmax"] = time_max
    if conds:
        base += " WHERE " + " AND ".join(conds)
    base += " ORDER BY ts ASC;"
    return pd.read_sql(text(base), eng, params=params)

def export_projector_files(df_feat: pd.DataFrame):
    out_dir = os.getenv("PROJECTOR_OUT_DIR", "data/processed")
    os.makedirs(out_dir, exist_ok=True)

    vecs_path = f"{out_dir}/vecs.tsv"
    meta_path = f"{out_dir}/meta.tsv"

    df_feat[["pc1","pc2","pc3"]].to_csv(vecs_path, sep="\t", index=False, header=False)

    meta_cols = ["ts","cluster_label","model_version",
                 "f_temp_out","f_out_hum","f_bar","f_wind_speed","f_rain_rate","f_solar_rad","f_uv_index"]
    meta = df_feat[meta_cols].copy()
    meta["ts"] = meta["ts"].astype(str)
    meta.to_csv(meta_path, sep="\t", index=False)
    return vecs_path, meta_path

st.title("Bradford Weather Visual Analytics (AWS Postgres)")

dfc = load_curated()
if dfc.empty:
    st.warning("No data in bradford.weather_curated. Run ingestion + preprocessing first.")
    st.stop()

min_ts, max_ts = pd.to_datetime(dfc["ts"]).min(), pd.to_datetime(dfc["ts"]).max()
c1, c2 = st.columns(2)
with c1:
    tmin = st.date_input("Start date", value=min_ts.date())
with c2:
    tmax = st.date_input("End date", value=max_ts.date())

dfc = load_curated(str(tmin), str(tmax))
dff = load_features(str(tmin), str(tmax))

tab1, tab2, tab3 = st.tabs(["EDA", "PCA + Clusters (from DB)", "TensorFlow Projector (3D export)"])

with tab1:
    st.subheader("Time-series exploration (curated)")
    numeric_cols = [c for c in dfc.columns if c not in ("ts","csv_date","csv_time","updated_at")]

    metric = st.selectbox("Metric", options=numeric_cols, index=0)
    fig = px.line(dfc, x="ts", y=metric, title=f"{metric} over time")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Correlation heatmap (selected)")
    selected = st.multiselect("Columns for correlation", options=numeric_cols, default=numeric_cols[:8])
    if len(selected) >= 2:
        corr = dfc[selected].corr(numeric_only=True)
        fig2 = px.imshow(corr, text_auto=True, aspect="auto", title="Correlation")
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("Select at least 2 columns.")

with tab2:
    st.subheader("PCA scatter (PC1 vs PC2) and clusters")
    if dff.empty:
        st.warning("No rows in bradford.weather_features. Run: python -m analytics.compute_features")
    else:
        fig = px.scatter(
            dff, x="pc1", y="pc2", color="cluster_label",
            hover_data=["ts","model_version"],
            title="PCA scatter coloured by cluster_label"
        )
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("3D PCA scatter (PC1/PC2/PC3)")
        fig3 = px.scatter_3d(
            dff, x="pc1", y="pc2", z="pc3", color="cluster_label",
            hover_data=["ts","model_version"],
            title="3D PCA (interactive)"
        )
        st.plotly_chart(fig3, use_container_width=True)

        st.subheader("Cluster summary (means of selected features)")
        feat_cols = [c for c in dff.columns if c.startswith("f_")]
        summ = dff.groupby("cluster_label")[feat_cols].mean().round(3)
        st.dataframe(summ, use_container_width=True)

with tab3:
    st.subheader("Export vectors + metadata for TensorFlow Embedding Projector")
    st.write("This exports PCA 3D vectors (pc1,pc2,pc3) and metadata (cluster + selected features).")

    if dff.empty:
        st.warning("No features to export. Run compute_features first.")
    else:
        if st.button("Generate vecs.tsv and meta.tsv"):
            vecs_path, meta_path = export_projector_files(dff)
            st.success("Exported TSV files.")
            st.code(f"Vectors: {vecs_path}\nMetadata: {meta_path}")

            with open(vecs_path, "rb") as f:
                st.download_button("Download vecs.tsv", data=f, file_name="vecs.tsv")
            with open(meta_path, "rb") as f:
                st.download_button("Download meta.tsv", data=f, file_name="meta.tsv")

        st.info("Upload both files to projector.tensorflow.org (Vectors + Metadata).")
