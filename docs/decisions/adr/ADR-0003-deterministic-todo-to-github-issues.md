# ADR-0003: Deterministic sync from local TODOs to GitHub Issues

Date: 2026-02-12

## Context

This repo uses local session task lists (`00_current/codex_active_tasks.md`, `00_current/codex_backlog.md`).
To delegate work to cloud/background workflows (including Codex/ChatGPT tooling), we need a canonical,
auditable queue.

GitHub Issues provide a stable system of record (IDs, labels, links to PRs) but we still want to keep
the lightweight local markdown workflow.

## Decision

Adopt GitHub Issues as the canonical delegation queue, with a deterministic bridge script:

- Script: `scripts/todos/sync_checked_tasks_to_github_issues.py`
- Source: checked tasks (`- [x] ...`) in `00_current/codex_active_tasks.md`
- Idempotency: once synced, a task line is stamped with `(GH-ISSUE: <n>)` and skipped on future runs.

## Consequences

- Delegated tasks gain stable identifiers and can be linked to PRs.
- Local session flow remains markdown-first.
- Some workflows will prefer adding labels (e.g. `agent:codex`); older GitHub CLI versions may require
  creating labels via API.

## Alternatives considered

- Use GitHub Projects only: helpful for visualization, but Issues remain the atomic work item.
- Use only markdown: rejected due to lack of durable IDs and cross-tool integration.
