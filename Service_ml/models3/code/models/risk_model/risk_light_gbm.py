import os
import sys
import pandas as pd
import numpy as np
import joblib

from lightgbm import LGBMClassifier
from sklearn.metrics import roc_auc_score, f1_score, confusion_matrix, classification_report
from sklearn.model_selection import train_test_split

# =========================================================
# PATH & CONFIG
# =========================================================
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from config import DATA_PROCESSED, MODELS_DIR, RANDOM_STATE

MODEL_PATH = os.path.join(MODELS_DIR, "risk_model_lgbm.joblib")

# =========================================================
# TARGET GENERATION (NO LEAKAGE)
# =========================================================
def create_risk_target(df, threshold=None):
    df = df.copy()

    risk_score = (
        0.4 * df["Revenue_per_Employee"].rank(pct=True) +
        0.3 * df["Company_Age"].rank(pct=True) +
        0.3 * df["Beta"].rank(pct=True)
    )

    if threshold is None:
        threshold = risk_score.quantile(0.80)
        print(f"--- Seuil Risk (train) : {threshold:.4f}")

    df["Risk"] = (risk_score > threshold).astype(int)
    return df, threshold


# =========================================================
# TRAINING
# =========================================================
def train():

   
    train_path = os.path.join(DATA_PROCESSED, "train_preprocessed.csv")
    test_path = os.path.join(DATA_PROCESSED, "test_preprocessed.csv")

    df_train = pd.read_csv(train_path)
    df_test = pd.read_csv(test_path)

    print("\nDATA LOADED")
    print("Train:", df_train.shape)
    print("Test :", df_test.shape)

    # -----------------------
    # TARGET
    # -----------------------
    df_train, threshold_val = create_risk_target(df_train)
    df_test, _ = create_risk_target(df_test, threshold=threshold_val)

    print("\nTARGET CREATED")

    # -----------------------
    # FEATURES
    # -----------------------
    FEATURES = [
       "Sector",
        "Region_std",
        "Debt To Equity",
        "Total Debt (M)",
        "Current Ratio",
        "Employees_Sector_Z"
    ]

    forbidden = ["Revenue_per_Employee", "Company_Age", "Beta"]
    FEATURES = [f for f in FEATURES if f in df_train.columns and f not in forbidden]

    X_train_full = df_train[FEATURES]
    y_train_full = df_train["Risk"]

    X_test = df_test[FEATURES]
    y_test = df_test["Risk"]

    # -----------------------
    # SPLIT VALIDATION
    # -----------------------
    X_train, X_val, y_train, y_val = train_test_split(
        X_train_full,
        y_train_full,
        test_size=0.15,
        random_state=RANDOM_STATE,
        stratify=y_train_full
    )

    
    cat_features = [c for c in ["Industry_Group", "Sector"] if c in FEATURES]

   
    for c in cat_features:
        X_train[c] = X_train[c].astype("category")
        X_val[c] = X_val[c].astype("category")
        X_test[c] = X_test[c].astype("category")

   
    # MODEL LIGHTGBM
 
    model = LGBMClassifier(
        n_estimators=2000,
        learning_rate=0.01,
        num_leaves=31,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=RANDOM_STATE
    )

    print(f"\nTRAINING LIGHTGBM ON {len(FEATURES)} FEATURES...")

    model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        eval_metric="auc"
    )


    # THRESHOLD 
    val_probs = model.predict_proba(X_val)[:, 1]

    best_t = 0.5
    best_f1 = 0

    for t in np.linspace(0.35, 0.65, 30):
        preds = (val_probs > t).astype(int)
        if len(np.unique(preds)) > 1:
            score = f1_score(y_val, preds)
            if score > best_f1:
                best_f1 = score
                best_t = t

    print(f"\nBEST THRESHOLD : {best_t:.3f}")

    # =========================================================
    # EVALUATION
    probs = model.predict_proba(X_test)[:, 1]
    preds = (probs > best_t).astype(int)

    print("\n" + "="*40)
    print("     FINAL RESULTS (LIGHTGBM)")
    print("="*40)

    print(f"AUC : {roc_auc_score(y_test, probs):.4f}")
    print(f"F1  : {f1_score(y_test, preds):.4f}")

    print("\nCONFUSION MATRIX:")
    print(confusion_matrix(y_test, preds))

    print("\nCLASSIFICATION REPORT:")
    print(classification_report(y_test, preds))

  
    # SAVE MODEL
   
    os.makedirs(MODELS_DIR, exist_ok=True)

    joblib.dump({
        "model": model,
        "features": FEATURES,
        "threshold": best_t,
        "risk_threshold_logic": threshold_val
    }, MODEL_PATH)

    print(f"\nMODEL SAVED: {MODEL_PATH}")
    print("TRAINING DONE (LIGHTGBM)")


if __name__ == "__main__":
    train()