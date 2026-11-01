# ==============================================================================
# Production Multi-Stage Dockerfile for Google A2A Multi-Agent System
# Frameworks: Google ADK (Agent Development Kit), LangChain, LangGraph, FastAPI
# ==============================================================================

# Stage 1: Build & Dependencies
FROM python:3.12-slim AS builder

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install uv for deterministic high-speed package installation
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy dependency manifests
COPY pyproject.toml uv.lock ./

# Install virtualenv and all dependencies into /app/.venv
RUN uv sync --frozen --no-dev --no-install-project

# ==============================================================================
# Stage 2: Minimal Distroless/Slim Production Runtime
# ==============================================================================
FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH" \
    PORT=8000 \
    HOST=0.0.0.0

WORKDIR /app

# Install runtime system libraries (SQLite, CA certificates, curl for healthcheck)
RUN apt-get update && apt-get install -y --no-install-recommends \
    sqlite3 \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create secure non-root system user
RUN groupadd -r a2a && useradd -r -g a2a -d /app -s /sbin/nologin a2a

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application source code
COPY a2a/ /app/a2a/
COPY podcast_agent/ /app/podcast_agent/
COPY sql_agent/ /app/sql_agent/
COPY rag_agent/ /app/rag_agent/
COPY ui/ /app/ui/
COPY entrypoint.py /app/entrypoint.py

# Set ownership to non-root user
RUN chown -R a2a:a2a /app

USER a2a

# Expose default HTTP port
EXPOSE 8000

# Docker healthcheck pinging A2A discovery endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://127.0.0.1:${PORT}/.well-known/agent-card.json || exit 1

# Production entrypoint: automatically pre-warms agents and launches A2A cluster
CMD ["python", "entrypoint.py"]
