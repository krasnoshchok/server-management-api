# lightweight python image
FROM python:3.11-slim

# set working directory
WORKDIR /app

# copy requirements first so we can take advantage of layer caching
COPY requirements.txt ./

# install system dependencies for asyncpg (libpq header)
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev && \
    pip install --no-cache-dir -r requirements.txt && \
    apt-get purge -y --auto-remove gcc && \
    rm -rf /var/lib/apt/lists/*

# copy application code
COPY ./app ./app
COPY sql ./sql
# make sure logs directory exists (compose mounts to it later)
RUN mkdir -p /logs

# copy any additional files such as constants, README, etc.
# (configuration is handled via environment variables; .env is ignored)

# expose port used by uvicorn
EXPOSE 8000

# basic healthcheck ensures the FastAPI app is up
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s \
    CMD python -c "import sys,urllib.request; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/health', timeout=3).status == 200 else 1)"

# default command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
