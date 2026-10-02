"""
LLM Service — Prompt Builder + LLaMA via Ollama
Exclusivement pour projets internes d'entreprise (CEO / société existante).
"""

import json
import re
import httpx
from typing import Any

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3"


def build_prompt(description: str, nlp_result: dict, scores: dict) -> str:
    sector = nlp_result["sector"]
    project_type = nlp_result["project_type"]
    keywords = ", ".join(nlp_result["keywords"]) if nlp_result["keywords"] else "Non détectés"
    global_score = scores["global_score"]
    feasibility = scores.get("feasibility", 0)
    roi_score = scores.get("roi_score", 0)
    risk_level = scores["risk_level"]

    return f"""Tu es un consultant expert en gestion de projets d'entreprise. Analyse ce projet interne de manière professionnelle.

PROJET :
{description}

ANALYSE PRÉLIMINAIRE :
- Secteur : {sector}
- Type de projet : {project_type}
- Mots-clés : {keywords}
- Score global : {global_score}/100
- Faisabilité : {feasibility}/100
- ROI estimé : {roi_score}/100
- Risque opérationnel : {risk_level}/100

Réponds UNIQUEMENT avec un objet JSON valide (sans markdown, sans explication) :
{{
  "advantages": ["point fort 1", "point fort 2", "point fort 3"],
  "disadvantages": ["risque ou contrainte 1", "risque ou contrainte 2", "risque ou contrainte 3"],
  "recommendation": "Recommandation concrète en 3-4 phrases pour le dirigeant : comment piloter ce projet, quelles étapes prioritaires, comment maîtriser les coûts et les délais.",
  "funding_potential": "Ex: Budget estimé 50K€ - 200K€ — ROI attendu sous 18-24 mois"
}}

Utilise un vocabulaire de management de projet : budget, délai, parties prenantes, ROI, risque opérationnel, plan d'exécution. Ne mentionne PAS de levée de fonds, MVP, ou early adopters."""


def _parse_llm_json(raw: str) -> dict:
    match = re.search(r'\{[\s\S]*\}', raw)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    raise ValueError(f"LLM output non parseable: {raw[:200]}")


def _fallback_response(scores: dict, nlp_result: dict) -> dict:
    """Fallback si Ollama n'est pas disponible."""
    sector = nlp_result.get("sector", "Autre")
    return _fallback_enterprise(scores, sector)


def _fallback_enterprise(scores: dict, sector: str) -> dict:
    global_score = scores["global_score"]
    feasibility = scores.get("feasibility", scores.get("innovation_score", 50))
    risk = scores["risk_level"]

    if global_score >= 70:
        reco = (
            f"Ce projet {sector} présente une bonne faisabilité et un retour sur investissement intéressant. "
            "Définissez un plan d'exécution détaillé avec des jalons clairs. "
            "Identifiez les parties prenantes clés et sécurisez le budget dès la phase de lancement. "
            "Un suivi mensuel des indicateurs de performance permettra de maîtriser les délais et les coûts."
        )
        budget = "Budget recommandé : étude de faisabilité + lancement progressif"
    elif global_score >= 50:
        reco = (
            f"Le projet {sector} est réalisable mais nécessite une préparation rigoureuse. "
            "Commencez par une étude de faisabilité approfondie et obtenez des devis précis. "
            "Identifiez les risques opérationnels en amont et prévoyez une marge budgétaire de 15-20%. "
            "Impliquez les équipes concernées dès la phase de planification."
        )
        budget = "Budget à préciser après étude de faisabilité"
    else:
        reco = (
            "Ce projet nécessite d'être mieux défini avant toute décision d'investissement. "
            "Clarifiez les objectifs, le périmètre et les ressources disponibles. "
            "Une analyse coût-bénéfice détaillée est indispensable avant de procéder. "
            "Envisagez de consulter des experts externes pour évaluer la faisabilité."
        )
        budget = "Phase d'analyse préalable recommandée avant tout engagement"

    advantages = [
        "Projet structurant pour le développement de la société",
        "Impact opérationnel positif attendu",
        f"Secteur {sector} avec des retours mesurables"
    ]

    disadvantages = [
        "Budget et délais à affiner précisément",
        "Coordination interne à anticiper",
        "Risques opérationnels à identifier et mitiger"
    ]

    if risk >= 60:
        disadvantages.append("Niveau de risque opérationnel élevé — plan de gestion des risques requis")

    return {
        "advantages": advantages,
        "disadvantages": disadvantages,
        "recommendation": reco,
        "funding_potential": budget,
    }


async def generate_llm_analysis(
    description: str,
    nlp_result: dict[str, Any],
    scores: dict[str, int]
) -> dict[str, Any]:
    prompt = build_prompt(description, nlp_result, scores)

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                OLLAMA_URL,
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.4,
                        "top_p": 0.9,
                        "num_predict": 600,
                    }
                }
            )

            if response.status_code != 200:
                return _fallback_response(scores, nlp_result)

            data = response.json()
            raw_text = data.get("response", "")
            return _parse_llm_json(raw_text)

    except (httpx.ConnectError, httpx.TimeoutException):
        return _fallback_response(scores, nlp_result)
    except (ValueError, KeyError):
        return _fallback_response(scores, nlp_result)