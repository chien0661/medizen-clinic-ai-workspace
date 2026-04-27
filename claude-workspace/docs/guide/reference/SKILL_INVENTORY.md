# Skill Inventory - AI Team Template

**Last Updated**: 2026-02-11
**Template Version**: 1.7.0

All 22 skills available in the AI Team Template, organized by category.

---

## Quick Stats

| Category | Count | Purpose |
|----------|-------|---------|
| Template Management | 4 | Release, upgrade, commit, build workflows |
| Task Management | 2 | Multi-file task tracking system |
| Persistent Memory | 4 | Search, export, clear, setup |
| Multi-Agent Orchestration | 6 | Workflow coordination and handoffs |
| MCP Integration | 5 | Jira and Confluence integration |
| Project Setup | 1 | Initialize new projects |

**Total Skills**: 22

> **Note**: Build/test command wrappers (`build-backend`, `build-frontend`, `test-api`) were removed in v1.6.10
> and replaced by `/auto-build` which auto-detects tech stack from PROJECT.md.

---

## 1. Template Management Skills (4)

### `/commit-push-pr`
**Purpose**: Commit, push, and create PRs with selective file staging
**Key Features**: Three modes (DEFAULT clean push, `--with-docs`, `--with-template`). Professional PRs without AI references.
```bash
/commit-push-pr TASK-001              # Clean push (partner/customer repos)
/commit-push-pr TASK-001 --with-docs  # Include documentation
```

### `/release`
**Purpose**: Automate complete template release (CHANGELOG, README, tag, push, Telegram)
**Key Features**: Tag format `X.X.X-RELEASE`. Two-step Telegram notification (preview then send). Template repo only.
```bash
/release 1.7.0 MINOR
/release 1.7.1 PATCH
```

### `/upgrade-template`
**Purpose**: Upgrade projects to latest template version from remote repository
**Key Features**: Auto-pulls template repo. Diff-based selective upgrade. Multi-platform support.
```bash
/upgrade-template --check   # Check for updates
/upgrade-template           # Upgrade to latest
```

### `/auto-build`
**Purpose**: Auto-detect tech stack from PROJECT.md and run build/test/lint commands
**Key Features**: Generates reusable `scripts/project-build.sh` on first run. Supports Maven, Gradle, npm, Python, Go, Rust, .NET.
```bash
/auto-build build    # Build project
/auto-build test     # Run all tests
/auto-build lint     # Run linter
```

---

## 2. Task Management Skills (2)

### `/task-create`
**Purpose**: Create new task files in multi-file tracking system
**Key Features**: Individual files (`docs/tasks/TASK-XXX.md`) with YAML frontmatter. Auto-regenerates dashboard.
```bash
/task-create TASK-001 "User Authentication API" High feature
/task-create BUG-001 "Login timeout" Medium bug
```

### `/task-status`
**Purpose**: Update task status, auto-assign agents, regenerate dashboard
**Key Features**: Status flow: TODO → IN_PROGRESS → IN_REVIEW → IN_TESTING → DOCUMENTING → DONE. Auto-timestamps.
```bash
/task-status TASK-001 IN_PROGRESS
/task-status TASK-001 BLOCKED "Waiting for DB approval"
```

---

## 3. Persistent Memory Skills (4)

### `/memory-search`
**Purpose**: Search past sessions with token-efficient three-layer progressive disclosure
**Key Features**: Layer 1 compact index, Layer 2 timeline, Layer 3 full details.
```bash
/memory-search "authentication JWT login"
/memory-search "database migration" --project nuxt-miniapp
```

### `/memory-export`
**Purpose**: Export memory database to timestamped markdown backup
```bash
/memory-export
/memory-export --file custom.md
```

### `/memory-clear`
**Purpose**: Clear all observations for current project (irreversible, confirmation required)
```bash
/memory-clear           # Clear current project only
/memory-clear --all     # Clear all projects (requires confirmation)
```

### `/setup-memory`
**Purpose**: Initialize persistent memory system (Docker or Local deployment)
**Key Features**: Creates database, starts worker service, configures MCP server. Supports remote team deployment.
```bash
/setup-memory
/setup-memory --docker   # Docker mode (recommended)
/setup-memory --local    # Local mode (no Docker)
```

---

## 4. Multi-Agent Orchestration Skills (6)

### `/dev-task`
**Purpose**: Spawn Code Implementation Agent for a single task
**Key Features**: Creates feature branch, implements code, writes unit tests. Transitions task TODO → IN_PROGRESS → IN_REVIEW.
```bash
/dev-task TASK-001
/dev-task TASK-001 --branch custom-branch
```

### `/review-code`
**Purpose**: Spawn Code Review Agent to review implementation
**Key Features**: Checks quality, security, performance. Generates review report. Optional SonarQube integration. Decision: APPROVED or CHANGES_REQUESTED.
```bash
/review-code TASK-001
/review-code TASK-001 --strict
```

### `/test-task`
**Purpose**: Spawn Test Agent to create and execute automated tests
**Key Features**: Creates API, integration, E2E, business rule tests. Generates test report. All tests must pass (100%) to proceed.
```bash
/test-task TASK-001
/test-task TASK-001 --api-only
```

### `/update-document`
**Purpose**: Spawn Documentation Agent to update all project documentation
**Key Features**: Updates API docs, feature docs, architecture docs. Reviews all changes. Finalizes task to DONE.
```bash
/update-document TASK-001
/update-document TASK-001 --api-only
```

### `/handoff`
**Purpose**: Create structured agent-to-agent handoff documents
**Key Features**: Summarizes completed work, git info, next steps. Stored in `docs/tasks/TASK-XXX/handoff/`.
```bash
/handoff TASK-001 "to:code-review" "Implementation complete"
/handoff TASK-001 "to:test" "Review approved"
```

### `/complete-task`
**Purpose**: Run full 4-phase multi-agent workflow (implement → review → test → document)
**Key Features**: Dispatches all 4 agents in sequence. Quality gates between phases. Loop prevention (max 2 rejections).
```bash
/complete-task TASK-001
/complete-task TASK-001 --skip-review
```

---

## 5. MCP Integration Skills (5)

### `/jira-task`
**Purpose**: Import Jira issues to local task files (Jira → docs/tasks/)
**Key Features**: Reads from Jira via MCP. Creates local task file. Hybrid approach: read from Jira, track locally.
```bash
/jira-task PROJ-456
/jira-task --project PROJ
/jira-task --jql "project = PROJ AND status = 'To Do'"
```
**Prerequisites**: Jira MCP server configured in `.mcp.json`

### `/update-jira-task`
**Purpose**: Sync local task status back to Jira (docs/tasks/ → Jira)
**Key Features**: Creates new Jira issues or updates existing linked ones. Auto-generates summary comments per phase.
```bash
/update-jira-task TASK-001
/update-jira-task --all
/update-jira-task --done
```
**Prerequisites**: Jira MCP server configured in `.mcp.json`

### `/import-confluence`
**Purpose**: Import Confluence pages to local markdown files
**Key Features**: Supports VISSoft internal (`atlassian`) and VDS partner (`atlassian-vds`). Auto-converts HTML to markdown.
```bash
/import-confluence "Page Title"
/import-confluence --page-id 123456
/import-confluence "SRS Template" --vds
```

### `/publish-confluence`
**Purpose**: Publish local documentation to Confluence pages
**Key Features**: Supports both Confluence instances. Uses VDS templates (SRS, Detail Design). Converts markdown to XHTML.
```bash
/publish-confluence TASK-001
/publish-confluence TASK-001 --vds --template srs
```

### `/publish-lesson-learn`
**Purpose**: Publish lessons learned to local backup + VISSoft Confluence
**Key Features**: Dual output: `docs/lessons-learned/LESSON-XXX.md` + Confluence page 147621793. Interactive prompts for issue details.
```bash
/publish-lesson-learn
```
**Note**: Special exception to "no MCP write" rule for team-wide knowledge sharing.

---

## 6. Project Setup Skills (1)

### `/project-setup`
**Purpose**: Initialize new project from template with interactive wizard
**Key Features**: Configures PROJECT.md, creates directory structure, sets up .gitignore and settings.
```bash
/project-setup
/project-setup --name "My Project" --tech "Spring Boot + React"
```

---

## Skill Usage Guidelines

### For New Projects
1. `/project-setup` → `/task-create` → `/dev-task` or `/complete-task` → `/commit-push-pr`

### For Partner/Customer Repos
- Use `/commit-push-pr` without flags (clean mode, no AI artifacts)
- Use `--with-docs` only when documentation is needed

### For Internal Repos
- Use `/commit-push-pr --with-template` to include all artifacts
- Use MCP skills for Jira/Confluence integration

### For Template Maintenance
- `/release` for new versions, `/upgrade-template` to check updates

---

## Finding the Right Skill

| Need to... | Skill |
|------------|-------|
| Commit code | `/commit-push-pr` |
| Create a task | `/task-create` |
| Update task status | `/task-status` |
| Start development | `/dev-task` |
| Run full workflow | `/complete-task` |
| Review code | `/review-code` |
| Run tests | `/test-task` |
| Update docs | `/update-document` |
| Search past work | `/memory-search` |
| Import from Jira | `/jira-task` |
| Publish to Confluence | `/publish-confluence` |
| Release template | `/release` |
| Upgrade template | `/upgrade-template` |

---

## Related Documentation

- [MULTI_AGENT_ORCHESTRATION.md](MULTI_AGENT_ORCHESTRATION.md) - Multi-agent workflow details
- [PERSISTENT_MEMORY_ARCHITECTURE.md](PERSISTENT_MEMORY_ARCHITECTURE.md) - Memory system architecture
- [CLAUDE.md](../CLAUDE.md) - Development guidelines
- [PROJECT.md](../PROJECT.md) - Project configuration
