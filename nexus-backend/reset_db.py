import asyncio
import os
from nexus_backend.database.engine import create_db_engine, NeonConnectionConfig
from nexus_backend.shared.infrastructure.models import Base
from nexus_backend.database.lifecycle import _register_models, _create_extensions
from dotenv import load_dotenv

load_dotenv()

async def reset_db():
    print("Resetting database...")
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("DATABASE_URL not set in .env")
        return
        
    config = NeonConnectionConfig(database_url=db_url)
    engine = create_db_engine(config)
    
    _register_models()
    
    async with engine.begin() as conn:
        print("Dropping specific tables...")
        from sqlalchemy import text
        await conn.execute(text("DROP TABLE IF EXISTS video_game_genres CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS video_games CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS genres CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS platforms CASCADE"))
        print("Creating extensions...")
        await _create_extensions(engine)
        print("Creating all tables...")
        await conn.run_sync(Base.metadata.create_all)
        
    print("Database reset complete.")
    await engine.dispose()
        
    print("Database reset complete.")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(reset_db())
