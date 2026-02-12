# MCP Operations Runbook (home-cooked-bytes)

## Start Services
- `scripts/mcp/up.sh`

## Stop Services
- `scripts/mcp/down.sh`

## Status
- `scripts/mcp/status.sh`

## Healthcheck
- `scripts/mcp/healthcheck.sh`

## Codex MCP Validation
- `codex mcp list | sed -n '1,200p'`
- `codex /mcp`

## Troubleshooting
- Missing env var → fill `.env` and re-run.
- Service down → check `docker compose ps` and logs.
- MCP handshake error → confirm command path and python venv.
