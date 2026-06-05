# Changelog

All notable changes to **gsc-gpc-mcp** will be documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [Unreleased]

---

## [0.1.3] - 2026-06-05

### Added
- `scripts/setup.py` — интерактивный CLI визард: проверка Python, зависимостей, ключей, создание `.env`, запуск тестов (`make setup`)
- `scripts/setup_web.py` — веб-визард на `http://localhost:7777`: загрузка JSON ключей через браузер, статус всех шагов (`make setup-web`)
- `scripts/templates/setup.html` — Jinja2 шаблон для веб-визарда (HTML отделён от логики)
- `jinja2>=3.1` добавлен в dev зависимости
- `make setup` и `make setup-web` targets в Makefile

### Refactored
- `GSC_API_VERSION` и `GPC_API_VERSION` вынесены как именованные константы в `shared/auth.py` — версии API меняются в одном месте
- `E501` исключён для `scripts/*.py` в ruff конфиге (HTML в строках неизбежен в setup.py до переноса в шаблон)

---

## [0.1.2] - 2026-06-05

### Added
- `GOOGLE_KEY_FILE` env var — one shared service account key for both servers
- `.pre-commit-config.yaml` — ruff lint + format runs automatically on every `git commit`

### Changed
- Key resolution priority: `GOOGLE_KEY_FILE` → `GSC_KEY_FILE`/`GPC_KEY_FILE` → default filenames

---

## [0.1.1] - 2026-06-05

### Changed
- HTTP transport support: servers now run `streamable-http` when `PORT` env var is set, stdio otherwise
- Added `Dockerfile` and `docker-compose.yml` for containerised deployment behind authmcp-gateway
- Updated README with correct gateway integration instructions (backends registered via REST API, not config file)

### Fixed
- Ruff lint errors: import ordering (I001), unused imports (F401), line length (E501)

---

## [0.1.0] - 2026-06-05

### Added
- `shared/auth.py` — общий auth helper: `load_credentials()`, `build_gsc_service()`, `build_gpc_service()`
- **GSC server** (`gsc/`) — 5 tools:
  - `gsc_get_performance` — performance data (queries, clicks, impressions, CTR, position)
  - `gsc_inspect_url` — indexing status of a specific URL
  - `gsc_list_sitemaps` — list submitted sitemaps
  - `gsc_submit_sitemap` — submit a new sitemap
  - `gsc_list_sites` — list all accessible properties
- **GPC server** (`gpc/`) — 6 tools:
  - `gpc_list_reviews` — list app reviews with optional translation
  - `gpc_get_review` — get a specific review by ID
  - `gpc_reply_to_review` — post a developer reply to a review
  - `gpc_get_release_tracks` — production/beta/alpha/internal tracks with versions
  - `gpc_get_bundles` — list uploaded AAB bundles
  - `gpc_get_install_stats` — install/uninstall statistics
- `pyproject.toml` — deps: fastmcp, google-api-python-client, google-auth; dev: pytest, ruff, mypy
- `Makefile` — targets: install, install-dev, lint, format, type-check, test, test-cov, run-gsc, run-gpc, clean
- `.github/workflows/ci.yml` — lint + tests on Python 3.11 and 3.12
- 16 unit tests, 100% pass, все без реального API (mock)

### Architecture
- Два независимых FastMCP сервера, один shared auth layer
- Service Account JSON auth (разные scopes для GSC и GPC)
- Designed for AuthMCP Gateway: `python -m gsc.server` / `python -m gpc.server`
