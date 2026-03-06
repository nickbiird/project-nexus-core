# ──────────────────────────────────────────────────────────────
# Yellowbird Telemetry — Production Dockerfile
# Multi-stage build: builder → runtime
# ──────────────────────────────────────────────────────────────

# ── Stage 1: Builder ──────────────────────────────────────────
FROM python:3.11-slim-bookworm AS builder

WORKDIR /app

# Install uv for fast dependency resolution
RUN pip install --no-cache-dir uv

# Copy dependency files first (layer caching)
COPY pyproject.toml uv.lock ./

# Install production dependencies into .venv
RUN uv venv /app/.venv && \
    uv sync --frozen --no-dev --no-cache

# ── Stage 2: Runtime ─────────────────────────────────────────
FROM python:3.11-slim-bookworm AS runtime

# Runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl && \
    rm -rf /var/lib/apt/lists/*

# Non-root user
RUN addgroup --system --gid 1000 yellowbird && \
    adduser --system --uid 1000 --gid 1000 --no-create-home yellowbird

WORKDIR /app

# Copy virtualenv from builder
COPY --from=builder --chown=yellowbird:yellowbird /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Copy application code (ordered by change frequency)
COPY --chown=yellowbird:yellowbird alembic.ini ./
COPY --chown=yellowbird:yellowbird src/db/migrations/ ./src/db/migrations/
COPY --chown=yellowbird:yellowbird src/ ./src/
COPY --chown=yellowbird:yellowbird app/ ./app/
COPY --chown=yellowbird:yellowbird api/ ./api/

# Environment variables (non-secret only)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8501/_stcore/health || exit 1

USER yellowbird

CMD ["python", "-m", "streamlit", "run", "app/main.py", "--server.port=8501", "--server.address=0.0.0.0"]
