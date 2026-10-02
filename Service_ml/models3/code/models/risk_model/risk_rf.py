import os
import sys
import pandas as pd
import numpy as np
import mlflow
import mlflow.sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from config import DATA_PROCESSED, RANDOM_STATE


def run_rf_risk():

    # =========================
    # 1. LOAD DATA
    # =========================
    df = pd.read_csv(os.path.join(DATA_PROCESSED, "preprocessed2.csv"))

    # =========================
    # 2. TARGET (RISK) SAFE VERSION
    # =========================
    # logique financière simple mais sans fuite directe
    df["Risk"] = np.where(
        (df["Debt To Equity"] > df["Debt To Equity"].quantile(0.75)) &
        (df["Net_Debt"] > 0),
        1,
        0
    )

    # =========================
    # 3. FEATURES (ANTI-LEAKAGE)
    # =========================
    FEATURES = [
             "Sector",
        "Region_std",
        "Debt To Equity",
        "Total Debt (M)",
        "Current Ratio",
        "Employees_Sector_Z"
           
        
    ]

    # sécurité (évite crash si colonne manque)
    FEATURES = [c for c in FEATURES if c in df.columns]

    X = df[FEATURES]
    y = df["Risk"]

    # =========================
    # 4. SPLIT
    # =========================
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        stratify=y,
        random_state=RANDOM_STATE
    )

    # =========================
    # 5. MODEL
    # =========================
    mlflow.set_experiment("risk_prediction_model")

    with mlflow.start_run(run_name="RandomForest_Risk"):

        rf = RandomForestClassifier(
            n_estimators=300,
            max_depth=10,
            min_samples_leaf=10,
            class_weight="balanced",
            random_state=RANDOM_STATE,
            n_jobs=-1
        )

        rf.fit(X_train, y_train)

        # =========================
        # 6. EVALUATION
        # =========================
        preds_proba = rf.predict_proba(X_test)[:, 1]
        auc = roc_auc_score(y_test, preds_proba)

        print(f"\nRF Risk AUC (SAFE): {auc:.4f}")

        # =========================
        # 7. LOG MLflow
        # =========================
        mlflow.log_param("model", "RandomForest_RISK")
        mlflow.log_metric("auc", auc)
        mlflow.sklearn.log_model(rf, "model")

        # =========================
        # 8. FEATURE IMPORTANCE
        # =========================
        fi = pd.Series(rf.feature_importances_, index=FEATURES)\
               .sort_values(ascending=False)

        print("\nTop Features RF:\n", fi.head(10))


if __name__ == "__main__":
    run_rf_risk()