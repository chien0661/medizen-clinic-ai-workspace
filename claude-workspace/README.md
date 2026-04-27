# AI Team Template for Multi-Agent Development

> 🤖 **Production-ready multi-agent development workflow** with automated orchestration, persistent memory, and token-efficient automation

Build software with AI agent teams using Claude Code. Features automated multi-agent workflows, persistent memory system, MCP integration, and 22 custom skills that save up to ~65,000 tokens per complete workflow.

**Version**: 1.9.7 (2026-03-11)
**Tech Stack**: Any (auto-detected from PROJECT.md)
**Automation**: Multi-agent orchestration + 20 skills + Persistent memory

---

## 🎯 What's New in 1.9.7-RELEASE (2026-03-11)

- **`/md-to-pdf` skill**: Convert markdown to styled PDF with PlantUML diagram support and embedded images — no external tools needed beyond Chrome and Node.js.
- **Test Agent status guard**: `/test-task` now validates task status before running. If status is `IN_PROGRESS`, agent stops immediately with clear guidance (fix → set IN_TESTING → re-run). Prevents accidental test runs on unfinished code.
- **Test Agent source code guardrail**: Test Agent is now explicitly blocked from modifying source code or fixing bugs — its role is to report failures only.

[See CHANGELOG.md for complete history](CHANGELOG.md)

---

## ⚡ Quick Start

### For New Projects
```bash
git clone https://bitbucket.vissoft.vn/scm/ct/template-ai-team.git my-project
cd my-project
claude code
> /project-setup    # Interactive wizard
```

### For Existing Projects
```bash
cd your-existing-project
# Copy template files, then:
claude code
> /setup-memory     # Initialize persistent memory
> /task-create TASK-001 "First task" High feature
```

### Using the Template
```bash
# Create and track tasks
/task-create TASK-001 "User authentication API" High feature
/task-status TASK-001 IN_PROGRESS

# Run multi-agent workflow
/dev-task TASK-001        # Code Implementation Agent
/review-code TASK-001     # Code Review Agent
/test-task TASK-001       # Test Agent
/update-document TASK-001 # Documentation Agent

# Commit and push (clean mode for partners)
/commit-push-pr TASK-001

# Search past work
/memory-search "authentication JWT"
```

---

## 🚀 Core Features

### 1. Multi-Agent Orchestration (6 Skills)

Specialized agents work together on development tasks:

- **`/dev-task`** - Code Implementation Agent (implements features, writes tests)
- **`/review-code`** - Code Review Agent (reviews quality, standards, security)
- **`/test-task`** - Test Agent (creates API/integration/E2E tests)
- **`/update-document`** - Documentation Agent (updates all docs)
- **`/handoff`** - Agent-to-agent handoff (passes context between agents)
- **`/complete-task`** - Finalize task (marks as DONE, archives artifacts)

**Workflow**: Implementation → Review → Testing → Documentation → Done

### 2. Persistent Memory System (4 Skills)

Never lose context across sessions with automatic memory capture:

- **Auto-capture**: Hooks save observations (Read, Write, Bash, etc.)
- **AI compression**: Claude compresses observations into learnings (10x reduction)
- **Token-efficient search**: 3-layer progressive disclosure (Search → Timeline → Details)
- **Two modes**: Local (solo) or Remote (team server with shared memory)

**Skills**: `/memory-search`, `/memory-export`, `/memory-clear`, `/setup-memory`

### 3. Multi-File Task Tracking (2 Skills)

Token-efficient task management with 55-72% reduction:

- **Individual task files**: `docs/tasks/TASK-XXX.md` (YAML frontmatter)
- **Auto-generated dashboard**: `docs/tasks/dashboard.md` regenerates automatically
- **Parallel work**: Multiple agents work simultaneously (no conflicts)
- **Scalable**: Performance constant with 100+ tasks

**Skills**: `/task-create`, `/task-status`

### 4. Template Management (3 Skills)

Professional commit workflows and template upgrades:

- **`/commit-push-pr`** - Clean commits by default (hides AI artifacts)
  - DEFAULT: Excludes `.claude/`, `docs/` (for partners/customers)
  - `--with-docs`: Include documentation
  - `--with-template`: Include everything (internal repos only)
- **`/upgrade-template`** - Auto-pull latest version from Bitbucket
- **`/release`** - Complete release automation (for template maintainers)

### 5. MCP Integration (5 Skills)

Hybrid approach - read from external systems, track locally:

- **`/jira-task`** - Import Jira issues → local tasks
- **`/update-jira-task`** - Sync local tasks → Jira (optional)
- **`/import-confluence`** - Import Confluence pages → markdown
- **`/publish-confluence`** - Publish docs → Confluence
- **`/publish-lesson-learn`** - Share lessons to VISSoft Confluence

### 6. Project Setup (1 Skill)

- **`/project-setup`** - Initialize new projects with interactive wizard

**Total**: 22 skills focused on valuable automation

[See complete skill catalog →](docs/guide/reference/SKILL_INVENTORY.md)

---

## 📊 Token Savings

| Feature | Before | After | Savings |
|---------|--------|-------|---------|
| **Task Tracking** | 5,500 tokens | 2,500 tokens | **-55%** |
| **Task Updates** | 6,000 tokens | 1,700 tokens | **-72%** |
| **Memory Search** | 25K-50K tokens | 2K-5K tokens | **-90%** |
| **Build Commands** | Verbose output | Silent mode | **~70%** |

**Complete workflow savings**: ~65,000 tokens per task (Implementation → Review → Testing → Documentation)

---

## 📁 Project Structure

```
template-ai-team/
├── .claude/
│   ├── agents/                  # Agent instructions (4 agents)
│   ├── hooks/                   # Observation capture hooks
│   ├── skills/                  # 22 custom skills
│   └── settings.json            # Permissions, hooks, env vars
│
├── docs/
│   ├── tasks/                   # Individual task files (TASK-XXX.md)
│   ├── tasks.md                 # Auto-generated dashboard
│   ├── reviews/                 # Code review reports
│   ├── test-reports/            # Test execution results
│   ├── handoffs/                # Agent-to-agent handoffs
│   ├── guides/                  # Setup and deployment guides
│   └── SKILL_INVENTORY.md       # Complete skill catalog
│
├── mcp-servers/
│   └── claude-mem-server/       # Persistent memory MCP server
│
├── scripts/
│   ├── lib/                     # Task tracking utilities
│   ├── worker-service.js        # Memory worker service
│   └── send-release-notification.js  # Telegram notifications
│
├── deployment/                  # Docker deployment configs
├── CLAUDE.md                    # Development guidelines (universal)
├── PROJECT.md                   # Project-specific details (customize!)
├── CHANGELOG.md                 # Version history
└── README.md                    # This file
```

---

## 🛠️ Technology Stack

**Core Components**:
- **Claude Code**: CLI tool for AI-powered development
- **Claude Sonnet 4.5**: Multi-agent orchestration & memory compression
- **SQLite (sql.js)**: Persistent memory database
- **MCP (Model Context Protocol)**: External system integration
- **Node.js**: Scripts, hooks, worker services

**Optional Integrations** (via MCP):
- Jira (task import/sync)
- Confluence (docs import/publish)
- SonarQube (code quality gates)
- MariaDB (database operations)
- Figma (design specs)

**Customizable Stack** (in PROJECT.md):
- Language: Java, TypeScript, Python, Go, Rust, etc.
- Framework: Spring Boot, Express, FastAPI, Django, etc.
- Database: PostgreSQL, MongoDB, MySQL, Redis, etc.

---

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| **[CLAUDE.md](CLAUDE.md)** | Universal development guidelines |
| **[PROJECT.md](PROJECT.md)** | Project-specific configuration (customize!) |
| **[CHANGELOG.md](CHANGELOG.md)** | Version history and release notes |
| **[SKILL_INVENTORY.md](docs/guide/reference/SKILL_INVENTORY.md)** | Complete skill catalog (22 skills) |
| **[MULTI_AGENT_ORCHESTRATION.md](docs/guide/workflow/MULTI_AGENT_ORCHESTRATION.md)** | Multi-agent workflow details |
| **[PERSISTENT_MEMORY_ARCHITECTURE.md](docs/guide/reference/PERSISTENT_MEMORY_ARCHITECTURE.md)** | Memory system architecture |

**Guides**:
- [Persistent Memory User Guide](docs/guide/reference/using-persistent-memory.md)
- [Remote Memory Deployment](docs/guide/setup/remote-memory-deployment.md) (team server)
- [Upgrade to Persistent Memory](docs/guide/setup/UPGRADE-TO-PERSISTENT-MEMORY.md) (existing projects)

---

## 🎯 Use Cases

### For Partner/Customer Projects
```bash
# Clean commits (no AI artifacts)
/commit-push-pr TASK-001

# Professional PRs (no "Generated by AI" footer)
/commit-push-pr TASK-001 --with-docs  # Include documentation only
```

### For Internal Projects
```bash
# Full tracking with AI artifacts
/commit-push-pr TASK-001 --with-template

# Multi-agent workflow
/dev-task TASK-001
/review-code TASK-001
/test-task TASK-001
/update-document TASK-001
```

### For Team Collaboration
```bash
# Deploy remote memory server (one-time, 20 minutes)
# See: docs/guides/remote-memory-deployment.md

# Each team member (5 minutes)
# Update .mcp.json and .claude/settings.local.json

# Benefits:
# - Shared memory across team
# - 50-90% cost savings (one API key)
# - Multi-machine access
```

---

## 🔧 Configuration

### Essential Files

**`.claude/settings.json`** - Claude Code settings
- Permissions (allowed/denied commands)
- Hooks (observation capture, session management)
- Environment variables (WORKER_URL, MEMORY_API_KEY)

**`PROJECT.md`** - Project-specific configuration
- Technology stack, architecture, build commands
- Database, auth, messaging systems
- Custom patterns and standards

**`.mcp.json`** - MCP server configuration
- Persistent memory server
- Jira, Confluence, SonarQube (optional)

### Quick Configuration Check
```bash
# Verify setup
/setup-memory --check

# Test memory search
/memory-search "test query"

# View all skills
ls .claude/skills/
```

---

## 📈 Workflow Example

**Complete task workflow with multi-agent orchestration:**

```bash
# 1. Create task
/task-create TASK-001 "User authentication API" High feature

# 2. Development (Code Implementation Agent)
/dev-task TASK-001
# → Implements feature
# → Writes unit tests
# → Creates commits
# → Updates status to IN_REVIEW

# 3. Code Review (Code Review Agent)
/review-code TASK-001
# → Reviews code quality
# → Checks security, performance
# → Generates review report
# → Updates status to IN_TESTING (if approved)

# 4. Testing (Test Agent)
/test-task TASK-001
# → Creates API/integration/E2E tests
# → Runs full test suite
# → Generates test report
# → Updates status to DOCUMENTING (if 100% pass)

# 5. Documentation (Documentation Agent)
/update-document TASK-001
# → Updates API docs
# → Updates feature docs
# → Finalizes changes
# → Updates status to DONE

# 6. Commit and push (clean mode)
/commit-push-pr TASK-001

# 7. Search memory for future reference
/memory-search "authentication implementation"
```

**Total time**: Automated workflow, ~65,000 tokens saved

---

## 🚢 Deployment Modes

### Local Mode (Default)
- Database: `~/.claude-mem/memory.db`
- Use case: Solo developers, personal projects
- Setup: Zero configuration (works out of the box)

### Remote Mode (Team)
- Database: Centralized server (e.g., `http://10.10.100.22:37777`)
- Use case: Teams, multiple machines, shared context
- Setup: 20 minutes server deployment + 5 minutes per team member
- Benefits: Shared memory, 50-90% cost savings, multi-machine access

[See deployment guide →](docs/guide/setup/remote-memory-deployment.md)

---

## 🤝 Contributing

This is an internal VISSoft template. For questions or issues:
- Check [CHANGELOG.md](CHANGELOG.md) for recent changes
- Review [docs/guide/reference/SKILL_INVENTORY.md](docs/guide/reference/SKILL_INVENTORY.md) for skill reference
- See troubleshooting in [CLAUDE.md](CLAUDE.md)

---

## 📜 License

Internal VISSoft use only.

---

## 🔗 Links

- **Bitbucket**: https://bitbucket.vissoft.vn/scm/ct/template-ai-team.git
- **CHANGELOG**: [CHANGELOG.md](CHANGELOG.md)
- **Skill Catalog**: [docs/guide/reference/SKILL_INVENTORY.md](docs/guide/reference/SKILL_INVENTORY.md)
- **VISSoft Confluence**: Lessons learned (page 147621793)

---

**Built with ❤️ by VISSoft Development Team**

**Last Updated**: 2026-02-10 | **Version**: 1.6.10-RELEASE
