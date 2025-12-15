Dưới đây là README mẫu (bạn copy thẳng vào `README.md`) để người khác clone repo về là **chạy được ngay** với **AWS Postgres**, **Python-only** (không cần psql), có cả pipeline analytics + dashboard + TensorFlow Projector + Andrews Curves.

---

# Bradford Weather Visual Analytics

End-to-end visual analytics pipeline for multivariate weather station data:

* Postgres (AWS) as data store
* Preprocessing + Feature Selection + PCA (3D) + KMeans
* Andrews Curves visualisation
* Interactive Streamlit dashboard (multi-page via sidebar router)
* Export embeddings to TensorFlow Projector

## 1) Project Structure

```text
.
├── analytics/
│   ├── preprocessing.py
│   ├── compute_features.py
│   └── export_projector_tsv.py
├── database/
│   ├── db.py
│   └── init_db.py
├── ingestion/
│   └── ingest_csv_to_postgres.py
├── dashboard/
│   ├── app.py
│   ├── components.py
│   └── views/
│       ├── __init__.py
│       ├── overview.py
│       ├── daily_snapshot.py
│       ├── trends.py
│       ├── pca_regimes.py
│       ├── andrews_curves.py
│       ├── extremes.py
│       └── projector_export.py
├── data/
│   ├── raw/
│   │   └── Bradford_Weather_Data.csv
│   └── processed/
│       ├── vecs.tsv
│       └── meta.tsv
├── .env
└── requirements.txt
```

> Note: Folder is `dashboard/views/` (NOT `dashboard/pages/`) to avoid Streamlit auto “pages” menu.

---

## 2) Requirements

* Python 3.10+ (recommended)
* AWS RDS Postgres database accessible from your machine
* A `DATABASE_URL` connection string

Example `requirements.txt` should include at least:

* `pandas`
* `sqlalchemy`
* `psycopg2-binary` (or `psycopg`)
* `python-dotenv`
* `scikit-learn`
* `streamlit`
* `plotly`

---

## 3) Setup

### 3.1 Create venv and install dependencies

```bash
python -m venv .venv
source .venv/bin/activate   # macOS/Linux
# .venv\Scripts\activate    # Windows

pip install -r requirements.txt
```

### 3.2 Configure `.env`

Create `.env` at project root:

```env
DATABASE_URL=postgresql+psycopg2://USERNAME:PASSWORD@HOST:5432/DBNAME
```

Optional settings:

```env
KMEANS_K=4
MODEL_VERSION=pca3_kmeans_v1
PROJECTOR_OUT_DIR=data/processed
```

---

## 4) Run the Pipeline (Python-only)

### Step 1 — Create schema & tables (no psql needed)

```bash
python -m database.init_db
```

### Step 2 — Ingest CSV into Postgres

Put your dataset here:

```text
data/raw/Bradford_Weather_Data.csv
```

Run:

```bash
python -m ingestion.ingest_csv_to_postgres
```

### Step 3 — Preprocess into curated table

```bash
python -m analytics.preprocessing
```

### Step 4 — Compute features (FS → Standardise → PCA 3D → KMeans) into features table

```bash
python -m analytics.compute_features
```

### Step 5 — Export TensorFlow Projector files (vecs.tsv + meta.tsv)

```bash
python -m analytics.export_projector_tsv
```

Outputs:

* `data/processed/vecs.tsv`
* `data/processed/meta.tsv`

Upload both to TensorFlow Projector:

* [https://projector.tensorflow.org/](https://projector.tensorflow.org/)

---

## 5) Run the Dashboard

```bash
streamlit run dashboard/app.py
```

### Dashboard Pages

* Overview (EDA: time-series, completeness)
* Daily Snapshot (pro layout: gauges + KPI cards)
* Trends (seasonality + correlations)
* PCA & Regimes (2D/3D PCA + cluster summary)
* Andrews Curves (multivariate curves coloured by cluster)
* Extremes (top-N peaks)
* Projector Export (download TSV files)

---

## 6) Troubleshooting

### “RuntimeError: DATABASE_URL is not set”

* Ensure `.env` is at project root
* Ensure code loads dotenv (if you use `python-dotenv`)
* Confirm shell can see it:

```bash
python -c "import os; print(os.getenv('DATABASE_URL'))"
```

### Cannot connect to AWS Postgres

* Check security group allows your IP on port 5432
* Check correct host/port/dbname/user/pass
* If using SSL on RDS, ensure your driver supports it (often default works)

### Streamlit shows an extra “pages” menu

* Ensure your folder is `dashboard/views/` not `dashboard/pages/`

### Andrews Curves page is slow

* Reduce “Sample size” and “Curve resolution” in the sidebar settings on that page

---

## 7) Reproducibility Notes

* `weather_curated` contains typed, cleaned, time-indexed data.
* `weather_features` stores derived analytics outputs (PCA + cluster labels), enabling consistent visualisation across PCA plots, Andrews Curves, and TensorFlow Projector.

---

## 8) Quick Start (Minimal)

```bash
pip install -r requirements.txt
python -m database.init_db
python -m ingestion.ingest_csv_to_postgres
python -m analytics.preprocessing
python -m analytics.compute_features
streamlit run dashboard/app.py
```

---

Nếu bạn paste cho mình `requirements.txt` hiện tại (hoặc `pip freeze | head -n 50`) mình sẽ chỉnh lại README cho đúng 100% theo repo của bạn (tên module, đường dẫn file CSV, v.v.).
