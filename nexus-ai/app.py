"""🎮 Nexus Digital Store — AI Multi-Agent Lab & Asistente Gamer (Streamlit App)
=============================================================================
Dashboard interactivo para presentar y demostrar en vivo el pipeline de IA:
  - System 1: Laya AI (Clasificación reflexiva de intenciones en microsegundos)
  - System 2: Groq LLM (NexusBot con streaming palabra por palabra)
  - Vector DB: Pinecone (Búsqueda semántica 384d en namespace 'nexus_chile')
  - Precios Externos: CheapShark API (Comparativa Steam, Epic, GOG con veredicto)
  - Noticias en Vivo: Tavily AI Search (Parches y actualidad gamer)
  - Lore Gamer: Wikipedia API (Trivia y curiosidades)
  - Envío de Correo: Google Gmail SMTP (Con Clave de Aplicación de Google)
"""

from __future__ import annotations

import asyncio
import os
import re
import sys
from typing import Any

import streamlit as st

# Configurar path para importar nexus_backend
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "nexus-backend"))
SRC_DIR = os.path.join(BACKEND_DIR, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

# Cargar variables de entorno de nexus-backend/.env
from dotenv import load_dotenv

ENV_PATH = os.path.join(BACKEND_DIR, ".env")
load_dotenv(ENV_PATH)

from nexus_backend.config import get_settings
from nexus_backend.catalog.domain.entities import VideoGame
from nexus_backend.ai_assistant.infrastructure.laya_adapter import LayaDecisionAdapter
from nexus_backend.ai_assistant.infrastructure.embeddings import HuggingFaceEmbeddingAdapter
from nexus_backend.ai_assistant.infrastructure.pinecone_store import PineconeVectorStoreAdapter
from nexus_backend.ai_assistant.infrastructure.wikipedia import WikipediaAdapter
from nexus_backend.ai_assistant.infrastructure.tavily_adapter import TavilyNewsAdapter
from nexus_backend.ai_assistant.infrastructure.cheapshark_adapter import CheapSharkPriceAdapter
from nexus_backend.ai_assistant.infrastructure.llm import GroqLLMAdapter
from nexus_backend.ai_assistant.infrastructure.email_adapter import GmailEmailAdapter
from nexus_backend.ai_assistant.application.chains import NEXUSBOT_SYSTEM_PROMPT


# ─────────────────────────────────────────────────────────────────────────────
# Configuración Visual de Streamlit
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Nexus AI — Gaming Assistant Lab",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Estilos CSS personalizados para temática Gamer Dark & Neon
st.markdown(
    """
    <style>
    .main {
        background: radial-gradient(circle at 50% 10%, #111827 0%, #030712 100%);
    }
    .stChatMessage {
        border-radius: 12px;
        margin-bottom: 12px;
    }
    .gamer-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 14px 18px;
        margin-bottom: 12px;
    }
    .metric-badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 0.5px;
    }
    .badge-cheaper {
        background-color: #064e3b;
        color: #34d399;
        border: 1px solid #059669;
    }
    .badge-expensive {
        background-color: #7f1d1d;
        color: #f87171;
        border: 1px solid #dc2626;
    }
    .badge-laya {
        background-color: #312e81;
        color: #a5b4fc;
        border: 1px solid #4f46e5;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ─────────────────────────────────────────────────────────────────────────────
# Funciones Helper Asíncronas
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def get_embedding_adapter(model_name: str) -> HuggingFaceEmbeddingAdapter:
    return HuggingFaceEmbeddingAdapter(model_name=model_name)


async def run_cognitive_pipeline(query: str, settings: Any, model_name: str, temp: float) -> dict[str, Any]:
    """Ejecuta los 5 pasos cognitivos (Laya, Pinecone, Wikipedia, Tavily, CheapShark) en paralelo."""
    # 1. Laya AI (System 1)
    laya = LayaDecisionAdapter(model_name=settings.LAYA_MODEL_NAME)
    decision = await laya.evaluate_decision(query)
    intent = decision.get("intent", "recommendation")
    need_trivia = decision.get("need_trivia", True)

    email_search = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", query)
    recipient_email = email_search.group(0) if email_search else decision.get("recipient_email")

    # 2. Pinecone Vector Store (RAG)
    matched_games: list[VideoGame] = []
    vector_source = "None"
    try:
        embed_adapter = get_embedding_adapter(settings.EMBEDDING_MODEL_NAME)
        q_vec = await embed_adapter.embed_text(query)
        pinecone_adapter = PineconeVectorStoreAdapter(
            api_key=settings.PINECONE_API_KEY,
            index_name=settings.PINECONE_INDEX_NAME,
            namespace=settings.PINECONE_NAMESPACE,
        )
        pinecone_results = await pinecone_adapter.similarity_search(q_vec, top_k=4)
        if pinecone_results:
            matched_games = pinecone_results
            vector_source = f"Pinecone ('{settings.PINECONE_INDEX_NAME}', '{settings.PINECONE_NAMESPACE}')"
    except Exception as e:
        vector_source = f"Error: {e}"

    target_title = matched_games[0].title if matched_games else query
    target_price = matched_games[0].price_clp if matched_games else 0

    # 3, 4, 5. Ejecución concurrente en paralelo de Wikipedia, Tavily y CheapShark
    async def _safe_trivia() -> str:
        if need_trivia and intent != "greeting":
            try:
                wiki = WikipediaAdapter(lang=settings.WIKIPEDIA_LANG, top_k_results=1, doc_content_chars_max=400)
                return await wiki.fetch_trivia(target_title)
            except Exception:
                pass
        return "Sin datos externos."

    async def _safe_news() -> str:
        if intent != "greeting" and settings.TAVILY_API_KEY:
            try:
                tavily = TavilyNewsAdapter(api_key=settings.TAVILY_API_KEY, max_results=3)
                return await tavily.fetch_news(target_title)
            except Exception:
                pass
        return "Sin noticias adicionales."

    async def _safe_cheapshark() -> dict:
        if intent != "greeting" and settings.CHEAPSHARK_ENABLED:
            try:
                cheap = CheapSharkPriceAdapter(usd_clp_rate=settings.CHEAPSHARK_USD_CLP_RATE)
                return await cheap.compare_price(target_title, target_price)
            except Exception:
                pass
        return {"has_data": False}

    trivia_res, news_res, cheap_res = await asyncio.gather(
        _safe_trivia(),
        _safe_news(),
        _safe_cheapshark(),
    )

    return {
        "decision": decision,
        "intent": intent,
        "recipient_email": recipient_email,
        "matched_games": matched_games,
        "vector_source": vector_source,
        "trivia": trivia_res,
        "news": news_res,
        "cheapshark": cheap_res,
        "target_title": target_title,
        "target_price": target_price,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Sidebar: Control Panel & Status
# ─────────────────────────────────────────────────────────────────────────────
settings = get_settings()

with st.sidebar:
    st.markdown("## ⚙️ Control Panel (Nexus AI)")
    st.markdown("---")

    selected_model = st.selectbox(
        "🧠 Modelo Groq Cloud LLM",
        ["openai/gpt-oss-120b", "llama-3.3-70b-versatile", "llama-3.1-8b-instant"],
        index=0,
    )

    temperature = st.slider("🌡️ Temperatura (Creatividad)", 0.0, 1.0, 0.2, 0.05)

    st.markdown("### 🔌 Estado de Integraciones")
    st.markdown(f"- **Laya AI (System 1):** `Active` ({settings.LAYA_MODEL_NAME})")
    st.markdown(f"- **Pinecone Vector DB:** `Active` ({settings.PINECONE_INDEX_NAME})")
    st.markdown(f"- **CheapShark API:** `Active` (Tasa CLP: ${settings.CHEAPSHARK_USD_CLP_RATE})")
    st.markdown(f"- **Tavily AI Search:** `Active` ({'Configurada' if settings.TAVILY_API_KEY else 'Falta Key'})")
    st.markdown(f"- **Google Gmail SMTP:** `Active` ({'Configurado' if settings.SMTP_USER else 'Falta User'})")

    st.markdown("---")
    st.markdown("### ⚡ Escenarios de Prueba Rápidos")

    scenario_1 = st.button("🏷️ ¿A cuánto está Elden Ring y dónde conviene?")
    scenario_2 = st.button("📰 ¿Qué noticias hay de Cyberpunk 2077?")
    scenario_3 = st.button("🍔 Tengo mucha hambre, ¿qué cocino? (Out-of-domain)")
    scenario_4 = st.button("📧 Ofertas de Elden Ring a mi correo")

    if st.button("🗑️ Limpiar Historial"):
        st.session_state.messages = []
        st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# Header Principal
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("# 🎮 Nexus Digital Store — AI Multi-Agent Lab")
st.caption(
    "Orquestación Cognitiva: **System 1 (Laya AI)** + **System 2 (Groq LLM + Pinecone RAG + CheapShark + Tavily + Gmail SMTP)**"
)

# Inicializar historial de chat
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "¡Hola gamer! 🎮 Soy **NexusBot**, el asesor inteligente de Nexus Digital Store. Puedo recomendarte juegos, comparar precios en tiempo real con Steam, Epic y GOG, buscar noticias de parches y enviarte cotizaciones directamente a tu correo electrónico. ¿Qué te gustaría jugar hoy?",
        }
    ]

# Renderizar historial
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "pipeline_data" in msg:
            p = msg["pipeline_data"]
            with st.expander("🔍 Inspeccionar Telemetría Cognitiva (System 1 + System 2 + APIs)", expanded=False):
                tab1, tab2, tab3, tab4, tab5 = st.tabs(["🧠 Laya AI", "🌲 Pinecone RAG", "🏷️ CheapShark", "📰 Tavily News", "📧 Gmail SMTP"])
                with tab1:
                    st.json(p["decision"])
                with tab2:
                    st.markdown(f"**Fuente:** `{p['vector_source']}`")
                    for g in p["matched_games"]:
                        st.markdown(f"- **{g.title}** — ${g.price_clp:,} CLP (Stock: {g.stock}) [{', '.join(x.name for x in g.genres)}]".replace(",", "."))
                with tab3:
                    if p["cheapshark"].get("has_data"):
                        c = p["cheapshark"]
                        st.markdown(f"**Dictamen:** `{c.get('verdict')}` | **Mejor Oferta Externa:** {c.get('cheapest_external_store')} (${c.get('cheapest_external_price_clp'):,} CLP)".replace(",", "."))
                        if c.get("deals"):
                            st.dataframe(c["deals"])
                    else:
                        st.info("Sin ofertas externas encontradas.")
                with tab4:
                    st.text(p["news"])
                with tab5:
                    if p.get("email_status"):
                        st.success(p["email_status"])
                    else:
                        st.info("No se solicitó envío de correo en esta interacción.")


# Detectar clic en escenarios de prueba
prompt_input = None
if scenario_1:
    prompt_input = "¿A cuánto está Elden Ring y en qué tienda conviene comprarlo?"
elif scenario_2:
    prompt_input = "¿Qué noticias y novedades recientes hay de Cyberpunk 2077?"
elif scenario_3:
    prompt_input = "Hola, tengo mucha hambre, ¿qué me recomiendas cocinar hoy?"
elif scenario_4:
    prompt_input = f"Recomiéndame Elden Ring y envíame las ofertas a {settings.SMTP_USER or 'cliente@nexus.com'}"

user_query = st.chat_input("Escribe tu consulta gamer o pide enviar ofertas a tu correo...") or prompt_input

if user_query:
    st.session_state.messages.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.markdown(user_query)

    with st.chat_message("assistant"):
        with st.status("🧠 Ejecutando Pipeline Cognitivo Multi-Agente...", expanded=True) as status_box:
            st.write("1. 🧠 Evaluando intención reflexiva con **Laya AI (System 1)**...")
            pipeline_data = asyncio.run(run_cognitive_pipeline(user_query, settings, selected_model, temperature))

            st.write(f"2. 🌲 Recuperando catálogo semántico desde **{pipeline_data['vector_source']}**...")
            st.write("3. 🏷️ Comparando precios internacionales en vivo con **CheapShark API**...")
            st.write("4. 📰 Buscando noticias y parches en **Tavily AI Search**...")
            st.write("5. ⚡ Generando síntesis contextual en **Groq Cloud**...")
            status_box.update(label="✔ Pipeline completado exitosamente", state="complete", expanded=False)

        # Construcción del contexto para el LLM
        matched_games = pipeline_data["matched_games"]
        context_games = "\n".join(
            [f"- {g.title} (${g.price_clp:,} CLP, Stock: {g.stock}): {g.description}".replace(",", ".") for g in matched_games]
        ) or "No se encontraron juegos en catálogo."

        price_summary = pipeline_data["cheapshark"].get("comparison_summary", "Sin datos comparativos.")
        news_summary = pipeline_data["news"]
        trivia_summary = pipeline_data["trivia"]

        user_message_prompt = (
            f"Intención del cliente (Laya AI): {pipeline_data['intent']}\n\n"
            f"Videojuegos disponibles en tienda:\n{context_games}\n\n"
            f"Dato curioso externo (Wikipedia):\n{trivia_summary}\n\n"
            f"Noticias recientes de videojuegos (Tavily API):\n{news_summary}\n\n"
            f"Comparativa de precios con otras tiendas (CheapShark API):\n{price_summary}\n\n"
            f"Pregunta del cliente: {user_query}"
        )

        llm = GroqLLMAdapter(
            api_key=settings.GROQ_API_KEY,
            model_name=selected_model,
            temperature=temperature,
        )

        response_placeholder = st.empty()
        full_response = ""

        try:
            async def generate_response():
                chunks = []
                async for chunk in llm.generate_stream(NEXUSBOT_SYSTEM_PROMPT, user_message_prompt):
                    chunks.append(chunk)
                    response_placeholder.markdown("".join(chunks) + "▌")
                return "".join(chunks)

            full_response = asyncio.run(generate_response())
            response_placeholder.markdown(full_response)
        except Exception as exc:
            full_response = f"¡Hola gamer! 🎮 Sobre tu consulta, aquí tienes los detalles de **{pipeline_data['target_title']}**:\n\n{price_summary}\n\n(Error conectando con Groq: {exc})"
            response_placeholder.markdown(full_response)

        # Enviar correo si corresponde
        email_status = None
        recipient = pipeline_data.get("recipient_email")
        if (pipeline_data["intent"] == "send_email" or recipient) and recipient:
            email_adapter = GmailEmailAdapter()
            if email_adapter.is_configured:
                with st.spinner(f"📧 Despachando correo a {recipient} vía Google SMTP..."):
                    mail_res = asyncio.run(
                        email_adapter.send_email(
                            to_email=recipient,
                            subject=f"🎮 Nexus Digital Store — Ofertas & Resumen: {pipeline_data['target_title']}",
                            content_html=full_response,
                            content_text=full_response,
                        )
                    )
                    if mail_res.get("success"):
                        email_status = f"✅ Correo enviado con éxito a {recipient} con la Clave de Aplicación de Google."
                        st.success(email_status)
                    else:
                        email_status = f"❌ Error enviando correo: {mail_res.get('error')}"
                        st.error(email_status)
            else:
                st.warning("⚠️ Para enviar correos, configura SMTP_USER y SMTP_PASSWORD en nexus-backend/.env")

        pipeline_data["email_status"] = email_status
        st.session_state.messages.append({
            "role": "assistant",
            "content": full_response,
            "pipeline_data": pipeline_data,
        })

