# gsc-gpc-mcp

MCP servers for **Google Search Console** and **Google Play Console**, designed to run behind [authmcp-gateway](https://github.com/loglux/authmcp-gateway).

```
Claude ↔ authmcp-gateway ↔ gsc-gpc-mcp ↔ Google APIs
```

## Servers

### Google Search Console (`gsc`)

| Tool | Description |
|------|-------------|
| `gsc_get_performance` | Performance data: queries, clicks, impressions, CTR, position |
| `gsc_inspect_url` | Indexing status of a specific URL |
| `gsc_list_sitemaps` | List submitted sitemaps for a property |
| `gsc_submit_sitemap` | Submit a new sitemap |
| `gsc_list_sites` | List all accessible Search Console properties |

### Google Play Console (`gpc`)

| Tool | Description |
|------|-------------|
| `gpc_list_reviews` | List app reviews with optional translation |
| `gpc_get_review` | Get a specific review by ID |
| `gpc_reply_to_review` | Post a developer reply to a review |
| `gpc_get_release_tracks` | Production/beta/alpha/internal tracks with versions |
| `gpc_get_bundles` | List uploaded AAB bundles |
| `gpc_get_install_stats` | Install/uninstall statistics |

## Setup

### 1. Service Accounts

Create two service accounts in [Google Cloud Console](https://console.cloud.google.com/iam-admin/serviceaccounts):

- `gsc-reader@YOUR_PROJECT.iam.gserviceaccount.com` — scope: `webmasters.readonly`
- `gpc-reader@YOUR_PROJECT.iam.gserviceaccount.com` — scope: `androidpublisher`

Download JSON keys and place them in `credentials/`:

```
credentials/
├── gsc-service-account.json
└── gpc-service-account.json
```

> **Note:** If you prefer a single service account for both, set `GOOGLE_KEY_FILE=your-sa.json` — it takes priority over `GSC_KEY_FILE`/`GPC_KEY_FILE`.

### 2. Grant Access

**Search Console:** Settings → Users and permissions → Add user → paste service account email → Owner or Full

**Play Console:** Setup → API access → Link Google Cloud project → grant access to service account

### 3. Run with Docker Compose

```bash
docker compose up -d
```

This starts two HTTP MCP servers:
- `gsc` — reachable at `http://gsc:8000/mcp` (internal Docker network)
- `gpc` — reachable at `http://gpc:8000/mcp` (internal Docker network)

If you expose ports to the host for testing:

```yaml
# add to docker-compose.yml temporarily:
ports:
  - "8001:8000"   # gsc
  - "8002:8000"   # gpc
```

### 4. Register backends in authmcp-gateway

The gateway does not read a config file — backends are registered at runtime via the admin API or UI.

**Via admin UI:** open `http://localhost:9105/admin` → MCP Servers → Add Server.

**Via API:**

```bash
# 1. Get a token
TOKEN=$(curl -s -X POST http://localhost:9105/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"yourpassword"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# 2. Register GSC
curl -X POST http://localhost:9105/admin/api/mcp-servers \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "gsc",
    "url": "http://gsc:8000/mcp",
    "description": "Google Search Console",
    "tool_prefix": "gsc_",
    "routing_strategy": "prefix",
    "enabled": true
  }'

# 3. Register GPC
curl -X POST http://localhost:9105/admin/api/mcp-servers \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "gpc",
    "url": "http://gpc:8000/mcp",
    "description": "Google Play Console",
    "tool_prefix": "gpc_",
    "routing_strategy": "prefix",
    "enabled": true
  }'
```

## Local development (without Docker)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# stdio mode (for direct testing with MCP Inspector)
python -m gsc.server
python -m gpc.server

# HTTP mode
PORT=8001 python -m gsc.server
PORT=8002 python -m gpc.server
```

Custom key file paths:

```bash
GSC_KEY_FILE=my-gsc-key.json PORT=8001 python -m gsc.server
```

## Development

```bash
make test        # run tests
make lint        # ruff check
make format      # ruff format + fix
make type-check  # mypy
```

## Project structure

```
gsc-gpc-mcp/
├── shared/
│   └── auth.py          # Google auth helper (service account)
├── gsc/
│   ├── server.py        # FastMCP server — Search Console
│   └── tools.py         # Business logic
├── gpc/
│   ├── server.py        # FastMCP server — Play Console
│   └── tools.py         # Business logic
├── tests/               # Unit tests (mocked, no real API calls)
├── credentials/         # gitignored — place JSON keys here
├── Dockerfile
└── docker-compose.yml
```

## License

MIT
