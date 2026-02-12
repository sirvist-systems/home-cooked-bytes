# Codex Backlog (Parking Lot)

Timestamp (UTC): 2026-02-12 06:49

This is the capture bucket. Anything not in `00_current/codex_active_tasks.md` belongs here.

Policy:
- Every item must have a **Workstream** and a **Next action**.
- Review cadence: weekly.
- Stale rule: if untouched for 14 days, move to **Stale** with a short note.

## Inbox (Unsorted)
- [ ] Workstream: `codex_tasks` | Next: confirm how VS Code “Turn TODOs into Codex tasks” maps to our workflow (do we use it or ignore it during migration?).

## Continuity
- [ ] Workstream: `continuity_manual` | Next: write a 5-line “restart recipe” (where to look + which command to run) and pin it in `06_session_continuity/sessions/manual/SESSION_CONTINUITY_MASTER.md`.
- [ ] Workstream: `continuity_extraction` | Next: build a deterministic “jsonl slim” extractor for Codex logs (reduce to: user/assistant text + tool calls + timestamps).

## Migration
- [ ] Workstream: `repo_migration` | Next: list folders/files to carry into the clean repo (minimum: `01_codebase/`, critical docs, scripts needed for manual continuity).

## Tooling
- [ ] Workstream: `mcp_hygiene` | Next: keep MCP list minimal in legacy repo; reintroduce servers only when required.

## Stale
- (empty)

