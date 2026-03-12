# buddy

Buddy is an autonomous assistant platform with a control-plane server, containerized agent runtimes, and multiple clients (CLI + web UI).

## What is in this repository

- `packages/buddy-control-plane`: FastAPI control plane for agent management, session APIs, and A2A proxying.
- `packages/buddy-runtime`: Reusable runtime that loads YAML config, builds a `pydantic_ai.Agent`, and serves A2A.
- `packages/buddy-shared`: Shared runtime config schema, logging helpers, data-dir helpers, and SQLite `SessionStore`.
- `app/`: SolidStart frontend for chat, managed/external agent admin, and agent logs.
- `src/buddy/cli.py`: CLI commands (`buddy server`, `buddy dev`, `buddy chat`, `buddy ask`).

## Current architecture

- Control plane exposes domain endpoints under `/agents` and `/sessions`.
- A2A traffic stays at the boundary and is proxied through:
  - `/a2a/managed/{agent_id}`
  - `/a2a/external/{agent_id}`
- Managed agents run as Docker containers from one reusable runtime image (`buddy-agent-runtime`).
- External agents are registered by base URL and proxied by the control plane.
- Sessions, messages, events, and todo state persist in SQLite via `SessionStore`.

## Quick start

### 1) Install dependencies

```bash
uv sync
```

### 2) Run the control plane

```bash
uv run buddy server
```

For auto-reload:

```bash
uv run buddy dev
```

### 3) Run the web client

```bash
cd app
bun install
bun run dev
```

### 4) Use the CLI client

```bash
uv run buddy chat
# or
uv run buddy ask "hello"
```

## Agent runtime container

Build the reusable runtime image:

```bash
docker build -f Dockerfile.agent-runtime -t buddy-agent-runtime:latest .
```

Managed-agent creation in the control plane expects this image tag by default.

## Data and configuration

- Default Buddy data directory: `~/.local/share/buddy`
- Override with:
  - `BUDDY_DATA_DIR`
  - `XDG_DATA_HOME`
- Useful server/runtime env vars:
  - `BUDDY_PUBLIC_URL`
  - `BUDDY_ALLOW_PRIVATE_EXTERNAL_URLS`
  - `BUDDY_AGENT_CONFIG` (required inside runtime container)
  - `BUDDY_REQUIRE_LANGFUSE`, `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`

## Frontend OpenAPI client generation

Generated client code lives in `app/src/buddy-client` and is configured by `openapi-ts.config.ts`.

```bash
bunx openapi-ts
```
