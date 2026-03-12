# Buddy Web App (`app/`)

SolidStart frontend for Buddy.

## What it does

- Chat UI for A2A agents (`/`)
- Managed/external agent administration (`/managed-agents`)
- Live managed-agent logs (`/agent-logs`)

The app talks to the Buddy control plane and does not call managed Docker runtimes directly.

## Requirements

- Node.js `>=22`
- `bun` package manager/runtime

## Install and run

```bash
bun install
bun run dev
```

Build and run production bundle:

```bash
bun run build
bun run start
```

## Configuration

- `VITE_A2A_BASE_URL` (optional): base URL of Buddy control plane.
  - default: `http://localhost:10001`

## Notes

- Generated OpenAPI client code is in `src/buddy-client/`.
- API wrappers used by the UI live in `src/a2a/`.
