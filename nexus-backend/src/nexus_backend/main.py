import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from nexus_backend.config import get_settings

logger = logging.getLogger("nexus_backend")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    logger.info("Starting %s...", settings.APP_NAME)

    from nexus_backend.database import init_db
    await init_db()
    logger.info("Database initialized")

    from nexus_backend.ai_assistant.infrastructure.embeddings import HuggingFaceEmbeddingAdapter
    _adapter = HuggingFaceEmbeddingAdapter()
    await _adapter.embed_text("warmup")
    logger.info("Embedding model loaded and warmed up")

    yield

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
    from nexus_backend.cart.presentation.router import router as cart_router
    from nexus_backend.ai_assistant.presentation.router import router as assistant_router

    api_prefix = "/api/v1"
    application.include_router(auth_router, prefix=api_prefix)
    application.include_router(catalog_router, prefix=api_prefix)
    application.include_router(cart_router, prefix=api_prefix)
    application.include_router(assistant_router, prefix=api_prefix)

    @application.get("/api/v1/health", tags=["Health"])
    async def health_check() -> dict:
        return {"status": "healthy", "service": settings.APP_NAME}

    return application


app = create_app()
