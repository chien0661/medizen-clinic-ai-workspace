# SonarQube MCP Server

MCP (Model Context Protocol) server for integrating SonarQube code quality checks into Claude Code workflows.

## Features

- **Quality Gate Validation**: Check if project passes quality gate with detailed failure reporting
- **Issue Search**: Find bugs, vulnerabilities, code smells, and security hotspots
- **Metrics Retrieval**: Get code coverage, technical debt, and other quality metrics
- **Fail-Safe Mode**: Blocks operations if SonarQube is unreachable (ensures quality checks never skipped)

## Installation

```bash
cd mcp-servers/sonarqube-server
npm install
```

## Configuration

### Pre-Configured for Company Use

✅ **The SonarQube token is already configured** in `.mcp.json` for company-wide use.

**No additional setup required** - the server is ready to use immediately.

### MCP Configuration

The server is configured in `.mcp.json` (already set up):

```json
{
  "sonarqube": {
    "command": "node",
    "args": ["mcp-servers/sonarqube-server/index.js"],
    "env": {
      "SONARQUBE_URL": "https://sonarqube.vissoft.vn",
      "SONARQUBE_TOKEN": "squ_fe8873c4ca8ed5ca60dc66bd40d84f649a2158b4"
    },
    "disabled": false
  }
}
```

**Note:** The token is a company-wide shared token with read-only access to all projects in SonarQube.

**How it works:**
- When Claude Code loads the MCP server, it automatically sets the environment variables from `.mcp.json`
- No manual configuration needed - just restart Claude Code to load the server
- The test scripts (test-connection.js, test-tools.js) require manual env var for standalone testing

### For Personal Token (Optional)

If you prefer to use your own personal token instead:

1. Login to https://sonarqube.vissoft.vn
2. Click on your avatar → **My Account**
3. Go to **Security** tab
4. Click **Generate Token**
5. Enter token name: `MCP Server - [Your Name]`
6. Select type: **User Token**
7. Click **Generate**
8. Update `.mcp.json` with your token (line 56)

## Available MCP Tools

### 1. `get_quality_gate`

Get the quality gate status for a project.

**Parameters:**
- `projectKey` (required): SonarQube project key
- `branch` (optional): Branch name

**Example:**
```json
{
  "projectKey": "com.company:my-project",
  "branch": "feature/user-authentication"
}
```

**Response:**
```json
{
  "projectStatus": {
    "status": "ERROR",
    "conditions": [
      {
        "status": "ERROR",
        "metricKey": "new_bugs",
        "comparator": "GT",
        "errorThreshold": "0",
        "actualValue": "2"
      }
    ]
  }
}
```

### 2. `get_issues`

Search for code quality issues.

**Parameters:**
- `projectKey` (required): SonarQube project key
- `branch` (optional): Branch name
- `severity` (optional): BLOCKER, CRITICAL, MAJOR, MINOR, INFO
- `types` (optional): BUG,VULNERABILITY,CODE_SMELL,SECURITY_HOTSPOT
- `createdAfter` (optional): ISO 8601 date (e.g., "2024-01-01")

**Example:**
```json
{
  "projectKey": "com.company:my-project",
  "severity": "CRITICAL",
  "types": "BUG,VULNERABILITY"
}
```

**Response:**
```json
{
  "total": 3,
  "issues": [
    {
      "key": "issue-123",
      "severity": "CRITICAL",
      "type": "BUG",
      "message": "Null pointer dereference",
      "component": "src/Main.java",
      "line": 42
    }
  ],
  "dashboardUrl": "https://sonarqube.vissoft.vn/dashboard?id=..."
}
```

### 3. `get_metrics`

Get code quality metrics.

**Parameters:**
- `projectKey` (required): SonarQube project key
- `branch` (optional): Branch name
- `metrics` (optional): Array of metric keys

**Example:**
```json
{
  "projectKey": "com.company:my-project",
  "branch": "develop"
}
```

**Response:**
```json
{
  "projectKey": "com.company:my-project",
  "branch": "develop",
  "metrics": {
    "coverage": "85.2",
    "bugs": "0",
    "vulnerabilities": "0",
    "code_smells": "12",
    "new_coverage": "90.5"
  },
  "dashboardUrl": "https://sonarqube.vissoft.vn/dashboard?id=..."
}
```

### 4. `validate_quality_gate` ⭐ **Primary Tool**

Validate if project passes quality gate with detailed failure information. Used by `/commit-push-pr` skill.

**Parameters:**
- `projectKey` (required): SonarQube project key
- `branch` (optional): Branch name

**Example:**
```json
{
  "projectKey": "com.company:my-project",
  "branch": "feature/task-001"
}
```

**Response (Pass):**
```json
{
  "passed": true,
  "status": "OK",
  "message": "All quality gate conditions met",
  "dashboardUrl": "https://sonarqube.vissoft.vn/dashboard?id=..."
}
```

**Response (Fail):**
```json
{
  "passed": false,
  "status": "ERROR",
  "message": "Quality gate error: 3 condition(s) failed",
  "failures": [
    {
      "metric": "new_bugs",
      "threshold": "0",
      "actual": "2",
      "comparator": "GT",
      "message": "New Bugs: 2 (threshold: ≤ 0)"
    },
    {
      "metric": "new_coverage",
      "threshold": "80",
      "actual": "65.3",
      "comparator": "LT",
      "message": "Coverage on New Code: 65.3% (threshold: ≥ 80%)"
    }
  ],
  "dashboardUrl": "https://sonarqube.vissoft.vn/dashboard?id=..."
}
```

**Response (Error - Fail Safe):**
```json
{
  "passed": false,
  "status": "ERROR",
  "error": "SONARQUBE_UNREACHABLE",
  "message": "Cannot reach SonarQube server. Please verify the server is accessible.",
  "details": {
    "cause": "ECONNREFUSED",
    "action": "BLOCK",
    "guidance": [
      "Verify SonarQube server is running: https://sonarqube.vissoft.vn",
      "Check network connectivity",
      "Verify firewall settings allow access"
    ]
  }
}
```

## Error Handling

The server implements **fail-safe mode**: all errors BLOCK operations to ensure quality checks are never skipped.

### Error Categories

| Error Code | HTTP Status | Meaning | Action |
|------------|-------------|---------|--------|
| `SONARQUBE_UNREACHABLE` | - | Server unreachable (network error) | BLOCK |
| `AUTHENTICATION_FAILED` | 401 | Invalid or missing token | BLOCK |
| `INSUFFICIENT_PERMISSIONS` | 403 | Token lacks permissions | BLOCK |
| `PROJECT_NOT_FOUND` | 404 | Project doesn't exist | BLOCK |
| `SERVER_ERROR` | 500-504 | SonarQube server error | BLOCK |
| `INVALID_RESPONSE` | - | Malformed JSON response | BLOCK |
| `UNKNOWN_ERROR` | - | Unexpected error | BLOCK |

Each error includes:
- **Error code**: Machine-readable error type
- **Message**: Human-readable error description
- **Guidance**: Step-by-step troubleshooting instructions

## Usage in commit-push-pr Skill

The `/commit-push-pr` skill automatically uses this MCP server to enforce quality gates before allowing code push.

**Workflow:**
```
[1] Commit changes locally
[2] Scan with SonarQube (validate_quality_gate)
[3] If PASS → Push to remote → Create PR
    If FAIL → BLOCK push, show issues
    If ERROR → BLOCK push (fail-safe)
```

**Example output on failure:**
```
❌ QUALITY GATE FAILED - Push Blocked

Project: com.company:my-project
Branch: feature/task-001-user-profile

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Failed Conditions (2):

1. ❌ New Bugs: 2 (threshold: ≤ 0)
   Must fix 2 new bugs before pushing

2. ❌ Coverage on New Code: 65.3% (threshold: ≥ 80%)
   Need 14.7% more test coverage

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 View detailed report:
https://sonarqube.vissoft.vn/dashboard?id=com.company:my-project&branch=feature/task-001-user-profile

🔧 Next steps:
1. Click the link above to see specific issues
2. Fix the identified problems
3. Commit your fixes
4. Re-run: /commit-push-pr TASK-001
```

## Testing

### Manual Testing

Test the server directly:

```bash
# Start the server
export SONARQUBE_TOKEN=your-token
node mcp-servers/sonarqube-server/index.js
```

### Test with Claude Code

Use MCP tools in Claude Code:

```
Call: mcp__sonarqube__validate_quality_gate
Parameters:
  - projectKey: your-project-key
  - branch: main
```

## Troubleshooting

### Server won't start

**Error:** `SONARQUBE_TOKEN environment variable is required`

**Solution:**
```bash
export SONARQUBE_TOKEN=squ_xxxxxxxxxxxxxxxxxxxx
```

### Authentication failed (401)

**Cause:** Invalid or expired token

**Solution:**
1. Generate new token in SonarQube
2. Update environment variable
3. Restart MCP server

### Project not found (404)

**Cause:** Project key is incorrect or project never analyzed

**Solution:**
1. Verify project key matches SonarQube
2. If new project, run initial analysis:
   ```bash
   mvn clean verify sonar:sonar
   ```
3. Check project exists: https://sonarqube.vissoft.vn/projects

### Server unreachable

**Cause:** Network issues or SonarQube server down

**Solution:**
1. Verify URL: https://sonarqube.vissoft.vn
2. Check network connectivity
3. Verify firewall allows access
4. Check SonarQube server status

## Dependencies

- **@modelcontextprotocol/sdk**: ^0.5.0
- **Node.js**: >= 18.0.0

## Architecture

```
index.js (MCP Server)
    ↓
lib/sonarqube-client.js (HTTP Client)
    ├→ GET /api/qualitygates/project_status
    ├→ GET /api/issues/search
    └→ GET /api/measures/component
    ↓
lib/quality-gate-checker.js (Validation Logic)
    ├→ Validate quality gate
    ├→ Parse failed conditions
    └→ Format failure messages
    ↓
lib/error-handler.js (Error Handling)
    ├→ Categorize errors
    ├→ Format error responses
    └→ Provide guidance
```

## License

MIT

## Support

For issues or questions:
- SonarQube access: Contact SonarQube administrator
- MCP server bugs: Create issue in project repository
- Integration issues: See PROJECT.md and CLAUDE.md
