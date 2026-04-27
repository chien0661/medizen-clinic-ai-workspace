# /dev-task - Code Implementation Command

## Usage

```bash
/dev-task TASK-001                    # Implement specific task
/dev-task TASK-001 --resume           # Resume incomplete implementation
/dev-task TASK-001 --branch custom    # Use custom branch name
/dev-task TASK-001 --skip-tests       # Skip unit test creation (not recommended)
```

## What This Command Does

Spawns the **Code Implementation Agent** (`.claude/agents/code-implementation.md`) in isolated context.

### Workflow

```
[1] Validate task exists (status must be TODO or IN_PROGRESS)
[2] Spawn Code Implementation Agent
    ├─ Read task requirements from docs/tasks/TASK-XXX/task.md and docs/tasks/TASK-XXX/refs/
    ├─ Create feature branch (feature/task-{id}-{slug})
    ├─ Implement the feature/fix following PROJECT.md patterns
    ├─ Write unit tests (coverage ≥ 80%)
    ├─ Run tests, linter, build to verify
    ├─ Commit with conventional commit message
    ├─ Update task status: TODO → IN_PROGRESS → IN_REVIEW
    └─ Create handoff document (docs/tasks/TASK-XXX/handoff/implementation-to-review.md)
[END] Ready for /review-code
```

### Status Transitions

| Before | After Success | After Failure |
|--------|---------------|---------------|
| TODO | IN_REVIEW | IN_PROGRESS (with error details) |
| IN_PROGRESS | IN_REVIEW | IN_PROGRESS (with error details) |
| Other statuses | Error | Must be TODO or IN_PROGRESS |

## Model: `sonnet`

When spawning the Code Implementation Agent via Task tool, pass `model: "sonnet"`. Override via PROJECT.md `agent-models` section.

## Agent Steps

1. **Read Requirements** - Task details, specs, Jira link context
2. **Setup Environment** - Create feature branch, verify dependencies, run baseline tests
3. **Implement Feature/Fix** - Follow architecture patterns, code style, error handling, SOLID
4. **Write Unit Tests** - ≥80% coverage, positive/negative/edge cases, AAA pattern
5. **Verify** - Tests pass (100%), linter clean, build succeeds
6. **Commit** - Conventional commit: `feat(module): description` with `Resolves: TASK-XXX`
7. **Update Status** → IN_REVIEW with implementation notes
8. **Create Handoff** - Summary, files changed, testing instructions, areas for review attention

## Parameters

| Parameter | Description |
|-----------|-------------|
| `TASK-ID` | Task identifier (TASK-001, BUG-001) |
| `--resume` | Resume incomplete implementation (keeps existing branch) |
| `--branch name` | Override default branch naming |
| `--skip-tests` | Skip unit test creation (not recommended) |

## vs /complete-task

| Feature | /dev-task | /complete-task |
|---------|-----------|----------------|
| Phases | Implementation only | All 4 (Code → Review → Test → Docs) |
| Control | Granular, stop after each phase | Fully automated |
| Status | TODO → IN_REVIEW | TODO → DONE |
| Use case | Manual workflow, exploratory work | Hands-off automation |

## Error Handling

| Error | Solution |
|-------|----------|
| Task not found | Verify task ID in docs/tasks/ or import from Jira |
| Task already in review | Use `/review-code` or `--resume` for rework |
| Unit tests failing | Agent retries up to 3 times, then marks IN_PROGRESS with error notes |
| Build failure | Agent fixes syntax/type errors; if unfixable, adds blocker to task notes |
| Missing dependencies | Documents blocker, keeps IN_PROGRESS, use `--resume` when resolved |

## Related Commands

- `/complete-task` - Full automation (includes /dev-task + review + test + docs)
- `/review-code` - Next step after /dev-task
- `/jira import` - Import tasks before implementation

---

**Skill Type**: Code Implementation (Agent Orchestration)
