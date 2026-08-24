from uuid import UUID
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from nexus_backend.catalog.domain.entities import VideoGame as VideoGameEntity, Genre as GenreEntity
from nexus_backend.catalog.domain.ports import VideoGameRepository
from nexus_backend.catalog.infrastructure.models import VideoGame as VideoGameModel, Genre as GenreModel


class SQLAlchemyVideoGameRepository(VideoGameRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _to_entity(self, model: VideoGameModel) -> VideoGameEntity:
        return VideoGameEntity(
            id=model.id,
            title=model.title,
            description=model.description,
            price_clp=model.price_clp,
            stock=model.stock,
            embedding=model.embedding if model.embedding is not None else [],
            genres=[GenreEntity(id=g.id, name=g.name) for g in model.genres],
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    async def get_by_id(self, video_game_id: UUID) -> VideoGameEntity | None:
        stmt = (
            select(VideoGameModel)
            .where(VideoGameModel.id == video_game_id)
            .options(selectinload(VideoGameModel.genres))
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def _get_or_create_genres(self, genre_names: list[str]) -> list[GenreModel]:
        genres: list[GenreModel] = []
        for name in genre_names:
            clean_name = name.strip()
            if not clean_name:
                continue
            stmt = select(GenreModel).where(GenreModel.name == clean_name)
            result = await self._session.execute(stmt)
            genre = result.scalar_one_or_none()
            if not genre:
                genre = GenreModel(name=clean_name)
                self._session.add(genre)
                await self._session.flush()
            genres.append(genre)
        return genres

    async def create(self, video_game: VideoGameEntity) -> VideoGameEntity:
        genre_models = await self._get_or_create_genres([g.name for g in video_game.genres])

        model = VideoGameModel(
            title=video_game.title,
            description=video_game.description,
            price_clp=video_game.price_clp,
            stock=video_game.stock,
            embedding=video_game.embedding if video_game.embedding else None,
            genres=genre_models,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model, ["genres"])
        return self._to_entity(model)

    async def list_all(self, skip: int = 0, limit: int = 100) -> list[VideoGameEntity]:
        stmt = (
            select(VideoGameModel)
            .options(selectinload(VideoGameModel.genres))
            .order_by(VideoGameModel.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars()]

    async def get_without_embedding(self, limit: int = 100) -> list[VideoGameEntity]:
        stmt = (
            select(VideoGameModel)
            .where(VideoGameModel.embedding == None)
            .options(selectinload(VideoGameModel.genres))
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars()]

    async def update(self, video_game: VideoGameEntity) -> VideoGameEntity:
        stmt = (
            select(VideoGameModel)
            .where(VideoGameModel.id == video_game.id)
            .options(selectinload(VideoGameModel.genres))
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            raise ValueError(f"Video game {video_game.id} not found")

        model.title = video_game.title
        model.description = video_game.description
        model.price_clp = video_game.price_clp
        model.stock = video_game.stock
        if video_game.embedding:
            model.embedding = video_game.embedding

        if video_game.genres:
            genre_models = await self._get_or_create_genres([g.name for g in video_game.genres])
            model.genres = genre_models

        await self._session.flush()
        await self._session.refresh(model, ["genres"])
        return self._to_entity(model)

    async def delete(self, video_game_id: UUID) -> bool:
        from sqlalchemy.exc import IntegrityError
        from nexus_backend.shared.domain.exceptions import BusinessRuleViolationException

        try:
            stmt = delete(VideoGameModel).where(VideoGameModel.id == video_game_id)
            result = await self._session.execute(stmt)
            await self._session.flush()
            return (result.rowcount or 0) > 0
        except IntegrityError as e:
            await self._session.rollback()
            raise BusinessRuleViolationException(
                f"Cannot delete video game {video_game_id} because it is referenced in existing customer orders. Set stock to 0 to deactivate instead."
            ) from e

    async def search_by_vector(self, embedding: list[float], top_k: int = 5) -> list[VideoGameEntity]:
        stmt = (
            select(VideoGameModel)
            .where(VideoGameModel.embedding != None)
            .options(selectinload(VideoGameModel.genres))
            .order_by(VideoGameModel.embedding.cosine_distance(embedding))
            .limit(top_k)
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars()]

    async def update_stock(self, video_game_id: UUID, quantity_change: int) -> bool:
        stmt = (
            update(VideoGameModel)
            .where(VideoGameModel.id == video_game_id, VideoGameModel.stock + quantity_change >= 0)
            .values(stock=VideoGameModel.stock + quantity_change)
        )
        result = await self._session.execute(stmt)
        return (result.rowcount or 0) > 0
