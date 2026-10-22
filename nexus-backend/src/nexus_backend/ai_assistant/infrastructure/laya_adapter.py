"""Adaptador de infraestructura para Laya AI (Open Source System 1 Decision Engine)."""

import asyncio
import logging
import re
from typing import Any

from nexus_backend.ai_assistant.domain.ports import DecisionEnginePort
from nexus_backend.config import get_settings

logger = logging.getLogger(__name__)

DEFAULT_ROUTER_CRITERIA = {
    "recommendation": "El usuario busca recomendaciones de videojuegos, novedades, opiniones o sugerencias de qué jugar.",
    "stock_price": "El usuario pregunta específicamente por el precio, descuento, disponibilidad o stock de un videojuego en particular.",
    "send_email": "El usuario solicita explícitamente enviar por correo electrónico información, resumen, ofertas o recomendaciones.",
    "greeting": "El usuario saluda (hola, buenos días, qué tal), se despide o expresa cortesía básica.",
    "support": "El usuario consulta por pedidos, compras previas, medios de pago, soporte o temas fuera de catálogo.",
}


class LayaDecisionAdapter(DecisionEnginePort):
    """Adaptador que encapsula Laya AI para toma de decisiones reflexivas y enrutamiento 'System 1'."""

    def __init__(
        self,
        criteria: dict[str, str] | None = None,
        model_name: str | None = None,
        fallback_intent: str = "recommendation",
        use_heuristics_fallback: bool = True,
    ) -> None:
        settings = get_settings()
        self._criteria = criteria or DEFAULT_ROUTER_CRITERIA
        self._model_name = model_name or settings.LAYA_MODEL_NAME
        self._fallback_intent = fallback_intent
        self._use_heuristics = use_heuristics_fallback
        self._router: Any = None
        self._initialized = False

    def _init_router_if_needed(self) -> None:
        if self._initialized:
            return
        self._initialized = True
        settings = get_settings()
        if not settings.ENABLE_LAYA_DECISION_ENGINE:
            return

        try:
            try:
                from laya import LayaRouter
            except ImportError:
                from laya.integrations.langchain import LayaRouter
            self._router = LayaRouter(
                criteria=self._criteria,
                fallback=self._fallback_intent,
                model=self._model_name,
            )
            logger.info("Laya AI Decision Engine inicializado correctamente con modelo %s", self._model_name)
        except Exception as exc:
            logger.warning("No se pudo instanciar LayaRouter, usando fallback: %s", exc)
            self._router = None

    def _heuristic_classify(self, query: str) -> str:
        q = query.strip().lower()
        # Envío de correo electrónico (prioritario si contiene dirección o intención de envío)
        if any(w in q for w in ["enviar correo", "mandar correo", "enviame un correo", "mandame un correo", "al correo", "a mi correo", "al mail", "a mi email", "enviame el mail", "mandame el correo"]) or ("@" in q and any(w in q for w in ["enviar", "manda", "envia", "mail", "correo"])):
            return "send_email"
        # Saludos
        if any(w in q for w in ["hola", "buenos dias", "buenas tardes", "buenas noches", "hey", "saludos", "chao", "adios"]):
            if len(q.split()) <= 4:
                return "greeting"
        # Precios / stock
        if any(w in q for w in ["precio", "cuanto vale", "cuanto cuesta", "stock", "tienen unidades", "disponible"]):
            return "stock_price"
        # Soporte
        if any(w in q for w in ["mi pedido", "mi orden", "devolucion", "reembolso", "factura", "tarjeta", "pago fallido"]):
            return "support"
        return "recommendation"

    async def classify_intent(self, query: str) -> str:
        if not query:
            return self._fallback_intent

        loop = asyncio.get_running_loop()

        def _run_classification() -> str:
            self._init_router_if_needed()
            if self._router:
                try:
                    decision = self._router.invoke(query)
                    if decision in self._criteria:
                        return decision
                except Exception as e:
                    logger.debug("LayaRouter invoke error: %s, falling back to heuristics", e)
            if self._use_heuristics:
                return self._heuristic_classify(query)
            return self._fallback_intent

        return await loop.run_in_executor(None, _run_classification)

    async def evaluate_decision(self, query: str) -> dict:
        intent = await self.classify_intent(query)
        need_trivia = intent in ("recommendation", "stock_price", "send_email")
        urgency = 2 if intent in ("stock_price", "send_email") else 1

        email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", query)
        recipient_email = email_match.group(0) if email_match else None

        return {
            "intent": intent,
            "need_trivia": need_trivia,
            "urgency": urgency,
            "engine": "laya-ai (system-1)",
            "recipient_email": recipient_email,
        }

