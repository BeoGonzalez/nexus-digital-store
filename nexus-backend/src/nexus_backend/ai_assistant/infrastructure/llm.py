from collections.abc import AsyncIterator

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

from nexus_backend.config import get_settings


class GroqLLMAdapter:
    def __init__(self, api_key: str, model_name: str) -> None:
        self._llm = ChatGroq(
            api_key=api_key,
            model=model_name,
            temperature=0.7,
            max_tokens=1024,
            streaming=True,
        )

    async def generate_stream(
        self, system_prompt: str, user_message: str,
    ) -> AsyncIterator[str]:
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message),
        ]
        async for chunk in self._llm.astream(messages):
            if chunk.content:
                yield chunk.content
