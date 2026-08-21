import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

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

    from nexus_backend.database import init_db
    await init_db()
    logger.info("Database initialized")

    from nexus_backend.ai_assistant.infrastructure.embeddings import HuggingFaceEmbeddingAdapter
    _adapter = HuggingFaceEmbeddingAdapter(model_name=settings.EMBEDDING_MODEL_NAME)
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
