# syntax=docker/dockerfile:1

# =========================================================
# Stage 1: builder
# Installs uv, resolves the locked dependency set into a
# virtualenv, then installs the project itself.
# =========================================================
FROM python:3.12-slim AS builder

# uv binary, copied straight from the official distroless image.
# Faster and more reproducible than `pip install uv`.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Build tools needed for compiling wheels that don't ship prebuilt
# manylinux binaries on slim images (e.g. some torch/tokenizers deps).
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

# uv-specific env: don't hardlink from the cache into the venv (breaks
# across the two-stage COPY below), and write bytecode at install time
# instead of on first import.
ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PROJECT_ENVIRONMENT=/app/.venv

# Copy only the dependency manifests first. This layer only
# invalidates when pyproject.toml/uv.lock change, not on every
# source edit -> dependency install is cached across code changes.
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project

# Now bring in the actual application source and finish the sync
# (installs the project itself into the same venv).
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen

# =========================================================
# Stage 2: runtime
# Only the built venv + app code, no compilers, no uv, no
# pip cache. This is the image that actually ships.
# =========================================================
FROM python:3.12-slim AS runtime

WORKDIR /app

# libpq is needed at runtime for asyncpg's underlying libpq calls
# on some platforms; harmless if unused.
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/app /app/app
COPY --from=builder /app/alembic /app/alembic
COPY --from=builder /app/alembic.ini /app/alembic.ini

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_PORT=8000

EXPOSE 8000

# Basic container-level healthcheck against the /health route
# already defined in app/main.py.
HEALTHCHECK --interval=15s --timeout=3s --start-period=10s --retries=5 \
    CMD python -c "import urllib.request,os,sys; \
    urllib.request.urlopen(f'http://127.0.0.1:{os.environ.get(\"APP_PORT\",\"8000\")}/health', timeout=2)" || exit 1

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${APP_PORT:-8000}"]
