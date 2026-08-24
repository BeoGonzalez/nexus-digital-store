import logging
from typing import Awaitable, Callable
from uuid import UUID

from nexus_backend.catalog.application.dtos import UpdateVideoGameRequest
from nexus_backend.catalog.domain.entities import VideoGame, Genre
from nexus_backend.catalog.domain.ports import VideoGameRepository
from nexus_backend.shared.domain.exceptions import ResourceNotFoundException

logger = logging.getLogger(__name__)


class CatalogService:
    def __init__(self, video_game_repo: VideoGameRepository) -> None:
        self._repo = video_game_repo

    async def list_video_games(self, skip: int = 0, limit: int = 100) -> list[VideoGame]:
        return await self._repo.list_all(skip=skip, limit=limit)

    async def get_video_game(self, video_game_id: UUID) -> VideoGame:
        game = await self._repo.get_by_id(video_game_id)
        if not game:
            raise ResourceNotFoundException(f"Video game with ID {video_game_id} not found")
        return game

    async def create_video_game(self, video_game: VideoGame) -> VideoGame:
        return await self._repo.create(video_game)

    async def update_video_game(
        self,
        video_game_id: UUID,
        request: UpdateVideoGameRequest,
    ) -> VideoGame:
        game = await self.get_video_game(video_game_id)

        if request.title is not None:
            game.title = request.title
        if request.description is not None:
            game.description = request.description
        if request.price_clp is not None:
            game.price_clp = request.price_clp
        if request.stock is not None:
            game.stock = request.stock
        if request.genre_names is not None:
            game.genres = [Genre(name=name) for name in request.genre_names]

        return await self._repo.update(game)

    async def delete_video_game(self, video_game_id: UUID) -> bool:
        # Verifica existencia primero
        await self.get_video_game(video_game_id)
        return await self._repo.delete(video_game_id)

    async def search_by_vector(self, embedding: list[float], top_k: int = 5) -> list[VideoGame]:
        return await self._repo.search_by_vector(embedding, top_k=top_k)

    async def sync_embeddings(self, embed_fn: Callable[[str], Awaitable[list[float]]]) -> int:
        games = await self._repo.get_without_embedding(limit=100)
        updated_count = 0

        for game in games:
            genres_str = ", ".join(g.name for g in game.genres)
            text_to_embed = f"{game.title} {genres_str} {game.description}"
            
            embedding = await embed_fn(text_to_embed)
            game.embedding = embedding
            await self._repo.update(game)
            updated_count += 1
            logger.info("Generated embedding for video game %s", game.id)

        return updated_count
