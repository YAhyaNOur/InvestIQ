import os
import mlflow

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MLFLOW_DIR = os.path.join(BASE_DIR, "mlruns")

mlflow.set_tracking_uri(f"file:{MLFLOW_DIR}")
mlflow.set_experiment("profitable")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MLFLOW_DIR = os.path.join(BASE_DIR, "mlruns")

mlflow.set_tracking_uri(f"file:{MLFLOW_DIR}")
mlflow.set_experiment("profitable")


import mlflow

mlflow.set_experiment("test_debug")

with mlflow.start_run():
    mlflow.log_metric("test", 1)
    print("RUN OK")