# /test-task - Automated Testing Command

## Usage

```bash
/test-task TASK-001                      # Run full test suite for task
/test-task TASK-001 --api-only           # Only API contract tests
/test-task TASK-001 --integration-only   # Only integration tests
/test-task TASK-001 --e2e-only           # Only end-to-end tests
/test-task --all                         # Test all tasks in IN_TESTING status
```

## What This Command Does

Spawns the **Test Agent** (`.claude/agents/test.md`) in isolated context.

### Workflow

```
[1] Validate task exists and status is IN_TESTING
    ├─ If status is IN_PROGRESS → STOP immediately, do NOT spawn agent
    │   Display to user:
    │   "⛔ Task TASK-XXX is IN_PROGRESS — cannot run tests yet.
    │
    │    The task is either being implemented or has unresolved bugs.
    │    Next steps:
    │    1. Fix the code (manually or via /dev-task TASK-XXX --resume)
    │    2. Set status back to IN_TESTING: /task-status TASK-XXX IN_TESTING
    │    3. Re-run: /test-task TASK-XXX"
    └─ If status is other (TODO, IN_REVIEW, DOCUMENTING, DONE) → STOP, show appropriate message
[2] Spawn Test Agent
    ├─ Read task details, review report, API specs, implemented code
    ├─ Create API contract tests (request/response schemas, status codes, errors)
    ├─ Create integration tests (component interactions, DB operations, transactions)
    ├─ Create business rule tests (constraints, state transitions, permissions)
    ├─ Create E2E tests (full user workflows, multi-step scenarios)
    ├─ Execute all test types
    ├─ Generate test report (docs/tasks/TASK-XXX/deliveries/test-reports/test-report.md)
    └─ Update task status based on results
[3] Decision
    ├─ ALL PASS (100%) → Status → DOCUMENTING, create docs/tasks/TASK-XXX/handoff/test-to-documentation.md
    └─ ANY FAIL → Status → IN_PROGRESS, create docs/tasks/TASK-XXX/handoff/test-to-implementation.md
```

### Status Transitions

| Before | Test Results | After | Next Command |
|--------|-------------|-------|--------------|
| IN_TESTING | ALL PASS (100%) | DOCUMENTING | /update-document TASK-001 |
| IN_TESTING | ANY FAIL | IN_PROGRESS | /dev-task TASK-001 --resume |
| Other statuses | Error | - | Must be IN_TESTING first |

## Model: `sonnet`

When spawning the Test Agent via Task tool, pass `model: "sonnet"`. Override via PROJECT.md `agent-models` section.

## Test Types Created

1. **API Contract Tests** - Request schemas, response schemas, HTTP status codes, error formats, headers, auth
2. **Integration Tests** - Controller → service → repository interactions, DB CRUD, transactions, error propagation
3. **Business Rule Tests** - Business constraints, valid/invalid values, state transitions, permissions
4. **E2E Tests** - Complete user workflows, multi-step scenarios, cross-module interactions

## Test Report

Generated at `docs/tasks/TASK-XXX/deliveries/test-reports/test-report.md`:
- Summary and overall result (PASS/FAIL)
- Results table by test type (tests created, pass, fail, pass rate)
- Test coverage metrics
- List of all tests with status
- Performance metrics
- Security testing results
- Next steps

## Test Success Criteria

**ALL PASS requires**: 100% pass rate across ALL test types (unit, API, integration, business rules, E2E).

**ANY failure**: Task returns to IN_PROGRESS with handoff listing failures and expected fixes.

## Error Handling

| Error | Solution |
|-------|----------|
| Task not IN_TESTING | Run `/review-code` first to get approval |
| Test environment not ready | Start database, run migrations, retry |
| Test loop (2+ failures) | Agent warns, suggests breaking task or manual intervention |

## Related Commands

- `/review-code` - Previous step (must approve before testing)
- `/update-document` - Next step if all tests pass
- `/dev-task` - Fix failures and resume
- `/complete-task` - Full automation (includes testing)

---

**Skill Type**: Automated Testing (Agent Orchestration)
