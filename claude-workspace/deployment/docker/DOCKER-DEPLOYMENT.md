# Docker Deployment Guide
**Claude Persistent Memory - Remote Server with Docker**

This guide shows you how to deploy the Claude Memory Worker using Docker, making it easy to run on any machine with Docker installed.

---

## 📋 Prerequisites

### On Your Server (or any machine with Docker)
- Docker 20.10+ installed
- Docker Compose V2 installed
- 2GB RAM minimum (4GB recommended)
- 10GB disk space
- Network access from client machines

### What You Need
- Anthropic API key (from https://console.anthropic.com/)
- Server IP address or hostname
- API key for authentication (we'll generate this)

---

## 🚀 Quick Start (5 Minutes)

### Step 1: Prepare Deployment Files

```bash
# On your local machine, copy deployment folder to server
# Option A: Using SCP
scp -r deployment/ user@your-server:/tmp/

# Option B: Clone repository on server
ssh user@your-server
git clone https://bitbucket.vissoft.vn/scm/ct/template-ai-team.git /tmp/template-ai-team
```

### Step 2: Navigate to Docker Deployment

```bash
# SSH to your server
ssh user@your-server

# Go to Docker deployment directory
cd /tmp/template-ai-team/deployment/docker
```

### Step 3: Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Generate API key for authentication
API_KEY=$(openssl rand -hex 32)
echo "Save this API key: $API_KEY"

# Edit .env file
nano .env
```

**Set these values in `.env`:**
```bash
# REQUIRED: Your Anthropic API key
ANTHROPIC_API_KEY=sk-ant-your-actual-key-here

# OPTIONAL: API key for client authentication (paste the generated key)
API_KEY=paste-generated-key-here

# OPTIONAL: Logging level
LOG_LEVEL=info

# OPTIONAL: Allowed origins (use * for development, specific IPs for production)
ALLOWED_ORIGINS=*
```

Save and exit (Ctrl+X, Y, Enter)

### Step 4: Build and Start Container

```bash
# Build the Docker image
docker compose build

# Start the service
docker compose up -d

# Check status
docker compose ps

# View logs
docker compose logs -f
```

**Expected output:**
```
NAME                      IMAGE                          STATUS         PORTS
claude-memory-worker      claude-memory-worker:latest    Up X seconds   0.0.0.0:37777->37777/tcp
```

### Step 5: Verify Service is Running

```bash
# Test health endpoint
curl http://localhost:37777/api/health

# Expected output:
# {"status":"ok","uptime":X,"timestamp":"..."}
```

✅ **Docker deployment complete!**

---

## 💻 Client Configuration

### On Your Local Machine (Windows)

```powershell
# Navigate to your project
cd D:\01. PROJECTS\05.Internal\template-ai-team

# Configure for remote server (use Git Bash or WSL)
bash deployment/client/configure-remote.sh http://your-server-ip:37777 your-api-key

# Test connection
bash deployment/client/test-connection.sh
```

**Expected:** ✅ All tests passed!

### Restart Claude Code

```bash
# Exit current session
exit

# Start new session
claude code

# Test memory search
/memory-search "test"
```

✅ **Client configured!**

---

## 🔧 Docker Management

### Service Management

```bash
# Start service
docker compose up -d

# Stop service
docker compose down

# Restart service
docker compose restart

# View logs
docker compose logs -f

# View last 50 lines
docker compose logs --tail=50

# Check status
docker compose ps

# View resource usage
docker stats claude-memory-worker
```

### Database Management

```bash
# Backup database
docker compose exec claude-memory-worker sh -c 'cp /opt/claude-memory/data/memory.db /opt/claude-memory/backups/memory-$(date +%Y%m%d-%H%M%S).db'

# List backups
docker compose exec claude-memory-worker ls -lh /opt/claude-memory/backups/

# Check database size
docker compose exec claude-memory-worker du -h /opt/claude-memory/data/memory.db

# Access container shell
docker compose exec claude-memory-worker sh
```

### Volume Management

```bash
# List volumes
docker volume ls | grep claude-memory

# Inspect volume
docker volume inspect deployment_claude-memory-data

# Backup volume to host
docker run --rm -v deployment_claude-memory-data:/data -v $(pwd):/backup alpine tar czf /backup/memory-backup-$(date +%Y%m%d).tar.gz -C /data .

# Restore volume from backup
docker run --rm -v deployment_claude-memory-data:/data -v $(pwd):/backup alpine tar xzf /backup/memory-backup-YYYYMMDD.tar.gz -C /data
```

---

## 🔒 Security Configuration

### 1. Enable API Key Authentication

Already done in Step 3! The API_KEY in `.env` file enables authentication.

### 2. Restrict Network Access

**Option A: Use Docker networks (recommended)**
```bash
# Already configured in docker-compose.yml
# Only expose port 37777 to specific IP ranges via firewall
```

**Option B: Configure host firewall**
```bash
# Allow only specific network
sudo ufw allow from 10.0.0.0/8 to any port 37777

# Or allow specific IPs
sudo ufw allow from 192.168.1.100 to any port 37777
```

### 3. Use HTTPS (Recommended for Production)

Add Nginx reverse proxy:

```bash
# Install nginx
sudo apt install nginx

# Copy nginx config
sudo cp ../configs/nginx.conf /etc/nginx/sites-available/claude-memory
sudo ln -s /etc/nginx/sites-available/claude-memory /etc/nginx/sites-enabled/

# Edit config
sudo nano /etc/nginx/sites-available/claude-memory
# Update: server_name your-domain.com;
# Update: proxy_pass http://localhost:37777;

# Test and reload
sudo nginx -t
sudo systemctl reload nginx

# Get SSL certificate
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

---

## 📊 Monitoring & Maintenance

### Health Checks

```bash
# Docker built-in health check
docker inspect --format='{{.State.Health.Status}}' claude-memory-worker

# Manual health check
curl http://localhost:37777/api/health

# Continuous monitoring
watch -n 5 'curl -s http://localhost:37777/api/health | jq'
```

### Automated Backups

Create backup script:

```bash
# Create backup script
cat > /opt/claude-memory-backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/claude-memory-backups"
DATE=$(date +%Y%m%d-%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup database
docker compose -f /tmp/template-ai-team/deployment/docker/docker-compose.yml exec -T claude-memory-worker sh -c \
  "cp /opt/claude-memory/data/memory.db /opt/claude-memory/backups/memory-$DATE.db"

# Keep only last 30 days
find $BACKUP_DIR -name "memory-*.db" -mtime +30 -delete

echo "Backup completed: memory-$DATE.db"
EOF

# Make executable
chmod +x /opt/claude-memory-backup.sh

# Add to crontab (daily at 2 AM)
(crontab -l 2>/dev/null; echo "0 2 * * * /opt/claude-memory-backup.sh") | crontab -
```

### Log Management

```bash
# View logs with timestamps
docker compose logs -f --timestamps

# Filter error logs
docker compose logs | grep ERROR

# Export logs
docker compose logs > memory-worker-logs-$(date +%Y%m%d).log

# Log rotation (automatic with Docker)
# Configure in /etc/docker/daemon.json:
cat /etc/docker/daemon.json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

---

## 🆙 Upgrading

### Update to New Version

```bash
# Pull latest code
cd /tmp/template-ai-team
git pull origin master

# Rebuild image
cd deployment/docker
docker compose build

# Stop old container
docker compose down

# Start new container
docker compose up -d

# Verify
docker compose ps
curl http://localhost:37777/api/health
```

---

## 🚨 Troubleshooting

### Container Won't Start

```bash
# Check logs for errors
docker compose logs

# Common issues:
# 1. Port 37777 already in use
sudo lsof -i :37777
# Kill process or change port in docker-compose.yml

# 2. Missing API key
# Edit .env and add ANTHROPIC_API_KEY

# 3. Permission issues
docker compose down
docker volume rm deployment_claude-memory-data
docker compose up -d
```

### Client Can't Connect

```bash
# Test from server
curl http://localhost:37777/api/health

# Test from network
curl http://server-ip:37777/api/health

# Check firewall
sudo ufw status
sudo ufw allow 37777

# Check Docker port binding
docker port claude-memory-worker
```

### Database Issues

```bash
# Check database file
docker compose exec claude-memory-worker ls -lh /opt/claude-memory/data/

# Reset database (WARNING: deletes all data)
docker compose down
docker volume rm deployment_claude-memory-data
docker compose up -d
```

### High Resource Usage

```bash
# Check resource usage
docker stats claude-memory-worker

# Adjust limits in docker-compose.yml:
deploy:
  resources:
    limits:
      cpus: '1'        # Reduce CPU limit
      memory: 1G       # Reduce memory limit

# Restart
docker compose up -d
```

---

## 🧹 Cleanup

### Remove Everything

```bash
# Stop and remove containers
docker compose down

# Remove volumes (WARNING: deletes all data)
docker compose down -v

# Remove images
docker rmi claude-memory-worker:latest

# Remove all unused Docker resources
docker system prune -a --volumes
```

---

## 📝 Production Checklist

- [ ] `.env` file configured with valid ANTHROPIC_API_KEY
- [ ] API_KEY generated and shared with team
- [ ] Container running (docker compose ps shows "Up")
- [ ] Health check passing (curl http://localhost:37777/api/health)
- [ ] Client connection tested (test-connection.sh)
- [ ] Firewall configured (restrict to internal network)
- [ ] HTTPS/SSL configured (optional but recommended)
- [ ] Automated backups scheduled (crontab)
- [ ] Monitoring setup (health checks)
- [ ] Resource limits configured (docker-compose.yml)
- [ ] Log rotation configured (/etc/docker/daemon.json)
- [ ] Documentation updated (server IP, API key location)

---

## 🎯 Next Steps

After successful deployment:

1. **Test from multiple clients**: Ensure all team members can connect
2. **Monitor for 24 hours**: Check logs and health
3. **Setup alerts**: Configure monitoring alerts
4. **Document for team**: Share server URL and API key securely
5. **Plan maintenance window**: Schedule regular updates

---

## 📞 Support

**Documentation:**
- [Deployment README](../README.md)
- [Security Guide](../SECURITY.md)
- [Troubleshooting](../TROUBLESHOOTING.md)

**Common Commands:**
```bash
# Quick health check
docker compose ps && curl http://localhost:37777/api/health

# View recent logs
docker compose logs --tail=50

# Restart service
docker compose restart

# Full reset
docker compose down && docker compose up -d
```

---

**Deployment Package Version:** 1.0.0
**Last Updated:** 2026-02-04
**Docker Compose Version:** 2.x
**Compatible with:** template-ai-team v1.6.0+
