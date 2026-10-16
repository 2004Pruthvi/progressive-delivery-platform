# =============================================================================
# Stage 1: Build Dependencies
# =============================================================================
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build dependencies if needed
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY app/requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# =============================================================================
# Stage 2: Runtime Image
# =============================================================================
FROM python:3.11-slim AS runtime

# Security: Set Python flags for container environments
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/home/appuser/.local/bin:$PATH"

# Create a non-root user and group with an explicit UID/GID
RUN groupadd --gid 10001 appgroup && \
    useradd --uid 10001 --gid appgroup --shell /sbin/nologin --no-create-home appuser

WORKDIR /app

# Copy installed Python packages from builder stage
COPY --from=builder /root/.local /home/appuser/.local

# Copy application source code
COPY --chown=appuser:appgroup app /app/app

# Build arguments for immutable image identification
ARG APP_VERSION=v1.0.0
ARG COMMIT_SHA=unknown
ARG APP_ENV=production

ENV APP_VERSION=${APP_VERSION} \
    COMMIT_SHA=${COMMIT_SHA} \
    APP_ENV=${APP_ENV}

# Set security ownership
RUN chown -R appuser:appgroup /app /home/appuser

# Switch to non-privileged user
USER 10001:10001

EXPOSE 8000

# Native Python healthcheck (does not require external curl or wget packages)
HEALTHCHECK --interval=15s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health').read()" || exit 1

STOPSIGNAL SIGTERM

ENTRYPOINT ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
