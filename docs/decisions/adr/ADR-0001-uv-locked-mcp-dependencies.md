# ADR-0001: Use uv + lockfile for MCP Python dependencies

Date: 2026-02-12

## Context

This repository runs multiple MCP servers, including local Python stdio servers under `mcp_servers/`.
These servers are workflow-critical: if dependency resolution drifts, MCP startup can fail and degrade
the developer experience.

Previously, MCP dependencies were installed via `pip` from `requirements-mcp.txt` with loose version
specifiers. This can lead to non-reproducible environments across machines and across time.

## Decision

Adopt `uv` as the standard tool for reproducible installs of MCP Python dependencies:

- Maintain a minimal, human-edited dependency list in `requirements-mcp.txt`.
- Maintain a fully pinned lockfile in `requirements-mcp.lock.txt`.
- Install MCP dependencies with:
  - `uv venv --python 3.12 .venv`
  - `uv pip sync --python .venv/bin/python requirements-mcp.lock.txt`

## Consequences

- MCP server environments become deterministic and easier to debug.
- Updating dependencies becomes an explicit action (edit `requirements-mcp.txt`, regenerate the lock).
- The repo standardizes on `uv` for this workflow.

## Alternatives considered

- Continue using `pip` with loose specifiers: rejected due to drift.
- Use `pip-tools` (`pip-compile`) for lock generation: viable, but `uv` is faster and already available
  in the environment.
