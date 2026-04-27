# /commit-push-pr - Auto Commit, Push & Create PR

## Usage

```bash
# ─── Workspace Repo (no Task ID needed) ─────────────────────────────────────
/commit-push-pr                                   # Commit/push all workspace changes
/commit-push-pr --message "chore: update config"  # Custom commit message

# ─── Monorepo / Standalone (default behavior) ───────────────────────────────
/commit-push-pr TASK-001                          # Clean push, current repo
/commit-push-pr TASK-001 --target develop         # Target specific branch
/commit-push-pr TASK-001 --draft                  # Create draft PR
/commit-push-pr TASK-001 --with-docs              # Also push docs/api/, docs/features/
/commit-push-pr TASK-001 --with-template          # Push everything (internal repos only)

# ─── Microservice Workspace (multi-repo) ────────────────────────────────────
# Reads affected-repos from task frontmatter + repo paths from PROJECT.md
/commit-push-pr TASK-001                          # Auto-detects multi-repo if workspace-type: microservice
```

## Workspace Mode Detection

**At the start**, determine mode:

| Condition | Mode |
|-----------|------|
| No TASK-ID provided | **Workspace commit** — commit/push current repo, no PR |
| TASK-ID + `workspace-type: workspace` | **Multi-repo** — source repos via `source-repos:` (absolute paths) |
| TASK-ID + `workspace-type: microservice` | **Multi-repo** — source repos via `repos:` (relative paths) |
| TASK-ID + `monorepo` / not set | **Single-repo** — commit/push/PR in current repo |

`workspace` and `microservice` share the same multi-repo flow — only the config key and path format differ.

## Three Push Modes (applies to each repo)

| Mode | What's Pushed | Use Case |
|------|---------------|----------|
| **Default** (clean) | Source, tests, config, README | Partner/customer repos |
| `--with-docs` | + docs/api/, docs/architecture/, docs/features/ | When sharing documentation |
| `--with-template` | Everything (git add .) | Internal repos only |

## Automated Workflow — Workspace Repo (no TASK-ID)

Triggers when: no TASK-ID provided **OR** `workspace-type: workspace` in PROJECT.md.

```
[1] Check git status — if nothing to commit, report and exit
[2] Run git diff --stat to understand what changed
[3] Generate commit message from changed files:
    - If --message provided → use it directly
    - Otherwise → infer from diff:
      * Only .claude/ or scripts/ changed → "chore: update agent config / scripts"
      * Only docs/tasks/ changed          → "docs: update task tracking"
      * Mix of files                      → "chore: update workspace [brief summary]"
[4] git add . (workspace repo: all files are workspace files)
[5] git commit -m "<generated message>"
[6] git push origin <current-branch>
[7] Report: files committed, branch pushed, no PR created
```

> **No PR** for workspace commits — workspace changes (config, docs, tasks) go directly to master/main.
> Use `--draft-pr` flag to create a PR anyway if needed.

## Automated Workflow — Single Repo (monorepo/standalone)

```
[1] Read task from docs/tasks/TASK-XXX/task.md
[2] Verify branch matches task (feature/TASK-XXX-*)
[3] Check for uncommitted changes
[4] Generate conventional commit message (type from task type)
[5] Stage files (based on push mode)
[6] Quality gate validation (SonarQube, if configured)
    - PASS → continue | FAIL → block push | ERROR → block (fail-safe)
[7] Push to remote
[8] Generate PR description (clean by default, AI-aware with --with-template)
[9] Create PR via `gh pr create`
[10] Update task with PR URL
```

## Automated Workflow — Multi-Repo (workspace + microservice)

Shared flow for both `workspace-type: workspace` and `workspace-type: microservice`.

```
[1] Read PROJECT.md → load repo config:
    - workspace-type: workspace    → read source-repos: (absolute paths)
    - workspace-type: microservice → read repos: (relative paths)
[2] Read docs/tasks/TASK-XXX/task.md → get affected-repos list
    - If affected-repos is empty → warn and stop:
      "Run /dev-task first to populate affected-repos"
[3] For each repo in affected-repos:
    a. Resolve path:
       - workspace mode   → absolute path from source-repos.<name>.path
       - microservice mode → relative path from repos.<name>.path
    b. cd to repo directory
    c. Verify branch feature/TASK-XXX exists (create if not)
    d. Check for uncommitted changes in this repo
    e. Generate commit message specific to changes in this repo:
       - Inspect git diff to understand what changed
       - Generate: "<type>(<scope>): <what changed in this repo> (TASK-XXX)"
    f. Stage files (same mode rules as single-repo)
    g. Run SonarQube quality gate if configured for this repo's project key
    h. Push: git push origin feature/TASK-XXX
    i. Create PR: gh pr create --title "feat(TASK-XXX): <task title>" --body "<description>"
       - Branch: feature/TASK-XXX → master (or --target branch)
    j. Record PR URL
[4] Return to workspace directory
[5] Report: list of repos committed + PR URLs created
```

> **Branch naming**: `feature/TASK-XXX` — same branch name across all repos for easy cross-repo tracking.
> **Workspace repo itself**: NOT committed in this flow. Use `/commit-push-pr` (no TASK-ID) separately if needed.

## Commit Message Format

```
<type>(<scope>): <description>

<body>

Resolves: TASK-XXX
```

**CRITICAL: NEVER add Co-Authored-By tags or any author attribution.**

### Type Detection

| Task Pattern | Commit Type |
|-------------|-------------|
| TASK-* / type: feature | `feat` |
| BUG-* / type: bug | `fix` |
| type: refactor | `refactor` |
| type: documentation | `docs` |

### Scope Detection
Auto-detected from changed files (e.g., `src/*/profile/*` → `profile`).

## File Staging by Mode

### Default (Clean)
```bash
# Stage source code, tests, config, build files
git add src/ lib/ app/ test/ __tests__/ spec/
git add package.json pom.xml build.gradle tsconfig.json Cargo.toml go.mod
git add README.md CONTRIBUTING.md CHANGELOG.md
git add Dockerfile docker-compose.yml .github/workflows/ Makefile

# Explicitly unstage excluded files
git reset .claude/ .template-version .mcp.json mcp-servers/ CLAUDE.md PROJECT.md
git reset docs/ scripts/lib/ scripts/migrations/
```

### --with-docs
```bash
# Same as default, plus:
git add docs/api/ docs/architecture/ docs/features/
# Still exclude internal docs:
git reset docs/tasks/*/handoff/ docs/tasks/*/deliveries/test-reports/ docs/tasks/*/deliveries/test-cases/ docs/lessons-learned/
```

### --with-template
```bash
git add .  # Everything (internal repos only)
```

## PR Description

**Default mode** (clean): No AI references, no "Generated by AI Team Template" footer, no agent mentions.
**--with-template mode**: Includes AI workflow references, internal doc links, template footer.

### Text Sanitization (Default Mode)
| Original | Clean Version |
|----------|--------------|
| "APPROVED (by Code Review Agent)" | "Approved" |
| "ALL PASS (by Test Agent)" | "All tests passing" |
| "Generated by AI Team Template" footer | (removed) |
| Links to docs/tasks/*/handoff/, docs/tasks/*/deliveries/ | (removed) |

### PR Body Template
```markdown
## Summary
[Brief description from task]

## Changes
- [Key changes from git log --oneline]

## Quality Metrics
- **Code Review**: [status]
- **Tests**: [pass/fail with counts]
- **Coverage**: [percentage]

## Test Instructions
1. Pull branch: `git checkout [branch]`
2. Install: [project-specific command]
3. Run tests: [project-specific command]

## Checklist
- [x] Code implements all requirements
- [x] Tests passing
- [x] Code reviewed
- [x] Documentation updated
```

## Quality Gate (SonarQube) - Optional

Only activates if BOTH:
1. SonarQube MCP server enabled in `.mcp.json`
2. SONARQUBE_PROJECT_KEY configured in PROJECT.md

```
mcp__sonarqube__validate_quality_gate(projectKey, branch)
```

- **PASS**: Continue to push
- **FAIL**: Block push, show failed conditions and dashboard link
- **ERROR**: Block push (fail-safe), show troubleshooting steps

## Parameters

| Parameter | Description |
|-----------|-------------|
| `TASK-ID` | Optional. Task identifier (e.g., TASK-001). Omit for workspace commit mode. |
| `--target <branch>` | Target branch for PR (default: master) |
| `--draft` | Create draft PR |
| `--draft-pr` | Create PR even in workspace mode (normally skipped) |
| `--no-commit` | Skip commit, only push + create PR |
| `--message "msg"` | Custom commit message |
| `--with-docs` | Include project documentation |
| `--with-template` | Include ALL files (internal repos only) |

## Error Handling

| Error | Solution |
|-------|----------|
| Task not found | Verify task ID exists in docs/tasks/ |
| `affected-repos` empty | Run `/dev-task TASK-ID` first to populate it |
| Repo path not in PROJECT.md | workspace mode: add to `source-repos:` / microservice mode: add to `repos:` |
| Branch mismatch | Confirm or switch to correct branch |
| Push failed (auth) | Check SSH key or run `gh auth login` |
| Push rejected | Pull and rebase: `git pull --rebase` in the affected repo |
| PR already exists | Shows existing PR URL |
| gh CLI not found | Install from https://cli.github.com/ |

## Prerequisites

1. GitHub CLI (`gh`) installed and authenticated
2. Git remote configured in each affected repo
3. Task exists in docs/tasks/ with `affected-repos` populated (microservice mode)

## Related Skills
- `/complete-task` - Complete task before creating PR
- `/jira export` - Sync status to Jira
- `/confluence publish` - Publish docs after PR

---

**Skill Type**: Git Automation (Commit + Push + PR)
