import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from nexus_backend.shared.domain.exceptions import (
    BusinessRuleViolationException,
    ResourceNotFoundException,
    UnauthorizedException,
)

from nexus_backend.config import get_settings

logger = logging.getLogger("nexus_backend")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    logger.info("Starting %s...", settings.APP_NAME)

    # ── LangSmith / LangChain Tracing V2 bootstrap ──
    import os
    if settings.LANGSMITH_API_KEY:
        os.environ["LANGSMITH_API_KEY"] = settings.LANGSMITH_API_KEY
        os.environ["LANGCHAIN_API_KEY"] = settings.LANGSMITH_API_KEY
        os.environ["LANGSMITH_PROJECT"] = settings.LANGSMITH_PROJECT
        os.environ["LANGCHAIN_PROJECT"] = settings.LANGSMITH_PROJECT
        os.environ["LANGSMITH_TRACING"] = "true"
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
        logger.info("LangSmith & LangChain Tracing V2 connected for project '%s'", settings.LANGSMITH_PROJECT)

    # ── Database bootstrap (Amazon Aurora PostgreSQL) ──
    from nexus_backend.database import (
        DatabaseConnectionConfig,
        create_db_engine,
        create_session_factory,
        init_db,
        shutdown_db,
    )

    db_config = DatabaseConnectionConfig(
        database_url=settings.DATABASE_URL,
        echo=settings.DEBUG,
        ssl=settings.DB_SSL,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
    )
    engine = create_db_engine(db_config)

    read_engine = None
    if settings.DATABASE_READ_URL:
        read_config = DatabaseConnectionConfig(
            database_url=settings.DATABASE_READ_URL,
            echo=settings.DEBUG,
            ssl=settings.DB_SSL,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
        )
        read_engine = create_db_engine(read_config)

    session_factory = create_session_factory(engine, read_engine=read_engine)
    await init_db(engine, session_factory)
    logger.info("Database initialized successfully")

    # ── Embedding model warmup ──
    try:
        from nexus_backend.ai_assistant.infrastructure.embeddings import (
            HuggingFaceEmbeddingAdapter,
        )
        _adapter = HuggingFaceEmbeddingAdapter(
            model_name=settings.EMBEDDING_MODEL_NAME,
        )
        await _adapter.embed_text("warmup")
        logger.info("Embedding model loaded and warmed up")
    except Exception as exc:
        logger.warning("Embedding model warmup skipped or deferred: %s", exc)

    yield

    # ── Graceful shutdown ──
    if read_engine is not None:
        await shutdown_db(read_engine)
    await shutdown_db(engine)
    logger.info("Shutting down %s...", settings.APP_NAME)


def create_app() -> FastAPI:
    settings = get_settings()

    application = FastAPI(
        title=settings.APP_NAME,
        version="0.1.0",
        description="Backend API for Nexus Digital Store — Premium Gamer Hardware E-Commerce",
        lifespan=lifespan,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from nexus_backend.auth.presentation.router import router as auth_router
    from nexus_backend.catalog.presentation.router import router as catalog_router
    from nexus_backend.orders.presentation.router import router as orders_router

    api_prefix = "/api/v1"
    application.include_router(auth_router, prefix=api_prefix)
    application.include_router(catalog_router, prefix=api_prefix)
    application.include_router(orders_router, prefix=api_prefix)

    try:
        from nexus_backend.ai_assistant.presentation.router import router as assistant_router
        application.include_router(assistant_router, prefix=api_prefix)
    except Exception as e:
        logger.warning(f"AI Assistant router could not be loaded: {e}")

    # ── Health checks ──
    # Liveness check: ALB / ECS ping sin tocar la base de datos
    @application.get("/api/health", tags=["Health"])
    @application.get("/api/v1/health", tags=["Health"])
    async def liveness_health_check() -> dict:
        return {"status": "healthy", "service": settings.APP_NAME}

    # Readiness check: verifica conectividad real contra Amazon Aurora
    @application.get("/api/health/ready", tags=["Health"])
    @application.get("/api/v1/health/ready", tags=["Health"])
    async def readiness_health_check() -> JSONResponse:
        from nexus_backend.database import get_session_factory
        try:
            factory = get_session_factory()
            async with factory() as session:
                await session.execute(text("SELECT 1"))
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={"status": "ready", "database": "connected", "service": settings.APP_NAME},
            )
        except Exception as exc:
            logger.error("Readiness check failed against Aurora: %s", exc)
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={"status": "not_ready", "database": str(exc), "service": settings.APP_NAME},
            )

    @application.exception_handler(ResourceNotFoundException)
    async def not_found_handler(request: Request, exc: ResourceNotFoundException):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": str(exc)},
        )

    @application.exception_handler(BusinessRuleViolationException)
    async def business_rule_handler(request: Request, exc: BusinessRuleViolationException):
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": str(exc)},
        )

    @application.exception_handler(UnauthorizedException)
    async def unauthorized_handler(request: Request, exc: UnauthorizedException):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": str(exc)},
        )

    return application


app = create_app()
