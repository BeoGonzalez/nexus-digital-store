# ==============================================================================
# Stage 1: Builder (Compilación y resolución de dependencias con Astral uv)
# ==============================================================================
FROM ghcr.io/astral-sh/uv:python3.11-bookworm-slim AS builder

# Configuración de rendimiento y resiliencia de red para uv
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_HTTP_TIMEOUT=300 \
    UV_CONCURRENT_DOWNLOADS=4

WORKDIR /app

# Copiamos manifiestos de dependencias
COPY pyproject.toml uv.lock ./

# Sincronización determinista aprovechando la caché de montaje de Docker
# Se usa --no-install-project para cachear todas las dependencias pesadas
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# ==============================================================================
# Stage 2: Runtime (Imagen de producción ultraligera y sin build tools)
# ==============================================================================
FROM python:3.11-slim-bookworm AS runner

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app/src \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

# Copiar el entorno virtual optimizado desde el builder
COPY --from=builder /app/.venv /app/.venv

# Copiar código fuente y manifiestos
COPY pyproject.toml README.md ./
COPY src /app/src

EXPOSE 8000

# Healthcheck nativo sin requerir curl instalado
HEALTHCHECK --interval=15s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health')" || exit 1

CMD ["uvicorn", "nexus_backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
