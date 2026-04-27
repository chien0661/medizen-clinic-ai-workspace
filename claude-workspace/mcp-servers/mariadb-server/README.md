# MariaDB MCP Server

This MCP server provides secure database access for the App Center Backend project.

## Features

- ✅ Execute SELECT queries
- ✅ Execute INSERT, UPDATE, DELETE statements
- ✅ Get table schema information
- ✅ Connection pooling
- ✅ Safety checks (prevents DROP, TRUNCATE)

## Installation

```bash
cd mcp-servers/mariadb-server
npm install
```

## Configuration

1. Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

2. Update `.env` with your database credentials:
```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=your_username
DB_PASSWORD=your_password
DB_NAME=miniapp_configuration
```

3. Get credentials from `src/main/resources/application-vis.properties`:
```properties
app.datasource.default.url=jdbc:mariadb://HOST:PORT/DATABASE
app.datasource.default.username=USERNAME
app.datasource.default.password=PASSWORD
```

## Usage with Claude Code

Add to your `.claude/settings.json`:

```json
{
  "mcpServers": {
    "mariadb": {
      "command": "node",
      "args": ["D:/01. PROJECTS/DEMO MULTIPLE AGENTS/my-ai-team/mcp-servers/mariadb-server/index.js"],
      "env": {
        "DB_HOST": "localhost",
        "DB_PORT": "3306",
        "DB_USER": "your_username",
        "DB_PASSWORD": "your_password",
        "DB_NAME": "miniapp_configuration"
      }
    }
  }
}
```

## Available Tools

### 1. query
Execute SELECT queries:
```javascript
{
  "name": "query",
  "arguments": {
    "sql": "SELECT * FROM bi_miniapp_stats WHERE miniapp_code = 'highland_loyalty' LIMIT 10"
  }
}
```

### 2. execute
Execute INSERT, UPDATE, DELETE:
```javascript
{
  "name": "execute",
  "arguments": {
    "sql": "INSERT INTO bi_miniapp_stats (...) VALUES (...)"
  }
}
```

### 3. schema
Get table schema:
```javascript
{
  "name": "schema",
  "arguments": {
    "table": "bi_miniapp_stats"
  }
}
```

## Safety Features

- ❌ **DROP** and **TRUNCATE** operations blocked
- ✅ Only SELECT queries allowed in `query` tool
- ✅ Connection pooling prevents resource exhaustion
- ✅ Parameterized queries support (via MariaDB driver)

## Testing

Test the MCP server directly:

```bash
# Set environment variables
export DB_HOST=localhost
export DB_PORT=3306
export DB_USER=your_username
export DB_PASSWORD=your_password
export DB_NAME=miniapp_configuration

# Run the server
node index.js
```

Then in another terminal, test with MCP inspector:
```bash
npx @modelcontextprotocol/inspector node index.js
```

## Troubleshooting

### Connection Refused
- Check MariaDB is running: `netstat -ano | findstr :3306`
- Verify credentials in `.env`
- Check firewall settings

### Permission Denied
- Ensure database user has SELECT, INSERT, UPDATE, DELETE permissions
- Grant permissions if needed:
```sql
GRANT SELECT, INSERT, UPDATE, DELETE ON miniapp_configuration.* TO 'your_username'@'localhost';
FLUSH PRIVILEGES;
```

### Module Not Found
- Run `npm install` in the mcp-servers/mariadb-server directory
- Ensure Node.js version >= 16

## Security Notes

- ⚠️ Never commit `.env` file to git
- ⚠️ Use read-only user for production queries
- ⚠️ Limit permissions to only required tables
- ✅ MCP server already blocks dangerous operations

## Integration with BUG-003 Diagnostic

Once configured, Claude can:
1. Run diagnostic queries automatically
2. Check for missing data
3. Execute INSERT statements
4. Verify data insertion
5. All without manual SQL execution!

Example workflow:
```
Claude: Let me check the database for missing demographics data...
[Runs diagnostic query via MCP]
Claude: Found missing data for highland_loyalty + seven_day + gender
[Executes INSERT via MCP]
Claude: Data inserted successfully. Verification shows 3 rows added.
[Re-runs tests]
Claude: Tests now pass! Bug fixed. ✅
```
