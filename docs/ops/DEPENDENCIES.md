# Dependencies (home-cooked-bytes)

## Python (MCP runtime)
- `requirements-mcp.txt`
- Managed by `pip` inside `.venv`

## Python (Quality tools)
- `pyproject.toml` (ruff + mypy)
- `scripts/dev/*` wrappers

## Node (JS/TS tooling)
- `package.json`
- `.prettierrc`
- `node_modules/` (local only, gitignored)

## Docker
- `infra/docker/docker-compose.mcp.yml`
- `infra/docker/docker-compose.local.yml` (optional overrides)

## Secrets
- `.env` (local only, gitignored)
- `.credentials/` (local only, gitignored)
