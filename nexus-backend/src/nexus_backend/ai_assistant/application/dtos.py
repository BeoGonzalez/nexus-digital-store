from pydantic import BaseModel, Field

from nexus_backend.ai_assistant.domain.entities import ChatMessage


class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Pregunta o consulta del usuario")
    chat_history: list[dict] = Field(default_factory=list)

    def to_chat_messages(self) -> list[ChatMessage]:
        return [
            ChatMessage(role=msg.get("role", "user"), content=msg.get("content", ""))
            for msg in self.chat_history
        ]
