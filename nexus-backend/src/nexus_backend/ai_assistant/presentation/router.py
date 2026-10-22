from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from langgraph.checkpoint.memory import MemorySaver

from nexus_backend.config import get_settings
from nexus_backend.ai_assistant.application.dtos import ChatRequest
from nexus_backend.ai_assistant.application.services import AssistantService
from nexus_backend.ai_assistant.infrastructure.cheapshark_adapter import CheapSharkPriceAdapter
from nexus_backend.ai_assistant.infrastructure.embeddings import HuggingFaceEmbeddingAdapter
from nexus_backend.ai_assistant.infrastructure.laya_adapter import LayaDecisionAdapter
from nexus_backend.ai_assistant.infrastructure.llm import GroqLLMAdapter
from nexus_backend.ai_assistant.infrastructure.pinecone_store import PineconeVectorStoreAdapter
from nexus_backend.ai_assistant.infrastructure.tavily_adapter import TavilyNewsAdapter
from nexus_backend.ai_assistant.infrastructure.wikipedia import WikipediaAdapter

router = APIRouter(prefix="/assistant", tags=["AI Shopping Assistant"])

# Checkpointer en memoria compartido para persistencia multi-turno por session_id (thread_id)
_shared_checkpointer = MemorySaver()


def _get_assistant_service() -> AssistantService:
    settings = get_settings()
    vector_store = PineconeVectorStoreAdapter(
        api_key=settings.PINECONE_API_KEY,
        index_name=settings.PINECONE_INDEX_NAME,
        namespace=settings.PINECONE_NAMESPACE,
    )
    gaming_news_adapter = (
        TavilyNewsAdapter(
            api_key=settings.TAVILY_API_KEY,
            max_results=settings.TAVILY_MAX_RESULTS,
        )
        if settings.TAVILY_API_KEY
        else None
    )
    price_comparison_adapter = (
        CheapSharkPriceAdapter(
            usd_clp_rate=settings.CHEAPSHARK_USD_CLP_RATE,
        )
        if settings.CHEAPSHARK_ENABLED
        else None
    )
    from nexus_backend.ai_assistant.infrastructure.email_adapter import GmailEmailAdapter
    email_adapter = (
        GmailEmailAdapter()
        if (settings.SMTP_USER or settings.GMAIL_USER)
        else None
    )

    return AssistantService(
        embedding_port=HuggingFaceEmbeddingAdapter(model_name=settings.EMBEDDING_MODEL_NAME),
        llm_port=GroqLLMAdapter(
            api_key=settings.GROQ_API_KEY,
            model_name=settings.GROQ_MODEL_NAME,
            temperature=settings.GROQ_TEMPERATURE,
        ),
        vector_store_port=vector_store,
        external_knowledge_port=WikipediaAdapter(
            lang=settings.WIKIPEDIA_LANG,
            top_k_results=settings.WIKIPEDIA_TOP_K,
            doc_content_chars_max=settings.WIKIPEDIA_MAX_CHARS,
        ),
        decision_port=LayaDecisionAdapter(
            model_name=settings.LAYA_MODEL_NAME,
        ),
        checkpointer=_shared_checkpointer,
        gaming_news_port=gaming_news_adapter,
        price_comparison_port=price_comparison_adapter,
        email_port=email_adapter,
    )


@router.post("/chat")
async def chat_stream(
    body: ChatRequest,
    service: AssistantService = Depends(_get_assistant_service),
) -> StreamingResponse:
    history = body.to_chat_messages()
    session_id = body.session_id or "default-session"
    return StreamingResponse(
        service.chat_stream(
            query=body.query,
            chat_history=history,
            session_id=session_id,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.delete("/session/{session_id}")
async def reset_session(session_id: str) -> dict:
    """Restablece la memoria de conversación acumulada para una sesión."""
    # Elimina los checkpoints de MemorySaver para ese thread_id
    if hasattr(_shared_checkpointer, "storage"):
        _shared_checkpointer.storage.pop(session_id, None)
    return {"status": "cleared", "session_id": session_id}
