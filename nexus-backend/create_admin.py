import requests
import asyncio
from sqlalchemy import text
from nexus_backend.database.engine import create_db_engine, NeonConnectionConfig
import os
from dotenv import load_dotenv

load_dotenv()

async def create_admin():
    email = "admin@nexus.com"
    password = "AdminPassword123!"
    name = "Administrador"
    
    # 1. Register user via Neon Auth (better-auth endpoint)
    url = "https://ep-winter-dust-aylq45fu.neonauth.c-5.us-east-2.aws.neon.tech/neondb/auth/sign-up/email"
    print(f"Registrando {email} en Neon Auth...")
    resp = requests.post(url, json={
        "email": email,
        "password": password,
        "name": name
    }, headers={"Origin": "http://localhost:3000"})
    
    if resp.status_code >= 400:
        print("Error en registro:", resp.text)
        # Continue anyway, might already exist
    else:
        print("Registro exitoso.")
        
    # 2. Update role in database
    db_url = os.environ.get("DATABASE_URL")
    config = NeonConnectionConfig(database_url=db_url)
    engine = create_db_engine(config)
    
    async with engine.begin() as conn:
        print("Actualizando rol a admin en la base de datos...")
        result = await conn.execute(
            text("UPDATE neon_auth.\"user\" SET role = 'admin' WHERE email = :email"),
            {"email": email}
        )
        print(f"Filas afectadas: {result.rowcount}")
        
    await engine.dispose()
    print(f"\n¡Usuario Admin listo!\nEmail: {email}\nPassword: {password}")

if __name__ == "__main__":
    asyncio.run(create_admin())
