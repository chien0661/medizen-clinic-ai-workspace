# Security Best Practices

Security guidelines for deploying Claude Memory on-premise.

---

## 🔒 Essential Security Measures

### 1. API Key Authentication

**Generate a secure API key:**
```bash
# On server
openssl rand -hex 32
```

**Server configuration** (`/opt/claude-memory/server/.env`):
```bash
API_KEY=your-32-character-hex-key-here
```

**Client configuration** (`.env`):
```bash
MEMORY_API_KEY=same-32-character-hex-key-here
```

**Rotate keys regularly:**
- Generate new key every 90 days
- Distribute to all clients
- Restart server after update

---

### 2. Network Security

**Firewall Rules:**
```bash
# Only allow from company network
sudo ufw allow from 10.0.0.0/8 to any port 37777

# Or specific subnets
sudo ufw allow from 192.168.1.0/24 to any port 37777
sudo ufw allow from 192.168.2.0/24 to any port 37777
```

**Use VPN for remote access:**
- Require VPN connection for access
- Don't expose port 37777 to internet
- Use private network only

---

### 3. HTTPS/TLS

**Always use HTTPS in production:**

```bash
# Option 1: Let's Encrypt (if public domain)
sudo certbot --nginx -d memory.company.com

# Option 2: Company certificates
sudo cp company.crt /etc/ssl/certs/
sudo cp company.key /etc/ssl/private/
# Update nginx.conf with certificate paths
```

**Update client configuration:**
```bash
# Use HTTPS URL
WORKER_URL=https://memory.company.com
```

---

### 4. File Permissions

**Correct permissions:**
```bash
# Application directory
sudo chmod 750 /opt/claude-memory
sudo chown -R claudemem:claudemem /opt/claude-memory

# Environment file (contains secrets!)
sudo chmod 600 /opt/claude-memory/server/.env
sudo chown claudemem:claudemem /opt/claude-memory/server/.env

# Database
sudo chmod 660 /opt/claude-memory/data/memory.db
sudo chown claudemem:claudemem /opt/claude-memory/data/memory.db

# Logs
sudo chmod 770 /opt/claude-memory/logs
sudo chown claudemem:claudemem /opt/claude-memory/logs
```

---

### 5. systemd Security

**Service hardening** (already in service file):
```ini
[Service]
# Run as non-root user
User=claudemem
Group=claudemem

# Security options
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true

# Resource limits
LimitNOFILE=65536
MemoryLimit=2G
```

---

### 6. Secrets Management

**Never commit secrets:**
- `.env` files must not be in git
- Use environment variables
- Use secret management tools

**Protect API keys:**
```bash
# Server
chmod 600 /opt/claude-memory/server/.env

# Client
chmod 600 /path/to/project/.env

# Add to .gitignore
echo ".env" >> .gitignore
echo ".env.*" >> .gitignore
```

---

### 7. Database Security

**Encrypt sensitive data:**
```bash
# Use encrypted filesystem for database
sudo cryptsetup luksFormat /dev/sdb1
sudo cryptsetup open /dev/sdb1 encrypted_db
sudo mkfs.ext4 /dev/mapper/encrypted_db
sudo mount /dev/mapper/encrypted_db /opt/claude-memory/data
```

**Regular backups:**
```bash
# Automated encrypted backup
sudo bash /opt/claude-memory/scripts/backup.sh
# Store backups on encrypted storage
```

**Database access control:**
```bash
# Only claudemem user can access
sudo chmod 660 /opt/claude-memory/data/memory.db
```

---

### 8. Logging and Monitoring

**Secure logs:**
```bash
# Restrict log access
sudo chmod 640 /var/log/nginx/claude-memory-*.log
sudo chown root:adm /var/log/nginx/claude-memory-*.log
```

**Monitor for security events:**
```bash
# Failed authentication attempts
sudo journalctl -u claude-memory-worker | grep "Unauthorized"

# Unusual activity
sudo journalctl -u claude-memory-worker | grep "ERROR"

# Setup alerting
sudo apt install logwatch
# Configure email alerts
```

---

### 9. Access Control

**Restrict SSH access:**
```bash
# Use SSH keys only
sudo nano /etc/ssh/sshd_config
# Set: PasswordAuthentication no
# Set: PermitRootLogin no
sudo systemctl restart sshd
```

**sudo access:**
```bash
# Limit who can manage service
sudo visudo
# Add: yourusername ALL=(ALL) /usr/bin/systemctl * claude-memory-worker
```

---

### 10. Update Management

**Keep system updated:**
```bash
# Regular updates
sudo apt update && sudo apt upgrade

# Security-only updates
sudo apt install unattended-upgrades
sudo dpkg-reconfigure unattended-upgrades
```

**Update Node.js:**
```bash
# Check for updates
npm outdated -g npm

# Update to LTS
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt install -y nodejs
```

---

## 🚨 Security Checklist

Before going to production:

- [ ] API key authentication enabled
- [ ] Firewall configured (only internal network)
- [ ] HTTPS/TLS enabled
- [ ] File permissions correct (600 for .env, 750 for dirs)
- [ ] Service runs as non-root user (claudemem)
- [ ] Secrets not in git repository
- [ ] Database on encrypted filesystem (optional but recommended)
- [ ] Log monitoring configured
- [ ] Automated backups enabled
- [ ] SSH hardened (key-only, no root)
- [ ] System updates automated
- [ ] Security audit completed

---

## 🔍 Security Audit Commands

```bash
# Check running services
sudo netstat -tlnp | grep 37777

# Check user permissions
id claudemem
sudo -l -U claudemem

# Check file permissions
ls -la /opt/claude-memory/server/.env
ls -la /opt/claude-memory/data/memory.db

# Check for exposed ports
sudo nmap localhost

# Check systemd security
systemctl show claude-memory-worker | grep -E "(User|Group|NoNewPrivileges|ProtectSystem|ProtectHome)"

# Review logs for issues
sudo journalctl -u claude-memory-worker --since "24 hours ago" | grep -i "error\|fail\|unauthorized"
```

---

## 📞 Incident Response

**If security breach suspected:**

1. **Immediate actions:**
```bash
# Stop service
sudo systemctl stop claude-memory-worker

# Block network access
sudo ufw deny 37777

# Backup for forensics
sudo cp -r /opt/claude-memory /forensics/claude-memory-$(date +%Y%m%d-%H%M%S)
```

2. **Investigate:**
```bash
# Check logs
sudo journalctl -u claude-memory-worker --since "7 days ago" > /tmp/logs.txt

# Check connections
sudo netstat -an | grep 37777

# Check file changes
sudo find /opt/claude-memory -type f -mtime -1
```

3. **Recovery:**
```bash
# Rotate all keys
openssl rand -hex 32  # New API key

# Update all clients
# ...

# Restore from clean backup if needed
sudo bash /opt/claude-memory/scripts/restore.sh /opt/claude-memory/backups/clean-backup.tar.gz

# Review and harden security
# Follow this checklist again
```

---

## 📚 Additional Resources

- OWASP Security Guidelines: https://owasp.org/
- Node.js Security Best Practices: https://nodejs.org/en/docs/guides/security/
- systemd Security: https://www.freedesktop.org/software/systemd/man/systemd.exec.html
- nginx Security: https://nginx.org/en/docs/http/ngx_http_ssl_module.html

---

**Remember: Security is a process, not a product. Review and update regularly!**

**Last Updated:** 2026-02-03
