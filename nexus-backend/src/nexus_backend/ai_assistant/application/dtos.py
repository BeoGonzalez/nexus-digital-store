from pydantic import BaseModel, Field, model_validator

from nexus_backend.ai_assistant.domain.entities import ChatMessage


class ChatRequest(BaseModel):
    query: str = Field(default="", description="Pregunta o consulta del usuario")
    message: str | None = Field(default=None, description="Alias opcional para query")
    chat_history: list[dict] = Field(default_factory=list)
    session_id: str | None = Field(default=None, description="ID de sesión para persistencia en memoria (MemorySaver)")

    @model_validator(mode="after")
    def validate_query(self) -> "ChatRequest":
        if not self.query and self.message:
            self.query = self.message
        if not self.query or not self.query.strip():
            raise ValueError("El campo 'query' o 'message' es requerido y no puede estar vacío.")
        return self

    def to_chat_messages(self) -> list[ChatMessage]:
        return [
            ChatMessage(role=msg.get("role", "user"), content=msg.get("content", ""))
            for msg in self.chat_history
        ]
