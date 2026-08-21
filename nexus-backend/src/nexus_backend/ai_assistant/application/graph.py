import logging

from langsmith import traceable
from langgraph.graph import StateGraph, END

from nexus_backend.ai_assistant.domain.entities import AssistantState
from nexus_backend.ai_assistant.domain.ports import EmbeddingPort, LLMPort, VectorStorePort
from nexus_backend.config import get_settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Eres el Shopping Assistant de Nexus Digital Store, una tienda de hardware gamer premium.

Tu rol:
- Ayudar a los clientes a encontrar los mejores productos de hardware gamer.
- Recomendar productos basándote EXCLUSIVAMENTE en el catálogo proporcionado.
- Comparar especificaciones técnicas cuando el cliente lo pida.
- Responder en el idioma del cliente (español o inglés).

Reglas:
- SOLO recomienda productos que aparezcan en el contexto proporcionado.
- Si no hay productos relevantes, indica que no encontraste coincidencias y sugiere reformular la búsqueda.
- Incluye precios y especificaciones clave en tus respuestas.
- Sé conciso pero informativo.
"""


def build_rag_graph(
    embedding_port: EmbeddingPort,
    llm_port: LLMPort,
    vector_store_port: VectorStorePort,
) -> StateGraph:
    settings = get_settings()

    @traceable(name="rag_retrieve")
    async def retrieve(state: AssistantState) -> dict:
        query = state["query"]
        embedding = await embedding_port.embed_text(query)
        products = await vector_store_port.similarity_search(
            embedding, top_k=settings.VECTOR_SEARCH_TOP_K,
        )

        context_parts = []
        for i, p in enumerate(products, 1):
            specs = ", ".join(f"{k}: {v}" for k, v in p.specifications.items()) if p.specifications else "N/A"
            context_parts.append(
                f"{i}. {p.name} ({p.brand}) — ${p.price}\n"
                f"   Categoría: {p.category}\n"
                f"   {p.description}\n"
                f"   Specs: {specs}\n"
                f"   Stock: {p.stock} unidades"
            )

        context = "\n\n".join(context_parts) if context_parts else "No se encontraron productos relevantes."

        logger.info("Retrieved %d products for query: %s", len(products), query[:80])
        return {
            "retrieved_products": products,
            "context": context,
        }

    @traceable(name="rag_generate")
    async def generate(state: AssistantState) -> dict:
        context = state.get("context", "")
        query = state["query"]

        history_text = ""
        if chat_history := state.get("chat_history"):
            history_lines = [f"{m.role}: {m.content}" for m in chat_history[-6:]]
            history_text = "\n".join(history_lines)

        user_message = (
            f"Historial de conversación:\n{history_text}\n\n"
            f"Productos disponibles:\n{context}\n\n"
            f"Pregunta del cliente: {query}"
        )

        chunks: list[str] = []
        async for chunk in llm_port.generate_stream(SYSTEM_PROMPT, user_message):
            chunks.append(chunk)

        return {"response": "".join(chunks)}

    graph = StateGraph(AssistantState)
    graph.add_node("retrieve", retrieve)
    graph.add_node("generate", generate)

    graph.set_entry_point("retrieve")
    graph.add_edge("retrieve", "generate")
    graph.add_edge("generate", END)

    return graph
