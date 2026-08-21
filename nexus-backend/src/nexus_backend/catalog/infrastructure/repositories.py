from decimal import Decimal
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from nexus_backend.catalog.domain.entities import Product
from nexus_backend.catalog.infrastructure.models import ProductModel


class SQLAlchemyProductRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_all(self, skip: int = 0, limit: int = 50) -> list[Product]:
        result = await self._session.execute(
            select(ProductModel).offset(skip).limit(limit).order_by(ProductModel.created_at.desc())
        )
        return [self._to_entity(m) for m in result.scalars().all()]

    async def get_by_id(self, product_id: UUID) -> Product | None:
        result = await self._session.execute(
            select(ProductModel).where(ProductModel.id == product_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def create(self, product: Product) -> Product:
        model = ProductModel(
            id=product.id,
            name=product.name,
            brand=product.brand,
            category=product.category,
            description=product.description,
            price=float(product.price),
            stock=product.stock,
            specifications=product.specifications,
            image_url=product.image_url,
            embedding=product.embedding,
        )
        self._session.add(model)
        await self._session.flush()
        return self._to_entity(model)

    async def update(self, product: Product) -> Product:
        result = await self._session.execute(
            select(ProductModel).where(ProductModel.id == product.id)
        )
        model = result.scalar_one()
        model.name = product.name
        model.brand = product.brand
        model.category = product.category
        model.description = product.description
        model.price = float(product.price)
        model.stock = product.stock
        model.specifications = product.specifications
        model.image_url = product.image_url
        model.embedding = product.embedding
        await self._session.flush()
        return self._to_entity(model)

    async def update_stock(self, product_id: UUID, quantity_delta: int) -> bool:
        result = await self._session.execute(
            update(ProductModel)
            .where(
                ProductModel.id == product_id,
                ProductModel.stock + quantity_delta >= 0,
            )
            .values(stock=ProductModel.stock + quantity_delta)
        )
        return result.rowcount > 0

    async def search_by_vector(self, embedding: list[float], top_k: int = 5) -> list[Product]:
        result = await self._session.execute(
            select(ProductModel)
            .where(ProductModel.embedding.isnot(None))
            .order_by(ProductModel.embedding.cosine_distance(embedding))
            .limit(top_k)
        )
        return [self._to_entity(m) for m in result.scalars().all()]

    async def get_without_embedding(self, limit: int = 100) -> list[Product]:
        result = await self._session.execute(
            select(ProductModel)
            .where(ProductModel.embedding.is_(None))
            .limit(limit)
        )
        return [self._to_entity(m) for m in result.scalars().all()]

    @staticmethod
    def _to_entity(model: ProductModel) -> Product:
        return Product(
            id=model.id,
            name=model.name,
            brand=model.brand,
            category=model.category,
            description=model.description,
            price=Decimal(str(model.price)),
            stock=model.stock,
            specifications=model.specifications or {},
            image_url=model.image_url,
            embedding=list(model.embedding) if model.embedding is not None else None,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
