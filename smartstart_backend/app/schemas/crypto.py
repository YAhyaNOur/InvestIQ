# smartstart_backend/app/schemas/crypto.py
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import date

class BudgetAnalysis(BaseModel):
    budget:                    float
    nb_crypto_achetable:       float
    investissement_recommande: float
    nb_crypto_recommande:      float
    gain_potentiel:            float
    perte_max_estimee:         float
    pourcentage_investir:      float
    conseil:                   str

# ── INPUT ──────────────────────────────────────
class CryptoRequest(BaseModel):
    societe:  str   = Field(..., example="Alpha Capital")
    ticker:   str   = Field(..., example="BTC-USD")
    jours:    int   = Field(1095, example=1095)   # 365 | 730 | 1095
    horizon:  int   = Field(7,    example=7)       # 7 | 14 | 30
    budget:   float = Field(0.0, example=10000.0) 
    

# ── OUTPUT ─────────────────────────────────────
class ModelResult(BaseModel):
    nom:       str
    cours:     str
    signal:    Literal["BUY", "SELL", "NEUTRAL", "HOLD"]
    detail:    str
    confiance: float
    

class CryptoStats(BaseModel):
    prix_actuel:      float
    prix_min:         float
    prix_max:         float
    rendement_total:  float
    vol_moy_7j:       float
    vol_moy_30j:      float
    vol_niveau:       str
    return_moyen:     float
    return_sd:        float
    adf_pvalue:       float
    adf_stationary:   bool

class ForecastResult(BaseModel):
    prix_predit: float
    variation:   float
    dates:       List[str]
    mean:        List[float]
    lo_80:       float
    hi_80:       float
    lo_95:       float
    hi_95:       float

class HistoriqueData(BaseModel):
    dates:       List[str]
    prix:        List[float]
    vol_7j:      List[Optional[float]]
    vol_30j:     List[Optional[float]]
    prob_hausse: List[Optional[float]]

class TableauRow(BaseModel):
    indicateur: str
    valeur:     str
    positive:   Optional[bool] = None

class CryptoResult(BaseModel):
    # Identité
    societe:          str
    crypto_nom:       str
    crypto_symbol:    str
    date_analyse:     str
    jours_analyses:   int
    horizon:          int

    # Signal final
    signal_final: Literal["BUY", "SELL", "HOLD"]
    score_confiance:  float
    niveau_confiance: str
    interpretation:   str

    # Vote modèles
    modeles: List[ModelResult]

    # Stats
    stats:   CryptoStats

    # Forecast
    forecast: ForecastResult

    # Probabilité hausse
    prob_hausse: float

    # Historique pour graphiques
    historique: HistoriqueData

    # Texte synthèse
    synthese: str

    # Tableau complet
    tableau_stats: List[TableauRow]
    budget_analysis: Optional[BudgetAnalysis] = None