import json
import logging
from collections.abc import AsyncIterator

from langsmith import traceable

from nexus_backend.ai_assistant.application.graph import SYSTEM_PROMPT, build_rag_graph
from nexus_backend.ai_assistant.domain.entities import AssistantState, ChatMessage
from nexus_backend.ai_assistant.domain.ports import EmbeddingPort, LLMPort, VectorStorePort
from nexus_backend.config import get_settings

logger = logging.getLogger(__name__)


class AssistantService:
    def __init__(
        self,
        embedding_port: EmbeddingPort,
        llm_port: LLMPort,
        vector_store_port: VectorStorePort,
    ) -> None:
        self._embedding = embedding_port
        self._llm = llm_port
        self._vector_store = vector_store_port
        self._graph = build_rag_graph(embedding_port, llm_port, vector_store_port).compile()

    @traceable(name="assistant_chat")
    async def chat(
        self, query: str, chat_history: list[ChatMessage] | None = None,
    ) -> str:
        state: AssistantState = {
            "query": query,
            "chat_history": chat_history or [],
        }
        result = await self._graph.ainvoke(state)
        return result.get("response", "")

    @traceable(name="assistant_chat_stream")
    async def chat_stream(
        self, query: str, chat_history: list[ChatMessage] | None = None,
    ) -> AsyncIterator[str]:
        settings = get_settings()

        embedding = await self._embedding.embed_text(query)
        video_games = await self._vector_store.similarity_search(
            embedding, top_k=settings.VECTOR_SEARCH_TOP_K,
        )

        context_parts = []
        for i, vg in enumerate(video_games, 1):
            genres = ", ".join(g.name for g in vg.genres) if vg.genres else "N/A"
            context_parts.append(
                f"{i}. {vg.title} — ${vg.price_clp} CLP\n"
                f"   Géneros: {genres}\n"
                f"   {vg.description}\n"
                f"   Stock: {vg.stock} unidades"
            )
        context = "\n\n".join(context_parts) if context_parts else "No se encontraron videojuegos relevantes."

        history_text = ""
        if chat_history:
            history_lines = [f"{m.role}: {m.content}" for m in chat_history[-6:]]
            history_text = "\n".join(history_lines)

        user_message = (
            f"Historial de conversación:\n{history_text}\n\n"
            f"Videojuegos disponibles:\n{context}\n\n"
            f"Pregunta del cliente: {query}"
        )

        product_data = [
            {"id": str(vg.id), "title": vg.title, "price_clp": str(vg.price_clp)}
            for vg in video_games
        ]
        yield f"data: {json.dumps({'type': 'products', 'data': product_data})}\n\n"

        async for chunk in self._llm.generate_stream(SYSTEM_PROMPT, user_message):
            yield f"data: {json.dumps({'type': 'token', 'data': chunk})}\n\n"

        yield f"data: {json.dumps({'type': 'done'})}\n\n"
