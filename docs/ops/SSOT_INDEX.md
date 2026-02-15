# SSOT Index (home-cooked-bytes)

Update (UTC): 2026-02-14 06:05:00Z

Purpose: keep guidance **non-drifting** by declaring where the truth lives.
Other docs should link here rather than duplicating operator/startup instructions.

## Canonical entrypoints

- Daily start (personal, command-first): `DRIVE_TO_WORK.txt`
- Agent/Codex instructions (router + constraints): `AGENTS.md`

## Operations

- MCP operations runbook (start/stop/healthcheck/troubleshooting): `docs/mcp/MCP_OPERATIONS_RUNBOOK.md`
- Change surfaces (what changes matter): `docs/ops/CHANGE_SURFACES.md`
- Active enforcement (what is actually enforced): `docs/ops/ACTIVE_ENFORCEMENT.md`
- Git graph policy (merge commit only): `docs/ops/GIT_GRAPH_POLICY.md`
- Dependencies (tools + lockfiles): `docs/ops/DEPENDENCIES.md`

## Planning + decisions

- Plans index: `docs/plans/README.md`
- Decisions index: `docs/decisions/README.md`
- Decision log (append-only): `docs/decisions/decision-log.md`

## Session alignment

- Session handoff (read first; use latest): `session_continuity/summaries/`
- Current tasks/backlog: `00_current/codex_active_tasks.md`, `00_current/codex_backlog.md`

## SSOT gates

- “Is the local stack actually usable?” gate: `bash scripts/mcp/healthcheck.sh`
