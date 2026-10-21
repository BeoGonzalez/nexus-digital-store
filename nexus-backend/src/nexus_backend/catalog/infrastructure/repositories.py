from uuid import UUID
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from nexus_backend.catalog.domain.entities import VideoGame as VideoGameEntity, Genre as GenreEntity, Platform as PlatformEntity
from nexus_backend.catalog.domain.ports import VideoGameRepository
from nexus_backend.catalog.infrastructure.models import VideoGame as VideoGameModel, Genre as GenreModel, Platform as PlatformModel


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
            image_url=model.image_url,
            platform=PlatformEntity(id=model.platform.id, name=model.platform.name) if model.platform else None,
            embedding=getattr(model, "embedding", []) or [],
            genres=[GenreEntity(id=g.id, name=g.name) for g in model.genres],
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    async def get_by_id(self, video_game_id: UUID) -> VideoGameEntity | None:
        stmt = (
            select(VideoGameModel)
            .where(VideoGameModel.id == video_game_id)
            .options(selectinload(VideoGameModel.genres), selectinload(VideoGameModel.platform))
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

    async def _get_or_create_platform(self, platform_name: str | None) -> PlatformModel | None:
        if not platform_name:
            return None
        clean_name = platform_name.strip()
        if not clean_name:
            return None
        stmt = select(PlatformModel).where(PlatformModel.name == clean_name)
        result = await self._session.execute(stmt)
        platform = result.scalar_one_or_none()
        if not platform:
            platform = PlatformModel(name=clean_name)
            self._session.add(platform)
            await self._session.flush()
        return platform

    async def create(self, video_game: VideoGameEntity) -> VideoGameEntity:
        genre_models = await self._get_or_create_genres([g.name for g in video_game.genres])
        platform_model = await self._get_or_create_platform(video_game.platform.name if video_game.platform else None)

        model = VideoGameModel(
            title=video_game.title,
            description=video_game.description,
            price_clp=video_game.price_clp,
            stock=video_game.stock,
            image_url=video_game.image_url,
            platform=platform_model,
            embedding=video_game.embedding if video_game.embedding else None,
            genres=genre_models,
        )
        self._session.add(model)
        await self._session.flush()
        await self._session.refresh(model, ["genres", "platform"])
        return self._to_entity(model)

    async def list_all(self, skip: int = 0, limit: int = 100) -> list[VideoGameEntity]:
        stmt = (
            select(VideoGameModel)
            .options(selectinload(VideoGameModel.genres), selectinload(VideoGameModel.platform))
            .order_by(VideoGameModel.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return [self._to_entity(m) for m in result.scalars()]

    async def get_without_embedding(self, limit: int = 100) -> list[VideoGameEntity]:
        return await self.list_all(skip=0, limit=limit)

    async def update(self, video_game: VideoGameEntity) -> VideoGameEntity:
        stmt = (
            select(VideoGameModel)
            .where(VideoGameModel.id == video_game.id)
            .options(selectinload(VideoGameModel.genres), selectinload(VideoGameModel.platform))
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if not model:
            raise ValueError(f"Video game {video_game.id} not found")

        model.title = video_game.title
        model.description = video_game.description
        model.price_clp = video_game.price_clp
        model.stock = video_game.stock
        if video_game.image_url is not None:
            model.image_url = video_game.image_url

        if video_game.platform:
            platform_model = await self._get_or_create_platform(video_game.platform.name)
            model.platform = platform_model

        if video_game.genres:
            genre_models = await self._get_or_create_genres([g.name for g in video_game.genres])
            model.genres = genre_models

        await self._session.flush()
        await self._session.refresh(model, ["genres", "platform"])
        return self._to_entity(model)

    async def delete(self, video_game_id: UUID) -> bool:
        from sqlalchemy.exc import IntegrityError
        from nexus_backend.shared.domain.exceptions import BusinessRuleViolationException

        try:
            stmt = delete(VideoGameModel).where(VideoGameModel.id == video_game_id)
            result = await self._session.execute(stmt)
            await self._session.flush()
            rowcount = getattr(result, "rowcount", 0) or 0
            return rowcount > 0
        except IntegrityError as e:
            await self._session.rollback()
            raise BusinessRuleViolationException(
                f"Cannot delete video game {video_game_id} because it is referenced in existing customer orders. Set stock to 0 to deactivate instead."
            ) from e

    async def search_by_vector(self, embedding: list[float], top_k: int = 5) -> list[VideoGameEntity]:
        # Vector search is handled by PineconeVectorStoreAdapter
        return []

    async def update_stock(self, video_game_id: UUID, quantity_change: int) -> bool:
        stmt = (
            update(VideoGameModel)
            .where(VideoGameModel.id == video_game_id, VideoGameModel.stock + quantity_change >= 0)
            .values(stock=VideoGameModel.stock + quantity_change)
        )
        result = await self._session.execute(stmt)
        rowcount = getattr(result, "rowcount", 0) or 0
        return rowcount > 0
