# MCP Migration Map (home-cooked-bytes)

## Purpose
Map legacy MCP servers to fresh, repo-local implementations and backing services.

## Source → Target
- `sirvist` (legacy: `03_dev_tools/mcp/sirvist_mcp_server.py`)
  - Target: `mcp_servers/sirvist_mcp_server.py`
  - Backing services: Neo4j, Redis, Postgres (if used), Weaviate, Bifrost (if referenced)
  - Env: `NEO4J_*`, `REDIS_URL`, `POSTGRES_URL`, `WEAVIATE_*`, `BIFROST_*` (as required)

- `openapi-local` (legacy: `03_dev_tools/mcp/openapi_local_mcp_server.py`)
  - Target: `mcp_servers/openapi_local_mcp_server.py`
  - Backing service: local OpenAPI JSON endpoint or file
  - Env: `SIRVIST_OPENAPI_SOURCE`

- `brave-search` (legacy: `03_dev_tools/mcp/brave_search_mcp_server.py`)
  - Target: `mcp_servers/brave_search_mcp_server.py`
  - Backing service: Brave Search API
  - Env: `BRAVE_SEARCH_API_KEY`, `BRAVE_API_KEY`

## External MCPs (no code port)
- `openaiDeveloperDocs` (remote URL MCP)
- `context7` (npx MCP)
- `sequentialthinking` (docker MCP)
- `redis` (uvx MCP)
- `postgres` (npx MCP)
- `neo4j` (neo4j-mcp binary)
- `graphiti-memory` (uvx MCP)
- `langgraph` (HTTP MCP)
- `langflow` (HTTP MCP)
- `weaviate` (binary MCP)
- `weaviate-docs` (remote URL MCP)

## Migration Rules
- No legacy shim paths (`03_dev_tools/...`) in active config.
- All custom MCPs must run from `mcp_servers/` with `./.venv/bin/python`.
- All services run in the `home-cooked-bytes` docker namespace.
