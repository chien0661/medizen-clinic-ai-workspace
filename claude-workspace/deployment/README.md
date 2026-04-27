# Remote On-Premise Deployment Guide

**Persistent Memory System - Remote Server Setup**

This guide will help you deploy the persistent memory worker service on your company's on-premise server.

---

## 📋 Prerequisites

### Server Requirements
- **OS**: Ubuntu 20.04+ / RHEL 8+ / Debian 11+
- **RAM**: 2GB minimum, 4GB recommended
- **Disk**: 10GB minimum for application + database growth
- **CPU**: 2 cores minimum
- **Network**: Static IP or internal DNS name
- **Ports**: 37777 (worker), 443 (HTTPS optional)

### Software Requirements
- Node.js 18+ (LTS recommended)
- npm 8+
- nginx (for reverse proxy)
- git
- systemd (for service management)

### Access Requirements
- SSH access to server
- sudo privileges
- Firewall rules configured
- Internal network access from client machines

---

## 🚀 Quick Start (5 Steps)

### Step 1: Copy Deployment Package to Server
```bash
# On your local machine
scp -r deployment/ user@your-server.company.com:/tmp/

# SSH to server
ssh user@your-server.company.com
```

### Step 2: Run Installation Script
```bash
cd /tmp/deployment/server
sudo bash install.sh
```

### Step 3: Configure Environment
```bash
sudo nano /opt/claude-memory/server/.env
# Set your ANTHROPIC_API_KEY and other settings
```

### Step 4: Start Service
```bash
sudo systemctl start claude-memory-worker
sudo systemctl enable claude-memory-worker
sudo systemctl status claude-memory-worker
```

### Step 5: Configure Clients
```bash
# On each client machine
cd /path/to/template-ai-team
bash deployment/client/configure-remote.sh http://your-server.company.com:37777
```

**Done!** Your remote memory system is ready.

---

## 📁 Deployment Package Contents

```
deployment/
├── README.md                           # This file
├── SECURITY.md                         # Security best practices
├── TROUBLESHOOTING.md                  # Common issues and solutions
│
├── server/                             # Server-side scripts
│   ├── install.sh                      # Complete installation script
│   ├── uninstall.sh                    # Removal script
│   ├── upgrade.sh                      # Upgrade script
│   ├── backup.sh                       # Database backup script
│   ├── restore.sh                      # Database restore script
│   ├── health-check.sh                 # Health monitoring script
│   └── .env.example                    # Environment configuration template
│
├── client/                             # Client-side scripts
│   ├── configure-remote.sh             # Configure client to use remote server
│   ├── configure-local.sh              # Revert to local mode
│   └── test-connection.sh              # Test remote connection
│
├── configs/                            # Configuration files
│   ├── claude-memory-worker.service    # Systemd service file
│   ├── nginx.conf                      # Nginx reverse proxy config
│   ├── logrotate.conf                  # Log rotation config
│   └── firewall-rules.sh               # Firewall setup script
│
└── scripts/                            # Utility scripts
    ├── migrate-to-postgres.sh          # Migrate from SQLite to PostgreSQL
    ├── add-api-auth.sh                 # Add API key authentication
    ├── setup-ssl.sh                    # Setup SSL certificates
    ├── monitor.sh                      # Monitoring and alerting
    └── multi-tenant.sh                 # Enable multi-tenant mode
```

---

## 🔧 Detailed Setup Instructions

### Installation Steps

**1. Prepare Server**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Node.js 20 LTS
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Install other dependencies
sudo apt install -y git nginx certbot python3-certbot-nginx
```

**2. Create Application User**
```bash
# Create dedicated user (security best practice)
sudo useradd -r -s /bin/bash -d /opt/claude-memory -m claudemem
```

**3. Run Installation Script**
```bash
cd /tmp/deployment/server
sudo bash install.sh
```

The script will:
- Clone the repository
- Install dependencies
- Build the MCP server
- Create systemd service
- Setup directories and permissions
- Configure nginx (optional)
- Setup firewall rules

**4. Configure Environment**
```bash
sudo nano /opt/claude-memory/server/.env
```

**Required settings:**
```bash
# Anthropic API Key (REQUIRED)
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxx

# Worker Configuration
WORKER_PORT=37777
NODE_ENV=production

# Database Configuration
MEMORY_DB_PATH=/opt/claude-memory/data/memory.db

# Security (IMPORTANT!)
API_KEY=your-secure-random-key-here
ALLOWED_ORIGINS=http://localhost,http://10.0.0.0/8

# Logging
LOG_LEVEL=info
LOG_PATH=/opt/claude-memory/logs
```

**5. Start and Enable Service**
```bash
sudo systemctl daemon-reload
sudo systemctl start claude-memory-worker
sudo systemctl enable claude-memory-worker

# Check status
sudo systemctl status claude-memory-worker

# View logs
sudo journalctl -u claude-memory-worker -f
```

**6. Verify Installation**
```bash
# Test health endpoint
curl http://localhost:37777/api/health

# Should return:
# {"status":"ok","uptime":X,"timestamp":"..."}
```

---

## 👥 Client Configuration

### Option 1: Using Configuration Script (Recommended)

```bash
# On each client machine
cd /path/to/template-ai-team

# Configure for remote server
bash deployment/client/configure-remote.sh http://memory.company.com:37777

# Test connection
bash deployment/client/test-connection.sh

# Restart Claude Code
exit
claude code
```

### Option 2: Manual Configuration

**Update `.mcp.json`:**
```json
{
  "mcpServers": {
    "claude-mem": {
      "command": "node",
      "args": ["mcp-servers/claude-mem-server/dist/index.js"],
      "env": {
        "WORKER_URL": "http://memory.company.com:37777",
        "API_KEY": "${MEMORY_API_KEY}",
        "ANTHROPIC_API_KEY": "${ANTHROPIC_API_KEY}"
      },
      "disabled": false,
      "alwaysAllow": ["search", "timeline", "get_observations"]
    }
  }
}
```

**Update `.env`:**
```bash
WORKER_URL=http://memory.company.com:37777
MEMORY_API_KEY=your-secure-random-key-here
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxx
```

**Update hooks:**
```bash
# No changes needed - hooks read WORKER_URL from environment
export WORKER_URL=http://memory.company.com:37777
```

---

## 🔒 Security Setup

### 1. API Key Authentication

```bash
# Generate secure API key
openssl rand -hex 32

# Add to server .env
API_KEY=generated-key-here

# Add to client .env
MEMORY_API_KEY=generated-key-here
```

### 2. Firewall Configuration

```bash
# Run firewall setup
sudo bash deployment/configs/firewall-rules.sh

# Or manually:
sudo ufw allow from 10.0.0.0/8 to any port 37777
sudo ufw allow 22  # SSH
sudo ufw allow 443 # HTTPS (if using nginx)
sudo ufw enable
```

### 3. SSL/HTTPS Setup (Recommended)

```bash
# Using Let's Encrypt (if server has public domain)
sudo bash deployment/scripts/setup-ssl.sh memory.company.com

# Or use company SSL certificates
sudo cp /path/to/company.crt /etc/ssl/certs/
sudo cp /path/to/company.key /etc/ssl/private/
sudo bash deployment/configs/nginx.conf
```

---

## 📊 Monitoring & Maintenance

### Health Monitoring

```bash
# Run health check script
bash deployment/server/health-check.sh

# Setup cron for automated monitoring
sudo crontab -e
# Add:
*/5 * * * * /opt/claude-memory/scripts/health-check.sh
```

### Database Backup

```bash
# Manual backup
sudo bash deployment/server/backup.sh

# Automated daily backup
sudo crontab -e
# Add:
0 2 * * * /opt/claude-memory/scripts/backup.sh
```

### Log Management

```bash
# View worker logs
sudo journalctl -u claude-memory-worker -f

# View application logs
sudo tail -f /opt/claude-memory/logs/worker-*.log

# Setup log rotation (automatic with logrotate.conf)
sudo cp deployment/configs/logrotate.conf /etc/logrotate.d/claude-memory
```

---

## 🔄 Maintenance Tasks

### Restart Service
```bash
sudo systemctl restart claude-memory-worker
```

### Stop Service
```bash
sudo systemctl stop claude-memory-worker
```

### Update Worker
```bash
sudo bash deployment/server/upgrade.sh
```

### Check Database Size
```bash
du -h /opt/claude-memory/data/memory.db
```

### Clean Old Logs
```bash
sudo find /opt/claude-memory/logs -name "*.log" -mtime +30 -delete
```

---

## 🚨 Troubleshooting

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for detailed solutions.

**Quick fixes:**

```bash
# Service won't start
sudo journalctl -u claude-memory-worker -n 50

# Port already in use
sudo lsof -i :37777

# Permission issues
sudo chown -R claudemem:claudemem /opt/claude-memory

# Database locked
sudo systemctl restart claude-memory-worker
```

---

## 📞 Support

For issues or questions:
1. Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
2. Check logs: `sudo journalctl -u claude-memory-worker -f`
3. Check health: `curl http://localhost:37777/api/health`
4. Contact your team administrator

---

## 🎯 Next Steps

After deployment:
1. ✅ Test from one client machine first
2. ✅ Monitor logs for 24 hours
3. ✅ Setup automated backups
4. ✅ Configure monitoring alerts
5. ✅ Roll out to all team members
6. ✅ Document your company-specific setup

---

**Deployment Package Version:** 1.0.0
**Last Updated:** 2026-02-03
**Compatible with:** template-ai-team v1.6.0+
