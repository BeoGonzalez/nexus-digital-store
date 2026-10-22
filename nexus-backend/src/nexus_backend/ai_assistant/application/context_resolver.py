"""
🎯 Nexus Digital Store — Context & Target Game Resolver
======================================================
Módulo centralizado para la resolución, anclaje y sincronización temático-contextual
del pipeline cognitivo (Pinecone RAG, CheapShark, Tavily, Wikipedia, Laya y Groq).

Garantiza que todas las fuentes de datos (catálogo interno, comparativas externas,
noticias y trivia) hablen con un 100% de coherencia sobre el mismo videojuego,
incluso en preguntas de seguimiento multi-turno o consultas con lenguaje coloquial.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from nexus_backend.catalog.domain.entities import Genre, VideoGame


@dataclass(frozen=True)
class KnownGame:
    title: str
    clean_title: str
    price_clp: int
    stock: int
    genres: list[str]
    description: str
    aliases: list[str]


# Catálogo curado oficial de Nexus Digital Store con sus alias coloquiales
NEXUS_CANONICAL_CATALOG: list[KnownGame] = [
    KnownGame(
        title="Elden Ring",
        clean_title="Elden Ring",
        price_clp=39990,
        stock=18,
        genres=["Action RPG", "Soulslike", "Open World", "Dark Fantasy"],
        description="Obra maestra del rol de acción y fantasía oscura de FromSoftware y Hidetaka Miyazaki. Explora las Tierras Intermedias y reclama el Círculo de Elden.",
        aliases=["elden ring", "elden", "tierras intermedias", "shadow of the erdtree"],
    ),
    KnownGame(
        title="Cyberpunk 2077: Phantom Liberty",
        clean_title="Cyberpunk 2077",
        price_clp=34990,
        stock=25,
        genres=["RPG", "Sci-Fi", "Cyberpunk", "Open World", "FPS"],
        description="Aventura de rol y acción futurista en Night City. Incluye la aclamada expansión Phantom Liberty con Idris Elba y mejoras gráficas.",
        aliases=["cyberpunk 2077", "cyberpunk", "phantom liberty", "night city", "cyber punk"],
    ),
    KnownGame(
        title="Hollow Knight",
        clean_title="Hollow Knight",
        price_clp=8500,
        stock=40,
        genres=["Metroidvania", "Indie", "Action", "Souls-lite"],
        description="Aclamado metroidvania en 2D a través de Hallownest. Combate preciso, más de 30 jefes épicos y banda sonora inolvidable.",
        aliases=["hollow knight", "hallownest", "silksong", "hollow"],
    ),
    KnownGame(
        title="God of War Ragnarök",
        clean_title="God of War Ragnarök",
        price_clp=44990,
        stock=12,
        genres=["Action", "Adventure", "Mythology", "Hack and Slash"],
        description="Kratos y Atreus viajan a través de los Nueve Reinos nórdicos antes de que estalle la batalla del Ragnarök. Combate visceral y narrativa profunda.",
        aliases=["god of war ragnarok", "god of war ragnarök", "god of war", "gow", "ragnarok", "kratos"],
    ),
    KnownGame(
        title="Black Myth: Wukong",
        clean_title="Black Myth: Wukong",
        price_clp=42990,
        stock=20,
        genres=["Action RPG", "Soulslike", "Mythology", "Action"],
        description="Rol de acción inspirado en la novela clásica Peregrinación al Oeste. Encarna al Destinado con gráficos hiperrealistas en Unreal Engine 5.",
        aliases=["black myth wukong", "black myth: wukong", "black myth", "wukong", "rey mono"],
    ),
    KnownGame(
        title="Baldur's Gate 3",
        clean_title="Baldur's Gate 3",
        price_clp=41990,
        stock=15,
        genres=["CRPG", "Turn-Based Strategy", "Fantasy", "D&D"],
        description="El galardonado CRPG de Larian Studios en el universo de Dungeons & Dragons. Libertad de decisiones morales y combate táctico por turnos.",
        aliases=["baldur's gate 3", "baldurs gate 3", "baldur's gate", "baldurs gate", "bg3", "baldur"],
    ),
    KnownGame(
        title="The Witcher 3: Wild Hunt",
        clean_title="The Witcher 3: Wild Hunt",
        price_clp=19990,
        stock=30,
        genres=["RPG", "Open World", "Dark Fantasy", "Story-Rich"],
        description="Geralt de Rivia emprende la búsqueda de Ciri en un vasto continente azotado por la cacería salvaje. Uno de los mejores RPGs de la historia.",
        aliases=["the witcher 3", "witcher 3", "the witcher", "witcher", "geralt de rivia", "geralt"],
    ),
    KnownGame(
        title="Red Dead Redemption 2",
        clean_title="Red Dead Redemption 2",
        price_clp=29990,
        stock=16,
        genres=["Action", "Adventure", "Open World", "Western"],
        description="La épica del salvaje oeste de Rockstar Games con Arthur Morgan y la banda de Van der Linde. Mundo abierto hiperrealista e historia conmovedora.",
        aliases=["red dead redemption 2", "red dead redemption", "red dead", "rdr2", "arthur morgan"],
    ),
    KnownGame(
        title="Resident Evil 4 Remake",
        clean_title="Resident Evil 4",
        price_clp=31990,
        stock=14,
        genres=["Survival Horror", "Action", "Zombies", "Shooter"],
        description="Sobrevive a Las Plagas en un pueblo europeo con Leon S. Kennedy. Tensa acción en tercera persona y terror renovado.",
        aliases=["resident evil 4 remake", "resident evil 4", "re4 remake", "re4", "resident evil"],
    ),
    KnownGame(
        title="Silent Hill 2 Remake",
        clean_title="Silent Hill 2",
        price_clp=38990,
        stock=11,
        genres=["Psychological Horror", "Survival Horror", "Atmospheric"],
        description="James Sunderland busca a su difunta esposa en la enigmática y brumosa Silent Hill. Terror psicológico opresivo y gráficos de última generación.",
        aliases=["silent hill 2 remake", "silent hill 2", "silent hill", "pyramid head"],
    ),
    KnownGame(
        title="Sekiro: Shadows Die Twice",
        clean_title="Sekiro: Shadows Die Twice",
        price_clp=32990,
        stock=10,
        genres=["Action", "Soulslike", "Stealth", "Ninja"],
        description="El Lobo de un solo brazo desafía al Japón Sengoku con katana y prótesis shinobi. Mecánica magistral de parry milimétrico.",
        aliases=["sekiro shadows die twice", "sekiro: shadows die twice", "sekiro", "shadows die twice"],
    ),
    KnownGame(
        title="Hades II",
        clean_title="Hades II",
        price_clp=18500,
        stock=28,
        genres=["Roguelike", "Action", "Indie", "Mythology"],
        description="Melínoë, la princesa del Inframundo, desafía al Titán Cronos con hechicería y bendiciones olímpicas en el roguelike definitivo de Supergiant.",
        aliases=["hades 2", "hades ii", "hades", "melinoe", "zagreus"],
    ),
    KnownGame(
        title="Dead Space Remake",
        clean_title="Dead Space",
        price_clp=27990,
        stock=10,
        genres=["Sci-Fi", "Survival Horror", "Gore", "Shooter"],
        description="Isaac Clarke lucha contra los necromorfos a bordo del USG Ishimura con tecnología Frostbite y desmembramiento estratégico.",
        aliases=["dead space remake", "dead space", "isaac clarke", "ishimura"],
    ),
    KnownGame(
        title="EA Sports FC 25",
        clean_title="EA Sports FC 25",
        price_clp=48990,
        stock=35,
        genres=["Sports", "Soccer", "Simulation", "Multiplayer"],
        description="Simulación definitiva del fútbol mundial con tecnología táctica FC IQ, Ultimate Team y ligas oficiales de todo el planeta.",
        aliases=["ea sports fc 25", "ea sports fc", "ea fc 25", "ea fc", "fc 25", "fifa 25", "fifa", "fc25"],
    ),
    KnownGame(
        title="Stardew Valley",
        clean_title="Stardew Valley",
        price_clp=7500,
        stock=50,
        genres=["Farming Sim", "RPG", "Cozy", "Indie", "Pixel Art"],
        description="Revitaliza la granja de tu abuelo, cultiva hortalizas, cuida animales y haz amigos en el pueblo en una experiencia relajante y entrañable.",
        aliases=["stardew valley", "stardew", "valle stardew"],
    ),
    KnownGame(
        title="Doom Eternal",
        clean_title="Doom Eternal",
        price_clp=16990,
        stock=20,
        genres=["FPS", "Action", "Fast-Paced", "Demons"],
        description="El Slayer arrasa con hordas demoníacas en la Tierra a ritmo de metal industrial. Combate agresivo y velocidad trepidante.",
        aliases=["doom eternal", "doom", "slayer"],
    ),
    KnownGame(
        title="Persona 5 Royal",
        clean_title="Persona 5 Royal",
        price_clp=33990,
        stock=15,
        genres=["JRPG", "Turn-Based", "Anime", "Story-Rich"],
        description="Únete a los Ladrones Fantasma de Corazones en Tokio. Estilo visual electrizante, combates por turnos dinámicos y banda sonora inolvidable.",
        aliases=["persona 5 royal", "persona 5", "p5r", "phantom thieves", "joker"],
    ),
    KnownGame(
        title="Monster Hunter: World",
        clean_title="Monster Hunter: World",
        price_clp=22990,
        stock=17,
        genres=["Action RPG", "Co-op", "Open World", "Hunting"],
        description="Caza criaturas colosales en un ecosistema vivo en solitario o cooperativo online con armas artesanales forjadas con piezas de monstruos.",
        aliases=["monster hunter world", "monster hunter: world", "monster hunter", "mhw"],
    ),
    KnownGame(
        title="Grand Theft Auto V",
        clean_title="Grand Theft Auto V",
        price_clp=15990,
        stock=45,
        genres=["Action", "Open World", "Crime", "Multiplayer"],
        description="Michael, Trevor y Franklin realizan audaces atracos en la metrópolis de Los Santos en una de las obras cumbres del videojuego moderno.",
        aliases=["grand theft auto v", "grand theft auto 5", "grand theft auto", "gta v", "gta 5", "gta", "los santos"],
    ),
    KnownGame(
        title="Celeste",
        clean_title="Celeste",
        price_clp=6990,
        stock=35,
        genres=["Platformer", "Precision", "Indie", "Emotional"],
        description="Ayuda a Madeline a escalar la cima de la montaña Celeste en un plataformas de precisión impecable y profunda carga emotiva.",
        aliases=["celeste", "madeline"],
    ),
]


@dataclass
class ResolvedTarget:
    """Información consolidada del juego ancla para todos los componentes cognitivos."""
    title: str                     # Título limpio para CheapShark, Tavily y Wikipedia
    catalog_title: str             # Título oficial de la tienda Nexus
    price_clp: int                 # Precio en catálogo Nexus (0 si no está en catálogo)
    stock: int                     # Unidades disponibles (0 si no hay stock)
    is_in_catalog: bool            # Si el juego pertenece a Nexus Digital Store
    canonical_game: KnownGame | None = None
    matched_video_game: VideoGame | None = None
    is_general_recommendation: bool = False
    source: str = "unknown"        # 'query_alias', 'query_candidate', 'history', 'clean_regex', 'top_candidate'


_INTENT_STRIP_REGEX = re.compile(
    r"(?i)\b(a cuanto esta|a cuánto está|cuanto cuesta|cuánto cuesta|cuanto sale|cuánto sale|"
    r"a como esta|a cómo está|precio de|precios de|ofertas de|oferta de|en otras tiendas|"
    r"en steam|en epic games|en epic|en gog|en humble|juego|videojuego|noticias de|parches de|"
    r"dime sobre|informacion de|información de|cuentame de|cuéntame de|recomiendame|recomiéndame|"
    r"comparar precios de|comparativa de|comparar|compara|tienen stock de|tienen|hay stock de|"
    r"stock de|hablame de|háblame de|que tal es|qué tal es|quiero comprar|cotizacion de|cotización de)\b"
)

_FOLLOW_UP_TRIGGERS = (
    "en steam", "en epic", "en gog", "en otras tiendas", "a cuanto", "a cuánto",
    "cuanto cuesta", "cuánto cuesta", "cuanto sale", "cuánto sale", "que precio",
    "qué precio", "tienen stock", "hay stock", "esta barato", "está barato",
    "esta caro", "está caro", "de que trata", "de qué trata", "que requisitos",
    "qué requisitos", "y ese", "y este", "recomiendamelo", "recomiéndamelo",
    "enviame", "envíame", "mandamelo", "mándamelo", "comparalo", "compáralo"
)


def _normalize(text: str) -> str:
    """Normaliza texto para comparaciones seguras de subcadenas."""
    t = text.lower()
    for src, dst in [("á", "a"), ("é", "e"), ("í", "i"), ("ó", "o"), ("ú", "u"), ("ñ", "n")]:
        t = t.replace(src, dst)
    return re.sub(r"[^\w\s]", " ", t).strip()


def resolve_target_game(
    query: str,
    chat_history: list[Any] | None = None,
    candidates: list[VideoGame] | None = None,
) -> ResolvedTarget:
    """
    Identifica de forma precisa y robusta el videojuego que el usuario desea consultar.
    
    Aplica una cascada de resolución:
      1. Coincidencia directa en la consulta con alias del catálogo Nexus.
      2. Coincidencia con títulos de candidatos pasados (e.g. Pinecone).
      3. Anáfora / Historial conversacional: Si la consulta es un follow-up sin título,
         busca en los turnos previos de chat_history.
      4. Limpieza regex de expresiones interrogativas para rescatar títulos externos.
      5. Si es consulta general ("recomiéndame juegos"), marca flag de recomendación.
      6. Fallback al mejor candidato disponible.
    """
    q_norm = f" {_normalize(query)} "
    candidates = candidates or []

    # 1. Coincidencia directa contra catálogo canónico por alias (ordenados por especificidad)
    for kg in sorted(NEXUS_CANONICAL_CATALOG, key=lambda x: max(len(a) for a in x.aliases), reverse=True):
        for alias in kg.aliases:
            alias_norm = f" {_normalize(alias)} "
            if alias_norm in q_norm or alias.lower() in query.lower():
                return ResolvedTarget(
                    title=kg.clean_title,
                    catalog_title=kg.title,
                    price_clp=kg.price_clp,
                    stock=kg.stock,
                    is_in_catalog=True,
                    canonical_game=kg,
                    source="query_alias",
                )

    # 2. Coincidencia contra candidatos de Pinecone / DB
    for vg in candidates:
        vg_base = vg.title.split(":")[0].split(" - ")[0].strip()
        vg_norm = f" {_normalize(vg_base)} "
        if vg_norm in q_norm or vg.title.lower() in query.lower():
            return ResolvedTarget(
                title=vg_base,
                catalog_title=vg.title,
                price_clp=vg.price_clp,
                stock=vg.stock,
                is_in_catalog=True,
                matched_video_game=vg,
                source="query_candidate",
            )

    # 3. Anáfora / Multi-Turn Conversational Check
    # Si la consulta parece una pregunta de seguimiento ("¿y en steam?", "¿cuánto cuesta?")
    is_follow_up = any(trig in query.lower() for trig in _FOLLOW_UP_TRIGGERS)
    if is_follow_up and chat_history:
        # Explorar historial de más reciente a más antiguo
        for msg in reversed(chat_history[-6:]):
            content = msg.get("content", "") if isinstance(msg, dict) else getattr(msg, "content", "")
            c_norm = f" {_normalize(content)} "
            for kg in NEXUS_CANONICAL_CATALOG:
                for alias in kg.aliases:
                    if f" {_normalize(alias)} " in c_norm:
                        return ResolvedTarget(
                            title=kg.clean_title,
                            catalog_title=kg.title,
                            price_clp=kg.price_clp,
                            stock=kg.stock,
                            is_in_catalog=True,
                            canonical_game=kg,
                            source="history",
                        )

    # 4. Limpieza regex para extraer título de juegos no catalogados o externos
    clean_extracted = _INTENT_STRIP_REGEX.sub("", query).strip(" ?¿!¡:.,-")
    clean_words = clean_extracted.split()
    if clean_extracted and len(clean_words) <= 5 and not any(w in clean_extracted.lower() for w in ("juegos", "algo", "hola", "buenas", "ayuda")):
        # Verificar si por casualidad coincide con un alias
        extracted_norm = _normalize(clean_extracted)
        for kg in NEXUS_CANONICAL_CATALOG:
            for alias in kg.aliases:
                if _normalize(alias) == extracted_norm:
                    return ResolvedTarget(
                        title=kg.clean_title,
                        catalog_title=kg.title,
                        price_clp=kg.price_clp,
                        stock=kg.stock,
                        is_in_catalog=True,
                        canonical_game=kg,
                        source="clean_regex_catalog",
                    )
        # Es un juego externo o específico no catalogado (e.g. "Hogwarts Legacy", "Starfield")
        return ResolvedTarget(
            title=clean_extracted,
            catalog_title=clean_extracted,
            price_clp=0,
            stock=0,
            is_in_catalog=False,
            source="clean_regex_external",
        )

    # 5. Detección de recomendación general
    q_lower = query.lower()
    is_general = any(kw in q_lower for kw in ("recomiend", "catalogo", "catálogo", "que juegos", "qué juegos", "opciones", "lista", "hola", "buenas"))
    if is_general:
        primary = candidates[0] if candidates else None
        return ResolvedTarget(
            title=primary.title if primary else "Catálogo General Nexus",
            catalog_title=primary.title if primary else "Catálogo General Nexus",
            price_clp=primary.price_clp if primary else 0,
            stock=primary.stock if primary else 0,
            is_in_catalog=bool(primary),
            matched_video_game=primary,
            is_general_recommendation=True,
            source="general_recommendation",
        )

    # 6. Fallback final al primer candidato de similitud vectorial
    if candidates:
        top_cand = candidates[0]
        base_cand = top_cand.title.split(":")[0].split(" - ")[0].strip()
        return ResolvedTarget(
            title=base_cand,
            catalog_title=top_cand.title,
            price_clp=top_cand.price_clp,
            stock=top_cand.stock,
            is_in_catalog=True,
            matched_video_game=top_cand,
            source="top_candidate",
        )

    return ResolvedTarget(
        title=clean_extracted or query,
        catalog_title=clean_extracted or query,
        price_clp=0,
        stock=0,
        is_in_catalog=False,
        source="raw_fallback",
    )


def align_catalog_context(
    target: ResolvedTarget,
    retrieved_games: list[VideoGame],
) -> tuple[list[VideoGame], str]:
    """
    Sincroniza la lista de videojuegos recuperados para que el juego objetivo
    resuelto esté garantizado en la posición [0] y se formatee el contexto de forma óptima.
    """
    games = list(retrieved_games)

    if target.is_in_catalog and target.canonical_game:
        # Buscar si ya está presente en la lista
        existing_idx = -1
        for idx, g in enumerate(games):
            if g.title.lower() == target.canonical_game.title.lower() or target.canonical_game.clean_title.lower() in g.title.lower():
                existing_idx = idx
                break

        if existing_idx >= 0:
            # Moverlo al frente
            target_obj = games.pop(existing_idx)
            games.insert(0, target_obj)
        else:
            # Sintetizar el VideoGame y colocarlo al frente
            synthesized = VideoGame(
                id=uuid4(),
                title=target.canonical_game.title,
                description=target.canonical_game.description,
                price_clp=target.canonical_game.price_clp,
                stock=target.canonical_game.stock,
                genres=[Genre(name=g) for g in target.canonical_game.genres],
            )
            games.insert(0, synthesized)

    # Formatear el contexto en texto estructurado
    context_parts: list[str] = []
    for i, vg in enumerate(games[:4], 1):
        genres_str = ", ".join(g.name for g in (vg.genres or [])) if vg.genres else "N/A"
        stock_str = f"Stock: {vg.stock} unidades" if vg.stock > 0 else "SIN STOCK (0 unidades)"
        price_str = f"${vg.price_clp} CLP"
        context_parts.append(
            f"{i}. {vg.title} — {price_str}\n"
            f"   Géneros: {genres_str}\n"
            f"   {vg.description}\n"
            f"   {stock_str}"
        )

    formatted_context = "\n\n".join(context_parts) if context_parts else "No se encontraron videojuegos relevantes en el catálogo."
    return games, formatted_context


def build_unified_user_message(
    query: str,
    target: ResolvedTarget,
    intent: str,
    context: str,
    external_context: str,
    gaming_news: str,
    price_comparison: str,
    crew_analysis: str = "",
    chat_history: list[Any] | None = None,
) -> str:
    """
    Construye el mensaje de usuario final sincronizado con anclaje explícito del juego objetivo.
    Garantiza que el LLM nunca mezcle contextos ni alucine datos de otros títulos.
    """
    history_text = ""
    if chat_history:
        lines: list[str] = []
        for m in chat_history[-6:]:
            role = m.get("role") if isinstance(m, dict) else getattr(m, "role", "user")
            content = m.get("content") if isinstance(m, dict) else getattr(m, "content", "")
            lines.append(f"{role}: {content}")
        history_text = "\n".join(lines)

    parts: list[str] = []

    if history_text:
        parts.append(f"Historial de conversación:\n{history_text}\n")

    parts.append(f"Intención detectada (Laya AI): {intent}")

    if target.title:
        status_catalog = f"(Disponible en Nexus por ${target.price_clp:,} CLP, Stock: {target.stock})".replace(",", ".") if target.is_in_catalog else "(Juego externo o fuera de catálogo)"
        parts.append(f"🎯 VIDEOJUEGO OBJETIVO IDENTIFICADO: {target.title} {status_catalog}\n")

    parts.append(f"Videojuegos disponibles en Nexus:\n{context}\n")

    if external_context and external_context != "Sin datos externos.":
        parts.append(f"Dato curioso histórico (Wikipedia sobre '{target.title}'):\n{external_context}\n")

    if gaming_news and "Sin noticias" not in gaming_news:
        parts.append(f"Noticias recientes de videojuegos (Tavily API sobre '{target.title}'):\n{gaming_news}\n")

    if price_comparison and "Sin datos" not in price_comparison:
        parts.append(f"Comparativa de precios con otras tiendas (CheapShark API sobre '{target.title}'):\n{price_comparison}\n")

    if crew_analysis:
        parts.append(f"Análisis estratégico de agentes:\n{crew_analysis}\n")

    parts.append(f"Pregunta del cliente: {query}")

    return "\n".join(parts)
