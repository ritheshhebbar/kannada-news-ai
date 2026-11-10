.PHONY: help up down build logs api worker web seed test lint clean

help:
	@echo "Available commands:"
	@echo "  make up        Start all services using Docker Compose"
	@echo "  make down      Stop all running containers"
	@echo "  make build     Build or rebuild docker images"
	@echo "  make logs      Follow container logs"
	@echo "  make api       Run FastAPI backend locally"
	@echo "  make worker    Run background AI worker locally"
	@echo "  make web       Run Next.js development server"
	@echo "  make seed      Seed database with fixed demo articles"
	@echo "  make test      Run unit and integration test suite"
	@echo "  make clean     Remove temporary files and caches"

up:
	docker compose up -d

down:
	docker compose down

build:
	docker compose build

logs:
	docker compose logs -f

api:
	cd apps/api && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

worker:
	cd services/worker && python worker.py

web:
	cd apps/web && npm run dev

seed:
	python scripts/seed.py

test:
	pytest apps/api/tests services/worker/tests -v

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +

