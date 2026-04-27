# Agent Manager Guide - Automated Workflow Orchestration

**The easiest way to use your AI development team!**

---

## 🎯 What is Agent Manager?

**Agent Manager** is a meta-agent (orchestrator) that **automatically manages your entire development workflow**.

Instead of manually invoking 4 different agents, you invoke the Agent Manager **once** and it handles everything:

```
WITHOUT Agent Manager (Manual):
User → Code Implementation Agent
User → Code Review Agent
User → Test Agent
User → Documentation Agent
= 4 commands per task ❌

WITH Agent Manager (Automated):
User → Agent Manager (handles all 4 agents automatically)
= 1 command per task ✅
```

**You save 75% of management overhead!**

---

## ✨ Key Features

### 1. **Fully Automated Workflow**
- You create task in `docs/tasks/dashboard.md`
- Agent Manager completes entire workflow
- No manual intervention needed

### 2. **Intelligent Decision Making**
- Code review approved? → Auto-dispatch Test Agent
- Tests failed? → Auto-dispatch Code Implementation to fix
- Handles all workflow transitions automatically

### 3. **Parallel Task Management**
- Can manage multiple tasks simultaneously
- Task A in testing, Task B in review, Task C in implementation
- Maximizes team throughput

### 4. **Progress Reporting**
- Real-time updates on task progress
- Alerts when phases complete
- Summary reports when tasks finish

### 5. **Error Handling**
- Detects stuck workflows (infinite loops)
- Reports errors clearly
- Asks for guidance when needed

---

## 🚀 Quick Start (5 Minutes)

### Step 1: Create a Task

Edit `docs/tasks/dashboard.md`:

```markdown
## TASK-001: User Profile API
**Status:** TODO
**Priority:** High
**Created:** 2026-01-23

### Description
Implement RESTful API for user profile management

### Requirements
- POST /users/{id}/profile (create/update)
- GET /users/{id}/profile (read)
- Validation, error handling, audit logging

### Acceptance Criteria
- [ ] API endpoints implemented
- [ ] Unit tests (80%+ coverage)
- [ ] Integration tests pass
- [ ] API documentation updated
```

### Step 2: Invoke Agent Manager

```bash
cd "D:\01. PROJECTS\DEMO MULTIPLE AGENTS\template-ai-team"
claude
```

Then in chat:
```
You are the Agent Manager (Project Manager). Read your configuration from .claude/agents/manager.md and complete TASK-001 from docs/tasks/dashboard.md
```

### Step 3: Agent Manager Takes Over

**You'll see:**

```
📋 Starting workflow for TASK-001: User Profile API
Status: TODO → IN_PROGRESS
Dispatching: Code Implementation Agent

[Code Implementation Agent working...]

✅ Code implementation complete for TASK-001
Status: IN_PROGRESS → IN_REVIEW
Dispatching: Code Review Agent

[Code Review Agent working...]

✅ Code review APPROVED for TASK-001
Status: IN_REVIEW → IN_TESTING
Dispatching: Test Agent

[Test Agent working...]

✅ All tests passed for TASK-001 (25/25 tests - 100%)
Status: IN_TESTING → DOCUMENTING
Dispatching: Documentation Agent

[Documentation Agent working...]

🎉 TASK-001 completed successfully!
✅ Implementation: Complete
✅ Code Review: APPROVED
✅ Testing: 25/25 tests passed (100%)
✅ Documentation: Updated

Status: DOCUMENTING → DONE
```

### Step 4: Done!

Your feature is fully implemented, reviewed, tested, and documented. No manual intervention required!

---

## 📋 Usage Modes

### Mode 1: Single Task Completion (Recommended for Learning)

**Command:**
```
You are the Agent Manager. Read your configuration from .claude/agents/manager.md and complete TASK-001 from docs/tasks/dashboard.md
```

**What happens:**
- Agent Manager processes TASK-001 through complete workflow
- Reports progress at each phase
- Stops when task is DONE
- Perfect for getting started

### Mode 2: Continuous Management (Recommended for Production)

**Command:**
```
You are the Agent Manager. Read your configuration from .claude/agents/manager.md and manage all tasks in docs/tasks/dashboard.md continuously
```

**What happens:**
- Agent Manager processes ALL tasks (TODO, IN_PROGRESS, IN_REVIEW, IN_TESTING, DOCUMENTING)
- Runs workflows in parallel for maximum efficiency
- Reports progress periodically
- Asks before continuing to next batch
- Perfect for managing multiple features

### Mode 3: Batch Processing (Process All TODO Tasks)

**Command:**
```
You are the Agent Manager. Read your configuration from .claude/agents/manager.md and process all TODO tasks in priority order (High → Medium → Low)
```

**What happens:**
- Agent Manager finds all TODO tasks
- Sorts by priority
- Processes each task sequentially
- Reports when all complete
- Perfect for backlog processing

### Mode 4: Parallel Processing (Maximum Speed)

**Command:**
```
You are the Agent Manager. Read your configuration from .claude/agents/manager.md and process all tasks in parallel
```

**What happens:**
- Agent Manager dispatches appropriate agent for EACH task based on status
- All agents run simultaneously
- Maximum throughput
- Perfect for large teams with many tasks

---

## 🔄 Workflow Orchestration

### What Agent Manager Does Automatically

```
┌──────────────────────────────────────────────────────┐
│  AGENT MANAGER reads docs/tasks/dashboard.md                   │
└────────────────┬─────────────────────────────────────┘
                 │
    ┌────────────┴────────────┐
    │ Task Status?            │
    └─┬───┬───┬───┬───┬──┬───┘
      │   │   │   │   │  │
      ▼   ▼   ▼   ▼   ▼  ▼

  TODO  IN_PROGRESS  IN_REVIEW  IN_TESTING  DOCUMENTING  DONE

   │        │           │           │            │         │
   │        │           │           │            │         │
   ▼        ▼           ▼           ▼            ▼         ▼

 Dispatch  Dispatch    Dispatch    Dispatch   Dispatch   Skip
   Code      Code        Code         Test        Doc    (Complete)
   Impl      Impl       Review       Agent       Agent
  Agent     Agent       Agent

   │        │           │           │            │
   │        │           │           │            │
   ▼        ▼           ▼           ▼            ▼

 Wait      Wait        Wait        Wait         Wait
  for       for         for         for          for
Complete  Complete    Complete    Complete     Complete

   │        │           │           │            │
   │        │           │           │            │
   ▼        ▼           ▼           ▼            ▼

Verify    Verify      Read        Read         Verify
Status    Status      Review      Test         Status
Updated   Updated     Decision    Results      = DONE

   │        │        ┌──┴──┐     ┌──┴──┐        │
   │        │        │     │     │     │        │
   │        │        ▼     ▼     ▼     ▼        │
   │        │     APPROVED  │  PASS   FAIL      │
   │        │        │   CHANGES│     │         │
   │        │        │   REQUESTED   │          │
   │        │        │      │    │    │         │
   └────────┴────────┴──────┘    │    └─────────┘
                 │                │
                 ▼                ▼
           Next Phase        Fix Bugs
         (Test Agent)    (Code Impl Agent)
```

### Decision Points Agent Manager Handles

**1. After Code Implementation:**
- ✅ Status updated to IN_REVIEW? → Dispatch Code Review
- ❌ Status not updated? → Report error, ask user

**2. After Code Review:**
- ✅ APPROVED? → Dispatch Test Agent
- ❌ CHANGES_REQUESTED? → Dispatch Code Implementation to fix

**3. After Testing:**
- ✅ All tests PASS? → Dispatch Documentation Agent
- ❌ Any tests FAIL? → Dispatch Code Implementation to fix bugs

**4. After Documentation:**
- ✅ Status updated to DONE? → Task complete, report success

---

## 💡 Example Scenarios

### Scenario 1: Perfect Happy Path

```
Task: TASK-001 (User Profile API)

Agent Manager:
1. Dispatches Code Implementation → Complete (80% coverage, all tests pass)
2. Dispatches Code Review → APPROVED (no issues found)
3. Dispatches Test Agent → ALL PASS (25/25 tests, 100%)
4. Dispatches Documentation → Updated
5. Task DONE

Total time: ~30 minutes (automated)
User commands: 1
Result: ✅ Feature complete
```

### Scenario 2: Code Review Finds Issues

```
Task: TASK-002 (Login Fix)

Agent Manager:
1. Dispatches Code Implementation → Complete
2. Dispatches Code Review → CHANGES_REQUESTED (2 MAJOR issues)
   → Report: "Code review found 2 MAJOR issues. Dispatching developer to fix..."
3. Dispatches Code Implementation (fix) → Fixed issues
4. Dispatches Code Review (retry) → APPROVED
5. Dispatches Test Agent → ALL PASS
6. Dispatches Documentation → Updated
7. Task DONE

Total iterations: 2 (review → fix → review)
User commands: 1
Result: ✅ Feature complete with higher quality
```

### Scenario 3: Tests Fail

```
Task: TASK-003 (Rate Limiting)

Agent Manager:
1. Dispatches Code Implementation → Complete
2. Dispatches Code Review → APPROVED
3. Dispatches Test Agent → FAIL (1 business rule test failed)
   → Creates BUG-001 in docs/bugs/
   → Report: "Tests failed (BR-002 rate limiting). Dispatching developer to fix..."
4. Dispatches Code Implementation (fix bug) → Fixed
5. Dispatches Test Agent (rerun) → ALL PASS
6. Dispatches Documentation → Updated
7. Task DONE

Total iterations: 2 (test → fix → test)
User commands: 1
Result: ✅ Feature complete with bug fixed
```

### Scenario 4: Multiple Tasks in Parallel

```
Tasks:
- TASK-001: User Profile API (TODO)
- TASK-002: Login Fix (IN_REVIEW)
- TASK-003: Dashboard (IN_TESTING)

Agent Manager:
1. Spawns Code Implementation for TASK-001
2. Spawns Code Review for TASK-002
3. Spawns Test Agent for TASK-003

[All 3 agents run in parallel]

30 minutes later:
- TASK-001: IN_REVIEW (implementation done)
- TASK-002: IN_TESTING (review approved)
- TASK-003: DOCUMENTING (tests passed)

Agent Manager continues managing all 3 tasks until all DONE

User commands: 1
Result: ✅ 3 features complete in parallel
```

---

## 🛡️ Error Handling

### Stuck in Review Loop

```
TASK-004 keeps bouncing: IN_REVIEW → IN_PROGRESS → IN_REVIEW → IN_PROGRESS...

Agent Manager detects after 3 iterations:
"⚠️ TASK-004 appears stuck in review-fix loop (3 iterations).
Issues found each time:
  - Iteration 1: 2 MAJOR (fixed)
  - Iteration 2: 1 MAJOR (fixed)
  - Iteration 3: 1 MAJOR (different issue)

Possible causes:
- Requirements unclear
- Standards too strict
- Complex feature needing different approach

Manual review recommended. Continue automatic retries? (yes/no)"

→ Waits for user decision
```

### Agent Returns Error

```
Test Agent fails with error:

Agent Manager:
"❌ Test Agent encountered error for TASK-005:
Error: Cannot connect to database

This appears to be an environment issue, not code issue.

Recommended actions:
1. Check database is running
2. Verify connection string in .env
3. Test database connectivity

Retry Test Agent? (yes/no/skip to documentation)"

→ Waits for user decision
```

---

## 📊 Progress Reporting

### Real-Time Updates

```
[Agent Manager] 📋 Starting workflow for TASK-001: User Profile API
[Agent Manager] Status: TODO → IN_PROGRESS
[Agent Manager] Dispatching: Code Implementation Agent

[15 minutes later]
[Agent Manager] ✅ Code implementation complete for TASK-001
[Agent Manager] Files changed: 5 Java files, 3 test files
[Agent Manager] Test coverage: 82% ✅
[Agent Manager] Status: IN_PROGRESS → IN_REVIEW
[Agent Manager] Dispatching: Code Review Agent

[10 minutes later]
[Agent Manager] ✅ Code review APPROVED for TASK-001
[Agent Manager] Issues found: 0 CRITICAL, 0 MAJOR, 2 MINOR (acceptable)
[Agent Manager] Status: IN_REVIEW → IN_TESTING
[Agent Manager] Dispatching: Test Agent

[20 minutes later]
[Agent Manager] ✅ All tests passed for TASK-001
[Agent Manager] Test results: 25/25 tests (100%)
[Agent Manager]   - API Contract: 8/8 ✅
[Agent Manager]   - Integration: 6/6 ✅
[Agent Manager]   - Business Rules: 4/4 ✅
[Agent Manager]   - E2E Workflows: 2/2 ✅
[Agent Manager] Status: IN_TESTING → DOCUMENTING
[Agent Manager] Dispatching: Documentation Agent

[5 minutes later]
[Agent Manager] 🎉 TASK-001 completed successfully!
[Agent Manager] Total time: ~50 minutes
[Agent Manager] ✅ Implementation: Complete
[Agent Manager] ✅ Code Review: APPROVED (2 minor issues)
[Agent Manager] ✅ Testing: 25/25 tests passed (100%)
[Agent Manager] ✅ Documentation: Updated (API + feature docs)
[Agent Manager] Status: DOCUMENTING → DONE
```

### Periodic Summary Reports

```
[Agent Manager] 📊 Multi-Task Progress Report (Every 30 minutes)

Active Tasks:
✅ TASK-001 (User Profile API): DONE (Completed 10 minutes ago)
⏳ TASK-002 (Login Fix): IN_TESTING (Test Agent running...)
⏳ TASK-003 (Dashboard): IN_REVIEW (Code Review Agent running...)
⏳ TASK-004 (Rate Limiting): IN_PROGRESS (Fixing review issues...)

Completed Today: 1 task
In Progress: 3 tasks
Blocked: 0 tasks

Next check in 30 minutes. Continue? (yes/no)
```

---

## ⚙️ Configuration & Customization

### Agent Manager is Configured in `.claude/agents/manager.md`

You can customize:

**1. Quality Gate Thresholds**
```markdown
# Change test coverage requirement:
Before Dispatching Test Agent:
- [ ] Test coverage ≥ 80%  ← Change this to 85% or 90%
```

**2. Error Detection**
```markdown
# Change loop detection threshold:
Detect loop: Same task returned to IN_PROGRESS 3+ times  ← Change to 5
```

**3. Reporting Frequency**
```markdown
# Change how often Agent Manager reports:
Report progress: Every 30 minutes  ← Change to every hour
```

**4. Parallel vs Sequential**
```markdown
# Default behavior:
Process multiple tasks: in parallel  ← Change to sequential
```

Simply edit `.claude/agents/manager.md` and Agent Manager will use new configuration on next invocation.

---

## 🎓 Learning Path

### Week 1: Get Comfortable
**Day 1-2**: Single task, observe complete workflow
```
"You are the Agent Manager. Read your configuration from .claude/agents/manager.md and complete TASK-001"
```

**Day 3-4**: Multiple tasks sequentially
```
"You are the Agent Manager. Process all TODO tasks in priority order"
```

**Day 5**: Introduce intentional errors (test error handling)
- Create task with failing tests
- Observe Agent Manager dispatch fix
- Learn error recovery workflow

### Week 2: Production Usage
**Day 1-3**: Continuous management mode
```
"You are the Agent Manager. Manage all tasks continuously"
```

**Day 4-5**: Parallel processing
```
"You are the Agent Manager. Process all tasks in parallel"
```

### Week 3: Advanced
- Customize Agent Manager configuration
- Add custom quality gates
- Integrate with MCP (Jira/Confluence)
- Set up metrics tracking

---

## 🔍 Debugging & Troubleshooting

### Agent Manager Not Dispatching Next Agent

**Check:**
1. Previous agent updated `docs/tasks/dashboard.md` status?
   ```bash
   # Look at docs/tasks/dashboard.md
   # Verify status changed (e.g., TODO → IN_PROGRESS)
   ```

2. Quality gates met?
   ```bash
   # Agent Manager checks quality gates before dispatching
   # Example: Before Test Agent, review must be APPROVED
   ```

**Solution:**
```
"Agent Manager, check why TASK-001 is stuck. Show me the current status and what quality gate is not met."
```

### Agent Manager Keeps Looping

**Symptom**: Same task keeps going IN_REVIEW → IN_PROGRESS → IN_REVIEW...

**Agent Manager will auto-detect after 3 iterations and alert you.**

**Solution:**
1. Read the review reports to understand recurring issues
2. Might need manual intervention (requirements unclear)
3. Consider if task is too complex (break into smaller tasks)

### Want to Skip a Phase

**Example**: Code is simple, want to skip review

**Solution:**
```
"Agent Manager, for TASK-001, skip code review and go directly to testing"
```

Agent Manager will:
1. Manually update status IN_REVIEW → IN_TESTING
2. Dispatch Test Agent
3. Continue normal workflow

---

## 📈 Metrics & Analytics

### Agent Manager Tracks (Automatically)

**Per Task:**
- Time in each phase
- Number of review iterations
- Number of test failures
- Total time from TODO → DONE

**Across All Tasks:**
- Tasks completed per day/week
- Average time per task
- Review approval rate
- First-time test pass rate
- Bottleneck identification

**Request metrics:**
```
"Agent Manager, show me metrics for last week"

Response:
📊 Metrics (Last 7 Days)

Tasks Completed: 15
Average Time per Task: 45 minutes
Review Approval Rate: 87% (target: >80%) ✅
First-Time Test Pass: 73% (target: >80%) ⚠️
Bottleneck: Testing phase (avg 25 min) - Consider parallelizing tests

Top Issues:
1. Business rule tests failing (40% of failures) - Review SRS clarity
2. API schema validation (30% of failures) - Add more examples
```

---

## 🌟 Advanced Features

### Feature 1: Smart Prioritization

```
"Agent Manager, process all TODO tasks, prioritizing:
1. Critical bugs first
2. Then high-priority features
3. Then everything else"

Agent Manager will:
1. Categorize tasks by priority and type
2. Process in intelligent order
3. Report completion by category
```

### Feature 2: Conditional Workflows

```
"Agent Manager, for simple bug fixes (< 20 lines changed), skip code review and go straight to testing"

Agent Manager will:
1. Check git diff size after implementation
2. If < 20 lines, skip review phase
3. Otherwise, follow normal workflow
```

### Feature 3: Parallel Test Execution

```
"Agent Manager, when testing, run all test types in parallel instead of sequentially"

Agent Manager will:
1. Spawn multiple Test Agents (one per test type)
2. Run API, Integration, Business, E2E tests simultaneously
3. Aggregate results
4. Faster testing phase
```

---

## ✅ Best Practices

### 1. Start Simple
- Begin with single task
- Observe complete workflow
- Understand each phase
- Then scale to multiple tasks

### 2. Trust the Process
- Agent Manager handles quality gates
- Don't manually intervene unless asked
- Let workflow complete naturally

### 3. Review Metrics
- Ask for weekly metrics
- Identify bottlenecks
- Optimize accordingly

### 4. Customize Gradually
- Use default configuration first
- Identify pain points
- Customize configuration
- Test changes on single task

### 5. Use MCP Integration
- Pull tasks from Jira automatically
- Pull specs from Confluence
- Agent Manager can handle external inputs
- See `docs/MCP_SETUP.md`

---

## 🎯 Summary

### Without Agent Manager
```
User: Implement TASK-001
User: Review TASK-001
User: Test TASK-001
User: Document TASK-001
= 4 commands, ~1 hour of management time
```

### With Agent Manager
```
User: "Agent Manager, complete TASK-001"
[Agent Manager handles everything automatically]
= 1 command, 0 management time ✅
```

**Agent Manager transforms your multi-agent system from a manual workflow into a fully automated development pipeline!**

---

## 🚀 Get Started Now

```bash
cd "D:\01. PROJECTS\DEMO MULTIPLE AGENTS\template-ai-team"
claude
```

Then:
```
You are the Agent Manager (Project Manager). Read your configuration from .claude/agents/manager.md and complete TASK-001 from docs/tasks/dashboard.md
```

**That's it! Agent Manager handles the rest! 🎉**

---

**Questions? Check:**
- `.claude/agents/manager.md` - Agent Manager configuration
- `.claude/agents/README.md` - Agent usage guide
- `AGENT_CONFIGURATION_GUIDE.md` - Complete setup guide

**Happy automating! 🤖**

---

**Last Updated**: 2026-01-23
**Agent**: Agent Manager (Project Manager)
**Status**: ✅ Production Ready
**Automation Level**: 95% (fully automated workflow)
