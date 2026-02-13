# PLAN-0002: Dingleberry Protocol (Open Loops)

Created (UTC): 2026-02-13 08:57:00Z

## Summary

Implement a "Dingleberry" pass that surfaces open loops from sessions (unanswered questions,
unstated decisions, rewrite impulses, TODOs) and makes them actionable.

- Canonicalize to Neo4j as `Dingleberry` nodes linked to `Session`
- Mirror to GitHub Issues for execution (labels + stable IDs)
- Severity gate is stubbed for future enforcement (record only; do not block)

## Scope

- Detector interface + initial ruleset (regex + heuristics)
- Session-end integration writes `dingleberries.json`
- Neo4j writes and optional GitHub mirroring

## Non-goals

- Automatically blocking session end (for now)
- Overfitting to one chat format

## Links

- TODO delegation: `docs/runbooks/TODO_DELEGATION.md`
- Decision log: `docs/decisions/decision-log.md`
