# /setup-memory - Persistent Memory Setup

## Usage

```bash
/setup-memory            # Interactive setup (choose mode)
/setup-memory --remote   # Remote worker (recommended for teams)
/setup-memory --docker   # Docker deployment (self-hosted)
/setup-memory --local    # Local mode (solo developer)
```

## Purpose

Set up the Persistent Memory system for never-lose-context capability across Claude Code sessions. Automatically captures tool observations, compresses with Claude Agent SDK, enables semantic search.

## Prerequisites

**Required**: Node.js 18+, npm 8+

**Remote Mode**: `MEMORY_API_KEY` from team lead (no local worker or Anthropic key needed)

**Docker Mode**: Docker 20.10+, Docker Compose 2.0+, port 37777, Anthropic API key

**Local Mode**: ~100 MB disk space, read/write to `~/.claude-mem/`, Anthropic API key

## Setup Steps

### Step 1: Choose Deployment Mode

| Aspect | Remote (Recommended) | Docker | Local |
|--------|---------------------|--------|-------|
| Setup time | ~2 min | ~5 min | ~3 min |
| Worker location | Team server | Local container | In-process |
| Anthropic API key | Not needed (server has it) | Required | Required |
| Team sharing | Yes (shared memory) | Supports remote | Single machine |
| Best for | Teams, multi-machine | Self-hosted production | Solo developer |

### Step 2A: Remote Mode (Recommended)

1. **Get credentials** from team lead: server URL + API key
2. **Configure .mcp.json** - add `claude-mem` entry:
   ```json
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
   ```
3. **Add to `.env`**: `MEMORY_API_KEY=<api-key-from-team-lead>`
4. **Configure hooks** in `.claude/settings.local.json`:
   ```json
   {
     "env": { "WORKER_URL": "http://10.10.100.22:37777" },
     "hooks": {
       "PostToolUse": [{ "hooks": [{ "type": "command", "command": "node .claude/hooks/save-hook.js", "statusMessage": "Capturing observation..." }] }],
       "SessionEnd": [{ "hooks": [{ "type": "command", "command": "node .claude/hooks/cleanup-hook.js", "statusMessage": "Finalizing session..." }] }],
       "SessionStart": [{ "hooks": [{ "type": "command", "command": "node .claude/hooks/context-hook.js", "statusMessage": "Loading context..." }] }]
     }
   }
   ```
5. **Build MCP server**: `cd mcp-servers/claude-mem-server && npm install && npm run build && cd ../..`
6. **Verify**: `curl http://10.10.100.22:37777/api/health`

### Step 2B: Docker Mode

1. **Check prerequisites**: `docker --version`, `docker compose version`, port 37777 free
2. **Run setup wizard**: `cd deployment/docker && bash setup.sh`
   - Enter Anthropic API key
   - Client API key auto-generated
   - Docker image built, container started, health checks run
3. **Save generated keys** (Client API Key needed for .mcp.json)
4. **Configure .mcp.json** - add `claude-mem` entry:
   ```json
   "claude-mem": {
     "command": "node",
     "args": ["mcp-servers/claude-mem-server/dist/index.js"],
     "env": {
       "WORKER_URL": "http://localhost:37777",
       "API_KEY": "<client-api-key-from-setup>",
       "ANTHROPIC_API_KEY": "${ANTHROPIC_API_KEY}"
     },
     "disabled": false,
     "alwaysAllow": ["search", "timeline", "get_observations", "__IMPORTANT"]
   }
   ```
5. **Configure hooks** in `.claude/settings.local.json` (same as Remote Mode, but `WORKER_URL` = `http://localhost:37777`)
6. **Build MCP server**: `cd mcp-servers/claude-mem-server && npm install && npm run build && cd ../..`
7. **Verify**: `docker compose ps` (healthy), `curl http://localhost:37777/api/health`

### Step 2C: Local Mode

1. **Configure .mcp.json** - add `claude-mem` entry:
   ```json
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
   ```
2. **Configure hooks** (same as Remote Mode, but `WORKER_URL` = `http://localhost:37777`)
3. **Build MCP server**: `cd mcp-servers/claude-mem-server && npm install && npm run build && cd ../..`
4. **Create database dir**: `mkdir -p ~/.claude-mem` (Windows: `mkdir %USERPROFILE%\.claude-mem`)

### Step 3: Test Setup

1. Restart Claude Code (exit and re-launch)
2. Use any tool → watch for "Capturing observation..." message
3. Test search: `/memory-search "query"` (may be empty initially - normal)

### Step 4: Validate

**Remote**: Health endpoint OK, MCP built, hooks executing, `/memory-search "test"` runs without errors
**Docker**: Container healthy, health endpoint OK, MCP built, hooks executing
**Local**: MCP built, hooks executing, database dir created

## Common Issues

| Issue | Solution |
|-------|----------|
| Remote connection refused | Check server URL, firewall allows your IP, server running |
| "Unauthorized" (remote) | Verify `MEMORY_API_KEY` in `.env` matches server's API key |
| Docker container fails | Check port 37777 available, Docker running, sufficient memory |
| Hooks not executing | Restart Claude Code; verify hooks in `.claude/settings.local.json` |
| Empty search results | Normal for new setup; use tools, wait 30-60s for compression, search again |
| "API key invalid" | Verify Anthropic key valid; check Client API key matches Docker .env |
| Permission denied (local) | `chmod 755 ~/.claude-mem/` |

## Advanced Options

- **Remote team deployment**: See `docs/guide/setup/remote-memory-deployment.md`
- **Switch modes**: Change `WORKER_URL` in `.mcp.json` and `.claude/settings.local.json`
- **Custom port**: Change in docker-compose.yml ports and WORKER_URL in settings
- **Database backup**: Docker: `docker exec` cp command; Local: `cp ~/.claude-mem/memory.db`

## Related Skills

- `/memory-search` - Search past observations
- `/memory-clear` - Clear memory database
- `/memory-export` - Export memory backup
- `/project-setup` - Includes memory setup option

## Documentation

- User Guide: `docs/guide/reference/using-persistent-memory.md`
- Architecture: `docs/guide/reference/PERSISTENT_MEMORY_ARCHITECTURE.md`
- Remote Deployment: `docs/guide/setup/remote-memory-deployment.md`

---

**Skill Type**: System Setup
**Dependencies**: Docker (optional), Node.js 18+, Anthropic API key
