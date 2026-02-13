# MCP Dependencies (Reproducible)

This repo treats MCP server Python dependencies as infrastructure: **install reproducibly**.

## Files

- `requirements-mcp.txt`: human-edited, minimal direct dependencies
- `requirements-mcp.lock.txt`: fully pinned lock (generated)

## Install (recommended)

```bash
cd /home/sirvist-lab/src/home-cooked-bytes

uv venv --python 3.12 .venv
uv pip sync --python .venv/bin/python requirements-mcp.lock.txt
```

## Update the lock

After changing `requirements-mcp.txt`:

```bash
cd /home/sirvist-lab/src/home-cooked-bytes

uv pip install --python .venv/bin/python -r requirements-mcp.txt
uv pip freeze --python .venv/bin/python > requirements-mcp.lock.txt
```

Then re-sync to ensure the environment exactly matches the lock:

```bash
uv pip sync --python .venv/bin/python requirements-mcp.lock.txt
```
