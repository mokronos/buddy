# TUI
Terminal client for streaming Buddy sessions.

---
## Start
Launch the server with `uv run buddy server` and the UI with `bun dev`. Use `TUI_SERVER_URL` (pointing at `/a2a`) when the server is not on localhost.

---
## Connect
The UI expects the A2A base URL, defaulting to `http://localhost:10001/a2a`. It fetches the agent card and streams messages through the SSE channel.

---
## Replay
Use `/sessions` to open the session picker. The UI reloads stored messages and replays saved events to rebuild the streaming output.

---
## Inspect
Status panel tracks connection state, agent name, task id, and context id. Errors from fetch or streaming show up inline.
