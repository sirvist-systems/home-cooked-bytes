from __future__ import annotations

import html
import json
import os
import re
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from fastmcp import FastMCP
from neo4j import GraphDatabase

from paths import bifrost_allowlists_dir, env_example_path, env_path
from paths import repo_root as repo_root_path


def _load_kv_file(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    if not path.exists():
        return data
    for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        data[key] = value.strip().strip('"')
    return data


def _load_repo_env(repo_root: Path) -> dict[str, str]:
    """
    Load environment key-values from repo files (secret-free defaults first, then .env overrides).

    Precedence within this helper:
      1) .env.example  (documented defaults; secret-free)
      2) .env          (local overrides; may contain secrets)
    """
    env: dict[str, str] = {}
    env.update(_load_kv_file(env_example_path()))
    env.update(_load_kv_file(env_path()))
    return env


def _repo_root() -> Path:
    return repo_root_path()


def _neo4j_driver(repo_root: Path):
    env = _load_repo_env(repo_root)
    uri = env.get("NEO4J_URI", "bolt://localhost:7687")
    user = env.get("NEO4J_USERNAME", env.get("NEO4J_USER", "neo4j"))
    password = env.get("NEO4J_PASSWORD", "")
    return GraphDatabase.driver(uri, auth=(user, password))


def _ensure_readonly(query: str) -> None:
    q = query.strip()
    if not q:
        raise ValueError("Empty Cypher query")
    # Allow CALL ... RETURN style procedures, but block obvious writes.
    banned = [
        r"\bCREATE\b",
        r"\bMERGE\b",
        r"\bDELETE\b",
        r"\bDETACH\s+DELETE\b",
        r"\bSET\b",
        r"\bDROP\b",
        r"\bREMOVE\b",
        r"\bLOAD\s+CSV\b",
        r"\bCALL\s+db\.index\.",  # schema mutation-ish; keep conservative
        r"\bCALL\s+db\.constraints\.",  # may include create/drop
    ]
    for pat in banned:
        if re.search(pat, q, flags=re.IGNORECASE):
            raise ValueError("Only read-only Cypher is allowed by this MCP tool.")


repo_root = _repo_root()
repo_env = _load_repo_env(repo_root)
mcp = FastMCP("sirvist")

_TAG_RE = re.compile(r"<[^>]+>")


def _env(name: str, default: str = "") -> str:
    v = (os.getenv(name) or "").strip().strip('"')
    if v:
        return v
    v2 = (repo_env.get(name) or "").strip().strip('"')
    return v2 if v2 else default


def _int_env(name: str, default: int) -> int:
    raw = _env(name, "")
    if not raw:
        return default
    try:
        return int(raw)
    except Exception:
        return default


_TOKEN_CACHE: dict[str, Any] = {"token": None, "ts": 0.0}


def _gcloud_adc_access_token() -> str:
    token = _env("SIRVIST_VERTEX_ACCESS_TOKEN") or _env("VERTEX_ACCESS_TOKEN")
    if token:
        return token

    now = time.time()
    cached = _TOKEN_CACHE.get("token")
    ts = float(_TOKEN_CACHE.get("ts") or 0.0)
    # Access tokens are typically ~1 hour. Refresh after 30 min.
    if cached and (now - ts) < 1800:
        return str(cached)

    out = subprocess.check_output(
        ["gcloud", "auth", "application-default", "print-access-token"],
        text=True,
    ).strip()
    _TOKEN_CACHE["token"] = out
    _TOKEN_CACHE["ts"] = now
    return out


def _clean_snippet(snippet: str) -> str:
    s = (snippet or "").strip()
    s = html.unescape(s)
    s = _TAG_RE.sub("", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _vertex_ai_search(*, datastore_id: str, query: str, k: int) -> dict[str, Any]:
    project = _env("SIRVIST_VERTEX_PROJECT_ID", _env("GOOGLE_CLOUD_PROJECT", ""))
    location = _env("SIRVIST_VERTEX_LOCATION", _env("GOOGLE_CLOUD_LOCATION", "global")) or "global"
    collection = _env("SIRVIST_VERTEX_COLLECTION", "default_collection")
    serving_config = _env("SIRVIST_VERTEX_SERVING_CONFIG", "default_search")
    if not project:
        raise ValueError(
            "Missing Vertex project id (SIRVIST_VERTEX_PROJECT_ID or GOOGLE_CLOUD_PROJECT)."
        )

    url = (
        f"https://discoveryengine.googleapis.com/v1/projects/{project}"
        f"/locations/{location}/collections/{collection}"
        f"/dataStores/{datastore_id}/servingConfigs/{serving_config}:search"
    )
    payload = {
        "query": query,
        "pageSize": max(1, min(20, int(k))),
        "contentSearchSpec": {"snippetSpec": {"returnSnippet": True}},
    }
    token = _gcloud_adc_access_token()
    req = urllib.request.Request(
        url=url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "content-type": "application/json",
            "authorization": f"Bearer {token}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace") if hasattr(e, "read") else str(e)
        raise RuntimeError(
            f"Vertex AI Search HTTP {getattr(e, 'code', 'unknown')}: {detail}"
        ) from e


def _build_evidence_packet(
    *,
    query: str,
    raw: dict[str, Any],
    max_results: int,
    source_kind: str,
    datastore_id: str,
) -> dict[str, Any]:
    max_snippet_chars = _int_env("SIRVIST_PATENT_RAG_MAX_SNIPPET_CHARS", 900)
    max_packet_chars = _int_env("SIRVIST_PATENT_RAG_MAX_PACKET_CHARS", 8000)

    packet: dict[str, Any] = {
        "query": query,
        "source": "vertex_ai_search",
        "datastore_id": datastore_id,
        "source_kind": source_kind,
        "results": [],
    }
    results = raw.get("results") if isinstance(raw, dict) else None
    if not isinstance(results, list):
        return packet

    for item in results[:max_results]:
        if not isinstance(item, dict):
            continue
        doc = item.get("document")
        if not isinstance(doc, dict):
            continue
        ds = doc.get("derivedStructData")
        if not isinstance(ds, dict):
            continue
        link = str(ds.get("link") or "").strip()
        title = str(ds.get("title") or "").strip()
        doc_id = str(doc.get("id") or item.get("id") or "").strip()

        snippet_text = ""
        snippets = ds.get("snippets")
        if isinstance(snippets, list) and snippets:
            first = snippets[0]
            if isinstance(first, dict):
                snippet_text = _clean_snippet(str(first.get("snippet") or ""))
        if max_snippet_chars > 0 and len(snippet_text) > max_snippet_chars:
            snippet_text = snippet_text[:max_snippet_chars] + "…"

        packet["results"].append(
            {
                "doc_id": doc_id or None,
                "title": title or None,
                "uri": link or None,
                "snippet": snippet_text or None,
                "source_kind": source_kind,
                "datastore_id": datastore_id,
            }
        )

    raw_json = json.dumps(packet, ensure_ascii=False)
    if max_packet_chars > 0 and len(raw_json) > max_packet_chars:
        for r in packet.get("results", []):
            if isinstance(r, dict):
                r["snippet"] = None
        raw_json = json.dumps(packet, ensure_ascii=False)
        if len(raw_json) > max_packet_chars:
            packet["results"] = (packet.get("results") or [])[: max(1, max_results // 2)]

    return packet


def _load_json_list(path: Path) -> set[str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return {str(x).strip() for x in data if str(x).strip()}
    except Exception:
        return set()
    return set()


_BIFROST_MODEL_ALLOWLIST: dict[str, set[str]] = {
    "openai": _load_json_list(bifrost_allowlists_dir() / "global_openai_models.json"),
    "vertex": set().union(
        _load_json_list(bifrost_allowlists_dir() / "global_vertex_models.json"),
        _load_json_list(bifrost_allowlists_dir() / "us_central1_vertex_models.json"),
        _load_json_list(bifrost_allowlists_dir() / "us_south1_vertex_models.json"),
    ),
}


def _enforce_bifrost_model_allowlist(model: str) -> None:
    raw = (model or "").strip()
    if not raw:
        raise ValueError("model is required")
    if "/" not in raw:
        raise ValueError("model must be provider-prefixed (e.g., openai/gpt-5.2-2025-12-11).")
    provider, model_id = raw.split("/", 1)
    allow = _BIFROST_MODEL_ALLOWLIST.get(provider.strip().lower())
    if not allow:
        return
    if model_id.strip() not in allow:
        raise ValueError(
            f"Model '{raw}' is not in the allowlist for provider '{provider}'. "
            "Use a versioned, VK-allowed model id."
        )


def _bifrost_chat_completions(
    *,
    model: str,
    messages: list[dict[str, Any]],
    max_tokens: int,
    temperature: float,
) -> dict[str, Any]:
    bifrost_url = _env("BIFROST_URL", "http://localhost:8080").rstrip("/")
    bifrost_vk = _env("BIFROST_API_KEY", _env("BIFROST_VK", "")).strip()
    if not bifrost_vk:
        raise ValueError("Missing Bifrost VK (set BIFROST_API_KEY or BIFROST_VK).")

    _enforce_bifrost_model_allowlist(model)

    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "max_tokens": int(max_tokens),
    }
    # Some models (notably certain OpenAI versions) reject non-default temperature values.
    # We optimistically include it, but will retry without temperature if the provider rejects it.
    payload["temperature"] = float(temperature)
    last_detail = ""
    for attempt in range(3):
        req = urllib.request.Request(
            url=f"{bifrost_url}/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "content-type": "application/json",
                "x-bf-vk": bifrost_vk,
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                return json.loads(resp.read().decode("utf-8", "replace"))
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", errors="replace") if hasattr(e, "read") else str(e)
            last_detail = detail
            code = getattr(e, "code", None)
            # Retry without temperature if the provider rejects it (common for some OpenAI models).
            if code == 400 and "temperature" in detail and "Only the default (1)" in detail:
                payload.pop("temperature", None)
                continue
            # Transient provider failures.
            if code in {502, 503, 504} and attempt < 2:
                time.sleep(2**attempt)
                continue
            raise RuntimeError(f"Bifrost HTTP {code or 'unknown'}: {detail}") from e

    raise RuntimeError(f"Bifrost failed after retries: {last_detail}")


def _langgraph_base_url() -> str:
    return (_env("SIRVIST_LANGGRAPH_URL", _env("LANGGRAPH_URL", "http://localhost:2024"))).rstrip(
        "/"
    )


def _http_json(method: str, url: str, payload: dict[str, Any] | None) -> Any:
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(
        url=url,
        data=body,
        headers={"content-type": "application/json"},
        method=method.upper(),
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8", "replace")
        return json.loads(raw) if raw.strip() else {}
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace") if hasattr(e, "read") else str(e)
        raise RuntimeError(f"HTTP {getattr(e, 'code', 'unknown')}: {detail}") from e


def _as_dict(value: Any, *, list_key: str = "items") -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, list):
        return {list_key: value, "count": len(value)}
    return {"value": value}


@mcp.tool(
    name="neo4j_query",
    description="Run a READ-ONLY Cypher query against the local Sirvist Neo4j instance.",
)
def neo4j_query(query: str, params_json: str | None = None, limit: int = 200) -> dict[str, Any]:
    _ensure_readonly(query)
    params: dict[str, Any] = {}
    if params_json:
        params = json.loads(params_json)
        if not isinstance(params, dict):
            raise ValueError("params_json must decode to a JSON object")
    if limit <= 0 or limit > 2000:
        raise ValueError("limit must be between 1 and 2000")

    # Best-effort cap to avoid huge payloads; only apply if query doesn't already contain LIMIT.
    capped_query = query
    if re.search(r"\bLIMIT\b", query, flags=re.IGNORECASE) is None:
        capped_query = f"{query.rstrip()}\nLIMIT {limit}"

    driver = _neo4j_driver(repo_root)
    try:
        with driver.session() as session:
            rows = session.run(capped_query, **params).data()
            return {"rows": rows, "row_count": len(rows)}
    finally:
        driver.close()


def _ensure_schema_only(query: str) -> None:
    q = query.strip()
    if not q:
        raise ValueError("Empty Cypher query")
    # Only allow schema operations (constraints/indexes) and introspection.
    allowed = [
        r"^\s*CREATE\s+(CONSTRAINT|INDEX)\b",
        r"^\s*DROP\s+(CONSTRAINT|INDEX)\b",
        r"^\s*SHOW\s+(CONSTRAINTS|INDEXES)\b",
        r"^\s*CALL\s+db\.constraints\b",
        r"^\s*CALL\s+db\.indexes\b",
    ]
    if not any(re.search(pat, q, flags=re.IGNORECASE) for pat in allowed):
        raise ValueError("Only schema/index/constraint operations are allowed by this MCP tool.")
    # Extra safety: reject non-schema writes even if mixed in.
    banned = [r"\bCREATE\b(?!\s+(CONSTRAINT|INDEX)\b)", r"\bMERGE\b", r"\bDELETE\b", r"\bSET\b"]
    for pat in banned:
        if re.search(pat, q, flags=re.IGNORECASE):
            raise ValueError("Non-schema writes are not allowed by this MCP tool.")


@mcp.tool(
    name="neo4j_schema",
    description=(
        "Run Cypher schema operations ONLY (constraints/indexes) against "
        "the local Sirvist Neo4j instance."
    ),
)
def neo4j_schema(query: str) -> dict[str, Any]:
    _ensure_schema_only(query)
    driver = _neo4j_driver(repo_root)
    try:
        with driver.session() as session:
            res = session.run(query)
            # Consume summary for side-effect queries.
            summary = res.consume()
            counters = summary.counters
            return {
                "ok": True,
                "counters": {
                    "constraints_added": counters.constraints_added,
                    "constraints_removed": counters.constraints_removed,
                    "indexes_added": counters.indexes_added,
                    "indexes_removed": counters.indexes_removed,
                },
                "notifications": [n.get("description") for n in (summary.notifications or [])],
            }
    finally:
        driver.close()


@mcp.tool(
    name="neo4j_inventory",
    description=(
        "Return basic inventory: labels and relationship types (counts only, plus sample lists)."
    ),
)
def neo4j_inventory() -> dict[str, Any]:
    driver = _neo4j_driver(repo_root)
    try:
        with driver.session() as session:
            labels = [
                r["label"]
                for r in session.run(
                    "CALL db.labels() YIELD label RETURN label ORDER BY label"
                ).data()
            ]
            rels = [
                r["relationshipType"]
                for r in session.run(
                    "CALL db.relationshipTypes() YIELD relationshipType "
                    "RETURN relationshipType ORDER BY relationshipType"
                ).data()
            ]
            return {
                "labels_count": len(labels),
                "rels_count": len(rels),
                "labels_sample": labels[:200],
                "rels_sample": rels[:200],
            }
    finally:
        driver.close()


@mcp.tool(
    name="patent_rag.query",
    description=(
        "Query the patent corpus and return a bounded EvidencePacket JSON. "
        "Backends: vertex (Vertex AI Search) or local (Sirvist hybrid RAG)."
    ),
)
def patent_rag_query(
    query: str,
    k: int = 5,
    backend: str = "vertex",
    sources: str | None = None,
) -> dict[str, Any]:
    backend_n = (backend or "vertex").strip().lower()
    q = (query or "").strip()
    if not q:
        raise ValueError("query is required")

    requested_sources = {"drafts", "provisional"}
    if sources is not None:
        parsed = [s.strip().lower() for s in str(sources).split(",") if s.strip()]
        requested_sources = set(parsed)
        unknown = requested_sources.difference({"drafts", "provisional"})
        if unknown:
            raise ValueError("sources must be a comma-separated list of: drafts, provisional")
        if not requested_sources:
            raise ValueError("sources must include at least one of: drafts, provisional")

    max_results = max(1, min(20, int(k)))
    if backend_n == "vertex":
        drafts_ds = _env("SIRVIST_VERTEX_PATENT_DRAFTS_DATASTORE_ID", "")
        provisional_ds = _env("SIRVIST_VERTEX_PROVISIONAL_DATASTORE_ID", "")
        if not drafts_ds and not provisional_ds:
            raise ValueError(
                "Missing Vertex datastore ids. Set "
                "SIRVIST_VERTEX_PATENT_DRAFTS_DATASTORE_ID and/or "
                "SIRVIST_VERTEX_PROVISIONAL_DATASTORE_ID."
                "SIRVIST_VERTEX_PROVISIONAL_DATASTORE_ID."
            )
        if "drafts" not in requested_sources:
            drafts_ds = ""
        if "provisional" not in requested_sources:
            provisional_ds = ""
        if not drafts_ds and not provisional_ds:
            raise ValueError(
                "Requested sources are not configured. Set Vertex datastore ids "
                "for the requested sources."
            )

        # Split budget across sources so we always return evidence from BOTH
        # when both are configured.
        k_provisional = 0
        k_drafts = 0
        if drafts_ds and provisional_ds:
            k_provisional = max(1, max_results // 2)
            k_drafts = max_results - k_provisional
        elif drafts_ds:
            k_drafts = max_results
        else:
            k_provisional = max_results

        packets: list[dict[str, Any]] = []
        if drafts_ds and k_drafts > 0:
            raw = _vertex_ai_search(datastore_id=drafts_ds, query=q, k=k_drafts)
            packets.append(
                _build_evidence_packet(
                    query=q,
                    raw=raw,
                    max_results=k_drafts,
                    source_kind="drafts",
                    datastore_id=drafts_ds,
                )
            )
        if provisional_ds and k_provisional > 0:
            raw = _vertex_ai_search(datastore_id=provisional_ds, query=q, k=k_provisional)
            packets.append(
                _build_evidence_packet(
                    query=q,
                    raw=raw,
                    max_results=k_provisional,
                    source_kind="provisional",
                    datastore_id=provisional_ds,
                )
            )

        merged: dict[str, Any] = {
            "query": q,
            "source": "vertex_ai_search",
            "results": [],
            "sources": [
                {"source_kind": "drafts", "datastore_id": drafts_ds} if drafts_ds else None,
                {"source_kind": "provisional", "datastore_id": provisional_ds}
                if provisional_ds
                else None,
            ],
        }
        merged["sources"] = [x for x in merged["sources"] if x]

        # Interleave results to preserve representation, with de-dupe by (uri, doc_id).
        lists: list[list[dict[str, Any]]] = []
        for pkt in packets:
            rows = pkt.get("results") if isinstance(pkt, dict) else None
            if isinstance(rows, list):
                lists.append([r for r in rows if isinstance(r, dict)])

        seen: set[tuple[str, str]] = set()
        for i in range(max(len(x) for x in lists) if lists else 0):
            for lst in lists:
                if i >= len(lst):
                    continue
                r = lst[i]
                key = (str(r.get("uri") or ""), str(r.get("doc_id") or ""))
                if key in seen:
                    continue
                seen.add(key)
                merged["results"].append(r)
                if len(merged["results"]) >= max_results:
                    break
            if len(merged["results"]) >= max_results:
                break

        return merged

    if backend_n == "local":
        return {
            "query": q,
            "source": "local_hybrid_rag",
            "error": "Local hybrid RAG adapter not wired in MCP yet. Use backend='vertex' for now.",
            "results": [],
        }

    raise ValueError("backend must be 'vertex' or 'local'")


@mcp.tool(
    name="bifrost.chat",
    description=(
        "Call Bifrost /v1/chat/completions with allowlisted models and strict caps. "
        "Returns the full JSON response plus a best-effort assistant_text field."
    ),
)
def bifrost_chat(
    messages_json: str,
    model: str | None = None,
    max_tokens: int = 800,
    temperature: float = 0.2,
) -> dict[str, Any]:
    try:
        messages = json.loads(messages_json)
    except Exception as e:
        raise ValueError(f"messages_json must be valid JSON: {e}") from e
    if not isinstance(messages, list):
        raise ValueError("messages_json must decode to a JSON list of messages")

    chosen_model = (model or "").strip() or _env("BIFROST_MODEL", "openai/gpt-5.2-2025-12-11")
    resp = _bifrost_chat_completions(
        model=chosen_model,
        messages=[m for m in messages if isinstance(m, dict)],
        max_tokens=max(1, min(4000, int(max_tokens))),
        temperature=float(temperature),
    )
    assistant_text = ""
    try:
        assistant_text = resp["choices"][0]["message"]["content"]
    except Exception:
        assistant_text = ""
    return {"model": chosen_model, "assistant_text": assistant_text, "response": resp}


@mcp.tool(
    name="langgraph.assistants.search",
    description=(
        "Search assistants in the local LangGraph API "
        "(e.g., find assistant_id UUID for graph_id/name)."
    ),
)
def langgraph_assistants_search(
    graph_id: str | None = None,
    name: str | None = None,
    limit: int = 10,
    offset: int = 0,
) -> dict[str, Any]:
    base = _langgraph_base_url()
    payload: dict[str, Any] = {
        "limit": max(1, min(100, int(limit))),
        "offset": max(0, int(offset)),
    }
    if graph_id:
        payload["graph_id"] = str(graph_id)
    if name:
        payload["name"] = str(name)
    return _as_dict(_http_json("POST", f"{base}/assistants/search", payload), list_key="assistants")


@mcp.tool(
    name="langgraph.threads.create",
    description="Create a thread in the local LangGraph API (stateful runs).",
)
def langgraph_threads_create(
    thread_id: str | None = None, metadata_json: str | None = None
) -> dict[str, Any]:
    base = _langgraph_base_url()
    payload: dict[str, Any] = {}
    if thread_id:
        payload["thread_id"] = str(thread_id)
    if metadata_json:
        meta = json.loads(metadata_json)
        if not isinstance(meta, dict):
            raise ValueError("metadata_json must decode to a JSON object")
        payload["metadata"] = meta
    return _http_json("POST", f"{base}/threads", payload)


@mcp.tool(
    name="langgraph.runs.create",
    description="Create a stateless run in the local LangGraph API (POST /runs).",
)
def langgraph_runs_create(
    assistant_id: str,
    input_json: str,
    config_json: str | None = None,
) -> dict[str, Any]:
    base = _langgraph_base_url()
    payload: dict[str, Any] = {"assistant_id": str(assistant_id)}
    inp = json.loads(input_json)
    payload["input"] = inp
    if config_json:
        cfg = json.loads(config_json)
        if not isinstance(cfg, dict):
            raise ValueError("config_json must decode to a JSON object")
        payload["config"] = cfg
    return _as_dict(_http_json("POST", f"{base}/runs", payload))


@mcp.tool(
    name="langgraph.runs.wait",
    description="Create a stateless run and wait for final output (POST /runs/wait).",
)
def langgraph_runs_wait(
    assistant_id: str,
    input_json: str,
    config_json: str | None = None,
) -> dict[str, Any]:
    base = _langgraph_base_url()
    payload: dict[str, Any] = {"assistant_id": str(assistant_id), "input": json.loads(input_json)}
    if config_json:
        cfg = json.loads(config_json)
        if not isinstance(cfg, dict):
            raise ValueError("config_json must decode to a JSON object")
        payload["config"] = cfg
    return _as_dict(_http_json("POST", f"{base}/runs/wait", payload))


@mcp.tool(
    name="langgraph.thread_runs.create",
    description=(
        "Create a stateful run in the local LangGraph API (POST /threads/{thread_id}/runs)."
    ),
)
def langgraph_thread_runs_create(
    thread_id: str,
    assistant_id: str,
    input_json: str,
    config_json: str | None = None,
) -> dict[str, Any]:
    base = _langgraph_base_url()
    payload: dict[str, Any] = {"assistant_id": str(assistant_id), "input": json.loads(input_json)}
    if config_json:
        cfg = json.loads(config_json)
        if not isinstance(cfg, dict):
            raise ValueError("config_json must decode to a JSON object")
        payload["config"] = cfg
    return _as_dict(_http_json("POST", f"{base}/threads/{thread_id}/runs", payload))


@mcp.tool(
    name="langgraph.thread_runs.wait",
    description=(
        "Create a stateful run and wait for final output (POST /threads/{thread_id}/runs/wait)."
    ),
)
def langgraph_thread_runs_wait(
    thread_id: str,
    assistant_id: str,
    input_json: str,
    config_json: str | None = None,
) -> dict[str, Any]:
    base = _langgraph_base_url()
    payload: dict[str, Any] = {"assistant_id": str(assistant_id), "input": json.loads(input_json)}
    if config_json:
        cfg = json.loads(config_json)
        if not isinstance(cfg, dict):
            raise ValueError("config_json must decode to a JSON object")
        payload["config"] = cfg
    return _as_dict(_http_json("POST", f"{base}/threads/{thread_id}/runs/wait", payload))


@mcp.tool(
    name="langgraph.thread_runs.get",
    description="Get run status/result in a thread (GET /threads/{thread_id}/runs/{run_id}).",
)
def langgraph_thread_runs_get(thread_id: str, run_id: str) -> dict[str, Any]:
    base = _langgraph_base_url()
    return _as_dict(_http_json("GET", f"{base}/threads/{thread_id}/runs/{run_id}", None))


@mcp.tool(
    name="langgraph.thread_runs.list",
    description="List runs in a thread (GET /threads/{thread_id}/runs).",
)
def langgraph_thread_runs_list(
    thread_id: str,
    *,
    limit: int = 20,
    offset: int = 0,
) -> dict[str, Any]:
    base = _langgraph_base_url()
    q_limit = max(1, min(100, int(limit)))
    q_offset = max(0, int(offset))
    url = f"{base}/threads/{thread_id}/runs?limit={q_limit}&offset={q_offset}"
    return _as_dict(_http_json("GET", url, None), list_key="runs")


if __name__ == "__main__":
    # Use stdio for maximum compatibility with local clients (Codex, Gemini CLI, etc.).
    mcp.run("stdio")
