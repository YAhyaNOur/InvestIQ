

import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import adfuller


def analyze_crypto(df: pd.DataFrame) -> dict:
    print("Analyse des séries temporelles...")

    prix = df["prix"].values
    n    = len(prix)

    # ── LOG-RETURNS ──────────────────────────────
    log_returns = np.diff(np.log(prix))

    # ── VOLATILITÉ GLISSANTE ─────────────────────
    vol_7j  = _rolling_std(log_returns, window=7)
    vol_30j = _rolling_std(log_returns, window=30)

    # ── TEST ADF ─────────────────────────────────
    adf_result = adfuller(log_returns, autolag="AIC")
    adf_pvalue = round(float(adf_result[1]), 4)
    stationary = adf_pvalue < 0.05

    print(f"   ADF p-value : {adf_pvalue:.4f} → "
          f"{'STATIONNAIRE ' if stationary else 'NON stationnaire ⚠️'}")

    # ── STATISTIQUES DESCRIPTIVES ────────────────
    rendement_total = round((prix[-1] / prix[0] - 1) * 100, 2)
    vol_moy_7j      = round(float(np.nanmean(vol_7j))  * 100, 4)
    vol_moy_30j     = round(float(np.nanmean(vol_30j)) * 100, 4)

    vol_niveau = (
        "élevée"  if vol_moy_7j > 3   else
        "modérée" if vol_moy_7j > 1.5 else
        "faible"
    )

    prix_30j_avant = prix[max(0, n - 31)]
    variation_30j  = round((prix[-1] / prix_30j_avant - 1) * 100, 2)

    stats = {
        "n_obs"          : n,
        "prix_actuel"    : round(float(prix[-1]),   2),
        "prix_min"       : round(float(prix.min()), 2),
        "prix_max"       : round(float(prix.max()), 2),
        "rendement_total": rendement_total,
        "variation_30j"  : variation_30j,
        "vol_moy_7j"     : vol_moy_7j,
        "vol_moy_30j"    : vol_moy_30j,
        "vol_niveau"     : vol_niveau,
        "return_moyen"   : round(float(np.mean(log_returns))  * 100, 4),
        "return_sd"      : round(float(np.std(log_returns))   * 100, 4),
        "return_max"     : round(float(log_returns.max())     * 100, 2),
        "return_min"     : round(float(log_returns.min())     * 100, 2),
        "adf_pvalue"     : adf_pvalue,
        "adf_stationary" : stationary,
    }

    print(f"   Rendement total  : {rendement_total:+.2f}%")
    print(f"   Volatilité 7j    : {vol_moy_7j:.4f}%/jour ({vol_niveau})")
    print(f"   Volatilité 30j   : {vol_moy_30j:.4f}%/jour")

    # ── DATA FRAME ENRICHI ───────────────────────
    df_enrichi = df.copy()                                      # ← ligne manquante !
    df_enrichi["log_return"] = [np.nan] + list(log_returns)
    df_enrichi["vol_7j"]     = [np.nan] + list(vol_7j)
    df_enrichi["vol_30j"]    = [np.nan] + list(vol_30j)

    return {
        "df_enrichi" : df_enrichi,
        "stats"      : stats,
        "log_returns": log_returns,
        "vol_7j"     : vol_7j,
        "vol_30j"    : vol_30j,
    }


def _rolling_std(x: np.ndarray, window: int) -> list:
    """Écart-type glissant sur une fenêtre."""
    n      = len(x)
    result = [np.nan] * n
    for i in range(window - 1, n):
        result[i] = float(np.std(x[i - window + 1 : i + 1]))
    return result