from collections.abc import AsyncIterator

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

from nexus_backend.config import get_settings


class GroqLLMAdapter:
    def __init__(
        self,
        api_key: str | None = None,
        model_name: str | None = None,
        temperature: float | None = None,
    ) -> None:
        settings = get_settings()
        self._temp = temperature if temperature is not None else settings.GROQ_TEMPERATURE
        key = api_key or settings.GROQ_API_KEY or "gsk_dummy_test_key_for_groq"
        model = model_name or settings.GROQ_MODEL_NAME
        self._llm = ChatGroq(
            api_key=key,
            model=model,
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
