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

    # Database (Amazon Aurora PostgreSQL / asyncpg)
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/nexus"
    DATABASE_READ_URL: str | None = None
    DB_SSL: bool = False
    RUN_DB_INIT: bool = True
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 5

    # AWS Cognito Identity
    COGNITO_REGION: str = "us-east-1"
    COGNITO_USER_POOL_ID: str = ""
    COGNITO_APP_CLIENT_ID: str = ""
    COGNITO_APP_CLIENT_SECRET: str = ""

    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 60

    # Groq LLM
    GROQ_API_KEY: str = ""
    GROQ_MODEL_NAME: str = "openai/gpt-oss-20b"
    GROQ_TEMPERATURE: float = 0.1

    # LangSmith Observability
    LANGSMITH_API_KEY: str = ""
    LANGSMITH_PROJECT: str = "nexus-digital-store"
    LANGSMITH_TRACING: str = "true"

    # Embeddings (local HuggingFace)
    EMBEDDING_MODEL_NAME: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    EMBEDDING_DIMENSIONS: int = 384

    # Pinecone Vector Store
    PINECONE_API_KEY: str = ""
    PINECONE_INDEX_NAME: str = "nexus-catalog"
    PINECONE_NAMESPACE: str = "nexus_chile"

    # Wikipedia Knowledge Retrieval
    WIKIPEDIA_LANG: str = "es"
    WIKIPEDIA_TOP_K: int = 1
    WIKIPEDIA_MAX_CHARS: int = 400

    # Tavily Gaming News API
    TAVILY_API_KEY: str = ""
    TAVILY_MAX_RESULTS: int = 3

    # CheapShark Video Game Deals & Price Comparison API
    CHEAPSHARK_ENABLED: bool = True
    CHEAPSHARK_USD_CLP_RATE: float = 950.0

    # Multi-Agent Orchestration (CrewAI + LangGraph)
    ENABLE_CREWAI_ORCHESTRATION: bool = True

    # Laya AI (Open Source System 1 Decision Engine)
    ENABLE_LAYA_DECISION_ENGINE: bool = True
    LAYA_MODEL_NAME: str = "convaiinnovations/laya"

    # Email Delivery (Google Gmail SMTP & App Passwords)
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_NAME: str = "Nexus Digital Store 🎮"
    GMAIL_USER: str = ""
    GMAIL_APP_PASSWORD: str = ""

    VECTOR_SEARCH_TOP_K: int = 5

    CORS_ORIGINS: list[str] = ["*"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
