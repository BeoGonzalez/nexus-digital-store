"""Adaptador de alto rendimiento para análisis y comparativa de precios mediante CheapShark API."""

from __future__ import annotations

import logging
import re
from typing import Any

import httpx

from nexus_backend.ai_assistant.domain.ports import PriceComparisonPort
from nexus_backend.config import get_settings

logger = logging.getLogger(__name__)

# Catálogo completo precargado de tiendas de CheapShark para evitar llamadas de red redundantes
STORE_NAMES: dict[str, str] = {
    "1": "Steam",
    "2": "GamersGate",
    "3": "GreenManGaming",
    "4": "Amazon",
    "5": "GameStop",
    "6": "Direct2Drive",
    "7": "GOG",
    "8": "Origin / EA App",
    "11": "Humble Store",
    "13": "Ubisoft Connect",
    "15": "Fanatical",
    "21": "WinGameStore",
    "23": "GameBillet",
    "24": "Voidu",
    "25": "Epic Games Store",
    "27": "Gamesplanet",
    "28": "Gamesload",
    "29": "2Game",
    "30": "IndieGala",
    "31": "Blizzard Shop",
    "32": "AllYouPlay",
    "35": "DreamGame",
}


class CheapSharkPriceAdapter(PriceComparisonPort):
    """Cliente asíncrono optimizado para comparar precios de Nexus Digital Store contra Steam, Epic, GOG, etc."""

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
            "User-Agent": "NexusDigitalStore/2.0 (soporte@nexusdigital.store; comparador-gamer-ultrafast)",
        }
        self._store_cache: dict[str, str] = dict(STORE_NAMES)

    def _clean_game_title(self, raw_title: str) -> str:
        """Limpia el título eliminando coletillas o palabras de búsqueda comunes."""
        clean = raw_title.strip()
        # Eliminar frases de búsqueda en español si vinieron en el título
        clean = re.sub(
            r"(?i)\b(a cuanto esta|cuanto cuesta|precio de|ofertas de|en otras tiendas|en steam|en epic|juego|videojuego)\b",
            "",
            clean,
        ).strip()
        # Eliminar caracteres extraños
        clean = re.sub(r"\s+", " ", clean).strip()
        return clean or raw_title.strip()

    async def _fetch_deals_direct(self, client: httpx.AsyncClient, title: str) -> list[dict[str, Any]]:
        """Consulta el endpoint /deals de CheapShark en 1 sola llamada ultrarrápida."""
        # 1. Intentar con el título limpio
        try:
            res = await client.get(
                f"{self._base_url}/deals",
                params={"title": title, "limit": 20},
            )
            if res.status_code == 200:
                data = res.json()
                if isinstance(data, list) and data and ("dealID" in data[0] or "salePrice" in data[0]):
                    return data
        except Exception as e:
            logger.debug("Error consultando /deals para '%s': %s", title, e)

        # 2. Si tiene subtítulo (ej: 'Cyberpunk 2077: Phantom Liberty' -> 'Cyberpunk 2077'), probar con la base
        if ":" in title or " - " in title:
            base_title = title.split(":")[0].split(" - ")[0].strip()
            if base_title and base_title != title:
                try:
                    res = await client.get(
                        f"{self._base_url}/deals",
                        params={"title": base_title, "limit": 20},
                    )
                    if res.status_code == 200:
                        data = res.json()
                        if isinstance(data, list) and data and ("dealID" in data[0] or "salePrice" in data[0]):
                            return data
                except Exception:
                    pass

        # 3. Fallback a /games?title=... si /deals no encontró directamente
        try:
            res = await client.get(
                f"{self._base_url}/games",
                params={"title": title, "limit": 3},
            )
            if res.status_code == 200:
                games_list = res.json()
                if isinstance(games_list, list) and games_list:
                    game_id = games_list[0].get("gameID")
                    if game_id:
                        g_res = await client.get(
                            f"{self._base_url}/games",
                            params={"id": game_id},
                        )
                        if g_res.status_code == 200:
                            g_data = g_res.json()
                            deals = g_data.get("deals", [])
                            # Adaptar formato de deals de /games al de /deals
                            return [
                                {
                                    "title": games_list[0].get("external", title),
                                    "storeID": str(d.get("storeID", "")),
                                    "salePrice": d.get("price", "0.0"),
                                    "normalPrice": d.get("retailPrice", "0.0"),
                                    "savings": d.get("savings", "0.0"),
                                }
                                for d in deals
                            ]
        except Exception:
            pass

        return []

    async def _compare_with_client(
        self,
        client: httpx.AsyncClient,
        clean_title: str,
        nexus_price_clp: int,
        empty_result: dict[str, Any],
    ) -> dict[str, Any]:
        raw_deals = await self._fetch_deals_direct(client, clean_title)
        if not raw_deals:
            return empty_result

        canonical_title = raw_deals[0].get("title", clean_title)

        parsed_deals: list[dict[str, Any]] = []
        seen_stores: set[str] = set()

        for d in raw_deals:
            store_id = str(d.get("storeID", ""))
            store_name = self._store_cache.get(store_id, f"Tienda #{store_id}")
            if store_name in seen_stores:
                continue
            seen_stores.add(store_name)

            deal_price_usd = float(d.get("salePrice") or d.get("price") or d.get("cheapest") or 0.0)
            retail_price_usd = float(d.get("normalPrice") or d.get("retailPrice") or deal_price_usd)
            savings_pct = float(d.get("savings") or 0.0)

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

        if not parsed_deals:
            return empty_result

        # Ordenar por el precio más bajo externo
        parsed_deals.sort(key=lambda x: x["deal_price_clp"])
        cheapest_deal = parsed_deals[0]
        cheapest_external_price = cheapest_deal["deal_price_clp"]
        cheapest_store = cheapest_deal["store_name"]

        # Determinar si en Nexus está más barato o más caro
        is_nexus_cheaper = nexus_price_clp < cheapest_external_price
        is_nexus_more_expensive = nexus_price_clp > cheapest_external_price
        diff_clp = abs(nexus_price_clp - cheapest_external_price)

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

        summary_lines.append("• Precios de referencia en tiendas internacionales:")
        for deal in parsed_deals[:5]:
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
        clean_title = self._clean_game_title(game_title)

        empty_result: dict[str, Any] = {
            "game_title": clean_title,
            "nexus_price_clp": nexus_price_clp,
            "has_data": False,
            "is_nexus_cheaper": False,
            "is_nexus_more_expensive": False,
            "comparison_summary": "Sin datos comparativos de otras tiendas.",
            "deals": [],
        }

        if not self._enabled or not clean_title:
            return empty_result

        try:
            if self._client:
                return await self._compare_with_client(self._client, clean_title, nexus_price_clp, empty_result)
            async with httpx.AsyncClient(timeout=12.0, headers=self._headers) as client:
                return await self._compare_with_client(client, clean_title, nexus_price_clp, empty_result)
        except Exception as exc:
            logger.debug("Fallo al comparar precios en CheapShark para '%s': %s", clean_title, exc)
            return empty_result
