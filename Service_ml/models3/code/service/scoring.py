"""import numpy as np
import pandas as pd"""


"""def business_score(row, profile):

    score = 0.0

    # ───────── RISK (BETA)
    beta = row.get("Beta", 0.5)
    risk = profile.get("risk", "medium")

    if risk == "low":
        score += (1 - beta)
    elif risk == "high":
        score += beta
    else:
        score += 0.5

    # ───────── SECTOR MATCH
    if row.get("Sector") == profile.get("sector"):
        score += 1.0

    # ───────── EBITDA (simple signal)
    ebitda = row.get("EBITDA Margins", 0)
    score += ebitda

    # ───────── DEBT PENALTY
    debt = row.get("Net_Debt", 0)
    score -= debt / 1_000_000

    return np.clip(score, 0, 1)"""


"""
import numpy as np

def business_score(row, profile):

    score = 0.0

    beta = row.get("Beta", 0.5)
    risk = profile.get("risk", "medium")

    # risk signal
    if risk == "low":
        score += (1 - beta)
    elif risk == "high":
        score += beta
    else:
        score += 0.5

    # sector match
    if row.get("Sector") == profile.get("sector"):
        score += 0.6

    # EBITDA (safe)
    ebitda = float(row.get("EBITDA Margins") or 0)
    score += ebitda

    # debt penalty (normalized)
    debt = float(row.get("Net_Debt") or 0)
    score -= debt / 1_000_000

    # normalize
    return np.clip(score, 0, 1)"""
"""
import numpy as np

def business_score(row, profile):

    score = 0.0

    beta = float(row.get("Beta") or 0.5)
    risk = profile.get("risk", "medium")

    # ── risk signal
    if risk == "low":
        score += (1 - beta)
    elif risk == "high":
        score += beta
    else:
        score += 0.5

    # ── sector match
    if row.get("Sector") == profile.get("sector"):
        score += 0.4

    # ── EBITDA (normalized)
    ebitda = float(row.get("EBITDA Margins") or 0)
    ebitda = np.tanh(ebitda)  
    score += ebitda * 0.2

    # ── debt penalty (log scale)
    debt = float(row.get("Net_Debt") or 0)
    debt_penalty = np.log1p(debt) / 10
    score -= debt_penalty

    # ── final safe normalization
    return float(np.tanh(score))"""

import numpy as np
def business_score(row, profile):

    score = 0.0

    beta = float(row.get("Beta") or 0.5)
    risk = profile.get("risk", "medium")

    # risk
    if risk == "low":
        score += (1 - beta)
    elif risk == "high":
        score += beta
    else:
        score += 0.5

    # sector
    if row.get("Sector") == profile.get("sector"):
        score += 0.4

    # EBITDA
    ebitda = float(row.get("EBITDA Margins") or 0)
    score += np.tanh(ebitda) * 0.2

    # debt penalty
    debt = float(row.get("Net_Debt") or 0)
    score -= np.log1p(debt) / 10

    # ── FINAL NORMALIZATION (IMPORTANT)
    score = np.tanh(score)

    # convert [-1,1] → [0,1]
    return float((score + 1) / 2)