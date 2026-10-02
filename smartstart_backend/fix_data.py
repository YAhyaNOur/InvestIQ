import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def fix():
    engine = create_async_engine('postgresql+asyncpg://postgres:admin@localhost:5432/smartstart_db')
    async with engine.begin() as conn:
        # Fix sectors investors
        await conn.execute(text("UPDATE investors SET preferred_sector='Tech' WHERE preferred_sector IN ('tech', 'Technology', 'technology')"))
        await conn.execute(text("UPDATE investors SET preferred_sector='Finance' WHERE preferred_sector IN ('finance')"))
        await conn.execute(text("UPDATE investors SET preferred_sector='Healthcare' WHERE preferred_sector IN ('health', 'healthcare', 'Health')"))

        # Fix regions investors
        await conn.execute(text("UPDATE investors SET region_std='North_America' WHERE region_std IS NULL OR region_std IN ('US', 'usa', 'us')"))
        await conn.execute(text("UPDATE investors SET region_std='Europe' WHERE region_std IN ('EU', 'eu', 'europe')"))
        await conn.execute(text("UPDATE investors SET region_std='Asia' WHERE region_std IN ('AS', 'as', 'asia')"))
        await conn.execute(text("UPDATE investors SET region_std='Other' WHERE region_std IN ('AF', 'af', 'africa')"))

        # Fix sectors companies
        await conn.execute(text("UPDATE companies SET sector='Tech' WHERE sector IN ('Technology', 'technology', 'tech')"))
        await conn.execute(text("UPDATE companies SET sector='Finance' WHERE sector IN ('finance', 'Banking')"))
        await conn.execute(text("UPDATE companies SET sector='Healthcare' WHERE sector IN ('health', 'Pharma', 'healthcare')"))
        await conn.execute(text("UPDATE companies SET sector='Energy' WHERE sector IN ('energy', 'Renewable')"))
        await conn.execute(text("UPDATE companies SET sector='Education' WHERE sector IN ('education', 'EdTech')"))

        # Fix regions companies
        await conn.execute(text("UPDATE companies SET region_std='North_America' WHERE region_std IN ('US', 'us', 'usa')"))
        await conn.execute(text("UPDATE companies SET region_std='Europe' WHERE region_std IN ('EU', 'eu')"))
        await conn.execute(text("UPDATE companies SET region_std='Asia' WHERE region_std IN ('AS', 'as')"))
        await conn.execute(text("UPDATE companies SET region_std='Other' WHERE region_std IN ('AF', 'af') OR region_std IS NULL"))

        # Vérification
        r1 = await conn.execute(text('SELECT user_id, preferred_sector, region_std FROM investors ORDER BY investor_id DESC LIMIT 5'))
        print('Investors:', r1.fetchall())
        r2 = await conn.execute(text('SELECT company_id, name, sector, region_std FROM companies'))
        print('Companies:', r2.fetchall())

asyncio.run(fix())