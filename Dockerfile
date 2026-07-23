FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app

COPY pyproject.toml README.md ./
COPY agentwatch ./agentwatch
COPY dashboard ./dashboard
COPY migrations ./migrations
COPY alembic.ini ./

RUN pip install --upgrade pip && pip install ".[dashboard]"

# Default command is the API; compose overrides the command per service.
CMD ["agentwatch", "serve", "--host", "0.0.0.0", "--port", "8000"]
