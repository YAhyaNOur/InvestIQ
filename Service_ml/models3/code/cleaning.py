import os
import pandas as pd
from config import *

# =========================
# LOAD
# =========================
def load_data(path=DATA_RAW):
    df = pd.read_csv(path)
    print("[load]", df.shape)
    return df


# =========================
# DROP
# =========================
def drop_columns(df):
    return df.drop(columns=[c for c in COLS_TO_DROP if c in df.columns], errors="ignore")


# =========================
# FLAG MISSING
# =========================
def flag_missing(df):
    for col in COLS_TO_FLAG:
        if col in df.columns:
            df[f"{col}_missing"] = df[col].isna().astype(int)
    return df


# =========================
# IMPUTE
# =========================
def impute_all(df):
    for col in NUMERICAL_COLS:
        if col in df.columns:
            df[col] = df[col].fillna(df[col].median())

    for col in CATEGORICAL_COLS:
        if col in df.columns and df[col].notna().any():
            df[col] = df[col].fillna(df[col].mode().iloc[0])

    return df


# =========================
# TYPES FIX
# =========================
def fix_types(df):
    for col in ["Year Founded", "Employees", "Profitable"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    return df


# =========================
# OUTLIERS
# =========================
def clip_outliers(df):
    cols = [c for c in NUMERICAL_COLS if c in df.columns]

    for col in cols:
        low = df[col].quantile(OUTLIER_QUANTILE_LOW)
        high = df[col].quantile(OUTLIER_QUANTILE_HIGH)
        df[col] = df[col].clip(low, high)

    return df


# =========================
# PIPELINE
# =========================
def run_cleaning():
    df = load_data()
    df = drop_columns(df)
    df = flag_missing(df)
    df = impute_all(df)
    df = fix_types(df)
    df = clip_outliers(df)

    out = os.path.join(DATA_PROCESSED, "cleaned2.csv")
    df.to_csv(out, index=False)

    print("[save]", out)
    return df


if __name__ == "__main__":
    run_cleaning()