# Upgrade Guide: Adding Persistent Memory to Existing Projects

This guide helps you upgrade an existing project from the `template-ai-team` to include the new **Persistent Memory** system with Docker deployment.

## Overview

The Persistent Memory system allows Claude Code to remember context across sessions, making long-running projects more efficient. This upgrade adds:

- **Automatic observation capture** via Claude Code hooks
- **AI-powered compression** using Claude Agent SDK
- **Token-efficient search** with progressive disclosure
- **Docker deployment** for easy setup and team sharing
- **Privacy protection** with automatic sensitive data stripping

## Prerequisites

Before starting the upgrade, ensure you have:

- [ ] **Docker** installed (version 20.10+)
- [ ] **Docker Compose** installed (version 2.0+)
- [ ] **Node.js** installed (version 18+)
- [ ] **Anthropic API key** from https://console.anthropic.com/
- [ ] **Git** for version control
- [ ] **Your project** is based on `template-ai-team`

Check versions:
```bash
docker --version          # Should be 20.10+
docker compose version    # Should be 2.0+
node --version           # Should be 18+
```

## Step 1: Backup Your Current Configuration

Before making changes, backup your existing configuration files:

```bash
# Create backup directory
mkdir -p .backups

# Backup existing configuration
cp .mcp.json .backups/.mcp.json.backup
cp .claude/settings.local.json .backups/settings.local.json.backup
cp .gitignore .backups/.gitignore.backup
```

## Step 2: Pull Latest Template Changes

If your project is based on the template repository:

```bash
# Add template as remote (if not already added)
git remote add template https://bitbucket.vissoft.vn/scm/ct/template-ai-team.git

# Fetch latest changes
git fetch template master

# Check what's new (review before merging)
git log HEAD..template/master --oneline

# Merge or cherry-pick the changes
git merge template/master
# OR cherry-pick specific commits
```

## Step 3: Copy Required Files

Copy the following files from the updated template to your project:

### Core Memory System Files

```bash
# MCP Server (if not already present)
cp -r mcp-servers/claude-mem-server/ ./mcp-servers/

# Hooks for automatic capture
cp -r .claude/hooks/ ./.claude/

# Docker deployment files
mkdir -p deployment/docker
cp deployment/docker/Dockerfile ./deployment/docker/
cp deployment/docker/docker-compose.yml ./deployment/docker/
cp deployment/docker/.env.example ./deployment/docker/
cp deployment/docker/setup.sh ./deployment/docker/
cp deployment/docker/README.md ./deployment/docker/
```

### Documentation

```bash
# Usage guides
cp docs/guides/using-persistent-memory.md ./docs/guides/
cp docs/PERSISTENT_MEMORY_ARCHITECTURE.md ./docs/
```

Make setup script executable:
```bash
chmod +x deployment/docker/setup.sh
```

## Step 4: Update Configuration Files

### 4.1 Update .gitignore

Add Docker and Claude Memory protection to your `.gitignore`:

```bash
# Add these lines at the end of .gitignore
cat >> .gitignore << 'EOF'

# Docker and Claude Memory Deployment
# Deployment environment files (sensitive credentials)
deployment/docker/.env
deployment/**/.env
!deployment/**/.env.example

# Docker volumes and data (contains user data and API keys)
deployment/docker/data/
deployment/docker/logs/
deployment/docker/backups/

# Claude Memory database (contains session data)
.claude-mem/
*.db-shm
*.db-wal

# Docker-related temporary files
deployment/**/*.log
deployment/**/temp/
deployment/**/tmp/

# Backup files from setup
.mcp.json.backup.*
.claude/settings.local.json.backup.*
EOF
```

### 4.2 Update .mcp.json

Add the `claude-mem` server configuration to your `.mcp.json`:

```json
{
  "mcpServers": {
    "claude-mem": {
      "command": "node",
      "args": [
        "mcp-servers/claude-mem-server/dist/index.js"
      ],
      "env": {
        "WORKER_URL": "${WORKER_URL}",
        "API_KEY": "${CLAUDE_MEM_API_KEY}",
        "ANTHROPIC_API_KEY": "${ANTHROPIC_API_KEY}"
      },
      "disabled": false,
      "alwaysAllow": [
        "search",
        "timeline",
        "get_observations",
        "__IMPORTANT"
      ]
    }
    // ... your other MCP servers
  }
}
```

**Note:** Set environment variables or replace placeholders with actual values:
- `WORKER_URL`: Default is `http://localhost:37777`
- `CLAUDE_MEM_API_KEY`: Generated during Docker setup
- `ANTHROPIC_API_KEY`: Your Anthropic API key

### 4.3 Update .claude/settings.local.json

Add environment variables and hooks configuration:

```json
{
  "env": {
    "WORKER_URL": "http://localhost:37777"
  },
  "enabledMcpjsonServers": [
    "claude-mem"
    // ... your other enabled servers
  ],
  "hooks": {
    "PostToolUse": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "node .claude/hooks/save-hook.js",
            "statusMessage": "Capturing observation..."
          }
        ]
      }
    ],
    "SessionEnd": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "node .claude/hooks/cleanup-hook.js",
            "statusMessage": "Finalizing session..."
          }
        ]
      }
    ],
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "node .claude/hooks/context-hook.js",
            "statusMessage": "Loading context..."
          }
        ]
      }
    ]
  }
}
```

## Step 5: Deploy Docker Worker

Navigate to the Docker deployment folder and run the setup script:

```bash
cd deployment/docker

# Run automated setup wizard
bash setup.sh
```

The setup wizard will:
1. Check Docker prerequisites
2. Create `.env` file from template
3. Prompt for your Anthropic API key
4. Generate client API key automatically
5. Build Docker image
6. Start the container
7. Run health checks

### Manual Setup (Alternative)

If you prefer manual setup:

```bash
# 1. Create .env from template
cp .env.example .env

# 2. Edit .env and add your keys
nano .env  # or your preferred editor

# Required values:
# ANTHROPIC_API_KEY=sk-ant-...  # Your API key
# API_KEY=<generate with: openssl rand -hex 32>

# 3. Build and start
docker compose build
docker compose up -d

# 4. Check status
docker compose ps
docker compose logs -f
```

## Step 6: Configure Claude Code Client

Update your environment variables or `.mcp.json` with the generated API key:

```bash
# Option 1: Set environment variables
export WORKER_URL=http://localhost:37777
export CLAUDE_MEM_API_KEY=<generated-api-key-from-setup>

# Option 2: Update .mcp.json directly with actual values
```

**IMPORTANT:** Save the client API key shown during setup. You'll need it for `.mcp.json` configuration.

## Step 7: Build MCP Server

Build the Claude Memory MCP server:

```bash
cd mcp-servers/claude-mem-server

# Install dependencies
npm install

# Build the server
npm run build

# Verify build
ls -la dist/
```

Expected output:
```
dist/
├── index.js
├── index.d.ts
├── services/
│   ├── database.js
│   ├── sdk-agent.js
│   ├── search.js
│   └── worker.js
└── utils/
```

## Step 8: Restart Claude Code

Restart Claude Code to activate the hooks and MCP server:

```bash
# In Claude Code CLI
exit

# Restart
claude code
```

## Step 9: Verify Installation

### 9.1 Check Docker Container

```bash
cd deployment/docker

# Check container status
docker compose ps

# Should show:
# NAME                    STATUS                    PORTS
# claude-memory-worker    Up X minutes (healthy)    0.0.0.0:37777->37777/tcp

# Check logs
docker compose logs --tail=50

# Should show:
# [Worker] Memory worker service listening on http://0.0.0.0:37777
# [Worker] Worker ready
```

### 9.2 Test API Endpoint

```bash
# Test health endpoint
curl http://localhost:37777/api/health

# Should return:
# {"status":"ok","uptime":XXX,"memory":{"rss":XXX,"heapTotal":XXX}}
```

### 9.3 Test Memory Search

In Claude Code, try searching:

```
/memory-search "docker deployment"
```

Initially, results may be empty (no sessions yet). Try again after some tool usage.

### 9.4 Verify Hooks Execution

Use any tool in Claude Code and watch for:

```
Capturing observation...  ✓
```

This confirms the PostToolUse hook is working.

Check Docker logs:
```bash
cd deployment/docker
docker compose logs --tail=20 | grep "POST /api"

# Should show:
# POST /api/sessions/xxx/init
# POST /api/sessions/observations
```

## Step 10: Test End-to-End Flow

Create a simple test to verify the full system:

```bash
# Create test script
cat > test-memory.js << 'EOF'
const WORKER_URL = 'http://localhost:37777';

async function testMemory() {
  console.log('Testing memory system...\n');

  // 1. Initialize session
  const initRes = await fetch(`${WORKER_URL}/api/sessions/test-001/init`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      claude_session_id: 'test-001',
      project_name: 'your-project-name'
    })
  });
  const session = await initRes.json();
  console.log('✓ Session created:', session.session_id);

  // 2. Save observation
  const obsRes = await fetch(`${WORKER_URL}/api/sessions/observations`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      session_id: session.session_id,
      tool_name: 'Bash',
      tool_input: 'echo "test"',
      tool_response: 'test'
    })
  });
  const obs = await obsRes.json();
  console.log('✓ Observation saved:', obs.observation_id);

  console.log('\n✅ Memory system working!');
}

testMemory().catch(console.error);
EOF

# Run test
node test-memory.js
```

Expected output:
```
Testing memory system...

✓ Session created: <session-id>
✓ Observation saved: <observation-id>

✅ Memory system working!
```

## Troubleshooting

### Container not starting

```bash
# Check logs for errors
docker compose logs

# Common issues:
# - Port 37777 already in use: Change port in docker-compose.yml
# - Build failed: Check Node.js version in Dockerfile
# - Permission denied: Check file ownership
```

### Hooks not capturing observations

```bash
# 1. Verify hooks are configured in .claude/settings.local.json
cat .claude/settings.local.json | grep -A 5 "hooks"

# 2. Check WORKER_URL is set
cat .claude/settings.local.json | grep WORKER_URL

# 3. Restart Claude Code
exit
claude code
```

### Search returns empty results

- **Normal for new setup**: No observations captured yet
- **Solution**: Use Claude Code tools (Read, Write, Bash, etc.) to generate observations
- **Wait time**: SDK Agent takes 10-15 seconds per observation to compress
- **Check logs**: `docker compose logs -f | grep SDK`

### Database size not growing

- **Normal behavior**: SQLite pre-allocates space
- **Check last modified**: `docker exec claude-memory-worker ls -lh /opt/claude-memory/data/`
- **Verify writes**: `docker compose logs | grep "Observation saved"`

## Rollback Instructions

If you need to rollback the upgrade:

```bash
# 1. Stop and remove Docker container
cd deployment/docker
docker compose down -v  # -v removes volumes

# 2. Restore backup configuration
cp .backups/.mcp.json.backup .mcp.json
cp .backups/settings.local.json.backup .claude/settings.local.json
cp .backups/.gitignore.backup .gitignore

# 3. Remove added files
rm -rf mcp-servers/claude-mem-server
rm -rf .claude/hooks
rm -rf deployment/docker
rm -rf .claude-mem/

# 4. Restart Claude Code
exit
claude code
```

## Next Steps

After successful upgrade:

1. **Read the user guide**: [docs/guides/using-persistent-memory.md](using-persistent-memory.md)
2. **Learn search commands**: `/memory-search`, `/memory-export`, `/memory-clear`
3. **Understand privacy**: Use `<private>` tags for sensitive data
4. **Optimize hooks**: Customize which tools trigger observation capture
5. **Monitor usage**: Check Docker logs and database size

## Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review Docker logs: `docker compose logs --tail=100`
3. Check architecture docs: [docs/PERSISTENT_MEMORY_ARCHITECTURE.md](../PERSISTENT_MEMORY_ARCHITECTURE.md)
4. Search existing issues on the template repository
5. Contact the AI Team for assistance

## Version Compatibility

This upgrade requires:

- **Template version**: 1.6.0+
- **Claude Code**: Latest version
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **Node.js**: 18+

Check your template version:
```bash
git log --oneline --grep="Persistent Memory" | head -1
```

## Summary

You have successfully upgraded your project with:

- ✅ Persistent Memory worker (Docker)
- ✅ Automatic observation capture (hooks)
- ✅ AI-powered compression (SDK Agent)
- ✅ Token-efficient search (3-layer)
- ✅ Privacy protection (tag stripping)

Your project now has **never-lose-context** capability for long-running sessions.

**Template Version**: 1.6.0+
**Last Updated**: 2026-02-04
**Author**: VISSoft AI Team
