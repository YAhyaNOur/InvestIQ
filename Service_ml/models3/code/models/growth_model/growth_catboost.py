import os
import sys
import numpy as np
import pandas as pd
import mlflow
import mlflow.catboost
from catboost import CatBoostClassifier
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import roc_auc_score, classification_report, confusion_matrix

# Configuration des chemins
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from config import DATA_PROCESSED, RANDOM_STATE, MODELS_DIR

TARGET = "Profitable"
CAT_FEATURES = ["Region_std", "Industry_Group", "Sector"]
FEATURES = [
   "Sector",
    "Industry_Group",
    "Beta",
    "Region_std",
    "Net_Debt",
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
        learning_rate=0.03,
        depth=6,
        loss_function="Logloss",
        eval_metric="AUC",
        random_seed=RANDOM_STATE,
        l2_leaf_reg=5,
        auto_class_weights="Balanced",
        early_stopping_rounds=100,
        verbose=0 # On réduit le bruit pendant la CV
    )

# ... (garder les imports et fonctions load_data / get_model identiques)

def run_train_pipeline():
    train_df, test_df = load_data()
    X_train = train_df[FEATURES]
    y_train = train_df[TARGET].astype(int)
    X_test = test_df[FEATURES]
    y_test = test_df[TARGET].astype(int)

    n_splits = 5
    skf = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=RANDOM_STATE)
    cv_aucs = []
    
    print(f"--- DÉBUT DE LA VALIDATION CROISÉE ({n_splits} FOLDS) ---")

    mlflow.set_experiment("profitable_model_")
    
    with mlflow.start_run(run_name="CatBoost_CV_Detailed"):
        for fold, (train_idx, val_idx) in enumerate(skf.split(X_train, y_train)):
            print(f"\n" + "-"*20)
            print(f" FOLD {fold+1} / {n_splits}")
            print("-"*20)
            
            X_tr, X_val = X_train.iloc[train_idx], X_train.iloc[val_idx]
            y_tr, y_val = y_train.iloc[train_idx], y_train.iloc[val_idx]

            model = get_model()
            model.fit(X_tr, y_tr, cat_features=CAT_FEATURES, eval_set=(X_val, y_val))
            
            # Métriques du Fold
            val_preds = model.predict(X_val)
            val_probs = model.predict_proba(X_val)[:, 1]
            
            fold_auc = roc_auc_score(y_val, val_probs)
            cv_aucs.append(fold_auc)
            
            # AFFICHAGE DES MÉTRIQUES PAR FOLD
            print(f"\nRésultats Validation Fold {fold+1}:")
            print(classification_report(y_val, val_preds))
            print(f"AUC: {fold_auc:.4f}")

        print("\n" + "="*50)
        print(" ENTRAÎNEMENT FINAL SUR TOUT LE TRAIN SET ")
        print("="*50)
        
        final_model = get_model()
        final_model.fit(X_train, y_train, cat_features=CAT_FEATURES, eval_set=(X_test, y_test))

        # Évaluation sur le Test Set
        test_preds = final_model.predict(X_test)
        test_probs = final_model.predict_proba(X_test)[:, 1]
        test_auc = roc_auc_score(y_test, test_probs)

        print("\n" + "*"*30)
        print(" PERFORMANCE FINALE SUR LE TEST SET ")
        print("*"*30)
        print(f"MOYENNE AUC CV : {np.mean(cv_aucs):.4f}")
        print(f"AUC TEST : {test_auc:.4f}")
        print("\nCLASSIFICATION REPORT FINAL :")
        print(classification_report(y_test, test_preds))
        print("\nMATRICE DE CONFUSION :")
        print(confusion_matrix(y_test, test_preds))

        # Sauvegarde
        final_model.save_model(os.path.join(MODELS_DIR, "profit_model.cbm"))
        
        mlflow.log_metric("mean_cv_auc", np.mean(cv_aucs))
        mlflow.log_metric("test_auc", test_auc)

    return final_model



def predict_new_companies(model):
    print("\n" + "=" * 40)
    print("TEST SUR 4 SOCIÉTÉS (PROFILS VARIÉS)")
    print("=" * 40)
    
    test_data = pd.DataFrame([
        {
            "Sector": "Technology",
            "Industry_Group": "Software & Services",
            "Beta": 1.1,
            "Region_std": "Americas",
            "Net_Debt": 0.5,
            "EBITDA Margins": 0.25  # Cas 1 : La pépite (Profitable)
        },
        {
            "Sector": "Energy",
            "Industry_Group": "Energy",
            "Beta": 1.5,
            "Region_std": "Europe",
            "Net_Debt": 15.0,
            "EBITDA Margins": -0.05 # Cas 2 : L'alerte rouge (Non-Profitable)
        },
        {
            "Sector": "Healthcare",
            "Industry_Group": "Pharmaceuticals",
            "Beta": 0.8,
            "Region_std": "Americas",
            "Net_Debt": 12.0,      # Beaucoup de dette
            "EBITDA Margins": 0.40  # MAIS marge énorme (Le test de force)
        },
        {
            "Sector": "Consumer Discretionary",
            "Industry_Group": "Retailing",
            "Beta": 1.0,
            "Region_std": "Asia",
            "Net_Debt": 2.0,
            "EBITDA Margins": 0.05  # Cas 4 : La zone grise (Marge faible)
        },
        {
        "Sector": "Technology",
        "Industry_Group": "Software & Services",
        "Beta": 1.2,
        "Region_std": "North_America",
        "Net_Debt": -50,
        "EBITDA Margins": 0.35
    },
    {
        "Sector": "Industrials",
        "Industry_Group": "Aerospace & Defense",
        "Beta": 1.3,
        "Region_std": "North_America",
        "Net_Debt": 800,
        "EBITDA Margins": 0.10
    },
    {
        "Sector": "Technology",
        "Industry_Group": "Hardware",
        "Beta": 1.6,
        "Region_std": "Europe",
        "Net_Debt": 1500,
        "EBITDA Margins": -0.05
    },{
        "Sector": "Technology",
        "Industry_Group": "Software & Services",
        "Beta": 1.25,
        "Region_std": "North_America",
        "Net_Debt": 80,
        "EBITDA Margins": 0.22
    },
    {
        "Sector": "Technology",
        "Industry_Group": "Software & Services",
        "Beta": 1.4,
        "Region_std": "Europe",
        "Net_Debt": 150,
        "EBITDA Margins": 0.08
    },
    {
        "Sector": "Energy",
        "Industry_Group": "Energy",
        "Beta": 1.7,
        "Region_std": "North_America",
        "Net_Debt": 600,
        "EBITDA Margins": -0.02
    },
    {
        "Sector": "Finance",
        "Industry_Group": "Capital Markets",
        "Beta": 1.0,
        "Region_std": "Europe",
        "Net_Debt": 300,
        "EBITDA Margins": 0.18
    },
        {
        "Sector": "Consumer",
        "Industry_Group": "Retailing",
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
        print(f" -> Verdict     : {status}\n")
if __name__ == "__main__":
    trained_model = run_train_pipeline()
    predict_new_companies(trained_model)
    