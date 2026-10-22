from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from nexus_backend.auth.domain.entities import User
from nexus_backend.auth.presentation.dependencies import require_admin
from nexus_backend.catalog.application.dtos import (
    CreateVideoGameRequest,
    DeleteVideoGameResponse,
    GenreResponse,
    PlatformResponse,
    UpdateVideoGameRequest,
    VideoGameResponse,
)
from nexus_backend.catalog.application.services import CatalogService
from nexus_backend.catalog.domain.entities import VideoGame, Genre, Platform
from nexus_backend.catalog.infrastructure.repositories import SQLAlchemyVideoGameRepository
from nexus_backend.database import get_db_session

router = APIRouter(prefix="/video-games", tags=["Video Games"])


def _get_catalog_service(session: AsyncSession = Depends(get_db_session)) -> CatalogService:
    repo = SQLAlchemyVideoGameRepository(session)
    return CatalogService(video_game_repo=repo)


def _to_response(game: VideoGame) -> VideoGameResponse:
    return VideoGameResponse(
        id=game.id,
        title=game.title,
        description=game.description,
        price_clp=game.price_clp,
        stock=game.stock,
        image_url=game.image_url,
        platform=PlatformResponse(id=game.platform.id, name=game.platform.name) if game.platform else None,
        genres=[GenreResponse(id=g.id, name=g.name) for g in game.genres],
        created_at=game.created_at if hasattr(game, "created_at") else None,
    )


# ──────────────────────────────────────────────────────────────
# Rutas Públicas (Lectura de Catálogo)
# ──────────────────────────────────────────────────────────────

@router.get("", response_model=list[VideoGameResponse])
async def list_video_games(
    skip: int = 0,
    limit: int = 100,
    service: CatalogService = Depends(_get_catalog_service),
) -> Any:
    """Lista todos los videojuegos disponibles en el catálogo."""
    games = await service.list_video_games(skip=skip, limit=limit)
    return [_to_response(g) for g in games]


@router.get("/{video_game_id}", response_model=VideoGameResponse)
async def get_video_game(
    video_game_id: UUID,
    service: CatalogService = Depends(_get_catalog_service),
) -> Any:
    """Obtiene el detalle de un videojuego específico."""
    game = await service.get_video_game(video_game_id)
    return _to_response(game)


# ──────────────────────────────────────────────────────────────
# Rutas Administrativas Protegidas por RBAC (Cognito Admin)
# ──────────────────────────────────────────────────────────────

@router.post(
    "",
    response_model=VideoGameResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Agregar nuevo videojuego (Solo Admin)",
)
async def create_video_game(
    body: CreateVideoGameRequest,
    service: CatalogService = Depends(_get_catalog_service),
    current_admin: User = Depends(require_admin),
) -> Any:
    """Crea un nuevo videojuego en el catálogo. Requiere rol 'admin'."""
    game = VideoGame(
        title=body.title,
        description=body.description,
        price_clp=body.price_clp,
        stock=body.stock,
        image_url=body.image_url,
        platform=Platform(name=body.platform_name) if body.platform_name else None,
        genres=[Genre(name=g) for g in body.genre_names],
    )
    created_game = await service.create_video_game(game)
    return _to_response(created_game)


@router.put(
    "/{video_game_id}",
    response_model=VideoGameResponse,
    summary="Modificar videojuego existente (Solo Admin)",
)
async def update_video_game(
    video_game_id: UUID,
    body: UpdateVideoGameRequest,
    service: CatalogService = Depends(_get_catalog_service),
    current_admin: User = Depends(require_admin),
) -> Any:
    """Actualiza los datos o stock de un videojuego. Requiere rol 'admin'."""
    updated_game = await service.update_video_game(video_game_id, body)
    return _to_response(updated_game)


@router.delete(
    "/{video_game_id}",
    response_model=DeleteVideoGameResponse,
    summary="Eliminar videojuego del catálogo (Solo Admin)",
)
async def delete_video_game(
    video_game_id: UUID,
    service: CatalogService = Depends(_get_catalog_service),
    current_admin: User = Depends(require_admin),
) -> Any:
    """Elimina un videojuego del catálogo. Requiere rol 'admin'."""
    success = await service.delete_video_game(video_game_id)
    return DeleteVideoGameResponse(
        id=video_game_id,
        success=success,
        message=f"Video game {video_game_id} deleted successfully.",
    )
