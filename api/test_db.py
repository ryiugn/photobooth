import asyncio
from sqlalchemy.ext.asyncio import create_async_engine

DATABASE_URL = "postgresql+asyncpg://postgres.dcwnkzyeaxbdsnidocda:ryreru4lyfe@aws-1-ap-south-1.pooler.supabase.com:6543/postgres"

async def test():
    engine = create_async_engine(DATABASE_URL)
    async with engine.begin() as conn:
        print('Database connected!')
    await engine.dispose()

asyncio.run(test())
