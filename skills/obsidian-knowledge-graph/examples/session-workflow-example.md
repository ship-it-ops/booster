# Example: Full Session Workflow

This example shows a complete read-work-write cycle across two sessions and two different projects, demonstrating how knowledge persists and cross-pollinates.

---

## Session 1: Debugging a WebSocket Bug in `my-api`

### Session Start — Read Protocol

The agent knows the vault path from a previous session: `~/Obsidian/claude-vault`

```
> Read: ~/Obsidian/claude-vault/_ai/MANIFEST.md
```

```markdown
# Knowledge Graph
Last updated: 2026-03-20 | Total notes: 3

## Decisions
- [[my-api--knowledge-graph-initialized]] | active | my-api | 2026-03-18 | AI knowledge graph set up in this vault
- [[my-api--websocket-library-choice]] | active | my-api | 2026-03-19 | Chose ws over socket.io for lower overhead

## Investigations

## Patterns
- [[my-api--error-handling-convention]] | active | my-api | 2026-03-20 | All services use Result type, never throw
```

The agent notes the project uses `ws` library and has an error handling convention.

### User Request

```
User: The WebSocket server is leaking memory. Connections aren't being cleaned
up when clients disconnect. Can you investigate?
```

### During Work — Consulting Knowledge

The agent reads `[[my-api--websocket-library-choice]]` for context on the WS setup, then reads `[[my-api--error-handling-convention]]` since error paths might be involved.

From the decision note, the agent learns the server uses raw `ws` with manual ping/pong heartbeats. It investigates the code, finds the bug: the `close` event handler doesn't remove the connection from the active connections Set when triggered by a ping timeout.

### After Fix — Write Protocol

**Step 1 — Search MANIFEST**: No existing investigation about WebSocket memory leaks.

**Step 2 — Decide**: Create new note.

**Step 3 — Write the note** to `~/Obsidian/claude-vault/_ai/notes/my-api--websocket-connection-leak-on-timeout.md`:

```markdown
---
type: investigation
status: active
created: 2026-03-21
updated: 2026-03-21
project: my-api
tags: websocket, memory-leak, connections
---

# WebSocket Connection Leak on Ping Timeout

## Symptoms
Memory usage grows linearly over time. After 24h in staging, the server
consumes 2GB+ RAM. Heap snapshot shows thousands of stale Connection objects.

## Root Cause
In `src/ws/server.ts`, the `close` event handler only fires on explicit client
disconnect (`code 1000`). When a client silently drops (ping timeout), the
`ws` library emits `close` with code `1006`, but our handler filters it out.
The connection stays in the `activeConnections` Set forever.

## Fix
Changed the close handler to remove the connection from `activeConnections`
regardless of close code. Added a periodic sweep (every 60s) that checks
`readyState` and removes any connections in CLOSED state.

## Prevention
- Always handle ALL close codes, not just clean disconnects
- Add a periodic connection audit as a safety net
- Monitor `activeConnections.size` as a metric

## Related
- [[my-api--websocket-library-choice]] — this decision set up the ws configuration
- [[my-api--error-handling-convention]] — the fix follows our Result type pattern
```

**Step 4 — Update MANIFEST** with the new entry under Investigations.

**Step 5 — Links** already added in `## Related`.

---

## Session 2: New Project, Cross-Project Knowledge

The next day, the developer works on a **different project**: `~/Repos/chat-service/`. This project also uses WebSockets.

### Session Start

```
> Read: ~/Obsidian/claude-vault/_ai/MANIFEST.md
```

The agent sees all 4 notes. It's now working in the `chat-service` project, but the MANIFEST includes notes from `my-api`.

### User Request

```
User: I'm setting up WebSocket handling for the chat service. Can you help
me implement the connection manager?
```

### Cross-Project Knowledge Surfaces

The agent notices `my-api--websocket-connection-leak-on-timeout` in the MANIFEST — a WebSocket investigation from yesterday in a different project. It reads the note.

```
Agent: Before we start, I found something relevant from your my-api project.
Yesterday we fixed a WebSocket memory leak caused by not handling all close
codes — connections were only cleaned up on explicit disconnect (code 1000),
not on ping timeouts (code 1006).

I'll make sure the chat-service connection manager handles this correctly
from the start:
- Remove connections on ALL close codes
- Add a periodic readyState sweep as a safety net
- Include a connection count metric
```

The agent implements the connection manager with these safeguards built in.

### New Knowledge Captured

After implementation, the agent writes a pattern note:

**Created: `~/Obsidian/claude-vault/_ai/notes/chat-service--websocket-connection-manager-pattern.md`**

```markdown
---
type: pattern
status: active
created: 2026-03-22
updated: 2026-03-22
project: chat-service
tags: websocket, connections, pattern
---

# WebSocket Connection Manager Pattern

## When to Use
Any service that manages WebSocket connections with heartbeat/ping-pong.

## Implementation
- Store connections in a Map keyed by client ID
- Remove on ALL close codes (not just 1000)
- Run periodic sweep (60s) checking readyState
- Expose connection count as a metric
- See `src/ws/connection-manager.ts` for the chat-service implementation

## Gotchas
- The `ws` library emits close code 1006 for ping timeouts — easy to miss
- Always check readyState before sending to any connection

## Related
- [[my-api--websocket-connection-leak-on-timeout]] — the bug that inspired this pattern
- [[my-api--websocket-library-choice]] — ws library specifics
```

MANIFEST updated. The knowledge graph now links across projects:

```
my-api--websocket-library-choice
    ↓
my-api--websocket-connection-leak-on-timeout
    ↓
chat-service--websocket-connection-manager-pattern
```

---

## What This Demonstrates

1. **Central vault**: One vault serves both `my-api` and `chat-service` projects
2. **Cross-project discovery**: A bug fix in project A becomes a preventive pattern in project B
3. **Knowledge compounds**: Each note links to related notes across project boundaries
4. **The agent surfaced relevant knowledge proactively** — the user didn't have to ask "did we have WebSocket issues before?"
5. **In Obsidian's graph view**: All three notes appear as connected nodes, showing how knowledge flows between projects
