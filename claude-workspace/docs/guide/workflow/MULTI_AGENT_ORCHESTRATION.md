# Multi-Agent Team Orchestration Guide

## Overview

This document defines the orchestration workflow for a multi-agent development team:

| # | Agent | Role | Config |
|---|-------|------|--------|
| 1 | **Code Implementation Agent** | Develops features and fixes bugs | `.claude/agents/code-implementation.md` |
| 2 | **Code Review Agent** | Reviews code quality and standards | `.claude/agents/code-review.md` |
| 3 | **Test Agent** | Creates and executes all automated tests | `.claude/agents/test.md` |
| 4 | **Documentation Agent** | Maintains technical documentation | `.claude/agents/documentation.md` |
| 5 | **Manager Agent** | Orchestrates workflow and dispatches agents | `.claude/agents/manager.md` |

**Each agent's detailed responsibilities, tools, and examples are in their config files.** This document covers orchestration only.

---

## Persistent Memory Integration

All agents share persistent memory across sessions via hook-based capture and SQLite storage.

**Key benefits:**
- Past decisions, patterns, and learnings are available to all agents
- At SessionStart, relevant context is automatically injected
- All agents should use `/memory-search "query"` as their first step

**Commands:** `/memory-search "query"` | `/memory-clear` | `/memory-export`

**Privacy:** Wrap sensitive data in `<private>...</private>` tags (automatically stripped before storage).

**See:** [docs/guides/using-persistent-memory.md](guides/using-persistent-memory.md) for complete guide.

---

## Agent Roles Summary

### 1. Code Implementation Agent

**Input:** Task file (`docs/tasks/TASK-XXX/task.md`), specs from `docs/tasks/TASK-XXX/specs/`

**Output:** Implementation code, unit tests, commit on feature branch, handoff in `docs/tasks/TASK-XXX/handoff/`

**Key rules:**
- Write unit tests (developer's responsibility, not tester's)
- Meet coverage threshold from PROJECT.md (default 80%)
- Use `/auto-build test` for tech-agnostic test execution
- Update status: `/task-status TASK-ID IN_REVIEW`
- Create handoff: Write `docs/tasks/TASK-ID/handoff/implementation-to-review.md`

### 2. Code Review Agent

**Input:** Code changes (`git diff --unified=3`), handoff from `docs/tasks/TASK-XXX/handoff/`, SonarQube (if configured)

**Output:** Review report at `docs/tasks/TASK-XXX/handoff/review-report.md`, approval/rejection decision

**Key rules:**
- SonarQube analysis is OPTIONAL (skip if not configured in PROJECT.md/.mcp.json)
- Check: code quality, security, test coverage, standards compliance
- APPROVED → `/task-status TASK-ID IN_TESTING`
- CHANGES_REQUESTED → `/task-status TASK-ID IN_PROGRESS`

### 3. Test Agent

**Input:** Approved code, specs from `docs/tasks/TASK-XXX/specs/`, API specs from `docs/tasks/TASK-XXX/deliveries/api-specs/`

**Output:** Test files, test report in `docs/tasks/TASK-XXX/deliveries/test-reports/`, bug reports in `docs/tasks/TASK-XXX/bugs/` (if failures)

**Key rules:**
- Create ALL test types: API contract, integration, business rules, E2E
- Use testing framework defined in PROJECT.md (tech-agnostic)
- Map each SRS business rule to a test scenario
- ALL tests must pass (100%) before proceeding
- ALL PASS → `/task-status TASK-ID DOCUMENTING`
- ANY FAIL → `/task-status TASK-ID IN_PROGRESS` + bug report

### 4. Documentation Agent

**Input:** Test report from `docs/tasks/TASK-XXX/deliveries/test-reports/`, code changes, feature details

**Output:** API specs in `docs/tasks/TASK-XXX/deliveries/api-specs/`, final specs in `docs/tasks/TASK-XXX/deliveries/final-specs/`, README.md (if needed)

**Key rules:**
- Review all changes from implementation and testing
- Update API specs, final specs, business rules documentation
- Write all output to `docs/tasks/TASK-XXX/deliveries/` folder (never to external systems)
- Update status: `/task-status TASK-ID DONE`

---

## Orchestration Workflow

### Phase Dependencies (CRITICAL)

```
Phase 1 (Implementation) → Phase 2 (Code Review) → Phase 3 (Testing) → Phase 4 (Documentation) → Phase 5 (Push/PR)
```

**Rules:**
- Phase 3 cannot start until Phase 2 is **APPROVED**
- Phase 4 cannot start until Phase 3 shows **100% PASS**
- Phase 5 cannot start until Phase 4 is **DONE**
- Any review rejection → back to Phase 1
- Any test failure → back to Phase 1
- SonarQube quality gate failure → back to Phase 1 (if enabled)

### Standard Feature Development Flow

```
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 0: PLANNING (optional, human-driven)                     │
│  Skill: /task-plan                                              │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 1. /task-create TASK-ID "title" Priority type            │  │
│  │ 2. BA/Tech Lead places DetailDesign in specs/ (optional) │  │
│  │ 3. /task-plan TASK-ID                                    │  │
│  │    ├─ Collect refs: DetailDesign, Figma, Confluence, ... │  │
│  │    ├─ Clarify requirements with user                     │  │
│  │    ├─ Build implementation plan together                 │  │
│  │    └─ Write specs/implementation-plan.md                 │  │
│  │ 4. task.md updated: refs + description + requirements    │  │
│  │                                                          │  │
│  │ Skip if: task is simple, or using /complete-task         │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 1: CODE IMPLEMENTATION                                   │
│  Agent: Code Implementation Agent                               │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 1. /memory-search "TASK-ID" (context from past sessions) │  │
│  │ 2. Read task + specs from docs/tasks/TASK-ID/specs/        │  │
│  │ 3. Create feature branch                                  │  │
│  │ 4. Implement feature + write unit tests                   │  │
│  │ 5. Run tests: /auto-build test                            │  │
│  │ 6. Commit code                                            │  │
│  │ 7. /task-status TASK-ID IN_REVIEW                         │  │
│  │ 8. Write handoff: TASK-ID/handoff/impl-to-review.md       │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 2: CODE REVIEW                                           │
│  Agent: Code Review Agent                                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 1. Read task + handoff from TASK-ID/handoff/              │  │
│  │ 2. SonarQube analysis (if configured in PROJECT.md)       │  │
│  │ 3. Review code: git diff --unified=3                      │  │
│  │ 4. Check standards, security, tests                       │  │
│  │ 5. Create: TASK-ID/handoff/review-report.md               │  │
│  │ 6. Decision:                                              │  │
│  │    APPROVED → /task-status TASK-ID IN_TESTING              │  │
│  │    CHANGES_REQUESTED → /task-status TASK-ID IN_PROGRESS    │  │
│  │    CLARIFICATION_NEEDED → ask questions, dev answers,      │  │
│  │      then re-review (no code changes, saves full roundtrip)│  │
│  │ 7. Write: TASK-ID/handoff/review-to-[test|impl].md        │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │ (APPROVED only)
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 3: AUTOMATED TESTING                                     │
│  Agent: Test Agent                                              │
│  PREREQUISITE: Code Review APPROVED                             │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 1. Read task + specs + handoff/review-report.md            │  │
│  │ 2. Create test scenarios → deliveries/test-cases/         │  │
│  │ 3. Execute tests: /auto-build test                        │  │
│  │ 4. Create: deliveries/test-reports/test-report.md         │  │
│  │ 5. Decision:                                              │  │
│  │    ALL PASS → /task-status TASK-ID DOCUMENTING             │  │
│  │    ANY FAIL → /task-status TASK-ID IN_PROGRESS + bugs/    │  │
│  │ 6. Write: TASK-ID/handoff/test-to-[doc|impl].md           │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │ (ALL PASS only)
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 4: DOCUMENTATION                                         │
│  Agent: Documentation Agent                                     │
│  PREREQUISITE: ALL tests PASSED (100%)                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 1. Read task + deliveries/test-reports/test-report.md     │  │
│  │ 2. Update: deliveries/api-specs/                          │  │
│  │ 3. Update: deliveries/final-specs/                        │  │
│  │ 4. Update README.md (if major feature/breaking change)    │  │
│  │ 5. Document business rules with test references           │  │
│  │ 6. Commit documentation                                   │  │
│  │ 7. /task-status TASK-ID DONE                              │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 5: QUALITY GATE & PUSH                                   │
│  Automated via /commit-push-pr command                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 1. Verify task status = DONE                              │  │
│  │ 2. Commit all changes                                     │  │
│  │ 3. SonarQube quality gate (if configured)                 │  │
│  │    PASS → push | FAIL → block, return to Phase 1          │  │
│  │ 4. Push to remote                                         │  │
│  │ 5. Create Pull Request                                    │  │
│  │ 6. Update task with PR URL                                │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Bug Fix Flow (Simplified)

```
Bug Report (docs/tasks/TASK-ID/bugs/) → Implementation (fix + unit test) → Code Review → Testing → Documentation → Done
```

Same phases, same quality gates. No shortcuts — bugs follow the full pipeline.

### Fast-Track Workflow (Hotfix / Minor Changes)

For hotfixes, typo fixes, config changes, and minor patches where the full pipeline is overkill.

**When to use:** Set `workflow: fast-track` in task frontmatter (default is `standard`).

```yaml
---
id: TASK-042
title: Fix typo in error message
status: TODO
workflow: fast-track
---
```

**Eligible changes:**
- Single-file bug fixes with obvious root cause
- Typo / copy / config corrections
- Dependency version bumps (non-breaking)
- Documentation-only changes

**NOT eligible (must use standard workflow):**
- New features or API changes
- Security fixes (need full review + testing)
- Database schema changes
- Changes touching 5+ files

**Fast-track flow:**

```
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 1: IMPLEMENTATION (same as standard)                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 1. Implement fix + unit test for the fix                  │  │
│  │ 2. /auto-build test (all existing tests must pass)        │  │
│  │ 3. Commit code                                            │  │
│  │ 4. /task-status TASK-ID IN_REVIEW                         │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 2: QUICK REVIEW (abbreviated)                            │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ 1. Review code diff (focus: correctness + no regressions) │  │
│  │ 2. Verify unit tests pass                                 │  │
│  │ 3. No SonarQube required, no full checklist               │  │
│  │ 4. APPROVED → /task-status TASK-ID DONE (skip Phase 3+4)  │  │
│  │    REJECTED → /task-status TASK-ID IN_PROGRESS             │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  PHASE 5: PUSH (skip testing + documentation phases)            │
│  /commit-push-pr TASK-ID                                        │
└─────────────────────────────────────────────────────────────────┘
```

**Quality gates (fast-track):**
- [ ] Code compiles: `/auto-build check`
- [ ] ALL existing tests still pass: `/auto-build test`
- [ ] No security issues introduced
- [ ] Review report created (can be abbreviated)
- [ ] Commit references task ID

**What is skipped:**
- Full test scenario creation (Phase 3)
- Documentation update (Phase 4)
- SonarQube quality gate (Phase 5 — still runs if configured, but non-blocking for fast-track)
- Business rules validation checklist

---

## Task Status Workflow

```
TODO → IN_PROGRESS → IN_REVIEW → IN_TESTING → DOCUMENTING → DONE

Clarification path (avoids unnecessary code rewrites):
  IN_REVIEW  → CLARIFICATION_NEEDED → IN_REVIEW  (reviewer asks, developer answers, review continues)

Rejection paths:
  IN_REVIEW  → IN_PROGRESS  (code must change)
  IN_TESTING → IN_PROGRESS  (any test failed)

Fast-track path:
  IN_REVIEW  → DONE  (skip testing + docs for hotfixes)
```

| Status | Meaning | Assigned To |
|--------|---------|-------------|
| **TODO** | Created, waiting to start | — |
| **IN_PROGRESS** | Developer implementing | Code Implementation Agent |
| **IN_REVIEW** | Code review in progress | Code Review Agent |
| **CLARIFICATION_NEEDED** | Reviewer has questions, developer answers (no code changes) | Code Implementation Agent |
| **IN_TESTING** | All automated tests running | Test Agent |
| **DOCUMENTING** | Documentation being updated | Documentation Agent |
| **DONE** | All phases complete | — |

**Tracking:** Individual task files at `docs/tasks/TASK-XXX/task.md` with YAML frontmatter. Dashboard auto-generated at `docs/tasks/dashboard.md`.

**Update command:** `/task-status TASK-ID STATUS`

---

## Agent Communication Protocol

### Handoff Structure

Agents communicate via structured markdown files inside each task's folder.
All files for a task are co-located under `docs/tasks/TASK-XXX/`.

**Create handoff:** Use Write tool to create the appropriate file in `docs/tasks/TASK-ID/handoff/`

### Communication Channels

| Channel | Purpose | Location |
|---------|---------|----------|
| **Task file** | Status tracking, progress | `docs/tasks/TASK-XXX/task.md` |
| **Specs** | Requirements, implementation plan | `docs/tasks/TASK-XXX/specs/` |
| **Handoffs** | Agent-to-agent transitions + reviews | `docs/tasks/TASK-XXX/handoff/` |
| **Test cases** | Test scenarios | `docs/tasks/TASK-XXX/deliveries/test-cases/` |
| **Test reports** | Test results + screenshots + bugs | `docs/tasks/TASK-XXX/deliveries/test-reports/` |
| **API specs** | API specification delivery | `docs/tasks/TASK-XXX/deliveries/api-specs/` |
| **SQL scripts** | DDL, config inserts | `docs/tasks/TASK-XXX/deliveries/sql-scripts/` |
| **Final specs** | Detailed feature design | `docs/tasks/TASK-XXX/deliveries/final-specs/` |
| **Git commits** | Code changes with task ID references | Feature branches |

---

## Quality Gates

### Phase Transition Checklist

**Implementation → Review:**
- [ ] Code compiles: `/auto-build check`
- [ ] All unit tests pass (100%): `/auto-build test`
- [ ] Coverage meets PROJECT.md threshold (default 80%)
- [ ] Lint passes (if required by PROJECT.md): `/auto-build lint`
- [ ] Code committed to feature branch
- [ ] Handoff created in `docs/tasks/TASK-ID/handoff/implementation-to-review.md`

**Review → Testing:**
- [ ] Code review APPROVED (no CRITICAL/MAJOR issues)
- [ ] SonarQube quality gate passed (if enabled)
- [ ] Review report created at `docs/tasks/TASK-ID/handoff/review-report.md`

**Testing → Documentation:**
- [ ] ALL test types passed (100%) — API, integration, business, E2E
- [ ] Business rules validation checklist complete
- [ ] Test report created at `docs/tasks/TASK-ID/deliveries/test-reports/test-report.md`

**Documentation → Done:**
- [ ] API specs updated in `docs/tasks/TASK-ID/deliveries/api-specs/`
- [ ] Final specs updated in `docs/tasks/TASK-ID/deliveries/final-specs/`
- [ ] README.md updated (if needed)
- [ ] All documentation committed

**Done → Push/PR (if SonarQube enabled):**
- [ ] SonarQube quality gate PASSED (new bugs=0, new vulnerabilities=0, coverage≥80%)
- [ ] If FAIL → block push, return to Phase 1

**Thresholds are configured in PROJECT.md "Quality Gates Configuration" section.** All agents read thresholds from there at runtime.

---

## Error Handling and Rollback

### When Code Review Fails

1. Code Review Agent creates detailed report at `docs/tasks/TASK-ID/handoff/review-report.md`
2. Status → IN_PROGRESS via `/task-status`
3. Handoff to Implementation Agent at `docs/tasks/TASK-ID/handoff/review-to-implementation.md`
4. Implementation Agent reads review, fixes, re-runs tests, re-submits

### When Tests Fail

1. Test Agent extracts failure details (max 50 lines)
2. Categorizes failure: API Contract | Integration | Business Logic | Data Integrity | Workflow | Test Issue
3. Creates bug report in `docs/tasks/TASK-ID/bugs/BUG-ID.md`
4. Status → IN_PROGRESS via `/task-status`
5. Implementation Agent reads bug report, fixes, follows full review→test cycle

### When Workflow Gets Stuck

Manager detects stuck tasks using these rules:
- **Max review iterations**: Read from PROJECT.md (default: 3)
- If same task returned to IN_PROGRESS ≥ threshold times → **STOP**
- Manager reports: "TASK-ID stuck in review/test loop. Manual intervention needed."
- Wait for user decision before continuing

### Agent Timeout Detection

Manager monitors agent progress:
- If agent status hasn't changed after **2 consecutive check-ins** → flag as potentially hung
- Manager reads agent output for errors
- If unrecoverable → inform user with error details and options (retry/skip/manual)

---

## Parallel Work Strategies

### Cross-Feature Parallelism

Multiple tasks CAN be in different phases simultaneously:

```
Time  | Implementation | Code Review | Test Agent | Documentation
------|----------------|-------------|------------|---------------
T1    | Feature A      | —           | —          | —
T2    | Feature B      | Feature A   | —          | —
T3    | Feature C      | Feature B   | Feature A  | —
T4    | Feature D      | Feature C   | Feature B  | Feature A
```

### Rules

- Each agent works on **maximum 1 task** at a time
- **Sequential within a feature**: Review must complete before testing starts (same feature)
- **Parallel across features**: Different tasks can be in different phases
- Priority features (emergency bugs) can jump the queue
- Manager dispatches agents based on task status independently per task

---

## Agent Teams Integration (Experimental)

> **Requires:** Claude Opus 4.6+ with `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` enabled.
> This is opt-in. The standard sequential workflow works without Agent Teams.

### What Agent Teams Adds

Agent Teams allows the Manager to spawn **real parallel teammates** — each running in its own Claude Code instance (tmux pane), with peer-to-peer messaging and shared task dependencies.

### When to Use Agent Teams

| Scenario | Standard Workflow | With Agent Teams |
|----------|-------------------|------------------|
| Single feature, sequential | Implementation → Review → Test → Docs | Same (no benefit) |
| **Testing phase** (parallel) | Test Agent runs all types sequentially | **3 teammates run test types in parallel** |
| **Multiple features** | Pipeline parallelism only | **True parallel: multiple features simultaneously** |
| **Debugging** (competing hypotheses) | Single agent investigates | **Multiple agents investigate different hypotheses** |

### Pattern 1: Parallel Testing

After Code Review APPROVED, Manager spawns 3 test teammates instead of 1 Test Agent:

```
Review APPROVED →
  ┌─ Teammate 1: API contract tests + smoke tests
  ├─ Teammate 2: Integration tests + database validation
  └─ Teammate 3: Business rule tests + E2E workflows
       │
       ▼ (all 3 must pass)
  Documentation Agent
```

**Manager dispatch (Agent Teams mode):**
```
Spawn 3 teammates for TASK-[ID] testing:

Teammate 1: "Run API contract and smoke tests for TASK-[ID]. Read .claude/agents/test.md for guidelines. Report results to lead when done."

Teammate 2: "Run integration tests for TASK-[ID]. Validate database operations. Read .claude/agents/test.md for guidelines. Report results to lead when done."

Teammate 3: "Run business rule and E2E tests for TASK-[ID]. Read .claude/agents/test.md for guidelines. Report results to lead when done."
```

**Merge rule:** ALL 3 teammates must report PASS. If ANY reports FAIL → status back to IN_PROGRESS. Manager creates consolidated test report from all 3 results.

### Pattern 2: Parallel Feature Development

With Agent Teams, different features can truly run in parallel (not just pipeline parallelism):

```
Teammate 1: Implementing Feature A (full pipeline)
Teammate 2: Implementing Feature B (full pipeline)
Lead (Manager): Coordinates, resolves conflicts, merges results
```

**Boundary rule:** Each teammate must own a **different set of files**. If features overlap in files, run them sequentially to avoid merge conflicts.

### Pattern 3: Delegate Mode

Enable delegate mode to restrict the Manager to coordination-only:

```
The Manager ONLY uses: Task tool (spawn teammates), messaging, task management
The Manager NEVER: reads code, runs builds, edits files, executes tests
```

This prevents the Manager from accidentally doing agent work instead of orchestrating.

### Cost Consideration

Agent Teams uses **3-5x more tokens** than sequential workflow due to parallel instances. Use it for:
- Large features where testing is the bottleneck
- Time-sensitive deliveries where speed > cost
- Complex debugging requiring multiple investigation paths

For routine tasks, the standard sequential workflow is more cost-efficient.

---

## Documentation Structure

```
docs/
├── tasks.md              # Task dashboard (auto-generated)
├── tasks/                # Individual task files (YAML frontmatter)
├── refs/                # SRS, Detail Design
├── api/                  # API endpoint documentation
├── features/             # Feature documentation
├── reviews/              # Code review reports
├── test-reports/         # Test execution reports
├── bugs/                 # Bug reports
├── handoffs/             # Agent handoff summaries
├── guides/               # How-to guides
├── troubleshooting/      # Troubleshooting guides
└── lessons-learned/      # Published lessons learned
```

---

## Token Optimization (All Agents)

| Rule | Do | Don't |
|------|----|-------|
| **Build/test** | `/auto-build test` (auto-detects tech) | Raw build commands with verbose output |
| **File reading** | `Read` tool with line ranges | `cat`, `head`, `tail` |
| **Search** | `Grep` / `Glob` tools | `grep`, `find` bash commands |
| **Task updates** | `/task-status TASK-ID STATUS` | Manually editing task files |
| **Handoffs** | `/handoff TASK-ID "to:agent" "..."` | Manually creating handoff files |
| **Logs** | `grep "FAILED" \| head -50` | Loading full log files |
| **Diffs** | `git diff --unified=3` | `git diff` (unlimited context) |

**Agent-specific optimization details are in each agent's config file.**

---

## MCP Tool Usage Rule

**CRITICAL: READ from MCP, WRITE to `docs/`**

- **INPUT**: Use MCP tools to read from external systems (Jira, Confluence, SonarQube)
- **OUTPUT**: Always write to markdown files in `docs/` folder
- **Never** update Jira tickets or write to Confluence via MCP
- **Exception**: `/publish-lesson-learn` writes BOTH locally and to VISSoft Confluence

---

## Best Practices Summary

1. **Search memory first** — `/memory-search` before starting any task
2. **Use slash commands** — `/auto-build`, `/task-status`, `/handoff` for consistency and token savings
3. **Follow quality gates** — Read thresholds from PROJECT.md, never skip checks
4. **Clear handoffs** — Every phase transition needs a handoff with summary, files changed, and focus areas
5. **Reference task ID** — In commits, handoffs, reviews, test reports, and bug reports
6. **Tech-agnostic** — Use PROJECT.md for tech-specific commands, not hardcoded in workflow
7. **Fail fast** — Stop at first test failure category, don't run all tests if smoke tests fail
8. **Audit trail** — Every decision (review, test, documentation) produces a markdown artifact in `docs/`
