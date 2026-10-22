"""Pruebas unitarias para LayaDecisionAdapter (Open Source System 1 Decision Engine)."""

from unittest.mock import MagicMock
import pytest

from nexus_backend.ai_assistant.infrastructure.laya_adapter import (
    DEFAULT_ROUTER_CRITERIA,
    LayaDecisionAdapter,
)


class TestLayaDecisionAdapter:
    @pytest.mark.asyncio
    async def test_classify_intent_via_router_mock(self) -> None:
        adapter = LayaDecisionAdapter(use_heuristics_fallback=False)
        mock_router = MagicMock()
        mock_router.invoke.return_value = "stock_price"
        adapter._router = mock_router
        adapter._initialized = True

        intent = await adapter.classify_intent("¿Cuánto cuesta Cyberpunk?")

        assert intent == "stock_price"
        mock_router.invoke.assert_called_once_with("¿Cuánto cuesta Cyberpunk?")

    @pytest.mark.asyncio
    async def test_classify_intent_heuristic_fallback(self) -> None:
        adapter = LayaDecisionAdapter(use_heuristics_fallback=True)
        # Forzamos _router a None
        adapter._router = None
        adapter._initialized = True

        greeting_intent = await adapter.classify_intent("Hola, buenos días")
        assert greeting_intent == "greeting"

        price_intent = await adapter.classify_intent("¿Tienen stock disponible y cuál es el precio?")
        assert price_intent == "stock_price"

        rec_intent = await adapter.classify_intent("Recomiéndame juegos de acción tipo dark souls")
        assert rec_intent == "recommendation"

    @pytest.mark.asyncio
    async def test_evaluate_decision_returns_system1_metrics(self) -> None:
        adapter = LayaDecisionAdapter(use_heuristics_fallback=True)
        adapter._router = None
        adapter._initialized = True

        metrics = await adapter.evaluate_decision("Hola amigo")

        assert metrics["intent"] == "greeting"
        assert metrics["need_trivia"] is False
        assert "laya-ai" in metrics["engine"]

    @pytest.mark.asyncio
    async def test_classify_intent_and_extract_email(self) -> None:
        adapter = LayaDecisionAdapter(use_heuristics_fallback=True)
        adapter._router = None
        adapter._initialized = True

        query = "Envíame las ofertas de Elden Ring a gamer123@gmail.com por favor"
        metrics = await adapter.evaluate_decision(query)

        assert metrics["intent"] == "send_email"
        assert metrics["recipient_email"] == "gamer123@gmail.com"
        assert metrics["need_trivia"] is True


