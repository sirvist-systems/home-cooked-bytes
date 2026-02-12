#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
docker compose --env-file .env -f infra/docker/docker-compose.mcp.yml ps
