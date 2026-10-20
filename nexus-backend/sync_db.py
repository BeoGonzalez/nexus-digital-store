import asyncio
import os
from nexus_backend.database.engine import create_db_engine, NeonConnectionConfig
from nexus_backend.shared.infrastructure.models import Base
from nexus_backend.database.lifecycle import _register_models
from dotenv import load_dotenv

load_dotenv()

async def run():
    engine = create_db_engine(NeonConnectionConfig(database_url=os.environ['DATABASE_URL']))
    _register_models()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print('Created missing tables')
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(run())
