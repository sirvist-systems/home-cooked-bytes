# Change Surfaces (home-cooked-bytes)

Purpose: list every surface where changes can impact behavior, stability, or security.
If a surface changes, update this file.

## Config + Env
- `.codex/config.toml`
- `.env.example` / `.env`
- `.pre-commit-config.yaml`
- `pyproject.toml`
- `package.json` / `package-lock.json`

## MCP Servers
- `mcp_servers/` (all custom MCP servers)

## Infra
- `infra/docker/` (compose files)
- `infra/bifrost/` (allowlists, configs)

## Scripts
- `scripts/mcp/` (ops entrypoints)
- `scripts/dev/` (quality tooling)

## Docs
- `docs/mcp/` (runtime contracts)
- `docs/ops/` (enforcement + dependencies)
- `migration/` (temporary sprint checklists)
