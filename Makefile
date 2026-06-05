.PHONY: install install-dev lint format type-check test test-cov run-gsc run-gpc clean

PYTHON := python
PIP := pip
VENV := .venv
VENV_PYTHON := $(VENV)/bin/python
VENV_PIP := $(VENV)/bin/pip

# ── Setup ──────────────────────────────────────────────────────────────────────

install:
	$(PIP) install -e .

install-dev:
	$(PIP) install -e ".[dev]"

venv:
	$(PYTHON) -m venv $(VENV)
	$(VENV_PIP) install -e ".[dev]"
	@echo "Activate with: source $(VENV)/bin/activate"

# ── Code quality ───────────────────────────────────────────────────────────────

lint:
	ruff check .

format:
	ruff format .
	ruff check --fix .

type-check:
	mypy shared/ gsc/ gpc/

check: lint type-check

# ── Tests ──────────────────────────────────────────────────────────────────────

test:
	pytest

test-cov:
	pytest --cov=. --cov-report=term-missing --cov-report=html
	@echo "HTML report: htmlcov/index.html"

# ── Run servers ────────────────────────────────────────────────────────────────

run-gsc:
	$(PYTHON) -m gsc.server

run-gpc:
	$(PYTHON) -m gpc.server

# ── Cleanup ────────────────────────────────────────────────────────────────────

clean:
	rm -rf __pycache__ **/__pycache__ *.pyc .pytest_cache htmlcov .coverage dist *.egg-info
