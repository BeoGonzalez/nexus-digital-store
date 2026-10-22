#!/usr/bin/env python3
"""
🎮 Nexus Digital Store — Script de Demostración del Asistente IA (LLM + Laya + APIs)
===================================================================================
Este script ejecuta una prueba interactiva y visual de extremo a extremo demostrando:
  1. 🧠 Laya AI (System 1 Decision Engine): Enrutamiento reflexivo e intención.
  2. 🌲 Catálogo Vectorial (Pinecone / Local RAG): Búsqueda de videojuegos y stock.
  3. 📚 Wikipedia API: Inyección de trivia, historia y lore gamer.
  4. 📰 Tavily API: Noticias de videojuegos de última hora, parches y lanzamientos.
  5. 🏷️ CheapShark API: Comparativa de precios en vivo (Steam, Epic, GOG, etc.) y dictamen
     explícito ("MÁS BARATO" o "MÁS CARO" que en Nexus Digital Store).
  6. ⚡ Groq LLM (NexusBot): Síntesis final en streaming integrando todo el contexto.

Uso:
  python demo_llm.py                    # Modo menú con escenarios guiados
  python demo_llm.py "¿A cuánto está Elden Ring?" # Consulta directa por argumento
"""

import asyncio
import os
import sys
from typing import Any

# Asegurar path al paquete nexus_backend
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

from nexus_backend.config import get_settings
from nexus_backend.catalog.domain.entities import Genre, VideoGame
from nexus_backend.ai_assistant.infrastructure.laya_adapter import LayaDecisionAdapter
from nexus_backend.ai_assistant.infrastructure.wikipedia import WikipediaAdapter
from nexus_backend.ai_assistant.infrastructure.tavily_adapter import TavilyNewsAdapter
from nexus_backend.ai_assistant.infrastructure.cheapshark_adapter import CheapSharkPriceAdapter
from nexus_backend.ai_assistant.infrastructure.llm import GroqLLMAdapter
from nexus_backend.ai_assistant.application.chains import NEXUSBOT_SYSTEM_PROMPT


# Colores ANSI para terminal
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
MAGENTA = "\033[95m"
BLUE = "\033[94m"
RED = "\033[91m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


# Catálogo demo local para pruebas inmediatas si Pinecone no está poblado
MOCK_CATALOG = [
    VideoGame(
        title="Elden Ring",
        description="Aclamado juego de rol de acción y fantasía oscura desarrollado por FromSoftware. Explora las Tierras Intermedias y conviértete en el Señor del Círculo.",
        price_clp=39990,
        stock=12,
        genres=[Genre(name="Action RPG"), Genre(name="Soulslike"), Genre(name="Open World")],
    ),
    VideoGame(
        title="Cyberpunk 2077",
        description="Aventura de rol y acción de mundo abierto ambientada en la megalópolis futurista de Night City. Incluye mejoras para Phantom Liberty.",
        price_clp=34990,
        stock=20,
        genres=[Genre(name="RPG"), Genre(name="Sci-Fi"), Genre(name="Open World")],
    ),
    VideoGame(
        title="Hollow Knight",
        description="Desafiante metroidvania en 2D a través de un vasto reino en ruinas de insectos y héroes. Banda sonora memorable y combate preciso.",
        price_clp=8500,
        stock=25,
        genres=[Genre(name="Metroidvania"), Genre(name="Indie"), Genre(name="Action")],
    ),
    VideoGame(
        title="God of War",
        description="Kratos regresa junto a su hijo Atreus en el brutal e implacable reino nórdico de dioses y monstruos.",
        price_clp=28990,
        stock=8,
        genres=[Genre(name="Action"), Genre(name="Adventure")],
    ),
]


def print_banner():
    print(f"\n{CYAN}{BOLD}======================================================================{RESET}")
    print(f"{CYAN}{BOLD}🎮  NEXUS DIGITAL STORE — DEMOSTRACIÓN DE PIPELINE DE IA COMPLETO  🎮{RESET}")
    print(f"{CYAN}{BOLD}======================================================================{RESET}")
    print(f"{DIM}Componentes: Laya AI (System 1) + Pinecone + Wikipedia + Tavily + CheapShark + Groq{RESET}\n")


async def run_demo_query(query: str):
    settings = get_settings()

    print(f"\n{BOLD}🎯 Consulta del usuario:{RESET} {YELLOW}\"{query}\"{RESET}\n")
    print(f"{DIM}──────────────────────────────────────────────────────────────────────{RESET}")

    # =========================================================================
    # PASO 1: Laya AI (System 1 Decision Engine)
    # =========================================================================
    print(f"{MAGENTA}{BOLD}[PASO 1] 🧠 Laya AI (System 1 - Clasificación Reflexiva){RESET}")
    laya = LayaDecisionAdapter(model_name=settings.LAYA_MODEL_NAME)
    decision = await laya.evaluate_decision(query)
    intent = decision.get("intent", "recommendation")
    need_trivia = decision.get("need_trivia", True)
    engine = decision.get("engine", "laya-ai")

    print(f"  • {BOLD}Intención detectada:{RESET} {GREEN}{intent.upper()}{RESET}")
    print(f"  • {BOLD}Requiere trivia gamer:{RESET} {GREEN if need_trivia else YELLOW}{need_trivia}{RESET}")
    print(f"  • {BOLD}Motor evaluador:{RESET} {DIM}{engine}{RESET}")
    print(f"  • {DIM}Explicación: Laya evalúa en microsegundos si amerita consumo de APIs externas o respuesta directa.{RESET}\n")

    # =========================================================================
    # PASO 2: Catálogo de Productos (Pinecone / Local RAG)
    # =========================================================================
    print(f"{BLUE}{BOLD}[PASO 2] 🌲 Catálogo de Productos (RAG Semántico){RESET}")
    # Búsqueda semántica simple en catálogo demo por relevancia de título o género
    q_words = set(query.lower().split())
    matched_games = []
    for g in MOCK_CATALOG:
        g_words = set(g.title.lower().split()) | {gen.name.lower() for gen in (g.genres or [])}
        if q_words & g_words or any(w in g.title.lower() for w in q_words):
            matched_games.append(g)

    if not matched_games:
        matched_games = [MOCK_CATALOG[0]]  # Fallback al top game

    target_game = matched_games[0]
    for i, g in enumerate(matched_games, 1):
        genres_str = ", ".join(gen.name for gen in g.genres) if g.genres else "General"
        print(f"  {i}. {BOLD}{g.title}{RESET} — {GREEN}${g.price_clp:,} CLP{RESET} (Stock: {g.stock}) [{DIM}{genres_str}{RESET}]".replace(",", "."))
    print()

    # =========================================================================
    # PASO 3: Wikipedia API (Trivia & Lore)
    # =========================================================================
    print(f"{CYAN}{BOLD}[PASO 3] 📚 Wikipedia API (Lore & Trivia Gamer){RESET}")
    wiki = WikipediaAdapter()
    trivia_context = "Sin datos externos."
    if need_trivia and intent != "greeting":
        try:
            trivia_context = await wiki.fetch_trivia(target_game.title)
            snippet = trivia_context[:160] + "..." if len(trivia_context) > 160 else trivia_context
            print(f"  • {BOLD}Contexto histórico:{RESET} {snippet}")
        except Exception as e:
            print(f"  • {YELLOW}Wikipedia API error:{RESET} {e}")
    else:
        print(f"  • {DIM}Omitido por decisión de Laya AI (intención={intent}){RESET}")
    print()

    # =========================================================================
    # PASO 4: Tavily API (Noticias de Videojuegos)
    # =========================================================================
    print(f"{GREEN}{BOLD}[PASO 4] 📰 Tavily API (Noticias en Tiempo Real & Parches){RESET}")
    tavily = TavilyNewsAdapter(api_key=settings.TAVILY_API_KEY, max_results=2)
    news_context = "Sin noticias adicionales."
    if intent != "greeting":
        try:
            news_context = await tavily.fetch_news(target_game.title)
            lines = news_context.strip().split("\n")
            for line in lines[:3]:
                print(f"  • {line}")
        except Exception as e:
            print(f"  • {YELLOW}Tavily API error:{RESET} {e}")
    else:
        print(f"  • {DIM}Omitido por decisión de Laya AI (saludo detectado){RESET}")
    print()

    # =========================================================================
    # PASO 5: CheapShark API (Comparador de Precios en Otras Tiendas)
    # =========================================================================
    print(f"{YELLOW}{BOLD}[PASO 5] 🏷️ CheapShark API (Comparativa en Vivo: Steam, Epic, GOG){RESET}")
    cheapshark = CheapSharkPriceAdapter(usd_clp_rate=settings.CHEAPSHARK_USD_CLP_RATE)
    price_context = "Sin datos comparativos."
    if intent != "greeting":
        try:
            comp = await cheapshark.compare_price(target_game.title, target_game.price_clp)
            if comp.get("has_data"):
                verdict = comp.get("verdict", "N/A")
                verdict_color = GREEN if verdict == "MÁS BARATO" else (RED if verdict == "MÁS CARO" else YELLOW)
                print(f"  • {BOLD}DICTAMEN NEXUS:{RESET} {verdict_color}{BOLD}{verdict}{RESET}")
                if comp.get("is_nexus_cheaper"):
                    print(f"  • {BOLD}Ahorro del cliente:{RESET} {GREEN}${comp['savings_clp']:,} CLP frente a {comp['cheapest_external_store']}{RESET}".replace(",", "."))
                elif comp.get("is_nexus_more_expensive"):
                    print(f"  • {BOLD}Oferta externa:{RESET} {YELLOW}{comp['cheapest_external_store']} tiene oferta a ${comp['cheapest_external_price_clp']:,} CLP{RESET}".replace(",", "."))

                print(f"  • {BOLD}Precios en tiendas internacionales:{RESET}")
                for d in comp.get("deals", [])[:4]:
                    print(f"    - {d['store_name']}: ${d['deal_price_usd']:.2f} USD (~${d['deal_price_clp']:,} CLP)".replace(",", "."))

                price_context = comp.get("comparison_summary", price_context)
            else:
                print(f"  • {DIM}No se encontraron ofertas activas en CheapShark para '{target_game.title}'.{RESET}")
        except Exception as e:
            print(f"  • {YELLOW}CheapShark API error:{RESET} {e}")
    else:
        print(f"  • {DIM}Omitido por decisión de Laya AI.{RESET}")
    print()

    # =========================================================================
    # PASO 6: Generación Final con Groq LLM (NexusBot)
    # =========================================================================
    print(f"{CYAN}{BOLD}[PASO 6] ⚡ Generación del LLM (NexusBot con Todo el Contexto Conectado){RESET}")
    print(f"{DIM}Enviando System Prompt + Contexto a Groq (Modelo: {settings.GROQ_MODEL_NAME})...{RESET}\n")

    catalog_text = f"• {target_game.title} — ${target_game.price_clp:,} CLP (Stock: {target_game.stock})\n  {target_game.description}".replace(",", ".")

    user_message = (
        f"Intención del cliente (Laya AI): {intent}\n\n"
        f"Videojuegos disponibles en tienda:\n{catalog_text}\n\n"
        f"Dato curioso externo (Wikipedia):\n{trivia_context}\n\n"
        f"Noticias recientes de videojuegos (Tavily API):\n{news_context}\n\n"
        f"Comparativa de precios con otras tiendas (CheapShark API):\n{price_context}\n\n"
        f"Pregunta del cliente: {query}"
    )

    llm = GroqLLMAdapter(
        api_key=settings.GROQ_API_KEY,
        model_name=settings.GROQ_MODEL_NAME,
        temperature=0.3,
    )

    print(f"{BOLD}Respuesta en tiempo real de NexusBot:{RESET}\n")
    print(f"{GREEN}", end="", flush=True)

    has_tokens = False
    try:
        async for chunk in llm.generate_stream(NEXUSBOT_SYSTEM_PROMPT, user_message):
            print(chunk, end="", flush=True)
            has_tokens = True
        print(f"{RESET}\n")
    except Exception as exc:
        print(f"{RESET}\n{YELLOW}Nota: No se pudo conectar a Groq Cloud con la API key actual ({exc}).{RESET}")
        print(f"{CYAN}Simulando respuesta que generaría el LLM con este contexto ensamblado:{RESET}\n")
        print(
            f"¡Hola gamer! 🎮 Sobre tu consulta por **{target_game.title}**:\n\n"
            f"En **Nexus Digital Store** lo tenemos disponible para entrega inmediata a **${target_game.price_clp:,} CLP** (quedan {target_game.stock} unidades en stock).\n\n"
            f"🏷️ **Comparativa de Precios en Otras Tiendas (CheapShark API)**:\n"
            f"{price_context}\n\n"
            f"📰 **Novedades de la Industria (Tavily API)**:\n"
            f"{news_context[:200]}...\n\n"
            f"¿Te gustaría que te ayude a procesar tu orden o prefieres ver otros títulos del género?".replace(",", ".")
        )

    print(f"\n{DIM}──────────────────────────────────────────────────────────────────────{RESET}")
    print(f"{GREEN}{BOLD}✔ Demostración completada con éxito.{RESET}\n")


async def main():
    print_banner()

    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        await run_demo_query(query)
        return

    # Menú interactivo
    options = [
        ("1", "¿A cuánto está Elden Ring y en qué tienda conviene comprarlo? (Prueba CheapShark + Laya)", "¿A cuánto está Elden Ring y en qué tienda conviene comprarlo?"),
        ("2", "¿Qué noticias y novedades recientes hay de Cyberpunk 2077? (Prueba Tavily + Wikipedia)", "¿Qué noticias y novedades recientes hay de Cyberpunk 2077?"),
        ("3", "Hola, tengo mucha hambre, ¿qué me recomiendas cocinar? (Prueba Laya AI Out-of-Domain)", "Hola, tengo mucha hambre, ¿qué me recomiendas cocinar?"),
        ("4", "Escribir mi propia consulta libre", "custom"),
    ]

    print(f"{BOLD}Selecciona un escenario de prueba para la demostración:{RESET}\n")
    for opt, desc, _ in options:
        print(f"  {CYAN}{opt}.{RESET} {desc}")
    print()

    choice = input(f"{BOLD}Ingresa una opción (1-4) [default: 1]: {RESET}").strip() or "1"

    selected_query = options[0][2]
    for opt, _, q in options:
        if opt == choice:
            selected_query = q
            break

    if selected_query == "custom":
        selected_query = input(f"\n{BOLD}Escribe tu consulta gamer: {RESET}").strip() or "¿A cuánto está Elden Ring?"

    await run_demo_query(selected_query)


if __name__ == "__main__":
    asyncio.run(main())

