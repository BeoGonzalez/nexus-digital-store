"""Script para sincronizar el catálogo de videojuegos con el índice de Pinecone."""

import asyncio
import logging

from dotenv import load_dotenv

load_dotenv()

from nexus_backend.ai_assistant.infrastructure.embeddings import HuggingFaceEmbeddingAdapter
from nexus_backend.ai_assistant.infrastructure.pinecone_store import PineconeVectorStoreAdapter
from nexus_backend.catalog.application.services import CatalogService
from nexus_backend.catalog.infrastructure.repositories import SQLAlchemyVideoGameRepository
from nexus_backend.config import get_settings
from nexus_backend.database import (
    DatabaseConnectionConfig,
    create_db_engine,
    create_session_factory,
    shutdown_db,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sync_pinecone")


async def main() -> None:
    settings = get_settings()
    logger.info("Iniciando sincronización con Pinecone: index=%s, namespace=%s", settings.PINECONE_INDEX_NAME, settings.PINECONE_NAMESPACE)

    db_config = DatabaseConnectionConfig(
        database_url=settings.DATABASE_URL,
        echo=False,
        ssl=settings.DB_SSL,
    )
    engine = create_db_engine(db_config)
    session_factory = create_session_factory(engine)

    pinecone_adapter = PineconeVectorStoreAdapter(
        api_key=settings.PINECONE_API_KEY,
        index_name=settings.PINECONE_INDEX_NAME,
        namespace=settings.PINECONE_NAMESPACE,
    )

    embedding_adapter = HuggingFaceEmbeddingAdapter(
        model_name=settings.EMBEDDING_MODEL_NAME,
    )

    async with session_factory() as session:
        repo = SQLAlchemyVideoGameRepository(session)
        service = CatalogService(repo)

        games = await service.list_video_games(skip=0, limit=200)
        logger.info("Encontrados %d juegos en la base de datos.", len(games))

        synced = 0
        for game in games:
            genres_str = ", ".join(g.name for g in game.genres)
            text_to_embed = f"{game.title} {genres_str} {game.description}"
            embedding = await embedding_adapter.embed_text(text_to_embed)

            # Actualizar embedding en DB y Pinecone
            await pinecone_adapter.upsert_game(game, embedding)
            synced += 1
            logger.info("Sincronizado: %s (ID: %s)", game.title, game.id)

        await session.commit()
        logger.info("✅ Sincronización finalizada exitosamente: %d juegos indexados.", synced)

    await shutdown_db(engine)


if __name__ == "__main__":
    asyncio.run(main())

