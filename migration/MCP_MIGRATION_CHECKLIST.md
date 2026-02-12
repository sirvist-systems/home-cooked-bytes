# MCP Migration Checklist (Sprint)

> Canonical docs live in `docs/mcp/`.

## Setup
- [ ] Confirm repo root: `pwd` == `/home/sirvist-lab/src/home-cooked-bytes`
- [ ] `.env` present locally and ignored (`git status --ignored -sb` shows `!! .env`)
- [ ] Docker running

## Code + Config
- [ ] `mcp_servers/` contains: `sirvist_mcp_server.py`, `openapi_local_mcp_server.py`, `brave_search_mcp_server.py`
- [ ] `.codex/config.toml` points to repo-local MCP servers only
- [ ] `.env.example` contains all required keys

## Infra
- [ ] `infra/docker/docker-compose.mcp.yml` present
- [ ] `scripts/mcp/up.sh` brings up stack without errors
- [ ] `scripts/mcp/status.sh` shows healthy services

## MCP Verification
- [ ] `codex /mcp` shows full target set
- [ ] `codex mcp list` shows no handshake failures
- [ ] Smoke tests pass per server

## Cutover
- [ ] Confirm `home-cooked-bytes` stack is isolated from `sirvist-lab`
- [ ] Declare new repo primary for MCP work
