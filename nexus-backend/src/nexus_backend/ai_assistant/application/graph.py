import logging
from langsmith import traceable
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, END
from langchain_core.messages import AIMessage, HumanMessage

from nexus_backend.ai_assistant.application.chains import (
    NEXUSBOT_SYSTEM_PROMPT,
    build_lcel_generation_chain,
)
from nexus_backend.ai_assistant.application.crew import run_nexus_crew
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

SYSTEM_PROMPT = NEXUSBOT_SYSTEM_PROMPT


def build_rag_graph(
    embedding_port: EmbeddingPort,
    llm_port: LLMPort,
    vector_store_port: VectorStorePort,
    external_knowledge_port: ExternalKnowledgePort | None = None,
    decision_port: DecisionEnginePort | None = None,
) -> StateGraph:
    settings = get_settings()

    @traceable(name="laya_decision")
    async def decide(state: AssistantState) -> dict:
        query = state.get("query", "")
        if decision_port:
            metrics = await decision_port.evaluate_decision(query)
            return {
                "intent": metrics.get("intent", "recommendation"),
                "decision_metrics": metrics,
            }
        return {"intent": "recommendation", "decision_metrics": {"engine": "default"}}

    @traceable(name="rag_retrieve")
    async def retrieve(state: AssistantState) -> dict:
        query = state["query"]
        intent = state.get("intent", "recommendation")
        decision_metrics = state.get("decision_metrics", {})

        embedding = await embedding_port.embed_text(query)
        video_games = await vector_store_port.similarity_search(
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

        # Búsqueda externa en Wikipedia (optimizado por System 1 de Laya AI)
        external_context = "Sin datos externos."
        should_fetch_trivia = decision_metrics.get("need_trivia", True) and (intent != "greeting")
        if video_games and external_knowledge_port and should_fetch_trivia:
            top_title = video_games[0].title
            try:
                external_context = await external_knowledge_port.fetch_trivia(top_title)
            except Exception as e:
                logger.debug("External knowledge fetch error: %s", e)

        logger.info("Retrieved %d games for query: %s (intent=%s)", len(video_games), query[:80], intent)
        return {
            "retrieved_products": video_games,
            "context": context,
            "external_context": external_context,
        }

    @traceable(name="crew_orchestrate")
    async def orchestrate(state: AssistantState) -> dict:
        query = state.get("query", "")
        catalog_context = state.get("context", "")
        external_context = state.get("external_context", "")
        intent = state.get("intent", "recommendation")

        if intent == "greeting" and "No se encontraron" in catalog_context:
            return {"crew_analysis": "Saludo cordial de bienvenida al usuario."}

        underlying_llm = getattr(llm_port, "llm", None)
        crew_analysis = await run_nexus_crew(
            query=query,
            catalog_context=catalog_context,
            external_context=external_context,
            llm=underlying_llm,
        )
        return {"crew_analysis": crew_analysis}

    @traceable(name="rag_generate")
    async def generate(state: AssistantState) -> dict:
        context = state.get("context", "")
        external_context = state.get("external_context", "Sin datos externos.")
        crew_analysis = state.get("crew_analysis", "")
        intent = state.get("intent", "recommendation")
        query = state["query"]

        history_text = ""
        if chat_history := state.get("chat_history"):
            history_lines = [
                f"{m['role'] if isinstance(m, dict) else m.role}: {m['content'] if isinstance(m, dict) else m.content}"
                for m in chat_history[-6:]
            ]
            history_text = "\n".join(history_lines)

        user_message = (
            f"Historial de conversación:\n{history_text}\n\n"
            f"Intención detectada (Laya AI): {intent}\n\n"
            f"Videojuegos disponibles:\n{context}\n\n"
            f"Dato curioso externo:\n{external_context}\n\n"
            f"Análisis estratégico:\n{crew_analysis}\n\n"
            f"Pregunta del cliente: {query}"
        )

        underlying_llm = getattr(llm_port, "llm", None)
        if underlying_llm:
            try:
                chain = build_lcel_generation_chain(underlying_llm)
                messages = []
                if chat_history:
                    for m in chat_history[-6:]:
                        role = m["role"] if isinstance(m, dict) else m.role
                        content = m["content"] if isinstance(m, dict) else m.content
                        messages.append(
                            HumanMessage(content=content) if role == "user" else AIMessage(content=content)
                        )
                response_text = await chain.ainvoke({
                    "context": context,
                    "external_context": external_context,
                    "crew_analysis": crew_analysis,
                    "messages": messages,
                    "query": query,
                })
                full_response = response_text
            except Exception as exc:
                logger.debug("LCEL chain execution fallback to llm_port: %s", exc)
                chunks: list[str] = []
                async for chunk in llm_port.generate_stream(SYSTEM_PROMPT, user_message):
                    chunks.append(chunk)
                full_response = "".join(chunks)
        else:
            chunks: list[str] = []
            async for chunk in llm_port.generate_stream(SYSTEM_PROMPT, user_message):
                chunks.append(chunk)
            full_response = "".join(chunks)

        # Actualizar historial serializable para el checkpointer de LangGraph (MemorySaver)
        updated_history = [
            {"role": m.role, "content": m.content} if isinstance(m, ChatMessage) else m
            for m in (chat_history or [])
        ] + [
            {"role": "user", "content": query},
            {"role": "assistant", "content": full_response},
        ]
        return {
            "response": full_response,
            "chat_history": updated_history,
        }

    graph = StateGraph(AssistantState)
    graph.add_node("decide", decide)
    graph.add_node("retrieve", retrieve)
    graph.add_node("orchestrate", orchestrate)
    graph.add_node("generate", generate)

    graph.set_entry_point("decide")
    graph.add_edge("decide", "retrieve")
    graph.add_edge("retrieve", "orchestrate")
    graph.add_edge("orchestrate", "generate")
    graph.add_edge("generate", END)

    return graph
