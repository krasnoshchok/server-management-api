FROM python:3.11-slim AS builder

WORKDIR /build

# Build dependencies only in builder stage.
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --upgrade pip && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

FROM python:3.11-slim AS runtime

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Create a non-root user for safer runtime defaults.
RUN useradd --create-home --shell /usr/sbin/nologin appuser && \
    mkdir -p /logs && \
    chown -R appuser:appuser /app /logs

COPY --from=builder /opt/venv /opt/venv
COPY --chown=appuser:appuser ./app ./app
COPY --chown=appuser:appuser ./sql ./sql

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s \
    CMD python -c "import sys,urllib.request; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/health', timeout=3).status == 200 else 1)"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
