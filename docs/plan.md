# Buddy Roadmap

This roadmap tracks current implementation status and near-term priorities.

## Implemented foundation

- [x] Server/client architecture with package split:
  - `buddy-control-plane`
  - `buddy-runtime`
  - `buddy-shared`
- [x] Control-plane APIs for agents and sessions
- [x] Managed-agent container lifecycle (create/start/stop/delete)
- [x] External-agent registry and proxying
- [x] A2A proxy boundary for managed and external agents
- [x] SQLite-backed session/event/message/todo persistence
- [x] CLI commands for server/dev/chat/ask
- [x] Web client with chat, managed-agents admin, and agent logs pages

## In progress / active focus

- [ ] Improve frontend session history/replay UX using existing `/sessions` APIs
- [ ] Tighten OpenAPI-driven frontend API usage (reduce handwritten wrappers)
- [ ] Improve runtime tool catalog and expose only production-ready tools by default
- [ ] Expand observability around runtime execution and proxy behavior

## Next priorities

- [ ] Add stronger integration tests across control-plane proxy + runtime streaming
- [ ] Improve external-agent auth and connection configuration
- [ ] Formalize compatibility guarantees for control-plane API responses
- [ ] Add clearer deployment docs for control plane + runtime image

## Longer-term ideas

- [ ] Multi-agent orchestration workflows with explicit inter-agent task handoff
- [ ] Richer session branching/forking UI and replay controls
- [ ] Policy/approval controls for high-impact tools
