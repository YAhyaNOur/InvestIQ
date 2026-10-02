import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

DATABASE_URL = 'postgresql+asyncpg://postgres:admin@localhost:5432/smartstart_db'

async def fix():
    engine = create_async_engine(DATABASE_URL)
    async with engine.begin() as conn:
        r1 = await conn.execute(text(
            "SELECT column_name FROM information_schema.columns WHERE table_name = 'roles'"
        ))
        print('Colonnes:', r1.fetchall())

        r2 = await conn.execute(text('SELECT * FROM roles'))
        print('Contenu:', r2.fetchall())

        # Insérer les rôles avec la bonne colonne
        await conn.execute(text(
            "INSERT INTO roles (name) VALUES ('INVESTOR'), ('CANDIDATE'), ('STARTUPER') ON CONFLICT DO NOTHING"
        ))
        print('Roles inseres!')

        r3 = await conn.execute(text('SELECT * FROM roles'))
        print('Apres insertion:', r3.fetchall())

asyncio.run(fix())