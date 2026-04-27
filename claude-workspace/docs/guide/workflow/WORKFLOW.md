# Multi-Agent Workflow Guide

This document describes the complete workflow for the 4-agent development system.

## Agents Overview

1. **Code Implementation Agent** - Develops features and fixes bugs
2. **Code Review Agent** - Reviews code quality and standards
3. **Test Agent** - Creates and executes all automated tests (Karate)
4. **Documentation Agent** - Maintains technical documentation

## Standard Feature Development Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     START: New Task in docs/tasks/dashboard.md            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 1: CODE IMPLEMENTATION                                   │
│  Agent: Code Implementation Agent                               │
│                                                                 │
│  1. Read task from docs/tasks/TASK-ID/task.md                   │
│  2. Read specs from docs/tasks/TASK-ID/specs/                   │
│  3. Create feature branch                                       │
│  4. Implement feature                                           │
│  5. Write unit tests (developer's responsibility)               │
│  6. Run unit tests: mvn test -q -Dtest=*UnitTest                │
│  7. Commit code                                                 │
│  8. Update status to "IN_REVIEW" via /task-status               │
│  9. Create handoff in docs/tasks/TASK-ID/handoff/               │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 2: CODE REVIEW                                           │
│  Agent: Code Review Agent                                       │
│                                                                 │
│  1. Read task + handoff from docs/tasks/TASK-ID/handoff/        │
│  2. Review code changes (git diff --unified=3)                  │
│  3. Check against coding standards (CLAUDE.md)                  │
│  4. Verify unit test coverage                                   │
│  5. Create: docs/tasks/TASK-ID/handoff/review-report.md         │
│  6. Decision:                                                   │
│     - APPROVED → Continue to Phase 3                            │
│     - CHANGES REQUESTED → Return to Phase 1                     │
│  7. Update task status via /task-status                         │
└────────────────────────────┬────────────────────────────────────┘
                             │ (if approved)
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 3: AUTOMATED TESTING (ALL TEST TYPES)                    │
│  Agent: Test Agent                                              │
│                                                                 │
│  1. Read task + specs + review-report from docs/tasks/TASK-ID/  │
│  2. Create test scenarios → deliveries/test-cases/:             │
│     - API contract tests (@smoke, @api-contract)                │
│     - Integration tests (@integration)                          │
│     - Business rule tests (@business, @srs-validation)          │
│     - End-to-end workflows (@e2e)                               │
│  3. Create test data (JSON files)                               │
│  4. Execute all automated tests (see execution order)           │
│  5. Verify API contracts, business rules, integrations          │
│  6. Create: deliveries/test-reports/test-report.md              │
│  7. Decision:                                                   │
│     - ALL PASSED → Continue to Phase 4                          │
│     - FAILED → Create bug in bugs/                              │
│  8. Update task status via /task-status                         │
└────────────────────────────┬────────────────────────────────────┘
                             │ (if all tests pass)
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 4: DOCUMENTATION                                         │
│  Agent: Documentation Agent                                     │
│                                                                 │
│  1. Read task + test report from docs/tasks/TASK-ID/            │
│  2. Review test results from deliveries/test-reports/           │
│  3. Update: deliveries/api-specs/                               │
│  4. Update: deliveries/final-specs/                             │
│  5. Update README.md if needed                                  │
│  6. Update task status to "DONE" via /task-status               │
│  7. Commit all documentation changes                            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
                    ┌────────────────┐
                    │   COMPLETED    │
                    └────────────────┘
```

## Test Execution Order (Phase 3)

The Test Agent executes tests in this priority order:

```
1. Smoke Tests (@smoke)
   ↓ Quick validation of basic functionality

2. API Contract Tests (@api-contract)
   ↓ Verify API behaves per specification

3. Integration Tests (@integration)
   ↓ Verify database, Kafka, external services

4. Business Rule Tests (@business)
   ↓ Validate SRS requirements compliance

5. End-to-End Workflows (@e2e)
   ↓ Complete user journeys

If any phase fails, stop and create bug report
```

## Bug Fix Flow

```
┌────────────────────────────────┐
│   Bug Report in                │
│   TASK-ID/bugs/                │
└──────────┬─────────────────────┘
           │
           ▼
┌─────────────────────────────┐
│  Code Implementation Agent  │
│  - Read bug from TASK-ID/   │
│    deliveries/test-reports/ │
│    bugs/                    │
│  - Analyze and fix bug      │
│  - Add unit test for bug    │
│  - Commit fix               │
│  - Update docs/tasks/dashboard.md     │
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│  Code Review Agent          │
│  - Quick review of fix      │
│  - Verify fix approach      │
│  - Check unit test added    │
│  - Create review            │
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│  Test Agent                 │
│  - Re-run all test types    │
│  - Verify bug is fixed      │
│  - Validate no side effects │
│  - Create test report       │
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│  Documentation Agent        │
│  - Update final-specs/      │
│  - Update task status: DONE │
└─────────────────────────────┘
```

## Agent Communication Protocol

### Handoff Structure

Each agent provides structured handoffs inside the task's folder:

**File location:** `docs/tasks/TASK-ID/handoff/[from-phase]-to-[to-phase].md`

Examples:
- `docs/tasks/TASK-001/handoff/implementation-to-review.md`
- `docs/tasks/TASK-001/handoff/review-to-test.md`
- `docs/tasks/TASK-001/handoff/test-to-documentation.md`
- `docs/tasks/TASK-001/handoff/review-report.md` (review decisions)

Use the template: `docs/templates/handoff-template.md`

### Task Status Workflow (docs/tasks/dashboard.md)

Track progress through task statuses:

```
TODO → IN_PROGRESS → IN_REVIEW → IN_TESTING → DOCUMENTING → DONE

# Rejection flows:
IN_REVIEW (changes requested) → IN_PROGRESS
IN_TESTING (tests failed) → IN_PROGRESS (with bug report)
```

### Status Definitions

- **TODO**: Task created, ready to start
- **IN_PROGRESS**: Code Implementation Agent implementing
- **IN_REVIEW**: Code Review Agent reviewing
- **IN_TESTING**: Test Agent creating and executing all tests
- **DOCUMENTING**: Documentation Agent updating docs
- **DONE**: All phases complete

## Quality Gates

### Implementation → Review

Code Implementation Agent must verify:
- [ ] Code compiles without errors
- [ ] All unit tests pass (100%)
- [ ] Unit test coverage ≥ 80%
- [ ] Code committed to feature branch
- [ ] Commit message references task ID
- [ ] Task status updated to "IN_REVIEW" via /task-status
- [ ] Handoff created in docs/tasks/TASK-ID/handoff/

### Review → Testing

Code Review Agent must verify:
- [ ] Code approved by reviewer
- [ ] All review issues addressed
- [ ] No critical issues (SonarQube)
- [ ] No security vulnerabilities
- [ ] Coding standards followed (CLAUDE.md)
- [ ] Task status updated to "IN_TESTING" via /task-status
- [ ] Review report created at docs/tasks/TASK-ID/handoff/review-report.md

### Testing → Documentation

Test Agent must verify:
- [ ] All smoke tests pass (100%)
- [ ] All API contract tests pass (100%)
- [ ] All integration tests pass (100%)
- [ ] All business rule tests pass (100%)
- [ ] All E2E workflows pass (100%)
- [ ] No defects found
- [ ] Business validation checklist completed
- [ ] Test report created at docs/tasks/TASK-ID/deliveries/test-reports/test-report.md
- [ ] Task status updated to "DOCUMENTING" via /task-status

### Documentation → Done

Documentation Agent must verify:
- [ ] API specs updated in docs/tasks/TASK-ID/deliveries/api-specs/
- [ ] Final specs updated in docs/tasks/TASK-ID/deliveries/final-specs/
- [ ] README.md updated if needed
- [ ] Business rules documented
- [ ] Configuration documented
- [ ] All documentation committed
- [ ] Task status set to "DONE" via /task-status

## Parallel Work Strategies

### When Multiple Features Are In Progress

**Parallelization Opportunities:**
- Code Implementation can start Feature B while Code Review reviews Feature A
- Test Agent can create tests for Feature B while Code Review reviews Feature A
- Documentation can document Feature A while Test Agent tests Feature B
- Multiple features can be in different phases simultaneously

**Sequential Dependencies (Same Feature):**
```
Feature X: Implementation → Review → Testing → Documentation
(Must complete in this order for single feature)

Feature Y: Can be in any phase while Feature X is in a different phase
```

**Example Timeline:**
```
Time  | Implementation | Code Review | Test Agent       | Documentation
------|----------------|-------------|------------------|---------------
T1    | Feature A      | -           | -                | -
T2    | Feature B      | Feature A   | -                | -
T3    | Feature C      | Feature B   | Feature A (all)  | -
T4    | Feature D      | Feature C   | Feature B (all)  | Feature A
T5    | Feature E      | Feature D   | Feature C (all)  | Feature B
```

## Error Handling and Rollback

### When Code Review Fails

**Code Review Agent:**
1. Create detailed review report at `docs/tasks/TASK-ID/handoff/review-report.md`
2. Update task status to "IN_PROGRESS" via `/task-status`
3. Categorize issues by severity (Critical, Major, Minor)

**Code Implementation Agent:**
1. Read review report from `docs/tasks/TASK-ID/handoff/review-report.md`
2. Address all issues
3. Re-run unit tests
4. Create new commit (or amend if appropriate)
5. Update task status back to "IN_REVIEW" via `/task-status`

### When Automated Tests Fail

**Test Agent:**
1. Extract failure details (max 50 lines)
2. Categorize failure type (API, Integration, Business Logic, etc.)
3. Create bug report in `docs/tasks/TASK-ID/bugs/`
4. Update task status to "IN_PROGRESS" via `/task-status`
5. Create handoff at `docs/tasks/TASK-ID/handoff/test-to-implementation.md`

**Code Implementation Agent:**
1. Read bug report from `docs/tasks/TASK-ID/bugs/`
2. Review SRS/DD references if business logic bug
3. Fix the issue
4. Add/update unit tests for the fix
5. Commit fix with bug ID reference
6. Follow standard review → test flow

## Token Optimization (All Agents)

### Global Rules
1. **Always use MCP tools first** - More token-efficient
2. **Never load full logs** - Use grep/tail with limits (max 20-50 lines)
3. **Use quiet flags** - `-q` for Maven, Docker, kubectl, etc.
4. **Targeted file reads** - Use view tool with line ranges
5. **Batch operations** - Multiple updates in one call

### Agent-Specific Examples

**Code Implementation:**
```bash
✅ mvn test -q -Dtest=*UnitTest
✅ view src/main/java/UserService.java --lines 50-100
❌ mvn test  # Loads all output
❌ cat src/main/java/UserService.java
```

**Code Review:**
```bash
✅ git diff main...feature-branch --unified=3
✅ grep -A 5 "TODO" src/**/*.java | head -30
❌ git diff  # Too much context
❌ cat entire_file.java
```

**Test Agent:**
```bash
✅ mvn test -Dkarate.options="--tags @smoke" -q
✅ grep "FAILED" target/karate.log | head -20
❌ mvn test  # Verbose output
❌ cat target/karate.log
```

**Documentation Agent:**
```bash
✅ view docs/api/endpoints.md --lines 100-150
✅ # Update only changed section
❌ cat docs/api/endpoints.md  # Entire file
```

## Metrics and Monitoring

### Key Performance Indicators (KPIs)

**Code Implementation Agent:**
- Average time from "TODO" to "IN_REVIEW"
- Number of review rejections (target: < 20%)
- Unit test coverage (target: 90%+)
- Defects found in later phases (target: < 5%)

**Code Review Agent:**
- Average review time (target: < 1 hour)
- Approval rate (target: > 80%)
- Issues caught vs escaped (target: > 95%)

**Test Agent:**
- Test creation time
- Test execution time
- API coverage (target: 100%)
- Business rule coverage (target: 100%)
- First-run pass rate (target: > 80%)

**Documentation Agent:**
- Documentation completion time
- Documentation quality (measured by feedback)
- Completeness score (target: 100%)

## Best Practices Summary

### For All Agents

1. **Always use MCP tools** for external operations
2. **Never load full logs** - extract only what's needed
3. **Use quiet mode** for build commands
4. **Targeted file operations** - read only necessary sections
5. **Update docs/tasks/dashboard.md frequently** - keep status current
6. **Clear handoffs** - use templates for consistency
7. **Follow conventions** - commit messages, branch names
8. **Think in tokens** - every operation should be efficient

### Communication Checklist

Before handing off to next agent:
- [ ] docs/tasks/dashboard.md updated with current status
- [ ] Clear summary of work completed
- [ ] Any blockers or issues documented
- [ ] Next steps identified
- [ ] All commits reference task ID
- [ ] Handoff document created (if applicable)

## Quick Reference

### File Locations
- **Agent Specs:** `.claude/agents/[agent-name].md`
- **Task Dashboard:** `docs/tasks/dashboard.md` (auto-generated)
- **Task File:** `docs/tasks/TASK-ID/task.md`
- **Specs:** `docs/tasks/TASK-ID/specs/`
- **Handoffs + Reviews:** `docs/tasks/TASK-ID/handoff/`
- **Test Cases:** `docs/tasks/TASK-ID/deliveries/test-cases/`
- **Test Reports:** `docs/tasks/TASK-ID/deliveries/test-reports/`
- **Bug Reports:** `docs/tasks/TASK-ID/bugs/`
- **API Specs:** `docs/tasks/TASK-ID/deliveries/api-specs/`
- **SQL Scripts:** `docs/tasks/TASK-ID/deliveries/sql-scripts/`
- **Final Specs:** `docs/tasks/TASK-ID/deliveries/final-specs/`
- **Templates:** `docs/templates/*.md`

### Command Patterns
```bash
# Build & Test (always use -q)
mvn clean install -q
mvn test -q -Dtest=*UnitTest

# Git operations (limited context)
git diff main...feature-branch --unified=3
git log --oneline -10

# Log extraction (never load full logs)
grep ERROR app.log | tail -20
grep "Tests run:" target/surefire-reports/*.txt

# File operations (use line ranges)
view src/main/java/Service.java --lines 50-100
```

### Decision Trees

**Is my change complete?**
```
Can I answer YES to all:
├─ Code compiles? → YES
├─ Tests pass? → YES
├─ Coverage ≥ 80%? → YES
├─ Follows standards? → YES
└─ Handoff created? → YES
    → Ready for next phase
```

**Should this be a bug report?**
```
Is it a code defect?
├─ YES → Create bug report in docs/tasks/TASK-ID/bugs/
└─ NO (test issue?) → Fix test, no bug report
```

---

**For detailed agent instructions, see:**
- [Code Implementation Agent](agents/code-implementation-agent.md)
- [Code Review Agent](agents/code-review-agent.md)
- [Test Agent](agents/test-agent.md)
- [Documentation Agent](agents/documentation-agent.md)

**For templates, see:**
- docs/templates/handoff-template.md
- docs/templates/review-template.md
- docs/templates/test-report-template.md
- docs/templates/bug-report-template.md
