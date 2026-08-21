import logging
from uuid import UUID

from nexus_backend.catalog.domain.entities import Product
from nexus_backend.catalog.domain.ports import ProductRepository

logger = logging.getLogger(__name__)


class CatalogService:
    def __init__(self, product_repo: ProductRepository) -> None:
        self._product_repo = product_repo

    async def list_products(self, skip: int = 0, limit: int = 50) -> list[Product]:
        return await self._product_repo.list_all(skip=skip, limit=limit)

    async def get_product(self, product_id: UUID) -> Product | None:
        return await self._product_repo.get_by_id(product_id)

    async def create_product(self, product: Product) -> Product:
        return await self._product_repo.create(product)

    async def search_by_vector(self, embedding: list[float], top_k: int = 5) -> list[Product]:
        return await self._product_repo.search_by_vector(embedding, top_k)

    async def sync_embeddings(self, embed_fn: callable) -> int:
        products = await self._product_repo.get_without_embedding(limit=100)
        count = 0
        for product in products:
            text = f"{product.name} {product.brand} {product.category} {product.description}"
            product.embedding = await embed_fn(text)
            await self._product_repo.update(product)
            count += 1
        logger.info("Synced embeddings for %d products", count)
        return count
