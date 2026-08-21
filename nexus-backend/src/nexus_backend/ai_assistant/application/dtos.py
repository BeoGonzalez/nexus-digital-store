from pydantic import BaseModel

from nexus_backend.ai_assistant.domain.entities import ChatMessage


class ChatRequest(BaseModel):
    query: str
    chat_history: list[dict] = []

    def to_chat_messages(self) -> list[ChatMessage]:
        return [
            ChatMessage(role=msg.get("role", "user"), content=msg.get("content", ""))
            for msg in self.chat_history
        ]
