"""from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Literal
import pandas as pd
import joblib
from pathlib import Path

router = APIRouter()
MODEL_PATH = Path(__file__).resolve().parents[2] / "models" / "hybrid_score_model.joblib"

# Chargement sécurisé
try:
    artifact = joblib.load(MODEL_PATH)
    model, scaler, FEATURES = artifact["model"], artifact["scaler"], artifact["features"]
    thresholds, bounds = artifact["thresholds"], artifact["score_bounds"]
except Exception as e:
    raise RuntimeError(f"Erreur modèle : {e}")

class CompanyData(BaseModel):
    Debt_to_Revenue: float
    Current_Ratio: float
    Revenue_per_Employee: float
    Net_Debt: float
    Employees_Sector_Z: float

@router.post("/analyze")
def predict(data: CompanyData):
    # 1. Résolution mismatch : Current_Ratio (API) -> Current Ratio (Modèle)
    input_dict = data.model_dump()
    input_dict["Current Ratio"] = input_dict.pop("Current_Ratio")
    
    df_input = pd.DataFrame([input_dict])
    X_scaled_raw = scaler.transform(df_input[FEATURES])
    X_scaled = pd.DataFrame(X_scaled_raw, columns=FEATURES)

    # 2. IA : Isolation Forest
    is_anomaly = bool(model.predict(X_scaled)[0] == -1)
    anomaly_raw = float(model.decision_function(X_scaled)[0])
    
    # Normalisation de l'anomaly_score (0 à 1)
    div = (bounds["anomaly_score_max"] - bounds["anomaly_score_min"] + 1e-9)
    a_score = max(0.0, min(1.0, float(1 - ((anomaly_raw - bounds["anomaly_score_min"]) / div))))

    # 3. Règles métiers & Score de fraude
    f_score = 0
    if is_anomaly: f_score += 20
    if data.Debt_to_Revenue > 1.5: f_score += 15
    if data.Current_Ratio < 0.7: f_score += 15
    if data.Net_Debt > thresholds["net_debt_q90"]: f_score += 10
    if data.Revenue_per_Employee < thresholds["rev_per_emp_q10"]: f_score += 10
    if abs(data.Employees_Sector_Z) > 3: f_score += 5
    f_score = min(100, f_score)

    # Label précis pour Angular
    if f_score >= 85: label = "HIGH RISK"
    elif f_score >= 65: label = "SUSPICIOUS"
    elif f_score >= 40: label = "WATCH"
    else: label = "NORMAL"

    # 4. Health Score (Calculé pour ton interface HTML)
    h_score = float(
        0.30 * (1 - X_scaled["Debt_to_Revenue"].iloc[0]) +
        0.25 * X_scaled["Current Ratio"].iloc[0] +
        0.20 * (1 - X_scaled["Net_Debt"].iloc[0]) +
        0.25 * X_scaled["Revenue_per_Employee"].iloc[0]
    ) * 100

    return {
        "fraud_score": round(f_score, 2),
        "fraud_label": label,
        "is_anomaly": is_anomaly,
        "anomaly_score": round(a_score, 4),
        "health_score": round(max(0, min(100, h_score)), 2)
    }"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import pandas as pd
import joblib
from pathlib import Path

router = APIRouter()
MODEL_PATH = Path(__file__).resolve().parents[2] / "models" / "hybrid_score_model.joblib"

# Chargement sécurisé
try:
    artifact = joblib.load(MODEL_PATH)
    model, scaler, FEATURES = artifact["model"], artifact["scaler"], artifact["features"]
    thresholds, bounds = artifact["thresholds"], artifact["score_bounds"]
except Exception as e:
    raise RuntimeError(f"Erreur chargement modèle : {e}")

class CompanyData(BaseModel):
    Debt_to_Revenue: float
    Current_Ratio: float
    Revenue_per_Employee: float
    Net_Debt: float
    Employees_Sector_Z: float

@router.post("/analyze")
def predict(data: CompanyData):
    # 1. Préparation des données
    input_dict = data.model_dump()
    # Mismatch : Current_Ratio (API) -> Current Ratio (Modèle)
    input_dict["Current Ratio"] = input_dict.pop("Current_Ratio")
    
    df_input = pd.DataFrame([input_dict])
    X_scaled_raw = scaler.transform(df_input[FEATURES])
    X_scaled = pd.DataFrame(X_scaled_raw, columns=FEATURES)

    # 2. IA : Isolation Forest (Détection pure)
    is_anomaly = bool(model.predict(X_scaled)[0] == -1)
    anomaly_raw = float(model.decision_function(X_scaled)[0])
    
    # Normalisation du score d'anomalie (0 à 1)
    div = (bounds["anomaly_score_max"] - bounds["anomaly_score_min"] + 1e-9)
    a_score = max(0.0, min(1.0, float(1 - ((anomaly_raw - bounds["anomaly_score_min"]) / div))))

    # 3. Calcul de la Sévérité de l'anomalie (Règles métiers)
    severity = 0
    if is_anomaly: severity += 25
    if data.Debt_to_Revenue > 1.5: severity += 20
    if data.Current_Ratio < 0.7: severity += 15
    if data.Net_Debt > thresholds["net_debt_q90"]: severity += 15
    if data.Revenue_per_Employee < thresholds["rev_per_emp_q10"]: severity += 15
    if abs(data.Employees_Sector_Z) > 3: severity += 10
    severity = min(100, severity)

    # Labels d'anomalies pour l'interface
    if severity >= 80: label = "CRITICAL ANOMALY"
    elif severity >= 50: label = "SIGNIFICANT DEVIATION"
    elif severity >= 30: label = "MILD DEVIATION"
    else: label = "TYPICAL PROFILE"

    # 4. Health Score 
    h_score = float(
        0.30 * (1 - X_scaled["Debt_to_Revenue"].iloc[0]) +
        0.25 * X_scaled["Current Ratio"].iloc[0] +
        0.20 * (1 - X_scaled["Net_Debt"].iloc[0]) +
        0.25 * X_scaled["Revenue_per_Employee"].iloc[0]
    ) * 100

    return {
        "is_anomaly": is_anomaly,
        "anomaly_score": round(a_score, 4),
        "anomaly_severity": round(severity, 2),
        "anomaly_label": label,
        "health_score": round(max(0, min(100, h_score)), 2)
    }