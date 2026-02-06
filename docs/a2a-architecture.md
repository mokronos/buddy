# A2A Multi-Agent Architecture Plan

## Overview

This document outlines the architecture for connecting Buddy to independent A2A agents while maintaining clear state ownership and avoiding the "triple state" problem. The architecture treats A2A as an internal protocol boundary, not as the public API for clients.

## Guiding Principles

1. **Single Source of Truth**: Backend owns all authoritative session state
2. **Clear Boundaries**: A2A types used only at agent boundary, transformed for client consumption
3. **Ephemeral Agent State**: Agent servers maintain only execution state, not session truth
4. **Client as Cache**: Frontend maintains only UI state and optimistic caches
5. **Event Sourcing**: All state changes flow through backend event log

## State Ownership Model

### Backend (System of Record)

**Owns:**
- Session graph (sessions, forks, branches)
- Message history (canonical truth)
- User edits, reverts, and modifications
- Agent run metadata (which agent ran, when, with what config)
- Event log (complete audit trail)
- Permissions and access control

**Database Schema Extensions:**

```sql
-- Core session table (exists)
CREATE TABLE sessions (
    session_id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    metadata_json TEXT NOT NULL  -- {title, agent_config_id, parent_session_id, fork_reason}
);

-- Message history with versioning (extends chat_messages)
CREATE TABLE session_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    revision_id TEXT NOT NULL,  -- for versioning/forking
    message_index INTEGER NOT NULL,
    role TEXT NOT NULL,  -- 'user' | 'assistant' | 'system' | 'tool'
    content TEXT NOT NULL,
    metadata_json TEXT,  -- {agent_run_id, tool_calls, edits, timestamp}
    created_at TEXT NOT NULL,
    FOREIGN KEY(session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
);

-- Agent runs (new)
CREATE TABLE agent_runs (
    run_id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    agent_url TEXT NOT NULL,  -- A2A agent endpoint
    context_id TEXT NOT NULL,  -- A2A context ID
    input_snapshot_hash TEXT NOT NULL,  -- hash of message history at run start
    status TEXT NOT NULL,  -- 'running' | 'completed' | 'failed' | 'cancelled'
    started_at TEXT NOT NULL,
    completed_at TEXT,
    metadata_json TEXT,  -- {agent_card, capabilities, config}
    FOREIGN KEY(session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
);

-- Event log for replay (extends events)
CREATE TABLE session_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    run_id TEXT,  -- nullable for non-run events
    event_index INTEGER NOT NULL,
    event_type TEXT NOT NULL,  -- 'user_message' | 'agent_start' | 'agent_token' | 'agent_tool' | 'agent_complete' | 'fork' | 'edit'
    payload_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(session_id) REFERENCES sessions(session_id) ON DELETE CASCADE,
    FOREIGN KEY(run_id) REFERENCES agent_runs(run_id) ON DELETE CASCADE
);

-- Session forking graph (new)
CREATE TABLE session_forks (
    fork_id TEXT PRIMARY KEY,
    parent_session_id TEXT NOT NULL,
    child_session_id TEXT NOT NULL UNIQUE,
    fork_reason TEXT,  -- 'user_edit' | 'branch' | 'retry'
    forked_at_message_index INTEGER NOT NULL,  -- where the fork occurred
    created_at TEXT NOT NULL,
    FOREIGN KEY(parent_session_id) REFERENCES sessions(session_id),
    FOREIGN KEY(child_session_id) REFERENCES sessions(session_id)
);
```

### Agent Servers (Ephemeral Execution State)

**Owns:**
- Internal agent loop state
- Tool call traces and execution details
- Scratchpads and intermediate reasoning
- Streaming token buffers

**Lifecycle:**
1. Backend sends snapshot + run_id to agent
2. Agent executes with A2A protocol
3. Agent streams events back to backend
4. On completion or failure, agent state is discarded
5. Backend can restart agent from same snapshot if needed

**Important:** Agent servers never mutate session history directly. All mutations flow through backend.

### Client (Cache + UI State)

**Owns:**
- UI state (scroll position, open panels, input drafts)
- Cached session metadata (for fast initial render)
- Optimistic updates (message sent, pending status)
- Local preferences and settings

**Behavior:**
- On startup: Load from cache immediately, then sync with backend
- Subscribe to backend events for real-time updates
- Assume cache invalidation at any time
- Always treat backend as authoritative

## Architecture Components

```
┌─────────────────────────────────────────────────────────────┐
│                         Client (SolidJS)                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │  UI State    │  │  Cache Store │  │  Sync Engine │       │
│  │  (Solid)     │  │  (IndexedDB) │  │  (SSE/WebSock│       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└──────────────────┬──────────────────────────────────────────┘
                   │ REST API + SSE
                   ▼
┌─────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI)                       │
│  ┌─────────────────────────────────────────────────────────┐│
│  │              Session Manager (Authoritative)             ││
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ││
│  │  │ Session Graph│  │ Message Hist │  │ Event Log    │  ││
│  │  └──────────────┘  └──────────────┘  └──────────────┘  ││
│  └─────────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────┐│
│  │              A2A Gateway (Protocol Bridge)               ││
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ││
│  │  │ A2A Client   │  │ Event Transf │  │ Run Manager  │  ││
│  │  │ (outbound)   │  │ (transform)  │  │ (tracking)   │  ││
│  │  └──────────────┘  └──────────────┘  └──────────────┘  ││
│  └─────────────────────────────────────────────────────────┘│
│  ┌─────────────────────────────────────────────────────────┐│
│  │              Client API (REST + SSE)                     ││
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ││
│  │  │ Session CRUD │  │ Event Stream │  │ Sync/Restore │  ││
│  │  └──────────────┘  └──────────────┘  └──────────────┘  ││
│  └─────────────────────────────────────────────────────────┘│
└──────────────────┬──────────────────────────────────────────┘
                   │ A2A Protocol (JSON-RPC + SSE)
                   ▼
┌─────────────────────────────────────────────────────────────┐
│                   External A2A Agents                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ Agent Loop   │  │ Tool Executor│  │ Event Queue  │       │
│  │ (pydantic-ai)│  │ (local/MCP)  │  │ (A2A spec)   │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

## Data Flows

### 1. Starting an Agent Run

```
User sends message
       ↓
Backend: Append to session history
         Create agent_run record
         Compute input_snapshot_hash
       ↓
Backend → A2A Agent: Send message with
         - context_id (new)
         - session snapshot (last N messages)
         - agent_run_id
       ↓
Agent: Initialize execution state
       Start agent loop
       ↓
Agent → Backend: Stream A2A events
       - status-update (working)
       - artifact-update (tokens)
       - artifact-update (tool calls)
       ↓
Backend: Transform A2A events to domain events
         Persist to event log
         Stream to connected clients
       ↓
Agent completes
       ↓
Backend: Mark run as completed
         Save final messages to history
         Notify clients
```

### 2. Editing History / Forking

```
User edits a message at index N
       ↓
Backend: Create new session (fork)
         Copy messages 0..N-1 to new session
         Apply edit as message N
         Mark old session as "forked"
       ↓
Backend: Cancel any running agent_run on old session
         (or let it complete, but it's now "orphaned")
       ↓
Backend → Clients: Emit "session_forked" event
         Clients switch to new session
       ↓
User can now continue from edited history
         (starts new agent run from clean state)
```

### 3. Client Restoration on Restart

```
Client starts
       ↓
Load cached session list from IndexedDB
Render immediately (stale OK)
       ↓
Fetch /sessions?since={last_sync}
Backend returns:
  - new sessions
  - updated sessions
  - deleted sessions
       ↓
Update cache
       ↓
Subscribe to SSE for real-time events
       ↓
For active session:
  Fetch /sessions/{id}?events_since={last_event_index}
  Replay events to restore UI state
```

## API Design

### Client-Facing API (REST + SSE)

Not using raw A2A types - using domain-specific schema:

```typescript
// Domain types for client
interface Session {
  id: string;
  title: string;
  createdAt: string;
  updatedAt: string;
  parentId?: string;  // if forked
  revision: number;   // for cache invalidation
  metadata: {
    agentUrl?: string;
    messageCount: number;
  };
}

interface DomainMessage {
  id: string;
  sessionId: string;
  index: number;
  role: 'user' | 'assistant' | 'system' | 'tool';
  content: string;
  timestamp: string;
  metadata: {
    agentRunId?: string;
    toolCalls?: ToolCall[];
    isEdited?: boolean;
    editHistory?: EditRecord[];
  };
}

interface DomainEvent {
  id: string;
  sessionId: string;
  index: number;
  type: 'user_message' | 'agent_start' | 'agent_token' | 
        'agent_tool_call' | 'agent_tool_result' | 
        'agent_complete' | 'fork' | 'edit';
  payload: unknown;
  timestamp: string;
}

// REST Endpoints
GET    /api/v1/sessions                    // List sessions
POST   /api/v1/sessions                    // Create session
GET    /api/v1/sessions/:id                // Get session + messages + events
POST   /api/v1/sessions/:id/messages       // Add user message (triggers agent)
POST   /api/v1/sessions/:id/fork           // Fork session at point
PUT    /api/v1/sessions/:id/messages/:msgId // Edit message (creates fork)
DELETE /api/v1/sessions/:id                // Delete session

// SSE Endpoint
GET    /api/v1/events?session_ids[]=...    // Subscribe to session events
```

### A2A Gateway (Internal)

```python
# Backend uses A2A types only here
from a2a.types import Message, Task, TaskStatusUpdateEvent, TaskArtifactUpdateEvent

class A2AGateway:
    """Manages connections to external A2A agents"""
    
    async def start_run(
        self, 
        session_id: str,
        agent_url: str,
        messages: list[DomainMessage]
    ) -> AgentRun:
        """Start an agent run via A2A"""
        # 1. Create run record
        run = await self.create_run_record(session_id, agent_url)
        
        # 2. Connect to A2A agent
        a2a_client = await A2AClient.connect(agent_url)
        
        # 3. Convert domain messages to A2A format
        a2a_message = self.to_a2a_message(messages)
        
        # 4. Start streaming
        async for a2a_event in a2a_client.send_message(a2a_message):
            # 5. Transform A2A event to domain event
            domain_event = self.transform_event(run.id, a2a_event)
            
            # 6. Persist and broadcast
            await self.persist_event(domain_event)
            await self.broadcast_to_clients(domain_event)
        
        return run
    
    def transform_event(
        self, 
        run_id: str, 
        a2a_event: TaskStatusUpdateEvent | TaskArtifactUpdateEvent
    ) -> DomainEvent:
        """Transform A2A event to domain event"""
        if isinstance(a2a_event, TaskStatusUpdateEvent):
            return DomainEvent(
                type='agent_status',
                payload={
                    'state': a2a_event.status.state,
                    'message': self.extract_text(a2a_event.status.message)
                }
            )
        elif isinstance(a2a_event, TaskArtifactUpdateEvent):
            # Distinguish between tokens, tool calls, final output
            artifact_name = a2a_event.artifact.name
            if artifact_name == 'output_delta':
                return DomainEvent(type='agent_token', payload={'token': ...})
            elif artifact_name == 'tool_result':
                return DomainEvent(type='agent_tool_result', payload={'result': ...})
            # etc.
```

## Event Transformation Examples

### A2A → Domain Event Mapping

| A2A Event | A2A Artifact Name | Domain Event Type | Purpose |
|-----------|------------------|-------------------|---------|
| status-update | (message) | `agent_start` | Agent began processing |
| artifact-update | output_start | `agent_token_start` | Begin token stream |
| artifact-update | output_delta | `agent_token` | Streaming token |
| artifact-update | output_end | `agent_token_end` | End token stream |
| artifact-update | tool_result | `agent_tool_result` | Tool execution result |
| artifact-update | full_output | `agent_complete` | Final response |
| status-update | (final) | `agent_status` | State change |

### Backend-Only Events (Not from A2A)

| Event Type | Trigger | Purpose |
|------------|---------|---------|
| `user_message` | Client sends message | Record user input |
| `fork` | User edits history | Session forked |
| `edit` | Message edited | Message modified |
| `agent_cancelled` | Backend cancels run | Run terminated |
| `session_archived` | Cleanup | Session moved to cold storage |

## Implementation Phases

### Phase 1: Foundation (Current → Target)

1. **Database Migration**
   - Add `agent_runs` table
   - Add `session_forks` table
   - Extend `sessions` with metadata
   - Migrate existing data

2. **Backend Refactoring**
   - Separate A2A executor from session management
   - Create A2A gateway module
   - Implement event transformation layer
   - Add REST API for client (non-A2A)

3. **Client API Design**
   - Define domain types
   - Create OpenAPI spec
   - Generate client SDK

### Phase 2: Multi-Agent Support

1. **Agent Registry**
   - Store agent URLs and capabilities
   - Agent discovery and health checks
   - Agent selection logic

2. **Session → Agent Mapping**
   - Allow switching agents mid-session
   - Track which agent handled which messages
   - Agent-specific configuration per session

3. **External A2A Agents**
   - Connect to non-local agents
   - Handle agent unavailability
   - Retry and fallback logic

### Phase 3: Advanced Features

1. **History Editing & Forking**
   - UI for editing messages
   - Fork creation on edit
   - Branch navigation

2. **Event Replay & Restoration**
   - Full session replay from events
   - Optimistic UI with server reconciliation
   - Offline support with sync

3. **Observability**
   - Event log inspection
   - Agent run analytics
   - Performance metrics

## Key Design Decisions

### Why Not Expose A2A Directly to Clients?

1. **A2A is agent-shaped, not user-shaped**: Includes internal details (tool calls, partial thoughts) that don't belong in UI
2. **UI evolves faster than agents**: Domain types allow frontend to change without breaking agent compatibility
3. **Need backend enrichment**: Attach metadata (timestamps, edit history, permissions) not in A2A
4. **Replay and forking**: Requires backend-managed event log that A2A doesn't provide
5. **Multiple agents**: Backend needs to coordinate between agents, not pass through raw A2A

### Why Keep Agent State Ephemeral?

1. **Reliability**: Can restart agent on different server from snapshot
2. **Debugging**: Clear separation between "what happened" (backend) and "how it happened" (agent)
3. **Cost**: Don't pay to persist agent scratchpads forever
4. **Compliance**: Sensitive internal reasoning stays in agent, not in permanent logs

### Why Event Sourcing?

1. **Complete audit trail**: Every action recorded
2. **Time travel**: Can reconstruct any session state at any point
3. **Sync**: Differential sync for clients (send only new events)
4. **Forking**: Natural model for branches - just replay events up to fork point
5. **Debugging**: Can replay exactly what user saw

## Code Structure

```
src/buddy/
├── api/                    # Client-facing REST API
│   ├── __init__.py
│   ├── sessions.py         # Session CRUD endpoints
│   ├── messages.py         # Message management
│   └── events.py           # SSE event streaming
├── a2a/
│   ├── __init__.py
│   ├── gateway.py          # A2A client for external agents
│   ├── transformer.py      # A2A → Domain event transformation
│   └── executor.py         # (existing) Local agent executor
├── domain/                 # Domain models (authoritative)
│   ├── __init__.py
│   ├── models.py           # DomainMessage, Session, AgentRun
│   └── events.py           # Domain event types
├── session/
│   ├── __init__.py
│   ├── manager.py          # Session lifecycle, forking
│   └── store.py            # Database operations
└── main.py                 # FastAPI app composition
```

## Migration Path from Current Implementation

### Current State
- SQLite database with `sessions`, `messages`, `events`, `chat_messages`
- A2A endpoint at `/a2a` serving local agent
- Direct A2A event storage in `events` table
- Session list at `/sessions`, detail at `/sessions/{id}`

### Migration Steps

1. **Schema Update** (non-breaking)
   ```sql
   -- Add new tables alongside existing
   CREATE TABLE agent_runs (...);
   CREATE TABLE session_forks (...);
   ALTER TABLE sessions ADD COLUMN metadata_json TEXT DEFAULT '{}';
   ```

2. **Dual Write** (backward compatible)
   - Continue writing to existing tables
   - Start writing to new tables
   - Backfill existing data

3. **API Versioning**
   - Keep `/sessions` for old clients
   - Add `/api/v1/sessions` with new schema
   - Migrate frontend to new API

4. **Cleanup**
   - Remove old endpoints
   - Consolidate tables
   - Remove dual write

## Success Metrics

- **State clarity**: Can answer "what is the current session state?" by querying backend only
- **Agent replaceability**: Can swap A2A agent without changing client code
- **History editing**: Can edit message and continue from that point
- **Multi-agent**: Can connect to 3+ different A2A agents
- **Client sync**: Client restores in <2 seconds with full session history
- **Replay**: Can replay any session from event log exactly as user saw it

## Open Questions

1. **Agent capability negotiation**: How to handle agents with different capabilities (streaming vs non-streaming)?
2. **Long-running tasks**: How to handle agents that take hours/days with human-in-the-loop?
3. **Agent authentication**: How to authenticate with external A2A agents?
4. **Rate limiting**: How to prevent client from overwhelming agent with edits/forks?
5. **Cold storage**: When to archive old sessions to cheaper storage?

## References

- [A2A Protocol Specification](https://github.com/google/A2A)
- [A2A Official Site](https://google.github.io/A2A)
- [Google A2A Announcement](https://developers.googleblog.com/en/a2a-a-new-era-of-agent-interoperability/)
- Current Buddy docs: `docs/server.md`, `docs/plan.md`
