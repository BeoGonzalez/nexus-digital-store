"""Pruebas unitarias para CatalogService con aserciones estrictas de mutación y contratos."""

from unittest.mock import AsyncMock, call
from uuid import UUID, uuid4
import pytest

from nexus_backend.catalog.application.dtos import UpdateVideoGameRequest
from nexus_backend.catalog.application.services import CatalogService
from nexus_backend.catalog.domain.entities import Genre, VideoGame
from nexus_backend.shared.domain.exceptions import ResourceNotFoundException


@pytest.fixture
def catalog_service(mock_video_game_repo: AsyncMock) -> CatalogService:
    return CatalogService(video_game_repo=mock_video_game_repo)


class TestCatalogService:
    """Suite de validación de lógica de negocio para CatalogService."""

    @pytest.mark.asyncio
    async def test_list_video_games_passes_pagination_arguments_strictly(
        self,
        catalog_service: CatalogService,
        mock_video_game_repo: AsyncMock,
        dummy_video_game: VideoGame,
    ) -> None:
        # Arrange
        mock_video_game_repo.list_all.return_value = [dummy_video_game]

        # Act
        result = await catalog_service.list_video_games(skip=10, limit=25)

        # Assert - Contrato estricto
        mock_video_game_repo.list_all.assert_called_once_with(skip=10, limit=25)
        assert len(result) == 1
        assert result[0] == dummy_video_game

    @pytest.mark.asyncio
    async def test_get_video_game_happy_path_returns_game(
        self,
        catalog_service: CatalogService,
        mock_video_game_repo: AsyncMock,
        dummy_video_game: VideoGame,
    ) -> None:
        # Arrange
        mock_video_game_repo.get_by_id.return_value = dummy_video_game

        # Act
        result = await catalog_service.get_video_game(dummy_video_game.id)

        # Assert
        mock_video_game_repo.get_by_id.assert_called_once_with(dummy_video_game.id)
        assert result == dummy_video_game

    @pytest.mark.asyncio
    async def test_get_video_game_not_found_raises_domain_exception(
        self,
        catalog_service: CatalogService,
        mock_video_game_repo: AsyncMock,
    ) -> None:
        # Arrange
        missing_id = uuid4()
        mock_video_game_repo.get_by_id.return_value = None

        # Act & Assert
        # Regla de negocio: La búsqueda de un juego inexistente debe lanzar ResourceNotFoundException
        with pytest.raises(ResourceNotFoundException) as exc_info:
            await catalog_service.get_video_game(missing_id)

        assert str(missing_id) in str(exc_info.value)
        mock_video_game_repo.get_by_id.assert_called_once_with(missing_id)

    @pytest.mark.asyncio
    async def test_create_video_game_delegates_to_repo(
        self,
        catalog_service: CatalogService,
        mock_video_game_repo: AsyncMock,
        dummy_video_game: VideoGame,
    ) -> None:
        # Arrange
        mock_video_game_repo.create.return_value = dummy_video_game

        # Act
        result = await catalog_service.create_video_game(dummy_video_game)

        # Assert
        mock_video_game_repo.create.assert_called_once_with(dummy_video_game)
        assert result == dummy_video_game

    @pytest.mark.asyncio
    async def test_update_video_game_mutates_state_and_persists(
        self,
        catalog_service: CatalogService,
        mock_video_game_repo: AsyncMock,
        dummy_video_game: VideoGame,
    ) -> None:
        # Arrange
        # Partimos con el juego existente
        mock_video_game_repo.get_by_id.return_value = dummy_video_game
        # Repo update devuelve la entidad actualizada
        mock_video_game_repo.update.side_effect = lambda g: g

        update_request = UpdateVideoGameRequest(
            title="Elden Ring: Shadow of the Erdtree",
            price_clp=34990,
            stock=150,
            genre_names=["Soulslike", "Action"],
        )

        # Act
        result = await catalog_service.update_video_game(dummy_video_game.id, update_request)

        # Assert - Verificación de mutación de estado ANTES y DURANTE el update
        mock_video_game_repo.get_by_id.assert_called_once_with(dummy_video_game.id)
        mock_video_game_repo.update.assert_called_once_with(dummy_video_game)

        # Verificamos que los atributos del objeto mutaron exactamente según el request
        assert dummy_video_game.title == "Elden Ring: Shadow of the Erdtree"
        assert dummy_video_game.price_clp == 34990
        assert dummy_video_game.stock == 150
        assert len(dummy_video_game.genres) == 2
        assert [g.name for g in dummy_video_game.genres] == ["Soulslike", "Action"]
        # Y que la descripción no mutó porque venía None en el request
        assert dummy_video_game.description == "Epic fantasy action RPG"
        assert result == dummy_video_game

    @pytest.mark.asyncio
    async def test_update_video_game_nonexistent_raises_not_found(
        self,
        catalog_service: CatalogService,
        mock_video_game_repo: AsyncMock,
    ) -> None:
        # Arrange
        missing_id = uuid4()
        mock_video_game_repo.get_by_id.return_value = None
        update_request = UpdateVideoGameRequest(title="Ghost Game")

        # Act & Assert
        with pytest.raises(ResourceNotFoundException):
            await catalog_service.update_video_game(missing_id, update_request)

        # Contrato: Si no existe, nunca debe invocar repo.update
        mock_video_game_repo.update.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_video_game_happy_path_checks_existence_and_deletes(
        self,
        catalog_service: CatalogService,
        mock_video_game_repo: AsyncMock,
        dummy_video_game: VideoGame,
    ) -> None:
        # Arrange
        mock_video_game_repo.get_by_id.return_value = dummy_video_game
        mock_video_game_repo.delete.return_value = True

        # Act
        success = await catalog_service.delete_video_game(dummy_video_game.id)

        # Assert
        # 1. Verifica existencia primero
        mock_video_game_repo.get_by_id.assert_called_once_with(dummy_video_game.id)
        # 2. Ejecuta eliminación con ID exacto
        mock_video_game_repo.delete.assert_called_once_with(dummy_video_game.id)
        assert success is True

    @pytest.mark.asyncio
    async def test_delete_video_game_nonexistent_raises_not_found(
        self,
        catalog_service: CatalogService,
        mock_video_game_repo: AsyncMock,
    ) -> None:
        # Arrange
        missing_id = uuid4()
        mock_video_game_repo.get_by_id.return_value = None

        # Act & Assert
        with pytest.raises(ResourceNotFoundException):
            await catalog_service.delete_video_game(missing_id)

        # Contrato: Si no existe, delete nunca debe ejecutarse
        mock_video_game_repo.delete.assert_not_called()

    @pytest.mark.asyncio
    async def test_sync_embeddings_mutates_state_and_calls_update(
        self,
        catalog_service: CatalogService,
        mock_video_game_repo: AsyncMock,
        dummy_video_game: VideoGame,
    ) -> None:
        # Arrange
        dummy_video_game.embedding = []
        dummy_video_game.title = "Zelda"
        dummy_video_game.description = "Adventure game"
        dummy_video_game.genres = [Genre(name="Action"), Genre(name="Adventure")]
        mock_video_game_repo.get_without_embedding.return_value = [dummy_video_game]

        received_texts: list[str] = []

        async def mock_embed_fn(text: str) -> list[float]:
            received_texts.append(text)
            return [0.777] * 384

        # Act
        updated_count = await catalog_service.sync_embeddings(mock_embed_fn)

        # Assert
        # 1. Validar el formato del texto generado para el modelo semántico
        assert len(received_texts) == 1
        assert received_texts[0] == "Zelda Action, Adventure Adventure game"

        # 2. Validar que la mutación se aplicó en el objeto del dominio
        assert dummy_video_game.embedding == [0.777] * 384
        assert updated_count == 1
        mock_video_game_repo.update.assert_called_once_with(dummy_video_game)

    @pytest.mark.asyncio
    async def test_search_by_vector_strict_args(
        self,
        catalog_service: CatalogService,
        mock_video_game_repo: AsyncMock,
        dummy_video_game: VideoGame,
    ) -> None:
        # Arrange
        test_vector = [0.123] * 384
        mock_video_game_repo.search_by_vector.return_value = [dummy_video_game]

        # Act
        result = await catalog_service.search_by_vector(test_vector, top_k=3)

        # Assert
        mock_video_game_repo.search_by_vector.assert_called_once_with(test_vector, top_k=3)
        assert result == [dummy_video_game]
