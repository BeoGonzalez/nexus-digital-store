import asyncio
import logging
from langsmith import traceable
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, END
from langchain_core.messages import AIMessage, HumanMessage

from nexus_backend.ai_assistant.application.chains import (
    NEXUSBOT_SYSTEM_PROMPT,
    build_lcel_generation_chain,
)
from nexus_backend.ai_assistant.application.context_resolver import (
    align_catalog_context,
    build_unified_user_message,
    resolve_target_game,
)
from nexus_backend.ai_assistant.application.crew import run_nexus_crew
from nexus_backend.ai_assistant.domain.entities import AssistantState, ChatMessage
from nexus_backend.ai_assistant.domain.ports import (
    DecisionEnginePort,
    EmailPort,
    EmbeddingPort,
    ExternalKnowledgePort,
    GamingNewsPort,
    LLMPort,
    PriceComparisonPort,
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
    gaming_news_port: GamingNewsPort | None = None,
    price_comparison_port: PriceComparisonPort | None = None,
    email_port: EmailPort | None = None,
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
        chat_history = state.get("chat_history", [])

        embedding = await embedding_port.embed_text(query)
        candidates = await vector_store_port.similarity_search(
            embedding, top_k=settings.VECTOR_SEARCH_TOP_K,
        )

        # Resolución inteligente y sincronizada del videojuego objetivo
        target = resolve_target_game(query, chat_history=chat_history, candidates=candidates)
        video_games, context = align_catalog_context(target, candidates)

        target_topic = target.title
        target_price = target.price_clp
        should_fetch_trivia = decision_metrics.get("need_trivia", True) and (intent != "greeting")

        async def _fetch_wiki() -> str:
            if external_knowledge_port and should_fetch_trivia and target_topic:
                try:
                    return await external_knowledge_port.fetch_trivia(target_topic)
                except Exception as e:
                    logger.debug("External knowledge fetch error: %s", e)
            return "Sin datos externos."

        async def _fetch_news() -> str:
            if gaming_news_port and (intent != "greeting") and target_topic:
                try:
                    return await gaming_news_port.fetch_news(target_topic)
                except Exception as e:
                    logger.debug("Gaming news fetch error (Tavily): %s", e)
            return "Sin noticias adicionales."

        async def _fetch_prices() -> str:
            if price_comparison_port and (intent != "greeting") and target_topic:
                try:
                    comp_data = await price_comparison_port.compare_price(target_topic, target_price)
                    if comp_data.get("has_data"):
                        return comp_data.get("comparison_summary", "Sin datos comparativos de otras tiendas.")
                except Exception as e:
                    logger.debug("Price comparison error (CheapShark): %s", e)
            return "Sin datos comparativos de otras tiendas."

        external_context, gaming_news, price_comparison = await asyncio.gather(
            _fetch_wiki(),
            _fetch_news(),
            _fetch_prices(),
        )

        logger.info(
            "Retrieved %d games for query: %s (target=%s, intent=%s)",
            len(video_games), query[:80], target_topic, intent,
        )
        return {
            "retrieved_products": video_games,
            "context": context,
            "external_context": external_context,
            "gaming_news": gaming_news,
            "price_comparison": price_comparison,
        }
        return {
            "retrieved_products": video_games,
            "context": context,
            "external_context": external_context,
            "gaming_news": gaming_news,
            "price_comparison": price_comparison,
        }

    @traceable(name="crew_orchestrate")
    async def orchestrate(state: AssistantState) -> dict:
        query = state.get("query", "")
        catalog_context = state.get("context", "")
        external_context = state.get("external_context", "")
        intent = state.get("intent", "recommendation")

        if not settings.ENABLE_CREWAI_ORCHESTRATION:
            return {"crew_analysis": ""}

        if intent in ("greeting", "support", "stock_price", "send_email") or "No se encontraron" in catalog_context:
            return {"crew_analysis": ""}

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
        gaming_news = state.get("gaming_news", "Sin noticias adicionales.")
        price_comparison = state.get("price_comparison", "Sin datos comparativos de otras tiendas.")
        crew_analysis = state.get("crew_analysis", "")
        intent = state.get("intent", "recommendation")
        query = state["query"]
        chat_history = state.get("chat_history")

        target = resolve_target_game(
            query,
            chat_history=chat_history,
            candidates=state.get("retrieved_products", []),
        )

        user_message = build_unified_user_message(
            query=query,
            target=target,
            intent=intent,
            context=context,
            external_context=external_context,
            gaming_news=gaming_news,
            price_comparison=price_comparison,
            crew_analysis=crew_analysis,
            chat_history=chat_history,
        )

        system_prompt = SYSTEM_PROMPT.format(
            context=context,
            external_context=external_context,
            gaming_news=gaming_news,
            price_comparison=price_comparison,
            crew_analysis=crew_analysis or "Sin análisis estratégico adicional.",
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
                    "gaming_news": gaming_news,
                    "price_comparison": price_comparison,
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

        # Si la consulta solicita enviar correo y hay un destinatario configurado o detectado
        recipient_email = (state.get("decision_metrics") or {}).get("recipient_email")
        if not recipient_email:
            import re
            m = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", query)
            recipient_email = m.group(0) if m else None

        if email_port and recipient_email:
            try:
                top_game_title = (state.get("retrieved_products") or [None])[0]
                game_subject = f": {top_game_title.title}" if top_game_title else ""
                subject = f"🎮 Nexus Digital Store — Recomendación & Ofertas{game_subject}"
                mail_res = await email_port.send_email(
                    to_email=recipient_email,
                    subject=subject,
                    content_html=full_response,
                    content_text=full_response,
                )
                if mail_res.get("success"):
                    full_response += f"\n\n✉️ *¡Listo! Te acabo de enviar esta recomendación y ofertas a tu correo ({recipient_email}).*"
            except Exception as mail_exc:
                logger.debug("Error enviando correo desde LangGraph: %s", mail_exc)

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
