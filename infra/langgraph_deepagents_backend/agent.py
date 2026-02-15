from __future__ import annotations

import html
import json
import os
import re
import subprocess
import urllib.error
import urllib.request
import uuid
from pathlib import Path

from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict


class State(TypedDict, total=False):
    messages: list[dict]
    bifrost_model: str


_TAG_RE = re.compile(r"<[^>]+>")


def _extract_text(content: object) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if not isinstance(block, dict):
                continue
            if "text" in block:
                parts.append(str(block.get("text", "")))
            elif "content" in block:
                parts.append(str(block.get("content", "")))
        return "\n".join([p for p in parts if p])
    if isinstance(content, dict):
        if "text" in content:
            return str(content.get("text", ""))
        if "content" in content:
            return str(content.get("content", ""))
    return str(content)


def _to_openai_messages(messages: list[dict]) -> list[dict]:
    out: list[dict] = []
    for msg in messages:
        if not isinstance(msg, dict):
            continue
        role = msg.get("role")
        msg_type = msg.get("type")
        content = _extract_text(msg.get("content"))

        # Normalize common non-OpenAI role aliases.
        if role == "human":
            role = "user"
        elif role == "ai":
            role = "assistant"

        if not role:
            if msg_type == "human":
                role = "user"
            elif msg_type == "ai":
                role = "assistant"
            elif msg_type == "system":
                role = "system"
            else:
                role = "user"

        out.append({"role": role, "content": content})
    return out


def _append_ai_message(messages: list[dict], text: str) -> list[dict]:
    messages = list(messages)
    messages.append(
        {
            "id": str(uuid.uuid4()),
            "type": "ai",
            "content": text,
        }
    )
    return messages


def _clean_snippet(snippet: str) -> str:
    s = (snippet or "").strip()
    s = html.unescape(s)
    s = _TAG_RE.sub("", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _agents_active_dir() -> Path | None:
    """
    Locate the current agent set so the backend can load role specs.

    Docker note: the `langgraph_deepagents_backend` service only mounts `/app` by default.
    For Gate 5 agent runs, mount `./agents` into the container (e.g. `/repo/agents:ro`).
    """
    env_dir = (os.getenv("SIRVIST_AGENTS_ACTIVE_DIR") or "").strip()
    if env_dir:
        p = Path(env_dir)
        if p.is_dir():
            return p

    # Prefer a curated “ready” set (rebuilt agents) over the legacy pool.
    for docker_default in (Path("/repo/agents/ready"), Path("/repo/agents/legacy_agents")):
        if docker_default.is_dir():
            return docker_default

    here = Path(__file__).resolve()
    for d in [here.parent, *here.parents]:
        for candidate in (d / "agents" / "ready", d / "agents" / "legacy_agents"):
            if candidate.is_dir():
                return candidate

    return None


def _list_agent_specs() -> list[str]:
    active = _agents_active_dir()
    if not active:
        return []
    # Prefer compiled specs if present (more consistent runtime behavior).
    # Keep separate compiled folders per active-dir name so we can have:
    # - agents/legacy_agents + agents/legacy_agents_compiled (legacy pool)
    # - agents/ready         + agents/ready_compiled (current pool)
    compiled_name = "ready_compiled" if active.name == "ready" else f"{active.name}_compiled"
    compiled = active.parent / compiled_name
    if compiled.is_dir():
        names = sorted(
            [
                p.stem
                for p in compiled.glob("*.json")
                if p.name not in {"manifest.json", "README.json"}
            ]
        )
        if names:
            return names
    return sorted([p.stem for p in active.glob("*.md")])


def _read_agent_spec(name: str) -> tuple[str, str] | None:
    """
    Returns (resolved_name, spec_text) or None if not found.
    Matching is case-insensitive against the filename stem.
    """
    candidates = _list_agent_specs()
    if not candidates:
        return None
    lookup = {c.lower(): c for c in candidates}
    resolved = lookup.get((name or "").strip().lower())
    if not resolved:
        return None
    active = _agents_active_dir()
    if not active:
        return None
    # Prefer compiled spec JSON if present.
    compiled_name = "ready_compiled" if active.name == "ready" else f"{active.name}_compiled"
    compiled = active.parent / compiled_name / f"{resolved}.json"
    if compiled.is_file():
        try:
            return resolved, compiled.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return None

    path = active / f"{resolved}.md"
    try:
        return resolved, path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return None


def _extract_system_prompt_from_agent_md(text: str) -> str:
    """
    Heuristic extractor:
    - If the agent file has a '## System Prompt' section with a fenced code block, use that block.
    - Otherwise, fall back to a bounded excerpt of the full markdown.
    """
    raw = (text or "").replace("\r\n", "\n").replace("\r", "\n")

    # Compiled agents are JSON with a `system_prompt` field.
    try:
        obj = json.loads(raw)
        if isinstance(obj, dict) and isinstance(obj.get("system_prompt"), str):
            return str(obj.get("system_prompt") or "").strip()
    except Exception:
        pass

    s = raw

    # Find "## System Prompt" then the next fenced block.
    m = re.search(r"(?im)^##\\s+System\\s+Prompt\\s*$", s)
    if m:
        tail = s[m.end() :]
        fence = re.search(r"```\\s*\\n(.*?)\\n```", tail, re.DOTALL)
        if fence:
            return fence.group(1).strip()

    max_chars = int(
        (os.getenv("SIRVIST_AGENT_SYSTEM_PROMPT_MAX_CHARS") or "12000").strip() or "12000"
    )
    if max_chars > 0 and len(s) > max_chars:
        return s[:max_chars].rstrip() + "\n\n...(truncated)...\n"
    return s.strip()


def _requires_max_completion_tokens(model_id: str) -> bool:
    mid = (model_id or "").lower()
    # Matches the same family used elsewhere in-repo: gpt-5* and o-series.
    return mid.startswith(
        ("openai/gpt-5", "openai/o1", "openai/o3", "openai/o4", "gpt-5", "o1", "o3", "o4")
    )


def _rewrite_versioned_openai_model(model: str) -> str:
    """
    Enforce repo policy: use versioned OpenAI model ids (VK allowlists can block aliases).
    """
    raw = (model or "").strip()
    if not raw:
        return raw
    if raw in {"openai/gpt-5.2", "gpt-5.2"}:
        return "openai/gpt-5.2-2025-12-11"
    if raw in {"openai/gpt-5-mini", "gpt-5-mini"}:
        return "openai/gpt-5-mini-2025-08-07"
    if raw in {"openai/gpt-5-nano", "gpt-5-nano"}:
        return "openai/gpt-5-nano-2025-08-07"
    return raw


def _get_vertex_access_token() -> str:
    token = (
        os.getenv("SIRVIST_VERTEX_ACCESS_TOKEN") or os.getenv("VERTEX_ACCESS_TOKEN") or ""
    ).strip()
    if token:
        return token
    return subprocess.check_output(
        ["gcloud", "auth", "application-default", "print-access-token"],
        text=True,
    ).strip()


def _vertex_patent_rag_packet(
    query: str,
    *,
    datastore_id: str,
    max_results: int | None = None,
    max_snippet_chars: int | None = None,
    max_packet_chars: int | None = None,
) -> dict:
    """
    Local-only MVP: call Vertex AI Search (Discovery Engine) REST and return a bounded
    evidence packet.

    This deliberately avoids any vendor SDK imports in repo code: we call REST with an
    ADC access token.
    """
    project = (os.getenv("SIRVIST_VERTEX_PROJECT_ID") or "").strip() or (
        os.getenv("GOOGLE_CLOUD_PROJECT") or ""
    ).strip()
    location = (
        (os.getenv("SIRVIST_VERTEX_LOCATION") or "").strip()
        or (os.getenv("GOOGLE_CLOUD_LOCATION") or "").strip()
        or "global"
    )
    collection = (os.getenv("SIRVIST_VERTEX_COLLECTION") or "default_collection").strip()
    serving_config = (os.getenv("SIRVIST_VERTEX_SERVING_CONFIG") or "default_search").strip()
    datastore = (datastore_id or "").strip()
    if not project or not datastore:
        return {
            "error": (
                "Vertex patent RAG not configured. Set SIRVIST_VERTEX_PROJECT_ID and the "
                "appropriate datastore id."
            )
        }

    max_results = (
        int(max_results)
        if max_results is not None
        else int(os.getenv("SIRVIST_PATENT_RAG_MAX_RESULTS") or "5")
    )
    max_snippet_chars = (
        int(max_snippet_chars)
        if max_snippet_chars is not None
        else int(os.getenv("SIRVIST_PATENT_RAG_MAX_SNIPPET_CHARS") or "900")
    )
    max_packet_chars = (
        int(max_packet_chars)
        if max_packet_chars is not None
        else int(os.getenv("SIRVIST_PATENT_RAG_MAX_PACKET_CHARS") or "8000")
    )

    url = (
        f"https://discoveryengine.googleapis.com/v1/projects/{project}"
        f"/locations/{location}/collections/{collection}"
        f"/dataStores/{datastore}/servingConfigs/{serving_config}:search"
    )
    body = {
        "query": query,
        "pageSize": max(1, min(20, max_results)),
        "contentSearchSpec": {"snippetSpec": {"returnSnippet": True}},
    }
    token = _get_vertex_access_token()
    req = urllib.request.Request(
        url=url,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "content-type": "application/json",
            "authorization": f"Bearer {token}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = json.loads(resp.read().decode("utf-8", "replace"))
    except Exception as e:
        return {"error": f"Vertex search failed: {e}"}

    packet: dict = {
        "query": query,
        "source": "vertex_ai_search",
        "datastore_id": datastore,
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
            }
        )

    # Hard cap packet size.
    raw_json = json.dumps(packet, ensure_ascii=False)
    if max_packet_chars > 0 and len(raw_json) > max_packet_chars:
        for r in packet.get("results", []):
            if isinstance(r, dict):
                r["snippet"] = None
        raw_json = json.dumps(packet, ensure_ascii=False)
        if len(raw_json) > max_packet_chars:
            packet["results"] = (packet.get("results") or [])[: max(1, max_results // 2)]

    return packet


def _maybe_inject_patent_rag(messages: list[dict]) -> list[dict]:
    """
    Minimal deterministic RAG hook (no tool calling).

    Commands:
    - `/patent-rag <query>` or `/patent <query>`: search the "drafts" datastore
    - `/patent-provisional <query>`: search the provisional datastore (baseline support)
    - `/patent-rag+ <query>`: same as `/patent-rag` but returns a larger evidence packet
      (more snippets)
    """
    if not messages:
        return messages
    last = messages[-1]
    if not isinstance(last, dict):
        return messages

    role = last.get("role")
    msg_type = last.get("type")
    if role not in {"user", "human"} and msg_type not in {"human"}:
        return messages

    content = _extract_text(last.get("content"))
    raw = content.strip()
    prefix = None
    source = "drafts"
    expanded = False
    for p in ("/patent-rag+ ",):
        if raw.lower().startswith(p):
            prefix = p
            source = "drafts"
            expanded = True
            break
    if not prefix:
        for p in ("/patent-rag ", "/patent "):
            if raw.lower().startswith(p):
                prefix = p
                source = "drafts"
                break
    if not prefix:
        for p in ("/patent-provisional+ ",):
            if raw.lower().startswith(p):
                prefix = p
                source = "provisional"
                expanded = True
                break
    if not prefix and raw.lower().startswith("/patent-provisional "):
        prefix = "/patent-provisional "
        source = "provisional"
    if not prefix:
        return messages

    query = raw[len(prefix) :].strip()
    if not query:
        return messages

    # Replace last message content with the actual query (strip the slash command).
    last2 = dict(last)
    last2["content"] = query

    if source == "provisional":
        datastore_id = (os.getenv("SIRVIST_VERTEX_PROVISIONAL_DATASTORE_ID") or "").strip()
        if not datastore_id:
            datastore_id = (os.getenv("SIRVIST_VERTEX_PATENT_DRAFTS_DATASTORE_ID") or "").strip()
    else:
        datastore_id = (os.getenv("SIRVIST_VERTEX_PATENT_DRAFTS_DATASTORE_ID") or "").strip()

    # Default packet is intentionally small to control costs. For drafting, allow an explicit
    # expanded variant that still stays bounded.
    overrides = {}
    if expanded:
        overrides = {"max_results": 12, "max_snippet_chars": 1600, "max_packet_chars": 24000}

    packet = _vertex_patent_rag_packet(query, datastore_id=datastore_id, **overrides)
    injected = {
        "id": str(uuid.uuid4()),
        "type": "system",
        "content": (
            "You are in PATENT MODE.\n"
            "Use the following evidence packet for precise citations and claim drafting.\n"
            "Do not invent citations; cite only what is in this packet.\n\n"
            f"EVIDENCE_PACKET_JSON:\n{json.dumps(packet, ensure_ascii=False)}"
        ),
    }

    return [*messages[:-1], injected, last2]


def _maybe_inject_agent_role(messages: list[dict]) -> list[dict]:
    """
    Minimal "agent contract" for Gate 5:
    - `/agent list` → returns a local list of the configured agent pool
      (default: `agents/ready/*.md`)
    - `/agent <AgentName> <task...>` → injects the agent's system prompt as a system message
      and replaces the user message with the task.

    This keeps everything local-only and routes model calls through Bifrost.
    """
    if not messages:
        return messages
    last = messages[-1]
    if not isinstance(last, dict):
        return messages
    raw = _extract_text(last.get("content"))
    if not isinstance(raw, str):
        return messages
    raw = raw.strip()
    if not raw.lower().startswith("/agent"):
        return messages

    parts = raw.split(None, 2)
    if len(parts) == 2 and parts[1].lower() == "list":
        names = _list_agent_specs()
        text = "Available agents:\n" + (
            "\n".join(f"- {n}" for n in names) if names else "- (none found)"
        )
        injected = {"id": str(uuid.uuid4()), "type": "system", "content": text}
        last2 = dict(last)
        last2["content"] = "List the available agents you were provided."
        return [*messages[:-1], injected, last2]

    if len(parts) < 3:
        injected = {
            "id": str(uuid.uuid4()),
            "type": "system",
            "content": "Usage: `/agent list` or `/agent <AgentName> <task...>`",
        }
        return [*messages[:-1], injected, last]

    agent_name = parts[1].strip()
    task = parts[2].strip()
    spec = _read_agent_spec(agent_name)
    if not spec:
        injected = {
            "id": str(uuid.uuid4()),
            "type": "system",
            "content": f"Unknown agent: {agent_name!r}. Try `/agent list`.",
        }
        return [*messages[:-1], injected, last]

    resolved, md = spec
    system_prompt = _extract_system_prompt_from_agent_md(md)
    adr_guard = (
        "Repo decision discipline (ADRs):\n"
        "- If you recommend changing repo behavior/stack\n"
        "  (routing layer, models, telemetry posture,\n"
        "  doc governance,\n"
        "  continuity strategy, agent contracts), you MUST request an ADR.\n"
        "- ADRs live under `02_knowledge/adr/`.\n"
        "- For now: include a short ADR stub in an existing JSON field\n"
        "  (e.g. `questions_for_principal`, `open_gaps`,\n"
        "  `notes`) with: title, context, decision, consequences, follow-ups.\n"
    )
    injected = {
        "id": str(uuid.uuid4()),
        "type": "system",
        "content": (
            f"You are now running as agent `{resolved}`.\n\n{adr_guard}"
            f"\nSYSTEM_PROMPT:\n{system_prompt}"
        ),
    }
    last2 = dict(last)
    last2["content"] = task
    return [*messages[:-1], injected, last2]


def _bifrost_chat(state: State, config: object = None) -> State:
    messages = list(state.get("messages", []))
    last_raw = _extract_text(messages[-1].get("content")) if messages else ""
    is_agent_cmd = isinstance(last_raw, str) and last_raw.strip().lower().startswith("/agent")
    messages = _maybe_inject_patent_rag(messages)
    messages = _maybe_inject_agent_role(messages)

    # Repo convention: many scripts use BIFROST_API_KEY as the Bifrost virtual key (x-bf-vk).
    bifrost_vk = (os.getenv("BIFROST_API_KEY") or os.getenv("BIFROST_VK") or "").strip()
    if not bifrost_vk:
        return {
            "messages": _append_ai_message(
                messages,
                "LangGraph backend is up, but Bifrost is not configured.\n\n"
                "Set env `BIFROST_API_KEY` (preferred) or `BIFROST_VK` for the `x-bf-vk` "
                "header, then retry.\n"
                "If running outside Docker, also set `BIFROST_URL` (e.g. http://localhost:8080).",
            )
        }

    bifrost_url = (os.getenv("BIFROST_URL") or "http://bifrost:8080").rstrip("/")
    model_override = (state.get("bifrost_model") or "").strip()
    if not model_override and isinstance(config, dict):
        configurable = config.get("configurable")
        if isinstance(configurable, dict):
            model_override = str(configurable.get("bifrost_model") or "").strip()

    # Default to a model that reliably returns visible `message.content` via our current Bifrost VK.
    model = model_override or os.getenv("BIFROST_MODEL", "openai/gpt-5.2-2025-12-11")
    model = _rewrite_versioned_openai_model(model)

    openai_messages = _to_openai_messages(messages)
    body: dict[str, object] = {"model": model, "messages": openai_messages}
    if is_agent_cmd:
        max_out = int(
            (os.getenv("SIRVIST_AGENT_MAX_COMPLETION_TOKENS") or "2048").strip() or "2048"
        )
        if max_out > 0:
            if _requires_max_completion_tokens(model):
                body["max_completion_tokens"] = max_out
            else:
                body["max_tokens"] = max_out
    req_body = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url=f"{bifrost_url}/v1/chat/completions",
        data=req_body,
        headers={
            "content-type": "application/json",
            "x-bf-vk": bifrost_vk,
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            detail = e.read().decode("utf-8", errors="replace")
        except Exception:
            detail = str(e)
        return {
            "messages": _append_ai_message(
                messages,
                f"Bifrost call failed: HTTP {getattr(e, 'code', 'unknown')}.\n\n"
                f"URL: {bifrost_url}/v1/chat/completions\n"
                f"Model: {model}\n\n"
                f"Details:\n{detail}",
            )
        }
    except Exception as e:
        return {
            "messages": _append_ai_message(
                messages,
                "Bifrost call failed.\n\n"
                f"URL: {bifrost_url}/v1/chat/completions\n"
                f"Model: {model}\n\n"
                f"Error: {e}",
            )
        }

    assistant_text = ""
    try:
        # OpenAI-compatible shape
        assistant_text = data["choices"][0]["message"]["content"]
    except Exception:
        assistant_text = json.dumps(data, indent=2, sort_keys=True)

    return {"messages": _append_ai_message(messages, assistant_text)}


graph = StateGraph(State)
graph.add_node("respond", _bifrost_chat)
graph.add_edge(START, "respond")
graph.add_edge("respond", END)

agent = graph.compile()
