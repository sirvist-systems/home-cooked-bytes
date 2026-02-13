# TODO Delegation (Deterministic)

This repo tracks local session tasks in `00_current/codex_active_tasks.md`.

When you want to delegate a task to cloud/background workflows, use GitHub Issues as the
canonical queue and link tasks to Issues deterministically.

## Create Issues from checked tasks

1) In `00_current/codex_active_tasks.md`, check the tasks you want delegated:

```md
- [x] Example task to delegate
```

2) Run the sync script from the repo root:

```bash
cd /home/sirvist-lab/src/home-cooked-bytes
python scripts/todos/sync_checked_tasks_to_github_issues.py
```

The script will:

- Create a GitHub Issue per checked task (skipping tasks already stamped)
- Append `(GH-ISSUE: <number>)` to each delegated task line
- Apply a default label `agent:codex` (customize with `--label`)

## Notes

- Dry run: `python scripts/todos/sync_checked_tasks_to_github_issues.py --dry-run`
- Extra labels: `--label priority:p1 --label risk:low`
