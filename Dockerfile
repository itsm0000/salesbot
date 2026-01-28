# =============================================================================
# Muntazir Sales Bot - Production Dockerfile
# Multi-stage build for smaller, secure image
# =============================================================================

# Stage 1: Builder - Install dependencies
FROM python:3.11-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir alembic aiosqlite


# Stage 2: Runtime - Lean production image
FROM python:3.11-slim as runtime

# Labels
LABEL maintainer="Muntazir Team"
LABEL version="1.0.0"
LABEL description="Iraqi Arabic Sales AI Agent"

# Environment
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV APP_HOME=/app
ENV PATH="/opt/venv/bin:$PATH"

# Create non-root user for security
RUN groupadd --gid 1000 muntazir && \
    useradd --uid 1000 --gid muntazir --shell /bin/bash --create-home muntazir

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Set work directory
WORKDIR $APP_HOME

# Copy application code
COPY --chown=muntazir:muntazir . .

# Create directories for data persistence
RUN mkdir -p data backups logs && \
    chown -R muntazir:muntazir data backups logs

# Switch to non-root user
USER muntazir

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Run the application
CMD ["python", "main.py"]
