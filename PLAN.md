# Plan: Basic 2-Tool Weather MCP Server (Remote, Render-deployed)

## What changes
`main.py` currently holds an expense tracker (4 tools + 1 resource, sqlite). This plan
**replaces it entirely** with a minimal, dependency-light server: 2 tools, no database,
no local state — same spirit as `Local_File_MCP`, just not file-based.

## API choice: Open-Meteo
Picked because it's the most "standard, never-hard-to-setup, always-up" public API:
no signup, no API key, no rate-limit auth, free forever, high uptime. Two calls:
geocoding (city name -> lat/lon) and forecast (lat/lon -> weather).

## The 2 tools
1. **`get_current_weather(city: str) -> dict`**
   Geocodes `city`, returns `{city, temperature_c, wind_kph, condition}`.
2. **`get_forecast(city: str, days: int = 3) -> dict`**
   Geocodes `city`, returns `{city, forecast: [{date, temp_max_c, temp_min_c, condition}, ...]}`
   (`days` capped at 7).

Both trim the raw API JSON down to just these fields — keeps responses (and token usage) small.

## Tech
- Keep `fastmcp`, add `httpx` (for the two GET calls), **drop `aiosqlite`**.
- Transport: `mcp.run(transport="http", host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))`
  — Render assigns `$PORT` at runtime, so this must read the env var, not hardcode 8000.
- No secrets, no `.env` needed.

## Phase-wise rollout

**Phase 1 — Build & test locally**
- Rewrite `main.py` with the 2 tools above.
- Update `pyproject.toml` deps.
- Run: `uv run python src/remote_mcp_server/main.py`
- Sanity-check both tools return real data for a known city before touching deployment.

**Phase 2 — Prepare for Render**
- Confirm host/port binding reads `$PORT` (above).
- Commit + push to a GitHub repo (Render deploys from GitHub).

**Phase 3 — Deploy on Render**
- New "Web Service" on Render → connect the repo → root directory `Remote_MCP_Server`.
- Build command: `uv sync`
- Start command: `uv run python src/remote_mcp_server/main.py`
- No environment variables required.
- Render gives a public HTTPS URL, e.g. `https://<name>.onrender.com`.

**Phase 4 — Verify it's actually running**
- `curl` the deployed URL's MCP endpoint and confirm a valid (non-error) response.
- Point an MCP client (e.g. VS Code `mcp.json`, `"type": "http"`, `"url": "https://<name>.onrender.com/mcp"`) at it and call both tools once each.
- Note: Render's free tier sleeps on idle — first request after idle will be slow (cold start). Expected, not a bug.

## Files touched
- `src/remote_mcp_server/main.py` — rewritten (2 tools only)
- `pyproject.toml` — deps updated (add `httpx`, remove `aiosqlite`)
- `README.md` — what it does, how to run locally, how it's deployed

## Confirm before I build
- OK to fully discard the current expense-tracker code?
- OK with Open-Meteo (weather) as the pick?
