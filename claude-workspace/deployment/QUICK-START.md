# Quick Start Guide - Remote Server Setup

**Get your remote memory server running in 15 minutes!**

---

## ☑️ Pre-Flight Checklist

Before starting, ensure you have:
- [ ] Ubuntu 20.04+ server (or similar Linux)
- [ ] SSH access with sudo privileges
- [ ] Server has static IP or DNS name
- [ ] Node.js 18+ installed on server
- [ ] git installed on server
- [ ] Anthropic API key ready
- [ ] Company network configured (firewall/VPN)

---

## 🚀 Server Setup (10 minutes)

### Step 1: Copy deployment package to server
```bash
# On your local machine
scp -r deployment/ user@your-server.company.com:/tmp/
```

### Step 2: SSH to server
```bash
ssh user@your-server.company.com
```

### Step 3: Run installation
```bash
cd /tmp/deployment/server
sudo bash install.sh
```

Wait 2-3 minutes for installation to complete.

### Step 4: Configure environment
```bash
# Generate API key
API_KEY=$(openssl rand -hex 32)
echo "Your API key: $API_KEY"  # Save this!

# Edit configuration
sudo nano /opt/claude-memory/server/.env
```

**Set these values:**
```bash
ANTHROPIC_API_KEY=sk-ant-your-key-here
API_KEY=the-key-you-generated-above
```

Save and exit (Ctrl+X, Y, Enter)

### Step 5: Start service
```bash
sudo systemctl start claude-memory-worker
sudo systemctl enable claude-memory-worker
sudo systemctl status claude-memory-worker
```

You should see: **Active: active (running)**

### Step 6: Test server
```bash
curl http://localhost:37777/api/health
```

Should return: `{"status":"ok","uptime":X,"timestamp":"..."}`

✅ **Server is ready!**

---

## 💻 Client Setup (5 minutes)

### Step 1: Configure client
```bash
# On your local machine, in your project directory
cd /path/to/template-ai-team

bash deployment/client/configure-remote.sh http://your-server.company.com:37777 your-api-key-here
```

### Step 2: Test connection
```bash
bash deployment/client/test-connection.sh
```

Should show: ✅ All tests passed!

### Step 3: Restart Claude Code
```bash
exit  # Exit current session
claude code  # Start new session
```

✅ **Client is configured!**

---

## 🧪 Verify It Works

### Test 1: Check worker status
```bash
node scripts/worker-service.js status
```

Should show: **Status: Running**

### Test 2: Try memory search
```bash
/memory-search "test"
```

Should execute without errors (may return no results if fresh install)

### Test 3: Create some content
Ask Claude to read a file or run a command. The activity will be captured automatically.

### Test 4: Start new session
Exit and restart Claude Code. Context from previous session should be automatically injected.

✅ **Everything works!**

---

## 🔧 Quick Configuration Reference

### Server Files
```
/opt/claude-memory/
├── server/          # Application code
├── data/            # Database (memory.db)
├── logs/            # Log files
└── backups/         # Database backups
```

### Important Commands

**Server:**
```bash
# Service management
sudo systemctl start claude-memory-worker
sudo systemctl stop claude-memory-worker
sudo systemctl restart claude-memory-worker
sudo systemctl status claude-memory-worker

# View logs
sudo journalctl -u claude-memory-worker -f

# Health check
curl http://localhost:37777/api/health

# Backup database
sudo bash /opt/claude-memory/scripts/backup.sh
```

**Client:**
```bash
# Test connection
bash deployment/client/test-connection.sh

# Switch to remote
bash deployment/client/configure-remote.sh http://server:37777 api-key

# Switch to local
bash deployment/client/configure-local.sh

# Check status
node scripts/worker-service.js status
```

---

## 🔒 Security Quick Wins

**1. Setup firewall:**
```bash
sudo bash /tmp/deployment/configs/firewall-rules.sh
```

**2. Setup HTTPS (optional but recommended):**
```bash
sudo apt install nginx certbot python3-certbot-nginx
sudo cp /tmp/deployment/configs/nginx.conf /etc/nginx/sites-available/claude-memory
sudo ln -s /etc/nginx/sites-available/claude-memory /etc/nginx/sites-enabled/
sudo nano /etc/nginx/sites-available/claude-memory  # Update server_name
sudo nginx -t
sudo systemctl reload nginx
sudo certbot --nginx -d memory.company.com
```

**3. Regular backups:**
```bash
# Add to crontab
sudo crontab -e
# Add line: 0 2 * * * /opt/claude-memory/scripts/backup.sh
```

---

## ❓ Troubleshooting

**Service won't start:**
```bash
sudo journalctl -u claude-memory-worker -n 50
# Check for error messages
```

**Client can't connect:**
```bash
# Test from server
curl http://localhost:37777/api/health

# Check firewall
sudo ufw status
sudo ufw allow from <client-ip> to any port 37777
```

**Database errors:**
```bash
# Restart service
sudo systemctl restart claude-memory-worker

# Check permissions
sudo chown -R claudemem:claudemem /opt/claude-memory
```

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for detailed solutions.

---

## 📞 Next Steps

1. **Roll out to team**: Share API key and server URL with team members
2. **Setup monitoring**: Configure health checks and alerts
3. **Schedule backups**: Automate daily database backups
4. **Review security**: Follow [SECURITY.md](SECURITY.md) checklist
5. **Document**: Add company-specific notes and procedures

---

## ✨ Success!

Your remote memory server is now running! Team members can:
- ✅ Share context across sessions
- ✅ Search past work with `/memory-search`
- ✅ Never lose context again
- ✅ Work from any machine with same memory

**Enjoy your persistent memory system!** 🎉

---

**Need help?** See [README.md](README.md) for full documentation or [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues.
