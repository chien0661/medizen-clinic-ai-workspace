# /task-create - Create New Task

## Usage

```bash
/task-create TASK-001 "Implement User Profile API" High feature
/task-create BUG-042 "Fix login timeout issue" High bug
/task-create DEBT-015 "Refactor authentication logic" Medium debt
```

## Parameters

| Parameter | Format | Valid Values |
|-----------|--------|-------------|
| `TASK-ID` | `TASK-XXX`, `BUG-XXX`, `DEBT-XXX` | 3-digit number, must be unique |
| `TITLE` | Quoted string | 10-100 characters recommended |
| `PRIORITY` | Case-sensitive | `High`, `Medium`, `Low` |
| `TYPE` | Lowercase | `feature`, `bug`, `debt` |

## What Happens

1. Validates task ID format, priority, type
2. Checks for duplicate task IDs
3. Creates `docs/tasks/` directory if needed
4. Reads template from `docs/templates/task-template.md`
5. Replaces placeholders (ID, title, priority, type, dates)
6. Creates task folder `docs/tasks/TASK-XXX/` with full subdir structure
7. Writes task file: `docs/tasks/TASK-XXX/task.md`
8. Regenerates `docs/tasks/dashboard.md` dashboard index

## Created File Structure

```
docs/tasks/TASK-XXX/
├── task.md                        ← task definition (YAML frontmatter + body)
├── refs/                          ← input docs: DetailDesign, SRS, implementation-plan
├── handoff/                       ← agent handoff files + review reports
├── bugs/                          ← bug reports (during testing cycle)
└── deliveries/
    ├── test-cases/                ← test scenarios
    ├── test-reports/              ← test results + screenshots
    ├── api-specs/                 ← API specification delivery
    ├── sql-scripts/               ← DDL, config inserts, etc.
    └── final-specs/               ← functional design (supersedes DetailDesign)
```

`task.md` has YAML frontmatter (id, type, title, status: TODO, priority, assigned: Unassigned, dates, branch, tags, refs) followed by sections: Description, Requirements, Acceptance Criteria, Progress Checklist, Related Files, Timestamps, Notes, Blockers.

## After Creating

1. Edit task file to fill in Description, Requirements, Acceptance Criteria
2. Start work: `/task-status TASK-001 IN_PROGRESS`

## Error Handling

| Error | Solution |
|-------|----------|
| Task file exists | Choose a different ID; check `docs/tasks/` |
| Invalid ID format | Use `PREFIX-NNN` format (e.g., TASK-001) |
| Invalid priority | Use exact: `High`, `Medium`, `Low` |
| Invalid type | Use exact: `feature`, `bug`, `debt` |
| Template not found | Verify `docs/templates/task-template.md` exists |

## Related Skills

- `/task-status` - Update task status after creation
- `/jira import` - Import tasks from Jira instead
- `/project-setup` - Creates initial tasks during setup

---

**Skill Type**: Task Management
