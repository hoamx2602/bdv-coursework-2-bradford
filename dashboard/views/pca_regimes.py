# dashboard/views/pca_regimes.py
import os
import streamlit as st
import plotly.express as px


def render(dff):
    st.title("PCA & Regimes")
    st.caption(
        "Dimensionality reduction and regime discovery using PCA and clustering. "
        "High-dimensional 3D exploration is delegated to TensorFlow Projector."
    )

    if dff.empty:
        st.warning("No data in bradford.weather_features. Run: python -m analytics.compute_features")
        return

    tab2d, tab_projector = st.tabs(["2D PCA", "TensorFlow Projector Export"])

    # -----------------------------
    # 2D PCA (main analytical view)
    # -----------------------------
    with tab2d:
        st.subheader("2D PCA projection")
        st.caption("PC1 vs PC2 coloured by cluster label")

        fig = px.scatter(
            dff,
            x="pc1",
            y="pc2",
            color="cluster_label",
            hover_data=["ts", "model_version"],
        )
        st.plotly_chart(fig, use_container_width=True)

        feat_cols = [
            c for c in [
                "f_temp_out",
                "f_out_hum",
                "f_bar",
                "f_rain_rate",
                "f_solar_rad",
                "f_uv_index",
            ]
            if c in dff.columns
        ]

        st.subheader("Cluster summary (mean of standardised features)")
        st.dataframe(
            dff.groupby("cluster_label")[feat_cols]
            .mean()
            .round(3),
            use_container_width=True,
        )

        st.info(
            "This 2D projection is used for analytical interpretation and cluster comparison. "
            "Higher-dimensional structure is explored separately using TensorFlow Projector."
        )

    # -----------------------------
    # TensorFlow Projector Export
    # -----------------------------
    with tab_projector:
        st.subheader("Export for TensorFlow Projector")
        st.caption(
            "Generate vecs.tsv (PC1–PC3) and meta.tsv for interactive 3D visualisation "
            "at https://projector.tensorflow.org/"
        )

        out_dir = os.getenv("PROJECTOR_OUT_DIR", "data/processed")
        os.makedirs(out_dir, exist_ok=True)
        vecs_path = os.path.join(out_dir, "vecs.tsv")
        meta_path = os.path.join(out_dir, "meta.tsv")

        colA, colB = st.columns([1, 2], gap="small")

        with colA:
            if st.button("Generate TSV files"):
                # Vectors (PC1–PC3), no header
                dff[["pc1", "pc2", "pc3"]].to_csv(
                    vecs_path, sep="\t", index=False, header=False
                )

                # Metadata
                meta_cols = [
                    "ts",
                    "cluster_label",
                    "model_version",
                    "f_temp_out",
                    "f_out_hum",
                    "f_bar",
                    "f_rain_rate",
                    "f_solar_rad",
                    "f_uv_index",
                ]
                meta_cols = [c for c in meta_cols if c in dff.columns]
                meta = dff[meta_cols].copy()
                meta["ts"] = meta["ts"].astype(str)
                meta.to_csv(meta_path, sep="\t", index=False)

                st.success("TSV files generated successfully.")

        with colB:
            st.code(
                f"Vectors:   {vecs_path}\n"
                f"Metadata:  {meta_path}"
            )

        if os.path.exists(vecs_path) and os.path.exists(meta_path):
            with open(vecs_path, "rb") as f:
                st.download_button("Download vecs.tsv", f, file_name="vecs.tsv")
            with open(meta_path, "rb") as f:
                st.download_button("Download meta.tsv", f, file_name="meta.tsv")

        st.markdown(
            """
            **How to use TensorFlow Projector**
            1. Open https://projector.tensorflow.org/
            2. Upload **vecs.tsv** as *Vectors*
            3. Upload **meta.tsv** as *Metadata*
            4. Select PCA or Custom projection
            5. Colour points by `cluster_label`
            """
        )
