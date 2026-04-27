# Using Persistent Memory in Claude Code

## What is Persistent Memory?

Persistent Memory allows Claude Code to **remember context across sessions**. Instead of starting fresh each time, Claude can:

✅ **Recall past work** - Remember previous implementations, decisions, and patterns
✅ **Learn from history** - Avoid repeating mistakes and leverage successful approaches
✅ **Share knowledge** - Enable memory across different agent roles (Implementation, Review, Test, Documentation)
✅ **Search efficiently** - Token-optimized three-layer search reduces context usage by 10x
✅ **Protect privacy** - Strip sensitive data automatically with `<private>` tags
✅ **🆕 Team Sharing** - Deploy remote server for centralized memory across team members

## Deployment Modes

The persistent memory system supports **two deployment modes**:

### 🖥️ Local Mode (Default)
- **Setup**: Zero configuration (works out of the box)
- **Best for**: Individual developers, single machines, personal projects
- **Database**: Local SQLite at `~/.claude-mem/memory.db`
- **Worker**: Runs locally on `http://localhost:37777`
- **Memory**: Private to your machine
- **API Key**: Your own Anthropic API key
- **Cost**: ~$15-30/month per developer

### 🌐 Remote Mode (Enterprise)
- **Setup**: One-time server deployment (20 minutes)
- **Best for**: Teams, multiple machines, shared context
- **Database**: Centralized SQLite on remote server
- **Worker**: Runs on company server (e.g., `http://memory.company.com:37777`)
- **Memory**: Shared across team members
- **API Key**: Single team Anthropic API key (50-90% cost savings)
- **Cost**: ~$150-300/month for entire team (shared)
- **Features**: Access from any machine, centralized backups, team-wide knowledge sharing

**This guide covers Local Mode usage. For Remote Mode deployment, see:**
- **🆕 [Remote Memory Deployment Guide](remote-memory-deployment.md)** - Complete server setup, team rollout, migration
- **🆕 [deployment/DEPLOYMENT-TOMORROW.md](../../deployment/DEPLOYMENT-TOMORROW.md)** - Step-by-step deployment checklist
- **🆕 [deployment/QUICK-START.md](../../deployment/QUICK-START.md)** - 15-minute quick setup

## How It Works

### Session Lifecycle

Every time you start Claude Code in a project with this template:

1. **SessionStart Hook** - Checks if worker service is running, starts it if needed
2. **Context Injection** - Fetches relevant past observations and injects into Claude's context
3. **Work Session** - Claude uses past knowledge to inform current work
4. **Observation Capture** - PostToolUse hook captures Read, Write, Edit, Bash, Grep, Glob operations
5. **AI Compression** - Background worker compresses observations into learnings (fire-and-forget)
6. **Session Summary** - Stop hook generates session summary with key decisions and next steps

### What Gets Captured

The system automatically captures:
- **File operations**: Read, Write, Edit operations with file paths and content
- **Search operations**: Grep, Glob patterns and results
- **Command execution**: Bash commands and outputs (sanitized)
- **User prompts**: Your questions and instructions to Claude
- **Session summaries**: High-level overview of work completed

**What does NOT get captured:**
- TodoWrite operations (task tracking)
- AskUserQuestion interactions (temporary decisions)
- TaskCreate/TaskUpdate operations (task management)
- Files in `.env`, `secrets/`, `*.key`, `*.pem` (automatically blocked)

### Privacy Protection

The system automatically strips sensitive data:

```markdown
This is public information.

<private>
API_KEY=sk-1234567890abcdef
DATABASE_PASSWORD=super_secret_pass
</private>

This is also public.
```

**Result stored in database:**
```markdown
This is public information.

[REDACTED]

This is also public.
```

**Privacy tags are removed at multiple layers:**
1. Hook level - Before sending to worker service
2. Database level - Before storing in SQLite
3. Search level - Before returning results to Claude

## Searching Memory

### Basic Search with /memory-search

Search through past observations across all sessions:

```bash
# Basic search
/memory-search "authentication JWT"

# Search specific tool type
/memory-search "database migration" --type Bash

# Limit results
/memory-search "API endpoint" --limit 5

# Search specific project
/memory-search "bug fix" --project my-project
```

### Three-Layer Search Workflow

The system uses a **token-efficient three-layer approach**:

**Layer 1: Index Search (50-100 tokens per result)**
```
Search for: "user authentication"
Results: 15 observations found
- Observation #1: Implemented JWT auth middleware [2026-01-15]
- Observation #2: Fixed login session bug [2026-01-20]
- Observation #3: Added password hashing [2026-01-22]
...
```

**Layer 2: Timeline Context (200-300 tokens per result)**
```
Timeline for observation #1, #3:
[2026-01-15 10:30] Session started: Implement authentication
[2026-01-15 10:45] Read: src/middleware/auth.js
[2026-01-15 11:00] Write: src/middleware/jwt.js (JWT verification)
[2026-01-15 11:30] Bash: npm test -- auth.test.js (all passed)
[2026-01-15 11:45] Session summary: JWT auth complete, tests passing
```

**Layer 3: Full Details (500-1000 tokens per result)**
```
Observation #1 details:
Tool: Write
File: src/middleware/jwt.js
Content:
import jwt from 'jsonwebtoken';

export function verifyToken(req, res, next) {
  const token = req.headers.authorization?.split(' ')[1];
  if (!token) return res.status(401).json({ error: 'No token provided' });

  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    req.user = decoded;
    next();
  } catch (err) {
    return res.status(401).json({ error: 'Invalid token' });
  }
}

Compressed Learning:
"Implemented JWT middleware with token extraction from Authorization header,
verification using jsonwebtoken library, and error handling for missing/invalid tokens.
Stores decoded user info in req.user for downstream middleware."
```

**Why three layers?**
- Start with compact index to scan many results quickly
- Expand to timeline for context around interesting observations
- Dive deep into full details only for the most relevant 1-3 observations
- **Result: 10x token savings** compared to loading all details upfront

### Using MCP Tools Directly

For advanced users, you can use MCP tools directly in your prompts:

```markdown
Search for past authentication work:
- Use MCP tool: search
- Query: "JWT authentication"
- Project: template-ai-team
- Limit: 10

Get timeline around observation #42:
- Use MCP tool: timeline
- Observation IDs: [42]
- Window: 5 observations before/after

Get full details for observations #42, #45:
- Use MCP tool: get_observations
- Observation IDs: [42, 45]
```

## Managing Memory

### Clearing Memory

Clear memory for current project or all projects:

```bash
# Clear current project only
/memory-clear

# Clear all projects (requires confirmation)
/memory-clear --all
```

**Safety features:**
- Current project only by default
- Confirmation required for `--all` flag
- Cannot be undone (backup database first if unsure)

**Database location:** `~/.claude-mem/memory.db` (or `%USERPROFILE%\.claude-mem\memory.db` on Windows)

**Backup before clearing:**
```bash
# macOS/Linux
cp ~/.claude-mem/memory.db ~/.claude-mem/memory.db.backup

# Windows PowerShell
Copy-Item "$env:USERPROFILE\.claude-mem\memory.db" "$env:USERPROFILE\.claude-mem\memory.db.backup"
```

### Exporting Memory

Export memory to markdown for review, backup, or sharing:

```bash
# Export current project to default file
/memory-export

# Export to custom location
/memory-export --file reports/memory-backup.md

# Export specific project
/memory-export --project my-project

# Export with date range
/memory-export --from 2026-01-01 --to 2026-02-01
```

**Output format:**
```markdown
# Memory Export: template-ai-team

## Session: 2026-01-15 10:30 - 11:45
**Summary:** Implemented JWT authentication middleware

### Key Observations
- Implemented token verification in src/middleware/jwt.js
- Added error handling for missing/invalid tokens
- All tests passing

### Decisions Made
- Used jsonwebtoken library for JWT operations
- Stored decoded user in req.user for downstream access
- 401 status for authentication failures

### Next Steps
- Add refresh token rotation
- Implement rate limiting for auth endpoints

---

## Session: 2026-01-20 14:00 - 15:30
**Summary:** Fixed login session bug
...
```

## Advanced Usage

### Worker Service Management

The worker service runs in the background and handles:
- AI-powered observation compression (using Claude Sonnet 4.5)
- Context injection for new sessions
- Search API for memory queries

**Manual worker control:**

```bash
# Check worker status
node scripts/worker-service.js status

# Start worker manually
node scripts/worker-service.js start

# Stop worker
node scripts/worker-service.js stop

# Restart worker
node scripts/worker-service.js restart
```

**Worker API endpoints:**
- `http://localhost:37777/api/health` - Health check
- `http://localhost:37777/api/context/inject?project=NAME` - Get context markdown
- `http://localhost:37777/api/search` - Search observations
- `http://localhost:37777/api/timeline` - Get timeline context
- `http://localhost:37777/api/observations` - Get full observation details

### MCP Server Configuration (.mcp.json)

Add the `claude-mem` entry to your project's `.mcp.json` file.

**Remote Mode (connect to team worker server):**
```json
{
  "mcpServers": {
    "claude-mem": {
      "command": "node",
      "args": ["mcp-servers/claude-mem-server/dist/index.js"],
      "env": {
        "WORKER_URL": "http://10.10.100.22:37777",
        "API_KEY": "${MEMORY_API_KEY}"
      },
      "disabled": false,
      "alwaysAllow": ["search", "timeline", "get_observations", "__IMPORTANT"]
    }
  }
}
```

- `WORKER_URL` - Remote worker server address (get from team lead)
- `API_KEY` - Authentication key resolved from `MEMORY_API_KEY` environment variable
- `alwaysAllow` - Auto-approve search tools so memory works without manual approval each time

**Local Mode (worker runs on your machine):**
```json
{
  "mcpServers": {
    "claude-mem": {
      "command": "node",
      "args": ["mcp-servers/claude-mem-server/dist/index.js"],
      "env": {
        "WORKER_URL": "http://localhost:37777",
        "ANTHROPIC_API_KEY": "${ANTHROPIC_API_KEY}"
      },
      "disabled": false,
      "alwaysAllow": ["search", "timeline", "get_observations", "__IMPORTANT"]
    }
  }
}
```

- Local mode requires `ANTHROPIC_API_KEY` for AI compression (set in system environment)
- Database stored at `~/.claude-mem/memory.db` (Windows: `%USERPROFILE%\.claude-mem\memory.db`)

**Custom database location (local mode only):**
Add `"MEMORY_DB_PATH": "/path/to/custom/memory.db"` to the `env` block.

## Troubleshooting

### Worker Service Won't Start

**Symptom:** Context injection fails, no observations captured

**Diagnosis:**
```bash
# Check worker status
node scripts/worker-service.js status

# Check worker logs
# macOS/Linux
tail -50 ~/.claude-mem/worker.log

# Windows PowerShell
Get-Content "$env:USERPROFILE\.claude-mem\worker.log" -Tail 50
```

**Common causes:**
1. **Port 37777 already in use**
   - Solution: Change `WORKER_PORT` in `.mcp.json`
   - Or kill process using port: `lsof -ti:37777 | xargs kill` (macOS/Linux)

2. **Missing ANTHROPIC_API_KEY**
   - Solution: Set environment variable (see "Anthropic API Key" section)

3. **Database permission denied**
   - Solution: Check `~/.claude-mem/` directory permissions
   - Create directory: `mkdir -p ~/.claude-mem`

4. **Node.js version too old**
   - Solution: Update to Node.js 18+ (`node --version`)

### Observations Not Being Captured

**Symptom:** Memory searches return no results, database is empty

**Diagnosis:**
```bash
# Check if hooks are configured
cat .claude/hooks/hooks.json

# Check hook logs (if logging enabled)
cat .claude/hooks/hook.log
```

**Common causes:**
1. **Hooks not enabled**
   - Solution: Run `/memory-setup` or `node scripts/setup-memory.js`

2. **Worker service not running**
   - Solution: `node scripts/worker-service.js start`

3. **Permissions blocking hook execution**
   - Solution: Check `.claude/settings.json` has hook permissions:
   ```json
   "allow": [
     "Bash(node .claude/hooks/*:*)",
     "Bash(node scripts/worker-service.js:*)",
     "Bash(node mcp-servers/claude-mem-server/dist/*:*)"
   ]
   ```

4. **Tool operations being skipped**
   - Solution: Check `save-hook.js` SKIP_TOOLS list
   - Some tools like TodoWrite, AskUserQuestion are intentionally skipped

### Search Returns No Results

**Symptom:** `/memory-search "query"` returns 0 results

**Diagnosis:**
```bash
# Check database directly
sqlite3 ~/.claude-mem/memory.db "SELECT COUNT(*) FROM observations;"
sqlite3 ~/.claude-mem/memory.db "SELECT COUNT(*) FROM sdk_sessions;"
```

**Common causes:**
1. **Wrong project name**
   - Solution: Check current project name: `basename $(pwd)`
   - Or search all projects: `/memory-search "query" --project "*"`

2. **Observations not compressed yet**
   - Solution: Worker compresses observations in background (takes 5-30 seconds per observation)
   - Check compression status: `sqlite3 ~/.claude-mem/memory.db "SELECT compression_status FROM observations LIMIT 10;"`

3. **FTS5 index out of sync**
   - Solution: Rebuild index:
   ```bash
   sqlite3 ~/.claude-mem/memory.db "INSERT INTO observations_fts(observations_fts) VALUES('rebuild');"
   ```

### High Token Usage Despite Memory

**Symptom:** Context window filling up even with persistent memory

**Common causes:**
1. **Loading full details too early**
   - Solution: Use three-layer workflow (search → timeline → details)
   - Don't jump straight to `get_observations` with many IDs

2. **Too many observations in timeline**
   - Solution: Reduce window size in timeline requests
   - Filter results in Layer 1 before expanding to Layer 2

3. **Context injection too broad**
   - Solution: Be specific with search queries
   - Use `--limit` flag to restrict results

### Privacy Tags Not Working

**Symptom:** Sensitive data still visible in search results

**Diagnosis:**
```bash
# Check raw observation in database
sqlite3 ~/.claude-mem/memory.db "SELECT compressed_observation FROM observations WHERE id = 123;"
```

**Common causes:**
1. **Tags not properly closed**
   - Wrong: `<private>secret` (no closing tag)
   - Right: `<private>secret</private>`

2. **Tags added after capture**
   - Privacy tags must be in original content when tool is executed
   - Adding tags to files later won't affect already-captured observations

3. **Using different tag format**
   - Only `<private>...</private>` is supported
   - Not `<!-- private -->` or `// private` or other formats

### MCP Server Connection Failed

**Symptom:** Error messages about MCP server not responding

**Diagnosis:**
```bash
# Check MCP server logs
cat ~/.claude/logs/mcp.log

# Verify MCP server build
ls -la mcp-servers/claude-mem-server/dist/
```

**Common causes:**
1. **MCP server not built**
   - Solution: `cd mcp-servers/claude-mem-server && npm install && npm run build`

2. **Wrong path in .mcp.json**
   - Solution: Verify `args` path is correct relative to project root
   ```json
   "args": ["mcp-servers/claude-mem-server/dist/index.js"]
   ```

3. **Database path not accessible**
   - Solution: Check `MEMORY_DB_PATH` in `.mcp.json`
   - Ensure directory exists and has write permissions

## Token Efficiency Tips

1. **Use /memory-search skill** instead of MCP tools directly
   - Skill implements three-layer workflow automatically
   - Handles pagination and filtering efficiently

2. **Be specific with search queries**
   - Good: `/memory-search "JWT authentication middleware"`
   - Bad: `/memory-search "auth"` (too broad, many results)

3. **Use filters to narrow results**
   - Filter by tool type: `--type Write` (only file writes)
   - Filter by project: `--project template-ai-team`
   - Limit results: `--limit 5`

4. **Expand timeline selectively**
   - Don't request timeline for all search results
   - Pick 2-3 most relevant observations from Layer 1

5. **Load full details sparingly**
   - Only load full details for 1-3 final observations
   - This is the most token-expensive operation

6. **Use privacy tags generously**
   - Shorter stored content = less tokens in search results
   - `<private>` removes unnecessary details from future context

## Best Practices

### For Individual Developers

1. **Let it run automatically** - Hooks capture observations without manual intervention
2. **Search before implementing** - Check if similar work was done before: `/memory-search "feature name"`
3. **Use privacy tags** - Wrap API keys, passwords, personal data in `<private>` tags
4. **Export regularly** - Backup memory monthly: `/memory-export --file backups/memory-$(date +%Y-%m).md`
5. **Clear old projects** - Remove memory for abandoned projects: `/memory-clear`

### For Multi-Agent Teams

1. **Shared memory across agents** - All agents (Implementation, Review, Test, Documentation) see same memory
2. **Handoff context** - Implementation Agent's work is visible to Review Agent automatically
3. **Learn from reviews** - Test Agent can search for past review findings: `/memory-search "code review"`
4. **Document learnings** - Documentation Agent searches for decisions: `/memory-search "architecture decision"`
5. **Project-specific memory** - Each project has isolated memory (no cross-contamination)

### For Privacy-Sensitive Projects

1. **Enable privacy tags** - Wrap all sensitive data
2. **Audit before sharing** - Use `/memory-export` to review what's stored before sharing project
3. **Clear sensitive sessions** - Use `/memory-clear` after handling secrets
4. **Backup before clearing** - Always backup database before clearing
5. **Use custom database location** - Store database in encrypted volume if needed

## FAQ

**Q: Does persistent memory work across different Claude Code sessions?**
A: Yes, that's the entire purpose. Memory persists in SQLite database at `~/.claude-mem/memory.db`.

**Q: Can I share memory across multiple projects?**
A: No, memory is project-isolated by default. Each project gets its own memory namespace.

**Q: How much disk space does memory use?**
A: Typically 1-10 MB per project depending on activity. Compressed observations are very compact.

**Q: Does this send my code to Anthropic?**
A: Yes, the worker service uses Claude Sonnet 4.5 API to compress observations. Use privacy tags to protect sensitive data.

**Q: Can I disable compression to save API costs?**
A: Observations are stored in raw form even without compression. Compression just makes search results more concise. You can disable worker service and still search raw observations.

**Q: What happens if worker service crashes?**
A: Hooks fail gracefully - your Claude Code session continues normally. Worker auto-restarts on next session.

**Q: Can I use this with Claude Desktop app?**
A: Not currently. This is designed for Claude Code CLI. Desktop app doesn't support hooks.

**Q: How do I migrate memory to a new machine?**
A: Copy `~/.claude-mem/memory.db` to new machine's `~/.claude-mem/` directory.

**Q: Can I edit observations in the database directly?**
A: Yes, it's SQLite. Use any SQLite client. Schema is in `docs/PERSISTENT_MEMORY_ARCHITECTURE.md`.

**Q: Does this work offline?**
A: Capture and search work offline. Compression requires internet (Anthropic API). Uncompressed observations are still searchable.

---

**For implementation details and architecture, see [PERSISTENT_MEMORY_ARCHITECTURE.md](../PERSISTENT_MEMORY_ARCHITECTURE.md)**

**For multi-agent orchestration, see [MULTI_AGENT_ORCHESTRATION.md](../MULTI_AGENT_ORCHESTRATION.md)**
