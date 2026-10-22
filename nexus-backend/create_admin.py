"""Script automatizado para crear y configurar la cuenta de Administrador en Amazon Cognito."""

import asyncio
import os
import sys

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import httpx
from nexus_backend.config import get_settings
from nexus_backend.auth.infrastructure.cognito import compute_secret_hash


async def create_admin():
    settings = get_settings()

    admin_email = os.getenv("ADMIN_EMAIL", "admin@nexus.com")
    admin_password = os.getenv("ADMIN_PASSWORD", "AdminPassword123!")
    admin_name = os.getenv("ADMIN_NAME", "Administrador Nexus")

    print("\n" + "=" * 65)
    print("🚀 Creando cuenta de Administrador en Amazon Cognito")
    print("=" * 65)
    print(f"Región: {settings.COGNITO_REGION}")
    print(f"User Pool ID: {settings.COGNITO_USER_POOL_ID or 'No configurado en .env'}")
    print(f"App Client ID: {settings.COGNITO_APP_CLIENT_ID or 'No configurado en .env'}")
    print(f"Email Administrador: {admin_email}")
    print("=" * 65)

    if not settings.COGNITO_APP_CLIENT_ID:
        print("\n❌ Error: Debes configurar COGNITO_APP_CLIENT_ID y COGNITO_USER_POOL_ID en las variables de entorno.")
        _print_cli_alternative(settings, admin_email, admin_password)
        return

    # 1. Registrar usuario vía SignUp en Cognito
    idp_url = f"https://cognito-idp.{settings.COGNITO_REGION}.amazonaws.com/"
    payload = {
        "ClientId": settings.COGNITO_APP_CLIENT_ID,
        "Username": admin_email,
        "Password": admin_password,
        "UserAttributes": [
            {"Name": "email", "Value": admin_email},
            {"Name": "name", "Value": admin_name},
        ],
    }
    if settings.COGNITO_APP_CLIENT_SECRET:
        payload["SecretHash"] = compute_secret_hash(
            admin_email, settings.COGNITO_APP_CLIENT_ID, settings.COGNITO_APP_CLIENT_SECRET
        )

    headers = {
        "Content-Type": "application/x-amz-json-1.1",
        "X-Amz-Target": "AWSCognitoIdentityProviderService.SignUp",
    }

    print("\n[1/3] Registrando usuario en Cognito...")
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.post(idp_url, json=payload, headers=headers)
            data = resp.json()

            if resp.status_code == 200:
                print(f"  ✓ Usuario {admin_email} registrado exitosamente.")
                user_sub = data.get("UserSub")
                print(f"  ✓ Cognito Sub: {user_sub}")
            else:
                err_type = str(data.get("__type", "")).split("#")[-1]
                if err_type == "UsernameExistsException":
                    print(f"  ℹ️ El usuario {admin_email} ya existe en Cognito.")
                else:
                    print(f"  ⚠️ Respuesta de Cognito ({err_type}): {data.get('message')}")
        except Exception as exc:
            print(f"  ❌ Error de conexión con Cognito: {exc}")
            _print_cli_alternative(settings, admin_email, admin_password)
            return

    # 2. Intentar asignación con boto3 si está disponible y hay credenciales AWS
    print("\n[2/3] Verificando permisos de administración con AWS SDK (boto3)...")
    try:
        import boto3
        cognito_client = boto3.client("cognito-idp", region_name=settings.COGNITO_REGION)

        # Crear grupo 'admin' si no existe
        try:
            cognito_client.create_group(
                GroupName="admin",
                UserPoolId=settings.COGNITO_USER_POOL_ID,
                Description="Grupo de Administradores de Nexus Store",
            )
            print("  ✓ Grupo 'admin' creado en Cognito User Pool.")
        except cognito_client.exceptions.GroupExistsException:
            print("  ✓ Grupo 'admin' ya existe en Cognito.")

        # Confirmar usuario si estaba pendiente
        try:
            cognito_client.admin_confirm_sign_up(
                UserPoolId=settings.COGNITO_USER_POOL_ID,
                Username=admin_email,
            )
            print(f"  ✓ Usuario {admin_email} confirmado administrativamente.")
        except Exception:
            pass

        # Agregar usuario al grupo admin
        cognito_client.admin_add_user_to_group(
            UserPoolId=settings.COGNITO_USER_POOL_ID,
            Username=admin_email,
            GroupName="admin",
        )
        print(f"  ✓ Usuario {admin_email} añadido al grupo 'admin'.")

    except ImportError:
        print("  ℹ️ boto3 no está instalado localmente. Recuerda confirmar el usuario en la consola o vía AWS CLI.")
    except Exception as e:
        print(f"  ℹ️ Aviso AWS SDK ({e}). Puedes confirmar el usuario vía AWS CLI:")

    print("\n[3/3] Resumen de credenciales de Administrador:")
    print("-" * 50)
    print(f"  Email:      {admin_email}")
    print(f"  Password:   {admin_password}")
    print(f"  Rol:        admin (acceso total al panel /admin)")
    print("-" * 50)
    print("\n¡Listo! Ahora puedes ingresar a la tienda con estas credenciales para acceder al Panel de Administración.\n")


def _print_cli_alternative(settings, email, password):
    pool_id = settings.COGNITO_USER_POOL_ID or "<TU_USER_POOL_ID>"
    region = settings.COGNITO_REGION or "us-east-1"
    print("\nAlternativa vía AWS CLI:")
    print(f"1. Crear usuario:")
    print(f"   aws cognito-idp admin-create-user --user-pool-id {pool_id} --username {email} --user-attributes Name=email,Value={email} Name=email_verified,Value=true --message-action SUPPRESS --region {region}")
    print(f"2. Asignar contraseña permanente:")
    print(f"   aws cognito-idp admin-set-user-password --user-pool-id {pool_id} --username {email} --password \"{password}\" --permanent --region {region}")
    print(f"3. Crear y asignar al grupo admin:")
    print(f"   aws cognito-idp create-group --group-name admin --user-pool-id {pool_id} --region {region}")
    print(f"   aws cognito-idp admin-add-user-to-group --user-pool-id {pool_id} --username {email} --group-name admin --region {region}")


if __name__ == "__main__":
    asyncio.run(create_admin())
