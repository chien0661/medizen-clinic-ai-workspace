# Multi-Team, Multi-Project Deployment Guide

**Managing persistent memory for multiple teams and projects on a single remote server**

---

## Overview

When deploying a remote memory server for multiple teams and projects, you need to consider:

1. **Data isolation** - Teams should only see their project's data
2. **API key management** - Separate keys per team
3. **Cost allocation** - Track usage per team
4. **Scalability** - Support growth without performance degradation

This guide covers three deployment strategies for multi-team environments.

---

## Current Architecture: Automatic Project Isolation

### How Data is Structured

**Database Schema:**
```sql
CREATE TABLE observations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_name TEXT NOT NULL,          -- Auto-detected from directory name
    session_id TEXT NOT NULL,
    tool_name TEXT,
    tool_input TEXT,
    tool_response TEXT,
    compressed_observation TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT,                        -- JSON: user, host, etc.
    UNIQUE(session_id, tool_name, timestamp)
);

CREATE INDEX idx_observations_project ON observations(project_name);
CREATE INDEX idx_observations_timestamp ON observations(timestamp);
CREATE INDEX idx_observations_session ON observations(session_id);
```

**Automatic Project Detection:**
```javascript
// Project name from directory
const projectName = path.basename(process.cwd());
// Example: /home/alice/backend-api → project_name = "backend-api"

// All queries automatically filter by project
const observations = db.searchObservations(query, projectName);
```

**Data Example:**
```
Database: /opt/claude-memory/data/memory.db

observations table:
┌────┬──────────────────┬────────────┬───────────┬──────────────┬─────────────┐
│ id │ project_name     │ session_id │ tool_name │ timestamp    │ user_info   │
├────┼──────────────────┼────────────┼───────────┼──────────────┼─────────────┤
│ 1  │ backend-api      │ sess-001   │ Read      │ 2026-02-01   │ team-a      │
│ 2  │ backend-api      │ sess-001   │ Write     │ 2026-02-01   │ team-a      │
│ 3  │ frontend-app     │ sess-002   │ Read      │ 2026-02-01   │ team-a      │
│ 4  │ mobile-app       │ sess-003   │ Bash      │ 2026-02-02   │ team-b      │
│ 5  │ analytics        │ sess-004   │ Read      │ 2026-02-02   │ team-c      │
└────┴──────────────────┴────────────┴───────────┴──────────────┴─────────────┘
```

**Isolation Behavior:**
```bash
# Team A working in /projects/backend-api
cd /projects/backend-api
claude code
/memory-search "authentication"
# Returns: observations 1, 2 only (project_name = "backend-api")

# Team A working in /projects/frontend-app
cd /projects/frontend-app
claude code
/memory-search "authentication"
# Returns: observation 3 only (project_name = "frontend-app")

# Team B working in /projects/mobile-app
cd /projects/mobile-app
claude code
/memory-search "authentication"
# Returns: observation 4 only (project_name = "mobile-app")
```

### Key Points

✅ **Automatic isolation** - No configuration needed, works by project directory name
✅ **Simple setup** - All teams use same server, different projects auto-separated
✅ **Secure** - Teams can't accidentally access other projects' data
⚠️ **Same project name = shared memory** - If two teams use same directory name, they share memory

---

## Deployment Strategy 1: Single Server, Shared Database

**Recommended for:** Small-medium companies (10-50 developers, 5-20 projects)

### Architecture

```
                    Company Network
┌──────────────────────────────────────────────────────┐
│                                                       │
│              Remote Memory Server                    │
│          http://memory.company.com:37777             │
│                                                       │
│  ┌────────────────────────────────────────────┐    │
│  │  Worker Service (Express API)              │    │
│  │  - Port: 37777                             │    │
│  │  - API Keys: team-a-key, team-b-key, ...   │    │
│  └────────────────────────────────────────────┘    │
│                        │                             │
│  ┌────────────────────▼────────────────────────┐   │
│  │  SQLite Database (memory.db)                │   │
│  │  /opt/claude-memory/data/memory.db          │   │
│  │                                              │   │
│  │  Projects:                                   │   │
│  │  ├── backend-api (Team A)     - 500 obs     │   │
│  │  ├── frontend-app (Team A)    - 300 obs     │   │
│  │  ├── mobile-app (Team B)      - 400 obs     │   │
│  │  ├── analytics (Team C)       - 350 obs     │   │
│  │  └── data-pipeline (Team C)   - 250 obs     │   │
│  └──────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────┘
          │                  │                  │
          │                  │                  │
    ┌─────▼────┐       ┌─────▼────┐      ┌────▼─────┐
    │ Team A   │       │ Team B   │      │ Team C   │
    │ (10 devs)│       │ (5 devs) │      │ (8 devs) │
    │ 2 projects│      │ 1 project│      │ 2 projects│
    └──────────┘       └──────────┘      └──────────┘
```

### Server Setup

**1. Deploy single server:**
```bash
# Follow standard deployment
bash deployment/server/install.sh
```

**2. Generate API keys for each team:**
```bash
# Generate separate keys
TEAM_A_KEY=$(openssl rand -hex 32)
TEAM_B_KEY=$(openssl rand -hex 32)
TEAM_C_KEY=$(openssl rand -hex 32)

echo "Team A: $TEAM_A_KEY"
echo "Team B: $TEAM_B_KEY"
echo "Team C: $TEAM_C_KEY"
```

**3. Configure server with multiple keys:**
```bash
# /opt/claude-memory/server/.env
ANTHROPIC_API_KEY=sk-ant-company-shared-key

# Comma-separated API keys (one per team)
API_KEY=team-a-32-char-key,team-b-32-char-key,team-c-32-char-key

WORKER_PORT=37777
LOG_LEVEL=info
```

**4. Restart service:**
```bash
sudo systemctl restart claude-memory-worker
```

### Client Configuration (Per Team)

**Team A:**
```bash
# .env
WORKER_URL=http://memory.company.com:37777
MEMORY_API_KEY=team-a-32-char-key
```

**Team B:**
```bash
# .env
WORKER_URL=http://memory.company.com:37777
MEMORY_API_KEY=team-b-32-char-key
```

**Team C:**
```bash
# .env
WORKER_URL=http://memory.company.com:37777
MEMORY_API_KEY=team-c-32-char-key
```

### Pros & Cons

**Pros:**
- ✅ Single server to maintain (lower cost)
- ✅ Shared infrastructure and Anthropic API key
- ✅ Simple backup (one database)
- ✅ Easy monitoring (one service)
- ✅ Automatic project isolation

**Cons:**
- ⚠️ All teams on same infrastructure
- ⚠️ Single point of failure
- ⚠️ No hard team-level isolation
- ⚠️ Potential performance impact if one team has huge data

**Cost:**
- Server: $20-50/month (VPS) or $0 (on-premise)
- Anthropic API: $300-600/month (shared across all teams)
- Total: **~$320-650/month for entire company**

---

## Deployment Strategy 2: Multiple Servers (One per Team)

**Recommended for:** Large enterprises (50+ developers), strict compliance, separate budgets per team

### Architecture

```
Company Network
┌─────────────────────────────────────────────────────────┐
│                                                          │
│  Team A Server                                          │
│  http://memory-team-a.company.com:37777                │
│  ├── backend-api (Team A)                              │
│  └── frontend-app (Team A)                             │
│                                                          │
│  Team B Server                                          │
│  http://memory-team-b.company.com:37777                │
│  └── mobile-app (Team B)                               │
│                                                          │
│  Team C Server                                          │
│  http://memory-team-c.company.com:37777                │
│  ├── analytics (Team C)                                │
│  └── data-pipeline (Team C)                            │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Server Setup (Per Team)

**Deploy separate server for each team:**

```bash
# Team A
ssh team-a-server
bash deployment/server/install.sh

# Team B
ssh team-b-server
bash deployment/server/install.sh

# Team C
ssh team-c-server
bash deployment/server/install.sh
```

**Configure each server:**
```bash
# Team A server: /opt/claude-memory/server/.env
ANTHROPIC_API_KEY=sk-ant-team-a-key
API_KEY=team-a-internal-key
WORKER_PORT=37777

# Team B server: /opt/claude-memory/server/.env
ANTHROPIC_API_KEY=sk-ant-team-b-key
API_KEY=team-b-internal-key
WORKER_PORT=37777

# Team C server: /opt/claude-memory/server/.env
ANTHROPIC_API_KEY=sk-ant-team-c-key
API_KEY=team-c-internal-key
WORKER_PORT=37777
```

### Client Configuration (Per Team)

**Team A:**
```bash
# .env
WORKER_URL=http://memory-team-a.company.com:37777
MEMORY_API_KEY=team-a-internal-key
```

**Team B:**
```bash
# .env
WORKER_URL=http://memory-team-b.company.com:37777
MEMORY_API_KEY=team-b-internal-key
```

**Team C:**
```bash
# .env
WORKER_URL=http://memory-team-c.company.com:37777
MEMORY_API_KEY=team-c-internal-key
```

### Pros & Cons

**Pros:**
- ✅ Complete team isolation (data, infrastructure, costs)
- ✅ Independent scaling per team
- ✅ Team-specific configuration and policies
- ✅ No cross-team performance impact
- ✅ Separate cost tracking per team

**Cons:**
- ❌ Higher infrastructure cost (3× servers)
- ❌ More maintenance overhead
- ❌ Separate backups for each server
- ❌ Duplicate monitoring setup

**Cost:**
- Server: $20-50/month × 3 teams = $60-150/month
- Anthropic API: $150-300/month × 3 teams = $450-900/month
- Total: **~$510-1050/month** (vs $320-650 for single server)

**Cost Savings vs Local:**
- Local mode: $15-30/month × 23 developers = $345-690/month
- Multiple servers: $510-1050/month
- **Breakeven: ~20-30 developers**

---

## Deployment Strategy 3: Enhanced Schema with Team Tracking

**Recommended for:** Companies wanting team-level analytics while sharing infrastructure

### Enhanced Database Schema

Add explicit team tracking to existing schema:

```sql
-- Add team_id column to observations
ALTER TABLE observations ADD COLUMN team_id TEXT;

-- Create team_projects mapping
CREATE TABLE team_projects (
    team_id TEXT NOT NULL,
    project_name TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (team_id, project_name)
);

-- Add indexes
CREATE INDEX idx_observations_team ON observations(team_id);
CREATE INDEX idx_team_projects ON team_projects(team_id);

-- Example data
INSERT INTO team_projects VALUES
    ('team-a', 'backend-api', '2026-02-01'),
    ('team-a', 'frontend-app', '2026-02-01'),
    ('team-b', 'mobile-app', '2026-02-01'),
    ('team-c', 'analytics', '2026-02-01'),
    ('team-c', 'data-pipeline', '2026-02-01');
```

### Server Implementation

**Add team detection to worker service:**

```javascript
// mcp-servers/claude-mem-server/src/services/worker.ts

// Detect team from API key
const API_KEY_TEAM_MAP = {
  'team-a-32-char-key': 'team-a',
  'team-b-32-char-key': 'team-b',
  'team-c-32-char-key': 'team-c',
};

// Middleware to add team_id to observations
app.use((req, res, next) => {
  const apiKey = req.headers['x-api-key'];
  req.teamId = API_KEY_TEAM_MAP[apiKey];
  next();
});

// Add team_id when saving observations
app.post('/api/observations', (req, res) => {
  const observation = {
    ...req.body,
    team_id: req.teamId,  // Add team tracking
  };
  db.saveObservation(observation);
});
```

### Analytics Queries

**Team-level usage analytics:**

```sql
-- Total observations per team
SELECT team_id, COUNT(*) as total_observations
FROM observations
GROUP BY team_id;

-- Team storage usage
SELECT team_id,
       COUNT(*) as observations,
       SUM(LENGTH(compressed_observation)) as total_bytes
FROM observations
GROUP BY team_id;

-- Team API usage (for cost allocation)
SELECT team_id,
       COUNT(DISTINCT session_id) as sessions,
       COUNT(*) as observations,
       COUNT(*) * 0.01 as estimated_cost_usd
FROM observations
WHERE timestamp >= date('now', '-30 days')
GROUP BY team_id;
```

**Results:**
```
┌──────────┬──────────────┬─────────────┬────────────────────┐
│ team_id  │ observations │ total_bytes │ estimated_cost_usd │
├──────────┼──────────────┼─────────────┼────────────────────┤
│ team-a   │ 800          │ 1,234,567   │ 8.00               │
│ team-b   │ 400          │ 567,890     │ 4.00               │
│ team-c   │ 600          │ 890,123     │ 6.00               │
└──────────┴──────────────┴─────────────┴────────────────────┘

Total: $18/month shared Anthropic API cost allocation
```

### Pros & Cons

**Pros:**
- ✅ Team-level analytics and cost tracking
- ✅ Single infrastructure (lower cost)
- ✅ Fair cost allocation across teams
- ✅ Project isolation still automatic

**Cons:**
- ⚠️ Requires schema migration
- ⚠️ More complex setup
- ⚠️ Still shared infrastructure

---

## Comparison Matrix

| Feature | Single Server | Multiple Servers | Enhanced Schema |
|---------|--------------|------------------|-----------------|
| **Setup Complexity** | ⭐ Simple | ⭐⭐⭐ Complex | ⭐⭐ Moderate |
| **Infrastructure Cost** | 💰 Low ($20-50/mo) | 💰💰💰 High ($60-150/mo) | 💰 Low ($20-50/mo) |
| **API Cost** | 💰 Shared ($300-600/mo) | 💰💰💰 Per-team ($450-900/mo) | 💰 Shared ($300-600/mo) |
| **Team Isolation** | ✅ Project-level | ✅✅✅ Complete | ✅✅ Project + Team |
| **Maintenance** | ⭐ Easy | ⭐⭐⭐ High | ⭐⭐ Moderate |
| **Scalability** | ⭐⭐ Good (100+ devs) | ⭐⭐⭐ Excellent | ⭐⭐ Good (100+ devs) |
| **Cost Tracking** | ❌ Manual | ✅ Automatic | ✅✅ Automatic + Analytics |
| **Single Point of Failure** | ⚠️ Yes | ✅ No | ⚠️ Yes |
| **Backup Complexity** | ⭐ Simple (1 DB) | ⭐⭐⭐ Complex (N DBs) | ⭐ Simple (1 DB) |

---

## Best Practices

### For All Strategies

**1. Use consistent project naming:**
```bash
# Good: Clear, unique project names
backend-api
frontend-app
mobile-ios
mobile-android
analytics-service

# Bad: Generic names (causes collisions)
api
app
service
project
```

**2. Document team-to-project mapping:**
```markdown
# Team Project Mapping

## Team A (Backend)
- backend-api
- frontend-app

## Team B (Mobile)
- mobile-ios
- mobile-android

## Team C (Data)
- analytics-service
- data-pipeline
- ml-models
```

**3. Implement API key rotation:**
```bash
# Rotate keys quarterly
openssl rand -hex 32  # Generate new key
# Update server .env
# Distribute to team
# Update all client .env files
# Remove old key after grace period
```

**4. Monitor database growth:**
```sql
-- Check database size per project
SELECT
    project_name,
    COUNT(*) as observations,
    SUM(LENGTH(compressed_observation)) as size_bytes,
    ROUND(SUM(LENGTH(compressed_observation)) / 1024.0 / 1024.0, 2) as size_mb
FROM observations
GROUP BY project_name
ORDER BY size_bytes DESC;
```

**5. Set up automated backups:**
```bash
# Daily backup per project (if needed)
sqlite3 /opt/claude-memory/data/memory.db \
  "SELECT * FROM observations WHERE project_name='backend-api'" \
  > /backups/backend-api-$(date +%Y%m%d).sql
```

### For Single Server Strategy

**1. Set clear API key policies:**
- One key per team (not per developer)
- Document key ownership
- Rotate quarterly
- Store in password manager

**2. Monitor resource usage:**
```bash
# Check memory usage
du -h /opt/claude-memory/data/memory.db

# Check API request rate
sudo journalctl -u claude-memory-worker --since "1 hour ago" | grep "POST /api" | wc -l
```

**3. Set up firewall rules per team:**
```bash
# Allow Team A network
sudo ufw allow from 192.168.1.0/24 to any port 37777

# Allow Team B network
sudo ufw allow from 192.168.2.0/24 to any port 37777

# Allow Team C network
sudo ufw allow from 192.168.3.0/24 to any port 37777
```

### For Multiple Servers Strategy

**1. Use consistent naming:**
```
memory-team-a.company.com
memory-team-b.company.com
memory-team-c.company.com
```

**2. Centralize monitoring:**
```bash
# Use centralized logging (ELK Stack, Splunk)
# All servers send logs to central location
# Setup alerts for all servers
```

**3. Automate deployments:**
```bash
# Ansible playbook for all servers
ansible-playbook -i hosts.ini deploy-memory-server.yml
```

---

## Migration Paths

### From Local to Single Server

**For each team:**
```bash
# 1. Backup all local databases
for dir in /home/*/projects/*; do
  if [ -f "$dir/.claude-mem/memory.db" ]; then
    cp "$dir/.claude-mem/memory.db" "/backups/$(basename $dir)-memory.db"
  fi
done

# 2. Merge into remote server
scp /backups/*-memory.db server:/tmp/
ssh server "sudo bash /opt/claude-memory/scripts/merge-databases.sh /tmp/*.db"

# 3. Configure all clients for remote
bash deployment/client/configure-remote.sh http://memory.company.com:37777 team-key
```

### From Single Server to Multiple Servers

**Split by team:**
```bash
# 1. Backup current database
sudo cp /opt/claude-memory/data/memory.db /backups/full-backup.db

# 2. Extract team-specific data
sqlite3 /backups/full-backup.db <<EOF
.output /backups/team-a-data.sql
SELECT * FROM observations WHERE project_name IN ('backend-api', 'frontend-app');
.output /backups/team-b-data.sql
SELECT * FROM observations WHERE project_name IN ('mobile-app');
.output /backups/team-c-data.sql
SELECT * FROM observations WHERE project_name IN ('analytics', 'data-pipeline');
EOF

# 3. Deploy new servers and import data
# (Follow Multiple Servers setup above)
```

---

## FAQ

**Q: Can two teams accidentally access each other's data?**
A: No. Project name isolation is automatic. Even with shared API key, searches filter by project directory name.

**Q: What if two teams use the same project name?**
A: They will share memory! Use unique, descriptive project names. Example: `team-a-backend` instead of just `backend`.

**Q: How much does it cost for 50 developers, 10 projects?**
A: Single server: ~$320-650/month total. Multiple servers (5 teams): ~$800-1200/month. Local mode: ~$750-1500/month.

**Q: Can I migrate from single server to multiple servers later?**
A: Yes! Export project-specific data and import to new servers. See "Migration Paths" section.

**Q: How do I track costs per team on single server?**
A: Use Enhanced Schema strategy (Option 3) to add team_id tracking and generate usage reports.

**Q: What's the maximum database size?**
A: SQLite supports up to 281 TB. Practical limit: ~10 GB before performance degrades. Use archiving for old data.

**Q: Can I use different Anthropic API keys per team on single server?**
A: No, server uses one key. For separate keys, use Multiple Servers strategy.

**Q: How do I archive old project data?**
A: Export to separate database:
```bash
sqlite3 memory.db "SELECT * FROM observations WHERE project_name='old-project' AND timestamp < date('now', '-1 year')" > archive.sql
sqlite3 memory.db "DELETE FROM observations WHERE project_name='old-project' AND timestamp < date('now', '-1 year')"
```

---

## Recommended Setup by Company Size

**Small (10-20 developers, 3-5 projects):**
- **Strategy:** Single Server, Shared Database
- **Cost:** ~$320-450/month
- **Setup time:** 30 minutes

**Medium (20-50 developers, 5-15 projects):**
- **Strategy:** Single Server with Enhanced Schema
- **Cost:** ~$450-650/month
- **Setup time:** 1-2 hours

**Large (50-100 developers, 15-30 projects):**
- **Strategy:** Multiple Servers (3-5 servers)
- **Cost:** ~$800-1200/month
- **Setup time:** 3-4 hours

**Enterprise (100+ developers, 30+ projects):**
- **Strategy:** Multiple Servers + Load Balancer
- **Cost:** ~$1200-2000/month
- **Setup time:** 1-2 days

---

## Next Steps

1. **Assess your requirements:**
   - How many teams?
   - How many projects per team?
   - Budget constraints?
   - Compliance requirements?

2. **Choose deployment strategy** (see comparison matrix above)

3. **Follow deployment guide:**
   - [Remote Deployment Guide](remote-memory-deployment.md)
   - [Quick Start Guide](../../deployment/QUICK-START.md)

4. **Configure teams and projects**

5. **Monitor and optimize**

---

**Last Updated:** 2026-02-03
**Related Docs:**
- [Remote Memory Deployment](remote-memory-deployment.md)
- [Deployment Tomorrow Guide](../../deployment/DEPLOYMENT-TOMORROW.md)
- [Security Guide](../../deployment/SECURITY.md)
