import sys
import os
sys.path.append(os.path.abspath("Backend/code"))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.api_growth import router as growth_router
from api.api_risk import router as risk_router
from api.api_hybride import router as hybrid_router
from service.api import router as service_router

app = FastAPI(title="BiAi Platform API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(growth_router, prefix="/growth")
app.include_router(risk_router, prefix="/risk")
app.include_router(hybrid_router, prefix="/score", tags=["Hybrid Analysis"])
app.include_router(service_router, prefix="/data")