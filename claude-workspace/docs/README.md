# Documentation Guide

Welcome to the multi-agent development system documentation! This guide explains the structure and usage of the documentation system.

## Overview

This project uses a **4-agent development workflow** with complete markdown-based documentation for task tracking, code reviews, testing, and feature documentation. No external tools (Jira, Confluence) are required - everything is tracked in this `docs/` folder.

## Quick Start

### For New Tasks
1. Add task to `docs/tasks/dashboard.md` with status "TODO"
2. Code Implementation Agent picks it up and changes status to "IN_PROGRESS"
3. Follow the workflow through all phases (see WORKFLOW.md)
4. Task is marked "DONE" when documentation is complete

### For Quick Reference
- **Workflow Overview:** [WORKFLOW.md](WORKFLOW.md)
- **Task Tracking:** [tasks.md](tasks.md)
- **Agent Specifications:** [agents/](agents/)
- **Templates:** [templates/](templates/)

## Directory Structure

```
docs/
├── README.md                  # This file - documentation guide
├── WORKFLOW.md                # Complete workflow orchestration guide
├── tasks.md                   # Task tracking (replaces Jira)
│
├── agents/                    # Agent specification files
│   ├── code-implementation-agent.md   # Implementation agent guide
│   ├── code-review-agent.md           # Review agent guide
│   ├── test-agent.md                  # Testing agent guide
│   └── documentation-agent.md         # Documentation agent guide
│
├── templates/                 # Workflow templates
│   ├── handoff-template.md            # Agent handoff template
│   ├── review-template.md             # Code review report template
│   ├── test-report-template.md        # Test report template
│   └── bug-report-template.md         # Bug report template
│
├── refs/                      # Input docs: DetailDesign, SRS, implementation-plan
│   ├── SRS-*.md                       # Software Requirements Specifications
│   └── DetailDesign-*.md              # Detail Design documents
│
├── api/                       # API documentation (OUTPUT)
│   ├── endpoints.md                   # API endpoint documentation
│   ├── errors.md                      # Error codes and messages
│   └── authentication.md              # Authentication documentation
│
├── features/                  # Feature documentation (OUTPUT)
│   └── [feature-name].md              # Feature-specific documentation
│
├── handoffs/                  # Agent handoff documents (OUTPUT)
│   └── TASK-ID-[phase]-to-[phase].md  # Handoff summaries
│
├── reviews/                   # Code review reports (OUTPUT)
│   └── TASK-ID-review.md              # Code review results
│
├── test-reports/              # Test execution reports (OUTPUT)
│   └── TASK-ID-test-report.md         # Comprehensive test results
│
├── bugs/                      # Bug reports (OUTPUT)
│   └── BUG-ID.md                      # Bug details and resolution
│
├── troubleshooting/           # Troubleshooting guides (OUTPUT)
│   └── [feature-name]-issues.md       # Common problems and solutions
│
└── configuration.md           # Configuration guide (OUTPUT)
```

## The 4 Agents

### 1. Code Implementation Agent
**Role:** Develops features and fixes bugs
- Reads tasks from tasks.md
- Implements features per specifications
- Writes unit tests (80%+ coverage)
- Creates handoff documents

**See:** [agents/code-implementation-agent.md](agents/code-implementation-agent.md)

### 2. Code Review Agent
**Role:** Reviews code quality and standards
- Reviews code changes against CLAUDE.md standards
- Checks test coverage and code quality
- Creates review reports
- Approves or requests changes

**See:** [agents/code-review-agent.md](agents/code-review-agent.md)

### 3. Test Agent
**Role:** Creates and executes ALL automated tests
- Creates Karate test scenarios (API, integration, business, E2E)
- Validates business rules from SRS
- Creates comprehensive test reports
- Creates bug reports for failures

**See:** [agents/test-agent.md](agents/test-agent.md)

### 4. Documentation Agent
**Role:** Maintains technical documentation
- Updates API documentation
- Creates feature documentation
- Updates README and configuration docs
- Finalizes tasks

**See:** [agents/documentation-agent.md](agents/documentation-agent.md)

## Workflow Summary

```
Task Added (TODO)
    ↓
Implementation (IN_PROGRESS)
    ↓
Code Review (IN_REVIEW)
    ↓ (if approved)
Testing (IN_TESTING)
    ↓ (if all pass)
Documentation (DOCUMENTING)
    ↓
Complete (DONE)
```

**Detailed workflow:** See [WORKFLOW.md](WORKFLOW.md)

## Key Documents

### For Agents (How to do work)
- **agents/code-implementation-agent.md** - How to implement features
- **agents/code-review-agent.md** - How to review code
- **agents/test-agent.md** - How to create and run tests
- **agents/documentation-agent.md** - How to document features

### For Tracking (What's happening)
- **tasks.md** - Current tasks and their status
- **handoffs/** - Agent-to-agent communication
- **reviews/** - Code review results
- **test-reports/** - Test execution results
- **bugs/** - Bug reports and resolutions

### For Reference (What exists)
- **api/** - API documentation
- **features/** - Feature documentation
- **refs/** - Input docs: DetailDesign, SRS, implementation-plan
- **troubleshooting/** - Problem-solving guides

### Project-Specific Documentation
- **[../PROJECT.md](../PROJECT.md)** - **CRITICAL**: Project-specific architecture, tech stack, package structure
- **[../CLAUDE.md](../CLAUDE.md)** - General development guidelines for all agents
- **[../MULTI_AGENT_ORCHESTRATION.md](../MULTI_AGENT_ORCHESTRATION.md)** - Complete orchestration guide

## Using Templates

All templates are in `docs/templates/`. Copy and fill them out:

### Handoff Template
**When:** Handing off work to next agent
**File:** `templates/handoff-template.md`
**Output:** `handoffs/TASK-ID-implementation-to-review.md`

### Review Template
**When:** Completing code review
**File:** `templates/review-template.md`
**Output:** `reviews/TASK-ID-review.md`

### Test Report Template
**When:** Completing all tests
**File:** `templates/test-report-template.md`
**Output:** `test-reports/TASK-ID-test-report.md`

### Bug Report Template
**When:** Test fails due to code defect
**File:** `templates/bug-report-template.md`
**Output:** `bugs/BUG-ID.md`

## File Naming Conventions

### Tasks
- `tasks.md` - Single file for all task tracking

### Handoffs
- `handoffs/TASK-001-implementation-to-review.md`
- `handoffs/TASK-001-review-to-testing.md`
- `handoffs/TASK-001-testing-to-documentation.md`

### Reviews
- `reviews/TASK-001-review.md`

### Test Reports
- `test-reports/TASK-001-test-report.md`

### Bug Reports
- `bugs/BUG-001.md`
- `bugs/BUG-002.md`

### Features
- `features/user-profile.md`
- `features/rate-limiting.md`

### API Documentation
- `api/endpoints.md` - All endpoints in one file
- `api/errors.md` - All error codes
- `api/authentication.md` - Auth documentation

## Best Practices

### Token Optimization
- **Always use MCP tools first** - More efficient than manual operations
- **Never load full logs** - Use grep/tail with limits (max 20-50 lines)
- **Use quiet flags** - Add `-q` to Maven, Docker commands
- **Read specific sections** - Use line ranges in view commands
- **Extract only needed info** - Filter before reading

### Documentation Quality
- **Be specific** - Include file names, line numbers, references
- **Link everything** - Connect docs to code, specs, tests
- **Update frequently** - Keep status current
- **Use templates** - Ensure consistency
- **Include examples** - Show, don't just tell

### Task Management
- **One task, one focus** - Don't multitask across features
- **Update status immediately** - When starting/completing phases
- **Create handoffs** - Clear communication between agents
- **Track everything** - Files, tests, reviews, documentation

## Common Workflows

### Starting a New Feature
1. Add task to `tasks.md` with status "TODO"
2. Fill in requirements and specifications
3. Link to SRS/Detail Design sections
4. Code Implementation Agent picks it up

### Completing Code Review
1. Use `templates/review-template.md`
2. Create `reviews/TASK-ID-review.md`
3. Update `tasks.md` with decision
4. Link review in task's Related Files

### Reporting a Bug
1. Use `templates/bug-report-template.md`
2. Create `bugs/BUG-ID.md`
3. Reference SRS/DD sections
4. Link test scenario that failed
5. Update `tasks.md` status to "IN_PROGRESS"

### Documenting a Feature
1. Update `api/endpoints.md` with new endpoints
2. Create `features/[feature-name].md`
3. Update README.md if significant feature
4. Update `tasks.md` status to "DONE"

## Integration with Code

### Source Code
- Main code: `src/main/java/`
- Tests: `src/test/java/` (unit tests)
- Karate tests: `src/test/resources/features/` (automated tests)

### Configuration
- `pom.xml` - Maven dependencies
- `src/main/resources/application.properties` - Configuration (NOT .yml)
- `../PROJECT.md` - **MUST READ**: Project-specific details (architecture, tech stack)
- `../CLAUDE.md` - General coding standards and guidelines

### Documentation Links
When documenting, always link to:
- **Specs:** `docs/templates/specs/SRS.md` - Section X.Y
- **Code:** `src/main/java/path/to/File.java:line`
- **Tests:** `src/test/java/path/to/Test.java`
- **Features:** `src/test/resources/features/path/file.feature`

## FAQ

### Q: Where do I track my current task?
**A:** In `docs/tasks/dashboard.md` - update status as you progress through phases.

### Q: How do I know what to do as an agent?
**A:** Read your agent guide in `.claude/agents/[your-agent]-agent.md`.

### Q: Where do I put my code review results?
**A:** Create a review report in `docs/reviews/TASK-ID-review.md` using the template.

### Q: Where do I put test results?
**A:** Create a test report in `docs/test-reports/TASK-ID-test-report.md` using the template.

### Q: How do I report a bug I found?
**A:** Create a bug report in `docs/bugs/BUG-ID.md` using the template.

### Q: Where is the API documentation?
**A:** In `docs/api/endpoints.md` - update it when APIs change.

### Q: Where are the coding standards?
**A:** In the root `CLAUDE.md` file - all agents must follow these.

### Q: How do I communicate with other agents?
**A:** Through docs/tasks/dashboard.md status updates and docs/handoffs/ documents.

### Q: What if tests fail?
**A:** Test Agent creates bug report in docs/bugs/, updates tasks.md to "IN_PROGRESS", assigns to Code Implementation Agent.

### Q: When is a task really done?
**A:** When Documentation Agent marks it "DONE" in tasks.md after updating all documentation.

## Tips for Success

1. **Read the workflow first:** [WORKFLOW.md](WORKFLOW.md) explains the complete process
2. **Use templates:** They ensure consistency and completeness
3. **Update tasks.md frequently:** Keep everyone informed
4. **Link everything:** Make documentation navigable
5. **Be specific:** Include file paths, line numbers, section references
6. **Think in tokens:** Use efficient commands, don't load large files
7. **Follow standards:** Check CLAUDE.md for coding guidelines
8. **Document as you go:** Don't wait until the end

## Getting Help

- **Agent guidelines:** See `.claude/agents/`
- **Workflow questions:** See [WORKFLOW.md](WORKFLOW.md)
- **Template usage:** See `docs/templates/`
- **Coding standards:** See `../CLAUDE.md`
- **Project orchestration:** See `../MULTI_AGENT_ORCHESTRATION.md`

---

**Last Updated:** 2026-01-21
**Maintained By:** Documentation Agent
