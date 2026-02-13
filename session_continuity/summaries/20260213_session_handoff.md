Update (UTC): 2026-02-13 09:55:52Z

## Session start read-order (fast alignment)

1) `AGENTS.md` (repo rules + router)
2) `00_current/codex_active_tasks.md` (today’s execution queue)
3) `00_current/codex_backlog.md` (parking lot)
4) `docs/ops/ACTIVE_ENFORCEMENT.md` + `docs/ops/GIT_GRAPH_POLICY.md` (don’t violate)
5) Decisions + plans: `docs/decisions/README.md`, `docs/plans/README.md`

---

# Session Handoff — Home Cooked Bytes

Date (UTC): 2026-02-13

## TL;DR (read this first)
- **MCP env stability is solved**: endpoints auto-export via `direnv` (no venv activation) or `source scripts/mcp/env.sh`.
- **LangGraph is OSS + local**: `hcb_langgraph` runs via `langgraph dev` on port `2026`.
- **Bifrost is required and stable**: runs on `8084` (avoids collision with sirvist stack).
- **Weaviate is healthy** on `8092`; **Weaviate MCP is repo-local** (no external binary dependency).
- **Ollama (repo-isolated)** is on `11436` with standard models installed.
- Deterministic delegation exists: checked tasks → GitHub Issues (`scripts/todos/sync_checked_tasks_to_github_issues.py`).

## Restart checklist (60 seconds)
```bash
cd /home/sirvist-lab/src/home-cooked-bytes

# Reproducible MCP deps
uv venv --python 3.12 .venv
uv pip sync --python .venv/bin/python requirements-mcp.lock.txt

# Ensure env vars exist for Codex + MCP
# Option A (recommended): direnv allow (see docs/runbooks/ENV_AUTOEXPORT.md)
# Option B (manual):
source scripts/mcp/env.sh

# Bring up the local stack
bash scripts/mcp/up.sh

# Start Codex (in the same shell so it inherits env vars)
codex
```

## What’s green
- Docker services up (HCB): `redis`, `postgres`, `neo4j`, `weaviate`, `langflow`, `ollama`, `langgraph`, `bifrost`.
- Weaviate responds: `curl -fsS http://localhost:8092/v1/meta | head`
- LangGraph responds: `curl -fsS http://localhost:2026/docs | head`

## What’s still noisy
- `weaviate-docs` MCP OAuth login can fail in browser with `OAuth error: An unexpected error occurred`.
  - Workaround: temporarily disable `weaviate-docs` in `.codex/config.toml` until OAuth cooperates.

## Key endpoints (HCB)
- Redis: `redis://localhost:6381/0`
- Postgres: `postgresql://postgres:${POSTGRES_PASSWORD}@localhost:5433/postgres`
- Neo4j: `bolt://localhost:7688`
- Weaviate: `http://localhost:8092`
- Langflow MCP: `http://localhost:7861/api/v1/mcp/streamable`
- Langgraph MCP: `http://localhost:2026/mcp`
- Ollama: `http://127.0.0.1:11436`
- Bifrost: `http://127.0.0.1:8084`

## Decisions finalized (with links)
- **MCP deps**: `uv` + lockfile (`requirements-mcp.lock.txt`).
  - ADR: `docs/decisions/adr/ADR-0001-uv-locked-mcp-dependencies.md`
- **Repo-isolated Ollama** service + standard models.
  - ADR: `docs/decisions/adr/ADR-0002-repo-isolated-ollama-service.md`
- **Deterministic TODO delegation**: checked tasks → GitHub Issues, stamp lines with `(GH-ISSUE: <n>)`.
  - ADR: `docs/decisions/adr/ADR-0003-deterministic-todo-to-github-issues.md`
- Decision log: `docs/decisions/decision-log.md`

## Session-start alignment sources of truth
- Repo behavior: `AGENTS.md`
- Enforcement/policies:
  - `docs/ops/ACTIVE_ENFORCEMENT.md`
  - `docs/ops/CHANGE_SURFACES.md`
  - `docs/ops/DEPENDENCIES.md`
  - `docs/ops/GIT_GRAPH_POLICY.md`

## Next “finish this session” items
- Create `docs/plans/` structure (hybrid: living plan + append-only decisions inside each plan folder).
- Add Docker cleanup/prizz deep-dive TODO (images/volumes hygiene + diagnostics).
- Decide how to handle `weaviate-docs` OAuth (keep trying vs disable by default).
