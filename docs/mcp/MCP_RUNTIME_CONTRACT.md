# MCP Runtime Contract (home-cooked-bytes)

## Objectives
- Full parity MCP set without shim debt.
- Deterministic startup with explicit env requirements.
- No cross-repo path dependencies.

## MCP List (Target)
Custom (repo-local):
- `sirvist` → `mcp_servers/sirvist_mcp_server.py`
- `openapi-local` → `mcp_servers/openapi_local_mcp_server.py`
- `brave-search` → `mcp_servers/brave_search_mcp_server.py`

External:
- `openaiDeveloperDocs` (URL)
- `context7` (npx)
- `sequentialthinking` (docker)
- `redis` (uvx)
- `postgres` (npx)
- `neo4j` (binary)
- `graphiti-memory` (uvx)
- `langgraph` (HTTP)
- `langflow` (HTTP)
- `weaviate` (binary)
- `weaviate-docs` (URL)

## Env Contract (.env / .env.example)
- `OPENAI_API_KEY`
- `BRAVE_SEARCH_API_KEY`, `BRAVE_API_KEY`
- `SIRVIST_OPENAPI_SOURCE`
- `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD`, `NEO4J_DATABASE`, `NEO4J_READ_ONLY`
- `WEAVIATE_URL`, `WEAVIATE_API_KEY`
- `REDIS_URL`, `POSTGRES_URL`
- `BIFROST_URL`, `BIFROST_API_KEY`
- `GRAPHITI_TELEMETRY_ENABLED`

## Config Rules
- Custom MCPs must run from repo-local paths.
- All docker services live under `home-cooked-bytes` project namespace.
- No shims, no PATH hacks, no cross-repo references.
