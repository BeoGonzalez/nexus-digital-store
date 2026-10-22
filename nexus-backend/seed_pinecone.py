#!/usr/bin/env python3
"""
🌲 Nexus Digital Store — Seeder de Catálogo en Pinecone Vector DB
================================================================
Este script genera embeddings semánticos multilingües (384 dimensiones)
y sube una colección completa de videojuegos con sus metadatos a Pinecone.

Uso:
  cd nexus-backend && PYTHONPATH=src .venv/bin/python seed_pinecone.py
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
import uuid
from typing import Any

from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

from pinecone import Pinecone
from nexus_backend.config import get_settings
from nexus_backend.ai_assistant.infrastructure.embeddings import HuggingFaceEmbeddingAdapter

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("seed_pinecone")


# Catálogo curado de videojuegos de alta calidad para la tienda gamer
GAMES_CATALOG = [
    {
        "title": "Elden Ring",
        "description": "Obra maestra del rol de acción y fantasía oscura desarrollada por FromSoftware y Hidetaka Miyazaki con la colaboración de George R.R. Martin. Explora las sobrecogedoras Tierras Intermedias a caballo, desafía a semidioses corruptos y reclama el poder del Círculo de Elden. Combate soulslike exigente y libertad absoluta.",
        "price_clp": 39990,
        "stock": 18,
        "genres": ["Action RPG", "Soulslike", "Open World", "Dark Fantasy"],
        "image_url": "https://images.unsplash.com/photo-1542751371-adc38448a05e?q=80&w=800",
    },
    {
        "title": "Cyberpunk 2077: Phantom Liberty",
        "description": "Aventura de rol, acción y disparos en primera persona ambientada en la megalópolis futurista de Night City. Conviértete en V, un mercenario urbano mejorado cibernéticamente. Incluye la aclamada expansión Phantom Liberty, trama de espionaje con Idris Elba, árbol de habilidades renovado y combate vehicular.",
        "price_clp": 34990,
        "stock": 25,
        "genres": ["RPG", "Sci-Fi", "Cyberpunk", "Open World", "FPS"],
        "image_url": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?q=80&w=800",
    },
    {
        "title": "Hollow Knight",
        "description": "Aclamado metroidvania en 2D ambientado en Hallownest, un vasto reino subterráneo en ruinas habitado por insectos y guerreros caídos. Controla a un misterioso caballero silencioso, perfecciona habilidades con el aguijón, descubre pasadizos secretos y enfréntate a más de 30 jefes épicos con una banda sonora inolvidable.",
        "price_clp": 8500,
        "stock": 40,
        "genres": ["Metroidvania", "Indie", "Action", "Souls-lite"],
        "image_url": "https://images.unsplash.com/photo-1550745165-9bc0b252726f?q=80&w=800",
    },
    {
        "title": "God of War Ragnarök",
        "description": "Kratos y Atreus se embarcan en un viaje mítico a través de los Nueve Reinos en busca de respuestas antes de que estalle la batalla profetizada que acabará con el mundo. Combate visceral con el hacha Leviatán y las Espadas del Caos, mitología nórdica profunda y una emotiva historia padre-hijo.",
        "price_clp": 44990,
        "stock": 12,
        "genres": ["Action", "Adventure", "Mythology", "Hack and Slash"],
        "image_url": "https://images.unsplash.com/photo-1538481199705-c710c4e965fc?q=80&w=800",
    },
    {
        "title": "Black Myth: Wukong",
        "description": "Juego de rol y acción inspirado en la mitología china y la novela clásica Peregrinación al Oeste. Encarna al Destinado y domina las artes del báculo, transformaciones mágicas y hechizos taoístas mientras exploras tierras ancestrales y enfrentas monstruos colosales con gráficos fotorrealistas en Unreal Engine 5.",
        "price_clp": 42990,
        "stock": 20,
        "genres": ["Action RPG", "Soulslike", "Mythology", "Action"],
        "image_url": "https://images.unsplash.com/photo-1511512578047-dfb367046420?q=80&w=800",
    },
    {
        "title": "Baldur's Gate 3",
        "description": "El CRPG definitivo de Larian Studios ambientado en el universo de Dungeons & Dragons. Secuestrado por los azotamentes, una larva ilícida implantada en tu cerebro te otorga poderes oscuros. Reúne a tu grupo, toma decisiones con ramificaciones morales ilimitadas y combate por turnos táctico galardonado como Juego del Año.",
        "price_clp": 41990,
        "stock": 15,
        "genres": ["CRPG", "Turn-Based Strategy", "Fantasy", "D&D"],
        "image_url": "https://images.unsplash.com/photo-1563089145-599997674d42?q=80&w=800",
    },
    {
        "title": "The Witcher 3: Wild Hunt",
        "description": "Conviértete en Geralt de Rivia, cazador de monstruos a sueldo en un mundo de fantasía oscura desgarrado por la guerra. Sigue el rastro de la Niña de la Profecía a través de Novigrado, las islas Skellige y Velen. Caza bestias con espadas de plata, pociones alquímicas y señales mágicas en una narrativa magistral.",
        "price_clp": 19990,
        "stock": 30,
        "genres": ["RPG", "Open World", "Dark Fantasy", "Story-Rich"],
        "image_url": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?q=80&w=800",
    },
    {
        "title": "Red Dead Redemption 2",
        "description": "Épica del salvaje oeste estadounidense a finales del siglo XIX creada por Rockstar Games. Sigue a Arthur Morgan y la banda de Van der Linde mientras huyen de agentes federales y cazarrecompensas. Mundo abierto hiperrealista con caza, pesca, atracos y una de las historias más conmovedoras del medio.",
        "price_clp": 29990,
        "stock": 16,
        "genres": ["Action", "Adventure", "Open World", "Western"],
        "image_url": "https://images.unsplash.com/photo-1542751371-adc38448a05e?q=80&w=800",
    },
    {
        "title": "Resident Evil 4 Remake",
        "description": "Sobrevive a la pesadilla en un pueblo rural europeo dominado por el parásito de Las Plagas. El agente especial Leon S. Kennedy es enviado a rescatar a la hija del presidente de los Estados Unidos. Reinvención magistral del clásico con combate tenso de disparos en tercera persona, gestión de inventario y terror de acción.",
        "price_clp": 31990,
        "stock": 14,
        "genres": ["Survival Horror", "Action", "Zombies", "Shooter"],
        "image_url": "https://images.unsplash.com/photo-1550745165-9bc0b252726f?q=80&w=800",
    },
    {
        "title": "Silent Hill 2 Remake",
        "description": "James Sunderland recibe una carta firmada por su difunta esposa Mary que le pide encontrarse en el enigmático pueblo de Silent Hill envuelto en niebla. Terror psicológico opresivo, acertijos perturbadores, criaturas icónicas como Pyramid Head y una atmósfera sonora estremecedora.",
        "price_clp": 38990,
        "stock": 11,
        "genres": ["Psychological Horror", "Survival Horror", "Atmospheric"],
        "image_url": "https://images.unsplash.com/photo-1538481199705-c710c4e965fc?q=80&w=800",
    },
    {
        "title": "Sekiro: Shadows Die Twice",
        "description": "En el periodo Sengoku de finales del siglo XVI en Japón, encarna al 'Lobo de un solo brazo', un shinobi desfigurado que debe rescatar a su joven señor. Mecánica revolucionaria basada en el desvío milimétrico con katana (parry) y el uso de una prótesis shinobi con gancho de agarre, hacha y shurikens.",
        "price_clp": 32990,
        "stock": 10,
        "genres": ["Action", "Soulslike", "Stealth", "Ninja"],
        "image_url": "https://images.unsplash.com/photo-1511512578047-dfb367046420?q=80&w=800",
    },
    {
        "title": "Hades II",
        "description": "El galardonado roguelike de acción y mazmorras de Supergiant Games regresa. Lucha como Melínoë, la princesa del Inframundo y hermana de Zagreus, usando hechicería y artes oscuras para desafiar al Titán del Tiempo, Cronos. Bendiciones de dioses olímpicos, combate frenético y arte espectacular.",
        "price_clp": 18500,
        "stock": 28,
        "genres": ["Roguelike", "Action", "Indie", "Mythology"],
        "image_url": "https://images.unsplash.com/photo-1563089145-599997674d42?q=80&w=800",
    },
    {
        "title": "Dead Space Remake",
        "description": "El clásico de horror y ciencia ficción completamente reconstruido desde cero con el motor Frostbite. Isaac Clarke es un ingeniero ordinario en una misión de reparación de la nave minera USG Ishimura, donde la tripulación ha sido masacrada por mutaciones alienígenas llamadas necromorfos. Desmembramiento estratégico.",
        "price_clp": 27990,
        "stock": 10,
        "genres": ["Sci-Fi", "Survival Horror", "Gore", "Shooter"],
        "image_url": "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?q=80&w=800",
    },
    {
        "title": "EA Sports FC 25",
        "description": "La máxima experiencia de simulación de fútbol mundial con tecnología FC IQ, control táctico modernizado, animaciones hiperrealistas basadas en datos volumétricos de partidos reales y los modos Ultimate Team y Carrera más completos con licencias de las principales ligas y clubes del planeta.",
        "price_clp": 48990,
        "stock": 35,
        "genres": ["Sports", "Soccer", "Simulation", "Multiplayer"],
        "image_url": "https://images.unsplash.com/photo-1542751371-adc38448a05e?q=80&w=800",
    },
    {
        "title": "Stardew Valley",
        "description": "Has heredado la vieja parcela de tu abuelo en Stardew Valley. Equipado con herramientas de segunda mano y unas pocas monedas, te dispones a comenzar una nueva vida. Cultiva hortalizas, cría animales, explora cuevas mineras con monstruos, haz amigos en el pueblo y revitaliza el centro comunitario.",
        "price_clp": 7500,
        "stock": 50,
        "genres": ["Farming Sim", "RPG", "Cozy", "Indie", "Pixel Art"],
        "image_url": "https://images.unsplash.com/photo-1550745165-9bc0b252726f?q=80&w=800",
    },
    {
        "title": "Doom Eternal",
        "description": "Los ejércitos del infierno han invadido la Tierra. Conviértete en el Slayer en una épica campaña monojugador para vencer demonios a través de dimensiones. Disparos ultrarrápidos en primera persona donde el ataque agresivo recupera salud, munición y armadura.",
        "price_clp": 16990,
        "stock": 20,
        "genres": ["FPS", "Action", "Fast-Paced", "Demons"],
        "image_url": "https://images.unsplash.com/photo-1538481199705-c710c4e965fc?q=80&w=800",
    },
    {
        "title": "Persona 5 Royal",
        "description": "Ponte la máscara de Joker y únete a los Ladrones Fantasma de Corazones mientras ejecutan grandes atracos psicológicos, se infiltran en los palacios de adultos corruptos y cambian sus corazones. Estilo visual anime electrizante, banda sonora de acid jazz y vida escolar en Tokio.",
        "price_clp": 33990,
        "stock": 15,
        "genres": ["JRPG", "Turn-Based", "Anime", "Story-Rich"],
        "image_url": "https://images.unsplash.com/photo-1511512578047-dfb367046420?q=80&w=800",
    },
    {
        "title": "Monster Hunter: World",
        "description": "Bienvenido al Nuevo Mundo. Asume el papel de un cazador y mata monstruos feroces en un ecosistema viviente donde puedes usar el paisaje y sus habitantes a tu favor. Caza en solitario o con hasta otros tres jugadores en cooperativo online, forja armas con piezas de monstruos.",
        "price_clp": 22990,
        "stock": 17,
        "genres": ["Action RPG", "Co-op", "Open World", "Hunting"],
        "image_url": "https://images.unsplash.com/photo-1563089145-599997674d42?q=80&w=800",
    },
    {
        "title": "Grand Theft Auto V",
        "description": "Cuando un joven estafador callejero, un ladrón de bancos retirado y un psicópata aterrador se ven involucrados con lo más aterrador del submundo criminal, deben realizar una serie de peligrosos atracos para sobrevivir en una ciudad despiadada.",
        "price_clp": 15990,
        "stock": 45,
        "genres": ["Action", "Open World", "Crime", "Multiplayer"],
        "image_url": "https://images.unsplash.com/photo-1542751371-adc38448a05e?q=80&w=800",
    },
    {
        "title": "Celeste",
        "description": "Ayuda a Madeline a sobrevivir a sus demonios internos en su viaje a la cima de la montaña Celeste en este ajustado y desafiante juego de plataformas hecho a mano de los creadores del clásico multijugador TowerFall.",
        "price_clp": 6990,
        "stock": 35,
        "genres": ["Platformer", "Precision", "Indie", "Emotional"],
        "image_url": "https://images.unsplash.com/photo-1550745165-9bc0b252726f?q=80&w=800",
    },
]


async def seed_pinecone():
    settings = get_settings()

    api_key = settings.PINECONE_API_KEY
    index_name = settings.PINECONE_INDEX_NAME
    primary_namespace = settings.PINECONE_NAMESPACE or "nexus_chile"

    logger.info("Conectando a Pinecone: index='%s', namespace='%s'...", index_name, primary_namespace)
    pc = Pinecone(api_key=api_key)

    # Verificar que el índice existe
    existing_indexes = [idx.name for idx in pc.list_indexes()]
    if index_name not in existing_indexes:
        logger.error("El índice '%s' no existe en Pinecone. Índices encontrados: %s", index_name, existing_indexes)
        sys.exit(1)

    index = pc.Index(index_name)

    logger.info("Cargando modelo de embeddings multilingüe (%s)...", settings.EMBEDDING_MODEL_NAME)
    embedding_adapter = HuggingFaceEmbeddingAdapter(model_name=settings.EMBEDDING_MODEL_NAME)

    # Preparar registros para Pinecone
    records_to_upsert: list[dict[str, Any]] = []

    logger.info("Generando vectores de 384 dimensiones para %d videojuegos...", len(GAMES_CATALOG))
    for i, game in enumerate(GAMES_CATALOG, 1):
        genres_str = ", ".join(game["genres"])
        # Texto enriquecido para búsqueda semántica potente
        text_to_embed = f"{game['title']} - Géneros: {genres_str}. {game['description']}"

        vector = await embedding_adapter.embed_text(text_to_embed)
        game_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, game["title"]))

        metadata = {
            "id": game_id,
            "title": game["title"],
            "description": game["description"],
            "price_clp": int(game["price_clp"]),
            "stock": int(game["stock"]),
            "genres": genres_str,
            "image_url": game.get("image_url", ""),
        }

        records_to_upsert.append({
            "id": game_id,
            "values": vector,
            "metadata": metadata,
        })
        logger.info("  [%d/%d] Vectorizado: %s (ID: %s)", i, len(GAMES_CATALOG), game["title"], game_id)

    # Subir en lotes al namespace principal y al namespace 'catalog' para máxima redundancia
    namespaces_to_populate = list({primary_namespace, "catalog", "nexus_chile"})

    for ns in namespaces_to_populate:
        logger.info("Subiendo %d videojuegos a Pinecone en namespace '%s'...", len(records_to_upsert), ns)
        # Upsert en Pinecone
        batch_size = 50
        for i in range(0, len(records_to_upsert), batch_size):
            batch = records_to_upsert[i : i + batch_size]
            index.upsert(vectors=batch, namespace=ns)
        logger.info("  ✔ Namespace '%s' poblado exitosamente.", ns)

    # Verificación final mediante búsqueda semántica de prueba
    logger.info("\n🧪 Ejecutando prueba de búsqueda semántica en Pinecone...")
    test_queries = [
        "juego difícil tipo soulslike de fantasía oscura y semidioses",
        "terror espacial con extraterrestres y gore",
        "juegos acogedores relajantes de granja y animales",
    ]

    for q in test_queries:
        query_vector = await embedding_adapter.embed_text(q)
        res = index.query(
            vector=query_vector,
            top_k=2,
            namespace=primary_namespace,
            include_metadata=True,
        )
        matches = res.get("matches", [])
        top_match = matches[0] if matches else None
        if top_match:
            logger.info("  🔍 Consulta: '%s'", q)
            logger.info(
                "     ➔ Top Match: '%s' (Score: %.4f, Precio: $%s CLP)",
                top_match["metadata"]["title"],
                top_match["score"],
                f"{top_match['metadata']['price_clp']:,}".replace(",", "."),
            )

    stats = index.describe_index_stats()
    logger.info("\n🎉 ¡ÉXITO! Catálogo de Pinecone actualizado completamente:")
    logger.info("   Total de vectores en índice: %d", stats.total_vector_count)
    logger.info("   Namespaces: %s", stats.namespaces)


if __name__ == "__main__":
    asyncio.run(seed_pinecone())

