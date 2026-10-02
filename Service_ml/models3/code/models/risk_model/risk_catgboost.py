import os
import sys
import pandas as pd
import numpy as np
import joblib

from catboost import CatBoostClassifier
from sklearn.metrics import roc_auc_score, f1_score, confusion_matrix
from sklearn.model_selection import train_test_split

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from config import DATA_PROCESSED, MODELS_DIR, RANDOM_STATE

MODEL_PATH = os.path.join(MODELS_DIR, "risk_model.joblib")


# =========================
# TARGET 
# =========================
def create_risk_target(df, threshold=None):
    df = df.copy()

    # sécurisation des données utilisées
    debt_to_revenue = df["Debt_to_Revenue"].replace([np.inf, -np.inf], np.nan).fillna(0)
    net_debt = df["Net_Debt"].replace([np.inf, -np.inf], np.nan).fillna(0)
    revenue_per_employee = df["Revenue_per_Employee"].replace([np.inf, -np.inf], np.nan).fillna(0)

    # risk score propre (ranking stable)
    risk_score = (
        0.4 * debt_to_revenue.rank(pct=True) +
        0.3 * net_debt.rank(pct=True) +
        0.3 * (1 - revenue_per_employee.rank(pct=True))
    )

    # seuil automatique
    if threshold is None:
        threshold = risk_score.quantile(0.70)
        print(f"--- Nouveau Seuil de risque (Train) : {threshold:.4f}")

    df["Risk"] = (risk_score > threshold).astype(int)
    return df, threshold


# =========================
# TRAINING PIPELINE
# =========================

def train():

    # 1. LOAD DATA
    train_path = os.path.join(DATA_PROCESSED, "train_catboost.csv")
    test_path = os.path.join(DATA_PROCESSED, "test_catboost.csv")

    df_train = pd.read_csv(train_path)
    df_test = pd.read_csv(test_path)

    # 2. CLEAN BASIC
    for df in [df_train, df_test]:
        if "Region_std" in df.columns:
            df["Region_std"] = df["Region_std"].fillna("Unknown")

    # 3. CREATE TARGET
    df_train, train_threshold = create_risk_target(df_train)
    df_test, _ = create_risk_target(df_test, threshold=train_threshold)

    # 4. FEATURES 
    FEATURES = [
        "Sector",
        "Region_std",
        "Debt To Equity",
        "Total Debt (M)",
        "Current Ratio",
        "Employees_Sector_Z"
    ]

    # sécurité colonnes existantes
    FEATURES = [f for f in FEATURES if f in df_train.columns]

    # 5. SPLIT
    X = df_train[FEATURES]
    y = df_train["Risk"]

    X_test = df_test[FEATURES]
    y_test = df_test["Risk"]

    X_train, X_val, y_train, y_val = train_test_split(
        X, y,
        test_size=0.2,
        random_state=RANDOM_STATE,
        stratify=y
    )

    # 6. CATEGORICAL FEATURES
    cat_features = [f for f in [ "Sector", "Region_std"] if f in FEATURES]

    # 7. MODEL CATBOOST (STABLE CONFIG)
    model = CatBoostClassifier(
        iterations=800,
        learning_rate=0.08,
        depth=6,
        l2_leaf_reg=6,
        loss_function="Logloss",
        eval_metric="AUC",
        class_weights=[1, 3],
        cat_features=cat_features,
        random_seed=RANDOM_STATE,
        verbose=100
    )

    print("\nENTRAÎNEMENT MODEL...")
    print(f"FEATURES: {FEATURES}")
    print(f"CATEGORICAL: {cat_features}")

    model.fit(X_train, y_train, eval_set=(X_val, y_val), use_best_model=True)

    # 8. SEUIL OPTIMISATION
    val_probs = model.predict_proba(X_val)[:, 1]

    best_t = 0.5
    best_f1 = 0

    for t in np.linspace(0.4, 0.7, 60):
        preds = (val_probs > t).astype(int)

        if len(np.unique(preds)) > 1:
            score = f1_score(y_val, preds)
            if score > best_f1:
                best_f1 = score
                best_t = t

    print(f"\nSEUIL OPTIMISÉ: {best_t:.3f}")

    # 9. EVALUATION
    test_probs = model.predict_proba(X_test)[:, 1]
    test_preds = (test_probs > best_t).astype(int)

    print("\n====================")
    print(f"AUC  : {roc_auc_score(y_test, test_probs):.4f}")
    print(f"F1   : {f1_score(y_test, test_preds):.4f}")
    print("====================")

    print("\nCONFUSION MATRIX:")
    print(confusion_matrix(y_test, test_preds))

    # 10. SAVE MODEL
    os.makedirs(MODELS_DIR, exist_ok=True)

    joblib.dump({
        "model": model,
        "features": FEATURES,
        "threshold": best_t,
        "risk_threshold_logic": train_threshold
    }, MODEL_PATH)

    # 11. IMPORTANCE
    print("\nFEATURE IMPORTANCE:")
    importances = model.get_feature_importance()

    for f, imp in sorted(zip(FEATURES, importances), key=lambda x: x[1], reverse=True):
        print(f"{f}: {imp:.2f}")


# =========================
# RUN
# =========================
if __name__ == "__main__":
    train()