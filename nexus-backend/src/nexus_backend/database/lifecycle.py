"""Database lifecycle — DDL creation & data seeding.

Responsabilidad única: preparar el esquema y los datos iniciales.
Separado del engine y del session management.
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

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────
# Registro de modelos — centralizado y explícito
# ──────────────────────────────────────────────────────────────
# Agregar un nuevo bounded context = agregar un string aquí.
# No más imports dispersos con `# noqa: F401`.
# ──────────────────────────────────────────────────────────────
_MODEL_MODULES: list[str] = [
    "nexus_backend.auth.infrastructure.models",
    "nexus_backend.catalog.infrastructure.models",
    "nexus_backend.orders.infrastructure.models",
]


def _register_models() -> None:
    """Importa todos los módulos de modelos para registrar metadata.

    Centralizado aquí para que agregar un nuevo bounded context
    sea un solo cambio en ``_MODEL_MODULES``, no una búsqueda en
    código disperso.
    """
    for module_path in _MODEL_MODULES:
        importlib.import_module(module_path)
    logger.info("Registered %d model modules", len(_MODEL_MODULES))


async def _create_extensions(engine: AsyncEngine) -> None:
    """Crea extensiones de Postgres requeridas."""
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    logger.info("PostgreSQL extensions verified")


async def _create_schema(engine: AsyncEngine) -> None:
    """Genera tablas DDL a partir de Base.metadata."""
    from nexus_backend.shared.infrastructure.models import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database schema created/verified")


async def init_db(
    engine: AsyncEngine,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Orquestador de inicialización — compone los pasos atómicos.

    Recibe dependencias inyectadas en vez de acceder a globales.
    Los usuarios y roles son gestionados exclusivamente por Neon Auth.
    """
    _register_models()
    await _create_extensions(engine)
    await _create_schema(engine)
    logger.info("Database initialization complete (Auth managed by Neon Auth)")


async def shutdown_db(engine: AsyncEngine) -> None:
    """Cierra el engine limpiamente en el shutdown del app."""
    await engine.dispose()
    logger.info("Database engine disposed")
