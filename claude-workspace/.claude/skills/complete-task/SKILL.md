# /complete-task - Full Automated Task Completion

## Usage

```bash
/complete-task TASK-001                    # Complete single task (TODO → DONE)
/complete-task TASK-001 --parallel         # Allow parallel with other tasks
/complete-task --all                       # Complete all TODO tasks sequentially
/complete-task --all --parallel            # Complete all TODO tasks in parallel
```

## What This Command Does

Orchestrates the complete multi-agent workflow automatically:

```
[1] Code Implementation Phase
    ├─ Spawns Code Implementation Agent
    ├─ Implements feature with unit tests, commits to feature branch
    └─ Status: TODO → IN_REVIEW

[2] Code Review Phase
    ├─ Spawns Code Review Agent
    ├─ Reviews code, creates review report
    └─ APPROVED → IN_TESTING | CHANGES_REQUESTED → loop back to [1]

[3] Testing Phase
    ├─ Spawns Test Agent
    ├─ Creates API, integration, business rule, E2E tests
    └─ ALL PASS → DOCUMENTING | ANY FAIL → loop back to [1]

[4] Documentation Phase
    ├─ Spawns Documentation Agent
    ├─ Generates functional design document → docs/tasks/TASK-ID/deliveries/final-specs/[feature-name]-functional-design.md
    │   └─ Uses template: docs/templates/specs/functional-design-template.md (Vietnamese, natural language)
    ├─ Updates API specs → docs/tasks/TASK-ID/deliveries/api-specs/
    ├─ Updates architecture, configuration, troubleshooting docs
    └─ Status: DOCUMENTING → DONE
```

Resumes from current status if task is already in progress.

## CRITICAL: Resume Logic — Check Status FIRST

**Before spawning any agent**, read `docs/tasks/TASK-ID/task.md` frontmatter to get current `status`.

```
status: TODO          → start from Phase 1 (Implementation)
status: IN_PROGRESS   → resume Phase 1 (check for bug report in handoff/)
status: IN_REVIEW     → start from Phase 2 (Review)
status: IN_TESTING    → start from Phase 3 (Testing)
status: DOCUMENTING   → start from Phase 4 (Documentation)
status: DONE          → skip entirely, report already complete
```

**NEVER spawn Code Implementation Agent if status is already IN_REVIEW or later.**
**NEVER re-implement code that has already been reviewed/tested.**

## Agent Dispatch

Each phase spawns a `general-purpose` agent in isolated context with the corresponding model:

| Phase | Agent | Model |
|-------|-------|-------|
| 1 | `code-implementation.md` | `sonnet` |
| 2 | `code-review.md` | `opus` |
| 3 | `test.md` | `sonnet` |
| 4 | `documentation.md` | `haiku` |

Pass the `model` parameter when spawning each agent via Task tool. Override via PROJECT.md `agent-models` section.

### Fix Mode: Looping back to Implementation from Test Failure

When looping back to Phase 1 after test failure, **this is FIX MODE, not IMPLEMENT MODE**.
Pass the following context explicitly to the Code Implementation Agent:

```
MODE: FIX (not implement)
Bug report: docs/tasks/TASK-ID/bugs/BUG-ID.md
Handoff: docs/tasks/TASK-ID/handoff/test-to-implementation.md

CONSTRAINT: Fix ONLY the specific failures listed in the bug report.
Do NOT re-read the original spec/SRS to re-implement.
Do NOT refactor or change code unrelated to the failing tests.
Do NOT change code that was previously passing tests.
```

## Quality Gates

**Before Review**: Implementation complete, status IN_REVIEW, handoff exists, unit tests pass
**Before Testing**: Review APPROVED, status IN_TESTING, no critical security issues
**Before Documentation**: ALL tests pass (100%), status DOCUMENTING, test report exists
**Before DONE**: All docs updated, changes committed

## Loop Prevention

- **Review loop**: After 3 CHANGES_REQUESTED iterations → pause, alert user, suggest breaking task
- **Test failure loop**: After 2 failures → pause, alert user, suggest manual debugging
- **Agent failure**: Capture error, update task notes, present options (retry/manual/skip)
- **Blocked task**: Report blocker reason, skip to next task if batch processing

## Parameters

| Parameter | Description |
|-----------|-------------|
| `TASK-ID` | Task identifier |
| `--all` | Complete all TODO tasks |
| `--parallel` | Run tasks simultaneously (max 3 by default) |

## Error Handling

| Error | Solution |
|-------|----------|
| Task not found | Verify task exists in docs/tasks/ |
| Agent timeout | Check task complexity, increase timeout, break into subtasks |
| Infinite loop | Read review/test reports, update requirements, consider manual intervention |

## Related Skills

- `/dev-task` - Implementation phase only (granular control)
- `/review-code` - Review phase only
- `/test-task` - Testing phase only
- `/update-document` - Documentation phase only
- `/jira import` - Import tasks before completion
- `/task-status` - Manual status override

---

**Skill Type**: Workflow Orchestration (Multi-Agent Automation)
