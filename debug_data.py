import sys
import os
import pandas as pd
from sqlalchemy import text

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.db import get_engine

def inspect_features():
    eng = get_engine()
    print("Connecting to database...")
    
    query = "SELECT * FROM bradford.weather_features LIMIT 10;"
    try:
        df = pd.read_sql(text(query), eng)
    except Exception as e:
        print(f"Error querying table: {e}")
        return

    print(f"Columns: {list(df.columns)}")
    print(f"Shape: {df.shape}")
    
    if df.empty:
        print("Table is empty.")
        return

    # Check for f_ columns
    f_cols = [c for c in df.columns if c.startswith("f_")]
    print(f"Feature columns: {f_cols}")
    
    # Check for NaNs
    nulls = df[f_cols].isnull().sum()
    print("Nulls in feature columns:")
    print(nulls)
    
    # Check rows with ANY NaN in features
    incomplete_rows = df[df[f_cols].isnull().any(axis=1)]
    print(f"Rows with incomplete features (in sample): {len(incomplete_rows)}")
    
    if not incomplete_rows.empty:
        print("Sample incomplete row:")
        print(incomplete_rows.iloc[0])

    # Check PC columns
    pc_cols = [c for c in df.columns if c.startswith("pc")]
    print(f"PC columns: {pc_cols}")
    print("Nulls in PC columns:")
    print(df[pc_cols].isnull().sum())

if __name__ == "__main__":
    inspect_features()
