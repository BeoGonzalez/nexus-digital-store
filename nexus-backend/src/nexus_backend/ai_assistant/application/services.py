import json
import logging
from collections.abc import AsyncIterator

from langgraph.checkpoint.memory import MemorySaver
from langsmith import traceable

from nexus_backend.ai_assistant.application.crew import run_nexus_crew
from nexus_backend.ai_assistant.application.graph import SYSTEM_PROMPT, build_rag_graph
from nexus_backend.ai_assistant.domain.entities import AssistantState, ChatMessage
from nexus_backend.ai_assistant.domain.ports import (
    DecisionEnginePort,
    EmbeddingPort,
    ExternalKnowledgePort,
    LLMPort,
    VectorStorePort,
)
from nexus_backend.config import get_settings

logger = logging.getLogger(__name__)


class AssistantService:
    def __init__(
        self,
        embedding_port: EmbeddingPort,
        llm_port: LLMPort,
        vector_store_port: VectorStorePort,
        external_knowledge_port: ExternalKnowledgePort | None = None,
        decision_port: DecisionEnginePort | None = None,
        checkpointer: MemorySaver | None = None,
    ) -> None:
        self._embedding = embedding_port
        self._llm = llm_port
        self._vector_store = vector_store_port
        self._external_knowledge = external_knowledge_port
        self._decision = decision_port
        self._checkpointer = checkpointer if checkpointer is not None else MemorySaver()
        self._graph = build_rag_graph(
            embedding_port,
            llm_port,
            vector_store_port,
            external_knowledge_port,
            decision_port,
        ).compile(checkpointer=self._checkpointer)

    @traceable(name="assistant_chat")
    async def chat(
        self,
        query: str,
        chat_history: list[ChatMessage] | None = None,
        session_id: str = "default-session",
    ) -> str:
        config = {"configurable": {"thread_id": session_id}}
        state: AssistantState = {"query": query}
        if chat_history:
            state["chat_history"] = chat_history

        result = await self._graph.ainvoke(state, config=config)
        return result.get("response", "")

    @traceable(name="assistant_chat_stream")
    async def chat_stream(
        self,
        query: str,
        chat_history: list[ChatMessage] | None = None,
        session_id: str = "default-session",
    ) -> AsyncIterator[str]:
        settings = get_settings()
        config = {"configurable": {"thread_id": session_id}}

        # Si el cliente no envió historial explícito, recuperarlo del checkpointer (MemorySaver)
        if not chat_history and self._checkpointer:
            try:
                saved_state = self._graph.get_state(config)
                if saved_state and saved_state.values:
                    raw_history = saved_state.values.get("chat_history", [])
                    chat_history = [
                        ChatMessage(role=m["role"], content=m["content"]) if isinstance(m, dict) else m
                        for m in raw_history
                    ]
            except Exception as e:
                logger.debug("Could not retrieve state from checkpointer: %s", e)
                chat_history = []

        # Evaluación System 1 (Laya AI)
        intent = "recommendation"
        need_trivia = True
        if self._decision:
            try:
                metrics = await self._decision.evaluate_decision(query)
                intent = metrics.get("intent", "recommendation")
                need_trivia = metrics.get("need_trivia", True)
            except Exception as e:
                logger.debug("Laya decision evaluation failed in chat_stream: %s", e)

        embedding = await self._embedding.embed_text(query)
        video_games = await self._vector_store.similarity_search(
            embedding, top_k=settings.VECTOR_SEARCH_TOP_K,
        )

        context_parts = []
        for i, vg in enumerate(video_games, 1):
            genres = ", ".join(g.name for g in vg.genres) if vg.genres else "N/A"
            stock_info = f"Stock: {vg.stock} unidades" if vg.stock > 0 else "SIN STOCK (0 unidades)"
            context_parts.append(
                f"{i}. {vg.title} — ${vg.price_clp} CLP\n"
                f"   Géneros: {genres}\n"
                f"   {vg.description}\n"
                f"   {stock_info}"
            )
        context = "\n\n".join(context_parts) if context_parts else "No se encontraron videojuegos relevantes."

        # Conocimiento externo (Wikipedia) optimizado por Laya AI
        external_context = "Sin datos externos."
        if video_games and self._external_knowledge and need_trivia and (intent != "greeting"):
            try:
                external_context = await self._external_knowledge.fetch_trivia(video_games[0].title)
            except Exception as e:
                logger.debug("External knowledge fetch error in stream: %s", e)

        # Orquestación multi-agente CrewAI
        crew_analysis = ""
        if settings.ENABLE_CREWAI_ORCHESTRATION and video_games and (intent != "greeting"):
            underlying_llm = getattr(self._llm, "llm", None)
            crew_analysis = await run_nexus_crew(
                query=query,
                catalog_context=context,
                external_context=external_context,
                llm=underlying_llm,
            )

        history_text = ""
        if chat_history:
            history_lines = [f"{m.role}: {m.content}" for m in chat_history[-6:]]
            history_text = "\n".join(history_lines)

        user_message_parts = [
            f"Historial de conversación:\n{history_text}\n",
            f"Videojuegos disponibles:\n{context}\n",
        ]
        if external_context and external_context != "Sin datos externos.":
            user_message_parts.append(f"Dato curioso externo:\n{external_context}\n")
        if crew_analysis:
            user_message_parts.append(f"Análisis estratégico:\n{crew_analysis}\n")
        user_message_parts.append(f"Pregunta del cliente: {query}")

        user_message = "\n".join(user_message_parts)

        product_data = [
            {"id": str(vg.id), "title": vg.title, "price_clp": str(vg.price_clp)}
            for vg in video_games
        ]
        yield f"data: {json.dumps({'type': 'products', 'data': product_data})}\n\n"

        accumulated_tokens: list[str] = []
        async for chunk in self._llm.generate_stream(SYSTEM_PROMPT, user_message):
            accumulated_tokens.append(chunk)
            yield f"data: {json.dumps({'type': 'token', 'data': chunk})}\n\n"

        # Persistir el turno generado en MemorySaver
        full_response = "".join(accumulated_tokens)
        if self._checkpointer:
            try:
                serialized_history = [
                    {"role": m.role, "content": m.content} if isinstance(m, ChatMessage) else m
                    for m in (chat_history or [])
                ] + [
                    {"role": "user", "content": query},
                    {"role": "assistant", "content": full_response},
                ]
                self._graph.update_state(
                    config,
                    {
                        "chat_history": serialized_history,
                        "query": query,
                        "response": full_response,
                    },
                )
            except Exception as e:
                logger.debug("Failed to update MemorySaver state in chat_stream: %s", e)

        yield f"data: {json.dumps({'type': 'done'})}\n\n"
