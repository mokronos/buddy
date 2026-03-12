# Module Map

## Workspace packages

- `packages/buddy-control-plane`
  - FastAPI control plane
  - agent lifecycle management (managed/external)
  - session listing/details API
  - A2A proxy routes for managed/external agents

- `packages/buddy-runtime`
  - reusable runtime process for one configured agent
  - A2A server wrapper and executor
  - tool wiring (`todo`, `web_search`, optional MCP streamable HTTP toolset)

- `packages/buddy-shared`
  - runtime config schema and YAML parsing
  - shared structured logging helpers
  - shared data-dir resolution
  - SQLite-backed `SessionStore`

## Top-level package (`src/buddy`)

- `cli.py`
  - `buddy server` / `buddy dev`
  - `buddy chat` / `buddy ask`

## Frontend (`app/`)

- SolidStart app with routes:
  - `/` chat UI
  - `/managed-agents` control-plane admin UI
  - `/agent-logs` managed-agent logs UI
- A2A wrappers in `app/src/a2a/`
- Generated OpenAPI client in `app/src/buddy-client/`
