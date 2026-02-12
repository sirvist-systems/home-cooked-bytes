#!/usr/bin/env python3
from __future__ import annotations

import json
import os
from typing import Any, Literal

import httpx
from fastmcp import FastMCP

mcp = FastMCP("openapi-local")

_OPENAPI_CACHE: dict[str, Any] | None = None
_OPENAPI_SOURCE: str | None = None


def _default_source() -> str:
    return os.getenv("SIRVIST_OPENAPI_SOURCE", "http://localhost:8001/openapi.json")


def _load_openapi_from_source(source: str) -> dict[str, Any]:
    source = source.strip()
    if not source:
        raise ValueError("source must be non-empty")

    if source.startswith("http://") or source.startswith("https://"):
        with httpx.Client(timeout=30.0) as client:
            resp = client.get(source)
            resp.raise_for_status()
            # Prevent runaway payloads.
            body = resp.content
            if len(body) > 2_000_000:
                raise RuntimeError(f"OpenAPI payload too large: {len(body)} bytes (cap: 2,000,000)")
            return resp.json()

    # Treat everything else as a local path.
    with open(source, "rb") as f:
        body = f.read(2_000_001)
    if len(body) > 2_000_000:
        raise RuntimeError(f"OpenAPI payload too large: {len(body)} bytes (cap: 2,000,000)")
    return json.loads(body.decode("utf-8"))


def _ensure_loaded(source: str | None = None) -> dict[str, Any]:
    global _OPENAPI_CACHE, _OPENAPI_SOURCE
    src = (source or _default_source()).strip()
    if _OPENAPI_CACHE is None or src != _OPENAPI_SOURCE:
        _OPENAPI_CACHE = _load_openapi_from_source(src)
        _OPENAPI_SOURCE = src
    return _OPENAPI_CACHE


def _iter_operations(spec: dict[str, Any]) -> list[dict[str, Any]]:
    ops: list[dict[str, Any]] = []
    for path, path_item in (spec.get("paths") or {}).items():
        if not isinstance(path_item, dict):
            continue
        for method, operation in path_item.items():
            if method.lower() not in {"get", "post", "put", "patch", "delete", "head", "options"}:
                continue
            if not isinstance(operation, dict):
                continue
            ops.append(
                {
                    "method": method.lower(),
                    "path": path,
                    "operationId": operation.get("operationId"),
                    "summary": operation.get("summary"),
                    "tags": operation.get("tags") or [],
                    "deprecated": bool(operation.get("deprecated") or False),
                }
            )
    return ops


@mcp.tool()
def openapi_reload(*, source: str | None = None) -> dict[str, Any]:
    """
    Reload OpenAPI JSON from a URL or local file path.

    Default source can be set via env `SIRVIST_OPENAPI_SOURCE`.
    """
    global _OPENAPI_CACHE, _OPENAPI_SOURCE
    _OPENAPI_CACHE = None
    _OPENAPI_SOURCE = None
    spec = _ensure_loaded(source)
    return {
        "source": _OPENAPI_SOURCE,
        "openapi": spec.get("openapi"),
        "title": ((spec.get("info") or {}).get("title")),
        "version": ((spec.get("info") or {}).get("version")),
        "paths": len((spec.get("paths") or {}).keys()),
    }


@mcp.tool()
def openapi_list_endpoints(
    *,
    source: str | None = None,
    contains: str | None = None,
    method: str | None = None,
    limit: int = 50,
) -> dict[str, Any]:
    """List endpoints from a local OpenAPI schema (bounded output)."""
    spec = _ensure_loaded(source)
    ops = _iter_operations(spec)

    if method:
        m = method.strip().lower()
        ops = [o for o in ops if o["method"] == m]
    if contains:
        needle = contains.strip().lower()
        if needle:
            ops = [
                o
                for o in ops
                if needle in (o.get("path") or "").lower()
                or needle in (o.get("operationId") or "").lower()
                or needle in (o.get("summary") or "").lower()
            ]

    limit = max(1, min(int(limit), 200))
    return {"source": _OPENAPI_SOURCE, "count": len(ops), "items": ops[:limit]}


@mcp.tool()
def openapi_get_operation(
    path: str,
    method: Literal["get", "post", "put", "patch", "delete", "head", "options"],
    *,
    source: str | None = None,
) -> dict[str, Any]:
    """Get a single operation (summary/tags/params/requestBody/responses) from OpenAPI."""
    spec = _ensure_loaded(source)
    path_item = (spec.get("paths") or {}).get(path)
    if not isinstance(path_item, dict):
        raise KeyError(f"Path not found: {path}")

    op = path_item.get(method)
    if not isinstance(op, dict):
        raise KeyError(f"Operation not found: {method.upper()} {path}")

    # Keep output compact; return schema refs/keys rather than full resolved schemas.
    return {
        "source": _OPENAPI_SOURCE,
        "method": method,
        "path": path,
        "operationId": op.get("operationId"),
        "summary": op.get("summary"),
        "description": op.get("description"),
        "tags": op.get("tags") or [],
        "parameters": op.get("parameters") or [],
        "requestBody": op.get("requestBody"),
        "responses": op.get("responses") or {},
        "security": op.get("security"),
    }


if __name__ == "__main__":
    mcp.run()
