SHELL := /bin/bash

.PHONY: install dev hooks \
        run run-producao run-oficinas \
        test cov lint fmt check \
        migrate-producao migrate-oficinas \
        web-install web-dev web-dev-oficinas web-build web-check web-generate \
        seed seed-oficinas \
        docker-up docker-down docker-logs docker-build \
        docker-up-producao docker-down-producao docker-logs-producao \
        docker-up-oficinas docker-down-oficinas docker-logs-oficinas \
        clean

UV = source $(HOME)/.local/bin/env && uv

# ── Workspace ──────────────────────────────────────────────────────────────────

install:
	$(UV) sync

dev:
	$(UV) sync --all-extras

hooks:
	git config core.hooksPath .githooks
	chmod +x .githooks/*
	@echo "Hooks instalados (.githooks/)"

# ── Apps ───────────────────────────────────────────────────────────────────────

run: run-producao

run-producao:
	$(UV) run --package producao fastapi dev apps/producao/src/producao/main.py --port 8000

run-oficinas:
	$(UV) run --package oficinas fastapi dev apps/oficinas/src/oficinas/main.py --port 8001

# ── Testes e qualidade ─────────────────────────────────────────────────────────

test:
	cd apps/producao && $(UV) run --package producao pytest tests -v --tb=short

cov:
	cd apps/producao && $(UV) run --package producao pytest tests \
		--cov=producao --cov-report=term-missing --cov-report=html

lint:
	$(UV) run --package producao ruff check \
		apps/producao/src apps/producao/tests \
		packages/core/src packages/auth/src packages/utils/src

fmt:
	$(UV) run --package producao ruff format \
		apps/producao/src apps/producao/tests \
		packages/core/src packages/auth/src packages/utils/src

check: lint
	cd apps/producao && $(UV) run --package producao pytest tests -q

# ── Migrations (por app) ───────────────────────────────────────────────────────
# Quando o producao migrar para banco real, Alembic ficará em apps/producao/.
# Cada app tem suas próprias migrations — nunca compartilhadas pelo core.

migrate-producao:
	@if [ -z "$(DATABASE_URL)" ]; then \
	  echo "DATABASE_URL não definida."; exit 1; \
	fi
	psql "$(DATABASE_URL)" -f apps/producao/src/producao/db/migrations/001_message_queue.sql

migrate-oficinas:
	@if [ -z "$(OFICINAS_DATABASE_URL)" ]; then \
	  echo "OFICINAS_DATABASE_URL não definida."; exit 1; \
	fi
	psql "$(OFICINAS_DATABASE_URL)" -f apps/oficinas/migrations/001_global_schema.sql
	psql "$(OFICINAS_DATABASE_URL)" -f apps/oficinas/migrations/002_tenant_schema.sql
	psql "$(OFICINAS_DATABASE_URL)" -f apps/oficinas/migrations/003_rls_policies.sql
	psql "$(OFICINAS_DATABASE_URL)" -f apps/oficinas/migrations/004_seed.sql
	psql "$(OFICINAS_DATABASE_URL)" -f apps/oficinas/migrations/005_iam_adjustments.sql
	psql "$(OFICINAS_DATABASE_URL)" -f apps/oficinas/migrations/006_nfe_rascunho.sql

# ── Web (frontend) ─────────────────────────────────────────────────────────────

web-install:
	cd web && pnpm install

web-dev:
	cd web && pnpm dev

web-dev-oficinas:
	cd web && pnpm --filter oficinas dev

web-build:
	cd web && pnpm build

web-check:
	cd web && pnpm check && pnpm typecheck

web-generate:
	cd web && pnpm generate:api

# ── Seed e limpeza ─────────────────────────────────────────────────────────────

seed:
	$(UV) run --package producao python scripts/seed.py

seed-oficinas:
	$(UV) run --package oficinas python scripts/seed_oficinas.py

# ── Docker ─────────────────────────────────────────────────────────────────────

docker-up:
	docker compose up -d

docker-down:
	docker compose down

docker-logs:
	docker compose logs -f

docker-build:
	docker compose build --no-cache

docker-up-producao:
	docker compose up -d producao

docker-down-producao:
	docker compose stop producao

docker-logs-producao:
	docker compose logs -f producao

docker-up-oficinas:
	docker compose up -d oficinas

docker-down-oficinas:
	docker compose stop oficinas

docker-logs-oficinas:
	docker compose logs -f oficinas

clean:
	rm -rf .venv __pycache__ .pytest_cache htmlcov .coverage
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
