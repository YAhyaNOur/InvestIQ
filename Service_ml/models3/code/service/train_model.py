import os
import pandas as pd
import mlflow
from catboost import CatBoostClassifier
from sklearn.metrics import roc_auc_score, classification_report
import joblib

# =========================
# PATHS
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))

DATA_PROCESSED = os.path.join(ROOT_DIR, "data", "processed")
MODELS_DIR = os.path.join(ROOT_DIR, "models")
RANDOM_STATE = 42

TARGET = "Profitable"


# FEATURES
CAT_FEATURES = [
    "Sector",
    "Industry_Group",
    "Region_std"
]

NUM_FEATURES = [
   
    "Revenue_Per_Employee",
    "Net_Debt",
    "Beta"
]

FEATURES = CAT_FEATURES + NUM_FEATURES


# LOAD DATA

def load_data():
    train_path = os.path.join(DATA_PROCESSED, "train_catboost.csv")
    test_path = os.path.join(DATA_PROCESSED, "test_catboost.csv")

    train_df = pd.read_csv(train_path)
    test_df = pd.read_csv(test_path)

   
    for df in [train_df, test_df]:
        for col in CAT_FEATURES:
            if col in df.columns:
                df[col] = df[col].astype(str).fillna("Unknown")

        # numeric safety
        for col in NUM_FEATURES:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    return train_df, test_df


# MODEL 
def get_model():
    return CatBoostClassifier(
        iterations=2000,             
        learning_rate=0.02,          
        depth=8,                      
        loss_function="Logloss",
        eval_metric="AUC",
        random_seed=RANDOM_STATE,
        verbose=200
        
    )



# TRAIN PIPELINE

def run_train_pipeline():

    train_df, test_df = load_data()

    X_train = train_df[FEATURES]
    y_train = train_df[TARGET].astype(int)

    X_test = test_df[FEATURES]
    y_test = test_df[TARGET].astype(int)

    mlflow.set_experiment("recommendation_model")

    with mlflow.start_run(run_name="CatBoost_reco_model_v2"):

        model = get_model()

        model.fit(
            X_train,
            y_train,
            cat_features=CAT_FEATURES,
            eval_set=(X_test, y_test),
            use_best_model=True
        )

      
        proba = model.predict_proba(X_test)[:, 1]
        auc = roc_auc_score(y_test, proba)

        print("\nAUC :", auc)

        preds = (proba >= 0.5).astype(int)
        print(classification_report(y_test, preds))

        
        # FEATURE 
        importance_df = pd.DataFrame({
            "Feature": FEATURES,
            "Importance": model.get_feature_importance()
        }).sort_values(by="Importance", ascending=False)

        print("\nIMPORTANCE:")
        print(importance_df)
        print(pd.Series(proba).describe())
       
        # SAVE MODEL 
        os.makedirs(MODELS_DIR, exist_ok=True)

        package = {
            "model": model,
            "features": FEATURES,
            "cat_features": CAT_FEATURES,
            "threshold": 0.5,
            "allowed_values": {
                col: train_df[col].unique().tolist() for col in CAT_FEATURES
            }
        }

        joblib_path = os.path.join(MODELS_DIR, "model_recommendation.joblib")
        joblib.dump(package, joblib_path)

        print(f"\n[OK] Saved at: {joblib_path}")

    return model


if __name__ == "__main__":
    run_train_pipeline()