# Remote Persistent Memory Deployment Guide

**Deploy centralized persistent memory for your entire team!**

---

## Overview

The persistent memory system supports **two deployment modes**:

### 🖥️ Local Mode (Default)
- **Best for**: Individual developers, single machines
- **Setup**: Zero configuration (works out of the box)
- **Database**: Local SQLite at `~/.claude-mem/memory.db`
- **Worker**: Runs locally on `http://localhost:37777`
- **Memory**: Private to your machine

### 🌐 Remote Mode (Enterprise)
- **Best for**: Teams, multiple machines, shared context
- **Setup**: One-time server deployment (20 minutes)
- **Database**: Centralized SQLite on remote server
- **Worker**: Runs on company server (e.g., `http://memory.company.com:37777`)
- **Memory**: Shared across team members

---

## When to Use Remote Mode

**Use Remote Mode if:**
- ✅ Working on a team that needs shared context
- ✅ Want to access same memory from multiple machines (laptop, desktop, remote workstation)
- ✅ Need centralized backup and management
- ✅ Want to consolidate AI API costs (single Anthropic API key)
- ✅ Have on-premise server infrastructure

**Use Local Mode if:**
- ✅ Solo developer
- ✅ Working on personal projects
- ✅ Don't need to share memory with others
- ✅ Want simplest setup (zero configuration)

---

## Remote Deployment Overview

### Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Remote Server                       │
│  ┌────────────────────────────────────────────┐    │
│  │  Worker Service (systemd)                   │    │
│  │  - Express HTTP API (port 37777)           │    │
│  │  - AI Compression (Claude Sonnet 4.5)      │    │
│  │  - SQLite Database                         │    │
│  └────────────────────────────────────────────┘    │
│                                                      │
│  /opt/claude-memory/                                │
│  ├── server/          # Application code            │
│  ├── data/            # memory.db                   │
│  ├── logs/            # Worker logs                 │
│  └── backups/         # Automated backups           │
└─────────────────────────────────────────────────────┘
                           ▲
                           │ HTTP API
                           │ (API Key Authentication)
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
   ┌────▼────┐        ┌────▼────┐        ┌───▼─────┐
   │ Client 1│        │ Client 2│        │ Client 3│
   │ (Alice) │        │ (Bob)   │        │ (Carol) │
   └─────────┘        └─────────┘        └─────────┘
```

### Security Features

- 🔐 **API Key Authentication**: Required for all client connections
- 🔥 **Firewall**: Only company network can access port 37777
- 🔒 **HTTPS** (optional): SSL/TLS encryption for data in transit
- 👤 **Non-root User**: Service runs as `claudemem` user (security hardening)
- 📋 **Audit Logs**: All API requests logged for review

---

## Quick Start: Remote Deployment

### Prerequisites

**Server Requirements:**
- Ubuntu 20.04+ or similar Linux distribution
- SSH access with sudo privileges
- Node.js 18+ installed
- Static IP or DNS name
- Open port 37777 (internal network only)
- Internet access (for npm and Claude API)

**You Need:**
- Server IP/hostname: `memory.company.com` or `10.0.1.50`
- SSH credentials
- Anthropic API key

### Step 1: Server Deployment (10 minutes)

**On your local machine:**

```bash
# Navigate to your template project
cd D:\Projects\template-ai-team

# Copy deployment package to server
scp -r deployment/ user@memory.company.com:/tmp/

# SSH to server
ssh user@memory.company.com
```

**On the server:**

```bash
# Navigate to deployment folder
cd /tmp/deployment/server

# Run installation script (creates user, directories, systemd service)
sudo bash install.sh

# Configure environment variables
# Generate API key
API_KEY=$(openssl rand -hex 32)
echo "Your API key: $API_KEY"  # SAVE THIS!

# Edit configuration
sudo nano /opt/claude-memory/server/.env
```

**Set these values in `.env`:**
```bash
# Anthropic API Key (for AI compression)
ANTHROPIC_API_KEY=sk-ant-your-actual-key-here

# API Key for client authentication (the one you generated)
API_KEY=your-32-character-hex-key-here

# Worker settings (keep defaults)
WORKER_PORT=37777
LOG_LEVEL=info
```

**Start the service:**
```bash
# Start worker service
sudo systemctl start claude-memory-worker
sudo systemctl enable claude-memory-worker

# Check status (should show "Active: active (running)")
sudo systemctl status claude-memory-worker

# Test health endpoint
curl http://localhost:37777/api/health
# Should return: {"status":"ok","uptime":X,"timestamp":"..."}
```

### Step 2: Firewall Configuration (3 minutes)

```bash
# Navigate to configs folder
cd /tmp/deployment/configs

# Edit firewall script to match your company network
sudo nano firewall-rules.sh

# Change this line:
INTERNAL_NETWORK="10.0.0.0/8"  # or "192.168.1.0/24" etc.

# Run firewall setup
sudo bash firewall-rules.sh

# Verify firewall
sudo ufw status
# Should show: 37777 allowed from your network
```

### Step 3: Client Configuration (5 minutes)

**On your local machine (Windows):**

```powershell
# Navigate to your project
cd D:\Projects\template-ai-team

# Configure for remote server (use Git Bash)
bash deployment/client/configure-remote.sh http://memory.company.com:37777 your-api-key-here

# Test connection
bash deployment/client/test-connection.sh
# Should show: "✅ All tests passed!"
```

**What the script does:**
1. Updates `.env` with `WORKER_URL` and `MEMORY_API_KEY`
2. Updates `.mcp.json` with remote worker URL
3. Creates backup of old configuration
4. Tests connection to remote server

### Step 4: Verify (1 minute)

```bash
# Restart Claude Code
exit
claude code

# Test memory search
/memory-search "test"
# Should work without errors (may return no results if fresh install)

# Try capturing an observation
cat README.md
# Should be captured and sent to remote server

# Check server logs (on server)
sudo journalctl -u claude-memory-worker -f
# Should show incoming API requests from your client
```

✅ **Deployment complete!** Your client is now using the remote memory server.

---

## Configuration Details

### Client Configuration (.env)

**Local Mode (Default):**
```bash
# Worker runs locally
WORKER_URL=http://localhost:37777
WORKER_PORT=37777

# No API key needed for local
MEMORY_API_KEY=

# Local database path
MEMORY_DB_PATH=$HOME/.claude-mem/memory.db

# Your Anthropic API key (for AI compression)
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

**Remote Mode:**
```bash
# Worker runs on remote server
WORKER_URL=http://memory.company.com:37777

# API key for authentication (required!)
MEMORY_API_KEY=your-32-character-hex-key-here

# Database path not used (remote database)
# MEMORY_DB_PATH is ignored in remote mode

# Anthropic API key not needed on client (server uses its own)
# ANTHROPIC_API_KEY not needed
```

### MCP Server Configuration (.mcp.json)

The MCP server automatically detects remote mode when `WORKER_URL` is set to a non-localhost URL.

**Example .mcp.json (Remote Mode):**
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

- `WORKER_URL` - Replace with your remote server address
- `API_KEY` - Resolved from `MEMORY_API_KEY` environment variable (set by `configure-remote.sh` or manually in `.env`)
- `alwaysAllow` - Auto-approve search tools so memory works without manual approval each time

---

## Switching Between Local and Remote

### Switch to Remote Mode

```bash
# Use the provided script
bash deployment/client/configure-remote.sh http://your-server:37777 your-api-key

# Or manually:
# 1. Edit .env
WORKER_URL=http://your-server:37777
MEMORY_API_KEY=your-api-key-here

# 2. Restart Claude Code
exit
claude code
```

### Switch Back to Local Mode

```bash
# Use the provided script
bash deployment/client/configure-local.sh

# Or manually:
# 1. Edit .env
WORKER_URL=http://localhost:37777
MEMORY_API_KEY=

# 2. Restart Claude Code
exit
claude code
```

---

## Team Rollout

### For Project Leaders

**1. Deploy Server (One Time)**
- Follow "Quick Start: Remote Deployment" above
- Save the API key securely (password manager, company vault)
- Document server URL and firewall rules

**2. Distribute Credentials to Team**

Share with team members (via secure channel):
```
Server URL: http://memory.company.com:37777
API Key: [32-character hex key]

Setup Instructions:
1. cd /path/to/template-ai-team
2. bash deployment/client/configure-remote.sh http://memory.company.com:37777 [API_KEY]
3. bash deployment/client/test-connection.sh
4. Restart Claude Code
```

**3. Verify Team Access**

Have each team member run:
```bash
bash deployment/client/test-connection.sh
# Should show: "✅ All tests passed!"
```

### For Team Members

**Setup (5 minutes):**

```bash
# 1. Navigate to your project
cd /path/to/template-ai-team

# 2. Run configuration script with URL and API key provided by team lead
bash deployment/client/configure-remote.sh http://memory.company.com:37777 your-api-key-here

# 3. Test connection
bash deployment/client/test-connection.sh

# 4. Restart Claude Code
exit
claude code

# 5. Verify memory search works
/memory-search "test"
```

---

## Maintenance

### Server Maintenance

**View Logs:**
```bash
# Real-time logs
sudo journalctl -u claude-memory-worker -f

# Last 50 lines
sudo journalctl -u claude-memory-worker -n 50

# Logs from last 24 hours
sudo journalctl -u claude-memory-worker --since "24 hours ago"
```

**Restart Service:**
```bash
sudo systemctl restart claude-memory-worker
sudo systemctl status claude-memory-worker
```

**Health Check:**
```bash
# On server
curl http://localhost:37777/api/health

# From client
curl http://memory.company.com:37777/api/health -H "X-API-Key: your-api-key"
```

**Database Size:**
```bash
du -h /opt/claude-memory/data/memory.db
```

### Backups

**Manual Backup:**
```bash
sudo bash /opt/claude-memory/scripts/backup.sh
ls -lh /opt/claude-memory/backups/
```

**Automated Backups (Recommended):**
```bash
# Edit crontab
sudo crontab -e

# Add daily backup at 2 AM
0 2 * * * /opt/claude-memory/scripts/backup.sh

# Add health check every 5 minutes
*/5 * * * * /opt/claude-memory/scripts/health-check.sh
```

**Restore from Backup:**
```bash
sudo systemctl stop claude-memory-worker
sudo bash /opt/claude-memory/scripts/restore.sh /opt/claude-memory/backups/memory-backup-YYYYMMDD-HHMMSS.tar.gz
sudo systemctl start claude-memory-worker
```

### Security Hardening

**See [deployment/SECURITY.md](../../deployment/SECURITY.md) for:**
- API key rotation
- HTTPS/TLS setup
- Firewall configuration
- Log monitoring
- Access control
- Update management

---

## Troubleshooting

### Client Can't Connect

**Symptom:** `curl http://memory.company.com:37777/api/health` times out

**Diagnosis:**
```bash
# 1. Check server is running
ssh user@memory.company.com
sudo systemctl status claude-memory-worker

# 2. Test from server (should work)
curl http://localhost:37777/api/health

# 3. Check firewall
sudo ufw status
# Should show: 37777 allowed from your network

# 4. Check your IP is in allowed range
curl ifconfig.me  # Your public IP
# Compare with firewall rule
```

**Solutions:**
```bash
# On server: Allow your IP
sudo ufw allow from YOUR_CLIENT_IP to any port 37777

# On server: Allow your network range
sudo ufw allow from 192.168.1.0/24 to any port 37777
```

### Authentication Failures

**Symptom:** `{"error":"Unauthorized"}`

**Diagnosis:**
```bash
# Check API key matches
# On server:
sudo grep API_KEY /opt/claude-memory/server/.env

# On client:
grep MEMORY_API_KEY .env

# These must match EXACTLY
```

**Solution:**
```bash
# Regenerate API key
openssl rand -hex 32

# Update on server
sudo nano /opt/claude-memory/server/.env
sudo systemctl restart claude-memory-worker

# Update on all clients
# Edit .env and set MEMORY_API_KEY=new-key
# Restart Claude Code
```

### Worker Service Won't Start

**Symptom:** `sudo systemctl status claude-memory-worker` shows "failed"

**Diagnosis:**
```bash
# Check logs for errors
sudo journalctl -u claude-memory-worker -n 50

# Common issues:
# 1. ANTHROPIC_API_KEY not set
# 2. Port 37777 already in use
# 3. Permission issues
```

**Solutions:**
```bash
# Fix permissions
sudo chown -R claudemem:claudemem /opt/claude-memory

# Check port availability
sudo lsof -i :37777

# Verify environment file
sudo cat /opt/claude-memory/server/.env
# Ensure ANTHROPIC_API_KEY is set
```

**See [deployment/TROUBLESHOOTING.md](../../deployment/TROUBLESHOOTING.md) for complete troubleshooting guide.**

---

## Advanced Topics

### HTTPS/SSL Setup

**Why:** Encrypt data in transit between clients and server

**Prerequisites:**
- Domain name pointing to server (e.g., `memory.company.com`)
- OR company SSL certificate

**Option 1: Let's Encrypt (Public Domain)**
```bash
# Install nginx and certbot
sudo apt install nginx certbot python3-certbot-nginx

# Configure nginx reverse proxy
sudo cp deployment/configs/nginx.conf /etc/nginx/sites-available/claude-memory
sudo nano /etc/nginx/sites-available/claude-memory
# Update server_name to your domain

sudo ln -s /etc/nginx/sites-available/claude-memory /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# Get SSL certificate
sudo certbot --nginx -d memory.company.com

# Client configuration
WORKER_URL=https://memory.company.com  # Note: HTTPS
```

**Option 2: Company Certificate**
```bash
# Copy certificates
sudo cp company.crt /etc/ssl/certs/
sudo cp company.key /etc/ssl/private/

# Update nginx.conf with certificate paths
sudo nano /etc/nginx/sites-available/claude-memory
# Add:
# ssl_certificate /etc/ssl/certs/company.crt;
# ssl_certificate_key /etc/ssl/private/company.key;

sudo systemctl reload nginx
```

### Multi-Project Isolation

**Scenario:** Multiple teams using same server, need isolated memory

**Solution:** Each team uses different API key + project name filtering

**Server Setup:**
```bash
# Generate separate API keys for each team
openssl rand -hex 32  # Team A
openssl rand -hex 32  # Team B

# Server supports multiple API keys (comma-separated)
sudo nano /opt/claude-memory/server/.env
API_KEY=team-a-key,team-b-key
```

**Client Setup:**
```bash
# Team A
MEMORY_API_KEY=team-a-key

# Team B
MEMORY_API_KEY=team-b-key
```

**Memory Isolation:**
- Project names automatically separate observations
- Each team only sees their own project's memory
- Database is shared, but queries filter by project

### Monitoring and Alerts

**Setup Monitoring:**
```bash
# Install logwatch
sudo apt install logwatch

# Configure email alerts
sudo nano /etc/cron.daily/00logwatch
# Add:
/usr/sbin/logwatch --output mail --mailto admin@company.com --detail high
```

**Health Check Monitoring:**
```bash
# Add to crontab
*/5 * * * * /opt/claude-memory/scripts/health-check.sh || /opt/claude-memory/scripts/alert.sh

# Create alert script
sudo nano /opt/claude-memory/scripts/alert.sh
```

```bash
#!/bin/bash
# Send alert to Slack/Teams/Email
curl -X POST https://hooks.slack.com/services/YOUR/WEBHOOK/URL \
  -H 'Content-Type: application/json' \
  -d '{"text":"⚠️ Claude Memory Worker is down!"}'
```

---

## Migration Guide

### Migrate from Local to Remote

**Scenario:** You've been using local mode, now want to switch to remote for team sharing

**Steps:**

**1. Backup local database:**
```bash
# macOS/Linux
cp ~/.claude-mem/memory.db ~/claude-mem-backup.db

# Windows
Copy-Item "$env:USERPROFILE\.claude-mem\memory.db" "$env:USERPROFILE\claude-mem-backup.db"
```

**2. Deploy remote server** (follow "Quick Start" above)

**3. Copy local database to server:**
```bash
# From local machine
scp ~/.claude-mem/memory.db user@memory.company.com:/tmp/

# On server
sudo systemctl stop claude-memory-worker
sudo cp /tmp/memory.db /opt/claude-memory/data/
sudo chown claudemem:claudemem /opt/claude-memory/data/memory.db
sudo systemctl start claude-memory-worker
```

**4. Configure clients for remote** (all team members)

**5. Verify migration:**
```bash
/memory-search "query from old local history"
# Should find observations from local database
```

### Migrate Between Servers

**Scenario:** Moving to new server or different hostname

**Steps:**

**1. Backup database on old server:**
```bash
sudo bash /opt/claude-memory/scripts/backup.sh
```

**2. Deploy new server** (follow "Quick Start" above)

**3. Restore backup on new server:**
```bash
# Copy backup from old server
scp user@old-server:/opt/claude-memory/backups/latest.tar.gz /tmp/

# Restore on new server
sudo bash /opt/claude-memory/scripts/restore.sh /tmp/latest.tar.gz
```

**4. Update all clients:**
```bash
# On each client
bash deployment/client/configure-remote.sh http://new-server:37777 same-api-key
```

---

## Cost Considerations

### Anthropic API Costs

**Local Mode:**
- Each developer uses their own Anthropic API key
- Cost: $15-30/month per developer (typical usage)
- Total: $150-300/month for 10 developers

**Remote Mode:**
- Server uses single Anthropic API key
- Cost: $150-300/month for entire team (shared)
- Savings: 50-90% depending on team size

**Compression Settings:**

To reduce API costs, you can adjust compression frequency:

```bash
# On server: /opt/claude-memory/server/.env
COMPRESSION_ENABLED=true
COMPRESSION_BATCH_SIZE=10        # Compress 10 at a time
COMPRESSION_INTERVAL=300000      # Every 5 minutes (default)
# COMPRESSION_INTERVAL=600000    # Every 10 minutes (lower cost)
```

### Server Costs

**Hardware Requirements:**
- CPU: 2 cores minimum
- RAM: 2GB minimum (4GB recommended)
- Disk: 10GB minimum (grows with usage)
- Network: Standard bandwidth

**Hosting Costs:**
- On-premise: Use existing infrastructure (no additional cost)
- Cloud VPS: $10-30/month (DigitalOcean, Linode, Vultr)
- AWS EC2: $15-50/month (t3.small or t3.medium)

---

## Best Practices

### For Team Leaders

1. **Deploy to stable server** - Use production-grade infrastructure
2. **Setup automated backups** - Daily backups to separate storage
3. **Monitor health** - Setup alerts for service downtime
4. **Rotate API keys** - Change keys every 90 days
5. **Review logs** - Check for suspicious activity monthly
6. **Document access** - Keep list of who has API keys
7. **Plan capacity** - Monitor database size and growth

### For Team Members

1. **Protect API key** - Never commit `.env` to Git
2. **Test connection** - Run `test-connection.sh` after any config changes
3. **Report issues** - Tell team lead if server is unreachable
4. **Use privacy tags** - Wrap sensitive data in `<private>` tags
5. **Don't abuse** - Avoid excessive searches (be mindful of costs)

---

## FAQ

**Q: Can I use both local and remote modes simultaneously?**
A: No, you configure one mode at a time. But you can switch anytime.

**Q: What happens to local memory when I switch to remote?**
A: Local memory stays in `~/.claude-mem/memory.db`. You can migrate it to remote server if needed.

**Q: Can team members see each other's work?**
A: Yes, if they work on the same project. Memory is isolated by project name, not by user.

**Q: How much does it cost to run a remote server?**
A: Anthropic API: $150-300/month (team shared). Server: $0-50/month depending on hosting.

**Q: Is HTTPS required?**
A: Not required, but recommended for production. API key provides authentication, HTTPS provides encryption.

**Q: What if server goes down?**
A: Clients will fail gracefully. Claude Code continues to work, but memory capture/search won't work until server is back.

**Q: Can I host on Windows Server?**
A: The deployment scripts are for Linux. Windows Server is possible but requires manual setup and adjustments.

**Q: How do I rotate API keys?**
A: Generate new key, update server `.env`, restart service, distribute new key to all team members, update client `.env` files.

**Q: Can I use multiple remote servers?**
A: Not simultaneously, but you can configure different projects to use different servers by setting `WORKER_URL` per project.

---

## Next Steps

**For New Deployments:**
1. Follow "Quick Start: Remote Deployment" section
2. Setup automated backups
3. Configure firewall
4. Roll out to team
5. Monitor and maintain

**For Existing Local Users:**
1. Backup local database
2. Deploy remote server
3. Migrate database to remote server
4. Switch clients to remote mode
5. Verify migration

**For Documentation:**
- [deployment/DEPLOYMENT-TOMORROW.md](../../deployment/DEPLOYMENT-TOMORROW.md) - Step-by-step deployment checklist
- [deployment/QUICK-START.md](../../deployment/QUICK-START.md) - 15-minute quick setup
- [deployment/SECURITY.md](../../deployment/SECURITY.md) - Security hardening guide
- [deployment/TROUBLESHOOTING.md](../../deployment/TROUBLESHOOTING.md) - Common issues and solutions

---

**Last Updated:** 2026-02-03
**Deployment Scripts Version:** 1.0.0
**Tested On:** Ubuntu 20.04, Ubuntu 22.04, Debian 11
