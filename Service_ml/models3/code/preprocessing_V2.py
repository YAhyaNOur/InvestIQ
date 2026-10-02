import os
import sys
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from config import DATA_PROCESSED, RANDOM_STATE


def load_data():
    path = os.path.join(DATA_PROCESSED, "featured2.csv")
    df = pd.read_csv(path)

    df = df.loc[:, ~df.columns.duplicated()].copy()

    return df


def clip_train_test(train_df, test_df, num_cols):
    for col in num_cols:
        low = train_df[col].quantile(0.01)
        high = train_df[col].quantile(0.99)

        train_df[col] = train_df[col].clip(low, high)
        test_df[col] = test_df[col].clip(low, high)

    return train_df, test_df


def add_sector_zscore(train_df, test_df, col, group_col="Sector"):
  

    # stats TRAIN ONLY
    sector_mean = train_df.groupby(group_col)[col].mean()
    sector_std = train_df.groupby(group_col)[col].std()

    # mapping sécurisé
    train_mean = train_df[group_col].map(sector_mean)
    train_std = train_df[group_col].map(sector_std)

    test_mean = test_df[group_col].map(sector_mean)
    test_std = test_df[group_col].map(sector_std)

    # Z-score train
    train_df[f"{col}_Sector_Z"] = (
        (train_df[col] - train_mean) / (train_std + 1e-6)
    ).fillna(0)

    # Z-score test
    test_df[f"{col}_Sector_Z"] = (
        (test_df[col] - test_mean) / (test_std + 1e-6)
    ).fillna(0)

    return train_df, test_df



def run_preprocessing_catboost():

    df = load_data()

  
    train_df, test_df = train_test_split(
        df,
        test_size=0.2,
        random_state=RANDOM_STATE,
        stratify=df["Profitable"] if "Profitable" in df.columns else None
    )

  
    num_cols = train_df.select_dtypes(include=[np.number]).columns.tolist()

    exclude = ["Valuation (M USD)", "Profitable", "Revenue Growth"]
    num_cols = [c for c in num_cols if c not in exclude]

    # clipping SAFE (train stats only)
    train_df, test_df = clip_train_test(train_df, test_df, num_cols)

    sector_cols = [
        "Revenue (M USD)",
        "Employees",
        "Revenue_Per_Employee"
    ]

    for col in sector_cols:
        if col in train_df.columns:
            train_df, test_df = add_sector_zscore(train_df, test_df, col)


    cat_cols = ["Region_std", "Industry_Group", "Sector"]

    for col in cat_cols:
        if col in train_df.columns:
            train_df[col] = train_df[col].astype(str).fillna("Unknown")
            test_df[col] = test_df[col].astype(str).fillna("Unknown")

   
    train_path = os.path.join(DATA_PROCESSED, "train_catboost.csv")
    test_path = os.path.join(DATA_PROCESSED, "test_catboost.csv")

    train_df.to_csv(train_path, index=False)
    test_df.to_csv(test_path, index=False)

    print("\n========== PIPELINE SAFE TERMINÉ ==========")
    print(f"Train : {train_df.shape}")
    print(f"Test  : {test_df.shape}")

    return train_df, test_df


if __name__ == "__main__":
    run_preprocessing_catboost()