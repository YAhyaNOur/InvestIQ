import os
import joblib
import pandas as pd
import numpy as np
import mlflow
import mlflow.sklearn
from pathlib import Path
from sklearn.preprocessing import MinMaxScaler
from sklearn.ensemble import IsolationForest

CURRENT = Path(__file__).resolve()
ROOT = CURRENT.parents[3]

DATA_PATH = ROOT / "data" / "processed" / "train_preprocessed.csv"
MODEL_PATH = ROOT / "models" / "hybrid_score_model.joblib"
OUTPUT_PATH = ROOT / "data" / "processed" / "score_results.csv"

MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)

# =========================================================
# MLFLOW
# =========================================================
mlflow.set_experiment("score_Model")

with mlflow.start_run(run_name="IsolationForest_Training"):

    FEATURES = [
        "Debt_to_Revenue",
        "Current Ratio",
        "Revenue_per_Employee",
        "Net_Debt",
        "Employees_Sector_Z",
    ]

    mlflow.log_params({
        "features": FEATURES,
        "contamination": 0.02,
        "random_state": 42
    })

    # =========================================================
    # DATA
    # =========================================================
    df = pd.read_csv(DATA_PATH).replace([np.inf, -np.inf], np.nan).dropna()

    X = df[FEATURES].copy()

    # =========================================================
    # SCALING
    # =========================================================
    scaler = MinMaxScaler()
    X_scaled = pd.DataFrame(scaler.fit_transform(X), columns=FEATURES)

    # =========================================================
    # ISOLATION FOREST
    # =========================================================
    iso = IsolationForest(
        contamination=0.02,
        random_state=42
    )

    iso.fit(X_scaled)

    df["anomaly_flag"] = iso.predict(X_scaled)
    df["is_anomaly"] = (df["anomaly_flag"] == -1).astype(int)

    df["anomaly_score_raw"] = iso.decision_function(X_scaled)

    score_min = df["anomaly_score_raw"].min()
    score_max = df["anomaly_score_raw"].max()

    df["anomaly_severity"] = (
        1 - (
            (df["anomaly_score_raw"] - score_min) /
            (score_max - score_min + 1e-9)
        )
    ).clip(0, 1)

    # =========================================================
    # THRESHOLDS MÉTIER
    # =========================================================
    q90_net_debt = float(df["Net_Debt"].quantile(0.90))
    q10_rev_per_emp = float(df["Revenue_per_Employee"].quantile(0.10))

    # =========================================================
    # FRAUD SCORE 
    # =========================================================
    df["fraud_score"] = 0

    # AI signal (réduit)
    df.loc[df["is_anomaly"] == 1, "fraud_score"] += 20

    # Rules métier (soft)
    df.loc[df["Debt_to_Revenue"] > 1.5, "fraud_score"] += 15
    df.loc[df["Current Ratio"] < 0.7, "fraud_score"] += 15
    df.loc[df["Net_Debt"] > q90_net_debt, "fraud_score"] += 10
    df.loc[df["Revenue_per_Employee"] < q10_rev_per_emp, "fraud_score"] += 10
    df.loc[df["Employees_Sector_Z"].abs() > 3, "fraud_score"] += 5

    df["fraud_score"] = df["fraud_score"].clip(0, 100)

    # =========================================================
    # LABELS 
    # =========================================================
    def label(x):
        if x >= 85:
            return "HIGH FRAUD RISK"
        elif x >= 65:
            return "SUSPICIOUS"
        elif x >= 40:
            return "WATCH"
        elif x >= 15:
            return "LOW RISK"
        else:
            return "NORMAL"

    df["fraud_label"] = df["fraud_score"].apply(label)

    # =========================================================
    # LOG MLFLOW
    # =========================================================
    mlflow.log_metric("fraud_mean", float(df["fraud_score"].mean()))
    mlflow.log_metric("anomaly_count", int(df["is_anomaly"].sum()))

    # =========================================================
    # SAVE MODEL
    # =========================================================
    model_artifact = {
        "scaler": scaler,
        "model": iso,
        "features": FEATURES,
        "thresholds": {
            "net_debt_q90": q90_net_debt,
            "rev_per_emp_q10": q10_rev_per_emp,
        },
        "score_bounds": {
            "anomaly_score_min": score_min,
            "anomaly_score_max": score_max,
        }
    }

    joblib.dump(model_artifact, MODEL_PATH)
    mlflow.sklearn.log_model(iso, "isolation_forest_model")

    df.to_csv(OUTPUT_PATH, index=False)
    mlflow.log_artifact(OUTPUT_PATH)

    # =========================================================
    # REPORT
    # =========================================================
    print("\n--- FRAUD DISTRIBUTION ---")
    print(df["fraud_label"].value_counts())

    print("\n--- TOP ANOMALIES ---")
    print(
        df[df["is_anomaly"] == 1]
        .nsmallest(5, "anomaly_score_raw")[
            FEATURES + ["fraud_score", "fraud_label"]
        ]
    )

    print("\nMODEL SAVED:", MODEL_PATH)