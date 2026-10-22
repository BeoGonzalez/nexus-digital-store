"""Pruebas unitarias para las integraciones de Tavily API y CheapShark API en el Asistente IA."""

from unittest.mock import AsyncMock, MagicMock
import httpx
import pytest

from nexus_backend.ai_assistant.application.services import AssistantService
from nexus_backend.ai_assistant.domain.ports import GamingNewsPort, PriceComparisonPort
from nexus_backend.ai_assistant.infrastructure.cheapshark_adapter import CheapSharkPriceAdapter
from nexus_backend.ai_assistant.infrastructure.tavily_adapter import TavilyNewsAdapter
from nexus_backend.catalog.domain.entities import VideoGame


class TestCheapSharkPriceAdapter:
    """Pruebas unitarias para el adaptador de CheapShark."""

    @pytest.mark.asyncio
    async def test_compare_price_when_disabled(self) -> None:
        adapter = CheapSharkPriceAdapter(enabled=False)
        result = await adapter.compare_price("Elden Ring", 40000)
        assert result["has_data"] is False
        assert "Sin datos" in result["comparison_summary"]

    @pytest.mark.asyncio
    async def test_compare_price_empty_title(self) -> None:
        adapter = CheapSharkPriceAdapter(enabled=True)
        result = await adapter.compare_price("", 40000)
        assert result["has_data"] is False

    @pytest.mark.asyncio
    async def test_compare_price_nexus_is_cheaper(self) -> None:
        # Mock responses de CheapShark:
        # 1. /games?title=Elden+Ring -> lista con gameID "1234"
        # 2. /games?id=1234 -> objeto con deals en Steam (storeID "1") a $59.99 USD ($59,990 CLP)
        # Precio Nexus: $39,990 CLP -> Nexus es MÁS BARATO por $20,000 CLP
        games_response = MagicMock(spec=httpx.Response)
        games_response.status_code = 200
        games_response.json.return_value = [{"gameID": "1234", "external": "Elden Ring", "cheapest": "59.99"}]

        deal_response = MagicMock(spec=httpx.Response)
        deal_response.status_code = 200
        deal_response.json.return_value = {
            "info": {"title": "Elden Ring"},
            "deals": [
                {
                    "storeID": "1",
                    "price": "59.99",
                    "retailPrice": "59.99",
                    "savings": "0.0",
                }
            ],
        }

        mock_client = AsyncMock(spec=httpx.AsyncClient)

        async def mock_get(url, **kwargs):
            if "games" in url and kwargs.get("params", {}).get("id") == "1234":
                return deal_response
            return games_response

        mock_client.get = AsyncMock(side_effect=mock_get)

        adapter = CheapSharkPriceAdapter(usd_clp_rate=1000.0, client=mock_client)
        result = await adapter.compare_price("Elden Ring", 39990)

        assert result["has_data"] is True
        assert result["verdict"] == "MÁS BARATO"
        assert "MÁS BARATO" in result["comparison_summary"]
        assert "Steam" in result["comparison_summary"]
        assert result["savings_clp"] > 0

    @pytest.mark.asyncio
    async def test_compare_price_nexus_is_more_expensive(self) -> None:
        # Oferta externa a $19.99 USD ($19,990 CLP) en Steam
        # Precio Nexus: $35,000 CLP -> Nexus está más caro
        games_response = MagicMock(spec=httpx.Response)
        games_response.status_code = 200
        games_response.json.return_value = [{"gameID": "5678", "external": "Cyberpunk 2077", "cheapest": "19.99"}]

        deal_response = MagicMock(spec=httpx.Response)
        deal_response.status_code = 200
        deal_response.json.return_value = {
            "info": {"title": "Cyberpunk 2077"},
            "deals": [
                {
                    "storeID": "1",
                    "price": "19.99",
                    "retailPrice": "59.99",
                    "savings": "66.6",
                }
            ],
        }

        mock_client = AsyncMock(spec=httpx.AsyncClient)

        async def mock_get(url, **kwargs):
            if "games" in url and kwargs.get("params", {}).get("id") == "5678":
                return deal_response
            return games_response

        mock_client.get = AsyncMock(side_effect=mock_get)

        adapter = CheapSharkPriceAdapter(usd_clp_rate=1000.0, client=mock_client)
        result = await adapter.compare_price("Cyberpunk 2077", 35000)

        assert result["has_data"] is True
        assert result["verdict"] == "MÁS CARO"
        assert "oferta especial" in result["comparison_summary"] or "Steam" in result["comparison_summary"]

    @pytest.mark.asyncio
    async def test_compare_price_api_error_fallback(self) -> None:
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.get = AsyncMock(side_effect=httpx.RequestError("Timeout"))

        adapter = CheapSharkPriceAdapter(client=mock_client)
        result = await adapter.compare_price("Doom", 20000)

        assert result["has_data"] is False
        assert "Sin datos" in result["comparison_summary"]


class TestTavilyNewsAdapter:
    """Pruebas unitarias para el adaptador de noticias de Tavily."""

    @pytest.mark.asyncio
    async def test_fetch_news_without_api_key(self) -> None:
        adapter = TavilyNewsAdapter(api_key="")
        result = await adapter.fetch_news("Elden Ring")
        assert "API Key no configurada" in result

    @pytest.mark.asyncio
    async def test_fetch_news_success(self) -> None:
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {
                    "title": "Elden Ring DLC Shadow of the Erdtree Update",
                    "content": "FromSoftware lanzó un nuevo parche con mejoras de balance.",
                    "url": "https://ign.com/elden-ring-patch",
                }
            ]
        }

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.post = AsyncMock(return_value=mock_response)

        adapter = TavilyNewsAdapter(api_key="test-key", max_results=2, client=mock_client)
        result = await adapter.fetch_news("Elden Ring")

        assert "Elden Ring DLC Shadow of the Erdtree" in result
        assert "FromSoftware lanzó un nuevo parche" in result

    @pytest.mark.asyncio
    async def test_fetch_news_error_handling(self) -> None:
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.post = AsyncMock(side_effect=httpx.HTTPError("Conn error"))

        adapter = TavilyNewsAdapter(api_key="test-key", client=mock_client)
        result = await adapter.fetch_news("Elden Ring")

        assert "Sin noticias" in result


class TestAssistantServiceWithAdapters:
    """Pruebas de integración del AssistantService inyectando noticias y comparativas."""

    @pytest.fixture(autouse=True)
    def mock_crew(self, monkeypatch: pytest.MonkeyPatch) -> None:
        async def fake_crew(*args, **kwargs):
            return "Análisis simulado."

        monkeypatch.setattr(
            "nexus_backend.ai_assistant.application.services.run_nexus_crew",
            fake_crew,
        )
        monkeypatch.setattr(
            "nexus_backend.ai_assistant.application.graph.run_nexus_crew",
            fake_crew,
        )

    @pytest.mark.asyncio
    async def test_chat_stream_incorporates_news_and_price_comparison(
        self,
        mock_embedding_port: AsyncMock,
        mock_vector_store_port: AsyncMock,
        mock_llm_port: MagicMock,
        dummy_video_game: VideoGame,
    ) -> None:
        mock_vector_store_port.similarity_search.return_value = [dummy_video_game]

        mock_news = AsyncMock(spec=GamingNewsPort)
        mock_news.fetch_news.return_value = "Nuevo parche 1.12 disponible para Elden Ring."

        mock_price = AsyncMock(spec=PriceComparisonPort)
        mock_price.compare_price.return_value = {
            "has_data": True,
            "verdict": "MÁS BARATO",
            "comparison_summary": "¡En Nexus Digital Store está MÁS BARATO que en Steam por $10.000 CLP!",
        }

        service = AssistantService(
            embedding_port=mock_embedding_port,
            llm_port=mock_llm_port,
            vector_store_port=mock_vector_store_port,
            gaming_news_port=mock_news,
            price_comparison_port=mock_price,
        )

        chunks = []
        async for chunk in service.chat_stream("¿A cuánto está Elden Ring comparado con otras tiendas?"):
            chunks.append(chunk)

        assert len(chunks) > 0
        mock_news.fetch_news.assert_called_once()
        mock_price.compare_price.assert_called_once()

        # Verificar que el LLM recibió las secciones de noticias y precios
        call_args = mock_llm_port.generate_stream.call_args
        user_message_arg = call_args[0][1]
        assert "Tavily API" in user_message_arg
        assert "CheapShark API" in user_message_arg
        assert "MÁS BARATO" in user_message_arg

