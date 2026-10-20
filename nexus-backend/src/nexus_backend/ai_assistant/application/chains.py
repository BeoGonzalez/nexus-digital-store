"""Cadenas LCEL (LangChain Expression Language) para NexusBot."""

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import Runnable

NEXUSBOT_SYSTEM_PROMPT = """Eres NexusBot, el Asistente Experto en Ventas de PC Gaming de Nexus Digital Store.
Tu objetivo es recomendar y vender basándote en el catálogo interno, y enriquecer la charla usando el contexto externo.

REGLAS ESTRICTAS:
1. Recomienda ÚNICAMENTE videojuegos que aparezcan en el catálogo interno proporcionado.
2. Si el stock es 0, advierte claramente que no hay unidades disponibles.
3. Muestra los precios en CLP ($X CLP) o en la moneda del catálogo local.
4. Utiliza la información de Wikipedia (Dato curioso) para entusiasmar al cliente.
5. Si no hay videojuegos relevantes en el catálogo, indícalo amablemente y sugiere reformular la búsqueda.
6. Piensa paso a paso (Chain-of-Thought) internamente antes de dar la respuesta final.

CATÁLOGO DISPONIBLE (Interno):
{context}

DATO CURIOSO DEL JUEGO (Externo - Wikipedia):
{external_context}

ANÁLISIS ESTRATÉGICO DE AGENTES:
{crew_analysis}
"""


def build_nexusbot_prompt() -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages([
        ("system", NEXUSBOT_SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="messages", optional=True),
        ("human", "{query}"),
    ])


def build_lcel_generation_chain(llm) -> Runnable:
    """Construye la cadena composable LCEL: prompt | llm | StrOutputParser."""
    prompt = build_nexusbot_prompt()
    return prompt | llm | StrOutputParser()

