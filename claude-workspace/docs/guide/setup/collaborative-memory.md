# Collaborative Memory Guide

**How multiple team members share context on the same project**

---

## Overview

When multiple developers work on the same project, the persistent memory system **automatically merges their contexts**. This enables powerful team collaboration features:

✅ **Automatic context sharing** - See teammates' work without manual sync
✅ **Cross-developer learning** - Learn from others' solutions and decisions
✅ **Institutional memory** - Team knowledge persists beyond individual sessions
✅ **Fast onboarding** - New members get full project history instantly
✅ **Avoid duplicate work** - Search finds existing solutions

---

## How Collaborative Memory Works

### Automatic Context Merging

**No configuration needed!** When team members work in projects with the same name, their observations automatically merge.

**Example:**

```
Remote Server Database
└── Project: "backend-api"
    ├── Alice: 500 observations (JWT auth, login, API)
    ├── Bob: 300 observations (refresh tokens, docs)
    ├── Carol: 200 observations (tests, debugging)
    └── David: 150 observations (deployment, monitoring)
```

**When any team member searches:**
```bash
cd /path/to/backend-api
/memory-search "authentication"

# Results include observations from ALL team members:
# - Alice: Implemented JWT authentication
# - Bob: Added refresh token rotation
# - Carol: Wrote integration tests
# - David: Deployed to production
```

### Data Flow

```
┌─────────────────────────────────────────────────────┐
│                  Remote Server                       │
│                                                       │
│  ┌────────────────────────────────────────────┐    │
│  │  Database: memory.db                        │    │
│  │                                              │    │
│  │  observations table:                         │    │
│  │  ┌─────────────────────────────────────┐   │    │
│  │  │ project_name: "backend-api"          │   │    │
│  │  │ ├── session: alice-001 (500 obs)     │   │    │
│  │  │ ├── session: bob-002 (300 obs)       │   │    │
│  │  │ ├── session: carol-003 (200 obs)     │   │    │
│  │  │ └── session: david-004 (150 obs)     │   │    │
│  │  └─────────────────────────────────────┘   │    │
│  └────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────┘
         ▲              ▲              ▲
         │              │              │
    ┌────┴───┐     ┌────┴───┐     ┌───┴────┐
    │ Alice  │     │  Bob   │     │ Carol  │
    │ Saves  │     │ Saves  │     │ Saves  │
    │ & Reads│     │ & Reads│     │ & Reads│
    └────────┘     └────────┘     └────────┘

    All team members read/write same project context!
```

### Query Behavior

**Search query:**
```sql
-- When Alice searches "authentication" in "backend-api"
SELECT * FROM observations
WHERE project_name = 'backend-api'
  AND (compressed_observation LIKE '%authentication%'
       OR tool_input LIKE '%authentication%'
       OR tool_response LIKE '%authentication%')
ORDER BY relevance DESC, timestamp DESC
LIMIT 20;
```

**Result:** Returns observations from **all sessions**, regardless of who created them.

---

## Benefits of Collaborative Memory

### 1. Team Knowledge Sharing

**Scenario:** Alice implements feature, Bob extends it later

```
Monday (Alice):
- Implements JWT authentication
- Saves observations:
  * "Used jsonwebtoken library for token generation"
  * "Stored tokens in Redis with 1-hour expiration"
  * "Added middleware in src/middleware/auth.js"

Wednesday (Bob):
- Needs to add refresh token support
- Searches: /memory-search "authentication JWT"
- Finds Alice's implementation details
- Extends existing pattern consistently
- Result: No need to ask Alice, maintains consistency
```

### 2. Avoid Duplicate Work

**Scenario:** Carol encounters bug Alice already fixed

```
Carol debugging login issue:
/memory-search "login session timeout"

Finds:
- Alice: "Fixed session timeout bug in AuthService.ts:45"
- Alice: "Issue was Redis TTL not matching JWT expiration"
- Alice: "Solution: Synchronized TTL values in config"

Result: Carol uses Alice's solution, saves 2 hours debugging
```

### 3. Fast Onboarding

**Scenario:** David joins team, first day

```
David (new developer):
/memory-search "API structure"

Finds:
- Alice: "API routes in src/routes/ following REST conventions"
- Bob: "Authentication required for all /api/v1/* endpoints"
- Carol: "Test examples in tests/integration/api/"
- Complete project context instantly!

Result: David productive on day 1, no onboarding meeting needed
```

### 4. Institutional Memory

**Scenario:** Team discusses "Why did we choose JWT over sessions?"

```
Anyone on team:
/memory-search "authentication decision"

Finds:
- Alice (6 months ago): "Chose JWT over sessions for stateless API"
- Alice: "Consideration: Microservices can verify tokens independently"
- Alice: "Tradeoff: Can't revoke tokens, added short expiration"

Result: Team understands historical context and reasoning
```

### 5. Cross-Session Learning

**Scenario:** Alice away, Bob needs to deploy her feature

```
Bob:
/memory-search "deployment backend API"

Finds:
- Alice: "Deploy with: npm run build && pm2 restart api"
- Carol: "Remember to run migrations: npm run migrate:prod"
- David: "Check health endpoint after deploy: /api/health"

Result: Bob deploys successfully without asking team
```

---

## Real-World Example

**Team: 4 developers working on "backend-api"**

### Week 1: Alice's Work

```bash
# Alice implements authentication
cd /projects/backend-api
claude code

# Session activities (auto-captured):
- Read: src/controllers/AuthController.ts
- Write: src/middleware/jwt.ts (implements JWT verification)
- Bash: npm test -- auth.test.ts (tests passing)
- Write: docs/api/authentication.md (documents endpoints)

# Observations saved with:
# - project_name: "backend-api"
# - session_id: "alice-2026-02-01-001"
# - compressed_observation: "Implemented JWT middleware..."
```

### Week 2: Bob's Work

```bash
# Bob starts new session (new feature)
cd /projects/backend-api
claude code

# Session start: Context automatically injected
# Bob sees summary:
# "Recent work: Alice implemented JWT authentication,
#  added middleware in src/middleware/jwt.ts,
#  all tests passing"

# Bob searches for related work:
/memory-search "authentication"

# Results show Alice's work:
# 1. Implemented JWT verification middleware
# 2. Added token validation in src/middleware/jwt.ts
# 3. Tests in tests/unit/jwt.test.ts
# 4. API docs in docs/api/authentication.md

# Bob builds on Alice's work:
# - Extends jwt.ts with refresh token logic
# - Adds refresh endpoint to AuthController
# - Updates Alice's tests with refresh token cases
# Result: Consistent with Alice's implementation
```

### Week 3: Carol's Work

```bash
# Carol writes integration tests
cd /projects/backend-api
claude code

# Carol searches for test patterns:
/memory-search "test API endpoints"

# Finds:
# - Alice: "Unit tests use Jest in tests/unit/"
# - Bob: "Mock JWT tokens with jwt.sign() in tests"
# - Bob: "Test refresh endpoint with supertest"

# Carol follows team's testing patterns
# Result: Consistent test structure across codebase
```

### Week 4: David Joins Team

```bash
# David's first day
cd /projects/backend-api
claude code

# Session start: Gets full project history
# David explores codebase:
/memory-search "authentication"
/memory-search "API structure"
/memory-search "deployment"
/memory-search "testing"

# Finds:
# - Alice's auth implementation
# - Bob's refresh token feature
# - Carol's test patterns
# - Complete project knowledge

# David productive immediately:
# - Understands architecture
# - Knows where to find things
# - Follows team patterns
# Result: No onboarding meeting needed!
```

---

## Managing Collaborative Memory

### Best Practices

**1. Use descriptive project names:**
```bash
# ✅ Good: Clear, unique names
backend-api
frontend-web-app
mobile-ios-app
data-pipeline-etl

# ❌ Bad: Generic names (causes unwanted sharing)
api
app
project
test
```

**2. Use privacy tags for sensitive data:**
```javascript
// Before committing/sharing
const apiKey = "<private>sk-ant-1234567890abcdef</private>";
const password = "<private>SuperSecret123!</private>";

// Saved to database as:
const apiKey = "[REDACTED]";
const password = "[REDACTED]";

// All team members see [REDACTED], not actual secrets
```

**3. Separate personal experiments:**
```bash
# Team shared work
cd /projects/backend-api
# project_name = "backend-api" (shared with team)

# Personal experiments/prototypes
cd /projects/alice-experiments
# project_name = "alice-experiments" (private to Alice)
```

**4. Use clear commit messages:**
```bash
# Good: Context helps team understand changes
"Implemented JWT authentication with 1-hour expiration"
"Fixed Redis connection timeout in AuthService"
"Added integration tests for refresh token flow"

# Bad: Vague messages don't help team
"Fix bug"
"Update auth"
"Changes"
```

**5. Search before implementing:**
```bash
# Before starting work, search for related context
/memory-search "feature name"
/memory-search "similar problem"
/memory-search "technology choice"

# Avoid reinventing the wheel
# Learn from team's past decisions
```

### Handling Noise

**Problem:** Too many observations from teammates?

**Solution 1: Use targeted searches**
```bash
# ✅ Specific query
/memory-search "JWT authentication middleware"
# Returns: Most relevant results only

# ❌ Broad query
/memory-search "auth"
# Returns: Too many results
```

**Solution 2: Filter by tool type**
```bash
# Only file changes
/memory-search "authentication" --type Write

# Only commands
/memory-search "deployment" --type Bash

# Only searches
/memory-search "API" --type Grep
```

**Solution 3: Limit results**
```bash
# Top 5 most relevant
/memory-search "authentication" --limit 5

# Recent work only (via compressed observations)
# System automatically prioritizes recent work
```

**Solution 4: Use private project for experiments**
```bash
# Shared team project (production code)
cd /projects/backend-api

# Your personal experiments (not shared)
cd /projects/alice-prototypes
```

### User Tracking (Optional Enhancement)

**Want to know WHO did what?**

**Current:** System tracks session_id, can add user info to metadata

**Enhancement:** Add username to observations

**Server implementation:**
```javascript
// worker.ts - Add username tracking
const observation = {
  ...req.body,
  user_info: {
    username: req.headers['x-user-name'] || 'unknown',
    hostname: req.headers['x-host-name'] || 'unknown',
    timestamp: new Date().toISOString(),
  }
};
```

**Client configuration:**
```bash
# .env
MEMORY_USER_NAME=alice
MEMORY_HOST_NAME=alice-laptop

# Or auto-detect
MEMORY_USER_NAME=$(whoami)
MEMORY_HOST_NAME=$(hostname)
```

**Search with user filter:**
```bash
# Find Alice's work
/memory-search "authentication" --user alice

# Find Bob's deployments
/memory-search "deploy" --user bob

# Find work from specific machine
/memory-search "test" --host dev-server-01
```

---

## Privacy and Security

### Privacy Levels

**1. Project-level isolation (default):**
```
backend-api project:
├── Alice: sees team's work
├── Bob: sees team's work
└── Carol: sees team's work

frontend-app project:
├── David: sees only frontend work
└── Eve: sees only frontend work

No cross-project visibility!
```

**2. Tag-level privacy:**
```javascript
// Redacted for all team members
const secret = "<private>my-secret</private>";
// Stored as: const secret = "[REDACTED]";
```

**3. Project-level privacy:**
```bash
# Create private project
cd /projects/alice-personal
# Only Alice's machine has this directory
# Only Alice sees this project's memory
```

### Security Considerations

**1. API Key per team:**
```bash
# Team A key
MEMORY_API_KEY=team-a-key-32-chars

# Team B key
MEMORY_API_KEY=team-b-key-32-chars

# Each team uses different key
# Server logs which key accessed what
```

**2. Network isolation:**
```bash
# Firewall: Only company network
sudo ufw allow from 192.168.0.0/16 to any port 37777

# VPN required for remote access
# No public internet exposure
```

**3. Database encryption:**
```bash
# Encrypt database at rest (optional)
# Use encrypted filesystem
# Regular backups to secure location
```

---

## FAQ

**Q: Can I see observations from teammates on different projects?**
A: No. Observations are isolated by project_name. Only teammates working on the same project share context.

**Q: What if two people have directories with same name?**
A: They share context! Example: `/home/alice/backend-api` and `/home/bob/backend-api` both share memory for "backend-api" project.

**Q: Can I hide my work from teammates?**
A: Use a different project name. Example: `alice-experiments` instead of `backend-api`.

**Q: What if someone commits secrets accidentally?**
A: Use `<private>` tags before capture. Already-captured secrets require database cleanup or `/memory-clear`.

**Q: How do I know whose observation is whose?**
A: Check session_id or implement user tracking enhancement (see "User Tracking" section above).

**Q: Can I delete a teammate's observation?**
A: Yes, with database access: `sqlite3 memory.db "DELETE FROM observations WHERE id=123"`. But requires server access.

**Q: What if observation count grows too large?**
A: Archive old observations:
```bash
# On server
sqlite3 memory.db "DELETE FROM observations WHERE timestamp < date('now', '-6 months')"
```

**Q: Can I merge observations from two projects?**
A: Yes, rename project:
```bash
# On server
sqlite3 memory.db "UPDATE observations SET project_name='new-name' WHERE project_name='old-name'"
```

---

## Comparison: Collaborative vs Individual Memory

| Feature | Individual (Local) | Collaborative (Remote) |
|---------|-------------------|------------------------|
| **Setup** | Zero config | One-time server setup |
| **Memory** | Private to you | Shared with team |
| **Context** | Your work only | Team's work |
| **Onboarding** | No help for new members | Instant project history |
| **Knowledge** | Lost when you leave | Persists with team |
| **Cost** | $15-30/mo per person | $300-600/mo for team |
| **Learning** | Learn from your past | Learn from team's past |
| **Consistency** | Individual patterns | Team patterns |

---

## Next Steps

**Start using collaborative memory:**

1. **Deploy remote server** (if not done)
   - Follow [Remote Deployment Guide](remote-memory-deployment.md)

2. **Configure all team members**
   ```bash
   bash deployment/client/configure-remote.sh http://server:37777 team-api-key
   ```

3. **Establish team conventions**
   - Project naming standards
   - Privacy tag usage
   - Search before implementing

4. **Monitor and optimize**
   - Review shared context regularly
   - Archive old observations
   - Adjust search strategies

---

## Related Documentation

- [Remote Memory Deployment](remote-memory-deployment.md)
- [Multi-Team Deployment](multi-team-deployment.md)
- [Using Persistent Memory](using-persistent-memory.md)
- [Persistent Memory Architecture](../PERSISTENT_MEMORY_ARCHITECTURE.md)

---

**Last Updated:** 2026-02-03
**Feature Status:** ✅ Built-in, works automatically
**Configuration Required:** None (automatic context merging)
