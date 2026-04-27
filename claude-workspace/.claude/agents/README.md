# Agent Configuration Guide

This directory contains configuration files for the 4 specialized agents in the multi-agent development workflow.

## Available Agents

### 0. Agent Manager (Project Manager) ⭐ **NEW**
**File**: `manager.md`
**Role**: **Automatically orchestrate the entire workflow**
**Triggered**: User invokes once, manages everything
**Output**: Complete task from TODO → DONE automatically

**THIS IS THE RECOMMENDED APPROACH** - Use Agent Manager to automate everything!

### 1. Code Implementation Agent
**File**: `code-implementation.md`
**Role**: Implement features and fix bugs
**Triggered**: When task status is "TODO" or "IN_PROGRESS"
**Output**: Code changes, unit tests, handoff to Code Review

### 2. Code Review Agent
**File**: `code-review.md`
**Role**: Review code quality, security, and standards
**Triggered**: When task status is "IN_REVIEW"
**Output**: Review report, decision (APPROVED or CHANGES_REQUESTED)

### 3. Test Agent
**File**: `test.md`
**Role**: Create and execute all automated tests
**Triggered**: When task status is "IN_TESTING"
**Output**: Test report, bug reports (if failures), decision (PASS or FAIL)

### 4. Documentation Agent
**File**: `documentation.md`
**Role**: Update all project documentation
**Triggered**: When task status is "DOCUMENTING"
**Output**: Updated documentation, task marked "DONE"

---

## How to Use Agents

### Method 0: Agent Manager - FULLY AUTOMATED ⭐ **RECOMMENDED**

**This is the easiest and most powerful way to use the multi-agent system!**

**Start a Claude Code session and invoke the Agent Manager:**

```bash
claude

# Then in the chat:
"You are the Agent Manager (Project Manager). Read your configuration from .claude/agents/manager.md and complete TASK-001 from docs/tasks/dashboard.md"
```

**The Agent Manager will:**
1. ✅ Read TASK-001 from docs/tasks/dashboard.md (status: TODO)
2. ✅ Automatically dispatch Code Implementation Agent
3. ✅ Wait for implementation to complete
4. ✅ Automatically dispatch Code Review Agent
5. ✅ Wait for review to complete
6. ✅ If approved, automatically dispatch Test Agent
7. ✅ If all tests pass, automatically dispatch Documentation Agent
8. ✅ Report when TASK-001 is DONE

**You just need ONE command!** The Agent Manager handles everything else.

**For continuous management:**
```
"You are the Agent Manager. Read your configuration from .claude/agents/manager.md and manage all tasks in docs/tasks/dashboard.md continuously until I say stop"
```

Agent Manager will:
- Process all TODO tasks
- Handle all tasks in progress
- Run complete workflows automatically
- Report progress periodically
- Ask before continuing to next batch

---

### Method 1: Manual Agent Invocation (For Learning/Debugging)

**Start a Claude Code session and explicitly tell it which agent to use:**

```bash
# Example: Starting with Code Implementation
claude

# Then in the chat:
"You are the Code Implementation Agent. Please read your configuration from .claude/agents/code-implementation.md and implement TASK-001 from docs/tasks/dashboard.md"
```

**After implementation is complete:**
```bash
# Switch to Code Review Agent
"You are now the Code Review Agent. Please read your configuration from .claude/agents/code-review.md and review the changes for TASK-001"
```

**Continue through the workflow:**
```
Code Implementation → Code Review → Test → Documentation
```

### Method 2: Using Task Tool to Spawn Agents (Advanced)

**In Claude Code, you can spawn specialized agents using the Task tool with model optimization:**

```markdown
# Example: Spawn Code Implementation Agent
Use Task tool with:
- subagent_type: "general-purpose"
- model: "sonnet"
- prompt: "You are the Code Implementation Agent. Read your configuration from .claude/agents/code-implementation.md. Implement TASK-001 from docs/tasks/dashboard.md following all guidelines in your configuration."
```

Each agent declares its recommended model at the top of its `.md` file. See PROJECT.md `Agent Model Configuration` section for the full model assignment table and per-project overrides.

**The spawned agent will:**
1. Read its configuration from `.claude/agents/code-implementation.md`
2. Read the task from `docs/tasks/dashboard.md`
3. Execute according to its role and responsibilities
4. Update task status when done
5. Return control to you

### Method 3: Sequential Workflow (Full Automation)

**Create a workflow file that spawns agents in sequence:**

```markdown
# docs/workflows/feature-development.md

## Workflow: Full Feature Development

1. Spawn Code Implementation Agent
   - Task: Implement feature from docs/tasks/dashboard.md
   - Exit condition: Task status = "IN_REVIEW"

2. Spawn Code Review Agent
   - Task: Review code changes
   - Exit condition: Review decision made (APPROVED or CHANGES_REQUESTED)
   - If CHANGES_REQUESTED: Return to step 1

3. Spawn Test Agent (only if review APPROVED)
   - Task: Create and execute all tests
   - Exit condition: All tests pass or bug report created
   - If tests fail: Return to step 1

4. Spawn Documentation Agent (only if all tests pass)
   - Task: Update all documentation
   - Exit condition: Task status = "DONE"

COMPLETE: Feature fully implemented, reviewed, tested, and documented
```

---

## Agent Configuration Files Explained

### What's in Each Agent File?

Each agent configuration file (`.md`) contains:

**1. Role Definition**: What this agent does
**2. Core Responsibilities**: Step-by-step tasks
**3. Token Optimization Rules**: How to save tokens (critical!)
**4. Quality Gates**: Checklist before moving to next phase
**5. Tools Allowed**: Which tools this agent can use
**6. Example Workflow**: Complete walkthrough
**7. Error Handling**: What to do when things go wrong

### How Agents Use These Files

When you tell Claude Code:
```
"You are the Code Implementation Agent. Read your configuration from .claude/agents/code-implementation.md"
```

Claude will:
1. Read the entire `.md` file
2. Adopt the role and responsibilities defined in it
3. Follow the guidelines and quality gates
4. Use the tools specified
5. Execute the example workflow

**Think of these files as "system prompts" for specialized agents.**

---

## Agent Communication Flow

```
┌──────────────────────────────────────────────────────┐
│  CODE IMPLEMENTATION AGENT                           │
│  - Implements feature                                │
│  - Writes unit tests                                 │
│  - Creates: docs/tasks/TASK-ID/handoff/              │
│             implementation-to-review.md              │
│  - Updates task status: "IN_REVIEW"                  │
└────────────────┬─────────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────────┐
│  CODE REVIEW AGENT                                   │
│  - Reviews code changes                              │
│  - Checks standards & security                       │
│  - Creates: docs/tasks/TASK-ID/handoff/              │
│             review-report.md                         │
│  - Decision: APPROVED or CHANGES_REQUESTED           │
│  - Updates task status: "IN_TESTING" or "IN_PROGRESS"│
└────────────────┬─────────────────────────────────────┘
                 │ (if APPROVED)
                 ▼
┌──────────────────────────────────────────────────────┐
│  TEST AGENT                                          │
│  - Creates all test types (API, Integration, etc.)  │
│  - Executes tests in priority order                 │
│  - Creates: docs/tasks/TASK-ID/deliveries/           │
│             test-reports/test-report.md              │
│  - If fail: bugs/ inside test-reports/               │
│  - Updates task status: "DOCUMENTING" or "IN_PROGRESS│
└────────────────┬─────────────────────────────────────┘
                 │ (if ALL tests pass)
                 ▼
┌──────────────────────────────────────────────────────┐
│  DOCUMENTATION AGENT                                 │
│  - Updates: docs/tasks/TASK-ID/deliveries/api-specs/ │
│  - Updates: docs/tasks/TASK-ID/deliveries/           │
│             final-specs/                             │
│  - Updates README.md (if needed)                     │
│  - Commits documentation                             │
│  - Updates task status: "DONE"                       │
└──────────────────────────────────────────────────────┘
```

**All documents are organized per-task under `docs/tasks/TASK-ID/`:**
- `docs/tasks/dashboard.md` - Dashboard (auto-generated index)
- `docs/tasks/TASK-ID/task.md` - Task definition (YAML frontmatter)
- `docs/tasks/TASK-ID/refs/` - Requirements, implementation plan
- `docs/tasks/TASK-ID/handoff/` - Agent handoffs + review reports
- `docs/tasks/TASK-ID/bugs/` - Bug reports (intermediate, during testing cycle)
- `docs/tasks/TASK-ID/deliveries/test-cases/` - Test scenarios
- `docs/tasks/TASK-ID/deliveries/test-reports/` - Test results + screenshots
- `docs/tasks/TASK-ID/deliveries/api-specs/` - API specifications
- `docs/tasks/TASK-ID/deliveries/sql-scripts/` - SQL scripts (DDL, config)
- `docs/tasks/TASK-ID/deliveries/final-specs/` - Detailed design docs

---

## Best Practices

### 1. Always Specify Agent Configuration
✅ **GOOD**: "You are the Code Implementation Agent. Read your configuration from .claude/agents/code-implementation.md"
❌ **BAD**: "Implement this feature" (unclear which agent, no configuration)

### 2. One Agent at a Time
- Don't mix agent roles in a single session
- Complete one phase before moving to next
- Example: Finish implementation completely before starting review

### 3. Follow the Quality Gates
- Each agent has a checklist before proceeding
- Don't skip quality gates (they prevent bugs downstream)
- Example: Code Implementation must have 80%+ test coverage before review

### 4. Use Token-Efficient Operations
- All agents have "Token Optimization Rules" sections
- Follow these rules strictly (logs/diffs can consume massive tokens)
- Example: Use `mvn test -q` not `mvn test` (quiet mode)

### 5. Update docs/tasks/dashboard.md Frequently
- Task status is the coordination mechanism
- Update status when transitioning between agents
- Example: "IN_PROGRESS" → "IN_REVIEW" → "IN_TESTING" → "DOCUMENTING" → "DONE"

---

## Troubleshooting

### "Agent not following configuration"
**Solution**: Explicitly reference the configuration file in your prompt:
```
"You are the Code Implementation Agent. Read and follow ALL guidelines from .claude/agents/code-implementation.md. Start by reading that file now."
```

### "Agent skipping quality gates"
**Solution**: Remind the agent of the quality gates:
```
"Before proceeding to IN_REVIEW status, verify ALL quality gates from your configuration are met. List each one."
```

### "Agent using too many tokens"
**Solution**: Reference the token optimization section:
```
"Follow the Token Optimization Rules from your configuration. Use -q flags and dedicated tools (Read/Grep/Glob), not bash shortcuts."
```

### "Agents not communicating properly"
**Solution**: Check that agents are updating task status and creating handoff files:
```
"Before finishing, verify you've:
1. Updated task status via /task-status TASK-ID STATUS
2. Created handoff file in docs/tasks/TASK-ID/handoff/
3. Documented any blockers or issues"
```

---

## Example: Complete Workflow Session

```bash
# Start Claude Code
claude

# Phase 1: Implementation
User: "You are the Code Implementation Agent. Read your configuration from .claude/agents/code-implementation.md and implement TASK-001 from docs/tasks/dashboard.md"

Agent: [Reads config, reads task, implements feature, writes tests, updates docs/tasks/dashboard.md to "IN_REVIEW", creates handoff]

# Phase 2: Code Review
User: "You are now the Code Review Agent. Read your configuration from .claude/agents/code-review.md and review TASK-001"

Agent: [Reads config, reviews code, creates review report, updates docs/tasks/dashboard.md to "IN_TESTING" (if approved)]

# Phase 3: Testing
User: "You are now the Test Agent. Read your configuration from .claude/agents/test.md and test TASK-001"

Agent: [Reads config, creates tests, executes tests, creates test report, updates docs/tasks/dashboard.md to "DOCUMENTING" (if all pass)]

# Phase 4: Documentation
User: "You are now the Documentation Agent. Read your configuration from .claude/agents/documentation.md and document TASK-001"

Agent: [Reads config, updates API docs, updates feature docs, commits, updates docs/tasks/dashboard.md to "DONE"]

# COMPLETE!
```

---

## Advanced: Parallel Workflows

You can run multiple features in different phases simultaneously:

```
Time  | Implementation | Code Review | Test Agent    | Documentation
------|----------------|-------------|---------------|---------------
T1    | Feature A      | -           | -             | -
T2    | Feature B      | Feature A   | -             | -
T3    | Feature C      | Feature B   | Feature A     | -
T4    | Feature D      | Feature C   | Feature B     | Feature A
```

**How**: Use separate Claude Code sessions or spawn agents in parallel using Task tool.

**Coordination**: `docs/tasks/dashboard.md` shows status of all features.

---

## Need Help?

**Questions about:**
- **Agent roles**: Read `.claude/agents/[agent-name]-agent.md` (detailed guides)
- **Configuration**: Read this file (`.claude/agents/README.md`)
- **Workflow**: Read `MULTI_AGENT_ORCHESTRATION.md`
- **Tools**: Read `.claude/SETTINGS_README.md`

**Want to customize agents?**
- Edit the `.md` files in `.claude/agents/`
- Add new responsibilities, tools, or quality gates
- Agents will follow the updated configuration

---

**Last Updated**: 2026-02-12
**Agent Files**: 5 (code-implementation.md, code-review.md, test.md, documentation.md, manager.md)
**Status**: ✅ Ready for use (with model tiering since v1.8.0)
