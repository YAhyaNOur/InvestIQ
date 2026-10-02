

import numpy as np
import pandas as pd
from datetime import timedelta
from statsmodels.tsa.arima.model   import ARIMA
from statsmodels.tsa.holtwinters   import ExponentialSmoothing
from statsmodels.tsa.stattools     import adfuller
import warnings
warnings.filterwarnings("ignore")


def run_arima(df: pd.DataFrame, horizon: int = 7, seuil: float = 0.01) -> dict:
   
    print(" Ajustement ARIMA + ETS...")

    prix        = df["prix"].values
    prix_actuel = float(prix[-1])

    # ── ARIMA — sélection automatique des ordres ──
    best_arima, best_aic_arima, best_order = _fit_best_arima(prix)

    # ── ETS (Holt-Winters) ────────────────────────
    best_ets, best_aic_ets = _fit_ets(prix)

    # ── SÉLECTION DU MEILLEUR MODÈLE ─────────────
    if best_aic_arima <= best_aic_ets:
        model_name  = f"ARIMA({best_order[0]},{best_order[1]},{best_order[2]})"
        best_model  = best_arima
        is_arima    = True
        print(f"    Meilleur modèle : {model_name} (AIC = {best_aic_arima:.1f})")
    else:
        model_name  = "ETS (Holt-Winters)"
        best_model  = best_ets
        is_arima    = False
        print(f"    Meilleur modèle : {model_name} (AIC = {best_aic_ets:.1f})")

    # ── PRÉVISION ────────────────────────────────
    if is_arima:
        forecast_result = best_model.get_forecast(steps=horizon)
        mean_fc = forecast_result.predicted_mean
        ci_80   = forecast_result.conf_int(alpha=0.20)
        ci_95   = forecast_result.conf_int(alpha=0.05)
    else:
        fc_ets  = best_model.forecast(horizon)
        mean_fc = fc_ets
        # ETS n'a pas d'IC natif — on estime avec l'écart-type résiduel
        resid_std = float(np.std(best_model.resid))
        ci_80 = pd.DataFrame({
            "lower prix": mean_fc - 1.28 * resid_std,
            "upper prix": mean_fc + 1.28 * resid_std
        })
        ci_95 = pd.DataFrame({
            "lower prix": mean_fc - 1.96 * resid_std,
            "upper prix": mean_fc + 1.96 * resid_std
        })

    prix_predit = float(np.array(mean_fc).flatten()[-1])
    variation   = round((prix_predit / prix_actuel - 1) * 100, 2)
    signal      = "BUY" if prix_predit > prix_actuel * (1 + seuil) else "SELL"

    print(f" Prévision J+{horizon} : ${prix_predit:,.2f} ({variation:+.2f}%)")
    print(f" Signal ARIMA : {signal}")

    # ── DATES DU FORECAST ─────────────────────────
    derniere_date  = df["date"].max()
    dates_forecast = [
        (derniere_date + timedelta(days=i)).strftime("%Y-%m-%d")
        for i in range(1, horizon + 1)
    ]

    mean_arr  = np.array(mean_fc).flatten()
    lo_80_arr = np.array(ci_80.iloc[:, 0]).flatten()
    hi_80_arr = np.array(ci_80.iloc[:, 1]).flatten()
    lo_95_arr = np.array(ci_95.iloc[:, 0]).flatten()
    hi_95_arr = np.array(ci_95.iloc[:, 1]).flatten()

    df_forecast = pd.DataFrame({
        "date" : dates_forecast,
        "mean" : mean_arr,
        "lo_80": lo_80_arr,
        "hi_80": hi_80_arr,
        "lo_95": lo_95_arr,
        "hi_95": hi_95_arr,
    })
    df_forecast["date"] = pd.to_datetime(df_forecast["date"])

    return {
        "model_name" : model_name,
        "signal"     : signal,
        "prix_actuel": prix_actuel,
        "prix_predit": round(prix_predit, 2),
        "variation"  : variation,
        "aic"        : min(best_aic_arima, best_aic_ets),
        "df_forecast": df_forecast,
    }


def _fit_best_arima(prix: np.ndarray):
    """Teste plusieurs ordres ARIMA et retourne le meilleur AIC."""
    best_aic   = np.inf
    best_model = None
    best_order = (1, 1, 1)

    # Grille de recherche des ordres
    candidates = [
        (0,1,0),(1,1,0),(0,1,1),(1,1,1),
        (2,1,0),(0,1,2),(2,1,1),(1,1,2),
        (2,1,2),(3,1,0),(0,1,3),
    ]

    for order in candidates:
        try:
            m   = ARIMA(prix, order=order).fit()
            aic = m.aic
            if aic < best_aic:
                best_aic   = aic
                best_model = m
                best_order = order
        except Exception:
            continue

    return best_model, best_aic, best_order


def _fit_ets(prix: np.ndarray):
    """Ajuste un modèle ETS (Holt-Winters)."""
    try:
        m   = ExponentialSmoothing(prix, trend="add", seasonal=None).fit()
        aic = m.aic
        return m, aic
    except Exception:
        return None, np.inf