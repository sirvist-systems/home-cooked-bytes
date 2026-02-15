#!/usr/bin/env bash
set -euo pipefail

# Update (UTC): 2026-02-13 17:50:04Z

# Source this file to set local MCP endpoints for the Home Cooked Bytes
# docker-compose stack defined in `infra/docker/docker-compose.mcp.yml`.
#
# Usage:
#   source scripts/mcp/env.sh

set -a

export REDIS_URL="${REDIS_URL:-redis://localhost:6381/0}"

# Postgres container uses the default `postgres` user unless you changed it.
if [ -z "${POSTGRES_PASSWORD:-}" ] && [ -f .env ]; then
  # shellcheck disable=SC1091
  set -a
  source .env
  set +a
fi

export POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-}"
if [ -n "${POSTGRES_PASSWORD}" ]; then
  # URL-encode reserved characters (notably `@`) so DSNs parse correctly.
  POSTGRES_PASSWORD_ENC="$(python3 -c 'import os, urllib.parse as u; print(u.quote(os.environ["POSTGRES_PASSWORD"], safe=""))')"
  export POSTGRES_URL="${POSTGRES_URL:-postgresql://postgres:${POSTGRES_PASSWORD_ENC}@localhost:5433/postgres}"
else
  export POSTGRES_URL="${POSTGRES_URL:-postgresql://postgres@localhost:5433/postgres}"
fi

# Prefer the repo compose ports even if `.env` came from another stack.
if [[ "${REDIS_URL}" == "redis://localhost:6379"* ]]; then
  export REDIS_URL="redis://localhost:6381/0"
fi

export NEO4J_USERNAME="${NEO4J_USERNAME:-neo4j}"
export NEO4J_PASSWORD="${NEO4J_PASSWORD:-}"
export NEO4J_URI="${NEO4J_URI:-bolt://localhost:7688}"

export WEAVIATE_API_KEY="${WEAVIATE_API_KEY:-}"

export WEAVIATE_URL="${WEAVIATE_URL:-http://localhost:8092}"

export LANGFLOW_URL="${LANGFLOW_URL:-http://localhost:7861/api/v1/mcp/streamable}"
export LANGGRAPH_URL="${LANGGRAPH_URL:-http://localhost:2026/mcp}"

# Ollama (shared local endpoint by default). If you add an Ollama service to this repo's
# docker compose, override OLLAMA_HOST accordingly.
export OLLAMA_HOST="${OLLAMA_HOST:-http://127.0.0.1:11436}"

export BIFROST_URL="${BIFROST_URL:-http://127.0.0.1:8084}"

# Optional multi-region Bifrost endpoints (for Vertex/Gemini MaaS).
export BIFROST_US_CENTRAL1_URL="${BIFROST_US_CENTRAL1_URL:-http://127.0.0.1:8082}"
export BIFROST_US_SOUTH1_URL="${BIFROST_US_SOUTH1_URL:-http://127.0.0.1:8083}"

# Keep tool caches inside writable sandbox roots.
export PRE_COMMIT_HOME="${PRE_COMMIT_HOME:-/tmp/pre-commit}"

# Prefer compose port for this repo, even if .env points elsewhere.
if [ "${BIFROST_URL}" = "http://localhost:8080" ]; then
  export BIFROST_URL="http://127.0.0.1:8084"
fi

if [ "${BIFROST_US_CENTRAL1_URL}" = "http://localhost:8082" ]; then
  export BIFROST_US_CENTRAL1_URL="http://127.0.0.1:8082"
fi

if [ "${BIFROST_US_SOUTH1_URL}" = "http://localhost:8083" ]; then
  export BIFROST_US_SOUTH1_URL="http://127.0.0.1:8083"
fi

set +a
