# PLAN-0005 — Bifrost multi-region + real healthchecks

Update (UTC): 2026-02-15 03:47:45Z

## Goal

Run **three** local Bifrost instances (global, `us-central1`, `us-south1`) with isolated state, and upgrade `scripts/mcp/healthcheck.sh` to probe them with real HTTP semantics (not just TCP).

## Constraints

- Do not commit secrets (API keys, service account JSONs).
- Prefer env-vars and local `.env` for secrets.
- Avoid root-owned artifacts in the repo working tree.

## Outcomes

- Bifrost instances:
  - Global: `http://127.0.0.1:8084`
  - us-central1: `http://127.0.0.1:8082`
  - us-south1: `http://127.0.0.1:8083`
- Each instance has its own sqlite stores (config/logs) and does not share state.
- `scripts/mcp/healthcheck.sh` fails if any Bifrost `/health` fails.
- Optional deeper check: `HEALTHCHECK_OLLAMA_CHAT_MODEL=<model>` runs a non-streaming `/api/chat` ping.

## Implementation plan (tight)

1. **Bifrost config SSOT**
   - Add `infra/docker/bifrost/config.json` (safe, no secrets).
   - Ensure `config_store` and `logs_store` paths are inside the app-dir.

2. **3 instances, 3 app-dirs**
   - `infra/docker/docker-compose.mcp.yml`:
     - Add `bifrost_us_central1`, `bifrost_us_south1` services.
     - Ensure each has its own docker volume mounted at `/app/data`.
     - Pass `-app-dir /app/data`.

3. **Healthcheck semantics**
   - `scripts/mcp/healthcheck.sh`:
     - Probe `/health` for all three instances.
     - Parse JSON and require `status in {"ok","healthy"}`.

4. **Operator workflow**
   - Bring stack up: `bash scripts/mcp/up.sh`.
   - Run healthcheck:
     - Basic: `bash scripts/mcp/healthcheck.sh`
     - Deeper (local model): `HEALTHCHECK_OLLAMA_CHAT_MODEL=qwen2.5:7b bash scripts/mcp/healthcheck.sh`

## Follow-ups (not in scope here)

- Provider key/material provisioning for each region (Vertex/Gemini routing) should be done via env-vars or manual config via Bifrost UI, not by copying old `config.db`.
- Replace “update-check / binary download” behavior with pinned images/binaries if startup becomes flaky.
