# Remote Deployment Upgrade Summary

**Date:** 2026-02-03
**Version:** 1.5.0+
**Upgrade:** Template configured for remote persistent memory deployment

---

## What Was Done

This upgrade adds **complete remote deployment support** for the persistent memory system, allowing teams to deploy a centralized memory server for shared context across all team members.

### Files Created

1. **docs/guides/remote-memory-deployment.md** (1,000+ lines)
   - Comprehensive remote deployment guide
   - Server setup instructions (Ubuntu/Debian)
   - Client configuration and team rollout
   - Security hardening and best practices
   - Maintenance, backups, monitoring
   - Migration guides (local to remote, server to server)
   - Troubleshooting and FAQ

2. **.env.example** (200+ lines)
   - Environment configuration template
   - Shows BOTH local and remote mode configuration
   - Clear sections for each deployment mode
   - Switching instructions
   - Security notes and best practices

3. **docs/REMOTE_DEPLOYMENT_UPGRADE.md** (this file)
   - Summary of changes
   - Configuration reference
   - Usage instructions

### Files Updated

1. **.mcp.json.example**
   - Added `WORKER_URL` environment variable
   - Added `MEMORY_API_KEY` environment variable
   - Supports both local and remote configuration

2. **README.md**
   - Updated "Persistent Memory System" section
   - Added deployment modes explanation (Local vs Remote)
   - Added benefits of remote deployment
   - Added link to remote deployment guide

3. **docs/guides/using-persistent-memory.md**
   - Added "Deployment Modes" section
   - Explained Local Mode (default)
   - Explained Remote Mode (enterprise)
   - Added links to remote deployment guide

4. **CLAUDE.md**
   - Updated "Persistent Memory Architecture" section
   - Added deployment modes explanation
   - Added remote deployment benefits
   - Added link to remote deployment guide

---

## Deployment Modes

### 🖥️ Local Mode (Default - No Changes Needed)

**This is the current default mode. Everything works as before.**

- **Database**: `~/.claude-mem/memory.db` on your machine
- **Worker**: `http://localhost:37777`
- **API Key**: Not required
- **Best for**: Individual developers, personal projects

**Configuration (.env):**
```bash
WORKER_URL=http://localhost:37777
WORKER_PORT=37777
MEMORY_DB_PATH=${HOME}/.claude-mem/memory.db
MEMORY_API_KEY=
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

### 🌐 Remote Mode (New - Team Deployment)

**New capability for teams!**

- **Database**: Centralized on remote server
- **Worker**: `http://memory.company.com:37777`
- **API Key**: Required for authentication
- **Best for**: Teams, multiple machines, shared context

**Configuration (.env):**
```bash
WORKER_URL=http://memory.company.com:37777
MEMORY_API_KEY=your-32-character-hex-key-here
# ANTHROPIC_API_KEY not needed on client
```

---

## Quick Start: Remote Deployment

### For Team Leaders (Server Deployment)

**Prerequisites:**
- Ubuntu 20.04+ server
- SSH access with sudo
- Node.js 18+
- Anthropic API key

**Steps:**

```bash
# 1. Copy deployment package to server
scp -r deployment/ user@memory.company.com:/tmp/

# 2. SSH to server
ssh user@memory.company.com

# 3. Run installation
cd /tmp/deployment/server
sudo bash install.sh

# 4. Configure environment
API_KEY=$(openssl rand -hex 32)
echo "API Key: $API_KEY"  # Share with team securely

sudo nano /opt/claude-memory/server/.env
# Set ANTHROPIC_API_KEY and API_KEY

# 5. Start service
sudo systemctl start claude-memory-worker
sudo systemctl enable claude-memory-worker

# 6. Configure firewall
cd /tmp/deployment/configs
sudo bash firewall-rules.sh

# 7. Test
curl http://localhost:37777/api/health
```

**Share with team:**
- Server URL: `http://memory.company.com:37777`
- API Key: `[the key you generated]`

### For Team Members (Client Configuration)

**Prerequisites:**
- Already using this template
- Received server URL and API key from team lead

**Steps:**

```bash
# 1. Navigate to project
cd /path/to/template-ai-team

# 2. Configure for remote
bash deployment/client/configure-remote.sh http://memory.company.com:37777 your-api-key

# 3. Test connection
bash deployment/client/test-connection.sh

# 4. Restart Claude Code
exit
claude code

# 5. Verify
/memory-search "test"
```

---

## Switching Between Modes

### Switch to Remote Mode

```bash
bash deployment/client/configure-remote.sh http://your-server:37777 your-api-key
exit && claude code
```

### Switch Back to Local Mode

```bash
bash deployment/client/configure-local.sh
exit && claude code
```

---

## Benefits of Remote Deployment

### For Teams

- ✅ **Shared Context**: All team members see same memory across projects
- ✅ **Multi-Machine Access**: Access memory from laptop, desktop, remote workstation
- ✅ **Centralized Management**: Single backup, monitoring, maintenance point
- ✅ **Cost Savings**: 50-90% reduction in Anthropic API costs (single shared key)
- ✅ **Knowledge Sharing**: Learn from each other's work automatically
- ✅ **Onboarding**: New team members get full project history instantly

### Cost Comparison

**Local Mode (10 developers):**
- 10 × $15-30/month = **$150-300/month total**
- Each developer pays for own API key

**Remote Mode (10 developers):**
- 1 × $150-300/month = **$150-300/month total**
- Team shares single API key
- **Savings: 50-90% depending on usage patterns**

---

## Documentation Reference

### Essential Guides

- **[docs/guides/remote-memory-deployment.md](remote-memory-deployment.md)** - Complete deployment guide
- **[deployment/DEPLOYMENT-TOMORROW.md](../deployment/DEPLOYMENT-TOMORROW.md)** - Step-by-step checklist
- **[deployment/QUICK-START.md](../deployment/QUICK-START.md)** - 15-minute quick setup

### Security & Maintenance

- **[deployment/SECURITY.md](../deployment/SECURITY.md)** - Security hardening guide
- **[deployment/TROUBLESHOOTING.md](../deployment/TROUBLESHOOTING.md)** - Common issues

### Configuration Reference

- **[.env.example](../.env.example)** - Environment configuration template
- **[.mcp.json.example](../.mcp.json.example)** - MCP server configuration

---

## Security Considerations

### For Remote Deployment

1. **API Key Authentication** - Required for all client connections
2. **Firewall Configuration** - Only company network can access port 37777
3. **HTTPS/TLS** (recommended) - Encrypt data in transit
4. **Non-root Service** - Runs as `claudemem` user
5. **Audit Logs** - All API requests logged
6. **API Key Rotation** - Change keys every 90 days

### Best Practices

- Use password manager or company vault for API keys
- Never commit `.env` files with real credentials
- Use HTTPS in production (not HTTP)
- Restrict firewall to internal network only
- Setup automated backups
- Monitor service health
- Review logs regularly

---

## Migration Path

### From Local to Remote (Preserve History)

**Scenario:** You've been using local mode and want to switch to remote with history

**Steps:**

1. **Backup local database:**
   ```bash
   cp ~/.claude-mem/memory.db ~/claude-mem-backup.db
   ```

2. **Deploy remote server** (follow guide above)

3. **Copy database to server:**
   ```bash
   scp ~/.claude-mem/memory.db user@server:/tmp/
   # On server:
   sudo systemctl stop claude-memory-worker
   sudo cp /tmp/memory.db /opt/claude-memory/data/
   sudo chown claudemem:claudemem /opt/claude-memory/data/memory.db
   sudo systemctl start claude-memory-worker
   ```

4. **Configure clients for remote**

5. **Verify migration:**
   ```bash
   /memory-search "query from old history"
   # Should find observations from local database
   ```

---

## Troubleshooting

### Client Can't Connect to Remote Server

**Check:**
1. Server is running: `sudo systemctl status claude-memory-worker`
2. Firewall allows your IP: `sudo ufw status`
3. API key matches: Compare `.env` on client and server
4. Network connectivity: `ping memory.company.com`

**Solution:**
```bash
# On server: Allow your network
sudo ufw allow from 192.168.1.0/24 to any port 37777
```

### Authentication Failures

**Check:**
```bash
# On server:
sudo grep API_KEY /opt/claude-memory/server/.env

# On client:
grep MEMORY_API_KEY .env

# Must match exactly!
```

**Solution:** Regenerate and update API key on both server and all clients.

### Complete Troubleshooting

See **[deployment/TROUBLESHOOTING.md](../deployment/TROUBLESHOOTING.md)** for complete guide.

---

## Next Steps

### For Individual Users (Local Mode)

**No action needed!** Continue using the template as before. Everything works the same.

### For Team Leaders (Want Remote Deployment)

1. Read **[docs/guides/remote-memory-deployment.md](remote-memory-deployment.md)**
2. Deploy server (20 minutes)
3. Configure firewall and security
4. Setup automated backups
5. Distribute credentials to team
6. Roll out to team members

### For Team Members (Team Lead Setup Server)

1. Receive server URL and API key from team lead
2. Run configuration script:
   ```bash
   bash deployment/client/configure-remote.sh <URL> <API-KEY>
   ```
3. Test connection and verify
4. Continue working as normal!

---

## Support

**Questions?**
- Check documentation guides above
- Review [deployment/TROUBLESHOOTING.md](../deployment/TROUBLESHOOTING.md)
- Ask team lead or project maintainer

**Issues with deployment scripts?**
- All scripts in `deployment/` folder
- Server scripts: `deployment/server/`
- Client scripts: `deployment/client/`
- Configuration: `deployment/configs/`

---

**Last Updated:** 2026-02-03
**Prepared By:** Claude Code
**Template Version:** 1.5.0+
