#!/usr/bin/env python3
"""
🎮 Nexus Digital Store — Demostración del Pipeline de IA Completo y Envío de Correos
===================================================================================
Este script ejecuta de manera 100% local (sin Docker ni bases de datos requeridas)
el stack cognitivo completo de Nexus Digital Store:

  1. 🧠 Laya AI (System 1 Decision Engine): Enrutamiento reflexivo e intención ('send_email', 'recommendation', 'stock_price').
  2. 🌲 Catálogo de Productos (Local / Pinecone RAG): Búsqueda de videojuegos, stock y precios CLP.
  3. 📚 Wikipedia API: Inyección contextual de trivia, historia y cultura gamer.
  4. 📰 Tavily API: Noticias de última hora, parches y lanzamientos en tiempo real.
  5. 🏷️ CheapShark API: Comparativa de precios en vivo (Steam, Epic, GOG, etc.) con dictamen explícito ("MÁS BARATO" / "MÁS CARO").
  6. ⚡ Groq LLM (NexusBot): Generación en streaming integrando todo el contexto.
  7. 📧 Google Gmail SMTP: Envío de correos formateados en HTML Dark Gamer utilizando la Clave de Aplicación de Google.

Uso:
  python demo_llm.py                               # Menú interactivo guiado
  python demo_llm.py "¿A cuánto está Elden Ring?"  # Consulta directa por argumento
  python demo_llm.py "Recomiéndame juegos y envíame las ofertas a usuario@gmail.com"
"""

from __future__ import annotations

import asyncio
import os
import re
import sys
from typing import Any

# Asegurar path al paquete nexus_backend
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

from nexus_backend.config import get_settings
from nexus_backend.catalog.domain.entities import Genre, VideoGame
from nexus_backend.ai_assistant.infrastructure.embeddings import HuggingFaceEmbeddingAdapter
from nexus_backend.ai_assistant.infrastructure.pinecone_store import PineconeVectorStoreAdapter
from nexus_backend.ai_assistant.infrastructure.laya_adapter import LayaDecisionAdapter
from nexus_backend.ai_assistant.infrastructure.wikipedia import WikipediaAdapter
from nexus_backend.ai_assistant.infrastructure.tavily_adapter import TavilyNewsAdapter
from nexus_backend.ai_assistant.infrastructure.cheapshark_adapter import CheapSharkPriceAdapter
from nexus_backend.ai_assistant.infrastructure.llm import GroqLLMAdapter
from nexus_backend.ai_assistant.infrastructure.email_adapter import GmailEmailAdapter
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


# Catálogo demo local para pruebas inmediatas sin dependencias externas
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
    print(f"{CYAN}{BOLD}🎮  NEXUS DIGITAL STORE — PIPELINE DE IA & ASISTENTE GAMER EN VIVO  🎮{RESET}")
    print(f"{CYAN}{BOLD}======================================================================{RESET}")
    print(f"{DIM}Stack: Laya AI (System 1) + CheapShark + Tavily + Wikipedia + Groq + Gmail SMTP{RESET}\n")


async def run_demo_query(query: str, recipient_override: str | None = None):
    settings = get_settings()

    print(f"\n{BOLD}🎯 Consulta del usuario:{RESET} {YELLOW}\"{query}\"{RESET}\n")
    print(f"{DIM}──────────────────────────────────────────────────────────────────────{RESET}")

    # =========================================================================
    # PASO 1: Laya AI (System 1 Decision Engine)
    # =========================================================================
    print(f"{MAGENTA}{BOLD}[PASO 1] 🧠 Laya AI (System 1 - Clasificación Reflexiva e Intención){RESET}")
    laya = LayaDecisionAdapter(model_name=settings.LAYA_MODEL_NAME)
    decision = await laya.evaluate_decision(query)
    intent = decision.get("intent", "recommendation")
    need_trivia = decision.get("need_trivia", True)
    engine = decision.get("engine", "laya-ai")
    detected_email = recipient_override or decision.get("recipient_email")

    if not detected_email:
        email_search = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", query)
        if email_search:
            detected_email = email_search.group(0)

    print(f"  • {BOLD}Intención detectada:{RESET} {GREEN}{intent.upper()}{RESET}")
    print(f"  • {BOLD}Requiere trivia gamer:{RESET} {GREEN if need_trivia else YELLOW}{need_trivia}{RESET}")
    if detected_email:
        print(f"  • {BOLD}Correo destinatario detectado:{RESET} {CYAN}{detected_email}{RESET}")
    print(f"  • {BOLD}Motor evaluador:{RESET} {DIM}{engine}{RESET}")
    print(f"  • {DIM}Explicación: Laya evalúa en microsegundos si la petición amerita APIs externas o envío de correos.{RESET}\n")

    # =========================================================================
    # PASO 2: Catálogo de Productos (Pinecone Vector DB & RAG)
    # =========================================================================
    print(f"{BLUE}{BOLD}[PASO 2] 🌲 Catálogo de Productos (Pinecone Vector DB & RAG Semántico){RESET}")
    matched_games = []
    source = "Local Fallback"
    if settings.PINECONE_API_KEY:
        try:
            embed_adapter = HuggingFaceEmbeddingAdapter(model_name=settings.EMBEDDING_MODEL_NAME)
            query_vec = await embed_adapter.embed_text(query)
            pinecone_adapter = PineconeVectorStoreAdapter(
                api_key=settings.PINECONE_API_KEY,
                index_name=settings.PINECONE_INDEX_NAME,
                namespace=settings.PINECONE_NAMESPACE,
            )
            pinecone_results = await pinecone_adapter.similarity_search(query_vec, top_k=4)
            if pinecone_results:
                matched_games = pinecone_results
                source = f"🌲 Pinecone Vector DB (Índice '{settings.PINECONE_INDEX_NAME}', namespace: '{settings.PINECONE_NAMESPACE}')"
        except Exception:
            pass

    if not matched_games:
        q_words = set(query.lower().split())
        for g in MOCK_CATALOG:
            g_words = set(g.title.lower().split()) | {gen.name.lower() for gen in (g.genres or [])}
            if q_words & g_words or any(w in g.title.lower() for w in q_words):
                matched_games.append(g)

    if not matched_games:
        matched_games = [MOCK_CATALOG[0]]

    print(f"  • {BOLD}Fuente:{RESET} {CYAN}{source}{RESET}")
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

    generated_text_chunks: list[str] = []
    try:
        async for chunk in llm.generate_stream(NEXUSBOT_SYSTEM_PROMPT, user_message):
            print(chunk, end="", flush=True)
            generated_text_chunks.append(chunk)
        print(f"{RESET}\n")
        full_llm_response = "".join(generated_text_chunks)
    except Exception as exc:
        print(f"{RESET}\n{YELLOW}Nota: No se pudo conectar a Groq Cloud con la API key actual ({exc}).{RESET}")
        print(f"{CYAN}Simulando respuesta que generaría el LLM con este contexto ensamblado:{RESET}\n")
        full_llm_response = (
            f"¡Hola gamer! 🎮 Sobre tu consulta por **{target_game.title}**:\n\n"
            f"En **Nexus Digital Store** lo tenemos disponible para entrega inmediata a **${target_game.price_clp:,} CLP** (quedan {target_game.stock} unidades en stock).\n\n"
            f"🏷️ **Comparativa de Precios en Otras Tiendas (CheapShark API)**:\n"
            f"{price_context}\n\n"
            f"📰 **Novedades de la Industria (Tavily API)**:\n"
            f"{news_context[:200]}...\n\n"
            f"¿Te gustaría que te ayude a procesar tu orden o prefieres ver otros títulos del género?".replace(",", ".")
        )
        print(f"{GREEN}{full_llm_response}{RESET}\n")

    # =========================================================================
    # PASO 7: Envío de Correo Electrónico (Gmail SMTP + App Password)
    # =========================================================================
    if intent == "send_email" or detected_email:
        print(f"{MAGENTA}{BOLD}[PASO 7] 📧 Envío de Correo Electrónico desde el LLM (Google SMTP){RESET}")
        to_email = detected_email
        if not to_email:
            to_email = input(f"{BOLD}Ingresa el correo al que deseas enviar la cotización: {RESET}").strip()

        if to_email:
            email_adapter = GmailEmailAdapter()
            if not email_adapter.is_configured:
                print(f"  {YELLOW}⚠️ Credenciales de Gmail no encontradas en el archivo .env.{RESET}")
                print(f"  {DIM}Puedes configurarlas en nexus-backend/.env:{RESET}")
                print(f"    SMTP_USER=tu_correo@gmail.com")
                print(f"    SMTP_PASSWORD=tu_clave_de_16_caracteres_de_google\n")
                prompt_setup = input(f"{BOLD}¿Deseas ingresar tu correo y clave de Google ahora para probar el envío? (s/n): {RESET}").strip().lower()
                if prompt_setup == "s":
                    user_input = input("Tu correo Gmail: ").strip()
                    pass_input = input("Tu clave de aplicación de 16 caracteres de Google: ").strip()
                    email_adapter = GmailEmailAdapter(smtp_user=user_input, smtp_password=pass_input)

            if email_adapter.is_configured:
                print(f"  • {BOLD}Preparando mensaje para:{RESET} {CYAN}{to_email}{RESET}")
                print(f"  • {BOLD}Conectando a:{RESET} {email_adapter.smtp_host}:{email_adapter.smtp_port} vía STARTTLS...")
                subject = f"🎮 Nexus Digital Store — Cotización & Ofertas: {target_game.title}"
                res = await email_adapter.send_email(
                    to_email=to_email,
                    subject=subject,
                    content_html=full_llm_response,
                    content_text=full_llm_response,
                )
                if res.get("success"):
                    print(f"  • {GREEN}{BOLD}✔ ¡CORREO ENVIADO CON ÉXITO!{RESET}")
                    print(f"    Destinatario: {to_email}")
                    print(f"    Asunto: {subject}")
                    print(f"    Remitente: {email_adapter.from_name} <{email_adapter.smtp_user}>\n")
                else:
                    print(f"  • {RED}❌ Error al enviar:{RESET} {res.get('error')}\n")
            else:
                print(f"  • {YELLOW}Envío omitido: Falta configurar la clave de Google en .env{RESET}\n")

    print(f"{DIM}──────────────────────────────────────────────────────────────────────{RESET}")
    print(f"{GREEN}{BOLD}✔ Demostración completada con éxito.{RESET}\n")


async def test_direct_email():
    """Prueba interactiva rápida de envío de correo para validar la clave de Google."""
    print(f"\n{MAGENTA}{BOLD}📧 PRUEBA DIRECTA DE ENVÍO DE CORREO (GOOGLE GMAIL SMTP){RESET}")
    print(f"{DIM}Valida que tu Clave de Aplicación de Google de 16 caracteres funcione correctamente.{RESET}\n")

    adapter = GmailEmailAdapter()
    if not adapter.is_configured:
        print(f"{YELLOW}No se encontraron credenciales en .env. Ingrésalas ahora:{RESET}")
        user_mail = input("Correo Gmail remitente: ").strip()
        user_pass = input("Clave de aplicación de Google (16 letras): ").strip()
        adapter = GmailEmailAdapter(smtp_user=user_mail, smtp_password=user_pass)

    if not adapter.is_configured:
        print(f"{RED}Credenciales incompletas.{RESET}")
        return

    dest = input(f"\n{BOLD}Correo destinatario de prueba [default: {adapter.smtp_user}]: {RESET}").strip() or adapter.smtp_user

    print(f"\n{DIM}Enviando correo de prueba a {dest}...{RESET}")
    res = await adapter.send_email(
        to_email=dest,
        subject="🎮 Prueba de Envío Exitosa — Nexus Digital Store LLM",
        content_html=(
            "¡Hola gamer!\n\n"
            "Este es un correo de prueba enviado directamente desde el Asistente de IA de Nexus Digital Store "
            "utilizando tu Clave de Aplicación de Google y el protocolo SMTP seguro.\n\n"
            "¡Tu integración de correo está 100% operativa!"
        ),
    )

    if res.get("success"):
        print(f"\n{GREEN}{BOLD}✔ ¡CORREO ENVIADO CON ÉXITO A {dest}!{RESET}")
        print(f"Revisa tu bandeja de entrada (o carpeta de spam por ser primera vez).\n")
    else:
        print(f"\n{RED}{BOLD}❌ Fallo en el envío:{RESET} {res.get('error')}\n")


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
        ("4", "📧 Recomiéndame Elden Ring y envíame las ofertas a mi correo (Prueba Gmail SMTP + Laya)", "email_scenario"),
        ("5", "Escribir mi propia consulta libre (ej: 'envíame las ofertas de Hollow Knight a mi@correo.com')", "custom"),
        ("6", "🧪 Prueba directa de conexión de correo con tu Clave de Google", "test_mail"),
    ]

    print(f"{BOLD}Selecciona un escenario de prueba para la demostración:{RESET}\n")
    for opt, desc, _ in options:
        print(f"  {CYAN}{opt}.{RESET} {desc}")
    print()

    choice = input(f"{BOLD}Ingresa una opción (1-6) [default: 1]: {RESET}").strip() or "1"

    if choice == "6":
        await test_direct_email()
        return

    selected_query = options[0][2]
    recipient_override = None

    for opt, _, q in options:
        if opt == choice:
            selected_query = q
            break

    if selected_query == "email_scenario":
        target_email = input(f"\n{BOLD}Ingresa tu correo para recibir las ofertas de Elden Ring: {RESET}").strip()
        selected_query = f"Envíame la cotización y comparativa de ofertas de Elden Ring al correo {target_email}"
        recipient_override = target_email
    elif selected_query == "custom":
        selected_query = input(f"\n{BOLD}Escribe tu consulta gamer: {RESET}").strip() or "¿A cuánto está Elden Ring?"

    await run_demo_query(selected_query, recipient_override=recipient_override)


if __name__ == "__main__":
    asyncio.run(main())
