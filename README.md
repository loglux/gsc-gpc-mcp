# gsc-gpc-mcp

MCP servers for **Google Search Console** and **Google Play Console**, designed to run behind [AuthMCP Gateway](https://github.com/authmcp/gateway).

```
Claude ↔ MCP Gateway (AuthMCP) ↔ gsc-gpc-mcp ↔ Google APIs
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

- `gsc-reader@YOUR_PROJECT.iam.gserviceaccount.com` — scopes: `webmasters.readonly`
- `gpc-reader@YOUR_PROJECT.iam.gserviceaccount.com` — scopes: `androidpublisher`

Download JSON keys and place them in the `credentials/` directory:

```
credentials/
├── gsc-service-account.json
└── gpc-service-account.json
```

### 2. Grant Access

**Search Console:** Settings → Users and permissions → Add user → paste service account email → Owner or Full

**Play Console:** Setup → API access → Link to Google Cloud project → Grant access to service account

### 3. Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 4. Run

```bash
# GSC server
python -m gsc.server

# GPC server
python -m gpc.server
```

### Custom key file paths

Override the default filenames via environment variables:

```bash
GSC_KEY_FILE=my-gsc-key.json python -m gsc.server
GPC_KEY_FILE=my-gpc-key.json python -m gpc.server
```

## AuthMCP Gateway config

```yaml
backends:
  - name: gsc
    command: python -m gsc.server
    cwd: /path/to/gsc-gpc-mcp

  - name: gpc
    command: python -m gpc.server
    cwd: /path/to/gsc-gpc-mcp
```

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
make test

# Lint + format
make lint
make format

# Type check
make type-check
```

## Project structure

```
gsc-gpc-mcp/
├── shared/
│   └── auth.py          # Shared Google auth helper
├── gsc/
│   ├── server.py        # FastMCP server — Search Console
│   └── tools.py         # Business logic
├── gpc/
│   ├── server.py        # FastMCP server — Play Console
│   └── tools.py         # Business logic
├── tests/               # Unit tests (mocked, no real API calls)
└── credentials/         # gitignored — place JSON keys here
```

## License

MIT
