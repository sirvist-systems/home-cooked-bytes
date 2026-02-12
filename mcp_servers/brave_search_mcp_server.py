#!/usr/bin/env python3
from __future__ import annotations

import os
from typing import Any

import httpx
from fastmcp import FastMCP

mcp = FastMCP("brave-search")


def _get_brave_api_key() -> str:
    # Brave Search API uses the X-Subscription-Token header.
    # Accept either env name to reduce friction across setups.
    key = (os.getenv("BRAVE_SEARCH_API_KEY") or os.getenv("BRAVE_API_KEY") or "").strip()
    if not key:
        raise RuntimeError(
            "Missing Brave Search API key. Set BRAVE_SEARCH_API_KEY (preferred) or BRAVE_API_KEY."
        )
    return key


@mcp.tool()
def brave_search_query(
    query: str,
    *,
    count: int = 5,
    country: str | None = None,
    language: str | None = None,
    safesearch: str = "moderate",
) -> dict[str, Any]:
    """
    Search the public internet via Brave Search API.

    Returns:
      - A compact result list (title, url, description)
      - Raw metadata needed for debugging (query, count)

    Notes:
      - This tool intentionally does NOT fetch arbitrary web pages (reduces prompt-injection risk).
      - If you need page content, do a second explicit, user-approved fetch step.
    """
    if not query.strip():
        raise ValueError("query must be non-empty")

    count = max(1, min(int(count), 10))
    safesearch = safesearch.strip().lower()
    if safesearch not in {"off", "moderate", "strict"}:
        raise ValueError("safesearch must be one of: off, moderate, strict")

    headers = {
        "Accept": "application/json",
        "X-Subscription-Token": _get_brave_api_key(),
    }
    params: dict[str, Any] = {
        "q": query,
        "count": count,
        "safesearch": safesearch,
    }
    if country:
        params["country"] = country
    if language:
        params["search_lang"] = language

    with httpx.Client(timeout=30.0) as client:
        resp = client.get(
            "https://api.search.brave.com/res/v1/web/search", headers=headers, params=params
        )
        resp.raise_for_status()
        data = resp.json()

    results: list[dict[str, Any]] = []
    for item in ((data or {}).get("web", {}) or {}).get("results", []) or []:
        if not isinstance(item, dict):
            continue
        results.append(
            {
                "title": item.get("title"),
                "url": item.get("url"),
                "description": item.get("description"),
                "age": item.get("age"),
            }
        )

    return {
        "query": query,
        "count": count,
        "results": results,
        "raw_top_level_keys": sorted((data or {}).keys()),
    }


if __name__ == "__main__":
    mcp.run()
