.PHONY: db-up db-down migrate test lint up down logs

db-up:
	docker compose -f deploy/docker-compose.yml up -d db

db-down:
	docker compose -f deploy/docker-compose.yml down

migrate:
	alembic upgrade head

test:
	python -m pytest -q

lint:
	ruff check .

# Full stack: db, api, dashboard, prometheus, grafana, caddy.
up:
	docker compose -f deploy/docker-compose.yml up -d --build

down:
	docker compose -f deploy/docker-compose.yml down

logs:
	docker compose -f deploy/docker-compose.yml logs -f
