# Comprehensive Slash Commands Guide for Multi-Agent Teams

**For**: Multi-Agent Development (any tech stack)
**Last Updated**: 2026-02-11

---

## Table of Contents

1. [Overview](#overview)
2. [Your Custom Commands (Already Configured)](#your-custom-commands-already-configured)
3. [New Custom Skills (Recommended)](#new-custom-skills-recommended)
4. [Standard Claude Code Commands](#standard-claude-code-commands)
5. [Agent-Specific Command Workflows](#agent-specific-command-workflows)
6. [Best Practices](#best-practices)
7. [Quick Reference Cheat Sheet](#quick-reference-cheat-sheet)

---

## Overview

This guide provides comprehensive documentation on slash commands available for your multi-agent development team. Commands are tech-agnostic and auto-detect your project's stack from PROJECT.md.

### Command Priority Hierarchy

```
┌─────────────────────────────────────────────┐
│  CUSTOM SKILLS (Most Specific)              │
│  /auto-build, /task-status, /handoff        │
│  /complete-task, /dev-task, /review-code     │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  YOUR CONFIGURED COMMANDS                    │
│  /init, /review, /pr-comments               │
│  /statusline                                 │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  STANDARD CLAUDE CODE COMMANDS              │
│  /run, /test, /diff, /commit, /git          │
└─────────────────────────────────────────────┘
```

---

## Your Custom Commands (Already Configured)

### 1. `/project-setup` - Interactive Project Initialization ⭐ **NEW**
**Purpose**: Initialize a new project from the AI Team Template with guided setup
**Usage**:
- `/project-setup` - Interactive mode with step-by-step guidance
- `/project-setup --quick` - Quick setup with defaults (2-3 minutes)
- `/project-setup --full` - Comprehensive setup with all options (10-15 minutes)

**What it does**:
- ✅ Guides through PROJECT.md customization (replaces template placeholders)
- ✅ Sets up docs/ folder structure
- ✅ Configures MCP servers (Jira, Confluence, MariaDB) - optional
- ✅ Initializes Git repository
- ✅ Configures Claude Code settings
- ✅ Creates initial tasks in docs/tasks/dashboard.md
- ✅ Validates setup and provides summary

**When to use**:
- **First time setting up a new project from this template** (REQUIRED)
- Onboarding new team members
- Re-initializing project configuration after template updates

**Team workflow**:
1. Project Leader clones template repository
2. Runs `/project-setup` to customize for actual project
3. Answers interactive prompts (project name, tech stack, architecture, MCP setup)
4. Reviews generated configuration and tasks
5. Team starts development with pre-configured agents

**Token savings**: ~300 tokens + 15 tool calls vs manual setup
**Time savings**: Reduces onboarding from 1+ hours to 2-10 minutes

**Complete guide**: [.claude/skills/project-setup.md](../.claude/skills/project-setup.md)

**Note**: The existing `/init` command (generates CLAUDE.md from codebase) remains available for analyzing project structure.

---

### 2. `/review` - Review a Pull Request
**Purpose**: Automated code review using Claude's analysis
**Usage**: `/review TASK-001` or `/review pr/123`
**When to use**:
- Code Review Agent reviewing implementation
- Security Review Agent checking for vulnerabilities

**Best practice**:
- Code Review Agent uses this for automated analysis
- Still performs detailed review using checklist in `.claude/agents/code-review.md`
- Use alongside Code Review Agent's manual review

---

### 3. `/pr-comments` - Get GitHub PR Comments
**Purpose**: Extract comments from GitHub pull requests
**Usage**: `/pr-comments TASK-001` or `/pr-comments pr/456`
**When to use**:
- Code Review Agent needs to review external PR comments
- Understanding reviewer feedback
- Collecting requirements from PR discussions

**Team integration**:
- Use if team uses GitHub PRs alongside Claude Code
- Extract comments and summarize in `docs/reviews/` for markdown-based workflow

---

### 4. `/statusline` - Set Up Status Line UI
**Purpose**: Configure Claude Code's status line display
**Usage**: `/statusline show` or `/statusline configure`
**When to use**:
- Setting up your development environment
- Displaying current task status while working
- Showing active agent during multi-agent workflows

**Multi-agent usage**: Shows which agent is currently active

---

## New Custom Skills (Recommended)

### 1. `/auto-build` - Universal Build, Test & Lint

**Purpose**: Auto-detect tech stack from PROJECT.md and run build/test/lint commands with token-efficient output

**Available Commands**:
```bash
/auto-build build         # Build the project
/auto-build test          # Run all tests (quiet output)
/auto-build test-unit     # Run unit tests only
/auto-build lint          # Run linter/formatter check
/auto-build check         # Quick compile/type-check
/auto-build run           # Start dev server
/auto-build clean         # Clean build artifacts
/auto-build install       # Install dependencies
```

**Token Efficiency**:
- ✅ Auto-detects tech stack (Maven, Gradle, npm, Python, Go, Rust, .NET)
- ✅ Uses quiet flags automatically (`-q`, `--silent`, etc.)
- ✅ Generates reusable `scripts/project-build.sh` (or `.cmd`) on first run
- ✅ Saves ~1800-2900 tokens per build vs raw commands

**How It Works**:
1. First run: Reads PROJECT.md to detect tech stack
2. Generates `scripts/project-build.sh` + `scripts/project-build.cmd`
3. Subsequent runs: Reuses generated script (instant)

**Agent Usage**:
- **Code Implementation**: `check`, `test`, `lint`
- **Code Review**: `check`, `test`, `lint`
- **Test Agent**: `test`, `test-unit`

**Example Workflow**:
```bash
# Code Implementation Agent
/auto-build check     # Quick syntax/type check
/auto-build test      # Run full test suite
/auto-build lint      # Verify code style
```

**Supported Tech Stacks**: Maven, Gradle, npm/yarn/pnpm, pip/poetry, Go, Rust/Cargo, .NET

**Complete guide**: [.claude/skills/auto-build/SKILL.md](../.claude/skills/auto-build/SKILL.md)

---

### 2. `/complete-task` - Full Task Automation

**Purpose**: Orchestrate complete multi-agent workflow to finish task from TODO to DONE automatically

**Available Commands**:
```bash
/complete-task TASK-001               # Complete single task end-to-end
/complete-task TASK-001 --parallel    # Allow parallel with other tasks
/complete-task --all                  # Complete all TODO tasks sequentially
/complete-task --all --parallel       # Complete all tasks in parallel
```

**Token Efficiency**:
- ✅ Saves **~39,500 tokens per task** (98.75% reduction)
- ✅ Agent Manager runs in main context (~500 tokens)
- ✅ Agents run in isolated contexts (don't consume main tokens)
- ✅ Zero manual intervention needed

**Complete Automation**:
```
User runs: /complete-task TASK-001

Agent Manager automatically orchestrates:

[1/4] Code Implementation Phase
      ├─ Spawns Code Implementation Agent
      ├─ Implements feature + unit tests
      ├─ Commits to feature branch
      └─ Status: TODO → IN_REVIEW

[2/4] Code Review Phase
      ├─ Spawns Code Review Agent
      ├─ Reviews code changes
      ├─ Creates review report
      └─ Status: IN_REVIEW → IN_TESTING (if approved)

[3/4] Testing Phase
      ├─ Spawns Test Agent
      ├─ Creates API/integration/business rule tests
      ├─ Executes all tests (100% pass required)
      └─ Status: IN_TESTING → DOCUMENTING (if all pass)

[4/4] Documentation Phase
      ├─ Spawns Documentation Agent
      ├─ Updates API docs + feature docs
      ├─ Commits documentation
      └─ Status: DOCUMENTING → DONE

🎉 Task complete! (typically 6-15 minutes)
```

**Quality Gates Enforced**:
- ✅ Code must compile and pass unit tests
- ✅ Code review must APPROVE (or loop back to fix)
- ✅ ALL tests must PASS 100% (or loop back to fix)
- ✅ Documentation must be updated before DONE

**Agent Usage**:
- **Agent Manager**: Orchestrates the full workflow
- **Project Leaders**: Batch complete sprint tasks
- **All roles**: Fully automated task execution

**Example Workflows**:
```bash
# Sprint start: Import from Jira + Complete all
/jira-task --project PROJ
/complete-task --all --parallel
# Come back in 2 hours - all tasks done! ☕

# Single task completion
/complete-task TASK-001
# Output: 🎉 TASK-001 complete in 8m 32s

# Resume incomplete task
/complete-task TASK-003  # Resumes from current phase
```

**Error Handling**:
- Detects review rejection loops (max 3 iterations)
- Detects test failure loops (max 2 iterations)
- Handles agent timeouts gracefully
- Reports metrics and bottlenecks

**Metrics Tracked**:
- Total time per task
- Time per phase (implementation, review, testing, docs)
- Review iterations (goal: ≤ 1)
- Test pass rate (goal: 100%)
- Bottleneck identification

**Complete guide**: [.claude/skills/complete-task/SKILL.md](../.claude/skills/complete-task/SKILL.md)

---

### 3. `/jira-task` - Fetch Tasks from Jira

**Purpose**: Import task details from Jira using MCP and create task entry in docs/tasks/dashboard.md

**Available Commands**:
```bash
/jira-task PROJ-456                   # Fetch single task from Jira
/jira-task 456                        # Use default project from JIRA_PROJECT_KEY env var
/jira-task --project PROJ             # Fetch all tasks from project
/jira-task --jql "status = 'To Do'"   # Fetch tasks with JQL query
/jira-task PROJ-456 --task-id TASK-100  # Use custom task ID
```

**Token Efficiency**:
- ✅ Single command vs 6 manual steps
- ✅ Saves ~1,550 tokens per task import
- ✅ Auto-converts Jira format to markdown
- ✅ Auto-generates task ID, branch name

**Hybrid MCP Approach**:
- **INPUT**: Reads from Jira via MCP (one-time)
- **OUTPUT**: Saves to `docs/tasks/dashboard.md` for tracking
- **NO SYNC**: All progress tracked locally, NOT in Jira

**Agent Usage**:
- **Agent Manager**: Batch import tasks at sprint start
- **Code Implementation**: Import individual tasks as needed
- **All Agents**: Track progress in `docs/tasks/dashboard.md` (not Jira)

**Example Workflow**:
```bash
# Sprint start: Import all tasks
/jira-task --project PROJ

# Output: Created 15 tasks from PROJ:
# - TASK-001 to TASK-010 (10 stories)
# - BUG-001 to BUG-003 (3 bugs)
# - EPIC-001 to EPIC-002 (2 epics)

# Individual task import
/jira-task PROJ-456
# Output: Created TASK-011 from PROJ-456

# Start work
/task-status TASK-011 IN_PROGRESS
```

**Configuration** (Optional):
```bash
# Set default project key to use shorthand
export JIRA_PROJECT_KEY="PROJ"

# Then use:
/jira-task 456  # Instead of /jira-task PROJ-456
```

**Requires**:
- Jira MCP server configured in `.mcp.json`
- Environment variables: `JIRA_URL`, `JIRA_EMAIL`, `JIRA_TOKEN`
- Optional: `JIRA_PROJECT_KEY` for default project

**Complete guide**: [.claude/skills/jira-task/SKILL.md](../.claude/skills/jira-task/SKILL.md)

---

### 4. `/update-jira-task` - Sync Status Back to Jira

**Purpose**: Update Jira issue with current task status and progress summary (reverse sync)

**Available Commands**:
```bash
/update-jira-task TASK-001            # Update single task to Jira
/update-jira-task --all               # Sync all changed tasks
/update-jira-task --done              # Sync only completed tasks
/update-jira-task --status IN_REVIEW  # Sync all tasks with specific status
/update-jira-task TASK-001 --force    # Force update even if unchanged
```

**Token Efficiency**:
- ✅ Saves manual UI work (5-10 min per task)
- ✅ Uses ~300 tokens per sync
- ✅ Extracts summaries automatically
- ✅ Batch updates multiple tasks efficiently

**Bidirectional Sync Flow**:
```
┌──────────────────────────────────────┐
│  /jira-task (Import)                 │
│  Jira → docs/tasks/dashboard.md                │
│  Read requirements from Jira         │
└──────────────────────────────────────┘
              ↓
    Work tracked locally
    in docs/tasks/dashboard.md
              ↓
┌──────────────────────────────────────┐
│  /update-jira-task (Sync Back)       │
│  docs/tasks/dashboard.md → Jira                │
│  Update Jira with progress           │
└──────────────────────────────────────┘
```

**What Gets Updated in Jira**:
- **Status**: Syncs from local status (TODO → In Progress, etc.)
- **Comment**: Auto-generated summary with:
  - Implementation details (commits, files changed)
  - Review results (APPROVED/CHANGES_REQUESTED)
  - Test results (pass rate, test counts)
  - Deliverables (code, tests, docs)
  - Links to artifacts (review reports, test reports)
- **Labels**: Optional "ai-team-template" label
- **Progress**: Optional progress percentage field

**Status Mapping**:
| Local Status | Jira Status |
|--------------|-------------|
| TODO | To Do |
| IN_PROGRESS | In Progress |
| IN_REVIEW | In Review |
| IN_TESTING | In Testing |
| DONE | Done |
| BLOCKED | Blocked |

**Agent Usage**:
- **All Agents**: Update Jira at milestones
- **Documentation Agent**: Final sync when marking DONE
- **Project Leaders**: Batch sync before sprint reviews

**Example Workflows**:
```bash
# Single task sync
/complete-task TASK-001
/update-jira-task TASK-001
# Jira updated: To Do → Done
# Comment: "Task completed. 25 tests, 100% pass rate."

# Sprint review preparation
/update-jira-task --done
# Syncs all completed tasks to Jira
# Stakeholders see latest status

# Incremental updates
/task-status TASK-001 IN_REVIEW
/update-jira-task TASK-001
# Jira: In Progress → In Review
# Comment: "Implementation complete, ready for review"
```

**Auto-Generated Comments**:

For DONE tasks:
```
✅ Task completed in AI Team Template

Summary:
- Time: 8m 32s
- Review: APPROVED (1 iteration)
- Tests: 100% PASS (50 tests total)

Deliverables:
- Code: 5 files, 450 lines added
- Tests: 25 unit, 15 API, 10 business rule tests
- Documentation: API docs + feature guide

Git: feature/task-001-user-profile-api (3 commits)

Generated by: Claude AI Team Template
```

**Configuration** (Optional):
```bash
# Custom status mappings for your Jira workflow
export JIRA_STATUS_IN_PROGRESS="Development"
export JIRA_STATUS_IN_REVIEW="Peer Review"
export JIRA_STATUS_DONE="Released"

# Field updates
export JIRA_ADD_LABEL=true              # Add "ai-team-template" label
export JIRA_UPDATE_PROGRESS=true        # Update progress field

# Artifact linking
export JIRA_LINK_ARTIFACTS=true
export JIRA_ARTIFACT_BASE_URL="https://github.com/org/repo"
```

**Requires**:
- Jira MCP server configured (same as /jira-task)
- JIRA_TOKEN with write permissions
- Tasks linked to Jira issues in docs/tasks/dashboard.md

**Complete guide**: [.claude/skills/update-jira-task/SKILL.md](../.claude/skills/update-jira-task/SKILL.md)

---

### 5. `/publish-confluence` - Generate Documentation in Confluence

**Purpose**: Generate comprehensive documentation from task artifacts and publish to Confluence

**Available Commands**:
```bash
/publish-confluence TASK-001            # Generate and publish task documentation
/publish-confluence --all-done          # Publish all completed tasks
/publish-confluence TASK-001 --update   # Update existing page
/publish-confluence TASK-001 --space PROJ --parent "API Docs"  # Specific location
```

**Token Efficiency**:
- ✅ Saves 30-60 minutes manual documentation work
- ✅ Uses ~800-1,300 tokens per publish
- ✅ Automatically formats for Confluence
- ✅ Generates professional, comprehensive docs

**Documentation Generation Flow**:
```
Local Artifacts (docs/ folder)
├─ docs/tasks/dashboard.md (task details)
├─ docs/api/ (API documentation)
├─ docs/features/ (feature guides)
├─ docs/reviews/ (code review reports)
├─ docs/test-reports/ (test results)
└─ Code examples (from implementation)
        ↓
  /publish-confluence generates
        ↓
Confluence Page with:
├─ 1. Overview & Requirements
├─ 2. API Documentation (endpoints, examples)
├─ 3. Implementation Details (schema, business rules)
├─ 4. Code Examples (Java, JavaScript, etc.)
├─ 5. Test Results (tables with pass/fail rates)
├─ 6. Code Review Summary (decision, checklist)
└─ 7. Related Links (Jira, Git, local docs)
```

**Generated Page Includes**:
- **Overview Section**: Task info, requirements, completion status
- **API Documentation**: Endpoints, request/response examples, error codes
- **Implementation Details**: Database schema, business rules, architecture
- **Code Examples**: Syntax-highlighted snippets (Java, JavaScript, SQL)
- **Test Results**: Formatted tables with pass rates and coverage
- **Review Summary**: Code review decision, checklist, issues found
- **Related Links**: Jira, Git branch, PR, local artifact links

**Confluence Features Used**:
- Status macros (green badges for passed tests)
- Code blocks with syntax highlighting
- Info/warning panels for important notes
- Tables for structured data
- Page hierarchy and parent pages
- Labels and metadata

**Agent Usage**:
- **Documentation Agent**: Auto-publish after finalizing docs
- **Project Leaders**: Publish sprint documentation
- **All roles**: Share comprehensive docs with stakeholders

**Example Workflow**:
```bash
# Single task documentation
/complete-task TASK-001
/publish-confluence TASK-001

# Output:
# ✅ Published to Confluence
# Title: "User Profile API - Implementation Documentation"
# URL: https://confluence.vissoft.vn/display/PROJ/User+Profile+API
# Sections: 7 (Overview, API, Implementation, Examples, Tests, Review, Links)
# Parent: API Documentation

# Sprint documentation release
/complete-task --all --parallel
/publish-confluence --all-done --space PROJ

# Result: 10 Confluence pages published with complete documentation
```

**Page Organization**:
```
PROJ (Confluence Space)
├── API Documentation (Parent)
│   ├── User Profile API - Implementation Docs
│   ├── Login API - Implementation Docs
│   └── Search API - Implementation Docs
├── Feature Documentation (Parent)
│   └── Dashboard Feature Guide
└── Bug Fixes (Parent)
    └── Login Bug Fix - Resolution Docs
```

**Configuration** (Optional):
```bash
# Confluence connection (same as MCP)
CONFLUENCE_URL=https://confluence.vissoft.vn
CONFLUENCE_TOKEN=your-token-here

# Default organization
CONFLUENCE_DEFAULT_SPACE="PROJ"
CONFLUENCE_PARENT_API_DOCS="API Documentation"
CONFLUENCE_PARENT_FEATURES="Feature Documentation"

# Auto-create parent pages if missing
CONFLUENCE_AUTO_CREATE_PARENTS=true

# Add labels to pages
CONFLUENCE_ADD_LABELS=true
CONFLUENCE_LABELS="ai-team-template,automated-docs"

# Link to GitHub/GitLab
CONFLUENCE_LINK_GITHUB=true
CONFLUENCE_GITHUB_BASE_URL="https://github.com/org/repo"
```

**Full Integration Example**:
```bash
# Complete workflow with full documentation
/jira-task PROJ-456                 # Import from Jira
/complete-task TASK-001             # Complete automatically
/update-jira-task TASK-001          # Update Jira status
/publish-confluence TASK-001        # Publish to Confluence

# Result:
# ✅ Task complete
# ✅ Jira updated with status + summary
# ✅ Confluence published with full documentation
# All stakeholders have complete visibility! 🎉
```

**Requires**:
- Confluence MCP server configured
- CONFLUENCE_TOKEN with write permissions
- Documentation artifacts in docs/ folder

**Complete guide**: [.claude/skills/publish-confluence/SKILL.md](../.claude/skills/publish-confluence/SKILL.md)

---

### 6. `/task-status` - Update Task Progress

**Purpose**: Update task status in docs/tasks/dashboard.md for multi-agent coordination

**Available Status Values**:
```bash
/task-status TASK-001 TODO           # Initial state
/task-status TASK-001 IN_PROGRESS    # Implementation working
/task-status TASK-001 IN_REVIEW      # Code review reviewing
/task-status TASK-001 IN_TESTING     # Test agent testing
/task-status TASK-001 DOCUMENTING    # Documentation updating
/task-status TASK-001 DONE           # Complete
/task-status TASK-001 BLOCKED        # Blocked (with reason)
```

**Workflow State Transitions**:
```
TODO → IN_PROGRESS → IN_REVIEW → IN_TESTING → DOCUMENTING → DONE

Rejection paths:
IN_REVIEW → IN_PROGRESS (changes requested)
IN_TESTING → IN_PROGRESS (tests failed)
```

**Token Efficiency**:
- ✅ Single command vs multiple Edit calls
- ✅ Saves ~120 tokens per status update
- ✅ Automatic timestamp and agent assignment

**Agent Usage**:
- **Code Implementation**: `IN_PROGRESS`, `IN_REVIEW`
- **Code Review**: `IN_TESTING` (approved) or `IN_PROGRESS` (changes)
- **Test Agent**: `DOCUMENTING` (pass) or `IN_PROGRESS` (fail)
- **Documentation**: `DONE`
- **Agent Manager**: All transitions

**Example Workflow**:
```bash
# Code Implementation Agent
/task-status TASK-001 IN_PROGRESS    # Start work
# ... implement feature ...
/task-status TASK-001 IN_REVIEW      # Ready for review

# Code Review Agent
/task-status TASK-001 IN_TESTING     # Approved

# Test Agent
/task-status TASK-001 DOCUMENTING    # All tests pass

# Documentation Agent
/task-status TASK-001 DONE           # Complete
```

---

### 7. `/handoff` - Create Agent Handoff Document

**Purpose**: Generate handoff summary for next agent in workflow

**Usage**:
```bash
/handoff TASK-001 "to:code-review" "Implementation complete with 25 unit tests"
/handoff TASK-001 "to:test" "Code review approved, all standards met"
/handoff TASK-001 "to:documentation" "All tests passed (25/25)"
/handoff TASK-001 "to:implementation" "Changes requested: Add input validation"
```

**Available Targets**:
- `to:code-review` - From Implementation to Review
- `to:test` - From Review to Testing
- `to:documentation` - From Testing to Documentation
- `to:implementation` - From Review/Testing back to Implementation

**Token Efficiency**:
- ✅ Auto-generates structured handoff documents
- ✅ Saves ~450 tokens per handoff
- ✅ Consistent format across all handoffs

**Generated Content**:
- Task summary and metadata
- What was completed (code, tests, database)
- Git information (branch, commits, files changed)
- What to review/test/document (checklists)
- Special notes and considerations
- Next steps for receiving agent

**Example Workflow**:
```bash
# Code Implementation Agent
/task-status TASK-001 IN_REVIEW
/handoff TASK-001 "to:code-review" "User profile API complete, 5 endpoints, 25 tests"

# Code Review Agent (after review)
/task-status TASK-001 IN_TESTING
/handoff TASK-001 "to:test" "Code review APPROVED. No security issues found."

# Test Agent (after testing)
/task-status TASK-001 DOCUMENTING
/handoff TASK-001 "to:documentation" "All tests PASSED (25/25). API validated."
```

**Files Created**: `docs/handoffs/TASK-XXX-to-[agent]-[timestamp].md`

---

## Standard Claude Code Commands

### Core Navigation & Context

#### `/help` or `?`
Display help information and available commands
```bash
/help
```

#### `/codebase` or `/context`
Understand codebase structure and context
```bash
/codebase
```

#### `/file` or `/read`
Read specific files for analysis
```bash
/file src/main/java/com/example/controller/UserController.java
```

#### `/search` or `/find`
Search for files, functions, or patterns
```bash
/search UserService
```

---

### Execution & Testing

#### `/run` or `/execute`
Execute bash commands (use custom skills instead when available)
```bash
# ❌ Token-wasteful
/run mvn clean install

# ✅ Token-efficient (use custom skill)
/auto-build build
```

#### `/test`
Run tests with specialized handling
```bash
/test UserControllerTest.java
/test UserService
```

---

### Code Analysis & Review

#### `/analyze` or `/lint`
Run linting and code analysis
```bash
/analyze
```

#### `/diff`
Show code changes in current branch
```bash
/diff master..feature/user-profile
```

---

### Git & Version Control

#### `/git` or `/branch`
Git operations
```bash
/git status
/git log --oneline -10
/git diff
```

#### `/commit`
Create commits with messages
```bash
/commit "feat: add user profile API endpoint"
/commit "test: add unit tests for UserService"
/commit "docs: update API documentation"
```

**Best practice**: Use conventional commit format

#### `/pr` or `/pull-request`
Create pull requests
```bash
/pr create --title "User Profile API" --description "Implements profile endpoints"
```

---

### Documentation

#### `/docs` or `/readme`
View or update documentation
```bash
/docs
```

---

### 8. `/dev-task` - Code Implementation (Individual Phase)

**Purpose**: Spawn Code Implementation Agent to develop/implement a specific task

**Available Commands**:
```bash
/dev-task TASK-001                    # Implement feature + unit tests
/dev-task TASK-001 --resume           # Resume incomplete implementation
/dev-task TASK-001 --branch custom    # Use custom branch name
/dev-task TASK-001 --skip-tests       # Skip unit tests (not recommended)
```

**Token Efficiency**:
- ✅ Saves **~4,000-8,000 tokens** vs manual step-by-step guidance
- ✅ Agent runs in isolated context (doesn't consume main tokens)
- ✅ Automatic feature branch, unit tests, commits
- ✅ 88-94% token savings

**What It Does**:
1. Validates task exists and status is TODO or IN_PROGRESS
2. Spawns Code Implementation Agent in isolated context
3. Agent reads task requirements from docs/tasks/dashboard.md and docs/templates/specs/
4. Creates feature branch (feature/task-{id}-{slug})
5. Implements feature/fix following PROJECT.md guidelines
6. Writes unit tests (≥80% coverage)
7. Runs tests to verify (must be 100% pass)
8. Commits changes with conventional commit message
9. Updates task status: TODO → IN_REVIEW
10. Creates handoff document for code review

**Example Workflow**:
```bash
# After importing task from Jira
/jira-task PROJ-456
# Output: Created TASK-001

# Implement the task
/dev-task TASK-001

# Agent Output:
# ✅ Branch: feature/task-001-user-profile-api
# ✅ Implemented: 3 source files, 2 test files
# ✅ Unit tests: 25/25 pass (100%), 85% coverage
# ✅ Committed: feat(profile): add user profile API endpoints
# ✅ Status: TODO → IN_REVIEW
# ⏱️ Time: 6m 42s
#
# Next: /review-code TASK-001

# Continue to code review
/review-code TASK-001
```

**When to Use**:
- Want granular control over workflow phases
- Need to pause between implementation and review
- Implementing exploratory/experimental features
- Learning codebase step-by-step

**vs /complete-task**:
- `/dev-task`: Implementation phase only (~5-12 min)
- `/complete-task`: Full workflow all 4 phases (~15-40 min)

**Complete guide**: [.claude/skills/dev-task/SKILL.md](../.claude/skills/dev-task/SKILL.md)

---

### 9. `/review-code` - Code Review (Individual Phase)

**Purpose**: Spawn Code Review Agent to review code changes for a specific task

**Available Commands**:
```bash
/review-code TASK-001                 # Review code for task
/review-code TASK-001 --strict        # Zero-tolerance review mode
/review-code TASK-001 --quick         # Quick review (critical issues only)
/review-code --all                    # Review all IN_REVIEW tasks
```

**Token Efficiency**:
- ✅ Saves **~5,000-10,000 tokens** vs manual code review
- ✅ Agent runs in isolated context
- ✅ Comprehensive review report generated
- ✅ 97-99% token savings

**What It Does**:
1. Validates task status is IN_REVIEW
2. Spawns Code Review Agent in isolated context
3. Agent reads code changes via git diff
4. Reviews against standards:
   - Code quality and style (PROJECT.md, CLAUDE.md)
   - Functionality and requirements
   - Security (OWASP Top 10, SQL injection, XSS)
   - Performance (N+1 queries, caching, complexity)
   - Test coverage and quality (≥80% threshold)
   - Architecture compliance
5. Generates detailed review report (docs/reviews/TASK-{id}-review.md)
6. Makes decision: APPROVED or CHANGES_REQUESTED
7. Updates task status:
   - APPROVED → IN_TESTING
   - CHANGES_REQUESTED → IN_PROGRESS
8. Creates handoff document for next agent

**Review Criteria**:
- **Critical Issues**: Security vulnerabilities, broken functionality
- **Major Issues**: Missing tests, poor error handling, performance problems
- **Minor Issues**: Code style, naming, documentation

**Example Workflow**:
```bash
# After implementation complete
/dev-task TASK-001
# Output: Status → IN_REVIEW

# Review the code
/review-code TASK-001

# Agent Output (APPROVED):
# 🔍 Reviewing code for TASK-001...
# Changes: 5 files (+320 -45 lines)
#
# Review Checklist:
# ✅ Code quality and style
# ✅ Security (no vulnerabilities)
# ✅ Performance (efficient)
# ✅ Test coverage (85%, above threshold)
#
# Findings:
# ├─ Critical: 0
# ├─ Major: 0
# └─ Minor: 2 (non-blocking)
#
# ✅ DECISION: APPROVED
# ✅ Status: IN_REVIEW → IN_TESTING
# ⏱️ Time: 3m 15s
#
# Next: /test-task TASK-001

# Continue to testing
/test-task TASK-001
```

**Review Modes**:
- **Normal** (default): Balanced review, minor issues OK
- **Strict** (`--strict`): Zero tolerance, any issue blocks
- **Quick** (`--quick`): Critical issues only, fast (for hotfixes)

**Complete guide**: [.claude/skills/review-code/SKILL.md](../.claude/skills/review-code/SKILL.md)

---

### 10. `/test-task` - Automated Testing (Individual Phase)

**Purpose**: Spawn Test Agent to create and execute comprehensive automated tests

**Available Commands**:
```bash
/test-task TASK-001                   # Full test suite (API, integration, E2E)
/test-task TASK-001 --api-only        # API contract tests only
/test-task TASK-001 --integration-only # Integration tests only
/test-task TASK-001 --e2e-only        # End-to-end tests only
/test-task --all                      # Test all IN_TESTING tasks
```

**Token Efficiency**:
- ✅ Saves **~6,000-12,000 tokens** vs manual test creation
- ✅ Agent runs in isolated context
- ✅ Creates multiple test types automatically
- ✅ 96-98% token savings

**What It Does**:
1. Validates task status is IN_TESTING
2. Spawns Test Agent in isolated context
3. Agent analyzes implementation and requirements
4. Creates comprehensive tests:
   - **API Contract Tests**: Request/response schemas, HTTP codes, error formats
   - **Integration Tests**: Component interactions, database operations, transactions
   - **Business Rule Tests**: Business logic, validations, edge cases
   - **E2E Tests**: Complete user workflows, multi-step scenarios
5. Executes all test types
6. Generates test report (docs/test-reports/TASK-{id}-test-report.md)
7. Updates task status:
   - ALL PASS (100%) → DOCUMENTING
   - ANY FAIL → IN_PROGRESS
8. Creates handoff document

**Test Types Created**:
- **Unit Tests**: Already exist from /dev-task (25 tests)
- **API Contract**: 10 tests (schemas, status codes, auth)
- **Integration**: 8 tests (DB operations, transactions)
- **Business Rules**: 5 tests (validations, constraints)
- **E2E**: 2 tests (complete workflows)
- **Total**: ~50 tests for comprehensive coverage

**Example Workflow**:
```bash
# After code review approved
/review-code TASK-001
# Output: APPROVED, Status → IN_TESTING

# Run comprehensive tests
/test-task TASK-001

# Agent Output:
# 🧪 Creating and executing tests for TASK-001...
#
# [1/5] API contract tests... ✅ 10 tests created
# [2/5] Integration tests... ✅ 8 tests created
# [3/5] Business rule tests... ✅ 5 tests created
# [4/5] E2E tests... ✅ 2 tests created
# [5/5] Executing all tests...
#
# Test Results:
# ├─ Unit: 25/25 pass (100%) ✅
# ├─ API Contract: 10/10 pass (100%) ✅
# ├─ Integration: 8/8 pass (100%) ✅
# ├─ Business Rules: 5/5 pass (100%) ✅
# └─ E2E: 2/2 pass (100%) ✅
#
# ✅ ALL TESTS PASS (50/50, 100%)
# ✅ Status: IN_TESTING → DOCUMENTING
# ⏱️ Time: 10m 22s
#
# Next: /update-document TASK-001

# Continue to documentation
/update-document TASK-001
```

**Quality Gate**: 100% pass rate required (all tests must pass to proceed)

**Complete guide**: [.claude/skills/test-task/SKILL.md](../.claude/skills/test-task/SKILL.md)

---

### 11. `/update-document` - Documentation Update (Individual Phase)

**Purpose**: Spawn Documentation Agent to update all documentation for a task

**Available Commands**:
```bash
/update-document TASK-001             # Update all documentation
/update-document TASK-001 --api-only  # Update API docs only
/update-document TASK-001 --feature-only # Update feature docs only
/update-document --all                # Document all DOCUMENTING tasks
```

**Token Efficiency**:
- ✅ Saves **~4,000-8,000 tokens** vs manual documentation
- ✅ Agent runs in isolated context
- ✅ Comprehensive docs generated automatically
- ✅ 94-97% token savings

**What It Does**:
1. Validates task status is DOCUMENTING
2. Spawns Documentation Agent in isolated context
3. Agent reviews all artifacts (code, review report, test report)
4. Updates documentation:
   - **API Docs** (docs/api/): Endpoints, examples, error codes
   - **Feature Docs** (docs/features/): User guides, how-tos
   - **Architecture Docs** (docs/architecture/): Components, diagrams
   - **Configuration** (docs/configuration.md): Environment variables
   - **Troubleshooting** (docs/troubleshooting/): Common issues, solutions
5. Commits documentation changes
6. Updates task status: DOCUMENTING → DONE
7. Creates completion summary

**Documentation Generated**:
- API reference with request/response examples
- Code examples in multiple languages (JavaScript, Java, etc.)
- Feature guides for end users
- Configuration documentation
- Troubleshooting guides
- Architecture updates

**Example Workflow**:
```bash
# After all tests pass
/test-task TASK-001
# Output: ALL PASS, Status → DOCUMENTING

# Update documentation
/update-document TASK-001

# Agent Output:
# 📝 Updating documentation for TASK-001...
#
# [1/7] Reviewing artifacts... ✅
# [2/7] API documentation... ✅ Created docs/api/user-profile-api.md
# [3/7] Feature documentation... ✅ Created docs/features/user-profile.md
# [4/7] Architecture docs... ✅ Updated docs/architecture/components.md
# [5/7] Configuration... ✅ Added PROFILE_* env vars
# [6/7] Troubleshooting... ✅ Added profile issues guide
# [7/7] Committing changes... ✅
#
# ✅ Documentation Complete!
# ✅ Status: DOCUMENTING → DONE
# ⏱️ Time: 8m 15s
#
# 🎉 TASK-001 is now DONE!
#
# Optional:
# - /publish-confluence TASK-001 (publish to Confluence)
# - /update-jira-task TASK-001 (sync to Jira)

# Optionally publish to Confluence
/publish-confluence TASK-001

# Optionally sync to Jira
/update-jira-task TASK-001
```

**Documentation Quality**:
- Clear, concise, and accurate
- Working code examples (tested)
- No broken internal links
- Proper markdown formatting
- Professional presentation

**Complete guide**: [.claude/skills/update-document/SKILL.md](../.claude/skills/update-document/SKILL.md)

---

### 12. `/commit-push-pr` - Auto Commit, Push & Create PR

**Purpose**: Automatically commit changes, push to remote, and create Pull Request with auto-generated description

**Available Commands**:
```bash
/commit-push-pr TASK-001                   # Create PR to default branch (master)
/commit-push-pr TASK-001 --target develop  # Create PR to specific branch
/commit-push-pr TASK-001 --base main       # Alternative syntax for target
/commit-push-pr TASK-001 --draft           # Create draft PR
/commit-push-pr TASK-001 --no-commit       # Push only (skip commit)
```

**Token Efficiency**:
- ✅ Saves **~1,250-2,250 tokens** vs manual git operations
- ✅ One command replaces 10+ manual steps
- ✅ Auto-generates conventional commit messages
- ✅ Auto-generates comprehensive PR descriptions
- ✅ 83-90% token savings, 80-93% time savings

**What It Does**:
1. Reads task details from docs/tasks/dashboard.md
2. Verifies current branch matches task (feature/task-{id}-{slug})
3. Auto-generates conventional commit message:
   - Type: feat, fix, refactor, docs (from task type)
   - Scope: Detected from files changed
   - Description: From task details
   - Example: `feat(profile): add user profile API endpoints`
4. Commits all changes with co-author attribution
5. Pushes to remote (handles new branches with -u flag)
6. Generates comprehensive PR description:
   - Summary from task description
   - Changes list from git log
   - Quality metrics (review status, test results)
   - Deliverables (code, tests, docs)
   - Related links (Jira, review report, test report)
   - Test instructions for reviewers
   - Pre-filled checklist
7. Creates Pull Request using GitHub CLI (gh pr create)
8. Updates task metadata with PR URL

**Auto-Generated PR Description Includes**:
- **Summary**: What the PR accomplishes
- **Changes**: Bullet list from git commits
- **Quality Metrics**:
  - Code Review: ✅ APPROVED | ⚠️ CHANGES_REQUESTED
  - Tests: ✅ ALL PASS (50/50, 100%) | ❌ FAILED
  - Coverage: 87% (above threshold)
- **Deliverables**: Files changed, test counts, documentation
- **Related Links**: Jira, review reports, test reports
- **Test Instructions**: How to test the changes
- **Checklist**: Pre-filled based on task status

**Example Workflow**:
```bash
# After task completion
/complete-task TASK-001
# Or manually:
/dev-task TASK-001
/review-code TASK-001
/test-task TASK-001
/update-document TASK-001

# Create PR (one command!)
/commit-push-pr TASK-001

# Agent Output:
# 📝 Reading task: TASK-001 - User Profile API
# 🔍 Branch: feature/task-001-user-profile-api ✅
# 📦 Changes: 6 files staged
# 💾 Commit: feat(profile): add user profile API endpoints ✅
# 🚀 Pushed to origin/feature/task-001-user-profile-api ✅
# 📋 Generated PR description (quality metrics, links, checklist)
# 🎯 PR #42 created → master ✅
#
# 🔗 https://github.com/your-org/your-repo/pull/42
#
# Next: Request reviews, address feedback, merge when approved

# Update task metadata
# ✅ PR URL added to docs/tasks/dashboard.md
# ✅ Task status remains DONE
```

**Example Generated Commit**:
```
feat(profile): add user profile API endpoints

Implement GET and PUT endpoints for user profile management.
Includes bio and location fields with validation.

Resolves: TASK-001
```

**Example PR Title & Description**:
```markdown
Title: User Profile API

## Summary
Implement user profile API with GET and PUT endpoints for bio and location management.

## Changes
- Add ProfileController with GET/PUT endpoints
- Add ProfileService with business logic and validation
- Add UserProfile model
- Add comprehensive test suite (25 unit + 25 integration/E2E tests)
- Update API documentation

## Quality Metrics
- **Code Review**: ✅ APPROVED (0 critical, 0 major, 2 minor issues)
- **Tests**: ✅ ALL PASS (50/50, 100%)
- **Coverage**: 87% (above 80% threshold)

## Deliverables
### Code
- 5 files changed (+320 -45 lines)
- ProfileController.java, ProfileService.java, UserProfile.java

### Tests
- 25 unit tests (100% pass)
- 10 API contract tests (100% pass)
- 8 integration tests (100% pass)
- 5 business rule tests (100% pass)
- 2 E2E tests (100% pass)

### Documentation
- docs/api/user-profile-api.md
- docs/features/user-profile.md
- docs/troubleshooting/profile-issues.md

## Related Links
- **Jira**: [PROJ-456](https://jira.vissoft.vn/browse/PROJ-456)
- **Review Report**: docs/reviews/TASK-001-review.md
- **Test Report**: docs/test-reports/TASK-001-test-report.md

## Test Instructions
1. Checkout: `git checkout feature/task-001-user-profile-api`
2. Build: `mvn clean install`
3. Run tests: `mvn test`
4. Start server: `mvn spring-boot:run`
5. Test endpoints:
   - GET /api/profile (requires Bearer token)
   - PUT /api/profile (requires Bearer token)

## Checklist
- [x] Code implements all requirements
- [x] Unit tests passing (100%)
- [x] Integration tests passing (100%)
- [x] Code review approved
- [x] Documentation updated
- [x] No security vulnerabilities
- [x] Performance validated

---
🤖 Generated by AI Team Template
```

**Prerequisites**:
- ✅ GitHub CLI (gh) installed and authenticated: `gh auth login`
- ✅ Git remote configured
- ✅ SSH key or HTTPS auth set up for push
- ✅ Task completed (status: DONE)

**Use Cases**:
- **Standard workflow**: Complete task → Create PR
- **Hotfix**: Quick fix → Draft PR for early feedback
- **Feature branch workflow**: PR to develop branch instead of master
- **Team collaboration**: Auto-assign reviewers, add labels

**Integration Example**:
```bash
# Complete workflow with all integrations
/jira-task PROJ-456                    # Import from Jira
/complete-task TASK-001                # Complete automatically
/update-jira-task TASK-001             # Sync to Jira
/commit-push-pr TASK-001 --target main # Create PR ⭐
/publish-confluence TASK-001           # Publish to Confluence

# Result: Task done, Jira updated, PR created, docs published! 🎉
```

**Configuration**:
```bash
# Environment variables (optional)
export PR_DEFAULT_TARGET="master"
export PR_AUTO_LABELS=true
export PR_LABELS="ai-team-template,automated"
export PR_AUTO_REVIEWERS=true
export PR_REVIEWERS="@team-leads"
export PR_DRAFT_DEFAULT=false
```

**Complete guide**: [.claude/skills/commit-push-pr/SKILL.md](../.claude/skills/commit-push-pr/SKILL.md)

---

### Granular Workflow vs Full Automation

**Granular Control** (use individual commands):
```bash
/dev-task TASK-001         # Step 1: Implementation (5-12 min)
/review-code TASK-001      # Step 2: Code Review (3-8 min)
/test-task TASK-001        # Step 3: Testing (8-15 min)
/update-document TASK-001  # Step 4: Documentation (6-12 min)
# Total: 22-47 min with manual control between phases
```

**Full Automation** (use /complete-task):
```bash
/complete-task TASK-001    # All 4 phases automatically (15-40 min)
# Zero manual intervention, 100% autonomous
```

**When to Use Granular Commands**:
- Want to review each phase before proceeding
- Need to make manual adjustments between phases
- Learning the codebase
- Experimental/exploratory work
- Want control over review strictness or test types

**When to Use Full Automation**:
- Trust the multi-agent workflow
- Production-ready features following standard patterns
- Sprint tasks with clear requirements
- Want hands-off completion

---

## Agent-Specific Command Workflows

### Code Implementation Agent Workflow

```bash
# 1. Start task
/task-status TASK-001 IN_PROGRESS

# 2. During implementation
/auto-build check                  # Quick syntax/type check

# 3. Before handoff
/auto-build test                   # Verify all tests pass
/auto-build lint                   # Verify code style
/commit "feat: implement user profile API"

# 4. Hand off to review
/task-status TASK-001 IN_REVIEW
/handoff TASK-001 "to:code-review" "Implementation complete, 25 tests, all pass"
```

---

### Code Review Agent Workflow

```bash
# 1. Read handoff
# docs/handoffs/TASK-001-to-code-review-*.md

# 2. Review code
/diff master..feature/TASK-001
/review TASK-001                    # Automated analysis

# 3. Verify builds and tests
/auto-build check
/auto-build test

# 4. Decision: Approve
/task-status TASK-001 IN_TESTING
/handoff TASK-001 "to:test" "Code review APPROVED. All standards met."

# Or Decision: Changes Requested
/task-status TASK-001 IN_PROGRESS
/handoff TASK-001 "to:implementation" "Changes: Add validation for bio field"
```

---

### Test Agent Workflow

```bash
# 1. Read handoff
# docs/handoffs/TASK-001-to-test-*.md

# 2. Run all tests
/auto-build test                    # Full test suite
/auto-build lint                    # Code quality check

# 3. Decision: All Pass
/task-status TASK-001 DOCUMENTING
/handoff TASK-001 "to:documentation" "All tests PASSED (25/25). API validated."

# Or Decision: Tests Fail
/task-status TASK-001 IN_PROGRESS
/handoff TASK-001 "to:implementation" "Tests FAILED (3/25). See test report."
```

---

### Documentation Agent Workflow

```bash
# 1. Read handoff
# docs/handoffs/TASK-001-to-documentation-*.md

# 2. Review changes
/git log --oneline -10
/diff master..feature/TASK-001

# 3. Update documentation
/docs                               # Update docs
# Edit API documentation
# Edit feature documentation
# Update README if needed

# 4. Finalize
/commit "docs: update API documentation for TASK-001"
/task-status TASK-001 DONE
```

---

### Agent Manager Workflow

```bash
# Orchestrating TASK-001

# 1. Start task
/statusline show
/task-status TASK-001 IN_PROGRESS
# Dispatch Code Implementation Agent

# 2. Code complete
/task-status TASK-001 IN_REVIEW
# Dispatch Code Review Agent

# 3. Review approved
/task-status TASK-001 IN_TESTING
# Dispatch Test Agent

# 4. All tests pass
/task-status TASK-001 DOCUMENTING
# Dispatch Documentation Agent

# 5. Documentation complete
/task-status TASK-001 DONE
# Report completion
```

---

## Best Practices

### 1. Token Optimization

**For any tech stack**:
```bash
❌ AVOID: /run mvn clean install (verbose)
✅ USE:   /auto-build build (auto-detects tech, quiet output)

❌ AVOID: /run npm test (verbose)
✅ USE:   /auto-build test (quiet output, summary only)

❌ AVOID: /run cargo check (verbose)
✅ USE:   /auto-build check (quiet output)
```

---

### 2. Workflow Sequencing

**Always follow this sequence**:
1. Update status BEFORE starting work
2. Use appropriate build/test commands during work
3. Verify all checks pass BEFORE handoff
4. Update status AFTER work complete
5. Create handoff with detailed context

**Example**:
```bash
# ✅ Correct sequence
/task-status TASK-001 IN_PROGRESS     # 1. Update status
# ... implement ...
/auto-build test                     # 2. Verify work
/task-status TASK-001 IN_REVIEW       # 3. Update status
/handoff TASK-001 "to:code-review" "..." # 4. Create handoff

# ❌ Incorrect sequence (no status update)
# ... implement ...
/handoff TASK-001 "to:code-review" "..."  # Missing status update!
```

---

### 3. Command Priority

**Priority order** (use higher priority when available):
1. **Custom skills** (`/auto-build`, `/task-status`, `/handoff`, `/complete-task`, `/dev-task`)
2. **Your configured commands** (`/init`, `/review`)
3. **Standard commands** (`/run`, `/test`, `/commit`)

---

### 4. Error Handling

**If builds fail**:
```bash
# Don't update status to next phase
/auto-build test
# If fails, fix issues first, don't move to IN_REVIEW
```

**If tests fail**:
```bash
# Create handoff back to implementation
/task-status TASK-001 IN_PROGRESS
/handoff TASK-001 "to:implementation" "Tests failed: [specific issues]"
```

**If blocked**:
```bash
# Mark as blocked with reason
/task-status TASK-001 BLOCKED "Waiting for API spec approval"
```

---

### 5. Agent Communication

**Always create handoffs** when changing agents:
```bash
# ✅ Good
/task-status TASK-001 IN_REVIEW
/handoff TASK-001 "to:code-review" "Implementation complete..."

# ❌ Bad (no handoff)
/task-status TASK-001 IN_REVIEW
# Code Review Agent has no context!
```

---

## Quick Reference Cheat Sheet

### Code Implementation Agent
```bash
# Option 1: Automated (recommended)
/dev-task TASK-ID                  # ⭐ NEW: Full implementation automatically
# Status: TODO → IN_REVIEW (auto)

# Option 2: Manual
/task-status TASK-ID IN_PROGRESS
/auto-build check
/auto-build test
/auto-build lint
/commit "feat: ..."
/task-status TASK-ID IN_REVIEW
/handoff TASK-ID "to:code-review" "..."
```

### Code Review Agent
```bash
# Option 1: Automated (recommended)
/review-code TASK-ID               # ⭐ NEW: Full review automatically
# Status: IN_REVIEW → IN_TESTING (if approved)

# Option 2: Manual
/diff master..feature/TASK-ID
/review TASK-ID
/auto-build check
/auto-build test
/task-status TASK-ID IN_TESTING
/handoff TASK-ID "to:test" "..."
```

### Test Agent
```bash
# Option 1: Automated (recommended)
/test-task TASK-ID                 # ⭐ NEW: Full testing automatically
# Status: IN_TESTING → DOCUMENTING (if all pass)

# Option 2: Manual
/auto-build test
/auto-build lint
/task-status TASK-ID DOCUMENTING
/handoff TASK-ID "to:documentation" "..."
```

### Documentation Agent
```bash
# Option 1: Automated (recommended)
/update-document TASK-ID           # ⭐ NEW: Full documentation automatically
# Status: DOCUMENTING → DONE (auto)

# Option 2: Manual
/git log --oneline -10
/diff master..feature/TASK-ID
/docs
/commit "docs: ..."
/task-status TASK-ID DONE

# After documentation complete
/commit-push-pr TASK-ID            # ⭐ NEW: Auto commit, push & create PR
/publish-confluence TASK-ID        # Publish to Confluence
```

### Agent Manager / Project Leader
```bash
# Project initialization (first time only)
/project-setup                 # Interactive project setup
/project-setup --quick         # Quick setup with defaults

# Sprint/iteration start ⭐ NEW
/jira-task --project PROJ      # Import all tasks from Jira
/jira-task PROJ-456            # Import single task

# Full task automation ⚡ NEW
/complete-task TASK-001        # Complete single task automatically
/complete-task --all           # Complete all TODO tasks sequentially
/complete-task --all --parallel  # Complete all tasks in parallel

# Granular workflow control ⭐ NEW (individual phases)
/dev-task TASK-001             # Step 1: Implementation only
/review-code TASK-001          # Step 2: Code review only
/test-task TASK-001            # Step 3: Testing only
/update-document TASK-001      # Step 4: Documentation only

# Git & Pull Request automation ⭐ NEW
/commit-push-pr TASK-001              # Auto commit, push & create PR
/commit-push-pr TASK-001 --target develop  # PR to specific branch
/commit-push-pr TASK-001 --draft      # Create draft PR

# Sync back to Jira ⭐ NEW
/update-jira-task --done       # Update completed tasks in Jira
/update-jira-task --all        # Sync all changed tasks
/update-jira-task TASK-001     # Sync specific task

# Publish documentation to Confluence ⭐ NEW
/publish-confluence --all-done # Publish all completed task docs
/publish-confluence TASK-001   # Publish specific task docs
/publish-confluence TASK-001 --update  # Update existing page

# Ongoing workflow monitoring
/statusline show
/task-status TASK-ID <STATUS>
# Monitor workflow progress
```

---

## Appendix: Command Configuration

### Registering Custom Skills

Skills are auto-detected from `.claude/skills/` directory:
```
.claude/skills/
├── project-setup/
│   └── SKILL.md              # Project initialization
├── build-backend/
│   └── SKILL.md              # Maven build commands
├── build-frontend/
│   └── SKILL.md              # React build commands
├── test-api/
│   └── SKILL.md              # API testing commands
├── complete-task/
│   └── SKILL.md              # ⚡ Full task automation
├── dev-task/
│   └── SKILL.md              # ⭐ NEW: Code implementation (individual phase)
├── review-code/
│   └── SKILL.md              # ⭐ NEW: Code review (individual phase)
├── test-task/
│   └── SKILL.md              # ⭐ NEW: Testing (individual phase)
├── update-document/
│   └── SKILL.md              # ⭐ NEW: Documentation (individual phase)
├── commit-push-pr/
│   └── SKILL.md              # ⭐ NEW: Auto commit, push & create PR
├── jira-task/
│   └── SKILL.md              # ⭐ Import tasks from Jira
├── update-jira-task/
│   └── SKILL.md              # ⭐ Sync status back to Jira
├── publish-confluence/
│   └── SKILL.md              # ⭐ Publish docs to Confluence
├── import-confluence/
│   └── SKILL.md              # ⭐ Import docs from Confluence
├── task-status/
│   └── SKILL.md              # Task status updates
└── handoff/
    └── SKILL.md              # Agent handoff documents
```

No manual registration needed - just place `SKILL.md` files in skill folders under `.claude/skills/`

### Required Permissions

Ensure `.claude/settings.json` includes:
```json
{
  "allow": [
    "Bash(mvn:*)",
    "Bash(npm:*)",
    "Bash(npx:*)",
    "Bash(newman:*)",
    "Bash(git:*)",
    "Read(docs/*)",
    "Edit(docs/tasks/dashboard.md:*)",
    "Write(docs/handoffs/*)"
  ]
}
```

---

## See Also

- [CLAUDE.md](../CLAUDE.md) - Development guidelines and token optimization
- [PROJECT.md](../PROJECT.md) - Project-specific tech stack details
- [MULTI_AGENT_ORCHESTRATION.md](../MULTI_AGENT_ORCHESTRATION.md) - Multi-agent workflow
- [AGENT_MANAGER_GUIDE.md](../AGENT_MANAGER_GUIDE.md) - Agent Manager usage
- [.claude/agents/](../.claude/agents/) - Individual agent configurations
- [.claude/skills/](../.claude/skills/) - Custom skill configurations

---

**Last Updated**: 2026-02-11
**Team**: Multi-Agent Development Team
**Tech Stack**: Any (auto-detected from PROJECT.md)
**Command Count**: 4 configured + 22 custom skills + 15+ standard commands
