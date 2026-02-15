Update (UTC): 2026-02-15 03:51:30Z

# Narrative Arc — Bifrost multiregion + deeper healthchecks + clean git cadence

This document continues the story after:

- `session_continuity/summaries/20260213_session_handoff.md`
- `session_continuity/summaries/20260213_mcp_healthcheck_live_probing_narrative_arc.md`

## Why this work happened

We were migrating away from the legacy `sirvist-lab` repo/stack toward `home-cooked-bytes` (HCB).
Two persistent sources of friction were:

1) **Docker “contamination”**: root-owned artifacts created by containers, and historical `/mnt/`-backed
   volumes from older WSL instances.
2) **Operational confidence**: knowing the stack is not just “up”, but actually usable for agent work.

Additionally, `sirvist-checkpoint` narratives relied on **Bifrost** for routing/model access, and we
needed **three region endpoints** so different Vertex/Gemini MaaS regions can be selected intentionally.

## Starting state

- Bifrost existed as a single instance in HCB (host port `8084`).
- There was no checked-in `config.json` in `infra/docker/bifrost/`, so Bifrost booted with defaults.
- `scripts/mcp/healthcheck.sh` only probed the single global Bifrost instance.

## Phase 1 — Vendor current-guideline verification

Per repo rules, we validated current Bifrost “app-dir” semantics using Context7 docs.
Key facts from docs:

- `-app-dir` controls where Bifrost stores persistent data (including sqlite stores).
- In Docker, mounting a volume to `/app/data` acts as the app-dir.
- `/health` is a real health endpoint that checks store connectivity.

## Phase 2 — Multi-instance Bifrost in docker-compose

We updated `infra/docker/docker-compose.mcp.yml` to run 3 instances:

- `bifrost` (global): host `8084` → container `8080`
- `bifrost_us_central1`: host `8082` → container `8080`
- `bifrost_us_south1`: host `8083` → container `8080`

### Isolation strategy

Each instance mounts a distinct docker volume to `/app/data` so sqlite stores do not collide:

- `hcb_bifrost_global_data:/app/data`
- `hcb_bifrost_us_central1_data:/app/data`
- `hcb_bifrost_us_south1_data:/app/data`

Each instance starts with `-app-dir /app/data`.

### Config file

We copied the legacy `sirvist-lab/bifrost_config/config.json` into HCB as a safe, secret-free config:

- New file: `infra/docker/bifrost/config.json`

We updated sqlite paths to be inside `/app/data`:

- `/app/data/config.db`
- `/app/data/logs.db`

This prevents writing into root-owned default locations.

### Root-owned repo folder surprise

We hit a concrete blocker: `infra/docker/bifrost/` was root-owned (likely created by a previous
container run). That prevented adding `config.json` via normal repo writes.

Resolution:

- Renamed the root-owned folder to `infra/docker/bifrost.root_owned.bak/`.
- Recreated `infra/docker/bifrost/` as user-owned.

## Phase 3 — Healthcheck improvements (“real checks”)

`scripts/mcp/healthcheck.sh` was extended so Bifrost health is no longer a shallow TCP check.

New behavior:

- Probes all three endpoints and requires JSON `status` to be `ok`/`healthy`:
  - `http://127.0.0.1:8084/health`
  - `http://127.0.0.1:8082/health`
  - `http://127.0.0.1:8083/health`

Optional deeper gate:

- `HEALTHCHECK_OLLAMA_CHAT_MODEL=qwen2.5:7b bash scripts/mcp/healthcheck.sh`
  - Performs a non-streaming `POST /api/chat` to Ollama and asserts it returns a message.

This gives a fast “is an LLM actually responding” signal without calling external providers.

## Phase 4 — Git cadence & enforcement lessons

We followed `docs/ops/GIT_GRAPH_POLICY.md`:

- Created a dedicated branch: `feature/mcp-stack-hardening-ssot-bifrost`.
- Committed in small slices.
- Pushed to origin.

Pre-commit enforcement (`ruff`) initially blocked a commit due to long lines in
`infra/langgraph_deepagents_backend/agent.py`. This was fixed so future commits are unblocked.

## Current status (end state)

- Three Bifrost instances run and `/health` returns OK.
- Healthcheck passes and can optionally validate a local-model chat response.
- Plan doc exists:
  - `docs/plans/PLAN-0005-bifrost-multiregion-healthcheck/README.md`
- Branch pushed to GitHub.

## Next work to pick up

The missing piece is not “containers exist”, but “callers choose regions intentionally”:

- Decide convention for where region selection happens (caller chooses endpoint vs Bifrost routes internally).
- Update LangGraph + any scripts to use `BIFROST_US_CENTRAL1_URL` / `BIFROST_US_SOUTH1_URL` when required.
