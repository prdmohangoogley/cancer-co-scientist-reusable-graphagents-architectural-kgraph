# Multi-stage production build for Cancer Co-Scientist Unified Orchestrator & Web App
# Adheres to DOC-01 (Quality & Observability), DOC-02 (ZAA: Non-root execution), DOC-03 (A2UI)

FROM python:3.11-slim AS builder

WORKDIR /app

# Install system build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install UV for fast deterministic dependency resolution
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy package manifests
COPY pyproject.toml ./
COPY packages/graphagent/pyproject.toml packages/graphagent/
COPY apps/co-scientist/pyproject.toml apps/co-scientist/

# Copy source trees
COPY packages/graphagent/ packages/graphagent/
COPY apps/co-scientist/ apps/co-scientist/

# Install dependencies into virtual environment
RUN uv venv /opt/venv && \
    . /opt/venv/bin/activate && \
    uv pip install pyjwt nest-asyncio && \
    uv pip install -e packages/graphagent -e apps/co-scientist

# Final stage: minimal production runtime
FROM python:3.11-slim AS runtime

WORKDIR /app

# Install runtime dependencies for health checks
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy virtualenv and code from builder
COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /app /app

# Enforce Zero Ambient Authority (DOC-02): Run as unprivileged non-root user
USER 10001:10001

# Environment configuration
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH="/app/apps/co-scientist:/app/packages/graphagent"
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Cloud Run Container Health Check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

EXPOSE 8080

# Entrypoint: Launch Unified Lead Orchestrator serving both A2UI Web App and GEA API
CMD ["python3", "-m", "uvicorn", "agent.orchestrator:app", "--host", "0.0.0.0", "--port", "8080"]
