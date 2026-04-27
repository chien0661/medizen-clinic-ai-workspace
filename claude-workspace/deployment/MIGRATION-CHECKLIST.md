# Migration Checklist: Upgrading to Persistent Memory v1.6.0+

Quick reference checklist for upgrading existing `template-ai-team` projects to include Persistent Memory.

**Estimated Time**: 30-45 minutes
**Difficulty**: Intermediate
**Rollback Available**: Yes

---

## Pre-Migration Phase

### 1. Prerequisites Check ✓

**System Requirements:**
- [ ] Docker 20.10+ installed and running
- [ ] Docker Compose 2.0+ installed
- [ ] Node.js 18+ installed
- [ ] npm 8+ installed
- [ ] Git installed
- [ ] 10+ GB free disk space
- [ ] Internet connectivity available

**Verify versions:**
```bash
docker --version          # 20.10+
docker compose version    # 2.0+
node --version           # 18+
npm --version            # 8+
```

**Credentials:**
- [ ] Anthropic API key obtained from https://console.anthropic.com/
- [ ] API key saved securely (will need during setup)

### 2. Backup Current Configuration ✓

**Create backups:**
```bash
mkdir -p .backups
cp .mcp.json .backups/.mcp.json.backup.$(date +%Y%m%d-%H%M%S)
cp .claude/settings.local.json .backups/settings.local.json.backup.$(date +%Y%m%d-%H%M%S)
cp .gitignore .backups/.gitignore.backup.$(date +%Y%m%d-%H%M%S)
```

**Checklist:**
- [ ] `.mcp.json` backed up
- [ ] `.claude/settings.local.json` backed up
- [ ] `.gitignore` backed up
- [ ] Backup files verified in `.backups/` folder

### 3. Git Repository Status ✓

**Check clean working tree:**
```bash
git status
```

**Checklist:**
- [ ] No uncommitted changes (or commit them first)
- [ ] On correct branch (usually `develop` or `main`)
- [ ] Pulled latest changes from remote
- [ ] Template remote added (if not already):
  ```bash
  git remote add template https://bitbucket.vissoft.vn/scm/ct/template-ai-team.git
  git fetch template master
  ```

---

## Migration Phase

### 4. Copy Core Files ✓

**MCP Server:**
```bash
cp -r [template-path]/mcp-servers/claude-mem-server ./mcp-servers/
```
- [ ] `mcp-servers/claude-mem-server/` directory copied
- [ ] Verify: `ls mcp-servers/claude-mem-server/package.json` exists

**Hooks System:**
```bash
cp -r [template-path]/.claude/hooks ./.claude/
```
- [ ] `.claude/hooks/save-hook.js` copied
- [ ] `.claude/hooks/cleanup-hook.js` copied
- [ ] `.claude/hooks/context-hook.js` copied
- [ ] Verify: `ls .claude/hooks/*.js` shows 3 files

**Docker Deployment:**
```bash
mkdir -p deployment/docker
cp [template-path]/deployment/docker/Dockerfile ./deployment/docker/
cp [template-path]/deployment/docker/docker-compose.yml ./deployment/docker/
cp [template-path]/deployment/docker/.env.example ./deployment/docker/
cp [template-path]/deployment/docker/setup.sh ./deployment/docker/
cp [template-path]/deployment/docker/README.md ./deployment/docker/
chmod +x deployment/docker/setup.sh
```
- [ ] `deployment/docker/Dockerfile` copied
- [ ] `deployment/docker/docker-compose.yml` copied
- [ ] `deployment/docker/.env.example` copied
- [ ] `deployment/docker/setup.sh` copied and executable
- [ ] `deployment/docker/README.md` copied

**Documentation:**
```bash
cp [template-path]/docs/guide/reference/using-persistent-memory.md ./docs/guides/
cp [template-path]/docs/guide/reference/PERSISTENT_MEMORY_ARCHITECTURE.md ./docs/
```
- [ ] `docs/guide/reference/using-persistent-memory.md` copied
- [ ] `docs/guide/reference/PERSISTENT_MEMORY_ARCHITECTURE.md` copied

### 5. Update .gitignore ✓

**Add to `.gitignore`:**
```bash
cat >> .gitignore << 'EOF'

# Docker and Claude Memory Deployment
deployment/docker/.env
deployment/**/.env
!deployment/**/.env.example
deployment/docker/data/
deployment/docker/logs/
deployment/docker/backups/
.claude-mem/
*.db-shm
*.db-wal
deployment/**/*.log
.mcp.json.backup.*
.claude/settings.local.json.backup.*
EOF
```

**Checklist:**
- [ ] `.gitignore` updated with Docker/Memory exclusions
- [ ] Verify: `grep "claude-mem" .gitignore` returns results
- [ ] Commit changes: `git add .gitignore && git commit -m "chore: add Docker and Memory to gitignore"`

### 6. Update .mcp.json ✓

**Add claude-mem server:**

Edit `.mcp.json` and add:
```json
{
  "mcpServers": {
    "claude-mem": {
      "command": "node",
      "args": ["mcp-servers/claude-mem-server/dist/index.js"],
      "env": {
        "WORKER_URL": "${WORKER_URL}",
        "API_KEY": "${CLAUDE_MEM_API_KEY}",
        "ANTHROPIC_API_KEY": "${ANTHROPIC_API_KEY}"
      },
      "disabled": false,
      "alwaysAllow": ["search", "timeline", "get_observations", "__IMPORTANT"]
    }
    // ... keep existing servers
  }
}
```

**Checklist:**
- [ ] `claude-mem` server added to `.mcp.json`
- [ ] Environment variables use `${...}` syntax
- [ ] Syntax is valid JSON (check with: `cat .mcp.json | jq .`)
- [ ] **Do NOT commit** (contains sensitive data, already in `.gitignore`)

### 7. Update .claude/settings.local.json ✓

**Add environment and hooks:**

Edit `.claude/settings.local.json`:
```json
{
  "env": {
    "WORKER_URL": "http://localhost:37777"
  },
  "enabledMcpjsonServers": [
    "claude-mem"
    // ... existing servers
  ],
  "hooks": {
    "PostToolUse": [{
      "hooks": [{
        "type": "command",
        "command": "node .claude/hooks/save-hook.js",
        "statusMessage": "Capturing observation..."
      }]
    }],
    "SessionEnd": [{
      "hooks": [{
        "type": "command",
        "command": "node .claude/hooks/cleanup-hook.js",
        "statusMessage": "Finalizing session..."
      }]
    }],
    "SessionStart": [{
      "hooks": [{
        "type": "command",
        "command": "node .claude/hooks/context-hook.js",
        "statusMessage": "Loading context..."
      }]
    }]
  }
}
```

**Checklist:**
- [ ] `WORKER_URL` set to `http://localhost:37777`
- [ ] `claude-mem` added to `enabledMcpjsonServers`
- [ ] All three hooks added (PostToolUse, SessionEnd, SessionStart)
- [ ] Syntax is valid JSON
- [ ] **Do NOT commit** (already in `.gitignore`)

### 8. Build MCP Server ✓

**Install and build:**
```bash
cd mcp-servers/claude-mem-server
npm install
npm run build
cd ../..
```

**Checklist:**
- [ ] Dependencies installed (no errors)
- [ ] Build completed successfully
- [ ] `dist/` folder created
- [ ] Verify: `ls mcp-servers/claude-mem-server/dist/index.js` exists

---

## Docker Deployment Phase

### 9. Run Docker Setup ✓

**Automated setup:**
```bash
cd deployment/docker
bash setup.sh
```

**During setup:**
- [ ] Docker prerequisites check passed
- [ ] `.env` file created
- [ ] Anthropic API key entered
- [ ] Client API key generated (copy this!)
- [ ] Docker image built successfully
- [ ] Container started
- [ ] Health check passed

**Save generated keys:**
- [ ] Anthropic API key: ________________
- [ ] Client API key: ________________

**Manual verification:**
```bash
docker compose ps
# Should show: claude-memory-worker   Up (healthy)

curl http://localhost:37777/api/health
# Should return: {"status":"ok",...}
```

### 10. Configure Client ✓

**Update environment variables or .mcp.json:**

Option 1 - Environment variables (recommended):
```bash
export WORKER_URL=http://localhost:37777
export CLAUDE_MEM_API_KEY=<client-api-key-from-setup>
export ANTHROPIC_API_KEY=<your-anthropic-key>
```

Option 2 - Direct in .mcp.json (replace placeholders):
```json
{
  "claude-mem": {
    "env": {
      "WORKER_URL": "http://localhost:37777",
      "API_KEY": "<client-api-key-from-setup>",
      "ANTHROPIC_API_KEY": "<your-anthropic-key>"
    }
  }
}
```

**Checklist:**
- [ ] Client API key configured
- [ ] Anthropic API key configured
- [ ] Worker URL configured
- [ ] Configuration method chosen (env vars or direct)

---

## Verification Phase

### 11. Restart Claude Code ✓

**Restart to activate hooks:**
```bash
# In Claude Code
exit

# Start again
claude code
```

**Checklist:**
- [ ] Claude Code restarted
- [ ] No startup errors
- [ ] MCP servers loaded (check startup messages)

### 12. Verify Docker Container ✓

**Check container status:**
```bash
cd deployment/docker

# Status
docker compose ps
# Should show: healthy

# Logs
docker compose logs --tail=50
# Should show: Worker ready, listening on port 37777
```

**Checklist:**
- [ ] Container status: Up (healthy)
- [ ] No error messages in logs
- [ ] Port 37777 listening

### 13. Test Hooks Execution ✓

**In Claude Code, run any tool:**
```
# Read a file
Read the README.md file
```

**Watch for:**
```
Capturing observation...  ✓
```

**Check Docker logs:**
```bash
docker compose logs --tail=20 | grep "POST /api"
# Should show:
# POST /api/sessions/xxx/init
# POST /api/sessions/observations
```

**Checklist:**
- [ ] "Capturing observation" message appears
- [ ] API requests in Docker logs
- [ ] No hook errors

### 14. Test Memory Search ✓

**Try searching:**
```
/memory-search "docker deployment"
```

**Note**: May return empty results initially (normal). Wait for observations to be captured and compressed.

**After some tool usage:**
- [ ] Search returns results
- [ ] Results show relevant observations
- [ ] No error messages

### 15. End-to-End Test ✓

**Create test script:**
```bash
cat > test-memory-complete.js << 'EOF'
const WORKER_URL = 'http://localhost:37777';

async function test() {
  console.log('🧪 Complete system test\n');

  // 1. Init session
  const init = await fetch(`${WORKER_URL}/api/sessions/test-migration/init`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      claude_session_id: 'test-migration',
      project_name: process.cwd().split('/').pop()
    })
  });
  const session = await init.json();
  console.log('✓ Session:', session.session_id);

  // 2. Save observation
  const obs = await fetch(`${WORKER_URL}/api/sessions/observations`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      session_id: session.session_id,
      tool_name: 'Bash',
      tool_input: 'echo "migration test"',
      tool_response: 'migration test'
    })
  });
  const obsData = await obs.json();
  console.log('✓ Observation:', obsData.observation_id);

  console.log('\n✅ All systems operational!\n');
}

test().catch(e => console.error('❌ Test failed:', e.message));
EOF

node test-memory-complete.js
```

**Expected output:**
```
🧪 Complete system test

✓ Session: <session-id>
✓ Observation: <observation-id>

✅ All systems operational!
```

**Checklist:**
- [ ] Test script runs without errors
- [ ] Session created successfully
- [ ] Observation saved successfully
- [ ] Test output shows "All systems operational"

---

## Post-Migration Phase

### 16. Commit Changes ✓

**Stage and commit:**
```bash
git add mcp-servers/claude-mem-server/
git add .claude/hooks/
git add deployment/docker/
git add docs/guide/reference/using-persistent-memory.md
git add docs/guide/reference/PERSISTENT_MEMORY_ARCHITECTURE.md
git add .gitignore

git commit -m "feat: add persistent memory system v1.6.0

- Add Claude Memory MCP server
- Add hooks for automatic observation capture
- Add Docker deployment configuration
- Add comprehensive documentation
- Update .gitignore for Docker and memory data

Enables never-lose-context capability across sessions."
```

**Checklist:**
- [ ] All new files staged
- [ ] Configuration files excluded (in .gitignore)
- [ ] Commit message clear and descriptive
- [ ] Changes committed successfully

### 17. Push and Share ✓

**Push to remote:**
```bash
git push origin <your-branch>
```

**Create PR if needed:**
- [ ] Pull request created
- [ ] Description includes upgrade notes
- [ ] Team members notified

### 18. Documentation ✓

**Update project README:**
- [ ] Add section about Persistent Memory feature
- [ ] Link to usage guide
- [ ] Document setup steps for new team members

**Share with team:**
- [ ] Demo the memory search feature
- [ ] Share Docker setup instructions
- [ ] Explain hooks and automatic capture

---

## Rollback Procedure (If Needed)

### Emergency Rollback ✓

If something goes wrong:

```bash
# 1. Stop Docker
cd deployment/docker
docker compose down -v

# 2. Restore backups
cp .backups/.mcp.json.backup.<date> .mcp.json
cp .backups/settings.local.json.backup.<date> .claude/settings.local.json
cp .backups/.gitignore.backup.<date> .gitignore

# 3. Remove new files
rm -rf mcp-servers/claude-mem-server
rm -rf .claude/hooks
rm -rf deployment/docker
rm -rf .claude-mem/

# 4. Restart Claude Code
exit
claude code

# 5. Revert Git changes (if committed)
git reset --hard <commit-before-migration>
```

**Checklist:**
- [ ] Docker stopped and volumes removed
- [ ] Configuration restored from backups
- [ ] New files removed
- [ ] Claude Code restarted
- [ ] System working as before

---

## Final Verification

### All Systems Check ✓

**Before closing migration:**

**Infrastructure:**
- [ ] Docker container running and healthy
- [ ] Port 37777 accessible
- [ ] Worker logs showing no errors

**Integration:**
- [ ] Claude Code loads without errors
- [ ] MCP claude-mem server active
- [ ] Hooks executing on tool use

**Functionality:**
- [ ] Observations being captured
- [ ] SDK Agent compressing observations
- [ ] Memory search working
- [ ] No errors in logs

**Documentation:**
- [ ] Team aware of new feature
- [ ] Usage guide accessible
- [ ] Setup documented for new members

**Version Control:**
- [ ] Changes committed
- [ ] .env and sensitive files not committed
- [ ] Backups preserved

---

## Success Criteria

Migration is complete when:

1. ✅ Docker container status: **Up (healthy)**
2. ✅ Health endpoint returns: **{"status":"ok"}**
3. ✅ Hooks execute with: **"Capturing observation... ✓"**
4. ✅ Memory search finds observations
5. ✅ No errors in Docker logs
6. ✅ Changes committed to Git
7. ✅ Team members can access documentation

---

## Next Steps

After successful migration:

1. **Read usage guide**: [docs/guide/reference/using-persistent-memory.md](../docs/guide/reference/using-persistent-memory.md)
2. **Learn search syntax**: Practice with `/memory-search`
3. **Configure privacy**: Use `<private>` tags for sensitive data
4. **Monitor usage**: Check Docker logs periodically
5. **Share knowledge**: Demo to team members
6. **Optimize hooks**: Customize observation capture if needed

---

## Support

**Troubleshooting:**
- Check: [deployment/PREREQUISITES.md](PREREQUISITES.md)
- Review: [docs/guide/reference/PERSISTENT_MEMORY_ARCHITECTURE.md](../docs/guide/reference/PERSISTENT_MEMORY_ARCHITECTURE.md)
- Logs: `cd deployment/docker && docker compose logs --tail=100`

**Contact:**
- VISSoft AI Team
- Template repository issues
- Team Slack/Teams channel

---

**Migration Checklist Version**: 1.0
**Template Version**: 1.6.0+
**Last Updated**: 2026-02-04

**Estimated Total Time**: 30-45 minutes
**Difficulty**: Intermediate
**Rollback Available**: Yes ✓

---

## Checklist Summary

**Print this page for offline reference during migration.**

**Phase 1 - Pre-Migration:**
- [ ] Prerequisites verified
- [ ] Backups created
- [ ] Git status clean

**Phase 2 - Migration:**
- [ ] Core files copied
- [ ] .gitignore updated
- [ ] .mcp.json updated
- [ ] settings.local.json updated
- [ ] MCP server built

**Phase 3 - Deployment:**
- [ ] Docker setup completed
- [ ] Client configured
- [ ] Keys saved securely

**Phase 4 - Verification:**
- [ ] Claude Code restarted
- [ ] Container healthy
- [ ] Hooks working
- [ ] Search functional
- [ ] E2E test passed

**Phase 5 - Post-Migration:**
- [ ] Changes committed
- [ ] Documentation updated
- [ ] Team notified

**MIGRATION COMPLETE** ✅
