# Server
Backend endpoints and streaming behavior in one place.

---
## Understand
Buddy runs a FastAPI app and mounts the A2A JSON-RPC server under `/a2a`. Sessions, events, and chat history persist in `sessions.db` for replay.

---
## Call
Use the A2A JSON-RPC endpoint at `POST /a2a` for messages and streaming. Fetch the agent card from `GET /a2a/.well-known/agent-card.json` (legacy `/a2a/.well-known/agent.json`). The agent card advertises the `/a2a` base URL for clients.

Quick one-off test from the CLI:

```bash
uv run buddy ask "Say hello in one short sentence"
```

Raw JSON-RPC via curl:

```bash
curl -sS http://localhost:10001/a2a \
  -H 'content-type: application/json' \
  -d '{
    "jsonrpc": "2.0",
    "id": "1",
    "method": "message/send",
    "params": {
      "message": {
        "messageId": "one-off-1",
        "kind": "message",
        "role": "user",
        "parts": [{"kind": "text", "text": "Say hello in one short sentence"}],
        "contextId": "quick-test"
      }
    }
  }'
```

---
## Stream
Streaming responses arrive as SSE events from the A2A handler. The backend emits `status-update` events plus `artifact-update` chunks like `output_delta`, `output_end`, `tool_result`, and `full_output`.

---
## Restore
Session history endpoints live at `GET /sessions` and `GET /sessions/{session_id}`. The detail response includes messages and stored events so clients can replay the stream.

---
## Configure
Set `BUDDY_PUBLIC_URL` to control the base URL advertised in the agent card. Provide either `https://host/a2a` or `https://host` and the server will normalize it. The server still binds to the host/port from `uvicorn`.
