# Agent Container Architecture

## Goal

Run each managed agent as its own Docker container while keeping one central control plane for orchestration, proxying, and client-facing APIs.

The runtime image is reusable: new agents are created by writing a config file and launching another container from the same image.

## Components

1. **Buddy control plane** (`packages/buddy-control-plane`)
   - Owns managed/external agent registries.
   - Starts/stops/deletes managed runtime containers.
   - Exposes `/agents` and `/sessions` APIs.
   - Proxies A2A traffic for managed and external agents.

2. **Runtime container** (`packages/buddy-runtime`)
   - Boots from `BUDDY_AGENT_CONFIG` YAML.
   - Builds a `pydantic_ai.Agent`.
   - Serves A2A endpoints and streams events.

3. **Web client** (`app/`)
   - Talks to control-plane APIs only.
   - Creates/updates managed and external agents.
   - Streams chat events through control-plane proxy routes.

## Runtime model

### Build once, configure per container

- Build image: `buddy-agent-runtime:latest`.
- For each managed agent, control plane:
  - validates runtime YAML,
  - writes config to `<buddy_data_dir>/agents/{agent_id}/agent.yaml`,
  - starts container with config mounted read-only,
  - sets `BUDDY_AGENT_CONFIG` to the mount path.

No runtime image rebuild is required for per-agent prompt/model/tool changes.

### Runtime config shape

```yaml
agent:
  id: sales-agent
  name: Sales Agent
  instructions: "You are a sales support agent."
  model: openrouter:openrouter/free

a2a:
  port: 8000
  mount_path: /a2a

tools:
  web_search: true
  todo: true

mcp:
  enabled: true
  url: http://127.0.0.1:18001/mcp
```

## Control-plane behavior

### Managed agents

- Registry stored in `<buddy_data_dir>/managed_agents.json`.
- Lifecycle APIs in `routes/agents.py`:
  - create/list/get/start/stop/delete
  - get/update runtime YAML config
  - fetch logs
- Reconcile with Docker metadata on startup.
- Optional auto-start on startup via `BUDDY_MANAGED_AGENT_AUTO_START_ALL`.

### External agents

- Registry stored in `<buddy_data_dir>/external_agents.json`.
- CRUD APIs in `routes/agents.py`.
- Base URLs are normalized/validated before persistence.

### Proxy routing

- Managed proxy root: `/a2a/managed/{agent_id}`
- External proxy root: `/a2a/external/{agent_id}`
- Agent-card responses are rewritten to point `url` at control-plane proxy routes.

## Current code layout

```text
packages/
  buddy-control-plane/src/buddy/control_plane/
    server.py
    routes/
      agents.py
      sessions.py
      proxy.py
    managed_agents.py
    external_agents.py

  buddy-runtime/src/buddy/runtime/
    main.py
    config.py
    agent.py
    a2a/server.py

  buddy-shared/src/buddy/
    shared/runtime_config.py
    session_store.py
    data_dirs.py
```

## Why this architecture works

- Single orchestrator for all clients and all agent endpoints.
- Stable proxy URLs regardless of container IP/port churn.
- Reproducible per-agent behavior through explicit YAML config.
- Clear split between lifecycle management (control plane) and execution (runtime).
