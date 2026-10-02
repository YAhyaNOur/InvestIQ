import os
import joblib
import pandas as pd
import numpy as np
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from pathlib import Path

router = APIRouter()

# =========================
# LOAD MODEL
# =========================
current_dir = Path(__file__).resolve().parent
MODEL_PATH = current_dir.parent.parent / "models" / "risk_model.joblib"

try:
    artifact = joblib.load(MODEL_PATH)
    model = artifact["model"]
    model_features = artifact["features"]
    model_threshold = artifact.get("threshold", 0.55)

    print(f"Model loaded ✔ Features: {len(model_features)}")
    print(f"Threshold: {model_threshold:.3f}")

except Exception as e:
    print(f"MODEL LOAD ERROR: {e}")
    model = None
    model_features = []


# =========================
# INPUT SCHEMA
# =========================
class CompanyData(BaseModel):
    Sector: str
    Region_std: str = "Unknown"

    Debt_To_Equity: float = Field(..., ge=-1000, le=1000)
    Total_Debt_M: float = Field(..., ge=0, le=1000000)
    Current_Ratio: float = Field(..., ge=-1000, le=1000)
    Employees_Sector_Z: float = Field(..., ge=-1000, le=1000)


# =========================
# ENDPOINT
# =========================
@router.post("/predict_risk")
async def predict_risk(data: CompanyData):

    if model is None:
        raise HTTPException(status_code=500, detail="Model not loaded")

    print(f"INPUT: {data}")

    # DATAFRAME CLEAN (NO OVERWRITING FEATURES)
    df = pd.DataFrame([{
        "Sector": data.Sector,
        "Region_std": data.Region_std,
        "Debt To Equity": data.Debt_To_Equity,
        "Total Debt (M)": data.Total_Debt_M,
        "Current Ratio": data.Current_Ratio,
        "Employees_Sector_Z": data.Employees_Sector_Z
    }])

    # =========================
    # OPTIONAL: SAFE CLAMPING (ONLY IF NECESSARY)
    # =========================
    # on NE détruit pas le signal, on le stabilise légèrement

    df["Debt To Equity"] = df["Debt To Equity"].clip(-200, 200)
    df["Current Ratio"] = df["Current Ratio"].clip(0.01, 50)

    # =========================
    # ALIGN FEATURES
    # =========================
    final_df = df[model_features]

    # =========================
    # PREDICTION
    # =========================
    prob = float(model.predict_proba(final_df)[0, 1])

    zone = "CRITICAL" if prob > model_threshold else "SAFE"

    return {
        "status": "success",
        "analysis": {
            "risk_score": round(prob * 100, 1),
            "zone": zone,
            "confidence": "High"
        },
        "ui_display": {
            "color": "#ef4444" if zone == "CRITICAL" else "#10b981",
            "label": zone
        },
        "recommendation": {
            "action": "VÉRIFICATION",
            "summary": "Analyse effectuée avec succès."
        }
    }