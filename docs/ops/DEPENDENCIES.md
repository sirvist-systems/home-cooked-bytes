# Dependencies (home-cooked-bytes)

Update (UTC): 2026-02-13 15:50:47Z

## Python (MCP runtime)
- `requirements-mcp.txt`
- Locked in `requirements-mcp.lock.txt`
- Installed reproducibly with `uv pip sync` (see `README_MCP_DEPS.md`)

## Shell utilities (required)
- `direnv` (auto‑export env vars when you enter repo)
- `jq` (JSON processing)
- `jd` (JSON diff)

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
