# Buddy Docs

Buddy is an autonomous assistant platform built around a control-plane server and A2A agent runtimes.

## Start here

- `server.md`: API surface, proxy boundaries, data persistence, and config.
- `a2a-architecture.md`: request flow between control plane, runtimes, and clients.
- `agent-container-architecture.md`: managed-agent container model and lifecycle.
- `modules.md`: package/module map for the repository.

## Current status

- Control plane is package-based (`packages/buddy-control-plane`).
- Runtime is package-based (`packages/buddy-runtime`) and configured by YAML.
- Shared contracts/storage live in `packages/buddy-shared`.
- Frontend lives in `app/` and talks to control-plane APIs.
