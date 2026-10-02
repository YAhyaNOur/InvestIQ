import os
import sys
import numpy as np
import pandas as pd
import mlflow
import mlflow.catboost
from catboost import CatBoostClassifier
from sklearn.metrics import roc_auc_score, classification_report, confusion_matrix
import joblib

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from config import DATA_PROCESSED, RANDOM_STATE, MODELS_DIR

TARGET = "Growth"
CAT_FEATURES = ["Region_std", "Sector"]

FEATURES = [
    "Sector",
    "Region_std",
    "Beta",
    "Net_Debt",
    "Revenue Growth",
    
    
    
]


def load_data():
    train_path = os.path.join(DATA_PROCESSED, "train_catboost.csv")
    test_path = os.path.join(DATA_PROCESSED, "test_catboost.csv")

    train_df = pd.read_csv(train_path)
    test_df = pd.read_csv(test_path)

    for df in [train_df, test_df]:
        for col in CAT_FEATURES:
            if col in df.columns:
                df[col] = df[col].astype(str).fillna("Unknown")

    return train_df, test_df


def get_model():
    return CatBoostClassifier(
        iterations=1500,
        learning_rate=0.025,
        depth=7,
        loss_function="Logloss",
        eval_metric="AUC",
        random_seed=RANDOM_STATE,
        scale_pos_weight=2.4,
        l2_leaf_reg=8,
        
        early_stopping_rounds=100,
        verbose=200
    )


def run_train_pipeline():

    train_df, test_df = load_data()

    X_train = train_df[FEATURES]
    y_train = train_df[TARGET].astype(int)

    X_test = test_df[FEATURES]
    y_test = test_df[TARGET].astype(int)

    mlflow.set_experiment("profitable")

    with mlflow.start_run(run_name="CatBoost_growth"):

        model = get_model()

        model.fit(
            X_train,
            y_train,
            cat_features=CAT_FEATURES,
            eval_set=(X_test, y_test)
        )

        # =========================
        # EVALUATION
        # =========================
        test_preds_proba = model.predict_proba(X_test)[:, 1]

        threshold = 0.48
        test_preds = (test_preds_proba >= threshold).astype(int)

        test_auc = roc_auc_score(y_test, test_preds_proba)

        print("\n" + "=" * 40)
        print(f"AUC TEST FINAL : {test_auc:.4f}")
        print("=" * 40)

        print(classification_report(y_test, test_preds))
        print("Matrice de Confusion:\n", confusion_matrix(y_test, test_preds))

        # =========================
        # SAVE MODEL (CBM)
        # =========================
        model_path = os.path.join(MODELS_DIR, "profit_model.cbm")
        model.save_model(model_path)

        # =========================
        # SAVE JOBLIB PACKAGE
        # =========================
        package = {
            "model": model,
            "features": FEATURES,
            "cat_features": CAT_FEATURES,
            "threshold": threshold
    }

        joblib_path = os.path.join(MODELS_DIR, "growth_score_model.joblib")
        joblib.dump(package, joblib_path)

        print(f"\n[MODEL SAVED] -> {joblib_path}")
        

        # =========================
        # MLflow
        # =========================
        mlflow.log_metric("test_auc", test_auc)
        mlflow.catboost.log_model(model, "model")

        fi = pd.Series(
            model.get_feature_importance(),
            index=FEATURES
        ).sort_values(ascending=False)

        print("\nTOP FEATURES:")
        print(fi.head(10))

    return model

"""
def predict_new_companies(model):
    print("\n" + "=" * 40)
    print("TEST SUR 4 SOCIÉTÉS (PROFILS VARIÉS)")
    print("=" * 40)
    
    test_data = pd.DataFrame([
        {
            "Sector": "Technology",
            #"Industry_Group": "Software & Services",
            "Beta": 1.1,
            "Region_std": "Americas",
            "Net_Debt": 0.5,
            "EBITDA Margins": 0.25 
        },
        {
            "Sector": "Energy",
            #"Industry_Group": "Energy",
            "Beta": 1.5,
            "Region_std": "Europe",
            "Net_Debt": 15.0,
            "EBITDA Margins": -0.05 
        },
        {
            "Sector": "Healthcare",
            #"Industry_Group": "Pharmaceuticals",
            "Beta": 0.8,
            "Region_std": "Americas",
            "Net_Debt": 12.0,      # Beaucoup de dette
            "EBITDA Margins": 0.40  
        },
        {
            "Sector": "Consumer Discretionary",
            #"Industry_Group": "Retailing",
            "Beta": 1.0,
            "Region_std": "Asia",
            "Net_Debt": 2.0,
            "EBITDA Margins": 0.05 
        },
        {
        "Sector": "Technology",
        #"Industry_Group": "Software & Services",
        "Beta": 1.2,
        "Region_std": "North_America",
        "Net_Debt": -50,
        "EBITDA Margins": 0.35
    },
    {
        "Sector": "Industrials",
        #"Industry_Group": "Aerospace & Defense",
        "Beta": 1.3,
        "Region_std": "North_America",
        "Net_Debt": 800,
        "EBITDA Margins": 0.10
    },
    {
        "Sector": "Technology",
        #"Industry_Group": "Hardware",
        "Beta": 1.6,
        "Region_std": "Europe",
        "Net_Debt": 1500,
         "EBITDA Margins": -0.05
    },{
        "Sector": "Technology",
       # "Industry_Group": "Software & Services",
        "Beta": 1.25,
        "Region_std": "North_America",
        "Net_Debt": 80,
         "EBITDA Margins": 0.22
    },
    {
        "Sector": "Technology",
        #"Industry_Group": "Software & Services",
        "Beta": 1.4,
        "Region_std": "Europe",
        "Net_Debt": 150,
         "EBITDA Margins": 0.08
    },
    {
        "Sector": "Energy",
        #"Industry_Group": "Energy",
        "Beta": 1.7,
        "Region_std": "North_America",
        "Net_Debt": 600,
        "EBITDA Margins": -0.02
    },
    {
        "Sector": "Finance",
        #"Industry_Group": "Capital Markets",
        "Beta": 1.0,
        "Region_std": "Europe",
        "Net_Debt": 300,
        "EBITDA Margins": 0.18
    },
        {
        "Sector": "Consumer",
        #"Industry_Group": "Retailing",
        "Beta": 0.95,
        "Region_std": "Asia",
        "Net_Debt": 120,
        "EBITDA Margins": 0.12
    }
        ])

    # Formatage
    for col in CAT_FEATURES:
        test_data[col] = test_data[col].astype(str)

    # Prédiction
    probas = model.predict_proba(test_data[FEATURES])[:, 1]
    
    for i, p in enumerate(probas):
        status = "PROFITABLE" if p >= 0.5 else "NON-PROFITABLE"
        print(f"Société {i+1} ({test_data.iloc[i]['Sector']}) :")
        print(f" -> Probabilité : {p:.2%}")
        print(f" -> Verdict     : {status}\n")"""
if __name__ == "__main__":
    trained_model = run_train_pipeline()
    """predict_new_companies(trained_model)"""