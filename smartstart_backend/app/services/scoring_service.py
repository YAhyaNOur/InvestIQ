"""
Scoring Service — Rule-based scoring engine
Exploite RÉELLEMENT les résultats NLP (secteur, confiance, keywords).
Exclusivement pour projets internes d'entreprise (CEO / sociétés existantes).
"""

from typing import Any

# --- Signal dictionaries ---

FEASIBILITY_SIGNALS = {
    "high": [
        "budget défini", "équipe en place", "fournisseur identifié", "délai précis",
        "expérience interne", "déjà réalisé", "maîtrisé", "validé", "approuvé"
    ],
    "medium": [
        "étude de faisabilité", "devis", "planifié", "prévu", "en cours d'analyse"
    ],
    "low": [
        "incertain", "à définir", "pas encore étudié", "complexe", "première fois"
    ]
}

ROI_SIGNALS = {
    "high": [
        "rentable", "retour rapide", "économies importantes", "gain de productivité",
        "réduction de coût", "augmentation de capacité", "revenu supplémentaire"
    ],
    "medium": [
        "amélioration", "optimisation", "efficacité", "performance",
        "qualité", "satisfaction"
    ],
    "low": [
        "coût élevé", "investissement lourd", "long terme", "incertain"
    ]
}

OPERATIONAL_RISK_SIGNALS = {
    "high": [
        "délai serré", "budget insuffisant", "dépendance externe", "réglementation",
        "opposition interne", "ressources limitées", "risque juridique"
    ],
    "medium": [
        "coordination requise", "formation nécessaire", "changement organisationnel",
        "dépendance fournisseur"
    ],
    "low": [
        "équipe expérimentée", "budget validé", "process connu", "faible impact"
    ]
}

TEAM_SIGNALS = [
    "expérience", "expert", "fondateur", "équipe", "années d'expérience",
    "spécialiste", "diplôme", "anciennement"
]

# --- Scores de base par secteur ---

SECTOR_BASE_SCORES = {
    "Immobilier / Construction":    {"feasibility": 65, "roi": 60, "risk": 55},
    "IT / Transformation digitale": {"feasibility": 60, "roi": 70, "risk": 45},
    "RH / Expansion":               {"feasibility": 70, "roi": 65, "risk": 35},
    "Production / Industrie":       {"feasibility": 65, "roi": 65, "risk": 50},
    "Commercial / Marketing":       {"feasibility": 72, "roi": 68, "risk": 40},
    "Finance / Investissement":     {"feasibility": 65, "roi": 70, "risk": 55},
    "Logistique / Supply Chain":    {"feasibility": 68, "roi": 65, "risk": 45},
    "Autre":                        {"feasibility": 55, "roi": 55, "risk": 50},
}


def _count_signals(text: str, signals: list[str]) -> int:
    return sum(1 for s in signals if s in text)


def _clamp(val: int, lo: int = 0, hi: int = 100) -> int:
    return max(lo, min(hi, val))


def compute_scores(description: str, nlp_result: dict[str, Any]) -> dict[str, Any]:
    text = description.lower()
    sector = nlp_result.get("sector", "Autre")
    base = SECTOR_BASE_SCORES.get(sector, SECTOR_BASE_SCORES["Autre"])

    
    sector_scores = nlp_result.get("sector_scores", {})
    sector_confidence = sector_scores.get(sector, 0)          # nb mots matchés
    confidence_bonus = min(sector_confidence, 10) // 2        # 0 à 5 pts

    # Si plusieurs secteurs détectés → projet multi-domaine → risque plus élevé
    multi_sector_count = len([s for s, v in sector_scores.items() if v > 0])
    multi_sector_penalty = max(0, (multi_sector_count - 1) * 5)  # +5 risque par secteur supplémentaire

    # ── 2. Richesse des keywords NLP ────────────────────────────────────────
    # Plus la description est précise (mots-clés riches), plus la faisabilité monte
    keyword_count = len(nlp_result.get("keywords", []))
    keyword_bonus = min(keyword_count, 8) * 1  # 0 à 8 pts de faisabilité

    # ── 3. Calcul faisabilité ───────────────────────────────────────────────
    feasibility = base["feasibility"]
    feasibility += confidence_bonus                                           # NLP confiance
    feasibility += keyword_bonus                                              # richesse description
    feasibility += _count_signals(text, FEASIBILITY_SIGNALS["high"]) * 5
    feasibility += _count_signals(text, FEASIBILITY_SIGNALS["medium"]) * 2
    feasibility -= _count_signals(text, FEASIBILITY_SIGNALS["low"]) * 4
    feasibility = _clamp(feasibility)

    # ── 4. Calcul ROI ───────────────────────────────────────────────────────
    roi = base["roi"]
    roi += confidence_bonus                                                   # NLP confiance
    roi += _count_signals(text, ROI_SIGNALS["high"]) * 5
    roi += _count_signals(text, ROI_SIGNALS["medium"]) * 2
    roi -= _count_signals(text, ROI_SIGNALS["low"]) * 4
    roi = _clamp(roi)

    # ── 5. Calcul risque opérationnel ───────────────────────────────────────
    op_risk = base["risk"]
    op_risk += multi_sector_penalty                                          
    op_risk += _count_signals(text, OPERATIONAL_RISK_SIGNALS["high"]) * 6
    op_risk += _count_signals(text, OPERATIONAL_RISK_SIGNALS["medium"]) * 3
    op_risk -= _count_signals(text, OPERATIONAL_RISK_SIGNALS["low"]) * 4
    op_risk -= _count_signals(text, TEAM_SIGNALS) * 2
    op_risk = _clamp(op_risk)

    # ── 6. Score global ─────────────────────────────────────────────────────
    # Faisabilité 40% + ROI 35% + (inverse du risque) 25%
    global_score = int(
        feasibility * 0.40 +
        roi         * 0.35 +
        (100 - op_risk) * 0.25
    )
    global_score = _clamp(global_score)

    return {
        "global_score":       global_score,
        "feasibility":        feasibility,
        "roi_score":          roi,
        "risk_level":         op_risk,
        "market_potential":   roi,
        "innovation_score":   feasibility,
        "sector_confidence":  sector_confidence,    
        "multi_sector":       multi_sector_count,   
        "mode":               "enterprise",
    }