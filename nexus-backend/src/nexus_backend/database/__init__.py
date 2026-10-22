"""Database package — public API re-exports.

Todos los consumidores existentes que hacen:
    from nexus_backend.database import get_db_session
seguirán funcionando sin cambios gracias a estos re-exports.
"""

from nexus_backend.database.engine import (
    AuroraConnectionConfig,
    DatabaseConnectionConfig,
    create_db_engine,
)
from nexus_backend.database.session import (
    create_session_factory,
    get_db_session,
    get_read_db_session,
    get_read_session_factory,
    get_session_factory,
)
from nexus_backend.database.lifecycle import init_db, shutdown_db

__all__ = [
    "AuroraConnectionConfig",
    "DatabaseConnectionConfig",
    "create_db_engine",
    "create_session_factory",
    "get_db_session",
    "get_read_db_session",
    "get_read_session_factory",
    "get_session_factory",
    "init_db",
    "shutdown_db",
]
