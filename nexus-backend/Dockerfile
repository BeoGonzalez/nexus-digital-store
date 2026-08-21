# Stage 1: Builder
# Utilizamos la imagen oficial de Astral para uv, combinada con Python 3.13 slim
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder

# Configuramos variables de entorno para optimizar uv y Python
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

# Instalamos dependencias usando la caché montada de Docker para uv
# Primero copiamos solo los archivos de definición de dependencias para aprovechar la caché de capas
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# Stage 2: Final
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    # PYTHONPATH configurado para que Python detecte el directorio src/
    PYTHONPATH=/app/src

WORKDIR /app

# Copiamos el entorno virtual (dependencias) desde el builder
COPY --from=builder /app/.venv /app/.venv

# Copiamos el código fuente de la aplicación
COPY src /app/src

# Exponemos el puerto de la API
EXPOSE 8000

# Aseguramos que los comandos se ejecuten dentro del entorno virtual gestionado por uv
ENV PATH="/app/.venv/bin:$PATH"

# Comando de inicio
CMD ["uv", "run", "uvicorn", "nexus_backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
