import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ⚠️ IMPORT DIRECT DES MODULES (IMPORTANT)
import models3.code.main as colleague_main
import Model_recommendation_talents_jobs.code.API.main as talent_main

# apps
colleague_app = colleague_main.app
talent_app = talent_main.app

print("Colleague loaded:", colleague_app)
print("Talent loaded:", talent_app)

# gateway
collective_app = FastAPI()

collective_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

collective_app.mount("/colleague", colleague_app)
collective_app.mount("/talent", talent_app)

if __name__ == "__main__":
    uvicorn.run(
        "run:collective_app",
        host="0.0.0.0",
        port=8082
    )