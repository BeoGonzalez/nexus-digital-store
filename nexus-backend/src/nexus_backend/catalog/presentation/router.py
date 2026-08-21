from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from nexus_backend.catalog.application.dtos import (
    ProductCreateRequest,
    ProductListResponse,
    ProductResponse,
)
from nexus_backend.catalog.application.services import CatalogService
from nexus_backend.catalog.domain.entities import Product
from nexus_backend.catalog.infrastructure.repositories import SQLAlchemyProductRepository
from nexus_backend.database import get_db_session

router = APIRouter(prefix="/products", tags=["Catalog"])


def _get_catalog_service(session: AsyncSession = Depends(get_db_session)) -> CatalogService:
    return CatalogService(product_repo=SQLAlchemyProductRepository(session))


@router.get("", response_model=ProductListResponse)
async def list_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    service: CatalogService = Depends(_get_catalog_service),
) -> ProductListResponse:
    products = await service.list_products(skip=skip, limit=limit)
    return ProductListResponse(
        items=[_to_response(p) for p in products],
        total=len(products),
    )


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: UUID,
    service: CatalogService = Depends(_get_catalog_service),
) -> ProductResponse:
    product = await service.get_product(product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return _to_response(product)


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    body: ProductCreateRequest,
    service: CatalogService = Depends(_get_catalog_service),
) -> ProductResponse:
    product = Product(
        name=body.name,
        brand=body.brand,
        category=body.category,
        description=body.description,
        price=body.price,
        stock=body.stock,
        specifications=body.specifications,
        image_url=body.image_url,
    )
    created = await service.create_product(product)
    return _to_response(created)


def _to_response(p: Product) -> ProductResponse:
    return ProductResponse(
        id=str(p.id),
        name=p.name,
        brand=p.brand,
        category=p.category,
        description=p.description,
        price=p.price,
        stock=p.stock,
        specifications=p.specifications,
        image_url=p.image_url,
    )
