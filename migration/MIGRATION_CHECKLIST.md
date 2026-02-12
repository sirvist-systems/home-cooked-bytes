# Migration Checklist: sirvist-lab → home-cooked-bytes

## Baseline carry
- [ ] Carry ADRs (`02_knowledge/adr/`) into `docs/adr/` (curated or full set)
- [ ] Carry minimal canon docs into `docs/canon/`
- [ ] Keep `.codex/` repo config + rules
- [ ] Keep `00_current/` workflow files

## Exclusions (no debt)
- [ ] Do NOT migrate shell wrappers / PATH init / git wrappers
- [ ] Do NOT migrate heavy pre-commit enforcement stack (for now)
- [ ] Do NOT migrate secrets: `.env`, `.credentials/`, `.secrets/`, tokens, service account JSON
- [ ] Do NOT migrate local-only continuity: `06_session_continuity/`, `.sirvist/`, `00__feed-me-seymore/`

## Verification
- [ ] `git status --ignored -sb` shows `.credentials/` ignored (not tracked)
- [ ] `rg -n "sirvist-git-commit|sirvist_path_init_wsl|\\.env|06_session_continuity|00__feed-me-seymore" .` is empty (or only appears in explicitly archived docs)
- [ ] `codex mcp list` shows minimal MCP set

## GitHub hard policy (manual UI step)
- [ ] Protect `main`
- [ ] Require PRs
- [ ] Allow merge commits
- [ ] Disable squash merges
- [ ] Disable rebase merges
- [ ] Auto-delete branches after merge
