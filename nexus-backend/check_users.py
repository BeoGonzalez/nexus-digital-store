import asyncio, os
from sqlalchemy import text
from dotenv import load_dotenv
load_dotenv()
from nexus_backend.database.engine import create_db_engine, NeonConnectionConfig

async def main():
    engine = create_db_engine(NeonConnectionConfig(database_url=os.getenv('DATABASE_URL')))
    async with engine.begin() as conn:
        res = await conn.execute(text('SELECT email, role FROM neon_auth."user"'))
        users = res.fetchall()
        print("Usuarios creados:")
        for u in users:
            print(f"- Email: {u.email} | Role: {u.role}")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())
