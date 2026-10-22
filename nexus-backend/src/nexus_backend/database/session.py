"""Session factory & FastAPI dependency.

Responsabilidad única: crear y gestionar el ciclo de vida
de AsyncSession dentro de una unit of work.
Soporta writer y opcionalmente reader (Amazon Aurora).
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

# Serán inicializados en el lifespan del app — nunca al importar.
_session_factory: async_sessionmaker[AsyncSession] | None = None
_read_session_factory: async_sessionmaker[AsyncSession] | None = None


def create_session_factory(
    engine: AsyncEngine,
    read_engine: AsyncEngine | None = None,
) -> async_sessionmaker[AsyncSession]:
    """Crea y registra el session factory global (writer y opcionalmente reader).

    Debe llamarse UNA VEZ durante el startup de la aplicación.
    """
    global _session_factory, _read_session_factory  # noqa: PLW0603
    _session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    if read_engine is not None:
        _read_session_factory = async_sessionmaker(
            bind=read_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        logger.info("Writer and Reader session factories initialized (Aurora multi-endpoint)")
    else:
        _read_session_factory = _session_factory
        logger.info("Session factory initialized (single endpoint / writer)")

    return _session_factory


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Accessor defensivo para el session factory writer — falla rápido si no se inicializó."""
    if _session_factory is None:
        raise RuntimeError(
            "Session factory not initialized. "
            "Call create_session_factory() during app startup."
        )
    return _session_factory


def get_read_session_factory() -> async_sessionmaker[AsyncSession]:
    """Accessor defensivo para el session factory reader (o writer si no hay reader)."""
    if _read_session_factory is None:
        return get_session_factory()
    return _read_session_factory


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency — unit of work (writer) con commit/rollback automático.

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


async def get_read_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency — solo lectura sobre Aurora reader (o writer si no está configurado)."""
    factory = get_read_session_factory()
    async with factory() as session:
        try:
            yield session
        finally:
            await session.close()
