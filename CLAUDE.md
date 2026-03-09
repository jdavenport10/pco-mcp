# CLAUDE.md

## Project Overview

PCO MCP Server — a FastMCP server that exposes Planning Center Online (PCO) API operations as MCP tools. Runs as an HTTP server with per-user OAuth authentication. 127 tools across 5 PCO products.

## Architecture

- `server.py` — Entrypoint. Auth (OAuth proxy + token verifier), MCP app instance, shared helpers (`_build_patch_body`, `get_pco`), imports all tool modules.
- `services.py` — PCO Services API tools (`/services/v2`): service types, plans, plan times, plan items, team members, schedules, songs, tags. (33 tools)
- `registrations.py` — PCO Registrations API tools (`/registrations/v2`): events, categories, event times, attendees, event duplication. (19 tools)
- `giving.py` — PCO Giving API tools (`/giving/v2`): funds, batches, donations, designations, payment sources, donors. (22 tools)
- `calendar_events.py` — PCO Calendar API tools (`/calendar/v2`): events, event instances, resources, tags, feeds, conflicts. (19 tools)
- `people.py` — PCO People API tools (`/people/v2`): people CRUD + search, emails, phone numbers, addresses, households, lists, notes, campuses, custom fields. (34 tools)

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

## Research Process for New PCO API Modules

Before writing a new module, research the target PCO API product using the official developer docs at `https://developer.planning.center/docs/#/apps/<product>` (e.g., `/people`, `/check-ins`, `/groups`). The goal is to map out all endpoints before writing any code.

### What to research

For each PCO product, identify:

1. **Resource types** — The primary nouns (e.g., `Person`, `Household`, `List`). Each becomes a section in the module.
2. **CRUD endpoints** — Standard REST paths: `GET /product/v2/resources`, `GET /:id`, `POST`, `PATCH /:id`, `DELETE /:id`. Also note nested paths like `GET /people/v2/people/:id/emails`.
3. **Writable attributes** — Distinguish read/write from read-only attributes. Only writable ones belong in `create_*` and `update_*` tool parameters.
4. **Relationship POSTs** — Some resources are created via nested paths (e.g., emails under a person) and require a relationship block in the body rather than using `pco.template()`.
5. **Filter/search params** — PCO uses `where[field]=value` query params for filtering. Expose the most useful ones (name search, status, date ranges) as optional tool parameters.
6. **Include params** — PCO supports `?include=related_resource` to sideload related data in one request. Use these in "get single" tools to avoid extra round trips.
7. **OAuth scope** — Confirm the scope string needed (e.g., `people`, `check-ins`). Check `app.py`'s `extra_authorize_params` — the scope may already be present.

### Module structure

Organise tools into clearly labelled sections, one per resource type:

```python
# =============================================================================
# Person Operations
# =============================================================================

# =============================================================================
# Email Operations
# =============================================================================
```

### Type annotation rules

FastMCP generates JSON Schemas from Python type hints at decoration time. Incorrect annotations cause tools to be silently dropped — no startup error, just missing tools.

| Pattern | Do this | Not this |
|---|---|---|
| Optional string param | `name: str = None` | `name: Optional[str] = None` |
| List param | `ids: list[str]` | `ids: list` (bare — generates invalid schema) |
| List return | `-> list:` | fine as-is |
| Unused imports | remove them | leave them in |

### POST body patterns

**Simple create** (attributes only) — use `pco.template()`:
```python
body = pco.template("Person", {"first_name": first_name, "last_name": last_name})
response = await asyncio.to_thread(pco.post, "/people/v2/people", body)
```

**Create with relationships** (e.g., nested resources, household members) — build manually:
```python
body = {
    "data": {
        "type": "Household",
        "attributes": {"name": name},
        "relationships": {
            "primary_contact": {"data": {"type": "Person", "id": primary_contact_id}},
            "people": {"data": [{"type": "Person", "id": pid} for pid in people_ids]},
        },
    }
}
```

**Create via nested path** (e.g., adding an email to a person):
```python
body = pco.template("Email", {"address": address, "location": location})
response = await asyncio.to_thread(pco.post, f"/people/v2/people/{person_id}/emails", body)
```

### Checklist before opening a PR

- [ ] No bare `list` type hints on parameters — always use `list[str]` or similar
- [ ] No unused imports
- [ ] Module added to `import` block in `server.py`
- [ ] Module filename added to `COPY` line in `Dockerfile`
- [ ] Tool count in this file's "Project Overview" updated
- [ ] Module summary added to the "Architecture" section
- [ ] Rebuilt with `docker compose down && docker compose up --build` and confirmed tools appear

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

**Common gotcha — stale image:** If tools from a newly added module are missing but the server starts cleanly, the Docker image was likely not rebuilt. Always use `--build`. Running `docker compose up` without `--build` reuses the cached image and will not include new files.

## Dependencies

- `fastmcp` — MCP server framework with OAuth support
- `pypco` — Planning Center API client
- `httpx` — Async HTTP for token verification
- `python-dotenv` — Environment variable loading
