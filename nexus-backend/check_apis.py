import asyncio
import time
from dotenv import load_dotenv

load_dotenv()
from nexus_backend.config import get_settings
from nexus_backend.ai_assistant.infrastructure.cheapshark_adapter import CheapSharkPriceAdapter
from nexus_backend.ai_assistant.infrastructure.tavily_adapter import TavilyNewsAdapter


async def test_apis():
    settings = get_settings()
    print("========================================")
    print("🧪 DIAGNÓSTICO EN VIVO DE APIS EXTERNAS")
    print("========================================")

    # 1. CHEAPSHARK API
    print("\n[1/2] 🏷️ Probando CheapShark API...")
    t0 = time.time()
    cheapshark = CheapSharkPriceAdapter(usd_clp_rate=settings.CHEAPSHARK_USD_CLP_RATE)
    game_title = "Elden Ring"
    nexus_price = 39990
    try:
        res_cheap = await cheapshark.compare_price(game_title, nexus_price)
        dt_cheap = time.time() - t0
        print(f"  ✔ CheapShark respondió en {dt_cheap:.2f}s")
        print(f"  • Has data: {res_cheap.get('has_data')}")
        print(f"  • Dictamen: {res_cheap.get('verdict')}")
        print(f"  • Mejor oferta externa: {res_cheap.get('cheapest_external_store')} - ${res_cheap.get('cheapest_external_price_clp')} CLP")
        deals = res_cheap.get("deals", [])
        print(f"  • Ofertas encontradas: {len(deals)}")
        for d in deals[:4]:
            print(f"     - {d['store_name']}: ${d['deal_price_usd']:.2f} USD (~${d['deal_price_clp']:,} CLP)".replace(",", "."))
    except Exception as e:
        print(f"  ❌ Error en CheapShark: {e}")

    # 2. TAVILY API
    print("\n[2/2] 📰 Probando Tavily AI Search API...")
    t0 = time.time()
    tavily = TavilyNewsAdapter(api_key=settings.TAVILY_API_KEY, max_results=2)
    try:
        news_res = await tavily.fetch_news(game_title)
        dt_tavily = time.time() - t0
        print(f"  ✔ Tavily respondió en {dt_tavily:.2f}s")
        lines = [line for line in news_res.strip().split("\n") if line.strip()]
        print(f"  • Líneas recibidas: {len(lines)}")
        for l in lines[:4]:
            print(f"     {l[:110]}...")
    except Exception as e:
        print(f"  ❌ Error en Tavily: {e}")

    print("\n========================================")
    print("Diagnóstico completado exitosamente.")


if __name__ == "__main__":
    asyncio.run(test_apis())

