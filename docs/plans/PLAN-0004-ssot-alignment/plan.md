# PLAN-0004 — SSOT alignment (DRIVE_TO_WORK + AGENTS + ops index)

Update (UTC): 2026-02-14 06:05:00Z

## Goal

Reduce instruction drift by making the “single source of truth” explicit:

- `DRIVE_TO_WORK.txt` remains the personal daily-start checklist.
- `AGENTS.md` remains lean (Codex-facing router + constraints).
- `docs/ops/SSOT_INDEX.md` declares canonical docs so other files link instead of copying.

## Success criteria

- Startup/MCP troubleshooting advice is consistent across:
  - `DRIVE_TO_WORK.txt`
  - `AGENTS.md`
  - `docs/mcp/MCP_OPERATIONS_RUNBOOK.md`
- A new SSOT index exists and other docs can link to it.

## Notes

- Prefer authoritative sources when making behavioral claims:
  - OpenAI Developer Docs MCP for Codex behavior
  - Context7 for vendor/library docs
