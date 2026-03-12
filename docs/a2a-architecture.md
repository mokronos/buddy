# A2A Architecture (Current Implementation)

This document describes the architecture that is implemented in the repository today.

## Summary

- Buddy exposes a control-plane API for clients.
- A2A remains the protocol boundary between control plane and agents.
- Managed agents are runtime containers orchestrated by the control plane.
- External agents are registered URLs proxied by the control plane.
- Sessions/messages/events are persisted by a shared SQLite `SessionStore`.

## Request flow

### Chat flow (managed agent)

1. Client resolves an agent from `GET /agents`.
2. Client sends A2A request to `/a2a/managed/{agent_id}`.
3. Control plane validates agent status and resolves the runtime target URL.
4. Proxy forwards JSON-RPC/SSE to the runtime container.
5. Runtime executes with `PyAIAgentExecutor`, streams A2A updates/artifacts.
6. Control plane streams the response back to client.
7. Runtime persists session events/messages to `SessionStore`.

### Chat flow (external agent)

1. Client sends A2A request to `/a2a/external/{agent_id}`.
2. Control plane resolves target from external registry.
3. Proxy forwards request and streams response.
4. For card requests, control plane rewrites card `url` to proxy route.

## Control plane

Source: `packages/buddy-control-plane/src/buddy/control_plane/`

Key modules:

- `server.py`: app composition, startup/shutdown, CORS, request logging middleware.
- `routes/agents.py`: managed/external CRUD + managed config + logs.
- `routes/sessions.py`: session list/detail APIs.
- `routes/proxy.py`: managed/external reverse proxy and card rewriting.
- `managed_agents.py`: Docker-backed managed-agent lifecycle and reconciliation.
- `external_agents.py`: external agent registry and URL normalization.

Control plane endpoint groups:

- Domain endpoints: `/agents`, `/agents/managed/*`, `/agents/external/*`, `/sessions*`
- A2A proxy endpoints:
  - `/a2a/managed/{agent_id}`
  - `/a2a/external/{agent_id}`

## Runtime

Source: `packages/buddy-runtime/src/buddy/runtime/`

Key modules:

- `main.py`: runtime process entrypoint.
- `config.py`: config-to-agent wiring.
- `agent.py`: `pydantic_ai.Agent` construction and toolset selection.
- `a2a/server.py`: A2A FastAPI app + card/rpc endpoint registration.
- `a2a/executor.py`: request execution, streaming, cancellation, persistence.
- `a2a/event_writer.py`: session event persistence helpers.

Runtime is configured via YAML (`BUDDY_AGENT_CONFIG`) using schema in `buddy.shared.runtime_config`.

## Shared persistence and contracts

Source: `packages/buddy-shared/src/buddy/`

- `session_store.py`: SQLite tables for sessions/messages/events/todos.
- `shared/runtime_config.py`: runtime config schema + path helpers.
- `shared/logging.py`: structured JSON logging helpers.
- `data_dirs.py`: Buddy data-dir resolution (`BUDDY_DATA_DIR` / `XDG_DATA_HOME`).

## Data locations

By default data is stored under `~/.local/share/buddy`.

- `sessions.db`
- `managed_agents.json`
- `external_agents.json`
- `agents/{agent_id}/agent.yaml`

## Tool model in runtime

Built-in toolsets currently wired in `runtime/agent.py`:

- Web tools (`web_search`, `fetch_web_page`)
- Todo tools (`todoread`, `todoadd`, `todoupdate`, `tododelete`)
- Optional MCP streamable HTTP toolset (`mcp.enabled` + `mcp.url`)

Standalone utility tools exist in `runtime/tools/` (for example, calculator/personal info wrappers using `pydantic_ai.Tool`), but runtime wiring is controlled by `agent.py`.

## Frontend integration

Source: `app/src/`

- Uses control-plane APIs for agent management and session views.
- Streams A2A through control-plane proxy URLs.
- Main routes:
  - `/` chat
  - `/managed-agents` agent administration
  - `/agent-logs` managed-agent logs

## Environment variables

Control-plane relevant:

- `BUDDY_PUBLIC_URL`
- `BUDDY_ALLOW_PRIVATE_EXTERNAL_URLS`
- `BUDDY_MANAGED_AGENT_AUTO_START_ALL`
- `BUDDY_A2A_PROXY_CONNECT_TIMEOUT_S`
- `BUDDY_A2A_PROXY_WRITE_TIMEOUT_S`
- `BUDDY_A2A_PROXY_POOL_TIMEOUT_S`

Runtime relevant:

- `BUDDY_AGENT_CONFIG`
- `BUDDY_REQUIRE_LANGFUSE`
- `LANGFUSE_PUBLIC_KEY`
- `LANGFUSE_SECRET_KEY`

## Current code structure

```text
packages/
  buddy-control-plane/
    src/buddy/control_plane/
      server.py
      server_state.py
      routes/
        agents.py
        sessions.py
        proxy.py
      managed_agents.py
      external_agents.py
      validation.py

  buddy-runtime/
    src/buddy/runtime/
      main.py
      config.py
      agent.py
      a2a/
        server.py
        executor.py
        event_writer.py
        utils.py
      tools/
        todo.py
        todo_store.py
        web_search.py
        ts_executor.py
        calculator.py
        personal_info.py

  buddy-shared/
    src/buddy/
      session_store.py
      data_dirs.py
      shared/
        runtime_config.py
        logging.py

app/
  src/
```

## Notes

- This reflects implemented behavior, not future speculative schema changes.
- Historical planning notes were replaced with the current package-based architecture to reduce drift.
