.PHONY: install dev hooks run test cov lint fmt check clean \
        web-install web-dev web-build web-check web-generate seed

VENV   = .venv
PYTHON = $(VENV)/bin/python
UV     = source $(HOME)/.local/bin/env && uv

install:
	$(UV) venv --python 3.12
	$(UV) pip install -e "."

dev:
	$(UV) pip install -e ".[dev]"

hooks:
	git config core.hooksPath .githooks
	chmod +x .githooks/*
	@echo "✅  Hooks instalados (.githooks/: pre-commit, commit-msg, pre-push)"

run:
	$(VENV)/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

test:
	$(VENV)/bin/pytest

cov:
	$(VENV)/bin/pytest --cov=app --cov-report=term-missing --cov-report=html

lint:
	$(VENV)/bin/ruff check app tests

fmt:
	$(VENV)/bin/ruff format app tests

check: lint
	$(VENV)/bin/pytest --cov=app -q

clean:
	rm -rf .venv __pycache__ .pytest_cache htmlcov .coverage
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

# ── Web (frontend) ─────────────────────────────────────────────────────────────

web-install:
	cd web && pnpm install

web-dev:
	cd web && pnpm dev

web-build:
	cd web && pnpm build

web-check:
	cd web && pnpm check && pnpm typecheck

web-generate:
	cd web && pnpm generate:api

seed:
	$(VENV)/bin/python scripts/seed.py
