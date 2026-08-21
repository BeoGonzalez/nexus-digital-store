from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from nexus_backend.config import get_settings

from nexus_backend.ai_assistant.application.dtos import ChatRequest
from nexus_backend.ai_assistant.application.services import AssistantService
from nexus_backend.ai_assistant.infrastructure.embeddings import HuggingFaceEmbeddingAdapter
from nexus_backend.ai_assistant.infrastructure.llm import GroqLLMAdapter
from nexus_backend.ai_assistant.infrastructure.vector_store import PgVectorStoreAdapter
from nexus_backend.database import get_db_session

router = APIRouter(prefix="/assistant", tags=["AI Shopping Assistant"])


def _get_assistant_service(
    session: AsyncSession = Depends(get_db_session),
) -> AssistantService:
    settings = get_settings()
    return AssistantService(
        embedding_port=HuggingFaceEmbeddingAdapter(model_name=settings.EMBEDDING_MODEL_NAME),
        llm_port=GroqLLMAdapter(api_key=settings.GROQ_API_KEY, model_name=settings.GROQ_MODEL_NAME),
        vector_store_port=PgVectorStoreAdapter(session),
    )


@router.post("/chat")
async def chat_stream(
    body: ChatRequest,
    service: AssistantService = Depends(_get_assistant_service),
) -> StreamingResponse:
    history = body.to_chat_messages()
    return StreamingResponse(
        service.chat_stream(query=body.query, chat_history=history),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
