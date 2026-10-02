from fastapi import APIRouter
from pydantic import BaseModel, Field
import pandas as pd
import joblib
from pathlib import Path

router = APIRouter()

# =========================
# LOAD MODEL
# =========================
current_dir = Path(__file__).resolve().parent
MODEL_PATH = current_dir.parent.parent / "models" / "growth_score_model.joblib"

if not MODEL_PATH.exists():
    raise FileNotFoundError(f"Model not found: {MODEL_PATH}")

try:
    package = joblib.load(MODEL_PATH)

    model = package.get("model")
    FEATURES = package.get("features")
    CAT_FEATURES = package.get("cat_features")
    THRESHOLD = package.get("threshold", 0.5)

    if FEATURES is None:
        raise ValueError("FEATURES missing in growth model file")

    print(" Growth model loaded successfully")

except Exception as e:
    raise RuntimeError(f" Growth model loading failed: {e}")


# =========================
# INPUT SCHEMA
# =========================
class GrowthInput(BaseModel):
    Sector: str
    Beta: float = Field(..., ge=-10, le=10)
    Region_std: str
    Net_Debt: float = Field(..., ge=-1_000_000, le=1_000_000)
    Revenue_Growth: float = Field(..., ge=-1, le=10)


# =========================
# SCORE LOGIC
# =========================
def interpret_growth(p: float):
    if p >= 0.70:
        return "HIGH GROWTH POTENTIAL"
    elif p >= 0.50:
        return "MEDIUM GROWTH POTENTIAL"
    elif p >= 0.30:
        return "LOW-MEDIUM GROWTH POTENTIAL"
    else:
        return "LOW GROWTH POTENTIAL"


# =========================
# PREDICT ENDPOINT
# =========================
@router.post("/predict")
def predict(data: GrowthInput):

    
    raw = {
        "Sector": data.Sector,
        "Beta": data.Beta,
        "Region_std": data.Region_std,
        "Net_Debt": data.Net_Debt,
        "Revenue Growth": data.Revenue_Growth
    }

    df = pd.DataFrame([raw])

    # ensure feature alignment
    for col in FEATURES:
        if col not in df.columns:
            df[col] = 0

    df = df[FEATURES]

    # categorical handling
    for c in CAT_FEATURES:
        if c in df.columns:
            df[c] = df[c].astype(str)

    # prediction
    proba = float(model.predict_proba(df)[0][1])
    label = interpret_growth(proba)

    return {
        "score": round(proba, 4),
        "label": label
    }