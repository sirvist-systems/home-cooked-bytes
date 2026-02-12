#!/usr/bin/env bash
set -euo pipefail
ruff check src tests mcp_servers
