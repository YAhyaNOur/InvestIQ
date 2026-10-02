import os
import sys
import numpy as np
import pandas as pd
import mlflow
import joblib

from lightgbm import LGBMClassifier
from sklearn.metrics import roc_auc_score, classification_report, confusion_matrix

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from config import DATA_PROCESSED, RANDOM_STATE, MODELS_DIR

TARGET = "Profitable"

CAT_FEATURES = ["Region_std",  "Sector"]

FEATURES = [
        "Sector",
        "Beta",
        "Region_std",
        "Net_Debt",
]

CAT_FEATURES = ["Sector",  "Region_std"]


def load_data():
    train_path = os.path.join(DATA_PROCESSED, "train_preprocessed.csv")
    test_path = os.path.join(DATA_PROCESSED, "test_preprocessed.csv")

    train_df = pd.read_csv(train_path)
    test_df = pd.read_csv(test_path)

    for df in [train_df, test_df]:
        for col in CAT_FEATURES:
            if col in df.columns:
                df[col] = df[col].astype("category")

    return train_df, test_df



def get_model():
    return LGBMClassifier(
        n_estimators=2000,
        learning_rate=0.03,
        num_leaves=31,
        max_depth=-1,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=RANDOM_STATE
    )



def run_train_pipeline():

    train_df, test_df = load_data()

    X_train = train_df[FEATURES]
    y_train = train_df[TARGET].astype(int)

    X_test = test_df[FEATURES]
    y_test = test_df[TARGET].astype(int)

    mlflow.set_experiment("profitable_model_")

    with mlflow.start_run(run_name="LightGBM_model"):

        model = get_model()

        model.fit(
            X_train,
            y_train,
            categorical_feature=CAT_FEATURES
        )

      
        # PREDICTION
       
        proba = model.predict_proba(X_test)[:, 1]

        threshold = 0.48
        preds = (proba >= threshold).astype(int)

        auc = roc_auc_score(y_test, proba)

        print("\n" + "=" * 40)
        print(f"AUC TEST FINAL : {auc:.4f}")
        print("=" * 40)

        print(classification_report(y_test, preds))
        print("Matrice de Confusion:\n", confusion_matrix(y_test, preds))

        # =========================
        # SAVE
        # =========================
        model_path = os.path.join(MODELS_DIR, "profit_model_lgbm.pkl")
        joblib.dump(model, model_path)

        mlflow.log_metric("test_auc", auc)
        mlflow.sklearn.log_model(model, "model")

        # Feature importance
        fi = pd.Series(model.feature_importances_, index=FEATURES).sort_values(ascending=False)
        print("\nTOP FEATURES:")
        print(fi)

    return model


def predict_new_companies(model):
    print("\n" + "=" * 40)
    print("TEST PRÉDICTIF SUR NOUVEAUX PROFILS")
    print("=" * 40)
    
    # On crée un petit DataFrame avec tes 4 profils de test
    test_cases = [
        {
            "Sector": "Technology", "Efficiency_Index": 1.5, "Industry_Group": "Software & Services",
            "Beta": 1.1, "Region_std": "Americas", "Net_Debt": 0.5, "EBITDA Margins": 0.25
        },
        {
            "Sector": "Energy", "Efficiency_Index": 0.7, "Industry_Group": "Energy",
            "Beta": 1.5, "Region_std": "Europe", "Net_Debt": 15.0, "EBITDA Margins": -0.05
        },
        {
            "Sector": "Healthcare", "Efficiency_Index": 2.0, "Industry_Group": "Pharmaceuticals",
            "Beta": 0.8, "Region_std": "Americas", "Net_Debt": 12.0, "EBITDA Margins": 0.40
        },
        {
            "Sector": "Consumer Discretionary", "Efficiency_Index": 1.1, "Industry_Group": "Retailing",
            "Beta": 1.0, "Region_std": "Asia", "Net_Debt": 2.0, "EBITDA Margins": 0.05
        }
    ]
    
    df_new = pd.DataFrame(test_cases)
    
    # Important : XGBoost a besoin de voir les colonnes "object" comme "category"
    for col in CAT_FEATURES:
        if col in df_new.columns:
            df_new[col] = df_new[col].astype("category")

    # Prédiction des probabilités
    probas = model.predict_proba(df_new[FEATURES])[:, 1]
    
    for i, p in enumerate(probas):
        # On utilise ton threshold de 0.48
        verdict = "PROFITABLE" if p >= 0.48 else "NON-PROFITABLE"
        print(f"Société {i+1} ({test_cases[i]['Sector']}) :")
        print(f" -> Probabilité : {p:.2%}")
        print(f" -> Verdict     : {verdict}\n")

# Modifie ton bloc main pour appeler la fonction
if __name__ == "__main__":
    trained_model = run_train_pipeline()
    predict_new_companies(trained_model)