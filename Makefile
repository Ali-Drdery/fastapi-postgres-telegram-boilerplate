.PHONY: run docker-up docker-down migrate revision format lint test

run:
	uvicorn app.main:app --reload

docker-up:
	docker compose up --build

docker-down:
	docker compose down

migrate:
	alembic upgrade head

revision:
	alembic revision --autogenerate -m "$(m)"

format:
	ruff format .

lint:
	ruff check .

test:
	pytest -v
