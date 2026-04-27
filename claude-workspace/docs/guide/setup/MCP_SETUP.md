# MCP (Model Context Protocol) Setup Guide

This guide explains how to configure MCP servers for reading tasks and requirements from external systems (Jira, Confluence, Figma).

---

## Overview

**Hybrid Approach**:
- **INPUT (Read)**: Use MCP to read from Jira, Confluence, Figma
- **OUTPUT (Write)**: Always write to markdown files in `docs/` folder

**Why?**
- Flexible input from multiple sources
- Self-contained project state (all in git)
- No dependency on external systems for history

---

## Available MCP Servers

### 1. Jira MCP ⭐ **RECOMMENDED**
**Purpose**: Read issues, epics, stories, bugs
**Use Case**: Pull task details from Jira, then track in `docs/tasks/dashboard.md`
**Tech Stack**: Spring Boot + React

### 2. Confluence MCP ⭐ **RECOMMENDED**
**Purpose**: Read technical specifications, architecture docs
**Use Case**: Pull SRS/Detail Design from Confluence, save to `docs/templates/specs/`
**Tech Stack**: Spring Boot + React

### 3. MariaDB MCP ⭐ **RECOMMENDED for Spring Boot**
**Purpose**: Query database for validation, check data integrity, verify test data
**Use Case**:
- Test Agent: Validate database state after tests
- Code Implementation: Check existing schema before migrations
- Code Review: Verify data integrity
**Tech Stack**: Spring Boot backend (perfect for your stack!)

### 4. Figma MCP
**Purpose**: Read design specifications, UI requirements
**Use Case**: Extract design requirements, document in `docs/templates/specs/`
**Tech Stack**: React frontend
**Note**: Disabled by default (enable if using Figma)

---

## Setup Instructions

### Prerequisites

1. **Node.js** installed (v18 or later)
   ```bash
   node --version
   # Should be v18.0.0 or higher
   ```

2. **Access tokens** for each service:
   - Jira API Token
   - Confluence API Token
   - Figma Access Token

---

## Step 1: Get API Tokens

### Jira API Token

1. Go to: https://id.atlassian.com/manage-profile/security/api-tokens
2. Click "Create API token"
3. Name it: "Claude Code MCP"
4. Copy the token (save securely - shown only once)

### Confluence API Token

1. Same as Jira (Atlassian account)
2. Go to: https://id.atlassian.com/manage-profile/security/api-tokens
3. Create token named "Claude Code MCP - Confluence"
4. Copy the token

### Figma Access Token

1. Go to: https://www.figma.com/developers/api#access-tokens
2. Settings → Account → Personal Access Tokens
3. Create new token named "Claude Code MCP"
4. Copy the token

### MariaDB Database Credentials

**IMPORTANT: Use a READ-ONLY user for security!**

1. Connect to your MariaDB server:
   ```bash
   mysql -u root -p
   ```

2. Create a READ-ONLY user for Claude Code:
   ```sql
   -- Create read-only user
   CREATE USER 'claude_readonly'@'localhost' IDENTIFIED BY 'secure_password_here';

   -- Grant SELECT only (read-only)
   GRANT SELECT ON your_database.* TO 'claude_readonly'@'localhost';

   -- If connecting remotely, also grant for remote host
   CREATE USER 'claude_readonly'@'%' IDENTIFIED BY 'secure_password_here';
   GRANT SELECT ON your_database.* TO 'claude_readonly'@'%';

   FLUSH PRIVILEGES;
   ```

3. Test the connection:
   ```bash
   mysql -u claude_readonly -p your_database
   # Should be able to SELECT but not INSERT/UPDATE/DELETE
   ```

**Security Best Practices:**
- ✅ Use READ-ONLY user (SELECT permission only)
- ✅ Use strong password
- ✅ Limit to specific database (not all databases)
- ✅ Use localhost connection if Claude Code is on same server
- ❌ Never use root user
- ❌ Never grant INSERT/UPDATE/DELETE permissions

---

## Step 2: Set Environment Variables

**CRITICAL**: Store tokens in environment variables, NOT in files!

### Windows (PowerShell)

```powershell
# Set user environment variables (persistent)

# Jira MCP
[System.Environment]::SetEnvironmentVariable('JIRA_URL', 'https://your-company.atlassian.net', 'User')
[System.Environment]::SetEnvironmentVariable('JIRA_EMAIL', 'your.email@company.com', 'User')
[System.Environment]::SetEnvironmentVariable('JIRA_API_TOKEN', 'your-jira-token-here', 'User')

# Confluence MCP
[System.Environment]::SetEnvironmentVariable('CONFLUENCE_URL', 'https://your-company.atlassian.net/wiki', 'User')
[System.Environment]::SetEnvironmentVariable('CONFLUENCE_EMAIL', 'your.email@company.com', 'User')
[System.Environment]::SetEnvironmentVariable('CONFLUENCE_API_TOKEN', 'your-confluence-token-here', 'User')

# MariaDB MCP (READ-ONLY user recommended)
[System.Environment]::SetEnvironmentVariable('MARIADB_HOST', 'localhost', 'User')
[System.Environment]::SetEnvironmentVariable('MARIADB_PORT', '3306', 'User')
[System.Environment]::SetEnvironmentVariable('MARIADB_USER', 'claude_readonly', 'User')
[System.Environment]::SetEnvironmentVariable('MARIADB_PASSWORD', 'your-readonly-password-here', 'User')
[System.Environment]::SetEnvironmentVariable('MARIADB_DATABASE', 'your_database_name', 'User')

# Figma MCP (optional - disable by default)
[System.Environment]::SetEnvironmentVariable('FIGMA_ACCESS_TOKEN', 'your-figma-token-here', 'User')

# Restart PowerShell to load new environment variables
```

### Linux / macOS (Bash)

```bash
# Add to ~/.bashrc or ~/.zshrc for persistence

# Jira MCP
export JIRA_URL="https://your-company.atlassian.net"
export JIRA_EMAIL="your.email@company.com"
export JIRA_API_TOKEN="your-jira-token-here"

# Confluence MCP
export CONFLUENCE_URL="https://your-company.atlassian.net/wiki"
export CONFLUENCE_EMAIL="your.email@company.com"
export CONFLUENCE_API_TOKEN="your-confluence-token-here"

# MariaDB MCP (READ-ONLY user recommended)
export MARIADB_HOST="localhost"
export MARIADB_PORT="3306"
export MARIADB_USER="claude_readonly"
export MARIADB_PASSWORD="your-readonly-password-here"
export MARIADB_DATABASE="your_database_name"

# Figma MCP (optional - disable by default)
export FIGMA_ACCESS_TOKEN="your-figma-token-here"

# Reload shell configuration
source ~/.bashrc  # or source ~/.zshrc
```

---

## Step 3: Configure MCP Servers

### Option A: Project-Level Configuration (Recommended)

**For this project only:**

1. Copy the example configuration:
   ```bash
   cp .mcp.json.example .mcp.json
   ```

2. The file is already configured with environment variables:
   ```json
   {
     "mcpServers": {
       "jira": {
         "command": "npx",
         "args": ["-y", "@modelcontextprotocol/server-jira"],
         "env": {
           "JIRA_URL": "${JIRA_URL}",
           "JIRA_EMAIL": "${JIRA_EMAIL}",
           "JIRA_API_TOKEN": "${JIRA_API_TOKEN}"
         }
       },
       ...
     }
   }
   ```

3. **Important**: `.mcp.json` is in `.gitignore` - never commit it!

### Option B: User-Level Configuration

**For all Claude Code projects:**

Configure in Claude Code global settings (usually prompts you on first use).

---

## Step 4: Enable MCP Servers in Claude Code

1. Start Claude Code in your project:
   ```bash
   cd D:\01. PROJECTS\DEMO MULTIPLE AGENTS\template-ai-team
   claude
   ```

2. Claude Code will detect `.mcp.json` and ask to enable servers

3. Approve each server:
   - ✅ Jira MCP
   - ✅ Confluence MCP
   - ✅ Figma MCP

4. Verify servers are running:
   ```
   # In Claude Code, servers will show as available tools
   ```

---

## Step 5: Test MCP Servers

### Test Jira MCP

```bash
# In Claude Code chat
"Use Jira MCP to list issues in project PROJ"
```

Expected response:
```
Found 15 issues in PROJ:
- PROJ-456: Implement user profile API
- PROJ-457: Fix login bug
...
```

### Test Confluence MCP

```bash
# In Claude Code chat
"Use Confluence MCP to read page 'User Profile SRS'"
```

Expected response:
```
Retrieved Confluence page: User Profile SRS
Content:
1. Overview
2. Requirements
...
```

### Test Figma MCP

```bash
# In Claude Code chat
"Use Figma MCP to get file 'User Profile Design'"
```

Expected response:
```
Retrieved Figma file: User Profile Design
Components: Header, Profile Form, Avatar Upload
...
```

---

## Usage Examples

### Example 1: Import Task from Jira

```markdown
User: "Use Jira MCP to read issue PROJ-456, then create a task entry in docs/tasks/dashboard.md"

Agent:
1. Reads PROJ-456 from Jira via MCP
2. Extracts: Title, Description, Acceptance Criteria
3. Creates entry in docs/tasks/dashboard.md:

## TASK-001: Implement User Profile API (from PROJ-456)
**Status:** TODO
**Jira:** [PROJ-456](https://your-company.atlassian.net/browse/PROJ-456)
**Description:** [from Jira description]
**Acceptance Criteria:**
- [from Jira AC]

**Progress tracking:** docs/tasks/dashboard.md (NOT Jira)
```

**Key Point**: Jira is INPUT only - all tracking in `docs/tasks/dashboard.md`

### Example 2: Import Specs from Confluence

```markdown
User: "Use Confluence MCP to read 'User Profile SRS' page, extract business rules, and save to docs/templates/specs/user-profile-srs.md"

Agent:
1. Reads Confluence page via MCP
2. Extracts business rules section
3. Creates docs/templates/specs/user-profile-srs.md:

# User Profile SRS

**Source:** [Confluence](https://your-company.atlassian.net/wiki/spaces/PROJ/pages/123456)
**Last Updated:** 2026-01-20

## Business Rules

### BR-001: Audit Trail
All profile updates must be logged...

### BR-002: Rate Limiting
Free users: 5 updates/day...

[Rest of extracted content]

**Note**: This is a snapshot from Confluence. See link above for latest version.
```

**Key Point**: Confluence is INPUT - we save snapshot to `docs/templates/specs/`

### Example 3: Extract Design from Figma

```markdown
User: "Use Figma MCP to read 'User Profile UI' design, extract component specs, and document in docs/templates/specs/user-profile-design.md"

Agent:
1. Reads Figma file via MCP
2. Extracts components, styles, interactions
3. Creates docs/templates/specs/user-profile-design.md:

# User Profile UI Design

**Source:** [Figma](https://figma.com/file/abc123)
**Last Updated:** 2026-01-22

## Components

### Profile Form
- Fields: Bio (textarea, max 500 chars), Location (input, max 100 chars)
- Button: "Update Profile" (primary action)
- Validation: Real-time character count

### Avatar Upload
- Size: 200x200px circular
- Formats: JPG, PNG, GIF (max 2MB)
- Upload behavior: Click to upload, drag-and-drop supported

[Rest of extracted design specs]
```

**Key Point**: Figma is INPUT - we document design in `docs/templates/specs/`

### Example 4: Validate Database Schema (MariaDB MCP) ⭐ **SPRING BOOT**

```markdown
User (Code Implementation Agent): "Use MariaDB MCP to check existing database schema before creating migration"

Agent:
1. Connects to MariaDB via MCP (read-only)
2. Queries schema information:

SHOW TABLES;
-- Returns: users, user_profiles, audit_log, profile_update_log

DESCRIBE user_profiles;
-- Returns:
-- | Field       | Type         | Null | Key | Default | Extra          |
-- |-------------|--------------|------|-----|---------|----------------|
-- | id          | bigint(20)   | NO   | PRI | NULL    | auto_increment |
-- | user_id     | bigint(20)   | NO   | UNI | NULL    |                |
-- | bio         | varchar(500) | YES  |     | NULL    |                |
-- | location    | varchar(100) | YES  |     | NULL    |                |
-- | avatar_url  | varchar(255) | YES  |     | NULL    |                |
-- | created_at  | timestamp    | NO   |     | CURRENT_TIMESTAMP |    |
-- | updated_at  | timestamp    | NO   |     | CURRENT_TIMESTAMP |    |

3. Creates migration script based on existing schema:
   - Knows user_id column already exists
   - Can safely add new columns without conflicts
   - Avoids duplicate table/column errors
```

**Key Point**: Check schema BEFORE creating migrations - prevents SQL errors!

### Example 5: Verify Data Integrity (Test Agent with MariaDB MCP) ⭐ **TESTING**

```markdown
User (Test Agent): "Use MariaDB MCP to verify audit log entry was created after profile update"

Test Scenario (Karate):
@business @srs-validation @BR-001 @database
Scenario: BR-001 - All profile updates must be audited
  # SRS Section 3.1.1: Audit Trail Requirement

  * def userId = 123

  # Update profile via API
  Given path 'users', userId, 'profile'
  And request { bio: 'New bio', location: 'Hanoi' }
  When method PUT
  Then status 200

  # Verify in database using MariaDB MCP
  * def mariaDbQuery =
    """
    SELECT * FROM audit_log
    WHERE user_id = 123
    AND action = 'PROFILE_UPDATE'
    ORDER BY created_at DESC
    LIMIT 1
    """

  # Execute query via MariaDB MCP
  # Returns:
  # | id | user_id | action         | old_value | new_value                    | created_at          |
  # |----|---------|----------------|-----------|------------------------------|---------------------|
  # | 45 | 123     | PROFILE_UPDATE | {...}     | {"bio":"New bio","loc":"HN"} | 2026-01-23 10:30:00 |

  * match auditLog.action == 'PROFILE_UPDATE'
  * match auditLog.new_value contains 'New bio'
  * match auditLog.new_value contains 'Hanoi'
```

**Key Point**: Validate database state directly - ensures data integrity beyond API responses!

### Example 6: Check Test Data (Code Implementation Agent) ⭐ **SETUP**

```markdown
User (Code Implementation Agent): "Use MariaDB MCP to check if test users exist before running tests"

Agent:
1. Queries database for test data:

SELECT email, subscription_type
FROM users
WHERE email IN ('free@example.com', 'premium@example.com');

-- Returns:
-- | email                | subscription_type |
-- |----------------------|-------------------|
-- | free@example.com     | FREE              |
-- | premium@example.com  | PREMIUM           |

2. If test users don't exist, creates SQL insert script:

INSERT INTO users (email, password_hash, subscription_type) VALUES
('free@example.com', '$2a$10$...', 'FREE'),
('premium@example.com', '$2a$10$...', 'PREMIUM');

3. Documents in test data setup script
```

**Key Point**: Verify test data exists - prevents flaky tests!

### Example 7: Analyze Database Performance (Code Review Agent) ⭐ **OPTIMIZATION**

```markdown
User (Code Review Agent): "Use MariaDB MCP to check if indexes exist for frequently queried columns"

Agent:
1. Checks indexes on user_profiles table:

SHOW INDEX FROM user_profiles;

-- Returns:
-- | Table         | Key_name | Column_name | Index_type |
-- |---------------|----------|-------------|------------|
-- | user_profiles | PRIMARY  | id          | BTREE      |
-- | user_profiles | user_id  | user_id     | BTREE      |

2. Reviews code to find queries:
   - SELECT * FROM user_profiles WHERE user_id = ?  ✅ (indexed)
   - SELECT * FROM user_profiles WHERE location = ?  ❌ (not indexed!)

3. Creates code review comment:
   "⚠️ Performance Issue: Query by 'location' column has no index.
   Consider adding: CREATE INDEX idx_location ON user_profiles(location);
   Expected impact: 10x faster queries for location search"
```

**Key Point**: MariaDB MCP helps identify performance issues before they hit production!

---

## Workflow Integration

### Code Implementation Agent

```markdown
1. (Optional) Use Jira MCP to read task details
2. SAVE to docs/tasks/dashboard.md (mandatory)
3. (Optional) Use Confluence MCP to read specifications
4. SAVE to docs/templates/specs/ (mandatory)
5. (Optional) Use Figma MCP to read design
6. SAVE to docs/templates/specs/ (mandatory)
7. ⭐ (Optional) Use MariaDB MCP to check existing schema before migrations
8. ⭐ (Optional) Use MariaDB MCP to verify test data exists
9. Track ALL progress in docs/tasks/dashboard.md (NOT external systems)
```

**Pattern**: READ from external → SAVE to markdown → TRACK in markdown

**MariaDB Usage for Code Implementation Agent**:
```sql
-- Check existing schema before creating migration
SHOW TABLES;
DESCRIBE user_profiles;

-- Verify test users exist
SELECT email, subscription_type FROM users
WHERE email IN ('test-free@example.com', 'test-premium@example.com');

-- Check foreign key constraints
SELECT CONSTRAINT_NAME, TABLE_NAME, REFERENCED_TABLE_NAME
FROM information_schema.KEY_COLUMN_USAGE
WHERE TABLE_SCHEMA = 'your_database_name'
AND REFERENCED_TABLE_NAME IS NOT NULL;
```

### Code Review Agent

```markdown
1. Review code changes
2. ⭐ Use MariaDB MCP to check for performance issues (missing indexes)
3. ⭐ Use MariaDB MCP to verify data integrity constraints
4. Create review report in docs/reviews/
5. Update docs/tasks/dashboard.md with review decision
```

**MariaDB Usage for Code Review Agent**:
```sql
-- Check if queries have appropriate indexes
SHOW INDEX FROM user_profiles;
SHOW INDEX FROM audit_log;

-- Analyze table structure for N+1 query issues
SELECT TABLE_NAME, COLUMN_NAME, REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME
FROM information_schema.KEY_COLUMN_USAGE
WHERE TABLE_SCHEMA = 'your_database_name'
AND REFERENCED_TABLE_NAME IS NOT NULL;

-- Check for missing indexes on foreign keys
SELECT c.TABLE_NAME, c.COLUMN_NAME
FROM information_schema.COLUMNS c
LEFT JOIN information_schema.STATISTICS s
  ON c.TABLE_SCHEMA = s.TABLE_SCHEMA
  AND c.TABLE_NAME = s.TABLE_NAME
  AND c.COLUMN_NAME = s.COLUMN_NAME
WHERE c.TABLE_SCHEMA = 'your_database_name'
  AND c.COLUMN_NAME LIKE '%_id'
  AND s.INDEX_NAME IS NULL;
```

### Test Agent

```markdown
1. Create test scenarios (API, Integration, Business Rules, E2E)
2. ⭐ Use MariaDB MCP to verify database state after API calls
3. ⭐ Use MariaDB MCP to validate business rules (audit logs, constraints)
4. Execute all tests
5. Create test report in docs/test-reports/
6. Update docs/tasks/dashboard.md with test results
```

**MariaDB Usage for Test Agent** (Karate Integration):
```gherkin
Feature: User Profile Business Rules (BR-001 to BR-005)

Background:
  * url baseUrl
  * def testUserId = 999

@business @BR-001 @database
Scenario: BR-001 - All profile updates must be audited
  # Update profile via API
  Given path 'users', testUserId, 'profile'
  And request { bio: 'Test bio', location: 'Hanoi' }
  When method PUT
  Then status 200

  # Verify in database using MariaDB MCP
  # Query: SELECT * FROM audit_log WHERE user_id = 999 AND action = 'PROFILE_UPDATE' ORDER BY created_at DESC LIMIT 1
  # Expected: One audit log entry with new values
  * def auditLogExists = true  # Result from MariaDB MCP query
  * assert auditLogExists == true

@business @BR-002 @rate-limiting @database
Scenario: BR-002 - Rate limiting for free users (5 updates/day)
  # Query current update count using MariaDB MCP
  # Query: SELECT COUNT(*) as update_count FROM profile_update_log WHERE user_id = 999 AND DATE(created_at) = CURDATE()
  # Expected: < 5 for free users
  * def updateCount = 3  # Result from MariaDB MCP query
  * assert updateCount < 5

  # Attempt update
  Given path 'users', testUserId, 'profile'
  And request { bio: 'Updated bio' }
  When method PUT
  Then status 200

  # Verify rate limit log updated in database
  # Query: SELECT COUNT(*) FROM profile_update_log WHERE user_id = 999 AND DATE(created_at) = CURDATE()
  # Expected: 4 (previous 3 + this 1)
```

### Documentation Agent

```markdown
1. Review all changes (code, tests, database migrations)
2. Update API documentation (docs/api/)
3. Update feature documentation (docs/features/)
4. ⭐ (Optional) Use MariaDB MCP to document schema changes
5. Update README if needed
6. Finalize task in docs/tasks/dashboard.md
```

**MariaDB Usage for Documentation Agent**:
```sql
-- Document schema changes in migration
SHOW CREATE TABLE user_profiles;

-- List all columns for API documentation
SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_KEY, COLUMN_DEFAULT, EXTRA
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = 'your_database_name'
AND TABLE_NAME = 'user_profiles'
ORDER BY ORDINAL_POSITION;

-- Document indexes for performance documentation
SHOW INDEX FROM user_profiles;
```

---

## Troubleshooting

### MCP Server Not Starting

**Error**: `Failed to start MCP server: jira`

**Solutions**:
1. Check environment variables are set:
   ```bash
   # Windows PowerShell
   echo $env:JIRA_API_TOKEN

   # Linux/macOS
   echo $JIRA_API_TOKEN
   ```

2. Check Node.js is installed:
   ```bash
   node --version
   npx --version
   ```

3. Test MCP package manually:
   ```bash
   npx -y @modelcontextprotocol/server-jira
   # Should start without errors
   ```

### Authentication Errors

**Error**: `401 Unauthorized`

**Solutions**:
1. Verify API token is correct (regenerate if needed)
2. Verify email matches Atlassian/Figma account
3. Check URL is correct:
   - Jira: `https://your-company.atlassian.net`
   - Confluence: `https://your-company.atlassian.net/wiki`

### MCP Tools Not Appearing

**Error**: MCP tools not showing in Claude Code

**Solutions**:
1. Restart Claude Code session
2. Check `.mcp.json` is in project root
3. Verify servers are not marked `"disabled": true`
4. Check Claude Code approved the servers (may need manual approval)

### Network Issues (On-Prem)

**Error**: Connection timeout to Jira/Confluence

**Solutions**:
1. Check firewall allows outbound HTTPS to Atlassian
2. Check proxy settings (if behind corporate proxy):
   ```bash
   # Set proxy environment variables
   export HTTP_PROXY="http://proxy.company.com:8080"
   export HTTPS_PROXY="http://proxy.company.com:8080"
   ```
3. Test connectivity:
   ```bash
   curl -I https://your-company.atlassian.net
   ```

### MariaDB MCP Connection Issues ⭐ **SPRING BOOT**

**Error**: `Failed to connect to MariaDB` or `ER_ACCESS_DENIED_ERROR`

**Solutions**:

1. **Verify environment variables are set correctly**:
   ```bash
   # Windows PowerShell
   echo $env:MARIADB_HOST
   echo $env:MARIADB_PORT
   echo $env:MARIADB_USER
   echo $env:MARIADB_DATABASE

   # Linux/macOS
   echo $MARIADB_HOST
   echo $MARIADB_PORT
   echo $MARIADB_USER
   echo $MARIADB_DATABASE
   ```

2. **Test database connection manually**:
   ```bash
   # Test connection from command line
   mysql -h localhost -P 3306 -u claude_readonly -p your_database_name

   # If successful, try a simple query
   SELECT 1;
   ```

3. **Verify READ-ONLY user permissions**:
   ```sql
   -- Connect as root
   mysql -u root -p

   -- Check user exists
   SELECT User, Host FROM mysql.user WHERE User = 'claude_readonly';

   -- Check grants
   SHOW GRANTS FOR 'claude_readonly'@'localhost';

   -- Should show: GRANT SELECT ON your_database.* TO 'claude_readonly'@'localhost'
   ```

4. **Common permission errors**:
   ```sql
   -- Error: Access denied
   -- Solution: Grant SELECT permission
   GRANT SELECT ON your_database.* TO 'claude_readonly'@'localhost';
   FLUSH PRIVILEGES;

   -- Error: User cannot connect from host
   -- Solution: Check host in GRANT statement matches connection host
   -- If connecting from remote machine, use:
   GRANT SELECT ON your_database.* TO 'claude_readonly'@'%';
   FLUSH PRIVILEGES;
   ```

5. **Check MariaDB server is running**:
   ```bash
   # Windows
   sc query mariadb
   # Or
   Get-Service mariadb

   # Linux
   sudo systemctl status mariadb
   # Or
   sudo service mariadb status

   # Check if port 3306 is listening
   netstat -an | grep 3306
   # Or (Windows PowerShell)
   Get-NetTCPConnection -LocalPort 3306
   ```

6. **Firewall issues (on-prem deployment)**:
   ```bash
   # Allow MariaDB port 3306 on Windows Firewall
   netsh advfirewall firewall add rule name="MariaDB" dir=in action=allow protocol=TCP localport=3306

   # Linux (iptables)
   sudo iptables -A INPUT -p tcp --dport 3306 -j ACCEPT
   # Or (firewalld)
   sudo firewall-cmd --permanent --add-port=3306/tcp
   sudo firewall-cmd --reload
   ```

**Error**: `ER_BAD_DB_ERROR: Unknown database`

**Solutions**:
1. Verify database name in environment variable:
   ```bash
   echo $env:MARIADB_DATABASE  # Windows
   echo $MARIADB_DATABASE      # Linux/macOS
   ```

2. List all databases:
   ```sql
   mysql -u root -p
   SHOW DATABASES;
   ```

3. Create database if it doesn't exist:
   ```sql
   CREATE DATABASE your_database_name;
   GRANT SELECT ON your_database_name.* TO 'claude_readonly'@'localhost';
   FLUSH PRIVILEGES;
   ```

**Error**: `ER_NO_SUCH_TABLE` when querying

**Solutions**:
1. Verify table exists:
   ```sql
   SHOW TABLES;
   ```

2. Check spelling (table names are case-sensitive on Linux):
   ```sql
   -- Case-sensitive on Linux/Unix, case-insensitive on Windows
   SELECT * FROM user_profiles;  -- May differ from User_Profiles
   ```

3. Check which database is selected:
   ```sql
   SELECT DATABASE();
   ```

---

## Security Best Practices

### ✅ DO:
- Store tokens in environment variables
- Use separate tokens for different purposes (Jira, Confluence, Figma)
- **⭐ Use READ-ONLY database user for MariaDB MCP (SELECT permission only)**
- Rotate tokens periodically (every 90 days)
- Revoke tokens when no longer needed
- Use least-privilege access (read-only if possible)
- **⭐ Use strong passwords for MariaDB users (min 16 characters)**
- **⭐ Limit MariaDB user to specific database (not all databases)**
- **⭐ Use localhost connection if Claude Code is on same server as MariaDB**

### ❌ DON'T:
- Commit `.mcp.json` with tokens (it's in `.gitignore`)
- Share tokens in chat/email
- Use personal tokens for team projects (use service accounts)
- Store tokens in code or configuration files
- Use production API tokens for development
- **⭐ Never use root user for MariaDB MCP**
- **⭐ Never grant INSERT/UPDATE/DELETE permissions to MCP user**
- **⭐ Never store database passwords in code or config files**
- **⭐ Never use production database for testing MCP (use dev/test database)**

### Token Rotation

**Schedule**: Every 90 days

**Process**:
1. Generate new token in Jira/Confluence/Figma
2. Update environment variable
3. Restart Claude Code
4. Test MCP server
5. Revoke old token

---

## Advanced Configuration

### Read-Only Mode (Recommended)

Configure MCP servers with read-only permissions:

1. In Jira: Create API token with "Browse Projects" permission only
2. In Confluence: Create API token with "Read" permission only
3. In Figma: Use "File" scope, not "Full access"

**Why**: Prevents accidental writes to external systems

### Custom MCP Servers

You can add custom MCP servers for:
- Internal APIs
- Custom documentation systems
- Proprietary tools

See: https://github.com/modelcontextprotocol/specification

---

## FAQ

### Q: Do I need all MCP servers?
**A**: No. Enable only what you use:
- **Jira MCP**: If tasks come from Jira
- **Confluence MCP**: If specs are in Confluence
- **MariaDB MCP**: ⭐ **RECOMMENDED for Spring Boot** - validates database state, checks schema, verifies test data
- **Figma MCP**: If designs are in Figma

Disable unused servers in `.mcp.json`: `"disabled": true`

### Q: Can MCP write back to Jira/Confluence?
**A**: Yes, but **DON'T**. This template uses hybrid approach:
- READ from external systems (Jira/Confluence/Figma)
- WRITE to markdown (`docs/` folder)

This keeps project self-contained.

### Q: What if Jira/Confluence is down?
**A**: Fallback to `docs/` folder:
- Tasks: Read from `docs/tasks/dashboard.md` (should have all info)
- Specs: Read from `docs/templates/specs/` (snapshots from Confluence)
- Designs: Read from `docs/templates/specs/` (extracted from Figma)

This is why we save everything to markdown.

### Q: How do I update tasks in Jira?
**A**: Manual sync (recommended):
1. Complete task in template (tracked in `docs/tasks/dashboard.md`)
2. Manually update Jira ticket status (Done, In Progress, etc.)
3. Add link to git commit in Jira comment

**Why manual?** Keeps template simple and avoids sync conflicts.

### Q: Can MariaDB MCP write to the database? ⭐ **SPRING BOOT**
**A**: **NO** - and it's by design for security!

The template configures MariaDB MCP with a **READ-ONLY user** that has:
- ✅ SELECT permission only
- ❌ NO INSERT/UPDATE/DELETE permissions

**Why read-only?**
- Prevents accidental data corruption
- Agents can validate state but not change it
- All data changes go through your Spring Boot application layer
- Follows principle of least privilege

**Use MariaDB MCP for:**
- ✅ Validating database schema before migrations
- ✅ Checking test data exists
- ✅ Verifying audit logs after API calls
- ✅ Analyzing performance (indexes, query plans)
- ❌ NOT for inserting/updating/deleting data

### Q: Should I use production or development database for MariaDB MCP?
**A**: **ALWAYS use development/test database**, never production!

**Setup**:
```sql
-- Create separate database for development
CREATE DATABASE myapp_dev;
CREATE USER 'claude_readonly'@'localhost' IDENTIFIED BY 'strong_password';
GRANT SELECT ON myapp_dev.* TO 'claude_readonly'@'localhost';
```

**Environment variables**:
```bash
# Point to DEV database
MARIADB_DATABASE=myapp_dev  # NOT myapp_prod
```

**Why?**
- Protects production data from accidental exposure
- Development database can have test data
- Faster queries (smaller dataset)
- Safe to experiment

### Q: How does MariaDB MCP integrate with Karate tests?
**A**: MariaDB MCP validates database state that Karate API tests trigger.

**Example workflow**:
1. **Karate test** makes API call: `PUT /users/123/profile`
2. **Spring Boot** processes request, updates database
3. **MariaDB MCP** validates: Check if audit_log entry was created
4. **Test passes** if database state is correct

**Benefits**:
- Validates end-to-end behavior (API → Service → Database)
- Catches business rule violations (missing audit logs, constraint violations)
- Verifies data integrity beyond API response

**See Example 5 in Usage Examples** for full Karate + MariaDB MCP integration.

---

## Next Steps

### For Spring Boot + React + MariaDB Stack

1. ✅ **Set environment variables**:
   - Jira: `JIRA_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN`
   - Confluence: `CONFLUENCE_URL`, `CONFLUENCE_EMAIL`, `CONFLUENCE_API_TOKEN`
   - ⭐ **MariaDB**: `MARIADB_HOST`, `MARIADB_PORT`, `MARIADB_USER`, `MARIADB_PASSWORD`, `MARIADB_DATABASE`
   - Figma: `FIGMA_ACCESS_TOKEN` (optional)

2. ✅ **Create READ-ONLY MariaDB user**:
   ```sql
   CREATE USER 'claude_readonly'@'localhost' IDENTIFIED BY 'strong_password';
   GRANT SELECT ON myapp_dev.* TO 'claude_readonly'@'localhost';
   FLUSH PRIVILEGES;
   ```

3. ✅ **Copy MCP configuration**:
   ```bash
   cp .mcp.json.example .mcp.json
   ```

4. ✅ **Start Claude Code and approve MCP servers**:
   ```bash
   cd D:\01. PROJECTS\DEMO MULTIPLE AGENTS\template-ai-team
   claude
   ```

5. ✅ **Test each MCP server**:
   - Test Jira: `"Use Jira MCP to list issues in project PROJ"`
   - Test Confluence: `"Use Confluence MCP to read page 'User Profile SRS'"`
   - ⭐ **Test MariaDB**: `"Use MariaDB MCP to show all tables in the database"`
   - Test Figma (optional): `"Use Figma MCP to get file 'User Profile Design'"`

6. ✅ **Try practical examples**:
   - **Example 1**: Import task from Jira to `docs/tasks/dashboard.md`
   - **Example 2**: Import specs from Confluence to `docs/templates/specs/`
   - ⭐ **Example 4**: Use MariaDB MCP to validate database schema before migration
   - ⭐ **Example 5**: Use MariaDB MCP to verify audit log in Karate test

**You're ready to use the hybrid MCP approach with Spring Boot + MariaDB!** 🎉

---

**Last Updated**: 2026-01-23
**MCP Servers Configured**: Jira, Confluence, ⭐ **MariaDB (Spring Boot)**, Figma
**Approach**: Hybrid (Read from external, Write to markdown)
**Tech Stack**: Java Spring Boot + ReactJS + MariaDB + Docker
