# ADR-0002: Add repo-isolated Ollama service for local-model offload

Date: 2026-02-12

## Context

This repository benefits from offloading certain tasks (summarization, indexing, bulk rewrite, and
non-critical ideation) to local models to reduce hosted-model costs.

Historically, local Ollama may be shared from another stack (e.g., a different repo's Docker
compose project). That coupling can create confusion, port collisions, and hidden dependencies.

## Decision

Add an `ollama` service to this repo’s MCP docker compose stack (`infra/docker/docker-compose.mcp.yml`).

- Default host binding: `127.0.0.1:11436 -> 11434` (avoid collisions with other stacks).
- Persist models via a named volume (`hcb_ollama_data`).
- Expose the endpoint to tools via `OLLAMA_HOST` set in `scripts/mcp/env.sh`.

## Consequences

- Local-model offload becomes repo-scoped and reproducible.
- Developers can run strict MCP mode without relying on another repo’s containers.
- The machine must have enough disk space for model weights in `hcb_ollama_data`.

## Alternatives considered

- Keep using a shared Ollama container: simpler initially, but increases cross-repo coupling.
- Install Ollama outside Docker: works, but is less reproducible across machines.
