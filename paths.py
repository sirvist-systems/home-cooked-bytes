from __future__ import annotations

from pathlib import Path


def repo_root() -> Path:
    here = Path(__file__).resolve()
    for candidate in [here, *here.parents]:
        if (candidate / ".git").exists():
            return candidate
    raise RuntimeError(f"Could not locate repo root from: {here}")


def path(*parts: str) -> Path:
    return repo_root().joinpath(*parts)


def env_example_path() -> Path:
    return path(".env.example")


def env_path() -> Path:
    return path(".env")


def mcp_servers_dir() -> Path:
    return path("mcp_servers")


def infra_dir() -> Path:
    return path("infra")


def bifrost_allowlists_dir() -> Path:
    return path("infra", "bifrost", "allowlists")


def docs_dir() -> Path:
    return path("docs")
