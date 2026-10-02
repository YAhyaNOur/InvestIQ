def run_vote(arima_res, prophet_res, reg_res):

    arima_var   = arima_res.get("variation")   or 0
    prophet_var = prophet_res.get("variation") or 0
    reg_prob    = reg_res.get("prob_hausse")   or 50

    score = 0

    # ARIMA (poids 1) — seuil proportionnel à la variation
    if arima_var > 0.5:
        score += 1
    elif arima_var < -0.5:
        score -= 1

    # PROPHET (poids 1) — seuil élargi pour longues séries
    if prophet_var > 2.0:     
        score += 1
    elif prophet_var < -2.0:   
        score -= 1

    # REGRESSION (poids 1.5)
    if reg_prob >= 55:
        score += 1.5
    elif reg_prob <= 45:
        score -= 1.5

    # Décision finale
    if score >= 1.5:
        signal = "BUY"
    elif score <= -1.5:
        signal = "SELL"
    else:
        signal = "HOLD"

    # ── Confiance corrigée ─────────────────────────────────────────
    # Score max possible = 3.5 (1 + 1 + 1.5)
    # Score min pour signal = ±1.5
    # On normalise sur 3.5 et on garantit un minimum si signal non-HOLD
    raw_confidence = min(100, int(abs(score) / 3.5 * 100))

    if signal != "HOLD" and raw_confidence == 0:
        raw_confidence = 33

    # ← ajouter ces lignes
    if signal == "HOLD":
        raw_confidence = max(20, raw_confidence)  # minimum 20% pour HOLD

    reg_conviction = abs(reg_prob - 50)
    bonus = int(reg_conviction / 50 * 20)
    confidence = min(100, raw_confidence + bonus)
    return {
        "signal_final"    : signal,
        "score_confiance" : confidence,
        "niveau_confiance": "HIGH" if confidence > 70 else "MEDIUM" if confidence > 40 else "LOW",
        "interpretation"  : (
            "Consensus haussier"  if signal == "BUY"
            else "Consensus baissier" if signal == "SELL"
            else "Marché indécis"
        )
    }