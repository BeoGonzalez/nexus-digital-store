from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "Nexus Digital Store"
    DEBUG: bool = False

    # Neon format: postgresql+asyncpg://<user>:<password>@<host>.neon.tech/<dbname>?ssl=require
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/nexus"
    NEON_POOLED: bool = False  # True = usar endpoint -pooler de Neon (pgbouncer)
    NEON_AUTH_URL: str = "https://ep-winter-dust-aylq45fu.neonauth.c-5.us-east-2.aws.neon.tech/neondb/auth"

    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 60

    GROQ_API_KEY: str = ""
    GROQ_MODEL_NAME: str = "openai/gpt-oss-120b"

    LANGSMITH_API_KEY: str = ""
    LANGSMITH_PROJECT: str = "nexus-digital-store"
    LANGSMITH_TRACING: str = "true"

    EMBEDDING_MODEL_NAME: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    EMBEDDING_DIMENSIONS: int = 384

    VECTOR_SEARCH_TOP_K: int = 5

    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
