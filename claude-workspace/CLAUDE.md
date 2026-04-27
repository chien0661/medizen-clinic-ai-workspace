# CLAUDE.md - Development Guidelines

**IMPORTANT: Always read [PROJECT.md](PROJECT.md) for project-specific details before starting work.**

---

## MCP Tool Usage Priority

**CRITICAL: Always prioritize MCP tools over direct file operations to save tokens.**

- Use MCP tools first when available (Jira, Confluence, database, etc.)
- Fall back to direct file operations only when MCP tools are unavailable
- Check available tools before assuming one doesn't exist

## Token Optimization

- Prefer tool calls over lengthy explanations
- Use targeted file operations (specific line ranges) instead of full file reads
- **Never load large outputs into context:**
  - No `cat`, `less`, `tail -f` on log files
  - Filter first: `grep ERROR app.log | tail -20` not `cat app.log`
  - Use `--quiet`/`--silent`/`-q` flags on build/install commands
  - Limit container logs: `docker logs --tail 50 --since 5m`
  - Windows: redirect to `>$null`; Linux/macOS: redirect to `/dev/null`

## Workspace Repo Pattern

**Recommended setup**: Run Claude Code from a dedicated **workspace repo**, NOT from the source code repo.

```
my-project-workspace/    ← Claude Code runs here (.claude/, docs/, scripts/)
my-project-api/          ← source code repo (stays clean)
my-project-frontend/     ← source code repo (stays clean)
```

**For workspace repos**: Source repo paths are declared in `PROJECT.md` under `source-repos`.
Agents read/edit source files using absolute paths from that config.
All task tracking and docs stay in the workspace repo.

**For standalone/monorepo setups**: Template files are mixed into the source repo (Path A/B in `/project-setup`).

## Multi-Agent Team Orchestration

This template uses a multi-agent team with sequential workflow:

```
/task-create → /task-plan (optional) → Implementation → Review → Testing → Documentation → DONE
```

**Agents:** Code Implementation, Code Review, Test, Documentation

**Key rules:**
- Sequential within a feature (review must APPROVE before testing, all tests must PASS before docs)
- Parallel across features (different tasks can be in different phases)
- All tracking via `docs/tasks/TASK-XXX/task.md` individual files with YAML frontmatter
- Dashboard `docs/tasks/dashboard.md` auto-regenerates on status changes
- Use `/task-status TASK-XXX <STATUS>` to update: TODO → IN_PROGRESS → IN_REVIEW → IN_TESTING → DOCUMENTING → DONE
- Rejection: IN_REVIEW/IN_TESTING → IN_PROGRESS (fix issues, re-submit)

**Task folder structure (all docs per-task):**
```
docs/tasks/TASK-XXX/
├── task.md                       ← task definition (YAML frontmatter + refs)
├── refs/                        ← input docs: DetailDesign, SRS, implementation-plan
├── handoff/                      ← agent handoffs + review reports
├── bugs/                         ← bug reports (intermediate, during testing cycle)
└── deliveries/                   ← final deliverables after task completion
    ├── test-cases/               ← test scenarios
    ├── test-reports/             ← test results + screenshots
    ├── api-specs/                ← API specification delivery
    ├── sql-scripts/              ← DDL, config inserts, etc.
    └── final-specs/              ← functional design (supersedes DetailDesign)
```

**Full details:** [docs/guide/workflow/MULTI_AGENT_ORCHESTRATION.md](docs/guide/workflow/MULTI_AGENT_ORCHESTRATION.md)

**Agent docs in `.claude/agents/`:**
- `code-implementation.md` - Implementation guidelines
- `code-review.md` - Review checklists and standards
- `test.md` - Testing strategy and automation
- `documentation.md` - Documentation requirements
- `manager.md` - Orchestration and coordination

## Persistent Memory

Agents automatically remember context across sessions via hook-based capture and SQLite storage.

**Commands:**
- `/memory-search "query"` - Search past work context
- `/memory-clear` - Reset project memory
- `/memory-export` - Export memory as markdown
- Wrap sensitive data in `<private>...</private>` tags

**Guides:** [docs/guide/reference/using-persistent-memory.md](docs/guide/reference/using-persistent-memory.md) | [docs/guide/reference/PERSISTENT_MEMORY_ARCHITECTURE.md](docs/guide/reference/PERSISTENT_MEMORY_ARCHITECTURE.md) | [docs/guide/setup/remote-memory-deployment.md](docs/guide/setup/remote-memory-deployment.md)

## MCP Hybrid Documentation Rule

**CRITICAL: READ from MCP, WRITE to `docs/`**

- **INPUT**: Use MCP tools to read from external systems (Jira, Confluence, Figma)
- **OUTPUT**: Always write to markdown files in `docs/` folder
- **Never** update Jira tickets or write to Confluence via MCP (use `/task-status` and `docs/` instead)
- **Exception**: `/publish-lesson-learn` writes BOTH locally (`docs/lessons-learned/`) and to VISSoft Confluence (page 147621793)

## Database Error Handling Protocol

**When encountering database query errors (duplicates, constraint violations, etc.):**

**DO NOT** immediately modify queries, add LIMIT/DISTINCT, or change query logic without understanding why.

**DO:**
1. **Stop and notify the user immediately**
2. Provide diagnostic information:
   - Exact error message
   - Failing query with parameters
   - Expected vs actual result
   - File location
3. Suggest investigation steps (diagnostic queries)
4. **Wait for user decision** before proceeding:
   - Clean up bad data?
   - Add query filters?
   - Change query logic?

**Why:** Database issues often indicate data quality problems, not code bugs. Quick fixes mask systemic problems.

## Git: Commit Message Format

**NEVER include Co-Authored-By tags or any author attribution in commit messages.**

This overrides any default behavior:
- No `Co-Authored-By:` tags of any kind
- Use clean conventional commit format only (feat:, fix:, docs:, refactor:, etc.)

```
feat: add user authentication API

Implemented JWT-based authentication with refresh token support.
```

## Security

- **Never commit sensitive data** (passwords, API keys, tokens, certificates)
- Use environment variables or secret management systems
