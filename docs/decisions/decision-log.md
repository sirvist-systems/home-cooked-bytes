# Decision Log

Append-only running log of project decisions that are useful for session-to-session continuity,
but don’t necessarily justify a full ADR.

## 2026-02-12

- Adopt `uv` for reproducible Python dependency installs for MCP servers.
  - Source deps: `requirements-mcp.txt`
  - Lockfile: `requirements-mcp.lock.txt`
  - Install: `uv venv --python 3.12 .venv` then `uv pip sync --python .venv/bin/python requirements-mcp.lock.txt`
- Keep `.codex/config.toml` MCP endpoints env-based for portability; provide local defaults via `scripts/mcp/env.sh`.
- Add an `ollama` service to `infra/docker/docker-compose.mcp.yml` for repo-isolated local-model offload.
- Add deterministic TODO delegation: checked tasks in `00_current/codex_active_tasks.md` can be synced to GitHub Issues via `scripts/todos/sync_checked_tasks_to_github_issues.py` (see `docs/runbooks/TODO_DELEGATION.md`).
