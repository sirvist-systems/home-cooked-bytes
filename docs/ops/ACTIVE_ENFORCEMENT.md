# Active Enforcement (home-cooked-bytes)

This file lists every active enforcement mechanism in this repo.
If it's not listed here, it should be assumed **inactive**.

## Pre-commit
- **Tool:** pre-commit
- **Config:** `.pre-commit-config.yaml`
- **Hooks:**
  - ruff (lint, auto-fix)
  - ruff-format
  - end-of-file-fixer
  - trailing-whitespace
  - check-yaml
  - check-added-large-files
- **Install:** `pre-commit install`
- **Run:** `pre-commit run --all-files`
- **Status:** Active

## Formatting / Linting
- **Ruff config:** `pyproject.toml`
- **Scripts:**
  - `scripts/dev/format.sh`
  - `scripts/dev/lint.sh`
  - `scripts/dev/typecheck.sh`
- **Status:** Active

## Shims / Shell Hooks
- **Status:** None (explicitly disallowed)

## Git Hooks
- **Status:** Only via pre-commit (no custom hooks)

## MCP Enforcement
- **Status:** None (runtime-only)

## Git Graph Policy
- **Policy:** `docs/ops/GIT_GRAPH_POLICY.md`
- **Status:** Active (must follow for every task)

## Repo-local Toolchains
- **Status:** Active (convention)
- **Rule:** Any one-off project tooling should live under `tools/` (avoid polluting product `src/`).
