# PLAN-0001: Session Continuity (Graph-First)

Created (UTC): 2026-02-13 08:57:00Z

## Summary

Implement a graph-first continuity system for home-cooked-bytes:

- Neo4j: canonical continuity truth (relationships + provenance)
- Postgres: required append-only ledger (events/metadata)
- Weaviate: semantic retrieval over artifacts/corpora
- Redis: hot cache + queues + locks (not canonical)
- Agent memory: thin pointers + summaries; the "thickness" lives in DB + artifacts

## Scope

- Session start/end scripts with deterministic IDs
- Session handoff artifacts (60-second read)
- Neo4j schema for Session/Artifact/Decision/Task/ModelRun
- Postgres ledger schema + minimal writer

## Non-goals

- Production hosting
- Multi-user auth/RBAC
- Persisting entire chat transcripts as canonical memory

## Links

- Decision log: `docs/decisions/decision-log.md`
- ADRs: `docs/decisions/adr/`
- Handoff: `session_continuity/summaries/YYYYMMDD_session_handoff.md`

## Graduation criteria

When decisions are durable (likely to hold for weeks/months) and affect the repo broadly, capture
them in:

- ADRs: `docs/decisions/adr/`
- Repo-wide decision log: `docs/decisions/decision-log.md`
