import json
import logging
from collections.abc import AsyncIterator

from langgraph.checkpoint.memory import MemorySaver
from langsmith import traceable

from nexus_backend.ai_assistant.application.crew import run_nexus_crew
from nexus_backend.ai_assistant.application.graph import SYSTEM_PROMPT, build_rag_graph
from nexus_backend.ai_assistant.domain.entities import AssistantState, ChatMessage
from nexus_backend.ai_assistant.domain.ports import (
    DecisionEnginePort,
    EmailPort,
    EmbeddingPort,
    ExternalKnowledgePort,
    GamingNewsPort,
    LLMPort,
    PriceComparisonPort,
    VectorStorePort,
)
from nexus_backend.config import get_settings

logger = logging.getLogger(__name__)


class AssistantService:
    def __init__(
        self,
        embedding_port: EmbeddingPort,
        llm_port: LLMPort,
        vector_store_port: VectorStorePort,
        external_knowledge_port: ExternalKnowledgePort | None = None,
        decision_port: DecisionEnginePort | None = None,
        checkpointer: MemorySaver | None = None,
        gaming_news_port: GamingNewsPort | None = None,
        price_comparison_port: PriceComparisonPort | None = None,
        email_port: EmailPort | None = None,
    ) -> None:
        self._embedding = embedding_port
        self._llm = llm_port
        self._vector_store = vector_store_port
        self._external_knowledge = external_knowledge_port
        self._decision = decision_port
        self._gaming_news = gaming_news_port
        self._price_comparison = price_comparison_port
        self._email = email_port
        self._checkpointer = checkpointer if checkpointer is not None else MemorySaver()
        self._graph = build_rag_graph(
            embedding_port,
            llm_port,
            vector_store_port,
            external_knowledge_port,
            decision_port,
            gaming_news_port,
            price_comparison_port,
            email_port,
        ).compile(checkpointer=self._checkpointer)

    @staticmethod
    def _build_contextual_fallback(query: str, video_games: list) -> str:
        q_lower = query.lower().strip()
        
        # 1. Saludos e introducciones
        greetings = ("hola", "buenas", "hey", "saludos", "que tal", "buenos dias", "buenas tardes", "buenas noches")
        if any(g in q_lower for g in greetings) and len(q_lower.split()) <= 4:
            return (
                "¡Hola! Bienvenido a Nexus Digital Store. 🎮\n\n"
                "Soy tu asesor gamer para encontrar videojuegos de PC. "
                "¿Qué tipo de experiencia buscas hoy? Cuéntame sobre tus géneros predilectos "
                "(RPG, Acción, Terror, Estrategia, Carreras) o si buscas algo para jugar en solitario o con amigos."
            )

        # 2. Sed y bebidas
        if any(w in q_lower for w in ("sed", "beber", "bebida", "agua", "tomar")):
            return (
                "¡Jaja! Como inteligencia artificial no tengo cuerpo biológico ni garganta, así que no tengo sed ni necesito beber líquidos. "
                "¡Mi única energía son los servidores y los buenos videojuegos! 🥤🎮\n\n"
                "Pero tú mantente hidratado para esas partidas largas. ¿Qué juego te gustaría jugar hoy?"
            )

        # 3. Hambre, comida y recetas
        if any(w in q_lower for w in ("hambre", "comes", "comida", "almuerzo", "cena", "desayuno", "comer", "cocina", "receta")):
            return (
                "¡Jaja! Como inteligencia artificial no tengo cuerpo biológico ni estómago, así que no estoy relacionado con el hambre ni necesito comida humana. "
                "¡Mi único combustible son los servidores, los gigabytes y los buenos videojuegos! 🍕🎮\n\n"
                "Eso sí, si a ti te apasiona la gastronomía o comida en el mundo gamer, hay simuladores culinarios increíbles como Overcooked o Chef RPG. "
                "Y para acompañar tu comida o snack, ¿qué tipo de juego te gustaría probar hoy?"
            )

        # 4. Clima y meteorología
        if any(w in q_lower for w in ("clima", "tiempo", "llov", "lluv", "temperatura", "frio", "calor", "soleado", "nublado", "pronostico", "meteorolog", "tormenta", "nieve")):
            return (
                "No puedo ver el clima exterior ni tengo sensores meteorológicos para saber si llueve, hace frío o hay sol en tu ciudad... ☀️🌧️\n\n"
                "Pero desde la terminal de Nexus te puedo asegurar que cualquier clima es perfecto para quedarse jugando con el PC bien ventilado. "
                "¿Buscas alguna recomendación de juego para pasar el día?"
            )

        # 4. Autos, mecánica y reparación
        if any(w in q_lower for w in ("auto", "coche", "carro", "mecanica", "motor", "rueda", "neumatico", "aceite", "reparar", "taller", "trafico")):
            return (
                "En cuanto a tu consulta sobre mecánica o vehículos del mundo real: como IA de Nexus no soy mecánico ni tengo un taller de reparación automotriz. "
                "¡Donde sí soy experto es en la velocidad y el asfalto virtual! 🏎️💨\n\n"
                "¿Te gustaría que busquemos algún simulador de carreras, rally o conducción para sentir la adrenalina de los motores en PC?"
            )

        # 5. Salud, medicina y síntomas
        if any(w in q_lower for w in ("salud", "medico", "medicina", "pastilla", "enfermo", "dolor", "sintoma", "remedio", "farmacia", "hospital")):
            return (
                "Respecto a tu consulta de salud: soy un asistente virtual de videojuegos y no poseo formación médica ni puedo recetar medicamentos (¡aquí solo manejamos botiquines y pociones de salud en pantalla!). 💊❤️\n\n"
                "Si no te sientes bien, por favor consulta a un profesional de la salud. Y para distraerte y descansar la mente, ¿hay algún juego relajante o aventura que te gustaría explorar?"
            )

        # 6. Tareas, matemáticas, física, colegio o universidad
        if any(w in q_lower for w in ("tarea", "matematica", "calculo", "colegio", "universidad", "profesor", "examen", "fisica", "quimica")):
            return (
                "Sobre tu consulta de estudio o tareas académicas: mi base de conocimiento en Nexus está 100% orientada al catálogo y la cultura gamer de PC, así que no resuelvo deberes escolares ni ecuaciones. 📚🎮\n\n"
                "¡Pero una vez que apruebes ese examen, aquí te espero para celebrarlo con una buena partida! ¿Qué juego tienes en la mira para jugar después?"
            )

        # 7. Política, elecciones y gobierno
        if any(w in q_lower for w in ("politica", "presidente", "eleccion", "gobierno", "ley", "voto", "partido")):
            return (
                "En cuanto a temas políticos o de gobierno: en Nexus nos enfocamos pura y exclusivamente en el entretenimiento y los videojuegos, por lo que no tomo posturas ni analizo política del mundo real. 🏛️🎮\n\n"
                "¡Las únicas batallas y estrategias que seguimos son dentro de los servidores de juego! ¿Te interesa algún juego de estrategia o táctica en el catálogo?"
            )

        # 8. Relaciones, amor o citas
        if any(w in q_lower for w in ("amor", "novia", "novio", "pareja", "cita", "enamorado", "casarme", "sentimientos")):
            return (
                "Respecto a tu pregunta sobre relaciones o amor: como entidad virtual que reside en un servidor, no tengo vida romántica ni sentimientos biológicos. ❤️🤖\n\n"
                "Mi verdadera devoción son los videojuegos épicos. Eso sí, tenemos títulos cooperativos increíbles para jugar en pareja o con amigos. ¿Buscas algún juego para dos?"
            )

        # 9. Cine, series o streaming
        if any(w in q_lower for w in ("pelicula", "cine", "serie", "netflix", "streaming", "cancion", "musica", "album")):
            return (
                "Sobre entretenimiento de cine o música: en Nexus nos especializamos en videojuegos de PC y no contamos con catálogo de películas ni servicios de streaming. 🎬🎧\n\n"
                "Aun así, muchísimos videojuegos tienen bandas sonoras y cinemáticas dignas de Hollywood. ¿Buscas algún juego con una historia cinematográfica profunda?"
            )

        # 2. Si se encontraron juegos relevantes en el catálogo
        if video_games:
            items_text = []
            for vg in video_games[:3]:
                stock_str = "Disponible" if vg.stock > 0 else "Sin stock temporalmente"
                price_str = f"${vg.price_clp:,}".replace(",", ".")
                items_text.append(f"• **{vg.title}** — {price_str} CLP ({stock_str})\n  {vg.description[:130]}...")
            
            joined_items = "\n".join(items_text)
            return (
                f"Respecto a lo que buscas sobre **\"{query}\"**, aquí tienes opciones muy recomendadas de nuestro catálogo:\n\n"
                f"{joined_items}\n\n"
                "¿Te gustaría conocer detalles sobre los requisitos, la historia o la jugabilidad de alguno de ellos?"
            )

        # 3. Preguntas sobre ofertas y precios
        if any(w in q_lower for w in ("precio", "barato", "oferta", "descuento", "economico", "cuanto vale", "costo")):
            return (
                "En Nexus Digital Store tenemos un catálogo con precios competitivos en pesos chilenos (CLP). "
                "¿Tienes algún presupuesto en mente o un género preferido (acción, rol, shooters) para recomendarte las opciones más convenientes?"
            )

        # 12. Fallback universal relativo al input específico del usuario
        return (
            f"Respecto a tu consulta sobre **\"{query}\"**: como asistente de Nexus Digital Store, mi conocimiento y funciones están enfocados exclusivamente en el mundo de los videojuegos de PC y el asesoramiento gamer, por lo que no puedo gestionar ese tema en el mundo exterior.\n\n"
            "¡Pero si quieres sumergirte en una gran aventura interactiva, aquí estoy para recomendarte los mejores juegos! ¿Qué estilo o género te gustaría explorar hoy?"
        )

    @traceable(name="assistant_chat")
    async def chat(
        self,
        query: str,
        chat_history: list[ChatMessage] | None = None,
        session_id: str = "default-session",
    ) -> str:
        config = {"configurable": {"thread_id": session_id}}
        state: AssistantState = {"query": query}
        if chat_history:
            state["chat_history"] = chat_history

        try:
            result = await self._graph.ainvoke(state, config=config)
            return result.get("response", "")
        except Exception as e:
            logger.warning("Graph ainvoke failed, returning contextual fallback: %s", e)
            try:
                embedding = await self._embedding.embed_text(query)
                games = await self._vector_store.similarity_search(embedding, top_k=3)
            except Exception:
                games = []
            return self._build_contextual_fallback(query, games)

    @traceable(name="assistant_chat_stream")
    async def chat_stream(
        self,
        query: str,
        chat_history: list[ChatMessage] | None = None,
        session_id: str = "default-session",
    ) -> AsyncIterator[str]:
        settings = get_settings()
        config = {"configurable": {"thread_id": session_id}}

        # Si el cliente no envió historial explícito, recuperarlo del checkpointer (MemorySaver)
        if not chat_history and self._checkpointer:
            try:
                saved_state = self._graph.get_state(config)
                if saved_state and saved_state.values:
                    raw_history = saved_state.values.get("chat_history", [])
                    chat_history = [
                        ChatMessage(role=m["role"], content=m["content"]) if isinstance(m, dict) else m
                        for m in raw_history
                    ]
            except Exception as e:
                logger.debug("Could not retrieve state from checkpointer: %s", e)
                chat_history = []

        # Evaluación System 1 (Laya AI)
        intent = "recommendation"
        need_trivia = True
        if self._decision:
            try:
                metrics = await self._decision.evaluate_decision(query)
                intent = metrics.get("intent", "recommendation")
                need_trivia = metrics.get("need_trivia", True)
            except Exception as e:
                logger.debug("Laya decision evaluation failed in chat_stream: %s", e)

        embedding = await self._embedding.embed_text(query)
        video_games = await self._vector_store.similarity_search(
            embedding, top_k=settings.VECTOR_SEARCH_TOP_K,
        )

        context_parts = []
        for i, vg in enumerate(video_games, 1):
            genres = ", ".join(g.name for g in vg.genres) if vg.genres else "N/A"
            stock_info = f"Stock: {vg.stock} unidades" if vg.stock > 0 else "SIN STOCK (0 unidades)"
            context_parts.append(
                f"{i}. {vg.title} — ${vg.price_clp} CLP\n"
                f"   Géneros: {genres}\n"
                f"   {vg.description}\n"
                f"   {stock_info}"
            )
        context = "\n\n".join(context_parts) if context_parts else "No se encontraron videojuegos relevantes."

        # Conocimiento externo (Wikipedia) optimizado por Laya AI
        external_context = "Sin datos externos."
        if video_games and self._external_knowledge and need_trivia and (intent != "greeting"):
            try:
                external_context = await self._external_knowledge.fetch_trivia(video_games[0].title)
            except Exception as e:
                logger.debug("External knowledge fetch error in stream: %s", e)

        # Noticias de videojuegos en tiempo real (Tavily API)
        gaming_news = "Sin noticias adicionales."
        if self._gaming_news and (intent != "greeting"):
            target_topic = video_games[0].title if video_games else query
            try:
                gaming_news = await self._gaming_news.fetch_news(target_topic)
            except Exception as e:
                logger.debug("Gaming news fetch error in stream (Tavily): %s", e)

        # Comparativa de precios con otras tiendas (CheapShark API - Steam, Epic, GOG, etc.)
        price_comparison = "Sin datos comparativos de otras tiendas."
        if self._price_comparison and (intent != "greeting"):
            target_title = video_games[0].title if video_games else query
            target_price = video_games[0].price_clp if video_games else 0
            try:
                comp_data = await self._price_comparison.compare_price(target_title, target_price)
                if comp_data.get("has_data"):
                    price_comparison = comp_data.get("comparison_summary", price_comparison)
            except Exception as e:
                logger.debug("Price comparison fetch error in stream (CheapShark): %s", e)

        # Orquestación multi-agente CrewAI
        crew_analysis = ""
        if settings.ENABLE_CREWAI_ORCHESTRATION and video_games and (intent != "greeting"):
            underlying_llm = getattr(self._llm, "llm", None)
            crew_analysis = await run_nexus_crew(
                query=query,
                catalog_context=context,
                external_context=external_context,
                llm=underlying_llm,
            )

        history_text = ""
        if chat_history:
            history_lines = [f"{m.role}: {m.content}" for m in chat_history[-6:]]
            history_text = "\n".join(history_lines)

        user_message_parts = [
            f"Historial de conversación:\n{history_text}\n",
            f"Intención detectada (Laya AI): {intent}\n",
            f"Videojuegos disponibles:\n{context}\n",
        ]
        if external_context and external_context != "Sin datos externos.":
            user_message_parts.append(f"Dato curioso externo (Wikipedia):\n{external_context}\n")
        if gaming_news and "Sin noticias" not in gaming_news:
            user_message_parts.append(f"Noticias recientes de videojuegos (Tavily API):\n{gaming_news}\n")
        if price_comparison and "Sin datos" not in price_comparison:
            user_message_parts.append(f"Comparativa de precios con otras tiendas (CheapShark API):\n{price_comparison}\n")
        if crew_analysis:
            user_message_parts.append(f"Análisis estratégico:\n{crew_analysis}\n")
        user_message_parts.append(f"Pregunta del cliente: {query}")

        user_message = "\n".join(user_message_parts)

        product_data = [
            {"id": str(vg.id), "title": vg.title, "price_clp": str(vg.price_clp)}
            for vg in video_games
        ]
        yield f"data: {json.dumps({'type': 'products', 'data': product_data})}\n\n"

        accumulated_tokens: list[str] = []
        try:
            async for chunk in self._llm.generate_stream(SYSTEM_PROMPT, user_message):
                accumulated_tokens.append(chunk)
                yield f"data: {json.dumps({'type': 'token', 'data': chunk})}\n\n"
        except Exception as e:
            logger.warning("LLM generate_stream failed in chat_stream, yielding contextual fallback: %s", e)
            fallback_text = self._build_contextual_fallback(query, video_games)
            accumulated_tokens.append(fallback_text)
            yield f"data: {json.dumps({'type': 'token', 'data': fallback_text})}\n\n"

        # Persistir el turno generado en MemorySaver
        full_response = "".join(accumulated_tokens)
        if self._checkpointer:
            try:
                serialized_history = [
                    {"role": m.role, "content": m.content} if isinstance(m, ChatMessage) else m
                    for m in (chat_history or [])
                ] + [
                    {"role": "user", "content": query},
                    {"role": "assistant", "content": full_response},
                ]
                self._graph.update_state(
                    config,
                    {
                        "chat_history": serialized_history,
                        "query": query,
                        "response": full_response,
                    },
                )
            except Exception as e:
                logger.debug("Failed to update MemorySaver state in chat_stream: %s", e)

        yield f"data: {json.dumps({'type': 'done'})}\n\n"
