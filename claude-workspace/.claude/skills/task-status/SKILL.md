# /task-status - Update Task Status

## Usage

```bash
/task-status TASK-001 IN_PROGRESS
/task-status TASK-001 BLOCKED "Waiting for database migration approval"
/task-status TASK-001,TASK-002,TASK-003 TODO    # Bulk update
```

## Purpose

Update task status in individual task files (`docs/tasks/TASK-XXX.md`) and auto-regenerate the dashboard (`docs/tasks/dashboard.md`).

## Available Statuses

| Status | Description | Used By | Next Status |
|--------|-------------|---------|-------------|
| `TODO` | Ready to start | Project/Agent Manager | IN_PROGRESS |
| `IN_PROGRESS` | Implementation active | Code Implementation Agent | IN_REVIEW |
| `IN_REVIEW` | Code review in progress | Code Review Agent | IN_TESTING or IN_PROGRESS |
| `IN_TESTING` | Tests running | Test Agent | DOCUMENTING or IN_PROGRESS |
| `DOCUMENTING` | Updating documentation | Documentation Agent | DONE |
| `DONE` | Complete (terminal) | Documentation Agent | - |
| `BLOCKED` | Cannot proceed | Any agent | Previous status |

## What Happens on Status Update

1. Validates task file exists and status transition is valid
2. Updates YAML frontmatter: `status`, `assigned`, `updated` date
3. Adds timestamp to body (e.g., "Started: 2026-01-23 10:30:00")
4. Auto-assigns agent based on new status
5. Regenerates `docs/tasks/dashboard.md` dashboard index

### Auto-Assignment

| Status | Auto-Assigned To |
|--------|------------------|
| TODO | Unassigned |
| IN_PROGRESS | Code Implementation Agent |
| IN_REVIEW | Code Review Agent |
| IN_TESTING | Test Agent |
| DOCUMENTING | Documentation Agent |
| DONE | None |
| BLOCKED | Retains current assignment |

### Auto-Timestamps

- IN_PROGRESS → "Started" timestamp
- IN_REVIEW → "Implementation Completed" timestamp
- IN_TESTING → "Review Completed" timestamp
- DOCUMENTING → "Testing Completed" timestamp
- DONE → "Documentation Completed" timestamp

## State Flow

```
TODO → IN_PROGRESS → IN_REVIEW → IN_TESTING → DOCUMENTING → DONE

Rejection paths:
IN_REVIEW → IN_PROGRESS (changes requested)
IN_TESTING → IN_PROGRESS (tests failed)
Any → BLOCKED → Previous status
```

## Error Handling

| Error | Solution |
|-------|----------|
| Task file not found | Verify file exists or create with `/task-create` |
| Invalid status transition | Follow correct workflow sequence |
| Invalid frontmatter | Ensure valid YAML between `---` markers |

## Related Skills

- `/auto-build` - Verify builds pass before status update
- `/task-create` - Create task files

---

**Skill Type**: Workflow Coordination
