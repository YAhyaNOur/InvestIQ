import os
import sys
import pandas as pd
import numpy as np
import mlflow
import mlflow.lightgbm
import lightgbm as lgb
from sklearn.metrics import roc_auc_score, accuracy_score, classification_report, confusion_matrix
import joblib

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from config import DATA_PROCESSED, RANDOM_STATE, MODELS_DIR

def run_lgb_risk():
   
    train_df = pd.read_csv(os.path.join(DATA_PROCESSED, "train_preprocessed.csv"))
    test_df = pd.read_csv(os.path.join(DATA_PROCESSED, "test_preprocessed.csv"))

    group_cols = ["Sector", "Region_std"]
    
   
    for df in [train_df, test_df]:
        df["risk_score"] = (
            0.4 * (
                df["Debt To Equity"] /
                (df.groupby(group_cols)["Debt To Equity"].transform("median") + 1e-6)
            )
            + 0.3 * (df["Net_Debt"] > 0).astype(int)
            + 0.2 * (
                df["Company_Age"] <
                df.groupby(group_cols)["Company_Age"].transform("median")
            ).astype(int)
            + 0.1 * (df["Current Ratio"] < 1).astype(int)
        )

        df["Risk"] = (
            df["risk_score"] >
            df.groupby(group_cols)["risk_score"].transform(lambda x: x.quantile(0.75))
        ).astype(int)
  
  
    FEATURES = [
        "Revenue (M USD)_Sector_Z", 
        "Employees_Sector_Z", 
        "Revenue_Per_Employee_Sector_Z",
        "Log_Revenue", 
        "Company_Age",
        "Efficiency_Index", 
        "Age_Size_Ratio", 
    ]
    
    X_train = train_df[FEATURES]
    y_train = train_df["Risk"]
    X_test = test_df[FEATURES]
    y_test = test_df["Risk"]

    # --- MLFLOW EXPERIMENT ---
    mlflow.set_experiment("risk_prediction_model")

    with mlflow.start_run(run_name="LightGBM_Risk_Tuned"):
        
        params = {
            "objective": "binary",
            "metric": "auc",
            "boosting_type": "gbdt",
            "learning_rate": 0.03,
            "num_leaves": 31,
            "max_depth": -1,
            "min_data_in_leaf": 20,
            "feature_fraction": 0.8,
            "bagging_fraction": 0.8,
            "bagging_freq": 5,
            "lambda_l1": 0.1,
            "lambda_l2": 0.1,
            "is_unbalance": True,
            "seed": RANDOM_STATE,
            "verbosity": -1
        }
        
        mlflow.log_params(params)

        train_set = lgb.Dataset(X_train, label=y_train)
        valid_set = lgb.Dataset(X_test, label=y_test)

        model = lgb.train(
            params,
            train_set,
            num_boost_round=2000,
            valid_sets=[valid_set],
            callbacks=[
                lgb.early_stopping(100),
                lgb.log_evaluation(50)
            ]
        )

        # 4. Calcul des Métriques
        y_proba = model.predict(X_test)
        y_pred = (y_proba >= 0.5).astype(int)

        auc = roc_auc_score(y_test, y_proba)
        acc = accuracy_score(y_test, y_pred)
        
       
        print("\n" + "="*35)
        print(" RÉSULTATS SUR LE TEST SET DÉDIÉ ")
        print("="*35)
        print(f"AUC Score : {auc:.4f}")
        print(f"Accuracy  : {acc:.4f}")
        print("\nClassification Report:")
        print(classification_report(y_test, y_pred))
        print("="*35)

       
        mlflow.log_metric("auc", auc)
        mlflow.log_metric("accuracy", acc)
        
        # Importance des features
        importance = pd.DataFrame({
            "feature": FEATURES,
            "importance": model.feature_importance()
        }).sort_values("importance", ascending=False)
        
        importance.to_csv("feature_importance_risk.csv", index=False)
        mlflow.log_artifact("feature_importance_risk.csv")

        mlflow.lightgbm.log_model(model, "risk_lgb_tuned")
        
        # Export final
        model_path = os.path.join(MODELS_DIR, "risk_model.joblib")
        joblib.dump(model, model_path)
        print(f"Modèle sauvegardé : {model_path}")

if __name__ == "__main__":
    run_lgb_risk()