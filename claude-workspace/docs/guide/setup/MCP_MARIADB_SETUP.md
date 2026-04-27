# MariaDB/MySQL MCP Server Setup Guide

**For**: VISSOFT Organization Multi-Agent Development
**Last Updated**: 2026-01-23

---

## Overview

The MariaDB MCP (Model Context Protocol) server allows AI agents to query your database for validation, testing, and code review purposes.

**✅ CRITICAL: This template uses READ-ONLY database access for security**

---

## Why Use MariaDB MCP?

### For Test Agent:
- ✅ **Verify test data** exists before running tests
- ✅ **Check audit logs** to validate business rules
- ✅ **Validate data integrity** after integration tests
- ✅ **Query test results** stored in database

### For Code Review Agent:
- ✅ **Detect missing indexes** on large tables
- ✅ **Verify foreign key constraints** are properly defined
- ✅ **Identify N+1 query patterns** using EXPLAIN
- ✅ **Check table schema** matches code expectations

### For Code Implementation Agent:
- ✅ **Check schema before migrations** to avoid conflicts
- ✅ **Verify column types** match entity definitions
- ✅ **Inspect existing constraints** before adding new ones

---

## Quick Setup (4 Steps)

### Step 0: Install Custom MCP Server Dependencies

This template includes a custom MariaDB MCP server that needs dependencies installed:

```bash
# Navigate to the MCP server directory
cd mcp-servers/mariadb-server

# Install dependencies
npm install

# Return to project root
cd ../..
```

**What gets installed:**
- `@modelcontextprotocol/sdk`: MCP protocol implementation
- `mariadb`: MariaDB Node.js connector

**Note**: The `node_modules/` and `.env` in the mcp-servers directory are gitignored for security.

### Step 1: Create READ-ONLY Database User

**⚠️ IMPORTANT**: Never use admin credentials for MCP. Always create a dedicated READ-ONLY user.

```sql
-- Connect to MariaDB as admin
mysql -u root -p

-- Create read-only user
CREATE USER 'readonly_user'@'localhost' IDENTIFIED BY 'secure_password_here';

-- Grant SELECT permission ONLY
GRANT SELECT ON your_database.* TO 'readonly_user'@'localhost';

-- Optional: Grant access to information_schema for schema inspection
GRANT SELECT ON information_schema.* TO 'readonly_user'@'localhost';

-- Apply changes
FLUSH PRIVILEGES;

-- Verify user was created
SELECT User, Host FROM mysql.user WHERE User = 'readonly_user';
```

### Step 2: Test the Connection

```bash
# Test connection
mysql -h localhost -P 3306 -u readonly_user -p your_database

# Try a SELECT query (should work)
SELECT COUNT(*) FROM users;

# Try an INSERT query (should fail - this is good!)
INSERT INTO users (name, email) VALUES ('test', 'test@example.com');
# Error: INSERT command denied - perfect!
```

### Step 3: Configure .env File

Copy `.env.example` to `.env` and fill in your credentials:

```bash
# Copy template
cp .env.example .env

# Edit .env file
# Update these values:
DB_HOST=localhost
DB_PORT=3306
DB_USER=readonly_user
DB_PASSWORD=your-actual-password-here
DB_NAME=your_database_name
```

---

## Configuration Details

### .mcp.json Configuration

The template includes a custom VISSOFT MariaDB MCP server:

```json
{
  "mcpServers": {
    "mariadb": {
      "command": "node",
      "args": ["mcp-servers/mariadb-server/index.js"],
      "env": {
        "DB_HOST": "${DB_HOST}",
        "DB_PORT": "${DB_PORT}",
        "DB_USER": "${DB_USER}",
        "DB_PASSWORD": "${DB_PASSWORD}",
        "DB_NAME": "${DB_NAME}"
      },
      "disabled": false
    }
  }
}
```

**Note**: This template uses a custom MariaDB MCP server located at `mcp-servers/mariadb-server/`. The server provides:
- **query** tool: Execute SELECT, SHOW, DESCRIBE queries (read-only)
- **execute** tool: Execute INSERT, UPDATE, DELETE statements (requires write permissions)
- **schema** tool: Get table schema information

**Security**: The custom server prevents DROP and TRUNCATE operations for safety.

---

## Usage Examples

### Test Agent: Verify Test Data

**Scenario**: Before running integration tests, verify test user exists

```sql
-- Check if test user exists
SELECT * FROM users WHERE email = 'test@example.com';

-- Verify test orders are set up
SELECT COUNT(*) FROM orders WHERE user_id = 123 AND status = 'PENDING';

-- Check audit logs for test actions
SELECT * FROM audit_logs
WHERE user_id = 123
AND action = 'USER_LOGIN'
AND created_at >= DATE_SUB(NOW(), INTERVAL 1 DAY);
```

**Agent Prompt**:
```
Before running integration tests, verify that test user with email 'test@example.com'
exists in the database using MariaDB MCP.
```

### Code Review Agent: Detect Missing Indexes

**Scenario**: Check if frequently queried columns have indexes

```sql
-- Show all indexes on users table
SHOW INDEXES FROM users;

-- Check if email column has index
SELECT
    TABLE_NAME,
    COLUMN_NAME,
    INDEX_NAME
FROM information_schema.STATISTICS
WHERE TABLE_SCHEMA = 'your_database'
  AND TABLE_NAME = 'users'
  AND COLUMN_NAME = 'email';

-- Detect tables with no indexes (performance risk)
SELECT
    t.TABLE_NAME,
    t.TABLE_ROWS
FROM information_schema.TABLES t
LEFT JOIN information_schema.STATISTICS s
    ON t.TABLE_NAME = s.TABLE_NAME
    AND s.INDEX_NAME != 'PRIMARY'
WHERE t.TABLE_SCHEMA = 'your_database'
  AND s.TABLE_NAME IS NULL
  AND t.TABLE_ROWS > 1000;
```

**Agent Prompt**:
```
Review the users table schema and verify that email column has an index
since it's used in WHERE clauses frequently.
```

### Code Review Agent: Identify N+1 Queries

**Scenario**: Analyze query execution plan

```sql
-- Explain query to detect table scans
EXPLAIN SELECT u.*, p.*
FROM users u
LEFT JOIN profiles p ON u.id = p.user_id
WHERE u.status = 'ACTIVE';

-- Check for full table scans (type = ALL is bad)
-- Look for "Using where" without index usage
```

**Agent Prompt**:
```
Use EXPLAIN to analyze the user profile query and identify potential N+1 issues
or missing indexes.
```

### Code Implementation Agent: Check Schema

**Scenario**: Verify table structure before migration

```sql
-- Check if table exists
SELECT TABLE_NAME
FROM information_schema.TABLES
WHERE TABLE_SCHEMA = 'your_database'
  AND TABLE_NAME = 'users';

-- Describe table structure
DESCRIBE users;

-- Check column types
SHOW COLUMNS FROM users;

-- List all foreign keys
SELECT
    CONSTRAINT_NAME,
    TABLE_NAME,
    COLUMN_NAME,
    REFERENCED_TABLE_NAME,
    REFERENCED_COLUMN_NAME
FROM information_schema.KEY_COLUMN_USAGE
WHERE TABLE_SCHEMA = 'your_database'
  AND REFERENCED_TABLE_NAME IS NOT NULL;
```

**Agent Prompt**:
```
Before creating the migration file, check if the users table already exists
and what columns it currently has.
```

---

## Security Best Practices

### ✅ DO:

1. **Use READ-ONLY user** for MCP
   ```sql
   GRANT SELECT ON database.* TO 'readonly_user'@'localhost';
   ```

2. **Limit to specific database**
   ```sql
   -- Good: Specific database
   GRANT SELECT ON my_app_db.* TO 'readonly_user'@'localhost';

   -- Bad: All databases
   GRANT SELECT ON *.* TO 'readonly_user'@'localhost';
   ```

3. **Use strong passwords**
   ```bash
   # Generate strong password
   openssl rand -base64 32
   ```

4. **Rotate credentials regularly**
   - Change password every 90 days
   - Update .env file with new credentials

5. **Use localhost connection** when possible
   ```sql
   CREATE USER 'readonly_user'@'localhost' IDENTIFIED BY 'password';
   -- localhost is more secure than '%' (any host)
   ```

### ❌ DON'T:

1. **Don't grant write permissions**
   ```sql
   -- BAD: Grants INSERT, UPDATE, DELETE
   GRANT ALL PRIVILEGES ON database.* TO 'user'@'localhost';
   ```

2. **Don't use production credentials**
   - Use separate development/test database
   - Never connect MCP to production database

3. **Don't commit .env to Git**
   - .env is in .gitignore (verify this)
   - Use .env.example as template only

4. **Don't share credentials**
   - Each team member should have their own database user
   - Don't share passwords via Slack/email

5. **Don't allow remote access unless needed**
   ```sql
   -- Avoid unless absolutely necessary
   CREATE USER 'user'@'%' IDENTIFIED BY 'password';
   ```

---

## Troubleshooting

### Issue: "Connection refused"

**Symptoms:**
```
Error: connect ECONNREFUSED 127.0.0.1:3306
```

**Solutions:**

1. Check if MariaDB is running
   ```bash
   # Linux/macOS
   sudo systemctl status mariadb
   # or
   sudo service mariadb status

   # Windows
   net start MariaDB
   ```

2. Verify port is correct
   ```sql
   SHOW VARIABLES LIKE 'port';
   ```

3. Check firewall
   ```bash
   # Linux: Allow MariaDB port
   sudo ufw allow 3306/tcp
   ```

### Issue: "Access denied for user"

**Symptoms:**
```
Error: ER_ACCESS_DENIED_ERROR: Access denied for user 'readonly_user'@'localhost'
```

**Solutions:**

1. Verify credentials
   ```bash
   mysql -h localhost -u readonly_user -p
   # Enter password and see if you can connect
   ```

2. Check user exists
   ```sql
   SELECT User, Host FROM mysql.user WHERE User = 'readonly_user';
   ```

3. Verify permissions
   ```sql
   SHOW GRANTS FOR 'readonly_user'@'localhost';
   ```

4. Recreate user if needed
   ```sql
   DROP USER 'readonly_user'@'localhost';
   CREATE USER 'readonly_user'@'localhost' IDENTIFIED BY 'new_password';
   GRANT SELECT ON your_database.* TO 'readonly_user'@'localhost';
   FLUSH PRIVILEGES;
   ```

### Issue: "Unknown database"

**Symptoms:**
```
Error: ER_BAD_DB_ERROR: Unknown database 'your_database'
```

**Solutions:**

1. List available databases
   ```sql
   SHOW DATABASES;
   ```

2. Update DB_NAME in .env with correct database name

3. Create database if needed
   ```sql
   CREATE DATABASE your_database CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```

### Issue: "MCP server not found"

**Symptoms:**
```
Error: MCP server 'mariadb' not found
```

**Solutions:**

1. Verify .mcp.json exists
   ```bash
   ls -la .mcp.json
   ```

2. Check MariaDB section in .mcp.json
   ```bash
   cat .mcp.json | grep -A 10 "mariadb"
   ```

3. Restart Claude Code
   ```bash
   exit
   claude
   ```

4. Test MCP server manually
   ```bash
   npx -y @modelcontextprotocol/server-mysql
   ```

---

## Advanced Configuration

### Using Remote Database

If your database is on a remote server:

```bash
# .env
DB_HOST=db.example.com
DB_PORT=3306
DB_USER=readonly_user
DB_PASSWORD=password
DB_NAME=production_db
```

**Security Note**: Ensure SSH tunnel or VPN is used for remote connections.

### SSH Tunnel for Remote Database

```bash
# Create SSH tunnel
ssh -L 3307:localhost:3306 user@remote-server.com

# Update .env to use tunneled port
DB_HOST=localhost
DB_PORT=3307
```

### Multiple Databases

If you need to query multiple databases, create multiple MCP server instances:

```json
{
  "mcpServers": {
    "mariadb-users": {
      "command": "node",
      "args": ["mcp-servers/mariadb-server/index.js"],
      "env": {
        "DB_HOST": "${DB_HOST}",
        "DB_PORT": "${DB_PORT}",
        "DB_USER": "${DB_USER}",
        "DB_PASSWORD": "${DB_PASSWORD}",
        "DB_NAME": "users_db"
      }
    },
    "mariadb-orders": {
      "command": "node",
      "args": ["mcp-servers/mariadb-server/index.js"],
      "env": {
        "DB_HOST": "${DB_HOST}",
        "DB_PORT": "${DB_PORT}",
        "DB_USER": "${DB_USER}",
        "DB_PASSWORD": "${DB_PASSWORD}",
        "DB_NAME": "orders_db"
      }
    }
  }
}
```

---

## FAQ

### Q: Can I use this with MySQL instead of MariaDB?
**A:** Yes! The MCP server package `@modelcontextprotocol/server-mysql` works with both MySQL and MariaDB.

### Q: Can agents write to the database?
**A:** No, by design. The READ-ONLY user can only SELECT data. This prevents accidental data corruption.

### Q: What if I need to test database writes?
**A:** Use a separate test database with a different user that has write permissions. Don't use MCP for write operations.

### Q: Can I use this with cloud databases (AWS RDS, Azure, etc.)?
**A:** Yes, just update DB_HOST to your cloud database endpoint and ensure network access is allowed.

### Q: How do I check which MCP servers are active?
**A:** In Claude Code, you can check active MCP servers. The MariaDB server will appear if configured correctly.

---

## Related Documentation

- [MCP Setup Guide for VISSOFT](MCP_SETUP_VISSOFT.md) - Jira & Confluence setup
- [Multi-Agent Orchestration](../MULTI_AGENT_ORCHESTRATION.md) - Complete workflow guide
- [Test Agent Guide](../.claude/agents/test.md) - Test agent configuration
- [Code Review Agent Guide](../.claude/agents/code-review.md) - Review agent configuration

---

## Support

**Issues with MariaDB MCP?**
1. Check troubleshooting section above
2. Verify .env configuration
3. Test database connection manually with mysql command
4. Check MCP server logs for errors

**Need help?**
- Contact DevOps team for database access
- See VISSOFT internal wiki for database credentials
- Ask in #dev-support Slack channel

---

**Last Updated**: 2026-01-23
**Version**: 1.0.0
**Maintained by**: VISSOFT DevOps Team
