# Decisions

This folder tracks durable project decisions.

## Structure

- `adr/`: Architectural Decision Records (ADRs). Use when a decision materially affects
  the system, developer workflow, or long-term maintenance.
- `decision-log.md`: Append-only running log of smaller operational decisions.

## Conventions

- ADRs are append-only in practice: supersede via a new ADR.
- Name ADRs like `ADR-0001-short-title.md`.
- Each ADR should include: **Context**, **Decision**, **Consequences**, and (optionally)
  **Alternatives considered**.
