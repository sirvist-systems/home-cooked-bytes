# Codex Rules (execpolicy)

Rules control which commands Codex can run **outside** the sandbox without asking you.
They are evaluated by Codex's "execpolicy" engine.

## Enable (Team Config)

1. Copy or rename `.codex/rules/default.rules.example` to `.codex/rules/default.rules`
   (already done in this repo).
2. Restart Codex (rules are loaded at startup).

## User rules (machine-scoped)

User rules live at `~/.codex/rules/default.rules`. Keep them compatible with (or identical to)
this repo’s rules so behavior doesn’t surprise you when switching repos.

## Test a rule

Use execpolicy to see what Codex would do:

```powershell
codex execpolicy check --pretty --rules .codex/rules/default.rules -- git status
codex execpolicy check --pretty --rules .codex/rules/default.rules -- curl https://example.com
```

Expected results with the current rules:
- `git status` -> allow
- `curl ...` -> allow

Team policy baked into the current rules:
- Allow network fetches by default
- Prompt for installs / “download and run code”
- Prompt or forbid destructive commands

## Editing guidance

- Prefer **prefix rules** (exact argv-prefix matching) for predictability.
- Keep the file small and auditable; add rules only when you feel real pain.
- Use `decision="prompt"` for anything that can delete data or rewrite history.
