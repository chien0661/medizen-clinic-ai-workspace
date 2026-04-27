# Docker Quick Start - 3 Minutes!

**Get Claude Memory Worker running in Docker in 3 minutes**

---

## Step 1: Prepare Environment (30 seconds)

```bash
# Navigate to docker deployment folder
cd deployment/docker

# Copy environment template
cp .env.example .env

# Generate API key
openssl rand -hex 32
# Copy the output - you'll need it!
```

## Step 2: Configure (1 minute)

Edit `.env` file:

```bash
# On Windows
notepad .env

# On Linux/Mac
nano .env
```

**Set these TWO values:**
```bash
ANTHROPIC_API_KEY=sk-ant-your-key-from-console-anthropic-com
API_KEY=paste-the-key-you-just-generated
```

Save and close.

## Step 3: Deploy (1 minute)

```bash
# Build and start
docker compose up -d

# Wait 10 seconds, then check
docker compose ps
```

Should show: **STATUS: Up X seconds**

## Step 4: Test (30 seconds)

```bash
# Test server
curl http://localhost:37777/api/health

# Should return: {"status":"ok",...}
```

✅ **Server is running!**

---

## Configure Client

**On your local machine:**

```bash
# Navigate to project
cd D:\01. PROJECTS\05.Internal\template-ai-team

# Configure (replace YOUR-API-KEY with the key you generated)
bash deployment/client/configure-remote.sh http://localhost:37777 YOUR-API-KEY

# Test
bash deployment/client/test-connection.sh
```

**Expected:** ✅ All tests passed!

---

## Verify It Works

```bash
# Restart Claude Code
exit
claude code

# Try memory search
/memory-search "test"
```

Should work without errors!

---

## Useful Commands

```bash
# View logs
docker compose logs -f

# Stop
docker compose down

# Restart
docker compose restart

# Status
docker compose ps

# Health check
curl http://localhost:37777/api/health
```

---

## Troubleshooting

**Container won't start:**
```bash
docker compose logs
# Check for errors (usually missing API key)
```

**Port already in use:**
```bash
# Edit docker-compose.yml, change port:
ports:
  - "38888:37777"  # Use different port
```

**Need to reset:**
```bash
docker compose down -v
docker compose up -d
```

---

## Next Steps

1. Test from client
2. Share API key with team
3. Setup backups (see DOCKER-DEPLOYMENT.md)
4. Configure firewall if needed

---

**That's it! You're done!** 🎉

For advanced configuration, see [DOCKER-DEPLOYMENT.md](DOCKER-DEPLOYMENT.md)
