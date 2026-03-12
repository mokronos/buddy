# Server
Control-plane endpoints and A2A proxy behavior.

---
## Overview
Buddy runs a FastAPI control plane. It exposes domain-style APIs for the UI and proxies raw A2A traffic at the agent boundary.

- Domain APIs are available under `/sessions` and `/agents`.
- A2A endpoints are exposed via managed/external agent proxies.

Session history, events, and chat messages persist in `sessions.db`.

---
## Domain API
Main control-plane APIs:

- `GET /sessions`
- `GET /sessions/{session_id}`
- `GET /agents`
- `GET /agents/managed`
- `POST /agents/managed`
- `GET /agents/managed/{agent_id}/config`
- `PUT /agents/managed/{agent_id}/config`
- `GET /agents/external`
- `POST /agents/external`

Managed-agent config is YAML and is validated before create/update.

---
## A2A Boundary
Raw A2A JSON-RPC/SSE stays at the agent boundary:

- Managed container proxies: `/a2a/managed/{agent_id}`
- External agent proxies: `/a2a/external/{agent_id}`

Agent-card requests are rewritten so `url` points at the control-plane proxy URL.

---
## Security Defaults
- External agent URLs are validated (http/https only, no credentials/query/fragment).

---
## Configure
- `BUDDY_PUBLIC_URL` controls advertised/proxy base URLs.
- `BUDDY_ALLOW_PRIVATE_EXTERNAL_URLS` controls whether private/loopback external URLs are allowed.
