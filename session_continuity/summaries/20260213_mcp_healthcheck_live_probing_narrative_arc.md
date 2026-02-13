Update (UTC): 2026-02-13 21:05:00Z

# Narrative Arc — MCP config parsing → live healthcheck probing → deep probes green

## Why this doc exists
This repo is mid-migration from a legacy repo (“sirvist-lab”) to `home-cooked-bytes`. During migration,
Codex + MCP startup behavior was inconsistent: MCP servers would show green when checked in-session,
but Codex startup reported “MCP startup incomplete”. We needed a deterministic, repo-local way to
verify the stack’s *actual usability* (not just that env vars exist).

This document captures the technical and narrative arc of the session that:
- fixed TOML/schema friction for Codex config,
- validated real MCP endpoints,
- replaced a “visibility-only” healthcheck with live probes,
- and wired in deep checks (redis/postgres/neo4j) so failures become explainable.

## Starting state (symptoms)
- User observed behavior suggesting only user-level Codex config was loading.
- Even Better TOML schema validation showed errors (e.g. “Additional properties are not allowed”).
- Codex startup printed warnings similar to:
  - Under-development features warning about `powershell_utf8`
  - MCP clients failing to start (`neo4j`, `postgres`, and sometimes `langflow`/`langgraph`)
  - “handshaking with MCP server failed: connection closed: initialize response”
- Yet running `/mcp` inside a session would show servers green.

## Phase 1 — Config parsing clarity (TOML vs schema)
Key realization: “parses as TOML” != “accepted by Codex schema”.

- Repo config `.codex/config.toml` was valid TOML.
- Some keys were rejected by schema tooling (Even Better TOML) and/or were expected to live in
  the user config.

Actions taken:
- Ensured the startup warning suppression flag lived in the **user** config:
  - `/home/sirvist-lab/.codex/config.toml`: `suppress_unstable_features_warning = true`
- Removed unsupported/unused schema keys from repo config (notably `http_method`), relying on the
  MCP transport implementation to use POST for JSON-RPC.

Outcome:
- User-level config parses.
- Repo-level config parses and validates against the referenced schema.

## Phase 2 — Proving the endpoints (LangFlow + LangGraph)
We validated that the URLs exported by direnv/env.sh correspond to real services.

Verified env values (examples):
- `LANGFLOW_URL=http://localhost:7861/api/v1/mcp/streamable`
- `LANGGRAPH_URL=http://localhost:2026/mcp`

LangFlow:
- GET with correct `Accept: application/json, text/event-stream` returns SSE.
- POST JSON-RPC `initialize` returns a valid initialize result.

LangGraph:
- GET may be 405, but POST initialize succeeds once probed correctly.

Outcome:
- The remaining startup failures were no longer ambiguous “method” issues; they were either
  handshake timing or non-probed dependency issues.

## Phase 3 — Making healthcheck real (live probes)
Problem: `scripts/mcp/healthcheck.sh` only printed endpoint visibility.
That is necessary but insufficient: it can’t distinguish “ports open” from “auth works” and
doesn’t verify MCP initialization.

Implementation:
- Replaced `scripts/mcp/healthcheck.sh` with a live-probing healthcheck:
  - deterministic PASS/FAIL/WARN lines
  - non-zero exit on any FAIL
  - docker container Up checks
  - deep probes for core services
  - real JSON-RPC initialize probes for LangFlow/LangGraph
  - Bifrost treated as required (HCB instance)

Runbook update:
- `docs/mcp/MCP_OPERATIONS_RUNBOOK.md` updated to explicitly state healthcheck is now “live probing”.

Outcome:
- `bash scripts/mcp/healthcheck.sh` became the SSOT “is the stack actually usable?” gate.

## Phase 4 — Wiring deep probes (redis-cli, psql, cypher-shell)
Goal: eliminate WARN fallbacks and make failures deterministic.

Status:
- `redis-cli` and `psql` installed.
- `cypher-shell` installed via Neo4j apt repository keyring + apt install.

Postgres nuance discovered:
- Password contained `@` (`POSTGRES_PASSWORD="Sirvist@2026"`).
- libpq/psql URL parsing can misinterpret `@` if embedded in a URL.

Resolution:
- Healthcheck uses discrete connection params via `PGPASSWORD` and `psql -h/-p/-U/-d`.
- Adds a deterministic fallback deep probe using `docker exec hcb_postgres psql ...` if host-port auth
  fails, ensuring the DB is validated even when host auth config differs.

Outcome:
- Healthcheck reached `RESULT: PASS` with no WARNs.

## Current state (end of session)
- Docker stack: all services Up.
- Healthcheck: live probes pass for docker containers + Redis + Postgres + Neo4j + Weaviate + Ollama.
- MCP initialize probes pass for LangFlow and LangGraph.
- Bifrost is validated as required.

## Follow-ups unlocked by this work
1) Use healthcheck output + Codex session JSONLs to pinpoint why startup prints
   “MCP startup incomplete” despite later green `/mcp` (likely timing, env inheritance,
   or different launch context).
2) HIGH backlog item captured: re-establish single source of truth + auto-alignment
   for Codex guidance/enforcement/runbooks to reduce drift.
