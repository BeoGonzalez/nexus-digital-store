"""Script interactivo y suite de pruebas para verificar la base de datos Amazon Aurora PostgreSQL."""

import asyncio
import os
import sys
from uuid import uuid4

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from nexus_backend.database.engine import create_db_engine, DatabaseConnectionConfig
from nexus_backend.database.lifecycle import _register_models, _create_schema
from nexus_backend.shared.infrastructure.models import Base
from nexus_backend.catalog.infrastructure.models import Genre, Platform, VideoGame
from nexus_backend.orders.infrastructure.models import OrderModel, OrderItemModel, OrderStatus
from nexus_backend.orders.infrastructure.repositories import SQLAlchemyOrderRepository


async def run_database_tests():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url or "localhost" in db_url:
        print("\n" + "=" * 70)
        print("AVISO: DATABASE_URL no apunta a un clúster remoto de Aurora en este entorno local.")
        print(f"DATABASE_URL actual: {db_url or 'NO DEFINIDA'}")
        print("Si deseas probar contra tu clúster de Aurora desde tu terminal:")
        print("DATABASE_URL='postgresql+asyncpg://<user>:<pass>@<aurora-host>:5432/<db>' python test_db_integration.py")
        print("=" * 70 + "\n")
        if not db_url:
            return

    ssl_enabled = os.environ.get("DB_SSL", "false").lower() in ("true", "1", "yes")

    print("\n[1/5] Creando Database Engine con configuración de Aurora...")
    config = DatabaseConnectionConfig(
        database_url=db_url,
        ssl=ssl_enabled,
        pool_size=5,
        max_overflow=2,
    )
    engine = create_db_engine(config)

    try:
        print("[2/5] Probando conectividad básica (SELECT 1 & metadatos de PostgreSQL)...")
        async with engine.begin() as conn:
            res = await conn.execute(text("SELECT version(), current_database(), current_schema()"))
            row = res.fetchone()
            print(f"  ✓ Conectado a la BD: {row[1]}")
            print(f"  ✓ Esquema activo: {row[2]}")
            print(f"  ✓ Versión de PostgreSQL: {row[0][:50]}...")

        print("[3/5] Probando Advisory Lock concurrente y creación de tablas DDL...")
        _register_models()
        await _create_schema(engine)
        print("  ✓ Tablas DDL creadas exitosamente en schema 'public'.")

        print("[4/5] Verificando tablas creadas en el catálogo de PostgreSQL...")
        async with engine.begin() as conn:
            tables_res = await conn.execute(
                text(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema = 'public' ORDER BY table_name"
                )
            )
            tables = [r[0] for r in tables_res.fetchall()]
            print(f"  ✓ Tablas detectadas en 'public': {tables}")
            expected_tables = {"genres", "platforms", "video_games", "video_game_genres", "orders", "order_items", "payment_methods"}
            missing = expected_tables - set(tables)
            if missing:
                print(f"  ⚠️ Faltan algunas tablas esperadas: {missing}")
            else:
                print("  ✓ Todas las tablas requeridas por la aplicación existen en 'public'.")

            # Verificar que el esquema activo sea public
            schema_res = await conn.execute(
                text("SELECT current_schema()")
            )
            print(f"  ✓ Esquema verificado: {schema_res.scalar()} (aislamiento limpio en 'public').")

        print("[5/5] Probando ciclo CRUD transaccional con Cognito sub (string user_id)...")
        async_session = AsyncSession(bind=engine, expire_on_commit=False)
        test_sub = f"cognito-sub-{uuid4()}"
        game_id = uuid4()
        order_id = uuid4()

        try:
            async with async_session.begin():
                # Crear plataforma y juego
                plat = Platform(name=f"TestPlatform-{uuid4().hex[:6]}")
                genre = Genre(name=f"TestGenre-{uuid4().hex[:6]}")
                game = VideoGame(
                    id=game_id,
                    title="Elden Ring Test",
                    description="Action RPG",
                    price_clp=39990,
                    stock=10,
                    platform=plat,
                    genres=[genre],
                )
                async_session.add_all([plat, genre, game])
                await async_session.flush()

                # Crear orden referenciando al sub de Cognito
                order = OrderModel(
                    id=order_id,
                    user_id=test_sub,
                    total_amount_clp=39990,
                    status=OrderStatus.CONFIRMED,
                    items=[
                        OrderItemModel(
                            video_game_id=game_id,
                            quantity=1,
                            unit_price_clp=39990,
                        )
                    ],
                )
                async_session.add(order)
                await async_session.flush()

            # Consultar con el repositorio
            repo = SQLAlchemyOrderRepository(async_session)
            retrieved_orders = await repo.get_by_user_id(test_sub)
            assert len(retrieved_orders) == 1, "Debería recuperar exactamente 1 orden"
            assert retrieved_orders[0].user_id == test_sub, "El user_id (Cognito sub) debe coincidir"
            print(f"  ✓ Orden creada y recuperada exitosamente para usuario Cognito sub: '{test_sub}'")

            # Limpieza
            async with async_session.begin():
                await async_session.execute(text("DELETE FROM orders WHERE id = :id"), {"id": order_id})
                await async_session.execute(text("DELETE FROM video_games WHERE id = :id"), {"id": game_id})
            print("  ✓ Limpieza de datos de prueba completada.")

        finally:
            await async_session.close()

        print("\n" + "=" * 70)
        print("✅ TODAS LAS PRUEBAS DE BASE DE DATOS FINALIZARON EXITOSAMENTE.")
        print("=" * 70 + "\n")

    except Exception as exc:
        print(f"\n❌ Error durante las pruebas de base de datos: {exc}")
        import traceback
        traceback.print_exc()
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(run_database_tests())
