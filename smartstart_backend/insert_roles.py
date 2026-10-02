import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

DATABASE_URL = 'postgresql+asyncpg://postgres:admin@localhost:5432/smartstart_db'

async def insert():
    engine = create_async_engine(DATABASE_URL)
    async with engine.begin() as conn:
        await conn.execute(text("INSERT INTO roles (name) VALUES ('INVESTOR'), ('STARTUPER') ON CONFLICT DO NOTHING"))
        result = await conn.execute(text('SELECT * FROM roles'))
        print('Roles inseres:', result.fetchall())

asyncio.run(insert())
