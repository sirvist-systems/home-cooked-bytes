# Codex Active Tasks (This Session)

Timestamp (UTC): 2026-02-12 06:49

Rules:
- Max 3 items in **Doing**.
- Any new idea goes to `00_current/codex_backlog.md` unless explicitly promoted.
- If a task needs more than 2 concrete sub-steps, split it.

## Doing
- [ ] Verify `sirvist-checkpoint` artifacts exist for this session (folder path + key files) and record the pointer in `06_session_continuity/sessions/manual/`.

  - Checkpoint pointer: `06_session_continuity/sessions/manual/021226_014821_config_toml_environment_stabilize_for_migrate/`

## Next
- [ ] Explore safe repo automation workflows (IP-safe)
  - [ ] Survey OpenAI/Codex-supported automation patterns (e.g., CLI + policies + background agents)
  - [ ] Define what is safe to automate vs must-prompt actions
  - [ ] Propose a minimal “delegate from TODO list” workflow for this repo
- [ ] Improve repo orientation docs (reduce drift)
  - [ ] Refine `AGENTS.md` to be more deliberate but still short
  - [ ] Ensure docs point to SSOT (avoid instruction sprawl)
  - [ ] Decide which docs are “read on session start” vs “reference only”
- [ ] Patent sprint toolchain v1: scaffold `tools/patent_sprint/` (isolated, multi-pass, Neo4j-first)
  - [ ] Port prompts + pilot deliverable templates
  - [ ] Implement runner passes (intake → citations → claims → compliance → ideas → drawings → package)
  - [ ] DOT→SVG+PNG render pipeline verified
  - [ ] Plan + validate USPTO rules/laws corpus completeness in Neo4j
- [ ] Create/standardize a frictionless “manual continuity” workflow for migration (what gets captured, where it goes, and the restart command).
- [ ] Migrate to clean repo (define scope: what to carry vs drop; create new repo skeleton).
- [ ] Enable GitHub auto-delete merged branches (repo setting).

## Done
- [x] Captured checkpoint pointer for migration stability: `06_session_continuity/sessions/manual/021226_014821_config_toml_environment_stabilize_for_migrate/`. (GH-ISSUE: 2)
- [x] Stabilize Codex MCP set for migration (minimal servers + verified config load). (GH-ISSUE: 3)
