"""Pruebas unitarias para las entidades y DTOs del Asistente IA."""

import pytest
from pydantic import ValidationError

from nexus_backend.ai_assistant.application.dtos import ChatRequest
from nexus_backend.ai_assistant.domain.entities import ChatMessage


class TestAIAssistantDomainAndDtos:
    """Suite de validación de estructuras de datos para el asistente conversacional."""

    def test_chat_message_entity_attributes(self) -> None:
        # Arrange & Act
        msg = ChatMessage(role="user", content="¿Tienen juegos de terror?")

        # Assert
        assert msg.role == "user"
        assert msg.content == "¿Tienen juegos de terror?"

    def test_chat_request_to_chat_messages_conversion(self) -> None:
        # Arrange
        request = ChatRequest(
            query="Busco un RPG difícil",
            chat_history=[
                {"role": "user", "content": "Hola"},
                {"role": "assistant", "content": "¡Hola! ¿En qué te ayudo?"},
            ],
        )

        # Act
        messages = request.to_chat_messages()

        # Assert - Conversión estricta a entidades de dominio
        assert len(messages) == 2
        assert isinstance(messages[0], ChatMessage)
        assert messages[0].role == "user"
        assert messages[0].content == "Hola"
        assert isinstance(messages[1], ChatMessage)
        assert messages[1].role == "assistant"
        assert messages[1].content == "¡Hola! ¿En qué te ayudo?"

    def test_chat_request_validation_error_empty_query(self) -> None:
        # Act & Assert
        # Regla de validación: La consulta (query) no puede ser una cadena vacía
        with pytest.raises(ValidationError):
            ChatRequest(query="")
