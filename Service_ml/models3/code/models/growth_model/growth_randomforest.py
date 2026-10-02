

import os
import sys
import pandas as pd
import mlflow
import mlflow.sklearn
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, f1_score, accuracy_score, roc_auc_score, confusion_matrix

# Configuration des chemins
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from config import DATA_PROCESSED, MODELS_DIR, RANDOM_STATE

EXPERIMENT_NAME = "profitable_model_"
MODEL_NAME      = "RandomForest"
TARGET          = "Profitable"

FEATURES = [
     "Sector",
        "Beta",
        "Region_std",
        "Net_Debt",
]


def load_data():
    """Charge les datasets pré-traités"""
    train_path = os.path.join(DATA_PROCESSED, "train_preprocessed.csv")
    test_path = os.path.join(DATA_PROCESSED, "test_preprocessed.csv")

    train_df = pd.read_csv(train_path)
    test_df = pd.read_csv(test_path)

    return train_df, test_df

def get_model():
    
    return RandomForestClassifier(
        n_estimators=300,
        max_depth=10,
        min_samples_split=5,
        min_samples_leaf=2,
        class_weight="balanced",
        random_state=RANDOM_STATE,
        n_jobs=-1
    )

def run_train_pipeline():
    # 1. Chargement
    train_df, test_df = load_data()

    X_train = train_df[FEATURES]
    y_train = train_df[TARGET].astype(int)
    X_test  = test_df[FEATURES]
    y_test  = test_df[TARGET].astype(int)

    # 2. MLflow Setup
    mlflow.set_experiment(EXPERIMENT_NAME)

    with mlflow.start_run(run_name=MODEL_NAME):
        # 3. Entraînement
        model = get_model()
        # Log des paramètres automatiquement
        mlflow.log_params(model.get_params())
        
        model.fit(X_train, y_train)

        # 4. Évaluation
        proba = model.predict_proba(X_test)[:, 1]
        
        # On peut ajuster le seuil ici comme dans ton script XGBoost
        threshold = 0.50 
        preds = (proba >= threshold).astype(int)

        auc = roc_auc_score(y_test, proba)
        f1 = f1_score(y_test, preds, average="weighted")
        acc = accuracy_score(y_test, preds)

        # 5. Affichage des résultats
        print("\n" + "=" * 45)
        print(f"   MODÈLE : {MODEL_NAME}")
        print(f"   AUC TEST FINAL : {auc:.4f}")
        print(f"   ACCURACY       : {acc:.4f}")
        print("=" * 45)
        print(classification_report(y_test, preds, target_names=['Non profitable','Profitable']))
        print("Matrice de Confusion:\n", confusion_matrix(y_test, preds))

        # 6. Sauvegarde et Logging MLflow
        model_path = os.path.join(MODELS_DIR, "random_forest_model.pkl")
        joblib.dump(model, model_path)

        mlflow.log_metric("test_auc", auc)
        mlflow.log_metric("f1_weighted", f1)
        mlflow.sklearn.log_model(model, "model")

        # Importance des variables
        fi = pd.Series(
            model.feature_importances_,
            index=X_train.columns
        ).sort_values(ascending=False)

        print("\nTOP FEATURES:")
        print(fi.head(10))
        print("=" * 45)

    return model

if __name__ == "__main__":
    run_train_pipeline()