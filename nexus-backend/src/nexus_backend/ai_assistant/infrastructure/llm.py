from collections.abc import AsyncIterator

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

from nexus_backend.config import get_settings


class GroqLLMAdapter:
    def __init__(
        self,
        api_key: str,
        model_name: str,
        temperature: float | None = None,
    ) -> None:
        settings = get_settings()
        self._temp = temperature if temperature is not None else settings.GROQ_TEMPERATURE
        self._llm = ChatGroq(
            api_key=api_key,
            model=model_name,
            temperature=self._temp,
            max_tokens=1024,
            streaming=True,
        )

    @property
    def llm(self) -> ChatGroq:
        return self._llm

    async def generate(self, system_prompt: str, user_message: str) -> str:
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message),
        ]
        response = await self._llm.ainvoke(messages)
        return str(response.content) if response and response.content else ""

    async def generate_stream(
        self, system_prompt: str, user_message: str,
    ) -> AsyncIterator[str]:
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_message),
        ]
        async for chunk in self._llm.astream(messages):
            if chunk.content:
                yield str(chunk.content)
