# app/api/routers/startup_dashboard.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import logging
import httpx
import os

from app.db.session import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.schemas.startup_dashboard import (
    AIAssistantRequest,
    AIAssistantResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/startup", tags=["Startup Dashboard"])

N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "http://localhost:5678/webhook/startup-ai")


# ── helpers ───────────────────────────────────────────────────────────────────

def _require_startuper(user: User) -> None:
    roles = [ur.role.name for ur in user.user_roles if ur.role]
    if "STARTUPER" not in roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Réservé aux comptes STARTUPER.",
        )


# ── AI ASSISTANT ──────────────────────────────────────────────────────────────

@router.post("/ai/ask", response_model=AIAssistantResponse)
async def ask_ai_assistant(
    payload: AIAssistantRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _require_startuper(current_user)
    uid = current_user.user_id

    context = {
        "user_id": uid,
        "startup_name": getattr(current_user, "company_name", None) or current_user.username,
        "message": payload.message,
        "action": payload.action,
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(N8N_WEBHOOK_URL, json=context)
            resp.raise_for_status()
            data = resp.json()
            result_text = data.get("result") or data.get("output") or data.get("text") or str(data)
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Le workflow n8n a mis trop de temps à répondre.")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"Erreur n8n : {e.response.status_code}")
    except Exception as e:
        logger.error(f"Erreur AI assistant: {e}")
        raise HTTPException(status_code=500, detail="Erreur lors de la communication avec l'assistant IA.")

    return AIAssistantResponse(result=result_text, action=payload.action)