.PHONY: db-up db-down migrate test lint

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
