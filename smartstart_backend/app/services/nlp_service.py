"""
NLP Service — Business sector detection + keyword extraction
Adapté exclusivement pour analyser des projets internes d'entreprise (CEO / sociétés existantes).
"""

import re
from typing import Any

SECTOR_KEYWORDS: dict[str, list[str]] = {
    "Immobilier / Construction": [
        "construction", "bâtiment", "bloc", "immeuble", "local", "locaux",
        "extension", "rénovation", "travaux", "génie civil", "chantier",
        "surface", "infrastructure", "aménagement", "bâtir", "terrain"
    ],
    "IT / Transformation digitale": [
        "système", "logiciel", "digital", "numérique", "erp", "crm", "api",
        "plateforme", "application", "automatisation", "données", "cloud",
        "cybersécurité", "intégration", "migration", "infrastructure it"
    ],
    "RH / Expansion": [
        "recrutement", "embauche", "équipe", "talent", "effectif", "formation",
        "compétence", "collaborateur", "ressources humaines", "onboarding",
        "politique rh", "masse salariale", "organigramme"
    ],
    "Production / Industrie": [
        "production", "usine", "chaîne", "fabrication", "équipement", "machine",
        "atelier", "rendement", "capacité", "process", "qualité", "industrie"
    ],
    "Commercial / Marketing": [
        "vente", "client", "marché", "croissance", "chiffre d'affaires", "prospection",
        "fidélisation", "campagne", "communication", "branding", "commercial"
    ],
    "Finance / Investissement": [
        "investissement", "financement", "budget", "trésorerie", "coût",
        "rentabilité", "retour sur investissement", "roi", "capital", "emprunt",
        "crédit", "bilan", "fiscalité"
    ],
    "Logistique / Supply Chain": [
        "logistique", "stock", "entrepôt", "livraison", "fournisseur", "approvisionnement",
        "chaîne logistique", "transport", "flux", "inventaire", "distribution"
    ],
}

PROJECT_TYPES = {
    "Construction / Immobilier": [
        "construction", "bloc", "bâtiment", "extension", "travaux", "chantier", "rénovation"
    ],
    "Transformation digitale": [
        "système", "erp", "logiciel", "plateforme", "digital", "numérique", "automatisation"
    ],
    "Expansion commerciale": [
        "nouveau marché", "expansion", "croissance", "commercial", "ouverture"
    ],
    "Recrutement / RH": [
        "recrutement", "embauche", "équipe", "talent", "effectif"
    ],
    "Logistique / Supply Chain": [
        "logistique", "stock", "entrepôt", "fournisseur", "approvisionnement", "distribution"
    ],
    "Finance / Investissement": [
        "budget", "financement", "trésorerie", "investissement", "roi", "rentabilité"
    ],
    "Production / Industrie": [
        "production", "usine", "fabrication", "machine", "atelier", "capacité"
    ],
}

TEAM_SIGNALS = [
    "expérience", "expert", "fondateur", "équipe", "années d'expérience",
    "spécialiste", "diplôme", "anciennement"
]


def clean_text(text: str) -> str:
    return text.lower().strip()


def extract_sector_and_keywords(description: str) -> dict[str, Any]:
    text = clean_text(description)

    # Sector detection
    sector_scores: dict[str, int] = {}
    matched_keywords: list[str] = []

    for sector, kws in SECTOR_KEYWORDS.items():
        count = sum(1 for kw in kws if kw in text)
        if count > 0:
            sector_scores[sector] = count
            matched_keywords.extend([kw for kw in kws if kw in text])

    sector = max(sector_scores, key=sector_scores.get) if sector_scores else "Autre"

    # Project type
    project_type = "Projet interne"
    for ptype, signals in PROJECT_TYPES.items():
        if any(s in text for s in signals):
            project_type = ptype
            break

    # Extract meaningful keywords
    seen = set()
    unique_keywords = []
    for kw in matched_keywords:
        if kw not in seen and len(kw) > 3:
            seen.add(kw)
            unique_keywords.append(kw.capitalize())
        if len(unique_keywords) >= 8:
            break

    target_market = f"Projet interne — Impact opérationnel — Secteur {sector}"

    return {
        "sector": sector,
        "project_type": project_type,
        "keywords": unique_keywords,
        "target_market": target_market,
        "is_enterprise": True,
        "raw_text": description,
        "sector_scores": sector_scores,
    }