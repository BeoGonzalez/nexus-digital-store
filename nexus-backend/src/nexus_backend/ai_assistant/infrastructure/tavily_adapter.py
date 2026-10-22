"""Adaptador para búsqueda de noticias de videojuegos en tiempo real mediante la API de Tavily."""

import logging
from typing import Any

import httpx

from nexus_backend.ai_assistant.domain.ports import GamingNewsPort
from nexus_backend.config import get_settings

logger = logging.getLogger(__name__)


class TavilyNewsAdapter(GamingNewsPort):
    """Cliente asíncrono para la API de Tavily enfocado en noticias y novedades gamer."""

    def __init__(
        self,
        api_key: str | None = None,
        max_results: int | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        settings = get_settings()
        self._api_key = api_key if api_key is not None else settings.TAVILY_API_KEY
        self._max_results = max_results or settings.TAVILY_MAX_RESULTS
        self._client = client
        self._endpoint = "https://api.tavily.com/search"

    async def _fetch_with_client(self, client: httpx.AsyncClient, payload: dict[str, Any]) -> str:
        response = await client.post(self._endpoint, json=payload)
        if response.status_code != 200:
            logger.debug("Tavily API retornó código HTTP %d: %s", response.status_code, response.text[:120])
            return "Sin noticias recientes disponibles."

        data = response.json()
        results = data.get("results", [])
        direct_answer = data.get("answer", "")

        output_parts: list[str] = []
        if direct_answer:
            output_parts.append(f"Resumen de noticias: {direct_answer.strip()}")

        for i, r in enumerate(results[:self._max_results], 1):
            title = r.get("title", "").strip()
            content = r.get("content", "").strip()
            url = r.get("url", "").strip()
            if title:
                clean_content = content[:160] + "..." if len(content) > 160 else content
                output_parts.append(f"{i}. {title}: {clean_content} ({url})")

        if not output_parts:
            return "Sin novedades recientes sobre este título."

        return "\n".join(output_parts)

    async def fetch_news(self, query: str) -> str:
        """Busca noticias recientes, parches y lanzamientos sobre el juego o tema."""
        if not self._api_key or not self._api_key.strip():
            logger.debug("Tavily API key no configurada; omitiendo búsqueda de noticias.")
            return "Sin noticias externas disponibles (API Key no configurada)."

        if not query or not query.strip():
            return "Sin noticias externas."

        search_query = f"{query.strip()} noticias videojuegos lanzamientos parches"

        payload: dict[str, Any] = {
            "api_key": self._api_key,
            "query": search_query,
            "search_depth": "basic",
            "include_answer": True,
            "max_results": self._max_results,
            "topic": "news",
        }

        try:
            if self._client:
                return await self._fetch_with_client(self._client, payload)
            async with httpx.AsyncClient(timeout=4.0) as client:
                return await self._fetch_with_client(client, payload)
        except Exception as exc:
            logger.debug("Fallo al consultar Tavily API para '%s': %s", query, exc)
            return "Sin noticias externas disponibles por el momento."

