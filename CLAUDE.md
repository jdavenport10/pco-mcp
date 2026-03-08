# CLAUDE.md

## Project Overview

PCO MCP Server — a FastMCP server that exposes Planning Center Online (PCO) API operations as MCP tools. Runs as an HTTP server with per-user OAuth authentication. 93 tools across 4 PCO products.

## Architecture

- `server.py` — Entrypoint. Auth (OAuth proxy + token verifier), MCP app instance, shared helpers (`_build_patch_body`, `get_pco`), imports all tool modules.
- `services.py` — PCO Services API tools (`/services/v2`): service types, plans, plan times, plan items, team members, schedules, songs, tags.
- `registrations.py` — PCO Registrations API tools (`/registrations/v2`): events, categories, event times, attendees, event duplication.
- `giving.py` — PCO Giving API tools (`/giving/v2`): funds, batches, donations, designations, payment sources, donors.
- `calendar_events.py` — PCO Calendar API tools (`/calendar/v2`): events, event instances, resources, tags, feeds, conflicts.

## Key Patterns

- All tools use `@mcp.tool()` decorator on async functions.
- All PCO API calls are wrapped in `asyncio.to_thread(pco.method, path, ...)` since pypco is synchronous.
- Authentication: `pco: PCO = Depends(get_pco)` dependency injection on every tool.
- POST bodies: use `pco.template("ResourceType", attributes)` for creates.
- PATCH bodies: use `_build_patch_body("ResourceType", **kwargs)` which filters out None values.
- DELETE returns `{"success": True, "message": "..."}`.
- JSON:API 1.0 spec for all request/response payloads.
- OAuth scopes: `services people registrations giving calendar`.

## Running

```bash
# Docker
docker compose up --build

# Local
pip install -r requirements.txt
python server.py
```

Server listens on `0.0.0.0:8000`. Requires `.env` with `PCO_CLIENT_ID`, `PCO_CLIENT_SECRET`, `BASE_URL`, `JWT_SIGNING_KEY`.

## Adding New Tools

1. Create a new file (e.g., `check_ins.py`) importing `mcp`, `get_pco`, `_build_patch_body` from `server.py`.
2. Add `@mcp.tool()` decorated async functions following the existing CRUD patterns.
3. Import the new module in `server.py` alongside the other tool imports.
4. Add the new file to the `COPY` line in `Dockerfile`.
5. Add the PCO product scope to the `extra_authorize_params` in `server.py`.

## Debugging Loop

When troubleshooting issues, follow this cycle until the service is healthy:

1. **Boot** — `docker compose up --build`
2. **Observe** — Watch logs for errors: `docker compose logs -f`
3. **Troubleshoot** — Fix the root cause in source files
4. **Reboot** — `docker compose down && docker compose up --build`
5. **Repeat** until the service starts cleanly and responds correctly

Key things to check in logs:
- Import errors or syntax errors on startup
- Missing environment variables (`.env` must have all 4 required keys)
- PCO API authentication failures (check OAuth scopes and token flow)
- Tool registration errors from FastMCP

## Dependencies

- `fastmcp` — MCP server framework with OAuth support
- `pypco` — Planning Center API client
- `httpx` — Async HTTP for token verification
- `python-dotenv` — Environment variable loading
