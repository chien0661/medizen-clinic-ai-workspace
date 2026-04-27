# Claude Memory Worker - Docker Deployment

**Batteries-Included Persistent Memory for Claude Code - Now with Docker! 🐳**

This directory contains everything you need to run the Claude Memory Worker in a Docker container, making deployment simple, portable, and consistent across all platforms.

---

## 🎯 What Is This?

The **Claude Memory Worker** is a persistent memory system for Claude Code that:
- **Remembers context** across sessions automatically
- **Never forgets** past work, decisions, and patterns
- **Shares knowledge** across different Claude Code agents
- **Token-efficient** search with 10x reduction vs traditional RAG
- **Privacy-first** with automatic sensitive data protection

**Docker deployment makes it:**
- ✅ **Easy to deploy** - One command to start
- ✅ **Portable** - Runs anywhere Docker runs
- ✅ **Isolated** - No conflicts with host system
- ✅ **Manageable** - Simple backup, restore, monitoring
- ✅ **Scalable** - Can run on localhost or remote server

---

## 📋 Quick Start (5 Minutes)

### Prerequisites
- Docker 20.10+ installed
- Docker Compose V2 installed
- Anthropic API key from https://console.anthropic.com/

### Deployment Steps

**1. Navigate to deployment folder:**
```bash
cd deployment/docker
```

**2. Configure environment:**
```bash
# Copy example environment file
cp .env.example .env

# Generate API key for authentication
openssl rand -hex 32

# Edit .env and set your keys
nano .env  # or notepad .env on Windows
```

Set these values in `.env`:
```bash
ANTHROPIC_API_KEY=sk-ant-your-key-here
API_KEY=paste-generated-key-here
```

**3. Build and start:**
```bash
docker compose up -d
```

**4. Verify it's running:**
```bash
# Check status
docker compose ps

# Test health endpoint
curl http://localhost:37777/api/health
# Should return: {"status":"ok",...}
```

**5. Configure your client:**

Edit `.mcp.json` in your project root and add:
```json
{
  "mcpServers": {
    "claude-mem": {
      "command": "node",
      "args": ["mcp-servers/claude-mem-server/dist/index.js"],
      "env": {
        "WORKER_URL": "http://localhost:37777",
        "API_KEY": "your-generated-api-key",
        "ANTHROPIC_API_KEY": "your-anthropic-api-key"
      },
      "disabled": false,
      "alwaysAllow": ["search", "timeline", "get_observations"]
    }
  }
}
```

**6. Restart Claude Code:**
```bash
exit
claude code
```

**✅ Done!** Your persistent memory is now active.

---

## 📁 Files in This Directory

```
deployment/docker/
├── README.md                     # This file
├── DOCKER-DEPLOYMENT.md          # Detailed deployment guide
├── QUICK-START-DOCKER.md         # 3-minute quick start
│
├── Dockerfile                    # Docker image configuration
├── docker-compose.yml            # Docker Compose orchestration
├── .env.example                  # Environment template
├── .env                          # Your configuration (gitignored)
│
├── backup.sh                     # Database backup script
├── restore.sh                    # Database restore script
├── health-check.sh               # Health monitoring script
├── test-endpoints.js             # API endpoint tests
│
└── backups/                      # Database backups (auto-created)
```

---

## 🔧 Common Operations

### Start/Stop Container

```bash
# Start
docker compose up -d

# Stop
docker compose down

# Restart
docker compose restart

# View logs
docker compose logs -f
```

### Database Backup

```bash
# Manual backup
bash backup.sh

# Automated (add to cron/Task Scheduler)
# Linux/Mac: Add to crontab
0 2 * * * /path/to/deployment/docker/backup.sh

# Windows: Use Task Scheduler
# - Run: bash.exe
# - Arguments: /path/to/deployment/docker/backup.sh
# - Schedule: Daily at 2 AM
```

### Database Restore

```bash
# List available backups
ls -lh backups/

# Restore specific backup
bash restore.sh backups/memory-20260204-120000.db
```

### Health Monitoring

```bash
# Manual health check
bash health-check.sh

# Automated monitoring (cron)
*/5 * * * * /path/to/deployment/docker/health-check.sh
```

### View Logs

```bash
# Live logs
docker compose logs -f

# Last 50 lines
docker compose logs --tail=50

# Logs for specific time
docker compose logs --since 1h

# Only errors
docker compose logs | grep ERROR
```

---

## 🎨 Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Your Computer                       │
│                                                      │
│  ┌────────────────┐          ┌──────────────────┐  │
│  │  Claude Code   │◄────────►│ Docker Container │  │
│  │                │  HTTP     │                  │  │
│  │  MCP Client    │  :37777   │  Memory Worker   │  │
│  │                │           │                  │  │
│  └────────────────┘           │  ┌────────────┐  │  │
│                               │  │   SQLite   │  │  │
│                               │  │  Database  │  │  │
│                               │  └────────────┘  │  │
│                               └──────────────────┘  │
│                                                      │
│  Volumes (Persistent):                              │
│  • claude-memory-data    (database)                 │
│  • claude-memory-logs    (logs)                     │
│  • claude-memory-backups (backups)                  │
└─────────────────────────────────────────────────────┘
```

**Key Components:**

1. **Docker Container**: Runs the Memory Worker service
2. **SQLite Database**: Stores sessions, observations, summaries
3. **HTTP API**: REST endpoints for memory operations
4. **MCP Server**: Exposes memory search tools to Claude Code
5. **Volumes**: Persist data across container restarts

---

## 🔐 Security

### Built-in Security Features

1. **API Key Authentication**: Required for all client connections
2. **Container Isolation**: Runs as non-root user (claudemem)
3. **Network Isolation**: Bridge network by default
4. **Data Persistence**: Volumes owned by container user
5. **Privacy Tags**: Automatic `<private>` tag stripping

### Production Security Checklist

- [ ] Change default API key (use strong random key)
- [ ] Restrict port 37777 to internal network only
- [ ] Use firewall rules (see DOCKER-DEPLOYMENT.md)
- [ ] Enable HTTPS with reverse proxy (nginx)
- [ ] Regular database backups (automated)
- [ ] Monitor logs for suspicious activity
- [ ] Keep Docker images updated
- [ ] Set resource limits in docker-compose.yml

---

## 📊 Monitoring & Metrics

### Built-in Health Checks

Docker performs automatic health checks every 30 seconds:
```bash
# Check container health
docker inspect --format='{{.State.Health.Status}}' claude-memory-worker
```

### Resource Monitoring

```bash
# Real-time resource usage
docker stats claude-memory-worker

# Container processes
docker top claude-memory-worker

# Disk usage
docker system df
```

### Application Metrics

```bash
# API health
curl http://localhost:37777/api/health

# Database size
docker exec claude-memory-worker du -h /opt/claude-memory/data/memory.db

# Log errors
docker logs claude-memory-worker 2>&1 | grep -i error
```

---

## 🚀 Advanced Usage

### Running on Remote Server

Deploy to a remote server and connect multiple clients:

**On Server:**
```bash
# Deploy as usual
cd deployment/docker
docker compose up -d

# Configure firewall to allow your network
# See DOCKER-DEPLOYMENT.md for details
```

**On Clients:**
Update `.mcp.json`:
```json
{
  "env": {
    "WORKER_URL": "http://your-server.company.com:37777",
    "API_KEY": "shared-team-api-key"
  }
}
```

### Custom Configuration

Edit `docker-compose.yml` to customize:

```yaml
environment:
  # Logging
  - LOG_LEVEL=debug           # debug, info, warn, error

  # CORS
  - ALLOWED_ORIGINS=*         # * for all, or comma-separated URLs

# Resource limits
deploy:
  resources:
    limits:
      cpus: '2'               # Max CPU cores
      memory: 2G              # Max memory
```

### Data Migration

Export data from container:
```bash
# Export database
docker cp claude-memory-worker:/opt/claude-memory/data/memory.db ./exported-db.db

# Import to new container
docker cp ./exported-db.db claude-memory-worker:/opt/claude-memory/data/memory.db
docker compose restart
```

---

## 🐛 Troubleshooting

### Container Won't Start

```bash
# Check logs for errors
docker compose logs

# Common issues:
# 1. Port already in use
sudo lsof -i :37777  # Kill the process or change port

# 2. Missing API key
# Edit .env and set ANTHROPIC_API_KEY

# 3. Permission issues
docker compose down -v  # Remove volumes
docker compose up -d    # Recreate
```

### Client Can't Connect

```bash
# Test from host
curl http://localhost:37777/api/health

# Test from network
curl http://your-server-ip:37777/api/health

# Check firewall
# Windows: Check Windows Firewall
# Linux: sudo ufw status
```

### High Memory Usage

```bash
# Check resource usage
docker stats claude-memory-worker

# Reduce memory limit
# Edit docker-compose.yml:
deploy:
  resources:
    limits:
      memory: 1G  # Reduce from 2G

# Restart
docker compose up -d
```

### Database Corruption

```bash
# Restore from backup
bash restore.sh backups/memory-YYYYMMDD-HHMMSS.db

# Or reset (WARNING: deletes all data)
docker compose down -v
docker compose up -d
```

---

## 📚 Documentation

- **[DOCKER-DEPLOYMENT.md](DOCKER-DEPLOYMENT.md)** - Complete deployment guide with all details
- **[QUICK-START-DOCKER.md](QUICK-START-DOCKER.md)** - Get running in 3 minutes
- **[../README.md](../README.md)** - General deployment documentation
- **[../SECURITY.md](../SECURITY.md)** - Security best practices
- **[../TROUBLESHOOTING.md](../TROUBLESHOOTING.md)** - Detailed troubleshooting

---

## 🤝 Support

**Need help?**
1. Check logs: `docker compose logs -f`
2. Run health check: `bash health-check.sh`
3. Test endpoints: `node test-endpoints.js`
4. Review documentation above

**Common scenarios:**
- First time setup? → Read QUICK-START-DOCKER.md
- Production deployment? → Read DOCKER-DEPLOYMENT.md + SECURITY.md
- Something not working? → Read TROUBLESHOOTING.md
- Want to understand architecture? → Read ../../docs/guide/reference/PERSISTENT_MEMORY_ARCHITECTURE.md

---

## 📝 Version Information

**Package Version**: 1.0.0
**Last Updated**: 2026-02-04
**Docker Image**: claude-memory-worker:latest
**Compatible with**: template-ai-team v1.6.0+

---

## 🎉 Success!

If you've made it this far, your Claude Memory Worker should be running in Docker!

**Verify it's working:**
1. Container is healthy: `docker compose ps` shows "healthy"
2. API responds: `curl http://localhost:37777/api/health` returns `{"status":"ok"}`
3. Client configured: `.mcp.json` has `claude-mem` server
4. Memory active: Restart Claude Code and use `/memory-search`

**Next steps:**
- Set up automated backups (daily recommended)
- Configure monitoring (health-check.sh every 5 minutes)
- Review security settings (SECURITY.md)
- Share with your team (same API key for everyone)

**Happy coding with persistent memory!** 🧠✨
