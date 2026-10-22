import pytest
from nexus_backend.ai_assistant.application.context_resolver import (
    align_catalog_context,
    build_unified_user_message,
    resolve_target_game,
)
from nexus_backend.catalog.domain.entities import VideoGame


def test_resolve_target_game_by_alias():
    # Caso 1: Cyberpunk 2077
    target = resolve_target_game("¿A cuánto está Cyberpunk 2077 en otras tiendas?")
    assert target.title == "Cyberpunk 2077"
    assert target.is_in_catalog is True
    assert target.price_clp == 34990

    # Caso 2: Phantom Liberty
    target2 = resolve_target_game("Háblame de Phantom Liberty por favor")
    assert target2.title == "Cyberpunk 2077"
    assert target2.is_in_catalog is True

    # Caso 3: Elden Ring
    target3 = resolve_target_game("¿Tienen Elden Ring disponible?")
    assert target3.title == "Elden Ring"
    assert target3.price_clp == 39990

    # Caso 4: Wukong
    target4 = resolve_target_game("Qué tal es Black Myth Wukong?")
    assert target4.title == "Black Myth: Wukong"
    assert target4.price_clp == 42990


def test_resolve_target_game_multi_turn_history():
    history = [
        {"role": "user", "content": "Hola, ¿de qué trata Elden Ring?"},
        {"role": "assistant", "content": "Elden Ring es un soulslike de FromSoftware..."},
    ]
    # Pregunta de seguimiento sin mencionar el nombre del juego
    target = resolve_target_game("¿Y a cuánto está en steam comparado con nexus?", chat_history=history)
    assert target.title == "Elden Ring"
    assert target.is_in_catalog is True
    assert target.price_clp == 39990
    assert target.source == "history"


def test_resolve_target_game_external_title():
    target = resolve_target_game("¿A cuánto está Hogwarts Legacy en otras tiendas?")
    assert "Hogwarts Legacy" in target.title
    assert target.is_in_catalog is False
    assert target.price_clp == 0


def test_align_catalog_context_bubbles_target():
    target = resolve_target_game("¿A cuánto está Cyberpunk 2077 en otras tiendas?")
    
    # Supongamos que Pinecone devolvió Hollow Knight primero y Cyberpunk segundo
    g1 = VideoGame(title="Hollow Knight", description="Metroidvania", price_clp=8500, stock=20)
    g2 = VideoGame(title="Cyberpunk 2077: Phantom Liberty", description="RPG Sci-Fi", price_clp=34990, stock=25)
    
    aligned_games, context_text = align_catalog_context(target, [g1, g2])
    
    # Debe haber colocado Cyberpunk 2077 de primero
    assert aligned_games[0].title == "Cyberpunk 2077: Phantom Liberty"
    assert "1. Cyberpunk 2077: Phantom Liberty" in context_text
    assert "$34990 CLP" in context_text


def test_build_unified_user_message():
    target = resolve_target_game("¿A cuánto está Elden Ring?")
    msg = build_unified_user_message(
        query="¿A cuánto está Elden Ring?",
        target=target,
        intent="price_comparison",
        context="1. Elden Ring - $39.990 CLP",
        external_context="Trivia de Elden Ring",
        gaming_news="Parche 1.12 disponible",
        price_comparison="MÁS BARATO en Nexus por $10.000 CLP vs Steam",
    )
    assert "🎯 VIDEOJUEGO OBJETIVO IDENTIFICADO: Elden Ring" in msg
    assert "Trivia de Elden Ring" in msg
    assert "MÁS BARATO en Nexus" in msg
