import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def fix():
    engine = create_async_engine('postgresql+asyncpg://postgres:admin@localhost:5432/smartstart_db')
    async with engine.begin() as conn:
        # Supprimer "string"
        await conn.execute(text("DELETE FROM companies WHERE name = 'string'"))
        # Supprimer GreenPower doublon (garder id 5)
        await conn.execute(text("DELETE FROM companies WHERE company_id = 6"))
        # Ajouter TechCorp manquante
        await conn.execute(text("""
            INSERT INTO companies (user_id, name, sector, industry_group, region_std, beta, ebitda_margins, revenue_per_employee, net_debt)
            VALUES (1, 'TechCorp', 'Technology', 'Software', 'US', 1.2, 0.25, 500000, 200000)
        """))
        r = await conn.execute(text('SELECT company_id, name, sector FROM companies'))
        print('Companies:', r.fetchall())

asyncio.run(fix())