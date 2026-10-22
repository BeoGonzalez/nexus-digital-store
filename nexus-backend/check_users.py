import os
from dotenv import load_dotenv

load_dotenv()

def main():
    print("Gestión de usuarios: Amazon Cognito User Pool")
    print(f"- Región: {os.getenv('COGNITO_REGION', 'us-east-1')}")
    print(f"- User Pool ID: {os.getenv('COGNITO_USER_POOL_ID', 'N/A')}")
    print(f"- App Client ID: {os.getenv('COGNITO_APP_CLIENT_ID', 'N/A')}")
    print("\nLos usuarios y roles no se almacenan en la base de datos relacional (Aurora), sino en Cognito.")

if __name__ == "__main__":
    main()
