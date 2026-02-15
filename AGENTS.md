# Home Cooked Bytes — Agent Instructions

Update (UTC): 2026-02-14 06:05:00Z

These instructions apply to this repository and all subdirectories.

## Operating assumptions

- Canonical environment is **WSL Ubuntu**.
- Prefer **repo-relative paths** and WSL-native tooling.
- Avoid Windows-path assumptions (`C:\...`, `%USERPROFILE%`, backslashes).

## Accuracy

- Before implementation beyond quick scripts:
  - Prefer authoritative sources first: OpenAI Developer Docs MCP (Codex/OpenAI behavior), Context7 (vendor/library docs), and primary upstream docs.
  - If sources conflict, call it out explicitly and choose the safest/default behavior.
- Always look in the codebase for what already exists before coding to avoid duplication.

## SSOT pointers (do not duplicate)

- Daily start (personal): `DRIVE_TO_WORK.txt`
- “What is canonical?” index: `docs/ops/SSOT_INDEX.md`
- MCP operations: `docs/mcp/MCP_OPERATIONS_RUNBOOK.md`
- Enforcement + constraints: `docs/ops/ACTIVE_ENFORCEMENT.md`, `docs/ops/CHANGE_SURFACES.md`, `docs/ops/GIT_GRAPH_POLICY.md`

## Safety

- If a command is destructive (deletes/resets/migrations), ask first.

## Default workflow (always)

When asked to do work in this repo:

1) Check the current plan and backlog:
   - `00_current/codex_active_tasks.md`
   - `00_current/codex_backlog.md`
2) Follow enforcement and operating constraints:
   - `docs/ops/ACTIVE_ENFORCEMENT.md`
   - `docs/ops/CHANGE_SURFACES.md`
   - `docs/ops/DEPENDENCIES.md`
   - `docs/ops/GIT_GRAPH_POLICY.md`
3) Prefer existing scripts/runbooks over inventing new flows.

### Task delegation (deterministic)

When delegating work to GitHub, prefer GitHub Issues as the canonical queue. To create issues
deterministically from checked tasks:

- Script: `scripts/todos/sync_checked_tasks_to_github_issues.py`
- Flow:
  1) Mark a task as checked (`- [x] ...`) in `00_current/codex_active_tasks.md`
  2) Run the script to create Issues and stamp each task line with `(GH-ISSUE: <n>)`

## Repo orientation (router)

Goal: keep this file short. It should *route* you to the right context fast, not duplicate docs.

Read order at session start (fast alignment):

1) Session handoff (60 seconds):
   - `session_continuity/summaries/20260213_session_handoff.md` (or latest `session_continuity/summaries/YYYYMMDD_session_handoff.md`)
2) What to do next:
   - `00_current/codex_active_tasks.md`
   - `00_current/codex_backlog.md`
3) Enforcement (do not violate):
   - `docs/ops/ACTIVE_ENFORCEMENT.md`
   - `docs/ops/CHANGE_SURFACES.md`
   - `docs/ops/GIT_GRAPH_POLICY.md`
4) Durable decisions + plans:
   - `docs/decisions/README.md` (where decisions live)
   - `docs/plans/README.md` (where plans live)

Overlap week posture (sirvist-lab is a read-only quarry):

- Keep sessions split by repo by default (safer).
- Only use sirvist-lab to extract/reference; land new canonical work in home-cooked-bytes.

Where to find “alignment docs” (not an exhaustive repo map):

- Architecture boundaries: `docs/architecture/ARCHITECTURE_BOUNDARIES.md`
- Workstreams: `docs/architecture/WORKSTREAMS.md`
- MCP ops: `docs/mcp/MCP_OPERATIONS_RUNBOOK.md`


## MCP expectations

- MCP servers for this repo are configured in `.codex/config.toml`.
- Many MCP servers require external services (Docker Compose stack) and/or environment variables.
- When MCP startup errors occur, diagnose in this order:
  1) Missing binaries on PATH
  2) Missing/empty required env vars
  3) Service not running / wrong URL
  4) Python dependencies missing for local MCP servers

### MCP bootstrap (strict mode)

To run with all MCP servers enabled, ensure the Docker MCP stack is up and required env vars are set.

- Start/stop/status: `scripts/mcp/up.sh`, `scripts/mcp/down.sh`, `scripts/mcp/status.sh`
- Healthcheck: `scripts/mcp/healthcheck.sh`

Recommended local workflow (portable config + local defaults):

- `source scripts/mcp/env.sh`
- `bash scripts/mcp/up.sh`
- Run Codex (`codex`) in this shell so it inherits the env vars

Local default endpoints implied by `infra/docker/docker-compose.mcp.yml`:

- `REDIS_URL=redis://localhost:6381/0`
- `POSTGRES_URL=postgresql://postgres:${POSTGRES_PASSWORD}@localhost:5433/postgres`
- `NEO4J_URI=bolt://localhost:7688` (plus `NEO4J_USERNAME=neo4j`, `NEO4J_PASSWORD=...`)
- `WEAVIATE_URL=http://localhost:8092`
- `LANGFLOW_URL=http://localhost:7861/api/v1/mcp/streamable`
- `LANGGRAPH_URL=http://localhost:2026/mcp`

For local Python MCP servers, install MCP deps into the repo venv:

- Reproducible install: `uv pip sync --python .venv/bin/python requirements-mcp.lock.txt`
- Updating deps: edit `requirements-mcp.txt`, then regenerate `requirements-mcp.lock.txt` (see `README_MCP_DEPS.md`)

## Local model offload (Ollama)

This repo is configured with `oss_provider = "ollama"` in `.codex/config.toml`.

### Local hardware context (developer workstation)

- Ryzen 9 9950 X 3D
- 64 GB RAM (WSL memory may be capped by `.wslconfig`)
- NVIDIA GeForce RTX 5080

### Ollama endpoint + model inventory

- Endpoint (recommended for this repo stack): `OLLAMA_HOST` from `scripts/mcp/env.sh`
- Models currently present on the machine:
  - Coding: `qwen2.5-coder:32b`, `deepseek-coder-v2:16b`
  - General/reasoning-ish: `qwen2.5:14b`, `qwen2.5:7b`, `llama2-uncensored:latest`
  - Embeddings: `bge-m3:latest`, `nomic-embed-text:latest`

Use local models for tasks that are:

- Low-risk / non-sensitive (no secrets)
- Heavier on token volume than on correctness (summaries, indexing, brainstorming)
- Not requiring web search or strict citation requirements

Prefer OpenAI-hosted models when tasks need maximum reasoning reliability, tool-heavy workflows,
or when output is user-facing and must be precise.

## Coding conventions

- Prefer small, reviewable patches.
- Don’t move/delete files without explicitly listing the file paths and getting confirmation.
- Prefer existing scripts/docs over inventing new workflows.

## Timestamping (UTC, required)

When creating or updating repo artifacts (docs, runbooks, reports, scripts, etc.), include an
explicit UTC timestamp so session continuity is deterministic.

- Prefer filenames with UTC stamps (e.g. `YYYYMMDD_HHMMSSZ_*`).
- If a stable daily filename is used (e.g. `YYYYMMDD_*`), prepend new updates at the top with
  `Update (UTC): YYYY-MM-DD HH:MM:SSZ`.
