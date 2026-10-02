

import numpy as np
import pandas as pd
from sklearn.linear_model    import LinearRegression, LogisticRegression
from sklearn.preprocessing   import StandardScaler
from sklearn.metrics         import r2_score
import warnings
warnings.filterwarnings("ignore")


def run_regression(df: pd.DataFrame, seuil: float = 0.01) -> dict:
    """
    Régression multiple  → prédit le prix de demain
    Régression logistique → prédit P(hausse) directement

    Args:
        df    : DataFrame enrichi (date, prix, log_return, vol_7j, vol_30j)
        seuil : seuil minimum de hausse pour signal BUY

    Returns:
        dict avec signaux, coefficients, probabilité, métriques
    """
    print(" Régression multiple + logistique...")

    prix = df["prix"].values
    n    = len(prix)

    # ── CONSTRUCTION DES VARIABLES ───────────────
    reg_df = pd.DataFrame({
        # Y : prix de demain
        "prix_demain"  : np.append(prix[1:], np.nan),

        # X : variables explicatives
        "prix_hier"    : prix,
        "prix_7j"      : np.append([np.nan]*7,  prix[:-7]),
        "prix_30j"     : np.append([np.nan]*30, prix[:-30]),
        "return_1j"    : np.append([np.nan], np.diff(np.log(prix))),
        "return_7j"    : _lag_diff(prix, lag=7),
        "vol_7j"       : df["vol_7j"].values,
        "tendance"     : np.arange(n),
        "jour_semaine" : pd.to_datetime(df["date"]).dt.dayofweek.values,
    })

    reg_df = reg_df.dropna()
    print(f"   Observations utilisées : {len(reg_df)} / {n}")

    # ══════════════════════════════════════════════
    # MODÈLE 1 : RÉGRESSION MULTIPLE
    # Y = prix_demain
    # X = prix_hier + return_7j + vol_7j + tendance
    
    # ══════════════════════════════════════════════
    print("\n   [1/2] Régression multiple...")

    X_lm = reg_df[["prix_hier", "return_7j", "vol_7j", "tendance"]].values
    y_lm = reg_df["prix_demain"].values

    # Normalisation
    scaler_lm = StandardScaler()
    X_lm_sc   = scaler_lm.fit_transform(X_lm)

    lm_model  = LinearRegression()
    lm_model.fit(X_lm_sc, y_lm)

    # R²
    y_pred_lm = lm_model.predict(X_lm_sc)
    r2        = round(r2_score(y_lm, y_pred_lm), 4)
    r2_adj    = round(1 - (1 - r2) * (len(y_lm) - 1) / (len(y_lm) - X_lm.shape[1] - 1), 4)

    # Prédiction de demain
    last_X     = reg_df[["prix_hier", "return_7j", "vol_7j", "tendance"]].iloc[[-1]].values
    last_X_sc  = scaler_lm.transform(last_X)
    prix_predit_lm = float(lm_model.predict(last_X_sc)[0])
    prix_actuel    = float(prix[-1])
    variation_lm   = round((prix_predit_lm / prix_actuel - 1) * 100, 2)
    signal_lm      = "BUY" if variation_lm > seuil * 100 else "SELL"

    # Coefficients
    feature_names = ["prix_hier", "return_7j", "vol_7j", "tendance"]
    coefs_lm = pd.DataFrame({
        "Variable"   : ["Constante"] + feature_names,
        "Coefficient": [round(lm_model.intercept_, 4)] + [round(c, 4) for c in lm_model.coef_],
    })

    print(f"   R²             : {r2:.4f} ({r2*100:.1f}% variance expliquée)")
    print(f"   Prix prédit J+1: ${prix_predit_lm:,.2f} ({variation_lm:+.2f}%)")
    print(f"   Signal LM      : {signal_lm}")

    # ══════════════════════════════════════════════
    # MODÈLE 2 : RÉGRESSION LOGISTIQUE
    # Y = 1 si hausse demain, 0 sinon
    # X = return_1j + return_7j + vol_7j + jour_semaine

    # ══════════════════════════════════════════════
    print("\n   [2/2] Régression logistique...")

    reg_df["hausse"] = (reg_df["prix_demain"] > reg_df["prix_hier"]).astype(int)

    X_logit = reg_df[["return_1j", "return_7j", "vol_7j", "jour_semaine"]].values
    y_logit = reg_df["hausse"].values

    scaler_logit = StandardScaler()
    X_logit_sc   = scaler_logit.fit_transform(X_logit)

    logit_model  = LogisticRegression(max_iter=1000, random_state=42)
    logit_model.fit(X_logit_sc, y_logit)

    # Probabilité de hausse pour demain
    last_X_logit    = reg_df[["return_1j", "return_7j", "vol_7j", "jour_semaine"]].iloc[[-1]].values
    last_X_logit_sc = scaler_logit.transform(last_X_logit)
    prob_hausse     = round(float(logit_model.predict_proba(last_X_logit_sc)[0][1]) * 100, 1)
    signal_logit    = "BUY" if prob_hausse > 50 else "SELL"

    # Pseudo R² 
    from sklearn.metrics import log_loss
    ll_model = -log_loss(y_logit, logit_model.predict_proba(X_logit_sc), normalize=False)
    ll_null  = -log_loss(y_logit, np.full_like(y_logit, y_logit.mean(), dtype=float), normalize=False)
    pseudo_r2 = round(1 - ll_model / ll_null, 4) if ll_null != 0 else 0

    # Précision du classifieur
    accuracy = round(float((logit_model.predict(X_logit_sc) == y_logit).mean()) * 100, 1)

    # Coefficients
    logit_features = ["return_1j", "return_7j", "vol_7j", "jour_semaine"]
    coefs_logit = pd.DataFrame({
        "Variable"   : logit_features,
        "Coefficient": [round(c, 4) for c in logit_model.coef_[0]],
    })

    # Rolling prob pour graphique
    prob_rolling = _rolling_prob(logit_model, scaler_logit,
                                 reg_df[["return_1j", "return_7j", "vol_7j", "jour_semaine"]])

    print(f"   P(hausse) demain  : {prob_hausse:.1f}%")
    print(f"   Signal logistique : {signal_logit}")
    print(f"   Précision modèle  : {accuracy}%")
    print(f"   Pseudo R²         : {pseudo_r2:.4f}")

    print("\n Régressions terminées.")

    return {
        # Régression multiple
        "model_lm"       : lm_model,
        "r2"             : r2,
        "r2_adj"         : r2_adj,
        "prix_predit_lm" : round(prix_predit_lm, 2),
        "variation_lm"   : variation_lm,
        "signal_lm"      : signal_lm,
        "coefs_lm"       : coefs_lm,

        # Régression logistique
        "model_logit"    : logit_model,
        "pseudo_r2"      : pseudo_r2,
        "accuracy"       : accuracy,
        "prob_hausse"    : prob_hausse,
        "signal_logit"   : signal_logit,
        "coefs_logit"    : coefs_logit,
        "prob_rolling"   : prob_rolling,

        "prix_actuel"    : prix_actuel,
        "reg_df"         : reg_df,
    }


def _lag_diff(prix: np.ndarray, lag: int) -> np.ndarray:
    """Log-return sur une fenêtre de `lag` jours."""
    result = np.full(len(prix), np.nan)
    for i in range(lag, len(prix)):
        result[i] = np.log(prix[i]) - np.log(prix[i - lag])
    return result


def _rolling_prob(model, scaler, X_df: pd.DataFrame) -> list:
    """Calcule la probabilité de hausse glissante pour le graphique."""
    try:
        X_sc = scaler.transform(X_df.values)
        probs = model.predict_proba(X_sc)[:, 1] * 100
        
        return [None] * (len(X_df) - len(probs)) + [round(float(p), 1) for p in probs]
    except Exception:
        return [None] * len(X_df)