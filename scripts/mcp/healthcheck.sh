#!/usr/bin/env bash

set -euo pipefail

################################################################################
# MCP Healthcheck (home-cooked-bytes)
#
# Live probing for the local MCP stack. Prints deterministic PASS/FAIL/WARN lines
# and exits non-zero if any required probe fails.
################################################################################

PASS_COUNT=0
WARN_COUNT=0
FAIL_COUNT=0

log_pass() {
  PASS_COUNT=$((PASS_COUNT + 1))
  echo "PASS $*"
}

log_warn() {
  WARN_COUNT=$((WARN_COUNT + 1))
  echo "WARN $*"
}

log_fail() {
  FAIL_COUNT=$((FAIL_COUNT + 1))
  echo "FAIL $*"
}

have() {
  command -v "$1" >/dev/null 2>&1
}

require_bin() {
  local bin="$1"
  if ! have "$bin"; then
    log_fail "bin:$bin missing"
    return 1
  fi
}

redact_url_basic() {
  # Redact credentials in URLs like scheme://user:pass@host/...
  # Best-effort only.
  local url="$1"
  if [[ "$url" =~ ^([^:]+://)([^/@]+)@(.+)$ ]]; then
    echo "${BASH_REMATCH[1]}***@${BASH_REMATCH[3]}"
  else
    echo "$url"
  fi
}

http_status_and_ctype() {
  local url="$1"
  local accept_header="$2"
  # Prints: "<status> <content-type>"
  curl -m 5 -sS -D - -o /dev/null -H "Accept: ${accept_header}" "$url" \
    | awk 'BEGIN{status=""; ctype=""} /^HTTP\//{status=$2} /^[Cc]ontent-[Tt]ype:/{gsub("\r","",$0); sub(/^[^:]+:[ ]*/,"",$0); ctype=$0} END{print status, ctype}'
}

sse_initialize_probe() {
  local name="$1"
  local url="$2"

  # 1) Confirm SSE GET works with expected Accept header.
  local accept="application/json, text/event-stream"
  local get_info
  get_info="$(http_status_and_ctype "$url" "$accept" || true)"

  local status
  local ctype
  status="$(awk '{print $1}' <<<"$get_info")"
  ctype="$(cut -d' ' -f2- <<<"$get_info" | xargs || true)"

  if [[ "$status" != "200" ]]; then
    log_fail "$name GET status=$status url=$(redact_url_basic "$url")"
    return 1
  fi
  if [[ "$ctype" != *"text/event-stream"* ]]; then
    log_fail "$name GET content-type=$ctype url=$(redact_url_basic "$url")"
    return 1
  fi

  # 2) Initialize via POST and parse first SSE data line.
  local payload
  payload='{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"hcb-healthcheck","version":"0"}}}'

  # Use --no-buffer so we can grab first event quickly.
  # We cap runtime with -m; grabbing only the first data line is enough.
  local data_line
  data_line="$(
    curl -m 5 -sS --no-buffer \
      -H "Content-Type: application/json" \
      -H "Accept: ${accept}" \
      -X POST \
      --data "$payload" \
      "$url" \
      | awk -F': ' '/^data: /{print $2; exit 0}'
  )"

  if [[ -z "$data_line" ]]; then
    log_fail "$name initialize missing data: line url=$(redact_url_basic "$url")"
    return 1
  fi

  if ! jq -e '.result.protocolVersion' >/dev/null 2>&1 <<<"$data_line"; then
    log_fail "$name initialize invalid jsonrpc result url=$(redact_url_basic "$url")"
    return 1
  fi

  local pv
  pv="$(jq -r '.result.protocolVersion' <<<"$data_line" 2>/dev/null || true)"
  log_pass "$name initialize protocolVersion=$pv"
}

json_or_sse_initialize_probe() {
  local name="$1"
  local url="$2"

  local accept="application/json, text/event-stream"

  # For some servers (e.g. LangGraph) GET may be disallowed; skip GET and POST
  # initialize directly.
  local payload
  payload='{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"hcb-healthcheck","version":"0"}}}'

  # First try to capture an SSE data line (streamable HTTP).
  local data_line
  data_line="$(
    curl -m 6 -sS --no-buffer \
      -H "Content-Type: application/json" \
      -H "Accept: ${accept}" \
      -X POST \
      --data "$payload" \
      "$url" \
      | awk -F': ' '/^data: /{print $2; exit 0}'
  )"

  if [[ -n "$data_line" ]]; then
    if jq -e '.result.protocolVersion' >/dev/null 2>&1 <<<"$data_line"; then
      local pv
      pv="$(jq -r '.result.protocolVersion' <<<"$data_line" 2>/dev/null || true)"
      log_pass "$name initialize protocolVersion=$pv"
      return 0
    fi
    log_fail "$name initialize SSE data not jsonrpc url=$(redact_url_basic "$url")"
    return 1
  fi

  # If no SSE data, attempt to read a direct JSON body.
  local body
  body="$(
    curl -m 6 -sS \
      -H "Content-Type: application/json" \
      -H "Accept: application/json" \
      -X POST \
      --data "$payload" \
      "$url" \
  )"

  if jq -e '.result.protocolVersion' >/dev/null 2>&1 <<<"$body"; then
    local pv
    pv="$(jq -r '.result.protocolVersion' <<<"$body" 2>/dev/null || true)"
    log_pass "$name initialize protocolVersion=$pv"
    return 0
  fi

  log_fail "$name initialize failed url=$(redact_url_basic "$url")"
  return 1
}

tcp_probe() {
  local name="$1"
  local host="$2"
  local port="$3"

  if have nc; then
    if nc -z "$host" "$port" >/dev/null 2>&1; then
      log_pass "$name tcp ${host}:${port}"
      return 0
    fi
    log_fail "$name tcp ${host}:${port}"
    return 1
  fi

  # Bash /dev/tcp fallback (best-effort)
  if (exec 3<>"/dev/tcp/${host}/${port}") >/dev/null 2>&1; then
    exec 3>&-
    log_warn "$name tcp ${host}:${port} (shallow; nc missing)"
    return 0
  fi
  log_fail "$name tcp ${host}:${port} (nc missing)"
  return 1
}

check_required_bins() {
  local ok=0
  require_bin curl || ok=1
  require_bin jq || ok=1
  require_bin redis-cli || ok=1
  require_bin psql || ok=1
  require_bin cypher-shell || ok=1
  require_bin docker || ok=1
  if ! docker compose version >/dev/null 2>&1; then
    log_fail "docker compose missing"
    ok=1
  fi
  return "$ok"
}

docker_compose_ps() {
  docker compose -f infra/docker/docker-compose.mcp.yml ps
}

check_docker_services_up() {
  local output
  output="$(docker_compose_ps)"

  local required=(
    hcb_redis
    hcb_postgres
    hcb_neo4j
    hcb_weaviate
    hcb_langflow
    hcb_langgraph
    hcb_ollama
    hcb_bifrost
  )

  local any_fail=0
  for container in "${required[@]}"; do
    if grep -q "^${container}[[:space:]]" <<<"$output" && grep -q "^${container}.*\bUp\b" <<<"$output"; then
      log_pass "docker:$container Up"
    else
      log_fail "docker:$container not Up"
      any_fail=1
    fi
  done

  return "$any_fail"
}

probe_redis() {
  if [[ -z "${REDIS_URL:-}" ]]; then
    log_fail "redis env REDIS_URL missing"
    return 1
  fi

  if redis-cli -u "$REDIS_URL" PING 2>/dev/null | rg -q '^PONG$'; then
    log_pass "redis PING"
    return 0
  fi
  log_fail "redis PING failed url=$(redact_url_basic "$REDIS_URL")"
  return 1
}

probe_postgres() {
  if [[ -z "${POSTGRES_URL:-}" ]]; then
    log_fail "postgres env POSTGRES_URL missing"
    return 1
  fi

  # Avoid libpq URL parsing edge-cases (e.g. '@' in passwords) by using discrete
  # connection parameters.
  local password
  password="${POSTGRES_PASSWORD:-}"

  # Try host-port first.
  if PGPASSWORD="$password" psql \
    -h "${POSTGRES_HOST:-localhost}" \
    -p "${POSTGRES_PORT:-5433}" \
    -U "${POSTGRES_USER:-postgres}" \
    -d "${POSTGRES_DB:-postgres}" \
    -c "select 1" \
    >/dev/null 2>&1; then
    log_pass "postgres query"
    return 0
  fi

  # If auth fails via port-forward but the container is up, fall back to
  # docker-exec as a deterministic deep probe (matches dockerized deployments).
  if docker exec -e PGPASSWORD="$password" hcb_postgres psql \
    -U "${POSTGRES_USER:-postgres}" \
    -d "${POSTGRES_DB:-postgres}" \
    -c "select 1" \
    >/dev/null 2>&1; then
    log_pass "postgres query (docker exec)"
    return 0
  fi

  local redacted
  redacted="postgresql://${POSTGRES_USER:-postgres}:***@${POSTGRES_HOST:-localhost}:${POSTGRES_PORT:-5433}/${POSTGRES_DB:-postgres}"
  log_fail "postgres query failed url=$redacted"
  return 1
}

probe_neo4j() {
  if [[ -z "${NEO4J_URI:-}" ]]; then
    log_fail "neo4j env NEO4J_URI missing"
    return 1
  fi

  tcp_probe "neo4j" "localhost" "7688" || return 1

  # We rely on NEO4J_URI/NEO4J_USERNAME/NEO4J_PASSWORD being set.
  if cypher-shell -a "$NEO4J_URI" -u "${NEO4J_USERNAME:-}" -p "${NEO4J_PASSWORD:-}" "RETURN 1;" >/dev/null 2>&1; then
    log_pass "neo4j cypher-shell"
    return 0
  fi
  log_fail "neo4j cypher-shell failed"
  return 1
}

probe_weaviate() {
  if [[ -z "${WEAVIATE_URL:-}" ]]; then
    log_fail "weaviate env WEAVIATE_URL missing"
    return 1
  fi
  local url="$WEAVIATE_URL/v1/meta"
  local version
  version="$(curl -m 5 -fsS "$url" | jq -r '.version' 2>/dev/null || true)"
  if [[ -n "$version" && "$version" != "null" ]]; then
    log_pass "weaviate version=$version"
    return 0
  fi
  log_fail "weaviate meta invalid url=$(redact_url_basic "$url")"
  return 1
}

probe_ollama() {
  if [[ -z "${OLLAMA_HOST:-}" ]]; then
    log_fail "ollama env OLLAMA_HOST missing"
    return 1
  fi
  local url="$OLLAMA_HOST/api/tags"
  if curl -m 5 -fsS "$url" | jq -e '.models | type=="array"' >/dev/null 2>&1; then
    local count
    count="$(curl -m 5 -fsS "$url" | jq '.models | length' 2>/dev/null || echo "?")"
    log_pass "ollama tags models=$count"
    return 0
  fi
  log_fail "ollama tags invalid url=$(redact_url_basic "$url")"
  return 1
}

probe_langflow() {
  if [[ -z "${LANGFLOW_URL:-}" ]]; then
    log_fail "langflow env LANGFLOW_URL missing"
    return 1
  fi
  sse_initialize_probe "langflow" "$LANGFLOW_URL"
}

probe_langgraph() {
  if [[ -z "${LANGGRAPH_URL:-}" ]]; then
    log_fail "langgraph env LANGGRAPH_URL missing"
    return 1
  fi
  json_or_sse_initialize_probe "langgraph" "$LANGGRAPH_URL"
}

probe_bifrost() {
  local url="http://127.0.0.1:8084/health"
  local status
  status="$(curl -m 5 -sS -o /dev/null -w "%{http_code}" "$url" || true)"
  if [[ "$status" == "200" ]]; then
    log_pass "bifrost health 200"
    return 0
  fi

  # Fallback to root if /health isn't implemented.
  local root="http://127.0.0.1:8084/"
  status="$(curl -m 5 -sS -o /dev/null -w "%{http_code}" "$root" || true)"
  if [[ "$status" =~ ^2|3|4 ]]; then
    # Even 404 from root is still proof the service is reachable.
    log_pass "bifrost reachable status=$status"
    return 0
  fi

  log_fail "bifrost unreachable 127.0.0.1:8084"
  return 1
}

main() {
  if ! check_required_bins; then
    echo "RESULT: FAIL (${PASS_COUNT} pass, ${WARN_COUNT} warn, ${FAIL_COUNT} fail)"
    exit 1
  fi

  check_docker_services_up || true

  probe_redis || true
  probe_postgres || true
  probe_neo4j || true
  probe_weaviate || true
  probe_ollama || true
  probe_langflow || true
  probe_langgraph || true
  probe_bifrost || true

  if [[ "$FAIL_COUNT" -gt 0 ]]; then
    echo "RESULT: FAIL (${PASS_COUNT} pass, ${WARN_COUNT} warn, ${FAIL_COUNT} fail)"
    exit 1
  fi
  echo "RESULT: PASS (${PASS_COUNT} pass, ${WARN_COUNT} warn, ${FAIL_COUNT} fail)"
}

main "$@"
