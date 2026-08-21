import pytest
import json
from unittest.mock import AsyncMock, MagicMock, call

from nexus_backend.ai_assistant.application.services import AssistantService
from nexus_backend.catalog.domain.entities import Product
from nexus_backend.ai_assistant.domain.entities import ChatMessage
from nexus_backend.ai_assistant.application.graph import SYSTEM_PROMPT


@pytest.fixture
def assistant_service(
    mock_embedding_port: AsyncMock, mock_llm_port: AsyncMock, mock_vector_store_port: AsyncMock
) -> AssistantService:
    return AssistantService(
        embedding_port=mock_embedding_port,
        llm_port=mock_llm_port,
        vector_store_port=mock_vector_store_port,
    )


@pytest.mark.asyncio
async def test_chat_stream_assembles_context_and_validates_contract(
    assistant_service: AssistantService,
    mock_embedding_port: AsyncMock,
    mock_vector_store_port: AsyncMock,
    mock_llm_port: MagicMock,
    dummy_product: Product,
):
    # Arrange
    query = "Do you have any GPUs?"
    mock_vector = [0.123] * 384
    mock_embedding_port.embed_text.return_value = mock_vector
    mock_vector_store_port.similarity_search.return_value = [dummy_product]
    
    history = [
        ChatMessage(role="user", content="Hi"),
        ChatMessage(role="assistant", content="Hello, how can I help?"),
    ]

    # Act
    chunks = []
    async for chunk in assistant_service.chat_stream(query, history):
        chunks.append(chunk)

    # Assert - Contract & State Mutations
    
    # 1. Spying: Exact query passed to embedding port
    mock_embedding_port.embed_text.assert_called_once_with(query)
    
    # 2. Spying: Exact vector and parameters passed to vector store
    mock_vector_store_port.similarity_search.assert_called_once_with(mock_vector, top_k=5)
    
    # 3. Spying: Exact prompt assembly passed to the LLM
    assert mock_llm_port.generate_stream.call_count == 1
    llm_call_args = mock_llm_port.generate_stream.call_args
    passed_system_prompt = llm_call_args[0][0]
    passed_user_message = llm_call_args[0][1]
    
    # Check that system prompt is strictly the system prompt constant
    assert passed_system_prompt == SYSTEM_PROMPT
    
    # Check that the user message includes the retrieved product specifications
    assert dummy_product.name in passed_user_message
    assert dummy_product.brand in passed_user_message
    assert "24GB" in passed_user_message  # The specification from dummy_product
    assert str(dummy_product.stock) in passed_user_message
    
    # Check that history is appended correctly
    assert "user: Hi" in passed_user_message
    assert "assistant: Hello, how can I help?" in passed_user_message
    assert f"Pregunta del cliente: {query}" in passed_user_message
    
    # 4. Assert chunk streaming formats (SSE format strictness)
    assert len(chunks) == 5  # 1 products + 3 token yields from mock + 1 done
    
    products_event = chunks[0]
    assert products_event.startswith("data: ")
    products_payload = json.loads(products_event[6:])
    assert products_payload["type"] == "products"
    assert len(products_payload["data"]) == 1
    assert products_payload["data"][0]["id"] == str(dummy_product.id)
    
    assert 'type": "done' in chunks[-1] or "type': 'done'" in chunks[-1]


@pytest.mark.asyncio
async def test_chat_stream_empty_results_and_history(
    assistant_service: AssistantService,
    mock_embedding_port: AsyncMock,
    mock_vector_store_port: AsyncMock,
    mock_llm_port: MagicMock,
):
    # Arrange
    mock_embedding_port.embed_text.return_value = [0.0] * 384
    mock_vector_store_port.similarity_search.return_value = []
    
    query = "Looking for something that doesn't exist"

    # Act
    chunks = []
    async for chunk in assistant_service.chat_stream(query, chat_history=None):
        chunks.append(chunk)

    # Assert - Contract
    mock_vector_store_port.similarity_search.assert_called_once_with([0.0] * 384, top_k=5)
    
    passed_user_message = mock_llm_port.generate_stream.call_args[0][1]
    
    # Fallback text when no products are found
    assert "No se encontraron productos relevantes." in passed_user_message
    # No history injected
    assert "Historial de conversación:\n\n" in passed_user_message
