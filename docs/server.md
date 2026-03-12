# Server

Control-plane APIs and A2A proxy behavior.

## Overview

Buddy runs a FastAPI control plane (`packages/buddy-control-plane/src/buddy/control_plane/server.py`) with three route modules:

- `routes/sessions.py`
- `routes/agents.py`
- `routes/proxy.py`

The control plane owns:

- managed-agent lifecycle (Docker)
- external-agent registry
- session read APIs
- A2A proxying for managed/external agents

## Domain API surface

Session endpoints:

- `GET /sessions`
- `GET /sessions/{session_id}`

Agent index:

- `GET /agents`

Managed agent endpoints:

- `GET /agents/managed`
- `GET /agents/managed/{agent_id}`
- `POST /agents/managed`
- `POST /agents/managed/{agent_id}/start`
- `POST /agents/managed/{agent_id}/stop`
- `DELETE /agents/managed/{agent_id}`
- `GET /agents/managed/{agent_id}/config`
- `PUT /agents/managed/{agent_id}/config`
- `GET /agents/managed/{agent_id}/logs`

External agent endpoints:

- `GET /agents/external`
- `POST /agents/external`
- `PUT /agents/external/{agent_id}`
- `DELETE /agents/external/{agent_id}`

## A2A boundary

Raw A2A JSON-RPC/SSE is proxied at:

- `/a2a/managed/{agent_id}` (and nested paths)
- `/a2a/external/{agent_id}` (and nested paths)

Agent-card payloads are rewritten so `url` points to the control-plane proxy route.

## Persistence and data locations

- SQLite session DB: `sessions.db` (resolved under Buddy data dir when relative)
- Managed-agent registry: `<buddy_data_dir>/managed_agents.json`
- External-agent registry: `<buddy_data_dir>/external_agents.json`
- Managed-agent YAML config files: `<buddy_data_dir>/agents/{agent_id}/agent.yaml`

Default Buddy data dir is `~/.local/share/buddy` and can be overridden via `BUDDY_DATA_DIR` or `XDG_DATA_HOME`.

## Key environment variables

- `BUDDY_PUBLIC_URL`: advertised base URL used in proxy/card URLs
- `BUDDY_ALLOW_PRIVATE_EXTERNAL_URLS`: allow/disallow private/loopback external agent URLs
- `BUDDY_MANAGED_AGENT_AUTO_START_ALL`: auto-start managed agents on control-plane startup
- `BUDDY_A2A_PROXY_CONNECT_TIMEOUT_S`
- `BUDDY_A2A_PROXY_WRITE_TIMEOUT_S`
- `BUDDY_A2A_PROXY_POOL_TIMEOUT_S`
