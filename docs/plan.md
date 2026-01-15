# Buddy roadmap

## Goal

Build a JARVIS-like assistant that can execute tasks autonomously, evolve its prompt/skills over time, and expose a clean client/server interface for multiple clients.

## Architecture decisions

- [ ] Use a server/client architecture
- [ ] Server hosts a single A2A endpoint for direct agent interaction
- [ ] Server exposes additional endpoints for session management and client needs
- [ ] First client is a CLI client that talks to the server
- [ ] Local core tools live in the main app
- [ ] MCP tools live in a dedicated module
- [ ] Use JSON files for all storage (debuggable + simple)
- [ ] TypeScript execution allowed with broad permissions

## Core tools (local)

- [ ] Planner / notetaking tool (JSON CRUD)
- [ ] Settings manager (get/set key/value pairs in JSON)
- [ ] Local file search/viewer
- [ ] CLI executor tool
- [ ] Web search and fetch tools (SearXNG + fetch)
- [ ] Code interpreter / TS REPL tool (Deno with broad permissions)

## MCP tools module

- [ ] MCP registry stored in JSON
- [ ] Install/register MCP servers
- [ ] Enable/disable MCP servers per session
- [ ] Expose MCP tools to the agent dynamically

## Context and memory

- [ ] Context manager for message history
- [ ] History persistence in JSON
- [ ] History trimming/summarization strategy
- [ ] Session storage keyed by context id

## Reflexion / self-improvement

- [ ] Post-run reflection step
- [ ] Store learned behaviors/skills in JSON
- [ ] Optional system prompt updates based on reflection

## Client/server endpoints

- [ ] A2A endpoint for agent interaction
- [ ] Session create/list/delete endpoints
- [ ] Session history fetch/append endpoints
- [ ] Endpoint(s) for tool inventory and status

## CLI client (first client)

- [ ] Connects to server A2A endpoint
- [ ] Manages sessions (create/select)
- [ ] Streams responses and tool events
- [ ] Simple config for server URL
