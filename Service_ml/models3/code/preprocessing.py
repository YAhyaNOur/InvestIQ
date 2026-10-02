import os
import sys
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import RobustScaler, OrdinalEncoder
import joblib

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config import DATA_PROCESSED, MODELS_DIR


def load_data():
    return pd.read_csv(os.path.join(DATA_PROCESSED, "featured2.csv"))


def run_preprocessing():

    # =========================
    # 0. LOAD DATA
    # =========================
    df = load_data()

    # =========================
    # 1. SPLIT
    # =========================
    train_df, test_df = train_test_split(
        df,
        test_size=0.2,
        random_state=42,
        stratify=df["Profitable"] if "Profitable" in df.columns else None
    )
    rev_cut = df["Revenue (M USD)"].quantile(0.99)
    val_cut = df["Valuation (M USD)"].quantile(0.99)

    df = df[
        (df["Revenue (M USD)"] <= rev_cut) &
        (df["Valuation (M USD)"] <= val_cut)
    ].copy()

    # optional hard cap
    df = df[df["Revenue (M USD)"] <= 1000].copy()
    # =========================
    # 2. CLIPPING
    # =========================
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    exclude = ["Valuation (M USD)", "Profitable"]
    num_cols = [c for c in num_cols if c not in exclude]

    for col in num_cols:
        lower = train_df[col].quantile(0.01)
        upper = train_df[col].quantile(0.99)

        train_df[col] = train_df[col].clip(lower, upper)
        test_df[col] = test_df[col].clip(lower, upper)

    # =========================
    # 3. SECTOR Z-SCORE
    # =========================
    cols_to_norm = ["Revenue (M USD)", "Employees", "Revenue_Per_Employee"]

    for col in cols_to_norm:
        stats = train_df.groupby("Sector")[col].agg(["mean", "std"]).reset_index()
        stats.columns = ["Sector", f"{col}_mean", f"{col}_std"]

        train_df = train_df.merge(stats, on="Sector", how="left")
        train_df[f"{col}_Sector_Z"] = (
            (train_df[col] - train_df[f"{col}_mean"]) /
            (train_df[f"{col}_std"] + 1e-6)
        )
        train_df.drop(columns=[f"{col}_mean", f"{col}_std"], inplace=True)

        test_df = test_df.merge(stats, on="Sector", how="left")
        test_df[f"{col}_Sector_Z"] = (
            (test_df[col] - test_df[f"{col}_mean"]) /
            (test_df[f"{col}_std"] + 1e-6)
        ).fillna(0)

        test_df.drop(columns=[f"{col}_mean", f"{col}_std"], inplace=True)

    # =========================
    # 4. ENCODING
    # =========================
    CAT_COLS = ["Region_std", "Industry_Group", "Sector"]

    enc = OrdinalEncoder(
        handle_unknown="use_encoded_value",
        unknown_value=-1
    )

    train_df[CAT_COLS] = enc.fit_transform(train_df[CAT_COLS].astype(str))
    test_df[CAT_COLS] = enc.transform(test_df[CAT_COLS].astype(str))

    joblib.dump(enc, os.path.join(MODELS_DIR, "encoder.pkl"))

    # =========================
    # 5. SCALING
    # =========================
    final_cols = [
        c for c in train_df.select_dtypes(include=[np.number]).columns
        if c not in exclude
    ]

    scaler = RobustScaler()

    train_df[final_cols] = scaler.fit_transform(train_df[final_cols])
    test_df[final_cols] = scaler.transform(test_df[final_cols])

    joblib.dump(scaler, os.path.join(MODELS_DIR, "scaler.pkl"))

    # =========================
    # 6. SAVE
    # =========================
    train_path = os.path.join(DATA_PROCESSED, "train_preprocessed.csv")
    test_path = os.path.join(DATA_PROCESSED, "test_preprocessed.csv")

    train_df.to_csv(train_path, index=False)
    test_df.to_csv(test_path, index=False)

    print("\n" + "=" * 40)
    print("PIPELINE DE PRÉ-TRAITEMENT TERMINÉE")
    print("=" * 40)
    print(f"Dataset final : {len(df)} lignes")
    print(f"Train sauvé : {train_path}")
    print(f"Test sauvé : {test_path}")
    print("=" * 40)

    return train_df, test_df


if __name__ == "__main__":
    run_preprocessing()