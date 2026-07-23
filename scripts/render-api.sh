#!/bin/sh
# API entrypoint: apply migrations, then serve. Runs migrations idempotently on boot.
set -e
alembic upgrade head
exec agentwatch serve --host 0.0.0.0 --port "${PORT:-8000}"
