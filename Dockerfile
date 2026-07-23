FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app

COPY pyproject.toml README.md ./
COPY agentwatch ./agentwatch
COPY dashboard ./dashboard
COPY migrations ./migrations
COPY alembic.ini ./
COPY scripts ./scripts

RUN pip install --upgrade pip && pip install ".[dashboard]" && chmod +x scripts/*.sh

# Default command is the API entrypoint (migrate + serve). Compose / Render override
# with a single-token script path per service so no shell quoting is involved.
CMD ["/app/scripts/render-api.sh"]
