"""Engine factory — construye el AsyncEngine bajo demanda para Amazon Aurora PostgreSQL.

Principio: ningún import de este módulo produce side-effects.
El engine se crea SOLO cuando se invoca la factory explícitamente.
"""

from __future__ import annotations

import logging
import urllib.parse
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class DatabaseConnectionConfig:
    """Parámetros de conexión para Amazon Aurora PostgreSQL."""

    database_url: str
    echo: bool = False
    ssl: bool = False
    pool_size: int = 10
    max_overflow: int = 5
    pool_recycle: int = 1800
    pool_pre_ping: bool = True

    @property
    def normalized_url(self) -> str:
        """Normaliza la URL asegurando el dialecto postgresql+asyncpg y eliminando query params incompatibles."""
        url = self.database_url.strip()
        if url.startswith("postgres://"):
            url = "postgresql+asyncpg://" + url[len("postgres://"):]
        elif url.startswith("postgresql://"):
            url = "postgresql+asyncpg://" + url[len("postgresql://"):]

        parsed = urllib.parse.urlparse(url)
        # asyncpg no tolera parámetros como sslmode, channel_binding o endpoint en el query string
        if parsed.query:
            params_to_strip = {"sslmode", "channel_binding", "endpoint", "ssl"}
            query_pairs = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
            filtered_pairs = [pair for pair in query_pairs if pair[0].lower() not in params_to_strip]
            new_query = urllib.parse.urlencode(filtered_pairs)
            return urllib.parse.urlunparse(parsed._replace(query=new_query))
        return url

    @property
    def connect_args(self) -> dict[str, object]:
        """Args de conexión TCP para asyncpg."""
        args: dict[str, object] = {}
        if self.ssl:
            args["ssl"] = "require"
        return args


# Alias para compatibilidad con Aurora
AuroraConnectionConfig = DatabaseConnectionConfig


def create_db_engine(config: DatabaseConnectionConfig) -> AsyncEngine:
    """Factory pura que crea un AsyncEngine a partir de la configuración inyectada.

    No lee settings globales. No produce side-effects al importar.
    """
    engine = create_async_engine(
        config.normalized_url,
        echo=config.echo,
        pool_size=config.pool_size,
        max_overflow=config.max_overflow,
        pool_recycle=config.pool_recycle,
        pool_pre_ping=config.pool_pre_ping,
        connect_args=config.connect_args,
    )
    logger.info(
        "Database engine created (pool_size=%d, max_overflow=%d, ssl=%s)",
        config.pool_size,
        config.max_overflow,
        config.ssl,
    )
    return engine
