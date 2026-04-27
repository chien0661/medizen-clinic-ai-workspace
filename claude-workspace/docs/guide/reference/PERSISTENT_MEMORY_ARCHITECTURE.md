# Persistent Memory Architecture for AI Agents

**Based on:** Claude-Mem Plugin Architecture
**Source:** VISSoft Confluence Page 147621929
**Purpose:** Template for implementing persistent memory in AI agent projects

---

## Table of Contents

1. [Overview](#overview)
2. [The Problem](#the-problem)
3. [Architecture Concepts](#architecture-concepts)
4. [Session Lifecycle](#session-lifecycle)
5. [Hook-Based Architecture](#hook-based-architecture)
6. [Database Schema](#database-schema)
7. [Worker Service](#worker-service)
8. [Token-Efficient Search](#token-efficient-search)
9. [Privacy and Security](#privacy-and-security)
10. [Integration with Multi-Agent System](#integration-with-multi-agent-system)
11. [Implementation Guide](#implementation-guide)
12. [Best Practices](#best-practices)

---

## Overview

**Persistent memory** enables AI agents to retain context across sessions, avoiding the need to re-explain project details every time. This architecture automatically captures tool usage observations, compresses them using AI, and stores them for future retrieval.

### Key Benefits

✅ **Never lose context** - Automatically inject relevant history from previous sessions
✅ **Token-efficient** - Three-layer search reduces token consumption by ~10x
✅ **Privacy-first** - Strip sensitive data with privacy tags
✅ **Asynchronous** - Background worker doesn't block main session
✅ **Searchable** - Full-text and semantic search across all observations
✅ **Multi-agent ready** - Shared memory across different agent roles

---

## The Problem

AI agents currently struggle with:

- **Session amnesia** - No memory between conversations
- **Repeated explanations** - Users must re-explain project context every session
- **Lost learnings** - Insights from debugging sessions disappear
- **Context switching** - Difficult to recall what happened in previous work

### Market Validation

Multiple funded startups are tackling this:
- **Mem0** - $24M raised for portable "memory passport"
- **Letta** - $10M for stateful MemGPT-style agents
- **Supermemory** - $2.6M for universal memory API
- **Memories.ai** - $8M for visual memory over video libraries

---

## Architecture Concepts

### Core Components

```
┌─────────────────────────────────────────────────────────────┐
│ Session Start → Inject context from last 10 sessions       │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ User Prompts → Create session, save user prompts           │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Tool Executions → Capture observations (Read, Write, etc.)  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Worker Processes → Extract learnings via Claude Agent SDK   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Session Ends → Generate summary, ready for next session     │
└─────────────────────────────────────────────────────────────┘
```

### Technology Stack

- **Storage**: SQLite with WAL mode + FTS5 for full-text search
- **Semantic Search**: ChromaDB for vector embeddings (optional)
- **Compression**: Claude Agent SDK for AI-powered summarization
- **API**: Express.js HTTP server (port 37777)
- **Runtime**: Node.js 18+ or Bun
- **Protocol**: Model Context Protocol (MCP) for tool integration

---

## Session Lifecycle

### 1. Session Start (Context Injection)

**When:** User opens Claude Code or resumes a session

**Actions:**
1. Health check on worker service (start if needed)
2. Identify current project from working directory
3. Fetch context from last 10 sessions via `/api/context/inject?project={project}`
4. Inject returned markdown into Claude's hidden context
5. User sees continuity from previous work without manual explanation

**Example Context Injected:**
```markdown
## Previous Session Context (Last 10 sessions)

### Session 2026-02-01: Implemented User Authentication
- Investigated: OAuth2 flow with JWT tokens
- Learned: JWT should expire in 1 hour, refresh tokens in 7 days
- Completed: Login endpoint, token refresh endpoint
- Next: Implement role-based access control

### Session 2026-01-30: Fixed Database Connection Pool
- Investigated: Connection timeouts under high load
- Learned: Pool size was too small (5), increased to 20
- Completed: Updated pool configuration in config/database.js
...
```

### 2. User Prompt Submit (Session Creation)

**When:** User submits a prompt/question

**Actions:**
1. Extract project name from working directory
2. Create or retrieve database session using `INSERT OR IGNORE` (idempotent)
3. Increment prompt counter for the session
4. Strip `<private>` tags from prompt (sensitive data removal)
5. Save cleaned prompt to `user_prompts` table
6. POST to worker service at `/sessions/{id}/init`

**Database Entry:**
```sql
INSERT OR IGNORE INTO sdk_sessions (
  claude_session_id,
  project_name,
  first_prompt,
  status
) VALUES (
  'session_abc123',
  'template-ai-team',
  'Please implement user authentication',
  'initialized'
);
```

### 3. Tool Execution (Observation Capture)

**When:** After every tool invocation (Read, Write, Bash, Grep, etc.)

**Actions:**
1. Check skip list - ignore low-value tools (`TodoWrite`, `AskUserQuestion`)
2. Strip privacy tags from tool input and output
3. Ensure worker is running
4. POST observation to `/api/sessions/observations` (async, non-blocking)
5. Worker queues observation for compression

**Example Observation:**
```json
{
  "session_id": 123,
  "tool_name": "Read",
  "tool_input": "src/auth/login.js",
  "tool_response": "// Login handler code...",
  "timestamp": "2026-02-03T14:30:00.000Z"
}
```

### 4. Worker Processing (Compression)

**When:** Background worker processes queued observations

**Actions:**
1. Dequeue observation from processing queue
2. Generate compression prompt using message generators
3. Call Claude Agent SDK to compress observation
4. Parse XML response from Claude
5. Extract structured learning (`<compressed_observation>...</compressed_observation>`)
6. Store compressed observation in SQLite
7. Generate vector embedding and store in ChromaDB (optional)
8. Emit SSE event to update web viewer

**Compression Prompt Example:**
```
You are observing a tool execution. Compress this observation into 2-3 sentences
focusing on what was learned, discovered, or changed.

Tool: Read
Input: src/auth/login.js
Response: [file contents]

Provide output in XML:
<compressed_observation>
[Your 2-3 sentence summary]
</compressed_observation>
```

**Compressed Result:**
```xml
<compressed_observation>
The login handler uses JWT tokens with bcrypt password hashing.
Access tokens expire in 1 hour and refresh tokens in 7 days.
The implementation follows OAuth2 bearer token pattern.
</compressed_observation>
```

### 5. Stop (Session Summary)

**When:** User pauses or stops asking questions

**Actions:**
1. Read transcript JSONL file
2. Extract last user and assistant messages
3. POST to `/api/sessions/summarize`
4. Generate structured summary (request, investigated, learned, completed, next_steps)
5. Store summary in `session_summaries` table
6. POST to `/api/processing` to stop UI spinner

**Summary Structure:**
```json
{
  "request": "Implement user authentication with JWT",
  "investigated": [
    "OAuth2 flow patterns",
    "JWT token expiration strategies",
    "Bcrypt hashing for passwords"
  ],
  "learned": [
    "Access tokens should expire in 1 hour",
    "Refresh tokens should expire in 7 days",
    "Need to implement token refresh endpoint"
  ],
  "completed": [
    "Login endpoint implemented in src/auth/login.js",
    "JWT signing and verification setup",
    "Password hashing with bcrypt"
  ],
  "next_steps": [
    "Implement token refresh endpoint",
    "Add role-based access control",
    "Write tests for authentication flow"
  ]
}
```

### 6. Session End (Cleanup)

**When:** Session closes (exit, clear, logout)

**Actions:**
1. POST to `/api/sessions/complete` with reason flag
2. Worker marks session as `completed` in database
3. Broadcast completion via SSE to update web viewer
4. Session data available for future context injection

---

## Hook-Based Architecture

### Hook Configuration (`hooks.json`)

```json
{
  "pre-hooks": [
    {
      "name": "smart-install",
      "description": "Verify dependencies before session start",
      "script": "scripts/smart-install.js"
    }
  ],
  "hooks": [
    {
      "name": "SessionStart",
      "script": "hooks/context-hook.js",
      "description": "Inject context from previous sessions"
    },
    {
      "name": "UserPromptSubmit",
      "script": "hooks/new-hook.js",
      "description": "Create session and save user prompt"
    },
    {
      "name": "PostToolUse",
      "script": "hooks/save-hook.js",
      "description": "Capture tool observations"
    },
    {
      "name": "Stop",
      "script": "hooks/summary-hook.js",
      "description": "Generate session summary"
    },
    {
      "name": "SessionEnd",
      "script": "hooks/cleanup-hook.js",
      "description": "Mark session as complete"
    }
  ]
}
```

### Hook Implementation Template

**Example: context-hook.js (SessionStart)**

```javascript
#!/usr/bin/env node
const WORKER_URL = 'http://localhost:37777';

async function main() {
  // 1. Health check worker
  const healthOk = await checkWorkerHealth();
  if (!healthOk) {
    await startWorker();
  }

  // 2. Get project name from working directory
  const project = getProjectName(process.cwd());

  // 3. Fetch context from worker
  const response = await fetch(
    `${WORKER_URL}/api/context/inject?project=${encodeURIComponent(project)}`
  );
  const contextData = await response.json();

  // 4. Output context as markdown (injected into Claude's context)
  console.log(contextData.markdown);
}

main().catch(console.error);
```

### Tools to Skip (Low Value)

```javascript
const SKIP_TOOLS = [
  'TodoWrite',           // Task management, not learning
  'AskUserQuestion',     // User interaction, not observation
  'EnterPlanMode',       // Mode switch, not data
  'ExitPlanMode',        // Mode switch, not data
  'TaskCreate',          // Task management
  'TaskUpdate',          // Task management
  'TaskList',            // Task management
];
```

---

## Database Schema

### SQLite Tables

#### 1. sdk_sessions

Stores metadata for each Claude Code session.

```sql
CREATE TABLE sdk_sessions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  claude_session_id TEXT UNIQUE NOT NULL,  -- From IDE
  project_name TEXT NOT NULL,
  first_prompt TEXT,
  prompt_count INTEGER DEFAULT 0,
  status TEXT DEFAULT 'initialized',  -- initialized/active/completed
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  completed_at DATETIME
);

CREATE INDEX idx_sessions_project ON sdk_sessions(project_name);
CREATE INDEX idx_sessions_status ON sdk_sessions(status);
```

**Idempotency Pattern:**
```sql
INSERT OR IGNORE INTO sdk_sessions (claude_session_id, project_name, first_prompt)
VALUES (?, ?, ?);
```

#### 2. user_prompts

Stores each user prompt submitted during a session.

```sql
CREATE TABLE user_prompts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id INTEGER NOT NULL,
  prompt_number INTEGER NOT NULL,
  prompt_text TEXT NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (session_id) REFERENCES sdk_sessions(id) ON DELETE CASCADE
);

CREATE INDEX idx_prompts_session ON user_prompts(session_id);
```

#### 3. observations

Stores tool execution observations with compressed summaries.

```sql
CREATE TABLE observations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id INTEGER NOT NULL,
  tool_name TEXT NOT NULL,
  tool_input TEXT,              -- Stripped of <private> tags
  tool_response TEXT,           -- Stripped of <private> tags
  compressed_observation TEXT,  -- Generated by Claude Agent SDK
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (session_id) REFERENCES sdk_sessions(id) ON DELETE CASCADE
);

CREATE INDEX idx_observations_session ON observations(session_id);
CREATE INDEX idx_observations_tool ON observations(tool_name);
CREATE INDEX idx_observations_created ON observations(created_at DESC);
```

#### 4. session_summaries

Stores structured summaries generated at the end of each session.

```sql
CREATE TABLE session_summaries (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id INTEGER NOT NULL UNIQUE,
  request TEXT,           -- What user requested
  investigated TEXT,      -- JSON array of investigation points
  learned TEXT,           -- JSON array of learnings
  completed TEXT,         -- JSON array of completed items
  next_steps TEXT,        -- JSON array of next steps
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (session_id) REFERENCES sdk_sessions(id) ON DELETE CASCADE
);
```

#### 5. observations_fts (FTS5 Virtual Table)

Full-text search index over observations.

```sql
CREATE VIRTUAL TABLE observations_fts USING fts5(
  observation_id UNINDEXED,
  tool_name,
  compressed_observation,
  content='observations',
  content_rowid='id'
);

-- Triggers to keep FTS in sync
CREATE TRIGGER observations_ai AFTER INSERT ON observations BEGIN
  INSERT INTO observations_fts(observation_id, tool_name, compressed_observation)
  VALUES (new.id, new.tool_name, new.compressed_observation);
END;

CREATE TRIGGER observations_ad AFTER DELETE ON observations BEGIN
  DELETE FROM observations_fts WHERE observation_id = old.id;
END;

CREATE TRIGGER observations_au AFTER UPDATE ON observations BEGIN
  UPDATE observations_fts
  SET tool_name = new.tool_name,
      compressed_observation = new.compressed_observation
  WHERE observation_id = new.id;
END;
```

### Database Configuration

```javascript
// SQLite configuration for optimal performance
const db = new Database('~/.claude-mem/memory.db', {
  // Write-Ahead Logging for better concurrency
  wal: true,

  // Optimize for speed
  pragma: {
    journal_mode: 'WAL',
    synchronous: 'NORMAL',
    cache_size: -64000,  // 64MB cache
    temp_store: 'MEMORY',
    mmap_size: 30000000000,  // 30GB mmap
  }
});
```

---

## Worker Service

### Architecture

The worker service runs as a separate Node/Bun process and handles:

1. **HTTP API** - Endpoints for hooks and search tools
2. **Queue Processing** - Async compression of observations
3. **Session Management** - CRUD operations on database
4. **Search Service** - Full-text and semantic search
5. **SSE Broadcasting** - Real-time updates to web viewer

### API Endpoints

#### Health Check
```
GET /api/health
Response: { status: "ok", uptime: 12345, sessions: 42 }
```

#### Context Injection
```
GET /api/context/inject?project={project}
Response: {
  markdown: "## Previous Session Context\n...",
  sessions: 10
}
```

#### Session Initialization
```
POST /api/sessions/{id}/init
Body: {
  "claude_session_id": "session_abc123",
  "project_name": "template-ai-team",
  "first_prompt": "Implement authentication"
}
Response: { session_id: 123 }
```

#### Save Observation
```
POST /api/sessions/observations
Body: {
  "session_id": 123,
  "tool_name": "Read",
  "tool_input": "src/auth/login.js",
  "tool_response": "// code..."
}
Response: { observation_id: 456, queued: true }
```

#### Generate Summary
```
POST /api/sessions/summarize
Body: {
  "session_id": 123,
  "last_user_message": "...",
  "last_assistant_message": "..."
}
Response: {
  "request": "...",
  "investigated": [...],
  "learned": [...],
  "completed": [...],
  "next_steps": [...]
}
```

#### Complete Session
```
POST /api/sessions/complete
Body: {
  "session_id": 123,
  "reason": "exit"
}
Response: { completed: true }
```

#### Search
```
POST /api/search
Body: {
  "query": "authentication JWT",
  "limit": 20,
  "project": "template-ai-team",
  "type": "Read"  // optional
}
Response: {
  "results": [
    { "id": 456, "title": "Read src/auth/login.js", "timestamp": "...", "type": "Read" }
  ]
}
```

#### Timeline
```
POST /api/timeline
Body: {
  "anchor_id": 456,  // or "query": "..."
  "before": 5,
  "after": 5
}
Response: {
  "observations": [...]  // Chronological context around anchor
}
```

#### Get Observations
```
POST /api/observations
Body: {
  "ids": [456, 457, 458]
}
Response: {
  "observations": [
    {
      "id": 456,
      "tool_name": "Read",
      "compressed_observation": "...",
      "timestamp": "..."
    }
  ]
}
```

### SDK Agent (Compression Engine)

The SDK Agent is an event-driven loop that processes queued observations:

```javascript
class SDKAgent {
  async processQueue() {
    while (true) {
      // 1. Dequeue observation
      const observation = await this.db.dequeueObservation();
      if (!observation) {
        await sleep(1000);
        continue;
      }

      // 2. Generate compression prompt
      const messages = this.generateCompressionPrompt(observation);

      // 3. Call Claude Agent SDK
      const response = await this.claudeSDK.sendMessage({
        model: 'claude-sonnet-4-5',
        max_tokens: 500,
        messages
      });

      // 4. Parse XML response
      const compressed = this.parseXML(response.content, 'compressed_observation');

      // 5. Store compressed observation
      await this.db.updateObservation(observation.id, {
        compressed_observation: compressed
      });

      // 6. Generate embedding and store in ChromaDB (optional)
      if (this.chromaDB) {
        const embedding = await this.generateEmbedding(compressed);
        await this.chromaDB.add({
          ids: [observation.id.toString()],
          documents: [compressed],
          embeddings: [embedding]
        });
      }

      // 7. Emit SSE event
      this.sse.emit('observation_compressed', {
        id: observation.id,
        compressed
      });
    }
  }

  generateCompressionPrompt(observation) {
    return [
      {
        role: 'user',
        content: `You are observing a tool execution. Compress this observation into 2-3 sentences focusing on what was learned, discovered, or changed.

Tool: ${observation.tool_name}
Input: ${observation.tool_input}
Response: ${observation.tool_response}

Provide output in XML:
<compressed_observation>
[Your 2-3 sentence summary]
</compressed_observation>`
      }
    ];
  }
}
```

### Worker Startup Script

```javascript
// scripts/worker-service.cjs
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const WORKER_DIR = path.join(process.env.HOME, '.claude-mem');
const LOG_FILE = path.join(WORKER_DIR, 'logs', `worker-${new Date().toISOString().split('T')[0]}.log`);
const PID_FILE = path.join(WORKER_DIR, 'worker.pid');

function startWorker() {
  // Ensure directories exist
  fs.mkdirSync(path.dirname(LOG_FILE), { recursive: true });

  // Spawn worker process
  const worker = spawn('node', ['plugin/dist/worker.js'], {
    detached: true,
    stdio: ['ignore', 'pipe', 'pipe']
  });

  // Write PID file
  fs.writeFileSync(PID_FILE, worker.pid.toString());

  // Redirect output to log file
  const logStream = fs.createWriteStream(LOG_FILE, { flags: 'a' });
  worker.stdout.pipe(logStream);
  worker.stderr.pipe(logStream);

  // Detach from parent process
  worker.unref();

  console.log(`Worker started with PID ${worker.pid}`);
}

function stopWorker() {
  if (fs.existsSync(PID_FILE)) {
    const pid = parseInt(fs.readFileSync(PID_FILE, 'utf8'));
    process.kill(pid);
    fs.unlinkSync(PID_FILE);
    console.log(`Worker stopped (PID ${pid})`);
  }
}

function checkWorkerHealth() {
  return fetch('http://localhost:37777/api/health')
    .then(res => res.ok)
    .catch(() => false);
}

// CLI
const command = process.argv[2];
if (command === 'start') startWorker();
else if (command === 'stop') stopWorker();
else if (command === 'restart') { stopWorker(); startWorker(); }
else if (command === 'status') {
  checkWorkerHealth().then(ok => {
    console.log(ok ? 'Worker is running' : 'Worker is not running');
  });
}
```

---

## Token-Efficient Search

### The Problem with Traditional RAG

Traditional retrieval-augmented generation (RAG) approaches fetch many observations upfront:

❌ **Traditional RAG:**
```
1. Semantic search → Top 50 results (500-1000 tokens each)
2. Load all 50 observations into context → 25,000-50,000 tokens
3. LLM reads everything to find relevant info
4. 90% of loaded context is irrelevant
```

**Result:** Wastes 25K-50K tokens per query

### Three-Layer Progressive Disclosure

✅ **Token-Efficient Approach:**

```
Layer 1: Search Index (50-100 tokens per result)
   ↓
Layer 2: Timeline Context (200-300 tokens per result)
   ↓
Layer 3: Full Details (500-1000 tokens per result)
```

**Result:** ~2,000-5,000 tokens total (10x reduction)

### Layer 1: Search Index

**Purpose:** Get a compact index of matching observations

**MCP Tool:** `search`

**Input:**
```json
{
  "query": "authentication JWT login",
  "limit": 20,
  "project": "template-ai-team",
  "type": "Read",
  "date_range": {
    "start": "2026-01-01",
    "end": "2026-02-03"
  },
  "order": "relevance"  // or "chronological"
}
```

**Output:**
```json
{
  "results": [
    { "id": 456, "title": "Read src/auth/login.js", "timestamp": "2026-02-01T10:30:00Z", "type": "Read" },
    { "id": 457, "title": "Write src/auth/jwt.js", "timestamp": "2026-02-01T10:35:00Z", "type": "Write" },
    { "id": 458, "title": "Bash npm install jsonwebtoken", "timestamp": "2026-02-01T10:32:00Z", "type": "Bash" }
  ],
  "total": 3
}
```

**Token Cost:** ~50-100 tokens per result × 20 results = 1,000-2,000 tokens

**Usage:**
- Claude sees compact list of observation IDs and titles
- Decides which are potentially relevant
- Moves to Layer 2 for selected observations

### Layer 2: Timeline Context

**Purpose:** Get chronological context around specific observations

**MCP Tool:** `timeline`

**Input:**
```json
{
  "anchor_id": 457,  // The observation to center on
  "before": 5,       // 5 observations before
  "after": 5         // 5 observations after
}
```

**OR using query:**
```json
{
  "query": "JWT token generation",
  "before": 5,
  "after": 5
}
```

**Output:**
```json
{
  "observations": [
    { "id": 452, "title": "Read package.json", "timestamp": "2026-02-01T10:25:00Z" },
    { "id": 453, "title": "Bash npm search jwt", "timestamp": "2026-02-01T10:27:00Z" },
    { "id": 456, "title": "Read src/auth/login.js", "timestamp": "2026-02-01T10:30:00Z" },
    { "id": 457, "title": "Write src/auth/jwt.js", "timestamp": "2026-02-01T10:35:00Z" },  // anchor
    { "id": 458, "title": "Bash npm test auth", "timestamp": "2026-02-01T10:40:00Z" },
    { "id": 459, "title": "Read test/auth.test.js", "timestamp": "2026-02-01T10:42:00Z" }
  ],
  "anchor_index": 3
}
```

**Token Cost:** ~200-300 tokens per observation × 11 observations = 2,200-3,300 tokens

**Usage:**
- Claude sees what happened before and after the target observation
- Understands the sequence of events
- Identifies which observations need full details

### Layer 3: Get Full Details

**Purpose:** Fetch complete observation data for final analysis

**MCP Tool:** `get_observations`

**Input:**
```json
{
  "ids": [456, 457, 458]
}
```

**Output:**
```json
{
  "observations": [
    {
      "id": 456,
      "session_id": 123,
      "tool_name": "Read",
      "tool_input": "src/auth/login.js",
      "tool_response": "// Full file contents...",
      "compressed_observation": "The login handler uses JWT tokens with bcrypt password hashing...",
      "timestamp": "2026-02-01T10:30:00Z"
    },
    {
      "id": 457,
      "session_id": 123,
      "tool_name": "Write",
      "tool_input": "src/auth/jwt.js",
      "tool_response": "// Full file contents...",
      "compressed_observation": "Created JWT utility module with sign and verify functions...",
      "timestamp": "2026-02-01T10:35:00Z"
    }
  ]
}
```

**Token Cost:** ~500-1,000 tokens per observation × 3 observations = 1,500-3,000 tokens

**Total Token Cost (All Layers):** ~4,700-8,300 tokens (vs 25K-50K traditional RAG)

### MCP Tool: `__IMPORTANT`

A special "always visible" tool that contains workflow documentation:

```json
{
  "name": "__IMPORTANT",
  "description": "ALWAYS READ THIS FIRST - Token-efficient search workflow",
  "schema": {
    "instructions": {
      "workflow": [
        "1. Start with search() to get compact index (50-100 tokens per result)",
        "2. Use timeline() for 3-5 most promising IDs to see chronological context",
        "3. Use get_observations() ONLY for final 1-3 observations you need full details on",
        "4. NEVER fetch full details without filtering through layers 1 and 2 first"
      ],
      "reasoning": "This three-layer approach reduces token consumption by ~10x compared to loading all observations upfront"
    }
  }
}
```

Claude always sees this tool and is reminded to follow the progressive disclosure pattern.

### Search Implementation (FTS5)

```javascript
class SessionSearch {
  // Full-text search using SQLite FTS5
  async search({ query, limit = 20, project, type, dateRange, order = 'relevance' }) {
    let sql = `
      SELECT
        o.id,
        o.tool_name || ' ' || SUBSTR(o.tool_input, 1, 50) as title,
        o.created_at as timestamp,
        o.tool_name as type,
        rank
      FROM observations_fts fts
      JOIN observations o ON fts.observation_id = o.id
      JOIN sdk_sessions s ON o.session_id = s.id
      WHERE observations_fts MATCH ?
    `;

    const params = [query];

    if (project) {
      sql += ` AND s.project_name = ?`;
      params.push(project);
    }

    if (type) {
      sql += ` AND o.tool_name = ?`;
      params.push(type);
    }

    if (dateRange) {
      sql += ` AND o.created_at BETWEEN ? AND ?`;
      params.push(dateRange.start, dateRange.end);
    }

    sql += order === 'relevance' ? ` ORDER BY rank` : ` ORDER BY o.created_at DESC`;
    sql += ` LIMIT ?`;
    params.push(limit);

    return this.db.prepare(sql).all(params);
  }

  // Timeline context around specific observation
  async timeline({ anchor_id, query, before = 5, after = 5 }) {
    // If query provided, find best matching observation first
    if (query && !anchor_id) {
      const results = await this.search({ query, limit: 1 });
      anchor_id = results[0]?.id;
    }

    if (!anchor_id) return { observations: [], anchor_index: -1 };

    // Get timestamp of anchor
    const anchor = this.db.prepare('SELECT created_at, session_id FROM observations WHERE id = ?').get(anchor_id);

    // Get observations before and after
    const observations = this.db.prepare(`
      SELECT
        id,
        tool_name || ' ' || SUBSTR(tool_input, 1, 50) as title,
        created_at as timestamp
      FROM observations
      WHERE session_id = ? AND (
        (created_at < ? ORDER BY created_at DESC LIMIT ?) OR
        (created_at >= ? ORDER BY created_at ASC LIMIT ?)
      )
      ORDER BY created_at ASC
    `).all(anchor.session_id, anchor.created_at, before, anchor.created_at, after + 1);

    // Find anchor index
    const anchor_index = observations.findIndex(o => o.id === anchor_id);

    return { observations, anchor_index };
  }

  // Get full observation details
  async getObservations({ ids }) {
    const placeholders = ids.map(() => '?').join(',');
    return this.db.prepare(`
      SELECT
        id,
        session_id,
        tool_name,
        tool_input,
        tool_response,
        compressed_observation,
        created_at as timestamp
      FROM observations
      WHERE id IN (${placeholders})
      ORDER BY created_at ASC
    `).all(ids);
  }
}
```

### Hybrid Search (FTS5 + ChromaDB)

For semantic search, combine FTS5 with vector embeddings:

```javascript
async hybridSearch({ query, limit = 20, alpha = 0.5 }) {
  // 1. FTS5 full-text search
  const ftsResults = await this.search({ query, limit: limit * 2 });
  const ftsScores = new Map(ftsResults.map((r, i) => [r.id, 1 - (i / ftsResults.length)]));

  // 2. ChromaDB semantic search
  const embedding = await this.generateEmbedding(query);
  const semanticResults = await this.chromaDB.query({
    queryEmbeddings: [embedding],
    nResults: limit * 2
  });
  const semanticScores = new Map(
    semanticResults.ids[0].map((id, i) => [parseInt(id), 1 - semanticResults.distances[0][i]])
  );

  // 3. Combine scores (weighted average)
  const allIds = new Set([...ftsScores.keys(), ...semanticScores.keys()]);
  const combined = Array.from(allIds).map(id => ({
    id,
    score: alpha * (ftsScores.get(id) || 0) + (1 - alpha) * (semanticScores.get(id) || 0)
  }));

  // 4. Sort by combined score and take top results
  combined.sort((a, b) => b.score - a.score);
  const topIds = combined.slice(0, limit).map(r => r.id);

  // 5. Fetch observation metadata
  return this.db.prepare(`
    SELECT
      id,
      tool_name || ' ' || SUBSTR(tool_input, 1, 50) as title,
      created_at as timestamp,
      tool_name as type
    FROM observations
    WHERE id IN (${topIds.map(() => '?').join(',')})
  `).all(topIds);
}
```

**Alpha Parameter:**
- `alpha = 1.0` → Pure FTS5 (keyword matching)
- `alpha = 0.5` → Balanced hybrid (default)
- `alpha = 0.0` → Pure semantic (meaning-based)

---

## Privacy and Security

### Privacy Tags

Users can wrap sensitive data in `<private>...</private>` tags:

```javascript
// User prompt
const prompt = `
Please deploy to production server.
<private>
Host: 192.168.1.100
Username: admin
Password: super_secret_123
</private>
`;
```

**Hook Processing:**
1. `UserPromptSubmit` hook strips `<private>` tags before saving
2. `PostToolUse` hook strips `<private>` from tool input/output
3. Only non-sensitive data sent to worker for compression
4. Privacy tags never stored in database

### Tag Stripping Implementation

```javascript
// src/utils/tag-stripping.ts

/**
 * Strip <private>...</private> tags from text
 */
export function stripPrivateTags(text: string): string {
  if (!text) return text;

  // Remove <private> content but preserve structure
  return text.replace(/<private>[\s\S]*?<\/private>/g, '[REDACTED]');
}

/**
 * Strip <claude-mem-context>...</claude-mem-context> tags
 * (prevents re-ingesting injected context)
 */
export function stripContextTags(text: string): string {
  if (!text) return text;

  return text.replace(/<claude-mem-context>[\s\S]*?<\/claude-mem-context>/g, '');
}

/**
 * Strip all memory-related tags
 */
export function stripAllMemoryTags(text: string): string {
  return stripContextTags(stripPrivateTags(text));
}
```

### System Tag: `<claude-mem-context>`

Context injected by the `SessionStart` hook is wrapped in this tag:

```markdown
<claude-mem-context>
## Previous Session Context (Last 10 sessions)

### Session 2026-02-01: Implemented User Authentication
...
</claude-mem-context>
```

**Purpose:** Prevent the plugin from re-ingesting its own injected context, which would create an infinite loop.

### Security Best Practices

1. **Local Storage Only** - All data stored locally in `~/.claude-mem/memory.db`
2. **No Cloud Sync** - No automatic sync to external services
3. **Privacy Tags** - Users control what gets stored
4. **API Keys Not Logged** - Skip tools that handle secrets
5. **Worker Port** - Only localhost (127.0.0.1), not 0.0.0.0
6. **File Permissions** - Database file readable only by user

```javascript
// Worker server configuration
const server = app.listen(37777, '127.0.0.1', () => {
  console.log('Worker listening on http://127.0.0.1:37777');
});
```

---

## Integration with Multi-Agent System

### How Persistent Memory Enhances Multi-Agent Workflows

The persistent memory architecture complements the multi-agent orchestration system in this template:

```
┌─────────────────────────────────────────────────────────────────┐
│                    PERSISTENT MEMORY LAYER                       │
│  (Shared knowledge base accessible by all agents)                │
└─────────────────────────────────────────────────────────────────┘
                              ↓ ↑
        ┌─────────────────────────────────────────────────┐
        │         Multi-Agent Orchestration                │
        └─────────────────────────────────────────────────┘
                 ↓              ↓             ↓              ↓
         Implementation     Code Review    Test Agent    Docs Agent
```

### Agent Memory Access Patterns

#### 1. Implementation Agent

**Memory Reads:**
- Previous implementation decisions for similar features
- Code patterns used in the project
- Past bugs encountered in related modules
- Dependencies installed and their configurations

**Memory Writes:**
- Files created/modified during implementation
- Dependencies installed via Bash tool
- Configuration changes made
- Implementation decisions and reasoning

**Example Query:**
```javascript
// Implementation Agent searches memory before starting
const context = await search({
  query: "authentication user login JWT implementation",
  project: "template-ai-team",
  type: "Write",  // Focus on previous implementations
  limit: 10
});

// "I see we implemented OAuth2 login in Session 2026-01-15.
//  Let me follow that same pattern with JWT tokens..."
```

#### 2. Code Review Agent

**Memory Reads:**
- Project coding standards and conventions
- Past code review feedback patterns
- Common issues found in reviews
- Security vulnerabilities previously identified

**Memory Writes:**
- Code review reports and findings
- Standards violations discovered
- Security issues identified
- Approved patterns confirmed

**Example Query:**
```javascript
// Code Review Agent checks past reviews for patterns
const pastReviews = await search({
  query: "code review authentication security",
  project: "template-ai-team",
  type: "Read",  // Reviews are typically Read operations
  limit: 5
});

// "Based on review Session 2026-01-20, we require bcrypt
//  with cost factor 12 for password hashing..."
```

#### 3. Test Agent

**Memory Reads:**
- Previous test scenarios for similar features
- Test data patterns used
- Past test failures and resolutions
- Integration test setup procedures

**Memory Writes:**
- Test files created
- Test execution results
- Test failures and debugging steps
- Integration test configurations

**Example Query:**
```javascript
// Test Agent searches for previous test patterns
const testPatterns = await search({
  query: "test authentication login JWT mock",
  project: "template-ai-team",
  limit: 10
});

// "I see Session 2026-01-22 created comprehensive auth tests
//  with mocked JWT verification. I'll follow that structure..."
```

#### 4. Documentation Agent

**Memory Reads:**
- Documentation structure and templates
- Previously documented API endpoints
- Terminology and naming conventions
- User-facing feature descriptions

**Memory Writes:**
- Documentation files created/updated
- API documentation additions
- Architecture diagrams
- Troubleshooting guides

**Example Query:**
```javascript
// Documentation Agent checks existing docs structure
const docStructure = await search({
  query: "documentation API endpoint authentication",
  project: "template-ai-team",
  type: "Write",  // Focus on doc file writes
  limit: 10
});

// "Based on Session 2026-01-25, API docs follow OpenAPI 3.0
//  format with examples in docs/api/..."
```

### Cross-Agent Knowledge Sharing

**Scenario:** Implementation Agent creates new API endpoint

```
Session 2026-02-03 - Implementation Agent:
┌────────────────────────────────────────────────────────────┐
│ Write: src/api/auth/refresh-token.js                      │
│ Compressed: "Created token refresh endpoint that accepts  │
│ refresh tokens and returns new access tokens with 1-hour  │
│ expiration. Uses JWT verify to validate refresh tokens."  │
└────────────────────────────────────────────────────────────┘
                          ↓
              [Stored in persistent memory]
                          ↓
┌────────────────────────────────────────────────────────────┐
│ Future Session - Code Review Agent                        │
│ Searches: "refresh token endpoint JWT"                    │
│ Finds: Session 2026-02-03 implementation details          │
│ Reviews: Checks against security standards learned from   │
│          Session 2026-01-20 (refresh token expiration)    │
└────────────────────────────────────────────────────────────┘
                          ↓
┌────────────────────────────────────────────────────────────┐
│ Future Session - Test Agent                               │
│ Searches: "test refresh token endpoint"                   │
│ Finds: Both implementation and review context             │
│ Creates: Comprehensive tests based on learned patterns    │
└────────────────────────────────────────────────────────────┘
                          ↓
┌────────────────────────────────────────────────────────────┐
│ Future Session - Documentation Agent                      │
│ Searches: "refresh token endpoint API documentation"      │
│ Finds: Implementation, review, and test context           │
│ Writes: Complete API docs with examples from tests        │
└────────────────────────────────────────────────────────────┘
```

### Task-Specific Memory Injection

Integrate with the task tracking system:

```javascript
// SessionStart hook enhancement
async function injectContext() {
  // 1. Get current task from docs/tasks/TASK-XXX.md
  const currentTask = await getCurrentTask();

  // 2. Search memory for related context
  const context = await search({
    query: currentTask.title + ' ' + currentTask.tags.join(' '),
    project: currentTask.project,
    limit: 10
  });

  // 3. Get timeline for most relevant observations
  const timeline = await getTimeline({
    anchor_id: context.results[0].id,
    before: 3,
    after: 3
  });

  // 4. Inject as markdown
  console.log(`
<claude-mem-context>
## Task Context: ${currentTask.id} - ${currentTask.title}

### Related Previous Work:
${formatContext(context, timeline)}

### Current Task Details:
- **Status**: ${currentTask.status}
- **Assigned**: ${currentTask.assigned}
- **Priority**: ${currentTask.priority}
- **Tags**: ${currentTask.tags.join(', ')}

### Task Description:
${currentTask.description}
</claude-mem-context>
  `);
}
```

### Agent Handoff with Memory

When agents hand off tasks, they can reference memory:

```markdown
## Handoff: Implementation → Code Review

**Task:** TASK-001 - Implement User Authentication

**Implementation Summary:**
- Created login endpoint in src/auth/login.js (Session 2026-02-03, Observation #456)
- Installed jsonwebtoken and bcrypt packages (Session 2026-02-03, Observation #458)
- Configured JWT signing with RS256 algorithm (Session 2026-02-03, Observation #460)

**Memory References:**
- Search "authentication JWT login" to see full implementation details
- Timeline around Observation #457 shows the complete implementation sequence
- Previous auth implementation in Session 2026-01-15 used similar pattern

**Ready for Review:**
All unit tests passing (100% coverage). Please review against security standards from Session 2026-01-20.
```

### Memory-Enhanced Task Status Updates

Update task files with memory references:

```markdown
## TASK-001: Implement User Authentication

**Status:** IN_REVIEW
**Assigned:** Code Review Agent
**Priority:** High

### Implementation Notes

✅ **Completed:**
- Login endpoint created ([Memory: Observation #456](http://localhost:37777/observation/456))
- JWT token generation ([Memory: Observation #457](http://localhost:37777/observation/457))
- Password hashing with bcrypt ([Memory: Observation #459](http://localhost:37777/observation/459))

### Lessons Learned

Reference Memory Session 2026-02-03 for:
- JWT configuration decisions (access token: 1h, refresh token: 7d)
- Bcrypt cost factor selection (12 for balance of security/performance)
- Token signing algorithm choice (RS256 for asymmetric keys)
```

---

## Implementation Guide

### Step 1: Project Setup

```bash
# 1. Create project structure
mkdir -p ~/.claude-mem/{logs,data}

# 2. Initialize package.json
npm init -y

# 3. Install dependencies
npm install express better-sqlite3 chromadb @anthropic-ai/sdk

# 4. Create directories
mkdir -p src/{hooks,services,utils,api}
mkdir -p plugin/{hooks,scripts,dist}
mkdir -p tests
```

### Step 2: Database Setup

```javascript
// src/services/database.ts
import Database from 'better-sqlite3';
import path from 'path';
import os from 'os';

export class MemoryDatabase {
  private db: Database.Database;

  constructor() {
    const dbPath = path.join(os.homedir(), '.claude-mem', 'data', 'memory.db');
    this.db = new Database(dbPath, {
      verbose: console.log
    });

    // Enable WAL mode
    this.db.pragma('journal_mode = WAL');
    this.db.pragma('synchronous = NORMAL');
    this.db.pragma('cache_size = -64000');

    this.initSchema();
  }

  private initSchema() {
    // Create tables (see Database Schema section)
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS sdk_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        claude_session_id TEXT UNIQUE NOT NULL,
        project_name TEXT NOT NULL,
        first_prompt TEXT,
        prompt_count INTEGER DEFAULT 0,
        status TEXT DEFAULT 'initialized',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        completed_at DATETIME
      );

      CREATE TABLE IF NOT EXISTS user_prompts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER NOT NULL,
        prompt_number INTEGER NOT NULL,
        prompt_text TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (session_id) REFERENCES sdk_sessions(id) ON DELETE CASCADE
      );

      CREATE TABLE IF NOT EXISTS observations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER NOT NULL,
        tool_name TEXT NOT NULL,
        tool_input TEXT,
        tool_response TEXT,
        compressed_observation TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (session_id) REFERENCES sdk_sessions(id) ON DELETE CASCADE
      );

      CREATE TABLE IF NOT EXISTS session_summaries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER NOT NULL UNIQUE,
        request TEXT,
        investigated TEXT,
        learned TEXT,
        completed TEXT,
        next_steps TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (session_id) REFERENCES sdk_sessions(id) ON DELETE CASCADE
      );

      -- FTS5 virtual table
      CREATE VIRTUAL TABLE IF NOT EXISTS observations_fts USING fts5(
        observation_id UNINDEXED,
        tool_name,
        compressed_observation,
        content='observations',
        content_rowid='id'
      );

      -- Indexes
      CREATE INDEX IF NOT EXISTS idx_sessions_project ON sdk_sessions(project_name);
      CREATE INDEX IF NOT EXISTS idx_observations_session ON observations(session_id);
      CREATE INDEX IF NOT EXISTS idx_observations_created ON observations(created_at DESC);
    `);

    // FTS5 triggers
    this.setupFTSTriggers();
  }

  private setupFTSTriggers() {
    this.db.exec(`
      CREATE TRIGGER IF NOT EXISTS observations_ai AFTER INSERT ON observations BEGIN
        INSERT INTO observations_fts(observation_id, tool_name, compressed_observation)
        VALUES (new.id, new.tool_name, new.compressed_observation);
      END;

      CREATE TRIGGER IF NOT EXISTS observations_ad AFTER DELETE ON observations BEGIN
        DELETE FROM observations_fts WHERE observation_id = old.id;
      END;

      CREATE TRIGGER IF NOT EXISTS observations_au AFTER UPDATE ON observations BEGIN
        UPDATE observations_fts
        SET tool_name = new.tool_name,
            compressed_observation = new.compressed_observation
        WHERE observation_id = new.id;
      END;
    `);
  }

  // Session methods
  createSession(claudeSessionId: string, projectName: string, firstPrompt: string) {
    const stmt = this.db.prepare(`
      INSERT OR IGNORE INTO sdk_sessions (claude_session_id, project_name, first_prompt)
      VALUES (?, ?, ?)
    `);
    stmt.run(claudeSessionId, projectName, firstPrompt);

    return this.db.prepare('SELECT * FROM sdk_sessions WHERE claude_session_id = ?').get(claudeSessionId);
  }

  // ... more methods (see full implementation in Worker Service section)
}
```

### Step 3: Worker Service

```javascript
// src/services/worker-service.ts
import express from 'express';
import { MemoryDatabase } from './database';
import { SDKAgent } from './sdk-agent';
import { SessionSearch } from './session-search';

export class WorkerService {
  private app = express();
  private db = new MemoryDatabase();
  private agent = new SDKAgent(this.db);
  private search = new SessionSearch(this.db);

  constructor() {
    this.setupMiddleware();
    this.setupRoutes();
  }

  private setupMiddleware() {
    this.app.use(express.json({ limit: '10mb' }));
    this.app.use((req, res, next) => {
      console.log(`${new Date().toISOString()} ${req.method} ${req.url}`);
      next();
    });
  }

  private setupRoutes() {
    // Health check
    this.app.get('/api/health', (req, res) => {
      res.json({ status: 'ok', uptime: process.uptime() });
    });

    // Context injection
    this.app.get('/api/context/inject', async (req, res) => {
      const { project } = req.query;
      const markdown = await this.generateContextMarkdown(project as string);
      res.json({ markdown });
    });

    // Session init
    this.app.post('/api/sessions/:id/init', async (req, res) => {
      const { claude_session_id, project_name, first_prompt } = req.body;
      const session = this.db.createSession(claude_session_id, project_name, first_prompt);
      res.json({ session_id: session.id });
    });

    // Save observation
    this.app.post('/api/sessions/observations', async (req, res) => {
      const observation = await this.db.saveObservation(req.body);
      res.json({ observation_id: observation.id, queued: true });
    });

    // Search
    this.app.post('/api/search', async (req, res) => {
      const results = await this.search.search(req.body);
      res.json({ results });
    });

    // Timeline
    this.app.post('/api/timeline', async (req, res) => {
      const results = await this.search.timeline(req.body);
      res.json(results);
    });

    // Get observations
    this.app.post('/api/observations', async (req, res) => {
      const observations = await this.search.getObservations(req.body);
      res.json({ observations });
    });
  }

  private async generateContextMarkdown(project: string): Promise<string> {
    const sessions = this.db.getRecentSessions(project, 10);
    let markdown = '<claude-mem-context>\n';
    markdown += '## Previous Session Context (Last 10 sessions)\n\n';

    for (const session of sessions) {
      const summary = this.db.getSessionSummary(session.id);
      if (summary) {
        markdown += `### Session ${session.created_at}: ${summary.request}\n`;
        markdown += `- **Investigated**: ${JSON.parse(summary.investigated).join(', ')}\n`;
        markdown += `- **Learned**: ${JSON.parse(summary.learned).join(', ')}\n`;
        markdown += `- **Completed**: ${JSON.parse(summary.completed).join(', ')}\n`;
        markdown += `- **Next**: ${JSON.parse(summary.next_steps).join(', ')}\n\n`;
      }
    }

    markdown += '</claude-mem-context>';
    return markdown;
  }

  start() {
    this.app.listen(37777, '127.0.0.1', () => {
      console.log('Worker service listening on http://127.0.0.1:37777');
    });

    // Start SDK agent queue processor
    this.agent.start();
  }
}

// Start worker
if (require.main === module) {
  const worker = new WorkerService();
  worker.start();
}
```

### Step 4: Hooks Implementation

```javascript
// plugin/hooks/context-hook.js (SessionStart)
#!/usr/bin/env node
const WORKER_URL = 'http://localhost:37777';

async function checkHealth() {
  try {
    const res = await fetch(`${WORKER_URL}/api/health`);
    return res.ok;
  } catch {
    return false;
  }
}

async function injectContext() {
  // Check worker health
  const healthy = await checkHealth();
  if (!healthy) {
    console.error('Worker service not responding. Start with: npm run worker:start');
    return;
  }

  // Get project name
  const project = process.cwd().split('/').pop();

  // Fetch context
  const res = await fetch(`${WORKER_URL}/api/context/inject?project=${encodeURIComponent(project)}`);
  const data = await res.json();

  // Output context (injected into Claude's context)
  console.log(data.markdown);
}

injectContext().catch(console.error);
```

```javascript
// plugin/hooks/save-hook.js (PostToolUse)
#!/usr/bin/env node
const WORKER_URL = 'http://localhost:37777';

const SKIP_TOOLS = ['TodoWrite', 'AskUserQuestion', 'TaskCreate', 'TaskUpdate'];

function stripPrivateTags(text) {
  if (!text) return text;
  return text.replace(/<private>[\s\S]*?<\/private>/g, '[REDACTED]');
}

async function saveObservation() {
  // Read tool use from stdin
  const toolUse = JSON.parse(await readStdin());

  // Skip low-value tools
  if (SKIP_TOOLS.includes(toolUse.tool_name)) {
    return;
  }

  // Strip privacy tags
  const observation = {
    session_id: process.env.CLAUDE_SESSION_ID,
    tool_name: toolUse.tool_name,
    tool_input: stripPrivateTags(toolUse.input),
    tool_response: stripPrivateTags(toolUse.output)
  };

  // Post to worker (fire and forget)
  fetch(`${WORKER_URL}/api/sessions/observations`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(observation)
  }).catch(() => {});  // Ignore errors, don't block
}

async function readStdin() {
  const chunks = [];
  for await (const chunk of process.stdin) chunks.push(chunk);
  return Buffer.concat(chunks).toString();
}

saveObservation();
```

### Step 5: MCP Server for Search Tools

```javascript
// plugin/scripts/mcp-server.cjs
#!/usr/bin/env node
const WORKER_URL = 'http://localhost:37777';

// MCP protocol handler
const tools = {
  search: {
    description: 'Search observations (Layer 1: Compact index)',
    inputSchema: {
      type: 'object',
      properties: {
        query: { type: 'string' },
        limit: { type: 'number', default: 20 },
        project: { type: 'string' },
        type: { type: 'string' }
      },
      required: ['query']
    },
    handler: async (params) => {
      const res = await fetch(`${WORKER_URL}/api/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(params)
      });
      return await res.json();
    }
  },

  timeline: {
    description: 'Get chronological context (Layer 2: Timeline)',
    inputSchema: {
      type: 'object',
      properties: {
        anchor_id: { type: 'number' },
        query: { type: 'string' },
        before: { type: 'number', default: 5 },
        after: { type: 'number', default: 5 }
      }
    },
    handler: async (params) => {
      const res = await fetch(`${WORKER_URL}/api/timeline`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(params)
      });
      return await res.json();
    }
  },

  get_observations: {
    description: 'Get full observation details (Layer 3: Full details)',
    inputSchema: {
      type: 'object',
      properties: {
        ids: { type: 'array', items: { type: 'number' } }
      },
      required: ['ids']
    },
    handler: async (params) => {
      const res = await fetch(`${WORKER_URL}/api/observations`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(params)
      });
      return await res.json();
    }
  },

  __IMPORTANT: {
    description: 'ALWAYS READ FIRST - Token-efficient workflow',
    inputSchema: {
      type: 'object',
      properties: {
        instructions: {
          type: 'object',
          properties: {
            workflow: {
              type: 'array',
              items: { type: 'string' },
              default: [
                '1. Start with search() to get compact index',
                '2. Use timeline() for context around promising results',
                '3. Use get_observations() ONLY for final details',
                '4. NEVER fetch full details without filtering first'
              ]
            }
          }
        }
      }
    },
    handler: async () => ({
      workflow: [
        '1. Start with search() to get compact index (50-100 tokens per result)',
        '2. Use timeline() for 3-5 most promising IDs to see chronological context',
        '3. Use get_observations() ONLY for final 1-3 observations you need',
        '4. This approach reduces token consumption by ~10x'
      ]
    })
  }
};

// JSON-RPC handler
process.stdin.on('data', async (data) => {
  const request = JSON.parse(data.toString());

  if (request.method === 'tools/list') {
    process.stdout.write(JSON.stringify({
      jsonrpc: '2.0',
      id: request.id,
      result: { tools: Object.keys(tools).map(name => ({ name, ...tools[name] })) }
    }));
  } else if (request.method === 'tools/call') {
    const { name, arguments: params } = request.params;
    const result = await tools[name].handler(params);
    process.stdout.write(JSON.stringify({
      jsonrpc: '2.0',
      id: request.id,
      result: { content: [{ type: 'text', text: JSON.stringify(result, null, 2) }] }
    }));
  }
});
```

### Step 6: Configuration Files

**package.json:**
```json
{
  "name": "claude-mem",
  "version": "1.0.0",
  "scripts": {
    "worker:start": "node plugin/scripts/worker-service.cjs start",
    "worker:stop": "node plugin/scripts/worker-service.cjs stop",
    "worker:restart": "node plugin/scripts/worker-service.cjs restart",
    "worker:status": "node plugin/scripts/worker-service.cjs status"
  },
  "dependencies": {
    "express": "^4.18.2",
    "better-sqlite3": "^9.2.2",
    "chromadb": "^1.7.3",
    "@anthropic-ai/sdk": "^0.14.0"
  }
}
```

**plugin/hooks/hooks.json:**
```json
{
  "pre-hooks": [
    {
      "name": "smart-install",
      "script": "scripts/smart-install.js",
      "description": "Verify dependencies"
    }
  ],
  "hooks": [
    {
      "name": "SessionStart",
      "script": "hooks/context-hook.js",
      "description": "Inject context from previous sessions"
    },
    {
      "name": "UserPromptSubmit",
      "script": "hooks/new-hook.js",
      "description": "Create session and save prompt"
    },
    {
      "name": "PostToolUse",
      "script": "hooks/save-hook.js",
      "description": "Capture tool observations"
    },
    {
      "name": "Stop",
      "script": "hooks/summary-hook.js",
      "description": "Generate session summary"
    },
    {
      "name": "SessionEnd",
      "script": "hooks/cleanup-hook.js",
      "description": "Mark session complete"
    }
  ]
}
```

---

## Best Practices

### 1. Token Optimization

✅ **DO:**
- Always use three-layer search workflow
- Filter to 3-5 observations before fetching full details
- Use compressed observations instead of full tool responses
- Implement progressive disclosure pattern

❌ **DON'T:**
- Fetch full details for all search results upfront
- Load entire session history into context
- Skip the search index layer
- Request observations without timeline context

### 2. Privacy and Security

✅ **DO:**
- Educate users about `<private>` tags
- Strip privacy tags at the earliest point (hooks)
- Store database locally only
- Bind worker to localhost (127.0.0.1)
- Skip tools that handle secrets (API keys, credentials)

❌ **DON'T:**
- Log sensitive data even temporarily
- Sync database to cloud without encryption
- Expose worker on 0.0.0.0 (all interfaces)
- Store raw API keys or credentials

### 3. Performance

✅ **DO:**
- Enable SQLite WAL mode for concurrency
- Use FTS5 for full-text search (not LIKE queries)
- Implement observation queue (async processing)
- Fire-and-forget for observation saves (don't block)
- Cache recent session data in memory

❌ **DON'T:**
- Block main session waiting for compression
- Query without indexes
- Process observations synchronously
- Load entire database into memory

### 4. Compression Quality

✅ **DO:**
- Use Claude Agent SDK for compression (not cheaper models)
- Aim for 2-3 sentence compressions
- Focus on learnings, not just facts
- Include "why" decisions were made
- Preserve technical details (library names, versions)

❌ **DON'T:**
- Over-compress (lose important context)
- Under-compress (waste tokens)
- Skip compression for large observations
- Use non-AI compression (loses meaning)

### 5. Observation Capture

✅ **DO:**
- Capture Read, Write, Bash, Grep, Edit tools
- Skip low-value tools (TodoWrite, AskUserQuestion)
- Strip privacy tags before saving
- Include tool name, input, and response
- Timestamp everything

❌ **DON'T:**
- Capture every tool indiscriminately
- Save observations without compression
- Ignore tool context (just save output)
- Skip timestamps

### 6. Context Injection

✅ **DO:**
- Inject last 10 sessions maximum
- Use session summaries (not raw observations)
- Filter by project name
- Wrap in `<claude-mem-context>` tags
- Make injection silent (no user-visible output)

❌ **DON'T:**
- Inject all historical sessions
- Use raw observations instead of summaries
- Mix projects in context
- Show injection to user (clutters output)

### 7. Search Queries

✅ **DO:**
- Use descriptive multi-word queries
- Include project name for filtering
- Specify tool type when relevant
- Use date ranges for recent work
- Combine FTS5 with semantic search (hybrid)

❌ **DON'T:**
- Use single-word queries (too broad)
- Search across all projects
- Ignore tool type (gets irrelevant results)
- Only use keyword matching (misses semantic meaning)

### 8. Multi-Agent Coordination

✅ **DO:**
- Share memory across all agent roles
- Reference memory in handoffs
- Link observations in task files
- Use memory to maintain consistency
- Search for similar past work before starting

❌ **DON'T:**
- Create separate memory per agent
- Forget to check memory before implementing
- Duplicate work already done
- Ignore lessons learned from past sessions

### 9. Testing and Debugging

✅ **DO:**
- Test worker health checks
- Verify privacy tag stripping
- Test FTS5 search queries
- Check compression quality regularly
- Monitor worker logs

❌ **DON'T:**
- Skip testing privacy features
- Assume worker is always running
- Ignore compression failures
- Leave debug logging in production

### 10. Documentation

✅ **DO:**
- Document custom MCP tools
- Explain three-layer workflow to users
- Provide example queries
- Document privacy tag usage
- Keep architecture docs updated

❌ **DON'T:**
- Assume users understand MCP
- Skip workflow documentation
- Hide internal architecture
- Forget to update docs when changing schema

---

## Conclusion

This persistent memory architecture enables AI agents to:

✅ **Remember** across sessions
✅ **Learn** from past work
✅ **Share** knowledge between agents
✅ **Search** efficiently with tokens
✅ **Protect** sensitive data

By implementing this template in your AI agent projects, you create agents that truly evolve and improve over time rather than starting from zero each session.

---

## Further Reading

- **Source Documentation:** VISSoft Confluence Page 147621929
- **Claude-Mem Repository:** https://github.com/thedotmack/claude-mem
- **Claude Agent SDK:** https://github.com/anthropics/anthropic-sdk-typescript
- **Model Context Protocol (MCP):** https://modelcontextprotocol.io
- **SQLite FTS5:** https://www.sqlite.org/fts5.html
- **ChromaDB:** https://docs.trychroma.com

---

**Last Updated:** 2026-02-03
**Version:** 1.0
**Status:** Template Documentation
