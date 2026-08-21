import pytest
from unittest.mock import AsyncMock
from uuid import uuid4

from nexus_backend.catalog.application.services import CatalogService
from nexus_backend.catalog.domain.entities import Product


@pytest.fixture
def catalog_service(mock_product_repo: AsyncMock) -> CatalogService:
    return CatalogService(product_repo=mock_product_repo)


@pytest.mark.asyncio
async def test_list_products_validates_contract(
    catalog_service: CatalogService, mock_product_repo: AsyncMock, dummy_product: Product
):
    # Arrange
    mock_product_repo.list_all.return_value = [dummy_product]

    # Act
    products = await catalog_service.list_products(skip=15, limit=35)

    # Assert - Spying exactly
    mock_product_repo.list_all.assert_called_once_with(skip=15, limit=35)
    assert products == [dummy_product]


@pytest.mark.asyncio
async def test_get_product_success_validates_contract(
    catalog_service: CatalogService, mock_product_repo: AsyncMock, dummy_product: Product
):
    # Arrange
    mock_product_repo.get_by_id.return_value = dummy_product

    # Act
    product = await catalog_service.get_product(dummy_product.id)

    # Assert - Spying exactly
    mock_product_repo.get_by_id.assert_called_once_with(dummy_product.id)
    assert product == dummy_product


@pytest.mark.asyncio
async def test_create_product_validates_contract(
    catalog_service: CatalogService, mock_product_repo: AsyncMock, dummy_product: Product
):
    # Arrange
    mock_product_repo.create.return_value = dummy_product

    # Act
    product = await catalog_service.create_product(dummy_product)

    # Assert - Spying exactly
    mock_product_repo.create.assert_called_once_with(dummy_product)
    assert product == dummy_product


@pytest.mark.asyncio
async def test_search_by_vector_validates_contract(
    catalog_service: CatalogService, mock_product_repo: AsyncMock, dummy_product: Product
):
    # Arrange
    mock_product_repo.search_by_vector.return_value = [dummy_product]
    vector = [0.8] * 384

    # Act
    results = await catalog_service.search_by_vector(vector, top_k=7)

    # Assert - Spying exactly
    mock_product_repo.search_by_vector.assert_called_once_with(vector, 7)
    assert results == [dummy_product]


@pytest.mark.asyncio
async def test_sync_embeddings_mutates_state_and_validates_contract(
    catalog_service: CatalogService, mock_product_repo: AsyncMock, dummy_product: Product
):
    # Arrange
    # Ensure initially empty
    dummy_product.embedding = []
    dummy_product.name = "Test Product"
    dummy_product.brand = "BrandX"
    dummy_product.category = "CategoryY"
    dummy_product.description = "DescZ"

    mock_product_repo.get_without_embedding.return_value = [dummy_product]
    
    # We capture the exact object passed to update
    mock_product_repo.update.side_effect = lambda p: p

    async def mock_embed_fn(text: str) -> list[float]:
        # We also validate that the embed function gets the EXACT expected string payload
        assert text == "Test Product BrandX CategoryY DescZ"
        return [0.99] * 384

    # Act
    count = await catalog_service.sync_embeddings(mock_embed_fn)

    # Assert - State Mutations
    # 1. Verify entity state mutated correctly BEFORE saving
    assert count == 1
    assert dummy_product.embedding == [0.99] * 384, "The service must mutate the Product's embedding list"

    # 2. Spying Contract
    mock_product_repo.get_without_embedding.assert_called_once_with(limit=100)
    
    # Verify the EXACT mutated object was passed down to the Repo
    mock_product_repo.update.assert_called_once()
    call_args = mock_product_repo.update.call_args[0]
    updated_product: Product = call_args[0]
    
    assert updated_product.id == dummy_product.id
    assert updated_product.embedding == [0.99] * 384


@pytest.mark.asyncio
async def test_sync_embeddings_handles_empty_queue(
    catalog_service: CatalogService, mock_product_repo: AsyncMock
):
    # Arrange
    mock_product_repo.get_without_embedding.return_value = []

    async def mock_embed_fn(text: str) -> list[float]:
        return [0.0] * 384

    # Act
    count = await catalog_service.sync_embeddings(mock_embed_fn)

    # Assert
    assert count == 0
    mock_product_repo.get_without_embedding.assert_called_once_with(limit=100)
    mock_product_repo.update.assert_not_called()
