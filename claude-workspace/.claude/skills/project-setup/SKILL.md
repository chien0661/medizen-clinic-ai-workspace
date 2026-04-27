# Skill: project-setup

## Description
Initialize a new or existing project from the AI Team Template with interactive setup.

## Invocation
```bash
/project-setup              # Interactive setup (default)
/project-setup --quick      # Minimal: skip MCP, basic docs, 3 starter tasks
/project-setup --full       # All options: MCP, hooks, memory, CI/CD
```

## Setup Paths

Ask user upfront: **"How do you want to set up this project?"**

| Path | When to use |
|------|-------------|
| **C: Workspace Repo** ⭐ Recommended | New project, or any project where you want a clean separation between AI tooling and source code |
| **A: Existing Project** | Adding template to an existing repo that already has team buy-in for mixed setup |
| **B: New Empty Project** | New project where source code WILL live in the same repo (simple/solo projects) |

> **Why workspace-first?** Source code repos stay clean — no AI team artifacts in commit history.
> All task tracking, agent files, and docs live in a dedicated workspace repo.
> Agents access source repos via absolute paths declared in PROJECT.md.

---

## Path C: Workspace Repo (Recommended)

A workspace repo contains only AI team files. Source code stays in its own repo(s).

```
my-project-workspace/      ← Claude Code runs from here
├── .claude/
├── docs/tasks/
├── scripts/
├── PROJECT.md
└── CLAUDE.md

my-project-api/            ← source code, untouched
my-project-frontend/       ← source code, untouched
```

### Steps

1. Ask: parent directory + workspace name (e.g. `my-project-workspace`)
2. Create and init:
```bash
mkdir -p "PARENT/WORKSPACE_NAME"
cd "PARENT/WORKSPACE_NAME"
git init
```
3. Copy template files (see File Copy Logic below — workspace variant)
4. Scan sibling directories for source repos:
```bash
for d in ../*/; do [ -d "$d/.git" ] && echo "$d"; done
```
5. Ask: "Which of these repos does this workspace manage?" (multi-select)
6. For each selected repo, ask for a short description
7. Customize PROJECT.md (see PROJECT.md Sections below)
   - Write `source-repos` section with absolute paths
   - Set `workspace-type: workspace`
   - Analyze source repos for tech stack, endpoints, test files (read-only scan)
8. Create `docs/` structure with `.gitkeep` in empty dirs
9. Configure MCP servers (see MCP Configuration below)
10. Ask for personal access tokens
11. Optionally set up Persistent Memory
12. Configure Claude Code settings (see Settings below)
13. Optionally create initial tasks
14. Validate setup (see Validation Checklist)
15. Guide user to exit and restart Claude in workspace directory

### File Copy Logic (Workspace Variant)

```bash
# Always copy
cp CLAUDE.md "TARGET/CLAUDE.md"
cp PROJECT.md "TARGET/PROJECT.md"
cp -r .claude/ "TARGET/.claude/"
cp -r docs/ "TARGET/docs/"
cp .env.example "TARGET/.env.example"
cp .mcp.json.example "TARGET/.mcp.json.example"
cp -r scripts/ "TARGET/scripts/"
cp .gitignore "TARGET/.gitignore"

# Create .template-version
LATEST_VERSION=$(grep -m 1 "^## \[" CHANGELOG.md | sed 's/## \[\(.*\)\].*/\1/')
```

No source code directories needed — workspace repo is docs/config only.

---

## Path A: Existing Project

Add template to an existing repo (source code + AI tooling in the same repo).

1. Ask project directory path (full absolute path)
2. Optionally ask project description (speeds up analysis)
3. Verify running from template-ai-team directory
4. Copy template files to target (see File Copy Logic — Existing Project below)
5. Navigate to target directory (`cd "TARGET_PATH"`)
6. Analyze codebase (auto-detect tech stack, deps, build files, endpoints, tests)
7. Customize PROJECT.md (see PROJECT.md Sections below)
8. Create docs/ structure with `.gitkeep` in empty dirs
9. Configure MCP servers
10. Ask for personal access tokens
11. Optionally set up Persistent Memory
12. Configure Claude Code settings
13. Optionally create initial tasks
14. Validate setup
15. Guide user to exit and restart Claude in target directory

### File Copy Logic (Existing Project)

**CRITICAL: Copy from template dir BEFORE navigating to target.**

```bash
# Always copy
cp CLAUDE.md "TARGET/CLAUDE.md"
cp PROJECT.md "TARGET/PROJECT.md"
cp -r .claude/ "TARGET/.claude/"

# Conditional: docs/
if [ ! -d "TARGET/docs" ]; then
  cp -r docs/ "TARGET/docs/"
else
  # Create missing subdirs (agent working directories)
  mkdir -p "TARGET/docs/specs" "TARGET/docs/api" "TARGET/docs/features"
  mkdir -p "TARGET/docs/reviews" "TARGET/docs/test-reports" "TARGET/docs/handoffs"
  mkdir -p "TARGET/docs/bugs" "TARGET/docs/troubleshooting" "TARGET/docs/tasks"
  mkdir -p "TARGET/docs/guides" "TARGET/docs/lessons-learned"

  # Copy template files used by agents (overwrite to keep up-to-date)
  cp -r docs/templates/ "TARGET/docs/templates/"
  cp -r docs/templates/specs/*-template.md "TARGET/docs/templates/specs/" 2>/dev/null || true
  cp -r docs/templates/specs/*-template.html "TARGET/docs/templates/specs/" 2>/dev/null || true

  # Copy reference docs (only if not exists — don't overwrite user edits)
  [ ! -f "TARGET/docs/guide/workflow/MULTI_AGENT_ORCHESTRATION.md" ] && mkdir -p "TARGET/docs/guide/workflow" && cp docs/guide/workflow/MULTI_AGENT_ORCHESTRATION.md "TARGET/docs/guide/workflow/"
  [ ! -f "TARGET/docs/guide/workflow/WORKFLOW.md" ] && mkdir -p "TARGET/docs/guide/workflow" && cp docs/guide/workflow/WORKFLOW.md "TARGET/docs/guide/workflow/"
  [ ! -f "TARGET/docs/guide/reference/using-persistent-memory.md" ] && mkdir -p "TARGET/docs/guide/reference" && cp docs/guide/reference/using-persistent-memory.md "TARGET/docs/guide/reference/" 2>/dev/null || true
  [ ! -f "TARGET/docs/guide/setup/remote-memory-deployment.md" ] && mkdir -p "TARGET/docs/guide/setup" && cp docs/guide/setup/remote-memory-deployment.md "TARGET/docs/guide/setup/" 2>/dev/null || true
  [ ! -f "TARGET/docs/lessons-learned/README.md" ] && cp docs/lessons-learned/README.md "TARGET/docs/lessons-learned/" 2>/dev/null || true
fi

# Conditional: only if not exists
[ ! -f "TARGET/.env.example" ] && cp .env.example "TARGET/.env.example"
[ ! -f "TARGET/.mcp.json.example" ] && cp .mcp.json.example "TARGET/.mcp.json.example"
[ ! -d "TARGET/scripts" ] && cp -r scripts/ "TARGET/scripts/"

# .gitignore: MERGE if exists, copy if not
if [ -f "TARGET/.gitignore" ]; then
  cat .gitignore >> "TARGET/.gitignore"
  sort -u "TARGET/.gitignore" -o "TARGET/.gitignore"
else
  cp .gitignore "TARGET/.gitignore"
fi

# Create .template-version
LATEST_VERSION=$(grep -m 1 "^## \[" CHANGELOG.md | sed 's/## \[\(.*\)\].*/\1/')
```

**Windows equivalents**: Use `copy`, `xcopy /E /I`, `findstr`, PowerShell for date parsing.

---

## Path B: New Empty Project

1. Ask parent directory + project name
2. `mkdir -p "PARENT/PROJECT_NAME"`
3. Copy template files (same as Path A)
4. Navigate to new directory
5. Collect project info (name, tech stack from 6 options, architecture from 5 options)
6. Generate PROJECT.md from collected info
7. Steps 8-15 same as Path A

---

## PROJECT.md Sections to Customize

Replace all `[placeholder]` values with actual detected or user-provided values:

- Project overview and description
- Technology stack details (language, framework, package manager)
- Architecture pattern (hexagonal, layered, microservices, etc.)
- Build and run commands (detected from package.json, pom.xml, etc.)
- Database configuration
- Environment setup
- Testing strategy (detected test frameworks)
- Code style guidelines

**Existing projects / Path A**: Auto-detect from codebase (actual deps, endpoints, test files, coverage).
**New projects / Path B**: Use template defaults for chosen tech stack.

### Source Repos Configuration (Path C only)

For workspace repos, write the `source-repos` section in PROJECT.md so agents know
where source code lives and can navigate there using absolute paths:

```yaml
workspace-type: workspace

source-repos:
  api:
    path: /absolute/path/to/my-project-api
    description: Backend REST API (Spring Boot)
    primary-language: java
    build-cmd: mvn clean package -q
    test-cmd: mvn test -q
  frontend:
    path: /absolute/path/to/my-project-frontend
    description: React web app
    primary-language: typescript
    build-cmd: npm run build --silent
    test-cmd: npm test -- --watchAll=false
```

Agents use these paths to:
- Read source files: `Read /absolute/path/to/my-project-api/src/...`
- Edit source files: `Edit /absolute/path/to/my-project-api/src/...`
- Run commands: `Bash(cd /absolute/path/to/my-project-api && mvn test)`

**Detect paths automatically** — check sibling directories, ask user to confirm.
Use `pwd` output as base for constructing absolute paths (avoid `~` or relative paths).

---

## MCP Configuration

### Step 1: Download MCP Client
```bash
curl -o mcp-client.js https://cdn.vissoft.vn/raw-file/mcp-client.js
```

### Step 2: Create `.mcp.json` from template

```bash
# Copy from example template (single source of truth)
cp .mcp.json.example "TARGET/.mcp.json"
```

**After copying**, ask user which MCP servers to enable/disable. Update `"disabled"` field accordingly:
- **atlassian**, **claude-mem**, **sonarqube**: Enabled by default (`disabled: false`)
- **mariadb**, **figma**, **playwright**: Disabled by default (`disabled: true`) — user enables as needed
- **atlassian-vds**: Enable only if team uses VDS Confluence

**Note:** `claude-mem` defaults to Remote Mode (team worker). See Persistent Memory Setup below for all modes.

### Step 3: Ask for Tokens

Prompt user for:
- **Jira Token**: Profile → Personal Access Tokens at `https://jira.vissoft.vn`
- **Confluence Token**: Profile → Personal Access Tokens at `https://confluence.vissoft.vn`
- **VDS Token** (if needed): Profile → Personal Access Tokens at `http://10.254.136.35:8090`

### Step 4: Create `.env`
```bash
JIRA_TOKEN=user-provided-token
CONFLUENCE_TOKEN=user-provided-token
VDS_CONFLUENCE_PAT=user-provided-token
MEMORY_API_KEY=api-key-from-team-lead
```

### Step 5: VDS MCP Server Setup
```bash
cd mcp-servers/mcp-vds-server && npm install && cd ../..
```
Note: `dist/` and `package.json` are committed to git. Teams only run `npm install`.

### Step 6: Ensure `.gitignore` entries
```
.env
.mcp.json
mcp-client.js
*.local.json
deployment/docker/.env
deployment/docker/data/
deployment/docker/logs/
.claude-mem/
*.db-shm
*.db-wal
```

---

## Persistent Memory Setup (Optional)

Ask: "Do you want to set up Persistent Memory?" → Remote / Docker / Local / No

### Remote Mode (Recommended for teams)

Connect to the shared team worker server. No local worker or API key needed.

`.mcp.json` `claude-mem` entry:
```json
"claude-mem": {
  "command": "node",
  "args": ["mcp-servers/claude-mem-server/dist/index.js"],
  "env": {
    "WORKER_URL": "http://10.10.100.22:37777",
    "API_KEY": "${MEMORY_API_KEY}"
  },
  "disabled": false,
  "alwaysAllow": ["search", "timeline", "get_observations", "__IMPORTANT"]
}
```

Add to `.env`:
```bash
MEMORY_API_KEY=<api-key-from-team-lead>
```

Ask user for `MEMORY_API_KEY` (get from team lead or server admin).

### Docker Mode (Self-hosted worker)
```bash
docker --version   # Must be 20.10+
docker compose version  # Must be 2.0+
cd deployment/docker && bash setup.sh
```

`.mcp.json` `claude-mem` entry:
```json
"claude-mem": {
  "command": "node",
  "args": ["mcp-servers/claude-mem-server/dist/index.js"],
  "env": {
    "WORKER_URL": "http://localhost:37777",
    "API_KEY": "<generated-client-api-key>",
    "ANTHROPIC_API_KEY": "${ANTHROPIC_API_KEY}"
  },
  "disabled": false,
  "alwaysAllow": ["search", "timeline", "get_observations", "__IMPORTANT"]
}
```

### Local Mode (Solo developer)

`.mcp.json` `claude-mem` entry:
```json
"claude-mem": {
  "command": "node",
  "args": ["mcp-servers/claude-mem-server/dist/index.js"],
  "env": {
    "WORKER_URL": "http://localhost:37777",
    "ANTHROPIC_API_KEY": "${ANTHROPIC_API_KEY}"
  },
  "disabled": false,
  "alwaysAllow": ["search", "timeline", "get_observations", "__IMPORTANT"]
}
```

Database stored at `~/.claude-mem/memory.db`. Requires `ANTHROPIC_API_KEY` in system environment.

### Hooks Configuration (All Modes)
Update `.claude/settings.local.json`:
```json
{
  "env": { "WORKER_URL": "http://10.10.100.22:37777" },
  "enabledMcpjsonServers": ["claude-mem"],
  "hooks": {
    "PostToolUse": [{ "hooks": [{ "type": "command", "command": "node .claude/hooks/save-hook.js", "statusMessage": "Capturing observation..." }] }],
    "SessionEnd": [{ "hooks": [{ "type": "command", "command": "node .claude/hooks/cleanup-hook.js", "statusMessage": "Finalizing session..." }] }],
    "SessionStart": [{ "hooks": [{ "type": "command", "command": "node .claude/hooks/context-hook.js", "statusMessage": "Loading context..." }] }]
  }
}
```

**Note:** For Docker/Local modes, change `WORKER_URL` in `env` to `http://localhost:37777`.

### Build MCP Server and Verify
```bash
cd mcp-servers/claude-mem-server && npm install && npm run build && cd ../..
# Remote: curl http://10.10.100.22:37777/api/health
# Docker: docker compose ps (healthy), curl http://localhost:37777/api/health
# Local: node scripts/worker-service.js status
```

---

## Claude Code Settings

Update `.claude/settings.json`:
```json
{
  "allowedPrompts": [
    { "tool": "Bash", "prompt": "run tests" },
    { "tool": "Bash", "prompt": "install dependencies" },
    { "tool": "Bash", "prompt": "build the project" },
    { "tool": "Bash", "prompt": "run linters" },
    { "tool": "Bash", "prompt": "git operations (non-destructive)" }
  ],
  "allow": [
    "Read(*)", "Edit(src/**/*)", "Edit(docs/**/*)",
    "Write(docs/**/*)", "Write(tests/**/*)",
    "Bash(npm:*)", "Bash(git:*)"
  ],
  "deny": [
    "Edit(.env)", "Edit(.mcp.json)",
    "Bash(rm -rf:*)", "Bash(git push --force:*)"
  ]
}
```

**For workspace repos (Path C)**: The `Edit(src/**/*)`  allow rule won't match source files in external repos.
Agents navigate to source repos using absolute paths — no additional settings needed since `Read(*)` and `Edit(*)`
without path prefix covers all absolute paths.

---

## Initial Tasks (Optional)

Ask: "Do you want to create initial tasks? (y/n)"

- **Yes (existing/workspace projects)**: Analyze codebase, suggest tasks (missing tests, undocumented endpoints, security issues)
- **Yes (new projects)**: Generic starter tasks (setup, first feature, testing)
- **No**: Create empty `docs/tasks/` directory. User runs `/task-create` later.

Creates individual files in `docs/tasks/` + auto-generates `docs/tasks/dashboard.md` dashboard.

---

## Validation Checklist

After setup, verify ALL items:
- CLAUDE.md copied to target
- PROJECT.md customized (no `[placeholder]` values remaining)
- `.claude/` folder with agents and skills copied
- `docs/` structure created with `.gitkeep` files
- `docs/templates/task-template.md` copied
- `scripts/lib/task-utils.js` available
- `.mcp.json` created from `.mcp.json.example` (servers enabled/disabled per user choice)
- `.mcp.json.example` copied to target
- `.env` file created with tokens
- VDS MCP server: `mcp-servers/mcp-vds-server/dist/index.js` exists
- Persistent Memory configured (if enabled): hooks in settings, MCP server built
- Docker container healthy (if Docker mode)
- `.gitignore` excludes secrets AND persistent memory data
- `.template-version` file created
- Git initialized (or existing repo verified clean)
- Initial tasks created as individual files (if user chose yes)
- **Path C only**: `source-repos` section in PROJECT.md has correct absolute paths, verify each path exists

---

## Post-Setup: CRITICAL Instructions

After setup completes, tell user:
1. **Exit** current Claude session
2. **Navigate** to target project: `cd "TARGET_PATH"`
3. **Start** Claude: `claude`
4. **Begin work**: `/task-create` or `/task-status TASK-001 IN_PROGRESS`

User is still in template directory - they MUST switch.

---

## Error Handling

| Error | Solution |
|-------|----------|
| Directory not found | Verify full path (Windows: `D:\path`, Linux: `/home/path`) |
| Permission denied | Windows: Run as Administrator. Linux: `chmod 755` |
| PROJECT.md exists | Create backup: `cp PROJECT.md PROJECT.md.backup` |
| MCP connection failed | Check `.env` tokens, restart Claude Code |
| VDS MCP failed | Verify `mcp-servers/mcp-vds-server/dist/index.js` exists, run `npm install` |
| VDS 401 Unauthorized | Regenerate token at `http://10.254.136.35:8090`, test with curl |
| Source repo path wrong (Path C) | Run `pwd` in source repo to get exact absolute path |

## Related Skills
- `/task-create` - Create tasks after setup
- `/task-status` - Update task status
- `/upgrade-template` - Upgrade template version later
- `/setup-memory` - Configure persistent memory separately

---

**Skill Type**: Project Initialization
**Tech Stack**: Universal (any tech stack)
