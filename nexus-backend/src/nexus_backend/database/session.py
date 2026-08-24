"""Session factory & FastAPI dependency.

Responsabilidad única: crear y gestionar el ciclo de vida
de AsyncSession dentro de una unit of work.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
)

logger = logging.getLogger(__name__)

# Será inicializado en el lifespan del app — nunca al importar.
_session_factory: async_sessionmaker[AsyncSession] | None = None


def create_session_factory(
    engine: AsyncEngine,
) -> async_sessionmaker[AsyncSession]:
    """Crea y registra el session factory global.

    Debe llamarse UNA VEZ durante el startup del application,
    no como side-effect de importación.
    """
    global _session_factory  # noqa: PLW0603
    _session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    logger.info("Session factory initialized")
    return _session_factory


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Accessor defensivo — falla rápido si no se inicializó."""
    if _session_factory is None:
        raise RuntimeError(
            "Session factory not initialized. "
            "Call create_session_factory() during app startup."
        )
    return _session_factory


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency — unit of work con commit/rollback automático.

    • Yield pattern para que FastAPI gestione el lifecycle.
    • Commit implícito al final exitoso del request.
    • Rollback explícito ante cualquier excepción no manejada.
    """
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
