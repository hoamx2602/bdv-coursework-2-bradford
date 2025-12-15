# dashboard/views/andrews_curves.py
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px

def _andrews_curves_matrix(X: np.ndarray, t_points: int = 160) -> tuple[np.ndarray, np.ndarray]:
    """
    Compute Andrews curves for rows of X (n_samples x n_features).
    Returns: t (t_points,), Y (n_samples x t_points)
    """
    t = np.linspace(-np.pi, np.pi, t_points)
    n, d = X.shape
    Y = np.zeros((n, t_points), dtype=float)

    # x1/sqrt(2)
    Y += (X[:, [0]] / np.sqrt(2.0))

    k = 1
    for j in range(1, d):
        if j % 2 == 1:
            Y += X[:, [j]] * np.sin(k * t)
        else:
            Y += X[:, [j]] * np.cos(k * t)
            k += 1

    return t, Y

def render(dfc: pd.DataFrame, dff: pd.DataFrame):
    st.title("Andrews Curves")
    st.caption("Multivariate visualisation: each record becomes a Fourier-series curve. "
               "Clusters should form separated bands when structure exists.")

    if dfc.empty:
        st.warning("No curated data available in the selected range.")
        return

    # Prefer to colour by cluster_label if features table exists and matches timestamps
    use_clusters = (not dff.empty) and ("cluster_label" in dff.columns)

    # Choose feature columns (from curated) for Andrews
    default_cols = ["temp_out", "out_hum", "bar", "wind_speed", "rain_rate", "solar_rad", "uv_index"]
    available = [c for c in default_cols if c in dfc.columns]
    if len(available) < 3:
        st.warning("Not enough numeric columns for Andrews curves in this range.")
        return

    with st.sidebar.expander("Andrews settings", expanded=True):
        cols = st.multiselect("Features used for Andrews curves", available, default=available[:5])
        t_points = st.slider("Curve resolution (t points)", 80, 300, 160, step=20)
        sample_n = st.slider("Sample size (performance)", 50, 600, 200, step=50)
        smooth = st.checkbox("Smooth (rolling mean on curves)", value=True)
        smooth_win = st.slider("Smoothing window", 3, 25, 9, step=2) if smooth else 1

    if len(cols) < 3:
        st.info("Select at least 3 features for meaningful Andrews curves.")
        return

    # Build dataset (sample for speed)
    base = dfc[["ts"] + cols].dropna().copy()
    if base.empty:
        st.warning("No complete rows after dropping missing values.")
        return

    if len(base) > sample_n:
        base = base.sample(sample_n, random_state=42).sort_values("ts")

    # Attach cluster labels if available
    if use_clusters:
        key = dff[["ts", "cluster_label"]].copy()
        key["ts"] = pd.to_datetime(key["ts"], utc=True, errors="coerce")
        base = base.merge(key, on="ts", how="left")
        base["cluster_label"] = base["cluster_label"].fillna(-1).astype(int)
    else:
        base["cluster_label"] = 0

    # Standardise features (important for Andrews)
    X = base[cols].astype(float).values
    X = (X - X.mean(axis=0)) / (X.std(axis=0) + 1e-9)

    t, Y = _andrews_curves_matrix(X, t_points=t_points)

    if smooth:
        # rolling mean across t dimension
        kernel = np.ones(smooth_win) / smooth_win
        Y = np.apply_along_axis(lambda y: np.convolve(y, kernel, mode="same"), 1, Y)

    # Long format for Plotly
    df_long = pd.DataFrame({
        "series_id": np.repeat(np.arange(Y.shape[0]), len(t)),
        "t": np.tile(t, Y.shape[0]),
        "y": Y.reshape(-1),
        "cluster_label": np.repeat(base["cluster_label"].values, len(t)),
    })

    # Plot
    st.subheader("Andrews Curves (coloured by cluster)")
    fig = px.line(
        df_long,
        x="t",
        y="y",
        color="cluster_label",
        line_group="series_id",
        title="Andrews curves in 2D (clusters should form bands if structure exists)",
    )
    fig.update_layout(showlegend=True)
    st.plotly_chart(fig, use_container_width=True)

    # Optional: show how many samples per cluster
    if use_clusters:
        st.subheader("Cluster composition (in sampled curves)")
        counts = base["cluster_label"].value_counts().sort_index()
        st.dataframe(counts.rename("count"), use_container_width=True)
