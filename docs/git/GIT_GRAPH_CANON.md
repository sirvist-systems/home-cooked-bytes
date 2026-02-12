# Git Graph Canon (Branch-Per-Task + Merge Commits)

This repo is optimized for a readable Git Graph.

## Non-negotiable rules

1) **Branch-per-task**
- Every meaningful unit of work happens on its own short-lived branch.
- Use names like `feat/...`, `fix/...`, `chore/...`, `docs/...`.

2) **Merge commits only for integrating work**
- When a task branch is complete, merge it into `main` using a **merge commit**.
- Do **not** squash-merge feature branches.
- Do **not** fast-forward merge when integrating; keep the branch shape.

3) **No history rewriting on shared branches**
- No rebases on shared branches.
- No force-push to `main`.

4) **PR-based integration (recommended)**
- Push branches and merge via PR.
- Keep `main` protected.

## GitHub settings (hard enforcement)

In GitHub repo settings:
- Protect `main`
- Require PRs
- Allow merge commits
- Disable squash merges
- Disable rebase merges
- Auto-delete branches after merge
