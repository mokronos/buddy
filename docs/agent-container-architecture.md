# Agent Container Architecture

## Goal

Run each agent as its own Docker container (agent runtime + A2A wrapper), while keeping one central Buddy server that orchestrates agent containers and serves the UI.

The agent runtime image is built once and reused. New agents are created by starting containers with different config files, not by rebuilding images.

## High-Level Components

1. **Buddy Control Plane (main server)**
   - Owns agent lifecycle (create, start, stop, delete).
   - Starts one container per agent using Docker API.
   - Tracks metadata (agent id, container id, status, URL, config path).
   - Exposes APIs for UI and forwards/aggregates agent discovery.

2. **Agent Runtime Container (one per agent)**
   - Runs the reusable `buddy-agent-runtime` image.
   - Hosts LLM agent logic + A2A endpoint(s).
   - Reads agent-specific config from mounted YAML.

3. **UI (`app/`)**
   - Talks only to Buddy control plane.
   - Lists available agents and status.
   - Creates agents from templates/config.
   - Sends chats/tasks to selected agent through control plane routing.

## Runtime Model

### Build once, configure at runtime

- Build image: `buddy-agent-runtime:<version>`.
- For each new agent:
  - Generate/store config file, e.g. `data/agents/<agent-id>/agent.yaml`.
  - Start container from the same image.
  - Mount config read-only into container (for example: `/etc/buddy/agent.yaml`).
  - Set env var like `BUDDY_AGENT_CONFIG=/etc/buddy/agent.yaml`.

No image rebuild is needed for new prompts/tools/model settings.

### Config example (YAML)

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
```

## Control Plane Responsibilities

1. **Agent Create**
   - Validate requested config.
   - Persist config + agent record.
   - Launch container with mounted config and labels (e.g. `buddy.agent.id=<id>`).
   - Health-check container A2A endpoint.
   - Register as active.

2. **Agent Discovery**
   - Maintain `/agents` index with state and A2A card URL.
   - UI reads this index; no direct Docker access from UI.

3. **Routing**
   - Either:
     - proxy requests (`/a2a/<id> -> container`), or
     - return direct endpoint to UI if network policy allows.
   - Prefer proxy first for simpler auth/CORS and stable URLs.

4. **Lifecycle + Recovery**
   - Restart policies.
   - Reconcile loop (detect dead containers, update status, optional restart).
   - Clean stop/delete APIs.

## UI Flow

1. User opens UI.
2. UI calls control plane `/agents`.
3. User creates or selects an agent.
4. UI sends prompt/task via control plane.
5. Control plane routes to agent container A2A endpoint.
6. Streaming/events flow back to UI.

## Current Code Layout

The current repository structure that implements this architecture:

```
src/buddy/
├── control_plane/
│   ├── server.py            # FastAPI app composition + startup/shutdown
│   ├── routes_agents.py     # Managed/external agent CRUD endpoints
│   ├── routes_proxy.py      # A2A proxy routes for managed/external agents
│   ├── managed_agents.py    # Docker-backed managed agent lifecycle
│   └── external_agents.py   # External agent registry
├── runtime/
│   ├── main.py              # Runtime container entrypoint
│   ├── config.py            # Build runtime agent from YAML config
│   ├── agent.py             # Agent + tools wiring
│   └── a2a/server.py        # A2A server and agent-card setup
└── shared/runtime_config.py # Shared YAML schema validation

app/src/                     # SolidStart client talking to control plane APIs
```

## Suggested Phased Rollout

1. **Phase 1: Single runtime image + YAML config mount**
   - Manual create/start/stop APIs.
   - Proxy A2A through control plane.

2. **Phase 2: Persistent registry + reconciliation**
   - Recover agents after server restart.
   - Health status in `/agents`.

3. **Phase 3: Templates + scaling controls**
   - Config templates for common agent types.
   - Resource limits/quotas per agent container.

## Why this matches your goal

- New agent instances come from the same prebuilt runtime image.
- Per-agent behavior comes from mounted YAML (or env), not rebuilds.
- Main server remains the orchestrator and UI backend.
- Architecture stays aligned with server/client + A2A direction.
