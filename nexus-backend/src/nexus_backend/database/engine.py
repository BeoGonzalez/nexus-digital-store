"""Engine factory — construye el AsyncEngine bajo demanda.

Principio: ningún import de este módulo produce side-effects.
El engine se crea SOLO cuando se invoca la factory explícitamente.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.pool import NullPool

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class NeonConnectionConfig:
    """Parámetros de conexión específicos de Neon Serverless.

    Encapsula la decisión de infraestructura en un Value Object
    inmutable, separando la política de conexión del mecanismo
    de creación del engine.

    Si mañana se soporta otro proveedor (Aurora, Supabase), se crea
    una nueva config sin modificar ``create_db_engine`` → Open/Closed.
    """

    database_url: str
    echo: bool = False
    use_neon_pooler: bool = False

    @property
    def normalized_url(self) -> str:
        """Normaliza la URL asegurando el dialecto postgresql+asyncpg y eliminando query params incompatibles."""
        import urllib.parse

        url = self.database_url.strip()
        if url.startswith("postgres://"):
            url = "postgresql+asyncpg://" + url[len("postgres://"):]
        elif url.startswith("postgresql://"):
            url = "postgresql+asyncpg://" + url[len("postgresql://"):]

        parsed = urllib.parse.urlparse(url)
        # Si es neon.tech o contiene query params como sslmode, limpiamos la query string ya que asyncpg
        # gestiona ssl y configs a través de connect_args
        if "sslmode" in parsed.query or "neon.tech" in parsed.netloc:
            return urllib.parse.urlunparse(parsed._replace(query=""))
        return url

    @property
    def is_pooler(self) -> bool:
        return self.use_neon_pooler or "-pooler" in self.database_url

    @property
    def pool_class(self) -> type:
        """NullPool para Neon serverless (sin pool local).

        Neon suspende el compute a cero; un pool persistente dejaría
        conexiones huérfanas contra un endpoint dormido.
        """
        return NullPool

    @property
    def connect_args(self) -> dict[str, object]:
        """Args de conexión TCP para asyncpg.

        • ssl='require': Neon rechaza conexiones sin TLS.
        • prepared_statement_cache_size=0: el pooler de Neon (pgbouncer
          en modo transaction) no soporta named prepared statements.
        """
        args: dict[str, object] = {}

        if self._is_neon_url:
            args["ssl"] = "require"

        if self.is_pooler:
            args["prepared_statement_cache_size"] = 0

        return args

    @property
    def _is_neon_url(self) -> bool:
        return "neon.tech" in self.database_url


def create_db_engine(config: NeonConnectionConfig) -> AsyncEngine:
    """Factory pura que crea un AsyncEngine a partir de config inyectada.

    No lee settings globales. No produce side-effects al importar.
    El llamador es responsable de gestionar el ciclo de vida del engine.
    """
    engine = create_async_engine(
        config.normalized_url,
        echo=config.echo,
        poolclass=config.pool_class,
        connect_args=config.connect_args,
    )
    logger.info(
        "Database engine created (pool=%s, is_pooler=%s)",
        config.pool_class.__name__,
        config.is_pooler,
    )
    return engine
