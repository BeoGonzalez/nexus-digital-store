"""Adaptador para análisis y comparativa de precios de videojuegos mediante CheapShark API."""

import logging
from typing import Any

import httpx

from nexus_backend.ai_assistant.domain.ports import PriceComparisonPort
from nexus_backend.config import get_settings

logger = logging.getLogger(__name__)

# Mapa conocido de tiendas principales en CheapShark
DEFAULT_STORE_NAMES: dict[str, str] = {
    "1": "Steam",
    "2": "GamersGate",
    "3": "GreenManGaming",
    "7": "GOG",
    "11": "Humble Store",
    "13": "Uplay / Ubisoft Connect",
    "15": "Fanatical",
    "21": "WinGameStore",
    "23": "GameBillet",
    "25": "Epic Games Store",
    "27": "Gamesplanet",
    "30": "IndieGala",
    "31": "Blizzard Shop",
}


class CheapSharkPriceAdapter(PriceComparisonPort):
    """Cliente asíncrono para comparar precios de Nexus Digital Store contra tiendas globales (Steam, Epic, GOG, etc.)."""

    def __init__(
        self,
        enabled: bool | None = None,
        usd_to_clp_rate: float | None = None,
        usd_clp_rate: float | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        settings = get_settings()
        self._enabled = enabled if enabled is not None else settings.CHEAPSHARK_ENABLED
        rate = usd_clp_rate if usd_clp_rate is not None else usd_to_clp_rate
        self._usd_rate = rate or settings.CHEAPSHARK_USD_CLP_RATE
        self._client = client
        self._base_url = "https://www.cheapshark.com/api/1.0"
        self._headers = {
            "User-Agent": "NexusDigitalStore/1.0 (soporte@nexusdigital.store; comparador-gamer)",
        }
        self._store_cache: dict[str, str] = dict(DEFAULT_STORE_NAMES)

    async def _ensure_stores_cache(self, client: httpx.AsyncClient) -> None:
        """Descarga dinámicamente el listado de tiendas de CheapShark si no se ha inicializado."""
        if len(self._store_cache) > len(DEFAULT_STORE_NAMES):
            return
        try:
            res = await client.get(f"{self._base_url}/stores")
            if res.status_code == 200:
                stores_data = res.json()
                for s in stores_data:
                    store_id = str(s.get("storeID", ""))
                    store_name = s.get("storeName", "")
                    if store_id and store_name:
                        self._store_cache[store_id] = store_name
        except Exception as e:
            logger.debug("No se pudo actualizar catálogo de tiendas CheapShark: %s", e)

    async def _compare_with_client(
        self,
        client: httpx.AsyncClient,
        clean_title: str,
        nexus_price_clp: int,
        empty_result: dict[str, Any],
    ) -> dict[str, Any]:
        await self._ensure_stores_cache(client)

        # 1. Buscar coincidencias del título en CheapShark
        search_res = await client.get(
            f"{self._base_url}/games",
            params={"title": clean_title, "limit": "3"},
        )

        if search_res.status_code != 200:
            logger.debug("CheapShark search error %d para '%s'", search_res.status_code, clean_title)
            return empty_result

        games_found = search_res.json()
        if not games_found or not isinstance(games_found, list):
            return empty_result

        # Tomar la coincidencia más relevante
        target_game = games_found[0]
        game_id = target_game.get("gameID")
        canonical_title = target_game.get("external", clean_title)

        if not game_id:
            return empty_result

        # 2. Consultar todos los deals disponibles para ese juego
        deals_res = await client.get(
            f"{self._base_url}/games",
            params={"id": game_id},
        )

        if deals_res.status_code != 200:
            return empty_result

        deals_data = deals_res.json()
        raw_deals = deals_data.get("deals", [])
        if not raw_deals:
            return empty_result

        # 3. Procesar las ofertas de otras tiendas
        parsed_deals: list[dict[str, Any]] = []
        for d in raw_deals:
            store_id = str(d.get("storeID", ""))
            store_name = self._store_cache.get(store_id, f"Tienda #{store_id}")
            deal_price_usd = float(d.get("price", "0.0"))
            retail_price_usd = float(d.get("retailPrice", "0.0"))
            savings_pct = float(d.get("savings", "0.0"))

            deal_price_clp = int(round(deal_price_usd * self._usd_rate))
            retail_price_clp = int(round(retail_price_usd * self._usd_rate))

            parsed_deals.append({
                "store_name": store_name,
                "deal_price_usd": deal_price_usd,
                "retail_price_usd": retail_price_usd,
                "deal_price_clp": deal_price_clp,
                "retail_price_clp": retail_price_clp,
                "savings_pct": savings_pct,
            })

        # Ordenar por el precio más bajo externo
        parsed_deals.sort(key=lambda x: x["deal_price_clp"])
        cheapest_deal = parsed_deals[0]
        cheapest_external_price = cheapest_deal["deal_price_clp"]
        cheapest_store = cheapest_deal["store_name"]

        # 4. Determinar si en Nexus está más barato o más caro
        is_nexus_cheaper = nexus_price_clp < cheapest_external_price
        is_nexus_more_expensive = nexus_price_clp > cheapest_external_price
        diff_clp = abs(nexus_price_clp - cheapest_external_price)

        # 5. Generar resumen estructurado y transparente para el asistente
        summary_lines = [
            f"Comparativa de precios para '{canonical_title}':",
            f"• Precio en Nexus Digital Store: ${nexus_price_clp:,} CLP".replace(",", "."),
        ]

        if is_nexus_cheaper:
            pct_savings = round((diff_clp / cheapest_external_price) * 100) if cheapest_external_price else 0
            summary_lines.append(
                f"• DICTAMEN: ¡En Nexus Digital Store está MÁS BARATO que en {cheapest_store}! "
                f"El cliente ahorra ${diff_clp:,} CLP ({pct_savings}% menos que los ${cheapest_external_price:,} CLP de {cheapest_store}).".replace(",", ".")
            )
            verdict = "MÁS BARATO"
        elif is_nexus_more_expensive:
            summary_lines.append(
                f"• DICTAMEN: En Nexus está a ${nexus_price_clp:,} CLP, mientras que en {cheapest_store} "
                f"está temporalmente en oferta especial a ${cheapest_external_price:,} CLP (diferencia de ${diff_clp:,} CLP).".replace(",", ".")
            )
            verdict = "MÁS CARO"
        else:
            summary_lines.append(
                f"• DICTAMEN: Precio equivalente al mejor precio del mercado (${cheapest_external_price:,} CLP en {cheapest_store}).".replace(",", ".")
            )
            verdict = "IGUAL PRECIO"

        summary_lines.append("• Precios de referencia en otras tiendas:")
        for deal in parsed_deals[:4]:
            p_usd = deal["deal_price_usd"]
            p_clp = deal["deal_price_clp"]
            store = deal["store_name"]
            summary_lines.append(f"  - {store}: ${p_usd:.2f} USD (~${p_clp:,} CLP)".replace(",", "."))

        comparison_summary = "\n".join(summary_lines)

        return {
            "game_title": canonical_title,
            "nexus_price_clp": nexus_price_clp,
            "has_data": True,
            "verdict": verdict,
            "is_nexus_cheaper": is_nexus_cheaper,
            "is_nexus_more_expensive": is_nexus_more_expensive,
            "cheapest_external_store": cheapest_store,
            "cheapest_external_price_clp": cheapest_external_price,
            "diff_clp": diff_clp,
            "savings_clp": diff_clp if is_nexus_cheaper else 0,
            "comparison_summary": comparison_summary,
            "deals": parsed_deals,
        }

    async def compare_price(self, game_title: str, nexus_price_clp: int) -> dict[str, Any]:
        """Compara el precio de un videojuego en Nexus con Steam, Epic Games, GOG y otras tiendas."""
        empty_result: dict[str, Any] = {
            "game_title": game_title,
            "nexus_price_clp": nexus_price_clp,
            "has_data": False,
            "is_nexus_cheaper": False,
            "is_nexus_more_expensive": False,
            "comparison_summary": "Sin datos comparativos de otras tiendas.",
            "deals": [],
        }

        if not self._enabled or not game_title or not game_title.strip():
            return empty_result

        clean_title = game_title.strip()

        try:
            if self._client:
                return await self._compare_with_client(self._client, clean_title, nexus_price_clp, empty_result)
            async with httpx.AsyncClient(timeout=8.0, headers=self._headers) as client:
                return await self._compare_with_client(client, clean_title, nexus_price_clp, empty_result)
        except Exception as exc:
            logger.debug("Fallo al comparar precios en CheapShark para '%s': %s", clean_title, exc)
            return empty_result

