"""Database lifecycle — DDL creation & safe startup for Amazon Aurora PostgreSQL.

Responsabilidad única: preparar el esquema de datos de forma segura
ante concurrencia (evitando carreras entre tareas de AWS ECS).
"""

from __future__ import annotations

import importlib
import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
)

from nexus_backend.config import get_settings

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────
# Registro de modelos — centralizado y explícito
# ──────────────────────────────────────────────────────────────
_MODEL_MODULES: list[str] = [
    "nexus_backend.catalog.infrastructure.models",
    "nexus_backend.orders.infrastructure.models",
]


def _register_models() -> None:
    """Importa todos los módulos de modelos para registrar metadata."""
    for module_path in _MODEL_MODULES:
        importlib.import_module(module_path)
    logger.info("Registered %d model modules for DDL generation", len(_MODEL_MODULES))


async def _create_schema(engine: AsyncEngine) -> None:
    """Genera tablas DDL a partir de Base.metadata protegiéndose con advisory lock."""
    from nexus_backend.shared.infrastructure.models import Base

    # ID arbitrario de 64 bits para el advisory lock a nivel de transacción
    ADVISORY_LOCK_ID = 718293041

    try:
        async with engine.begin() as conn:
            logger.info("Acquiring Postgres advisory lock (%d) for safe DDL migration...", ADVISORY_LOCK_ID)
            await conn.execute(
                text("SELECT pg_advisory_xact_lock(:lock_id)"),
                {"lock_id": ADVISORY_LOCK_ID},
            )
            logger.info("Advisory lock acquired. Creating/verifying database tables...")
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Database tables created/verified successfully in schema 'public'")
    except Exception as exc:
        logger.critical(
            "Database schema initialization failed on Aurora PostgreSQL: %s",
            exc,
            exc_info=True,
        )
        raise


async def init_db(
    engine: AsyncEngine,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Orquestador de inicialización de base de datos en el arranque de la app."""
    settings = get_settings()

    if not settings.RUN_DB_INIT:
        logger.info("RUN_DB_INIT=false: Skipping schema initialization.")
        return

    _register_models()
    try:
        await _create_schema(engine)
        logger.info("Database initialization complete (Aurora PostgreSQL)")
    except Exception as exc:
        logger.error("Error during database startup initialization: %s", exc)
        raise


async def shutdown_db(engine: AsyncEngine) -> None:
    """Cierra el engine limpiamente en el shutdown del app."""
    await engine.dispose()
    logger.info("Database engine disposed")
