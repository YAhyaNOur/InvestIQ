# smartstart_backend/app/services/crypto_service.py

from datetime import datetime
from pathlib import Path
import sys
import math
import traceback

BASE_DIR = Path(__file__).resolve().parents[4]
ML_PATH = BASE_DIR / "Service_ml" / "models3" / "code"

sys.path.insert(0, str(ML_PATH))

from models.crypto.data_loader import load_crypto_data
from models.crypto.analysis import analyze_crypto
from models.crypto.arima_model import run_arima
from models.crypto.prophet_model import run_prophet
from models.crypto.regression_model import run_regression
from models.crypto.vote import run_vote

from app.schemas.crypto import (
    CryptoRequest,
    CryptoResult,
    CryptoStats,
    ForecastResult,
    HistoriqueData,
    ModelResult,
    TableauRow,
    BudgetAnalysis 
)

CRYPTO_NAMES = {
    "BTC-USD": ("Bitcoin", "BTC"),
    "ETH-USD": ("Ethereum", "ETH"),
    "BNB-USD": ("Binance Coin", "BNB"),
    "SOL-USD": ("Solana", "SOL"),
    "ADA-USD": ("Cardano", "ADA"),
    "XRP-USD": ("XRP", "XRP"),
}


class CryptoService:

    def safe(self, value, default=0):
        if value is None:
            return default
        try:
            if math.isnan(value):
                return default
        except:
            pass
        return value

    async def analyze(self, req: CryptoRequest) -> CryptoResult:

        crypto_nom, crypto_symbol = CRYPTO_NAMES.get(
            req.ticker,
            (req.ticker.replace("-USD", ""), req.ticker.replace("-USD", ""))
        )

        # DATA
        df = load_crypto_data(ticker=req.ticker, jours=req.jours)

        if df is None or len(df) < 50:
            raise ValueError(f"Données insuffisantes pour {req.ticker}")

        # ANALYSE
        analysis = analyze_crypto(df)

        # ── ARIMA ──────────────────────────────────────────────
        print("START ARIMA")
        try:
            arima_res = run_arima(df, horizon=req.horizon)
            print("ARIMA OK:", arima_res)
        except Exception as e:
            print("ARIMA FAILED:")
            print(traceback.format_exc())
            raise

        # ── PROPHET ────────────────────────────────────────────
        print("START PROPHET")
        try:
            prophet_res = run_prophet(df, horizon=req.horizon)
            print("PROPHET OK:", prophet_res)
        except Exception as e:
            print("PROPHET FAILED:")
            print(traceback.format_exc())
            raise

        # ── REGRESSION ─────────────────────────────────────────
        print("START REGRESSION")
        try:
            reg_res = run_regression(analysis["df_enrichi"])
            print("REGRESSION OK:", reg_res)
        except Exception as e:
            print("REGRESSION FAILED:")
            print(traceback.format_exc())
            raise

        # SAFE VALUES
        arima_var   = self.safe(arima_res.get("variation"))
        prophet_var = self.safe(prophet_res.get("variation"))
        reg_prob    = self.safe(reg_res.get("prob_hausse"))
        arima_price = self.safe(arima_res.get("prix_predit"))

        print("ARIMA VAR:", arima_var)
        print("PROPHET VAR:", prophet_var)
        print("REG PROB:", reg_prob)

        # VOTE
        vote = run_vote(arima_res, prophet_res, reg_res)
        print("VOTE:", vote)
        # Après vote = run_vote(...)

        budget_analysis = None
        if req.budget and req.budget > 0:
            prix_actuel = analysis["stats"]["prix_actuel"]
            
            # Combien de crypto peut-il acheter avec tout son budget ?
            nb_crypto_achetable = req.budget / prix_actuel
            
            # Pourcentage à investir selon le signal et la confiance
            score = vote["score_confiance"]
            signal = vote["signal_final"]
            
            if signal == "BUY":
                pourcentage = min(80, score)
            elif signal == "SELL":
                pourcentage = 0  # on garde 0 mais on affiche quand même
            else:  # HOLD
                pourcentage = min(30, score * 0.4)

            investissement_recommande = req.budget * (pourcentage / 100)
            nb_crypto_recommande      = investissement_recommande / prix_actuel if prix_actuel > 0 else 0
            gain_potentiel            = investissement_recommande * (arima_var / 100)
            perte_max_estimee         = req.budget * (abs(prophet_var) / 100)  # ← sur tout le budget

            if signal == "BUY":
                conseil = (
                    f" Recommandation : investir {pourcentage:.0f}% de votre budget "
                    f"(${investissement_recommande:,.0f}) pour acheter "
                    f"{nb_crypto_recommande:.4f} {crypto_symbol}. "
                    f"Gain potentiel estimé : +${gain_potentiel:,.0f}."
                )
            elif signal == "SELL":
                conseil = (
                    f" Le marché est baissier. Ne pas investir vos ${req.budget:,.0f} maintenant. "
                    f"Si vous détenez déjà du {crypto_symbol}, envisagez de vendre. "
                    f"Risque de perte estimé si vous investissez quand même : -${perte_max_estimee:,.0f}."
                )
            else:
                conseil = (
                    f" Marché incertain. Investir prudemment maximum {pourcentage:.0f}% "
                    f"(${investissement_recommande:,.0f}) en attendant une tendance claire. "
                    f"Risque estimé : -${perte_max_estimee:,.0f}."
                )

            budget_analysis = {
                "budget":                    req.budget,
                "nb_crypto_achetable":       round(req.budget / prix_actuel, 6),
                "investissement_recommande": round(investissement_recommande, 2),
                "nb_crypto_recommande":      round(nb_crypto_recommande, 6),
                "gain_potentiel":            round(gain_potentiel, 2),
                "perte_max_estimee":         round(perte_max_estimee, 2),
                "pourcentage_investir":      round(pourcentage, 1),
                "conseil":                   conseil
            }
            print("BUDGET ANALYSIS:", budget_analysis)  # debug

        hist = analysis["df_enrichi"]
        fc   = arima_res["df_forecast"]

        lo_80 = self.safe(fc["lo_80"].iloc[-1])
        hi_80 = self.safe(fc["hi_80"].iloc[-1])
        lo_95 = self.safe(fc["lo_95"].iloc[-1])
        hi_95 = self.safe(fc["hi_95"].iloc[-1])

        return CryptoResult(

            societe=req.societe,
            crypto_nom=crypto_nom,
            crypto_symbol=crypto_symbol,

            date_analyse=datetime.now().strftime("%Y-%m-%d"),

            jours_analyses=len(df),
            horizon=req.horizon,

            signal_final=vote["signal_final"],
            score_confiance=vote["score_confiance"],
            niveau_confiance=vote["niveau_confiance"],
            interpretation=vote["interpretation"],

            modeles=[
                ModelResult(
                    nom=arima_res.get("model_name", "ARIMA"),
                    cours="Séries temporelles — ARIMA/ETS",
                    signal=arima_res.get("signal", "NEUTRAL"),
                    detail=f"Prévision J+{req.horizon} : {arima_var:+.2f}%",
                    confiance=abs(arima_var) * 10
                ),
                ModelResult(
                    nom="Prophet",
                    cours="Séries temporelles — Tendance + Saisonnalité",
                    signal=prophet_res.get("signal", "NEUTRAL"),
                    detail=f"Tendance : {prophet_res.get('tendance', 'N/A')} | {prophet_var:+.2f}%",
                    confiance=self.safe(prophet_res.get("confiance"))
                ),
                ModelResult(
                    nom="Régression logistique",
                    cours="Régression — Chap 3",
                    signal=reg_res.get("signal_logit", "NEUTRAL"),
                    detail=f"P(hausse) = {reg_prob:.1f}%",
                    confiance=reg_prob
                )
            ],

            stats=CryptoStats(
                prix_actuel=analysis["stats"]["prix_actuel"],
                prix_min=analysis["stats"]["prix_min"],
                prix_max=analysis["stats"]["prix_max"],
                rendement_total=analysis["stats"]["rendement_total"],
                vol_moy_7j=analysis["stats"]["vol_moy_7j"],
                vol_moy_30j=analysis["stats"]["vol_moy_30j"],
                vol_niveau=analysis["stats"]["vol_niveau"],
                return_moyen=analysis["stats"]["return_moyen"],
                return_sd=analysis["stats"]["return_sd"],
                adf_pvalue=analysis["stats"]["adf_pvalue"],
                adf_stationary=analysis["stats"]["adf_stationary"]
            ),

            forecast=ForecastResult(
                prix_predit=arima_price,
                variation=arima_var,
                dates=fc["date"].dt.strftime("%Y-%m-%d").tolist(),
                mean=fc["mean"].fillna(0).tolist(),
                lo_80=lo_80,
                hi_80=hi_80,
                lo_95=lo_95,
                hi_95=hi_95
            ),

            prob_hausse=reg_prob,

            historique=HistoriqueData(
                dates=hist["date"].dt.strftime("%Y-%m-%d").tolist(),
                prix=hist["prix"].fillna(0).tolist(),
                vol_7j=hist["vol_7j"].fillna(0).tolist(),
                vol_30j=hist["vol_30j"].fillna(0).tolist(),
                prob_hausse=hist["prob_hausse"].fillna(0).tolist()
                if "prob_hausse" in hist.columns else []
            ),
            budget_analysis=BudgetAnalysis(**budget_analysis) if budget_analysis else None,

            synthese="Analyse crypto générée avec succès.",
            tableau_stats=[]
        )