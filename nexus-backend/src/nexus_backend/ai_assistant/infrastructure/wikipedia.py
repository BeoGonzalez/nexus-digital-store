import asyncio
import logging

from langchain_community.utilities import WikipediaAPIWrapper

from nexus_backend.ai_assistant.domain.ports import ExternalKnowledgePort
from nexus_backend.config import get_settings

logger = logging.getLogger(__name__)


class WikipediaAdapter(ExternalKnowledgePort):
    def __init__(
        self,
        lang: str | None = None,
        top_k_results: int | None = None,
        doc_content_chars_max: int | None = None,
    ) -> None:
        settings = get_settings()
        self._lang = lang or settings.WIKIPEDIA_LANG
        self._top_k = top_k_results or settings.WIKIPEDIA_TOP_K
        self._chars_max = doc_content_chars_max or settings.WIKIPEDIA_MAX_CHARS
        try:
            self._wiki = WikipediaAPIWrapper(
                lang=self._lang,
                top_k_results=self._top_k,
                doc_content_chars_max=self._chars_max,
            )
        except Exception as e:
            logger.warning("Could not initialize WikipediaAPIWrapper: %s", e)
            self._wiki = None

    async def fetch_trivia(self, topic: str) -> str:
        if not topic or not self._wiki:
            return "Sin datos externos."

        query = f"{topic} videojuego" if "videojuego" not in topic.lower() else topic

        def _fetch() -> str:
            try:
                result = self._wiki.run(query)
                return result.strip() if result else "Sin datos externos."
            except Exception as exc:
                logger.debug("Wikipedia query failed for '%s': %s", query, exc)
                return "Sin datos externos."

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _fetch)

