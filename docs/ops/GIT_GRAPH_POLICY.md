# Git Graph Policy (Enforced)

This repo must always produce a branch graph with visible merge lines.

## Required workflow (every task)
1) Create a new branch per task
   - `git checkout -b feature/<task-name>`
2) Commit in small, chronological slices
   - `git commit -m "<type>(<scope>): <summary>"`
3) Push branch to origin
   - `git push -u origin feature/<task-name>`
4) Open PR and **merge with a merge commit**
   - Squash: **disabled**
   - Rebase: **disabled**

## Hard rules
- Never commit directly to `main`.
- Never squash or rebase merge into `main`.
- Every change set must go through a PR.

## Enforcement points
- GitHub branch protections: PR required + merge commits only.
- Local convention: new task = new branch.
- GitHub setting: auto-delete head branches after merge (pending enablement).

## If the graph "isn't being made"
- The branch line only appears after a merge commit into `main`.
- Squash/rebase merges erase the branch line.
- If you only see a straight line, the branch hasn’t merged yet.

If a change violates this policy, revert it and re‑do via a proper branch + merge commit.
