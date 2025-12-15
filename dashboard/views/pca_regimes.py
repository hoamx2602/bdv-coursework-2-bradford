import plotly.express as px
import streamlit as st

def render(dff):
    st.title("PCA & Regimes")
    st.caption("Visualise weather regimes from precomputed PCA components and clustering labels (weather_features).")

    if dff.empty:
        st.warning("No data in bradford.weather_features. Run: python -m analytics.compute_features")
        return

    a, b = st.tabs(["2D PCA", "3D PCA"])
    with a:
        fig = px.scatter(dff, x="pc1", y="pc2", color="cluster_label", hover_data=["ts","model_version"],
                         title="PC1 vs PC2 coloured by cluster")
        st.plotly_chart(fig, use_container_width=True)

        feat_cols = [c for c in dff.columns if c.startswith("f_")]
        st.subheader("Cluster summary (means of selected features)")
        st.dataframe(dff.groupby("cluster_label")[feat_cols].mean().round(3), use_container_width=True)

    with b:
        fig3 = px.scatter_3d(dff, x="pc1", y="pc2", z="pc3", color="cluster_label",
                             hover_data=["ts","model_version"], title="3D PCA (interactive)")
        st.plotly_chart(fig3, use_container_width=True)
