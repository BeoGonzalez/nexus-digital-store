import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

from nexus_backend.database.engine import create_db_engine, DatabaseConnectionConfig
from nexus_backend.database.lifecycle import _register_models, _create_schema

async def run():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("DATABASE_URL no está configurada")
        return

    ssl_enabled = os.environ.get("DB_SSL", "false").lower() in ("true", "1", "yes")
    engine = create_db_engine(DatabaseConnectionConfig(database_url=db_url, ssl=ssl_enabled))
    _register_models()
    await _create_schema(engine)
    print("Tablas creadas y verificadas en Aurora PostgreSQL")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(run())
