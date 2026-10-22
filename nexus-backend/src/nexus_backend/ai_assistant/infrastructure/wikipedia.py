import asyncio
import logging

try:
    from langchain_community.utilities import WikipediaAPIWrapper
except ImportError:
    WikipediaAPIWrapper = None

try:
    import wikipedia
except ImportError:
    wikipedia = None

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
        self._wiki = None
        if WikipediaAPIWrapper:
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
        if not topic:
            return "Sin datos externos."

        query = f"{topic} videojuego" if "videojuego" not in topic.lower() else topic

        def _fetch() -> str:
            if self._wiki:
                try:
                    result = self._wiki.run(query)
                    return result.strip() if result else "Sin datos externos."
                except Exception as exc:
                    logger.debug("WikipediaAPIWrapper query failed for '%s': %s", query, exc)
                    return "Sin datos externos."
            elif wikipedia:
                try:
                    wikipedia.set_lang(self._lang)
                    search_results = wikipedia.search(query, results=self._top_k)
                    if search_results:
                        summary = wikipedia.summary(search_results[0], sentences=3)
                        return summary[:self._chars_max].strip() if summary else "Sin datos externos."
                except Exception as exc:
                    logger.debug("Native wikipedia query failed for '%s': %s", query, exc)
            return "Sin datos externos."

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _fetch)

