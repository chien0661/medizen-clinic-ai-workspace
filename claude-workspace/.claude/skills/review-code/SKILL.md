# /review-code - Code Review Command

## Usage

```bash
/review-code TASK-001                    # Review code for specific task
/review-code TASK-001 --strict           # Zero tolerance for any issues
/review-code TASK-001 --quick            # Critical issues only (for hotfixes)
/review-code --all                       # Review all tasks in IN_REVIEW status
```

## What This Command Does

Spawns the **Code Review Agent** (`.claude/agents/code-review.md`) in isolated context.

### Workflow

```
[1] Validate task exists and status is IN_REVIEW
[2] Spawn Code Review Agent
    ├─ Read task details from docs/tasks/TASK-XXX/task.md
    ├─ Read handoff document (docs/tasks/TASK-XXX/handoff/implementation-to-review.md)
    ├─ Get git diff for changes
    ├─ SonarQube analysis (OPTIONAL - only if configured in PROJECT.md)
    ├─ Manual code review (quality, functionality, security, performance, tests, architecture)
    └─ Generate review report (docs/tasks/TASK-XXX/handoff/review-report.md)
[3] Review Decision
    ├─ APPROVED → Status → IN_TESTING, create handoff to Test Agent
    └─ CHANGES_REQUESTED → Status → IN_PROGRESS, create handoff to Dev Agent
```

### Status Transitions

| Before | Decision | After | Next Command |
|--------|----------|-------|--------------|
| IN_REVIEW | APPROVED | IN_TESTING | /test-task TASK-001 |
| IN_REVIEW | CHANGES_REQUESTED | IN_PROGRESS | /dev-task TASK-001 --resume |
| Other statuses | Error | - | Must be IN_REVIEW first |

## Model: `opus`

When spawning the Code Review Agent via Task tool, pass `model: "opus"`. Override via PROJECT.md `agent-models` section.

## Agent Review Steps

1. **Analyze Changes** - git diff, files changed, modules affected, read handoff

2. **SonarQube Analysis** (OPTIONAL - skip if not configured)
   - Check SONARQUBE_PROJECT_KEY in PROJECT.md and sonarqube MCP in .mcp.json
   - If enabled: call `mcp__sonarqube__get_quality_gate`, `mcp__sonarqube__get_issues`, `mcp__sonarqube__get_metrics`
   - Quality gate ERROR → automatic CHANGES_REQUESTED
   - BLOCKER/CRITICAL bugs → critical issues
   - If unavailable/not configured → skip, rely on manual review

3. **Code Quality Review** - Style compliance, naming, organization, DRY, SOLID
4. **Functionality Review** - Requirements met, edge cases, error handling, input validation
5. **Security Review** - SQL injection, XSS, auth, authorization, OWASP Top 10
6. **Performance Review** - Query efficiency, N+1, caching, memory leaks, complexity
7. **Test Quality Review** - Coverage ≥80%, meaningful tests, AAA pattern, edge cases
8. **Architecture Review** - Pattern consistency, coupling, layering

9. **Generate Review Report** (`docs/tasks/TASK-XXX/handoff/review-report.md`)
   - Summary, changes reviewed, review checklist
   - SonarQube results (if enabled)
   - Findings by severity (Critical/Major/Minor)
   - Strengths, decision rationale, next steps

10. **Update Task Status** - IN_TESTING (approved) or IN_PROGRESS (changes requested)
11. **Create Handoff** - `docs/tasks/TASK-XXX/handoff/review-to-test.md` (approved) or `review-to-implementation.md` (changes requested)

## Review Criteria

**APPROVED requires ALL**:
- Zero critical issues (manual + SonarQube if enabled)
- Zero unacknowledged major issues
- Test coverage ≥ threshold (default 80%)
- No security vulnerabilities
- Follows code style, implements all requirements
- SonarQube quality gate OK (if enabled)

**CHANGES_REQUESTED if ANY**:
- Critical or major issues found
- Test coverage below threshold
- Security vulnerabilities found
- SonarQube quality gate ERROR (if enabled)
- Missing required functionality

## Review Modes

| Mode | Behavior |
|------|----------|
| Default | Standard review, minor issues non-blocking |
| `--strict` | Zero tolerance - any issue triggers CHANGES_REQUESTED |
| `--quick` | Critical issues only (security, functionality, breaking changes) |
| `--all` | Batch review all IN_REVIEW tasks sequentially |

## Error Handling

| Error | Solution |
|-------|----------|
| Task not in IN_REVIEW | Run `/dev-task` first to implement |
| No changes to review | Verify feature branch has commits |
| Review loop (3+ iterations) | Agent warns, suggests breaking task into smaller pieces |

## Related Commands

- `/dev-task` - Previous step (implementation)
- `/test-task` - Next step if APPROVED
- `/complete-task` - Full automation (includes review)

---

**Skill Type**: Code Review (Agent Orchestration)
