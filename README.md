# Remote Weather MCP Server

A minimal MCP server with 2 tools, backed by [wttr.in](https://wttr.in/)
(free, no API key, no signup required, single call per tool).

## Tools

- `get_current_weather(city: str) -> dict`
  Returns `{city, temperature_c, wind_kph, condition}`.
- `get_forecast(city: str, days: int = 3) -> dict`
  Returns `{city, forecast: [{date, temp_max_c, temp_min_c, condition}, ...]}` (1-3 days).

## Run locally

```
uv sync
uv run python src/remote_mcp_server/main.py
```

Server listens on `http://0.0.0.0:8000/mcp` (streamable HTTP transport).

## Test it

```
uv run python -c "
import asyncio
from fastmcp import Client

async def main():
    async with Client('http://127.0.0.1:8000/mcp') as client:
        print(await client.call_tool('get_current_weather', {'city': 'London'}))

asyncio.run(main())
"
```

## Deploy on Render

1. Push this repo to GitHub.
2. Render dashboard -> New -> Web Service -> connect the repo (root directory: `Remote_MCP_Server`).
3. Build command: `uv sync`
4. Start command: `uv run python src/remote_mcp_server/main.py`
5. No environment variables needed. Render sets `$PORT` automatically; the server already reads it.

Render gives you a public URL like `https://<name>.onrender.com`.

## Verify the deployment

```
curl -i https://<name>.onrender.com/mcp
```

A `400`/protocol-error response is fine for a bare GET (the endpoint expects a JSON-RPC
POST) — it just confirms the server is up and reachable. To actually exercise the tools,
point an MCP client at `https://<name>.onrender.com/mcp` (same as the local test above,
just swap the URL) and call `get_current_weather` / `get_forecast`.

Note: Render's free tier sleeps after idle periods — the first request after a sleep
will be slow (cold start). That's expected.
