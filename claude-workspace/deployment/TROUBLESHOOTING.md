# Troubleshooting Guide

Common issues and solutions for the Claude Memory remote deployment.

---

## Service Won't Start

### Symptom
```bash
sudo systemctl start claude-memory-worker
# Returns error or service immediately stops
```

### Solutions

**1. Check service status:**
```bash
sudo systemctl status claude-memory-worker
sudo journalctl -u claude-memory-worker -n 50
```

**2. Check for missing dependencies:**
```bash
cd /opt/claude-memory/server/mcp-servers/claude-mem-server
npm install
npm run build
```

**3. Check environment file:**
```bash
sudo cat /opt/claude-memory/server/.env
# Ensure ANTHROPIC_API_KEY is set
```

**4. Check permissions:**
```bash
sudo chown -R claudemem:claudemem /opt/claude-memory
sudo chmod 750 /opt/claude-memory/server
sudo chmod 770 /opt/claude-memory/data
```

**5. Check port availability:**
```bash
sudo lsof -i :37777
# If port is in use, change WORKER_PORT in .env
```

---

## Client Can't Connect

### Symptom
```bash
curl http://memory.company.com:37777/api/health
# Connection refused or timeout
```

### Solutions

**1. Check server is running:**
```bash
# On server
sudo systemctl status claude-memory-worker
curl http://localhost:37777/api/health
```

**2. Check firewall:**
```bash
# On server
sudo ufw status
sudo ufw allow from <client-ip> to any port 37777
```

**3. Check network connectivity:**
```bash
# From client
ping memory.company.com
telnet memory.company.com 37777
```

**4. Check nginx (if using reverse proxy):**
```bash
# On server
sudo nginx -t
sudo systemctl status nginx
sudo tail -f /var/log/nginx/claude-memory-error.log
```

---

## Database Errors

### Symptom
```
Error: database is locked
```

### Solutions

**1. Stop service and check processes:**
```bash
sudo systemctl stop claude-memory-worker
sudo lsof /opt/claude-memory/data/memory.db
# Kill any stray processes
sudo systemctl start claude-memory-worker
```

**2. Repair database:**
```bash
sudo systemctl stop claude-memory-worker
cd /opt/claude-memory/data
sudo -u claudemem sqlite3 memory.db "PRAGMA integrity_check;"
sudo systemctl start claude-memory-worker
```

**3. Restore from backup:**
```bash
sudo systemctl stop claude-memory-worker
sudo bash /opt/claude-memory/scripts/restore.sh /opt/claude-memory/backups/memory-backup-YYYYMMDD-HHMMSS.tar.gz
sudo systemctl start claude-memory-worker
```

---

## High Memory Usage

### Symptom
Worker process using > 1GB RAM

### Solutions

**1. Check observation queue:**
```bash
curl http://localhost:37777/api/health
# Look at queue size in response
```

**2. Restart service:**
```bash
sudo systemctl restart claude-memory-worker
```

**3. Adjust memory limit:**
```bash
sudo nano /etc/systemd/system/claude-memory-worker.service
# Change: MemoryLimit=2G to higher value
sudo systemctl daemon-reload
sudo systemctl restart claude-memory-worker
```

---

## Authentication Failures

### Symptom
```
{"error":"Unauthorized"}
```

### Solutions

**1. Check API key matches:**
```bash
# On server
sudo grep API_KEY /opt/claude-memory/server/.env

# On client
grep MEMORY_API_KEY .env
# These must match!
```

**2. Regenerate API key:**
```bash
# On server
openssl rand -hex 32
# Update /opt/claude-memory/server/.env
sudo systemctl restart claude-memory-worker

# On clients
# Update MEMORY_API_KEY in .env
```

---

## Logs Show Errors

### Check Logs

```bash
# Systemd journal
sudo journalctl -u claude-memory-worker -f

# Application logs
sudo tail -f /opt/claude-memory/logs/worker-*.log

# Nginx logs (if using)
sudo tail -f /var/log/nginx/claude-memory-error.log
```

### Common Errors

**"ANTHROPIC_API_KEY not set"**
```bash
sudo nano /opt/claude-memory/server/.env
# Add: ANTHROPIC_API_KEY=sk-ant-...
sudo systemctl restart claude-memory-worker
```

**"EADDRINUSE: address already in use"**
```bash
sudo lsof -i :37777
# Kill the process or change port
```

**"Permission denied"**
```bash
sudo chown -R claudemem:claudemem /opt/claude-memory
sudo systemctl restart claude-memory-worker
```

---

## Performance Issues

### Slow Response Times

**1. Check database size:**
```bash
du -h /opt/claude-memory/data/memory.db
# If > 1GB, consider archiving old data
```

**2. Check system resources:**
```bash
top -p $(pgrep -f "node dist/services/worker.js")
df -h /opt/claude-memory
```

**3. Enable query optimization:**
```sql
# Vacuum database
sqlite3 /opt/claude-memory/data/memory.db "VACUUM;"
```

---

## SSL/HTTPS Issues

### Certificate Errors

**1. Check certificate validity:**
```bash
openssl x509 -in /etc/ssl/certs/company.crt -text -noout
```

**2. Test SSL configuration:**
```bash
sudo nginx -t
openssl s_client -connect memory.company.com:443
```

**3. Renew Let's Encrypt certificate:**
```bash
sudo certbot renew
sudo systemctl reload nginx
```

---

## Backup/Restore Issues

### Backup Fails

```bash
# Check disk space
df -h /opt/claude-memory/backups

# Check permissions
ls -la /opt/claude-memory/backups

# Manual backup
sudo -u claudemem cp /opt/claude-memory/data/memory.db /opt/claude-memory/backups/manual-backup-$(date +%Y%m%d).db
```

### Restore Fails

```bash
# Extract backup manually
tar -xzf backup-file.tar.gz -C /tmp/restore
sudo cp /tmp/restore/memory.db /opt/claude-memory/data/
sudo chown claudemem:claudemem /opt/claude-memory/data/memory.db
sudo systemctl restart claude-memory-worker
```

---

## Monitoring Alerts

### Health Check Fails

```bash
# Run full health check
sudo bash /opt/claude-memory/scripts/health-check.sh

# Check each component manually
sudo systemctl status claude-memory-worker
curl http://localhost:37777/api/health
ls -lh /opt/claude-memory/data/memory.db
```

---

## Getting Help

If issues persist:

1. **Collect diagnostics:**
```bash
# Create diagnostic bundle
sudo bash /opt/claude-memory/scripts/diagnostics.sh
# Sends output to /tmp/claude-memory-diagnostics.txt
```

2. **Contact support with:**
   - Error messages from logs
   - Output of `systemctl status claude-memory-worker`
   - Output of health check script
   - System information (OS, Node version)

3. **Emergency recovery:**
```bash
# Stop everything
sudo systemctl stop claude-memory-worker

# Backup current state
sudo cp -r /opt/claude-memory /opt/claude-memory.backup

# Reinstall
sudo bash /tmp/deployment/server/install.sh

# Restore data
sudo cp /opt/claude-memory.backup/data/memory.db /opt/claude-memory/data/
sudo systemctl start claude-memory-worker
```

---

**Last Updated:** 2026-02-03
