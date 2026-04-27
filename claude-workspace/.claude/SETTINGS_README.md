# Claude Code Settings Guide

This file explains the permissions configured in `settings.json` for this AI Team template.

## Overview

The `.claude/settings.json` file controls what operations Claude Code agents can perform. This template is configured for:

- **Main Tech Stack**: Java Spring Boot + ReactJS
- **Deployment**: On-premises (Docker)
- **Documentation**: Hybrid (Read from Jira/Confluence/Figma, Write to markdown)

## Permission Philosophy

**ALLOW List**: Operations explicitly permitted
**DENY List**: Operations explicitly blocked (security)

**Default behavior**: If not in either list, Claude Code will ask for permission.

---

## Allowed Operations

### Git Operations
**Full git workflow supported:**
- `git status`, `git add`, `git commit`, `git log`, `git diff`
- `git branch`, `git checkout`, `git merge`
- `git pull`, `git push`, `git tag`, `git fetch`, `git stash`, `git reset`

**Why**: Git operations are core to the multi-agent workflow.

### Java / Spring Boot (Maven)
**Build and development:**
- `mvn clean`, `mvn install`, `mvn test`, `mvn compile`, `mvn package`, `mvn verify`
- `mvn spring-boot:run`, `mvn spring-boot:start`, `mvn spring-boot:stop`
- `mvn sonar:sonar` (code quality)
- `mvn dependency:tree`, `mvn dependency:analyze`
- `mvn versions:display-dependency-updates`

**Combined commands:**
- `mvn clean install`, `mvn clean package`, `mvn clean test`

**Why**: Maven is the standard build tool for Spring Boot projects.

### Java / Spring Boot (Gradle)
**Alternative build tool:**
- `gradle build`, `gradle clean`, `gradle test`
- `gradle bootRun`, `gradle bootJar`
- `gradle dependencies`, `gradle tasks`

**Why**: Some Spring Boot projects use Gradle instead of Maven.

### Java Direct Execution
- `java -jar` (run built JAR files)
- `java -version` (check Java version)
- `javac` (compile Java source files)

### Node.js / React (NPM)
**Package management and development:**
- `npm install`, `npm ci` (install dependencies)
- `npm run build`, `npm run dev`, `npm run start`, `npm run test`
- `npm run lint`, `npm run format` (code quality)
- `npm test` (run tests)
- `npm outdated`, `npm audit`, `npm audit fix` (security)
- `npm list` (dependency tree)

**Why**: NPM is the standard package manager for React projects.

### Node.js / React (Yarn)
**Alternative package manager:**
- `yarn`, `yarn install`
- `yarn build`, `yarn dev`, `yarn start`, `yarn test`
- `yarn lint`, `yarn format`

**Why**: Many React projects use Yarn for faster dependency management.

### Node.js / React (PNPM)
**Alternative package manager:**
- `pnpm install`, `pnpm build`, `pnpm dev`, `pnpm start`, `pnpm test`

**Why**: PNPM is growing in popularity for monorepos.

### Node.js Direct Execution
- `node -v`, `node --version` (check Node version)
- `npx` (execute npm packages)

### Docker & Containers (On-Prem Deployment)
**Container operations:**
- `docker build`, `docker run`, `docker ps`, `docker images`
- `docker logs`, `docker exec` (debugging)
- `docker stop`, `docker start`, `docker restart`
- `docker system prune` (cleanup)

**Docker Compose (orchestration):**
- `docker-compose up`, `docker-compose down`
- `docker-compose ps`, `docker-compose logs`, `docker-compose build`

**Why**: On-premises deployment requires Docker for containerization.

### Testing Tools
- `jest`, `vitest` (JavaScript/React testing)
- `junit` (Java testing)
- `newman` (Postman/API testing)
- `cypress`, `playwright` (E2E testing)

**Why**: Comprehensive testing is core to the multi-agent workflow.

### Code Quality & Security
- `eslint`, `prettier` (JavaScript/React)
- `sonar-scanner` (SonarQube)
- `checkstyle`, `spotbugs` (Java)

**Why**: Code Review Agent needs these tools.

### General Utilities
**File operations:**
- `ls`, `pwd`, `cd`, `mkdir`, `tree`
- `cp`, `mv`, `ln -s` (copy, move, symlink)
- `chmod`, `chown` (permissions)

**Process management:**
- `ps`, `kill`, `pkill`, `killall`

**Network (health checks):**
- `netstat`, `lsof`, `ping`

**Other:**
- `echo`, `which`

**Why**: Required for basic file navigation and system operations.

### Dedicated Tools (PREFERRED)
- `Read`, `Edit`, `Write` (file operations - more efficient than bash)
- `Glob`, `Grep` (searching - more efficient than find/grep)
- `TodoWrite` (task tracking)

**Why**: These dedicated tools are more token-efficient than bash equivalents.

---

## Denied Operations (Security)

### Secrets & Sensitive Files
**Blocked from reading:**
- `.env`, `.env.*` (environment variables)
- `secrets/**` (secrets directory)
- `**/*.key`, `**/*.pem`, `**/*.p12`, `**/*.jks` (cryptographic keys)
- `**/credentials.json` (credentials)
- `**/application-prod.properties`, `**/application-prod.yml` (production configs)

**Why**: Prevent accidental exposure of sensitive data.

### Destructive Operations
**Blocked:**
- `rm -rf`, `rm -fr` (recursive delete)
- `sudo rm` (elevated delete)
- `sudo *` (any elevated command)

**Why**: Prevent accidental data loss.

### Network Operations
**Blocked:**
- `curl`, `wget` (arbitrary HTTP requests)
- `WebFetch` (Claude Code's web fetch tool)

**Why**: Prevent unauthorized external calls and data exfiltration.

### System Modifications
**Blocked:**
- `apt`, `apt-get`, `yum`, `dnf`, `pacman` (package managers)
- `brew install` (macOS package manager)
- `npm install -g`, `yarn global` (global package installation)
- `systemctl`, `service` (system service management)

**Why**: Prevent system-level changes that could affect stability.

### Disk Operations
**Blocked:**
- `dd`, `mkfs`, `fdisk`, `parted` (disk formatting)

**Why**: Prevent data loss from disk operations.

---

## How to Customize

### Adding New Tech Stack

To add support for another tech stack (e.g., Python, Go, Rust):

1. Edit `.claude/settings.json`
2. Add to `permissions.allow` array:

```json
"Bash(python3:*)",
"Bash(pip3:*)",
"Bash(pytest:*)",
"Bash(poetry:*)"
```

3. Save and restart Claude Code session

### Adding Specific Commands

If you need a specific command pattern:

```json
"Bash(your-command:*)"
```

The `:*` means "any arguments after this command".

### Blocking Specific Patterns

Add to `permissions.deny`:

```json
"Bash(dangerous-command:*)",
"Read(./sensitive-folder/**)"
```

---

## Best Practices

### 1. Use Dedicated Tools First
❌ **DON'T**: `Bash(cat filename.txt)`
✅ **DO**: `Read` tool

**Why**: Dedicated tools are more token-efficient and provide better error handling.

### 2. Never Bypass Security Blocks
The deny list exists for good reasons:
- Secrets protection
- Data loss prevention
- System stability

If you need access to something blocked, **modify the project** to not require it (e.g., use environment variables instead of credentials files).

### 3. Keep Production Configs Separate
Production configurations should:
- Use environment variables
- Not be committed to git
- Not be readable by Claude Code (blocked in deny list)

### 4. Token Optimization
- Use `-q` (quiet) flags: `mvn test -q`
- Use `--silent` flags: `npm install --silent`
- Use dedicated tools instead of bash when possible

---

## Troubleshooting

### "Permission denied" errors

**If you see**: `Permission denied: Bash(some-command:...)`

**Check**:
1. Is the command in the `deny` list? (intentional block)
2. Is the command not in the `allow` list? (needs approval)

**Fix**:
- If command is safe, add to `allow` list
- If command is dangerous, find alternative approach

### Commands asking for permission every time

**If**: Claude Code keeps asking for permission for safe commands

**Fix**: Add the command pattern to `allow` list in `settings.json`

### MCP Tools Not Working

**If**: Jira/Confluence/Figma MCP tools fail

**Check**:
1. MCP server configured? (see `.mcp.json` or user MCP settings)
2. Environment variables set? (`JIRA_API_TOKEN`, etc.)
3. Network accessible? (on-prem may have firewall rules)

**See**: `CLAUDE.md` MCP Integration section for setup details

---

## Security Review Checklist

Before deploying this template, verify:

- [ ] Production secrets are NOT in `.env` files (use secret manager)
- [ ] Production configs are in `deny` list
- [ ] No global package installation allowed (`npm install -g`, etc.)
- [ ] No sudo access allowed
- [ ] No arbitrary network requests allowed (`curl`, `wget`)
- [ ] Destructive commands are blocked (`rm -rf`, disk operations)
- [ ] Only necessary commands in `allow` list

---

## Related Documentation

- **[CLAUDE.md](../CLAUDE.md)**: Full development guidelines including MCP integration
- **[PROJECT.md](../PROJECT.md)**: Project-specific configuration
- **[settings.json](./settings.json)**: Actual permission configuration

---

**Last Updated**: 2026-01-23
**Tech Stack**: Java Spring Boot + ReactJS
**Deployment**: On-premises (Docker)
