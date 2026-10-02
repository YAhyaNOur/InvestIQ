import yfinance as yf
import joblib
import os
import pandas as pd
import numpy as np
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.core.deps import get_current_user

router = APIRouter(prefix="/analyze", tags=["YFinance Analysis"])

from pathlib import Path
MODELS_DIR = Path(r"C:\Users\user\Desktop\BIIA\BiAi\Service_ml\models3\models")
growth_package = joblib.load(os.path.join(MODELS_DIR, "growth_score_model.joblib"))
growth_model = growth_package["model"]
FEATURES_GROWTH = growth_package["features"]

risk_package = joblib.load(os.path.join(MODELS_DIR, "risk_model.joblib"))
risk_model = risk_package["model"]
FEATURES_RISK = risk_package["features"]

COUNTRY_TO_REGION = {
    "United States": "North_America",
    "Canada": "North_America",
    "France": "Europe",
    "Germany": "Europe",
    "United Kingdom": "Europe",
    "Japan": "Asia",
    "China": "Asia",
    "India": "Asia",
}

SECTOR_MAP = {
    "Technology": "Technology",
    "Financial Services": "Finance",
    "Healthcare": "Healthcare",
    "Industrials": "Industrials",
    "Consumer Cyclical": "Consumer",
    "Consumer Defensive": "Consumer",
    "Real Estate": "Real_Estate",
    "Energy": "Energy",
    "Communication Services": "Communication",
    "Basic Materials": "Industrials",
    "Utilities": "Energy",
}


class CompanyRequest(BaseModel):
    symbol: str


@router.post("/company")
async def analyze_company(
    request: CompanyRequest,
    current_user=Depends(get_current_user)
):
    symbol = request.symbol.upper().strip()

    # ── 1. Fetch yfinance ──────────────────────────────────────────────────
    ticker = yf.Ticker(symbol)
    info = ticker.info

    print("DEBUG quoteType:", info.get("quoteType"))
    print("DEBUG currentPrice:", info.get("currentPrice"))
    print("DEBUG regularMarketPrice:", info.get("regularMarketPrice"))
    print("DEBUG bid:", info.get("bid"))

    price = (
        info.get("currentPrice")
        or info.get("regularMarketPrice")
        or info.get("navPrice")
        or info.get("bid")
    )

    print("DEBUG price final:", price)

    if not info or not info.get("quoteType") or price is None:
        raise HTTPException(status_code=404, detail=f"Symbol '{symbol}' not found")

    # ── 2. Extraire les données ────────────────────────────────────────────
    sector_raw = info.get("sector", "Other")
    sector = SECTOR_MAP.get(sector_raw, "Other")
    country = info.get("country", "United States")
    region = COUNTRY_TO_REGION.get(country, "Other")
    industry = info.get("industry", "Other")

    beta = float(info.get("beta") or 1.0)
    revenue_growth = float(info.get("revenueGrowth") or 0) * 100
    debt_to_equity = float(info.get("debtToEquity") or 0)
    current_ratio = float(info.get("currentRatio") or 1)
    quick_ratio = float(info.get("quickRatio") or 1)
    ebitda_margins = float(info.get("ebitdaMargins") or 0) * 100
    net_debt = float(info.get("totalDebt") or 0) - float(info.get("totalCash") or 0)
    revenue = float(info.get("totalRevenue") or 0)
    employees = int(info.get("fullTimeEmployees") or 1)
    revenue_per_employee = revenue / max(employees, 1)

    # ── 3. Préparer features Growth ────────────────────────────────────────
    df_growth = pd.DataFrame([{
        "Sector": sector,
        "Region_std": region,
        "Beta": beta,
        "Net_Debt": net_debt / 1e6,
        "Revenue Growth": revenue_growth,
    }])
    for col in ["Sector", "Region_std"]:
        df_growth[col] = df_growth[col].astype(str)

    # ── 4. Préparer features Risk ──────────────────────────────────────────
    df_risk = pd.DataFrame([{
        "Sector": sector,
        "Region_std": region,
        "Debt To Equity": debt_to_equity,
        "Total Debt (M)": float(info.get("totalDebt") or 0) / 1e6,
        "Current Ratio": current_ratio,
        "Employees_Sector_Z": 0,
    }])
    for col in ["Sector", "Region_std"]:
        df_risk[col] = df_risk[col].astype(str)

    # ── 5. Prédictions ─────────────────────────────────────────────────────
    try:
        growth_score = float(growth_model.predict_proba(df_growth[FEATURES_GROWTH])[0][1]) * 100
    except Exception as e:
        print(f"Growth model error: {e}")
        growth_score = 50.0

    try:
        risk_score = float(risk_model.predict_proba(df_risk[FEATURES_RISK])[0][1]) * 100
    except Exception as e:
        print(f"Risk model error: {e}")
        risk_score = 50.0

    # ── 6. Investment Score ────────────────────────────────────────────────
    investment_score = round(min(100, max(0, 100 - risk_score + growth_score * 0.5)), 1)

    # ── 7. Decision ────────────────────────────────────────────────────────
    if investment_score > 75:
        decision = "STRONG BUY"
        decision_color = "#10b981"
    elif investment_score > 55:
        decision = "BUY"
        decision_color = "#3b82f6"
    elif investment_score > 35:
        decision = "HOLD"
        decision_color = "#f59e0b"
    else:
        decision = "AVOID"
        decision_color = "#ef4444"

    # ── 8. Response ────────────────────────────────────────────────────────
    return {
        "symbol": symbol,
        "name": info.get("longName", symbol),
        "sector": sector,
        "sector_raw": sector_raw,
        "region": region,
        "country": country,
        "industry": industry,
        "growth_score": round(growth_score, 1),
        "risk_score": round(risk_score, 1),
        "investment_score": investment_score,
        "decision": decision,
        "decision_color": decision_color,
        "beta": round(beta, 2),
        "revenue_growth": round(revenue_growth, 1),
        "debt_to_equity": round(debt_to_equity, 2),
        "current_ratio": round(current_ratio, 2),
        "ebitda_margins": round(ebitda_margins, 1),
        "net_debt_m": round(net_debt / 1e6, 1),
        "revenue_per_employee": round(revenue_per_employee, 0),
        "market_cap": info.get("marketCap"),
        "price": price,
        "pe_ratio": info.get("trailingPE"),
        "52w_high": info.get("fiftyTwoWeekHigh"),
        "52w_low": info.get("fiftyTwoWeekLow"),
        "description": (info.get("longBusinessSummary") or "")[:300],
    }