# smartstart_backend/app/routers/crypto.py

from fastapi import APIRouter, HTTPException
from app.schemas.crypto import CryptoRequest, CryptoResult
from app.services.crypto_service import CryptoService

router = APIRouter(tags=["Crypto Analysis"])

crypto_service = CryptoService()


@router.post("/analyze", response_model=CryptoResult)
async def analyze_crypto(request: CryptoRequest):
    try:
        result = await crypto_service.analyze(request)
        return result

    except ValueError as e:
        msg = str(e)

        # erreurs utilisateur (400)
        if "insuffisantes" in msg.lower() or "ticker" in msg.lower():
            raise HTTPException(status_code=400, detail=msg)

        # erreurs serveur (500)
        raise HTTPException(status_code=500, detail=msg)

    except Exception as e:
        # sécurité finale (évite crash backend)
        raise HTTPException(
            status_code=500,
            detail=f"Erreur interne serveur: {str(e)}"
        )