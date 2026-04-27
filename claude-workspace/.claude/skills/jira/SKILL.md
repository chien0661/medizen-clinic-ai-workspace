# Skill: jira

## Description
Bidirectional Jira sync: **import** issues from Jira into local task files, or **export** local tasks back to Jira.

## Invocation
```bash
# IMPORT: Jira → docs/tasks/
/jira import PROJ-456                          # Import single issue by key
/jira import 456                               # Uses JIRA_PROJECT_KEY env var
/jira import --project PROJ                    # Import all issues from project
/jira import PROJ-456 --task-id TASK-001       # Custom task ID
/jira import --jql "project = PROJ AND status = 'To Do'"  # JQL query

# EXPORT: docs/tasks/ → Jira
/jira export TASK-001                          # Create or update single task
/jira export TASK-001 --force                  # Force update even if status unchanged
/jira export --all                             # Sync all tasks
/jira export --done                            # Sync only DONE tasks
/jira export --create-only                     # Only create new issues (skip existing)
/jira export --update-only                     # Only update existing issues (skip new)
```

## Prerequisites

1. Jira MCP server configured in `.mcp.json`
2. Environment variables: `JIRA_URL`, `JIRA_EMAIL`, `JIRA_API_TOKEN`
3. Optional: `JIRA_PROJECT_KEY` for shorthand

---

## IMPORT Mode (`/jira import`)

Import Jira issues as local task files. **Read-only from Jira.**

### Step 1: Read from Jira (MCP)
Call `mcp__atlassian__jira_get_issue` or `mcp__atlassian__jira_search_issues` to fetch:
- Issue key, summary, description, type, priority, status
- Assignee, reporter, labels, created date

### Step 2: Generate Task ID
- Read `docs/tasks/` directory for highest existing TASK-XXX number
- Increment by 1 (or use custom `--task-id`)
- Map issue type: Story/Task → `TASK-XXX`, Bug → `BUG-XXX`

### Step 3: Create Task File
Create `docs/tasks/TASK-XXX.md` with YAML frontmatter:

```yaml
---
id: TASK-XXX
type: feature
title: "[Jira Summary]"
status: TODO
priority: High
assigned: Unassigned
created: YYYY-MM-DD
updated: YYYY-MM-DD
branch: "feature/task-xxx-[slugified-title]"
jira_key: "PROJ-456"
tags: [from-jira-labels]
---
```

Body includes:
- Title with Jira reference
- Jira link: `**Jira:** [PROJ-456](https://jira.url/browse/PROJ-456)`
- Description (converted from Jira formatting to markdown)
- Requirements and acceptance criteria (extracted from description)
- Progress checklist (Implementation, Review, Testing, Documentation)
- Original Jira metadata (status, reporter, labels)
- Warning: "This task is tracked locally, NOT in Jira"

### Step 4: Regenerate Dashboard
Update `docs/tasks/dashboard.md` via `regenerateIndexFile()`

### Jira → Markdown Formatting
Convert Jira markup to markdown:
- `*bold*` → `**bold**`
- `{code}...{code}` → triple backticks
- `h1.` → `#`
- Jira bullets → markdown bullets

### Import Error Handling
- **Issue not found**: Verify issue key exists in Jira
- **MCP not available**: Check `.mcp.json` config, verify env vars, restart Claude Code
- **Missing project key**: Set `JIRA_PROJECT_KEY` env var or use full key (`PROJ-456`)
- **Duplicate import**: Check if issue already imported (`Grep "PROJ-456" docs/tasks/`)

---

## EXPORT Mode (`/jira export`)

Publish local tasks to Jira: **create** new issues or **update** existing linked issues.

### Create vs Update Decision

```
Read docs/tasks/TASK-XXX.md frontmatter
  │
  ├─ Has jira_key? → UPDATE: Update existing issue status + add comment
  │
  └─ No jira_key? → CREATE: Create new Jira issue, save key back to frontmatter
```

### CREATE Mode (No jira_key)

1. Read task file frontmatter and body
2. Get project key from `JIRA_PROJECT_KEY` env var (or ask user)
3. Map fields:

| Local Field | Jira Field |
|-------------|------------|
| title | Summary |
| type: feature | Issue Type: Story |
| type: bug | Issue Type: Bug |
| type: task/debt | Issue Type: Task |
| priority | Priority (direct map) |
| Description section | Description (markdown → Jira format) |
| tags | Labels + "ai-team-template" |

4. Call `mcp__atlassian__jira_create_issue` (or `mcp__atlassian-vds__jira_create_issue`)
5. Save returned `jira_key` back to task frontmatter
6. Regenerate dashboard (`docs/tasks/dashboard.md`)

### UPDATE Mode (Has jira_key)

1. Read task file for current status and `jira_key`
2. Call Jira MCP to get current issue status
3. If status changed → update via `mcp__atlassian__jira_update_issue`
4. Add summary comment based on current phase

### Status Mapping

| Local Status | Jira Status |
|-------------|-------------|
| `TODO` | To Do |
| `IN_PROGRESS` | In Progress |
| `IN_REVIEW` | In Review |
| `IN_TESTING` | In Testing |
| `DOCUMENTING` | In Testing (keep) |
| `DONE` | Done |
| `BLOCKED` | Blocked |

Custom mappings via environment variables:
```bash
export JIRA_STATUS_TODO="Backlog"
export JIRA_STATUS_IN_PROGRESS="In Development"
export JIRA_STATUS_DONE="Closed"
```

### Comment Generation
Add a summary comment extracting info from:
- `docs/tasks/TASK-XXX/task.md` - status, priority, branch
- `docs/tasks/TASK-XXX/handoff/review-report.md` - review decision (`Grep "Decision:"`)
- `docs/tasks/TASK-XXX/deliveries/test-reports/test-report.md` - test results (`Grep "Test Results:"`)
- `git log --oneline feature/task-xxx-*` - commit count

Comment format per status:
- **DONE**: Full summary (status flow, test results, deliverables, artifacts)
- **IN_REVIEW**: Implementation summary (files changed, unit tests, branch)
- **IN_TESTING**: Review result + testing plan
- **BLOCKED**: Blocker reason and next steps

Footer: `Generated by: Claude AI Team Template`

### Export Error Handling
- **Issue not found**: Verify `jira_key` in task frontmatter
- **Permission denied**: Check token has write permissions
- **Invalid transition**: Update to intermediate states first, or use `--force` for comment-only
- **No project key (CREATE mode)**: Set `JIRA_PROJECT_KEY` env var or specify when prompted

---

## Token Optimization
- Use `Grep` to extract key metrics from reports (not full file reads)
- Single MCP call per task (create or update + comment)
- Read only frontmatter + summary sections from task files

---

## Related Skills
- `/confluence` - Import/publish Confluence documentation
- `/task-status` - Update local task status
- `/complete-task` - Complete tasks locally

---

**Skill Type**: Jira Integration (Bidirectional)
**MCP Servers**: `atlassian`, `atlassian-vds`
**Directions**: Jira → docs/tasks/ (import) | docs/tasks/ → Jira (export)
