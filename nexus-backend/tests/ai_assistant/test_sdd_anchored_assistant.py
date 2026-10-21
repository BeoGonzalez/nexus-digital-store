"""=============================================================================
SUITE DE PRUEBAS UNITARIAS: TDD & SDD ANCHORED (ASISTENTE IA - NEXUSBOT)
=============================================================================
Metodología:
- TDD (Test-Driven Development): Red -> Green -> Refactor.
- SDD Anchored (Specification-Driven Development): Cada test está estrictamente
  anclado a una especificación de requerimiento funcional, contrato de dominio
  y criterio de aceptación (Given-When-Then / Arrange-Act-Assert).

Especificaciones Ancladas:
- [SDD-SPEC-AI-01]: Respuestas de rechazo/fuera de dominio relativas al input del usuario.
- [SDD-SPEC-AI-02]: DTO Polymorphism y validación estricta de ChatRequest (query vs message).
- [SDD-SPEC-AI-03]: Resiliencia, degradación elegante y contención de excepciones (Groq 429/Offline).
- [SDD-SPEC-AI-04]: Guardrails y directivas del System Prompt (NEXUSBOT_SYSTEM_PROMPT).
- [SDD-SPEC-AI-05]: Contratos de integración de Router y protocolo SSE.
- [SDD-SPEC-AI-06]: Aislamiento multi-turno por session_id (MemorySaver).
=============================================================================
"""

import json
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID
import pytest
from pydantic import ValidationError

from nexus_backend.ai_assistant.application.chains import NEXUSBOT_SYSTEM_PROMPT
from nexus_backend.ai_assistant.application.dtos import ChatRequest
from nexus_backend.ai_assistant.application.services import AssistantService
from nexus_backend.ai_assistant.domain.entities import ChatMessage
from nexus_backend.catalog.domain.entities import VideoGame


# =============================================================================
# [SDD-SPEC-AI-01]: RESPUESTAS RECHAZADAS RELATIVAS AL INPUT DEL USUARIO
# =============================================================================
class TestSDDSpecAI01InputRelativeRejection:
    """[SDD-SPEC-AI-01]: Criterio de Aceptación:
    Cualquier consulta rechazada o fuera de dominio debe responderse en estricta
    relación al input del usuario, explicando la identidad de la IA y tendiendo
    un puente creativo gamer hacia ese tema, sin frases genéricas ni "calibrando".
    """

    @pytest.mark.parametrize(
        ("prompt", "expected_keyword", "expected_context"),
        [
            ("¿Tienes hambre?", "hambre", "no tengo cuerpo biológico ni estómago"),
            ("¿Qué vas a comer hoy?", "comida", "necesito comida humana"),
            ("Tengo mucha sed", "sed", "no tengo cuerpo biológico"),
        ],
    )
    def test_rejection_biological_needs_is_anchored_to_input(
        self, prompt: str, expected_keyword: str, expected_context: str
    ) -> None:
        # Arrange
        dummy_games: list[VideoGame] = []

        # Act
        response = AssistantService._build_contextual_fallback(prompt, dummy_games)
        response_lower = response.lower()

        # Assert (SDD Anchor: alusión al tema + explicación IA + prohibición de frase estática)
        assert expected_keyword in response_lower
        assert expected_context in response_lower
        assert "calibrando en esta iteración" not in response_lower
        assert "¿qué tipo de juego" in response_lower or "videojuegos" in response_lower

    @pytest.mark.parametrize(
        "prompt",
        [
            "¿Cómo está el clima hoy?",
            "¿Va a llover en Santiago?",
            "¿Cuál es la temperatura exterior?",
            "¿Está soleado afuera?",
        ],
    )
    def test_rejection_meteorology_is_anchored_to_input(self, prompt: str) -> None:
        # Arrange
        dummy_games: list[VideoGame] = []

        # Act
        response = AssistantService._build_contextual_fallback(prompt, dummy_games)
        response_lower = response.lower()

        # Assert (SDD Anchor: menciona clima/tiempo + declara no ver el clima + puente PC gamer)
        assert any(k in response_lower for k in ("clima", "temperatura", "meteorológico", "llueve"))
        assert "no puedo ver el clima" in response_lower or "no tengo sensores meteorológicos" in response_lower
        assert "calibrando en esta iteración" not in response_lower

    def test_rejection_automotive_mechanics_bridges_to_racing_games(self) -> None:
        # Arrange
        prompt = "¿Cómo cambio el aceite del motor de mi auto?"

        # Act
        response = AssistantService._build_contextual_fallback(prompt, [])
        response_lower = response.lower()

        # Assert (SDD Anchor: aborda autos/mecánica + aclara rol de IA + puente a carreras)
        assert any(k in response_lower for k in ("mecánica", "vehículo", "auto", "motor"))
        assert "no soy mecánico" in response_lower or "no tengo un taller" in response_lower
        assert any(k in response_lower for k in ("carreras", "simulador", "conducción", "asfalto"))

    def test_rejection_medical_health_bridges_to_rpg_potions(self) -> None:
        # Arrange
        prompt = "Me duele la cabeza, ¿qué pastilla o medicina me tomo?"

        # Act
        response = AssistantService._build_contextual_fallback(prompt, [])
        response_lower = response.lower()

        # Assert (SDD Anchor: aborda salud/medicina + aclara no ser médico + puente pociones/botiquines)
        assert any(k in response_lower for k in ("salud", "médica", "medicamento", "medicina"))
        assert "no poseo formación médica" in response_lower or "no puedo recetar" in response_lower
        assert any(k in response_lower for k in ("pociones", "botiquines", "pantalla", "profesional"))

    def test_rejection_academic_homework_bridges_to_celebration_gaming(self) -> None:
        # Arrange
        prompt = "Resuélveme esta tarea de matemáticas para el colegio"

        # Act
        response = AssistantService._build_contextual_fallback(prompt, [])
        response_lower = response.lower()

        # Assert (SDD Anchor: aborda tareas/estudio + declina deberes escolares + puente post-estudio)
        assert any(k in response_lower for k in ("tarea", "académica", "estudio", "matemática"))
        assert "no resuelvo deberes" in response_lower or "orientada al catálogo" in response_lower

    def test_rejection_universal_quotes_exact_user_query(self) -> None:
        # Arrange: una pregunta arbitraria no cubierta por palabras clave específicas
        prompt = "¿Cómo puedo tramitar una visa para visitar Australia?"

        # Act
        response = AssistantService._build_contextual_fallback(prompt, [])

        # Assert (SDD Anchor: cita textualmente la consulta y delimita el alcance gamer)
        assert prompt in response
        assert "Nexus Digital Store" in response
        assert "videojuegos de PC" in response


# =============================================================================
# [SDD-SPEC-AI-02]: DTO POLYMORPHISM & VALIDATION (ChatRequest)
# =============================================================================
class TestSDDSpecAI02DtoAliasingAndValidation:
    """[SDD-SPEC-AI-02]: Criterio de Aceptación:
    ChatRequest debe soportar polimorfismo entre 'query' y 'message', asegurando
    retrocompatibilidad con clientes web y validación estricta de strings vacíos.
    """

    def test_dto_accepts_standard_query_field(self) -> None:
        # Arrange & Act
        req = ChatRequest(query="Elden Ring")

        # Assert
        assert req.query == "Elden Ring"
        assert req.message is None

    def test_dto_accepts_message_alias_and_normalizes_to_query(self) -> None:
        # Arrange & Act
        req = ChatRequest(message="¿Tienen juegos de acción?")

        # Assert
        assert req.query == "¿Tienen juegos de acción?"

    def test_dto_prioritizes_query_when_both_present(self) -> None:
        # Arrange & Act
        req = ChatRequest(query="Cyberpunk 2077", message="Otro juego")

        # Assert
        assert req.query == "Cyberpunk 2077"

    @pytest.mark.parametrize("invalid_value", ["", "   ", "\t\n"])
    def test_dto_rejects_empty_or_whitespace_query_and_message(self, invalid_value: str) -> None:
        # Act & Assert
        with pytest.raises(ValidationError):
            ChatRequest(query=invalid_value)

        with pytest.raises(ValidationError):
            ChatRequest(message=invalid_value)

    def test_dto_raises_validation_error_when_neither_query_nor_message_provided(self) -> None:
        # Act & Assert
        with pytest.raises(ValidationError):
            ChatRequest()

    def test_dto_to_chat_messages_converts_history_robustly(self) -> None:
        # Arrange
        req = ChatRequest(
            query="Hola",
            chat_history=[
                {"role": "user", "content": "Buenas"},
                {"role": "assistant", "content": "¡Hola! ¿Qué buscas?"},
                {"role": "invalid_extra"},  # Campo content ausente
            ],
        )

        # Act
        messages = req.to_chat_messages()

        # Assert
        assert len(messages) == 3
        assert all(isinstance(m, ChatMessage) for m in messages)
        assert messages[0].content == "Buenas"
        assert messages[1].content == "¡Hola! ¿Qué buscas?"
        assert messages[2].content == ""


# =============================================================================
# [SDD-SPEC-AI-03]: RESILIENCIA Y CONTENCIÓN DE EXCEPCIONES EN STREAMING
# =============================================================================
class TestSDDSpecAI03ResilientDegradation:
    """[SDD-SPEC-AI-03]: Criterio de Aceptación:
    Si el motor LLM (Groq) arroja una excepción (Rate Limit 429, APIConnectionError),
    el servicio no debe crashear la respuesta HTTP/SSE; debe degradar graciosamente
    al fallback contextual relativo al input y finalizar con 'done'.
    """

    @pytest.mark.asyncio
    async def test_chat_stream_contains_groq_rate_limit_and_yields_fallback(
        self,
        mock_embedding_port: AsyncMock,
        mock_vector_store_port: AsyncMock,
    ) -> None:
        # Arrange: LLM falla con excepción simulada de Rate Limit 429
        failing_llm = MagicMock()

        async def throw_429(*args, **kwargs):
            raise RuntimeError("Error code: 429 - Rate limit reached for model openai/gpt-oss-20b")
            yield "never_reached"

        failing_llm.generate_stream = MagicMock(side_effect=throw_429)

        service = AssistantService(
            embedding_port=mock_embedding_port,
            llm_port=failing_llm,
            vector_store_port=mock_vector_store_port,
        )

        # Act: Ejecución de chat_stream sobre una pregunta que dispara el fallback
        query = "¿Tienes hambre?"
        chunks: list[str] = []
        async for chunk in service.chat_stream(query):
            chunks.append(chunk)

        # Assert (SDD Anchor: Stream no se interrumpe y entrega los 3 eventos SSE requeridos)
        assert len(chunks) == 3  # products, token (fallback), done
        products_event = json.loads(chunks[0].replace("data: ", ""))
        token_event = json.loads(chunks[1].replace("data: ", ""))
        done_event = json.loads(chunks[2].replace("data: ", ""))

        assert products_event["type"] == "products"
        assert token_event["type"] == "token"
        assert done_event["type"] == "done"

        # Validar que el token del fallback es relativo al hambre y la IA
        token_text = token_event["data"].lower()
        assert "hambre" in token_text
        assert "inteligencia artificial" in token_text or "cuerpo biológico" in token_text
        assert "calibrando" not in token_text

    @pytest.mark.asyncio
    async def test_chat_method_gracefully_falls_back_on_graph_failure(
        self,
        mock_embedding_port: AsyncMock,
        mock_vector_store_port: AsyncMock,
    ) -> None:
        # Arrange
        failing_llm = MagicMock()
        service = AssistantService(
            embedding_port=mock_embedding_port,
            llm_port=failing_llm,
            vector_store_port=mock_vector_store_port,
        )
        # Forzar falla en ainvoke del grafo
        service._graph.ainvoke = AsyncMock(side_effect=RuntimeError("Graph state error"))

        # Act
        result = await service.chat("¿Cómo está el clima hoy?")

        # Assert (SDD Anchor: chat síncrono devuelve fallback relativo al clima)
        assert isinstance(result, str)
        assert "clima" in result.lower()
        assert "sensores meteorológicos" in result.lower() or "no puedo ver el clima" in result.lower()


# =============================================================================
# [SDD-SPEC-AI-04]: GUARDRAILS Y CONTRATO DEL SYSTEM PROMPT
# =============================================================================
class TestSDDSpecAI04SystemPromptGuardrails:
    """[SDD-SPEC-AI-04]: Criterio de Aceptación:
    El System Prompt inyectado en el LLM debe contener obligatoriamente las directivas
    de identidad, el principio universal de respuestas relativas al input, el formato
    en CLP ($X CLP) y la prohibición expresa de frases repetitivas.
    """

    def test_system_prompt_mandates_universal_input_relative_principle(self) -> None:
        prompt_upper = NEXUSBOT_SYSTEM_PROMPT.upper()

        assert "PRINCIPIO UNIVERSAL DE RESPUESTAS RECHAZADAS O FUERA DE DOMINIO" in prompt_upper
        assert "ALUSIÓN DIRECTA AL TEMA" in prompt_upper
        assert "EXPLICACIÓN TRANSPARENTE" in prompt_upper
        assert "PUENTE CREATIVO" in prompt_upper

    def test_system_prompt_explicitly_bans_robotic_calibrando_phrase(self) -> None:
        assert 'mi red neuronal se está calibrando' in NEXUSBOT_SYSTEM_PROMPT.lower()
        assert 'NUNCA' in NEXUSBOT_SYSTEM_PROMPT or 'nunca' in NEXUSBOT_SYSTEM_PROMPT.lower()

    def test_system_prompt_mandates_clp_currency_and_catalog_grounding(self) -> None:
        assert "CLP" in NEXUSBOT_SYSTEM_PROMPT
        assert "CATÁLOGO DISPONIBLE" in NEXUSBOT_SYSTEM_PROMPT


# =============================================================================
# [SDD-SPEC-AI-05]: CONTRATO DE INTEGRACIÓN HTTP EN ROUTER (/chat)
# =============================================================================
class TestSDDSpecAI05RouterContract:
    """[SDD-SPEC-AI-05]: Criterio de Aceptación:
    El endpoint POST /api/v1/assistant/chat debe aceptar tanto 'query' como 'message'
    vía HTTP, responder con Content-Type: text/event-stream y rechazar queries vacías.
    """

    @pytest.mark.asyncio
    async def test_router_accepts_message_alias_payload(
        self,
        async_client,
        mock_assistant_service: MagicMock,
    ) -> None:
        from nexus_backend.ai_assistant.presentation.router import _get_assistant_service
        from nexus_backend.main import app

        app.dependency_overrides[_get_assistant_service] = lambda: mock_assistant_service
        try:
            payload = {"message": "¿Tienes ofertas de juegos?"}
            response = await async_client.post("/api/v1/assistant/chat", json=payload)

            assert response.status_code == 200
            assert "text/event-stream" in response.headers["content-type"]
            assert mock_assistant_service.chat_stream.called
        finally:
            app.dependency_overrides.pop(_get_assistant_service, None)

    @pytest.mark.asyncio
    async def test_router_rejects_whitespace_payload_with_422(
        self,
        async_client,
    ) -> None:
        # Arrange
        invalid_payload = {"message": "   "}

        # Act
        response = await async_client.post("/api/v1/assistant/chat", json=invalid_payload)

        # Assert
        assert response.status_code == 422
