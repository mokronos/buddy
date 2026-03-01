# Server
Control-plane endpoints and A2A proxy behavior.

---
## Overview
Buddy runs a FastAPI control plane. It exposes domain-style APIs for the UI and proxies raw A2A traffic at the agent boundary.

- Domain APIs are available under `/api/v1/...`.
- Backward-compatible aliases still exist for `/sessions` and `/agents`.
- A2A endpoints are exposed via managed/external agent proxies.

Session history, events, and chat messages persist in `sessions.db`.

---
## Domain API
Main control-plane APIs:

- `GET /api/v1/sessions`
- `GET /api/v1/sessions/{session_id}`
- `GET /api/v1/agents`
- `GET /api/v1/agents/managed`
- `POST /api/v1/agents/managed`
- `GET /api/v1/agents/managed/{agent_id}/config`
- `PUT /api/v1/agents/managed/{agent_id}/config`
- `GET /api/v1/agents/external`
- `POST /api/v1/agents/external`

Managed-agent config is YAML and is validated before create/update.

---
## A2A Boundary
Raw A2A JSON-RPC/SSE stays at the agent boundary:

- Managed container proxies: `/a2a/managed/{agent_id}`
- External agent proxies: `/a2a/external/{agent_id}`

Agent-card requests are rewritten so `url` points at the control-plane proxy URL.

---
## Runtime API
Internal runtime endpoints are for environment container operations only:

- `POST /internal/runtime/acquire`
- `POST /internal/runtime/release`
- `POST /internal/runtime/exec`
- `POST /internal/runtime/read-file`
- `POST /internal/runtime/write-file`
- `POST /internal/runtime/patch-file`

Use header `x-buddy-internal-token` when `BUDDY_INTERNAL_RUNTIME_TOKEN` is configured.

---
## Security Defaults
- In non-local environments, `BUDDY_INTERNAL_RUNTIME_TOKEN` is required by default.
- To explicitly bypass this in development, set `BUDDY_ALLOW_INSECURE_INTERNAL_RUNTIME=true`.
- External agent URLs are validated (http/https only, no credentials/query/fragment).

---
## Configure
- `BUDDY_PUBLIC_URL` controls advertised/proxy base URLs.
- `BUDDY_RUNTIME_API_BASE_URL` is used by runtime containers to call control-plane internal runtime APIs.
- `BUDDY_ALLOW_PRIVATE_EXTERNAL_URLS` controls whether private/loopback external URLs are allowed.
