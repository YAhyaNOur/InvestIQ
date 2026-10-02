import asyncio
from app.db.session import engine, Base
from app.models.user import User
from app.models.company import Company
from app.models.investor import Investor
from app.models.investment_recommendation import InvestmentRecommendation
from app.models.investor_interest import InvestorInterest
from app.models.role import Role
from app.models.user_role import UserRole

async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables creees avec succes !")

asyncio.run(create_tables())
