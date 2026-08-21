import asyncio
from functools import lru_cache

from langchain_huggingface import HuggingFaceEmbeddings

from nexus_backend.config import get_settings


class HuggingFaceEmbeddingAdapter:
    def __init__(self) -> None:
        settings = get_settings()
        self._model = _get_embedding_model(settings.EMBEDDING_MODEL_NAME)

    async def embed_text(self, text: str) -> list[float]:
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(None, self._model.embed_query, text)
        return result


@lru_cache(maxsize=1)
def _get_embedding_model(model_name: str) -> HuggingFaceEmbeddings:
    return HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )
