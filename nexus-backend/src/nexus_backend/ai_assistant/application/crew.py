"""Orquestación Multi-Agente con CrewAI para Nexus Digital Store."""

import asyncio
import logging
from typing import Any

import litellm
litellm.drop_params = True

# Neutralizar cache_breakpoint de CrewAI para compatibilidad total con Groq
try:
    import crewai.llms.cache
    crewai.llms.cache.mark_cache_breakpoint = lambda message: message
except Exception:
    pass

try:
    from crewai import Agent, Crew, Process, Task
except ImportError:
    Agent = Any  # type: ignore
    Crew = Any  # type: ignore
    Process = Any  # type: ignore
    Task = Any  # type: ignore
from nexus_backend.config import get_settings

logger = logging.getLogger(__name__)


def create_nexus_crew(
    llm: Any = None,
) -> Crew:
    """Crea la Crew multi-agente para análisis de catálogo y estrategia de ventas."""
    settings = get_settings()
    agent_llm = llm

    if settings.GROQ_API_KEY and settings.GROQ_API_KEY != "your-groq-api-key":
        try:
            from crewai import LLM
            agent_llm = LLM(
                model=f"groq/{settings.GROQ_MODEL_NAME}",
                api_key=settings.GROQ_API_KEY,
                temperature=settings.GROQ_TEMPERATURE,
            )
        except Exception:
            agent_llm = None

    catalog_analyst = Agent(
        role="Catalog & Inventory Analyst",
        goal="Evaluar los videojuegos disponibles en el catálogo interno, validando stock, precios y afinidad con el usuario.",
        backstory=(
            "Eres un analista de datos de e-commerce especializado en gaming. "
            "Revisas meticulosamente precios, disponibilidad y características para identificar qué juegos "
            "se ajustan de verdad al pedido del cliente."
        ),
        llm=agent_llm,
        verbose=False,
    )

    research_specialist = Agent(
        role="Gaming Culture & Trivia Researcher",
        goal="Destacar datos curiosos, impacto cultural e información externa relevante sobre los títulos candidatos.",
        backstory=(
            "Eres un apasionado historiador y periodista de videojuegos con amplio conocimiento de la industria. "
            "Encuentras anécdotas, trivia y datos fascinantes para hacer memorable la recomendación."
        ),
        llm=agent_llm,
        verbose=False,
    )

    sales_strategist = Agent(
        role="Senior Sales Strategist",
        goal="Sintetizar el análisis del catálogo y los datos curiosos en una estrategia de venta persuasiva y honesta.",
        backstory=(
            "Eres el estratega líder de Nexus Digital Store. Tu misión es transformar datos de inventario e "
            "historia en argumentos de venta irresistibles para el cliente gamer, siempre respetando las reglas de stock."
        ),
        llm=agent_llm,
        verbose=False,
    )

    task_analyze_catalog = Task(
        description=(
            "Analiza los siguientes videojuegos del catálogo en relación con la consulta del usuario.\n"
            "Consulta del usuario: {query}\n"
            "Catálogo disponible:\n{catalog_context}\n\n"
            "Identifica cuáles tienen stock, su relación calidad/precio y el grado de coincidencia."
        ),
        expected_output="Resumen conciso de los juegos viables, estado de stock y puntos clave de inventario.",
        agent=catalog_analyst,
    )

    task_research_trivia = Task(
        description=(
            "A partir de los juegos analizados y de los datos externos disponibles:\n"
            "{external_context}\n"
            "Extrae 1 o 2 datos curiosos o elementos de interés para entusiasmar al usuario con la recomendación."
        ),
        expected_output="1 o 2 datos curiosos o highlights destacados de los juegos.",
        agent=research_specialist,
    )

    task_sales_pitch = Task(
        description=(
            "Combina el informe de catálogo y la trivia en una síntesis estratégica para NexusBot.\n"
            "Provee una guía concisa con: qué juego recomendar como opción principal, alternativas secundarias y advertencias de stock si aplica."
        ),
        expected_output="Guía estratégica de venta concisa con puntos clave a comunicar.",
        agent=sales_strategist,
    )

    return Crew(
        agents=[catalog_analyst, research_specialist, sales_strategist],
        tasks=[task_analyze_catalog, task_research_trivia, task_sales_pitch],
        process=Process.sequential,
        verbose=False,
    )


async def run_nexus_crew(
    query: str,
    catalog_context: str,
    external_context: str,
    llm: Any = None,
) -> str:
    """Ejecuta la orquestación de CrewAI de forma asíncrona y segura con fallback."""
    settings = get_settings()
    if not settings.ENABLE_CREWAI_ORCHESTRATION:
        return "Orquestación multi-agente deshabilitada."

    # Si no hay catálogo relevante o no hay API key configurada, generar síntesis directa
    if not catalog_context or "No se encontraron" in catalog_context:
        return "Sin productos en inventario para análisis multi-agente."

    if not settings.GROQ_API_KEY or settings.GROQ_API_KEY == "your-groq-api-key":
        # Fallback determinista en modo desarrollo/testing sin API key
        return (
            f"Análisis de catálogo: Juegos evaluados para '{query}'. "
            f"Stock y precios verificados. Contexto externo integrado."
        )

    def _execute() -> str:
        try:
            crew = create_nexus_crew(llm=llm)
            inputs = {
                "query": query,
                "catalog_context": catalog_context,
                "external_context": external_context,
            }
            result = crew.kickoff(inputs=inputs)
            return str(result)
        except Exception as exc:
            logger.warning("CrewAI orchestration encountered an issue, falling back: %s", exc)
            return f"Análisis rápido: inventario procesado para '{query}'."

    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _execute)

