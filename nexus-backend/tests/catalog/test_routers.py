import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock
from uuid import uuid4
from decimal import Decimal

from nexus_backend.catalog.application.services import CatalogService
from nexus_backend.catalog.domain.entities import Product
from nexus_backend.catalog.presentation.router import _get_catalog_service
from nexus_backend.main import app


@pytest.fixture
def mock_catalog_service() -> AsyncMock:
    return AsyncMock(spec=CatalogService)


@pytest.fixture(autouse=True)
def override_dependencies(mock_catalog_service: AsyncMock):
    app.dependency_overrides[_get_catalog_service] = lambda: mock_catalog_service
    yield
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_list_products_endpoint(async_client: AsyncClient, mock_catalog_service: AsyncMock, dummy_product: Product):
    # Arrange
    mock_catalog_service.list_products.return_value = [dummy_product]

    # Act
    response = await async_client.get("/api/v1/products?skip=5&limit=10")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["id"] == str(dummy_product.id)
    assert data["items"][0]["name"] == "RTX 4090"
    mock_catalog_service.list_products.assert_called_once_with(skip=5, limit=10)


@pytest.mark.asyncio
async def test_get_product_endpoint_success(async_client: AsyncClient, mock_catalog_service: AsyncMock, dummy_product: Product):
    # Arrange
    mock_catalog_service.get_product.return_value = dummy_product

    # Act
    response = await async_client.get(f"/api/v1/products/{dummy_product.id}")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(dummy_product.id)
    assert data["name"] == "RTX 4090"
    mock_catalog_service.get_product.assert_called_once_with(dummy_product.id)


@pytest.mark.asyncio
async def test_get_product_endpoint_not_found(async_client: AsyncClient, mock_catalog_service: AsyncMock):
    # Arrange
    mock_catalog_service.get_product.return_value = None
    pid = uuid4()

    # Act
    response = await async_client.get(f"/api/v1/products/{pid}")

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found"
    mock_catalog_service.get_product.assert_called_once_with(pid)


@pytest.mark.asyncio
async def test_create_product_endpoint(async_client: AsyncClient, mock_catalog_service: AsyncMock, dummy_product: Product):
    # Arrange
    mock_catalog_service.create_product.return_value = dummy_product
    payload = {
        "name": "RTX 4090",
        "brand": "NVIDIA",
        "category": "GPU",
        "description": "Flagship graphics card",
        "price": 1599.99,
        "stock": 10,
        "specifications": {"vram": "24GB"},
        "image_url": "http://example.com/rtx4090.png"
    }

    # Act
    response = await async_client.post("/api/v1/products", json=payload)

    # Assert
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == str(dummy_product.id)
    assert data["name"] == "RTX 4090"
    mock_catalog_service.create_product.assert_called_once()
    
    # Verify the argument passed to create_product
    args, _ = mock_catalog_service.create_product.call_args
    product_arg = args[0]
    assert product_arg.name == "RTX 4090"
    assert product_arg.price == Decimal("1599.99")
