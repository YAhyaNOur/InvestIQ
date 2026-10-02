# app/schemas/startup_dashboard.py

from pydantic import BaseModel
from typing import Optional


# ─────────────────────────────────────────────
#  AI ASSISTANT  (proxy → n8n)
# ─────────────────────────────────────────────

class AIAssistantRequest(BaseModel):
    message: str
    action: Optional[str] = None   # "summary" | "career_advice" | "custom"


class AIAssistantResponse(BaseModel):
    result: str
    action: Optional[str] = None