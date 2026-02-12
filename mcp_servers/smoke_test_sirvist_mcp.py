from __future__ import annotations

import sys
from pathlib import Path

import anyio
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


def _repo_root() -> Path:
    here = Path(__file__).resolve()
    for p in [here, *here.parents]:
        if (p / ".git").exists():
            return p
    raise RuntimeError(f"Could not locate repo root from: {here}")


async def _run() -> int:
    repo_root = _repo_root()
    server_path = repo_root / "03_dev_tools/mcp/sirvist_mcp_server.py"
    if not server_path.exists():
        raise FileNotFoundError(str(server_path))

    server_params = StdioServerParameters(command=sys.executable, args=[str(server_path)], env={})
    async with (
        stdio_client(server_params) as (read_stream, write_stream),
        ClientSession(read_stream, write_stream) as session,
    ):
        await session.initialize()
        tools_result = await session.list_tools()

    tool_names = [t.name for t in tools_result.tools]
    print("ok: initialize + tools/list")
    print("tools:", ", ".join(tool_names))
    return 0


def main() -> int:
    return anyio.run(_run, backend="asyncio")


if __name__ == "__main__":
    raise SystemExit(main())
