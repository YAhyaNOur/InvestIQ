import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text  # <- important

DATABASE_URL = "postgresql+asyncpg://postgres:admin@localhost:5432/smartstart_db"

async def test_connection():
    engine = create_async_engine(DATABASE_URL, echo=True)
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))  # <- text() autour de la requête
            print("DB connection OK:", result.scalar())
    except Exception as e:
        print("DB connection failed:", e)

asyncio.run(test_connection())