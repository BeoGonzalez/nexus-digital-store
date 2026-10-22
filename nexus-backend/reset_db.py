import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

from nexus_backend.database.engine import create_db_engine, DatabaseConnectionConfig
from nexus_backend.shared.infrastructure.models import Base
from nexus_backend.database.lifecycle import _register_models, _create_schema
from sqlalchemy import text

async def reset_db():
    print("Resetting database...")
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("DATABASE_URL not set in .env")
        return

    ssl_enabled = os.environ.get("DB_SSL", "false").lower() in ("true", "1", "yes")
    config = DatabaseConnectionConfig(database_url=db_url, ssl=ssl_enabled)
    engine = create_db_engine(config)

    _register_models()

    async with engine.begin() as conn:
        print("Dropping existing application tables...")
        await conn.execute(text("DROP TABLE IF EXISTS payment_methods CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS order_items CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS orders CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS video_game_genres CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS video_games CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS genres CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS platforms CASCADE"))
        print("Recreating tables...")
        await conn.run_sync(Base.metadata.create_all)

    print("Database reset complete.")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(reset_db())
