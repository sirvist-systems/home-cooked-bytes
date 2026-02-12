#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"

echo "Redis:   ${REDIS_URL:-redis://localhost:6381/0}"
echo "Postgres:${POSTGRES_URL:-postgresql://postgres:REPLACE_ME@localhost:5433/postgres}"
echo "Neo4j:   ${NEO4J_URI:-bolt://localhost:7688}"
echo "Weaviate:${WEAVIATE_URL:-http://localhost:8082}"
echo "Langflow:${LANGFLOW_URL:-http://localhost:7861/api/v1/mcp/streamable}"
echo "Langgraph:${LANGGRAPH_URL:-http://localhost:2026}"
echo "Bifrost: ${BIFROST_URL:-http://localhost:8081}"

echo "(Healthcheck is config visibility only for now)"
