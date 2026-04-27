# Contributing Guidelines

Thank you for considering contributing to this project! This document provides guidelines for both human developers and AI agents.

---

## For Human Developers

### Getting Started

1. **Fork the repository** (for external contributors)
2. **Clone your fork**
   ```bash
   git clone https://github.com/[your-username]/[repo-name].git
   cd [repo-name]
   ```
3. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

### Development Workflow

1. **Read the documentation**
   - [PROJECT.md](PROJECT.md) - Project-specific details
   - [CLAUDE.md](CLAUDE.md) - Development guidelines
   - [MULTI_AGENT_ORCHESTRATION.md](MULTI_AGENT_ORCHESTRATION.md) - Multi-agent workflow

2. **Make your changes**
   - Follow the coding standards in CLAUDE.md
   - Write unit tests for new functionality
   - Update documentation if needed

3. **Test your changes**
   ```bash
   # Run tests (replace with actual command from PROJECT.md)
   mvn test
   # Or: npm test, pytest, etc.
   ```

4. **Commit your changes**
   - Use conventional commits format:
     ```
     type(scope): subject

     body (optional)

     footer (optional)
     ```
   - Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`
   - Example: `feat(auth): add JWT authentication`

5. **Push and create pull request**
   ```bash
   git push origin feature/your-feature-name
   ```

### Pull Request Guidelines

- **Title**: Clear, descriptive title
- **Description**:
  - What changes were made
  - Why the changes were necessary
  - How to test the changes
- **Checklist**:
  - [ ] Code follows style guidelines
  - [ ] Tests added/updated
  - [ ] Documentation updated
  - [ ] All tests passing
  - [ ] No breaking changes (or clearly documented)

### Code Review Process

1. **Automated checks** must pass (CI/CD, linters, tests)
2. **Code review** by at least one maintainer
3. **Address feedback** and push updates
4. **Merge** after approval

---

## For AI Agents

### Claude Code / Multi-Agent System

If you're an AI agent working on this project, follow the multi-agent orchestration workflow:

#### 1. Code Implementation Agent
- Read task from `docs/tasks/TASK-ID/task.md`
- Read specifications from `docs/tasks/TASK-ID/specs/`
- Implement feature following CLAUDE.md guidelines
- Write unit tests (developer's responsibility)
- Create feature branch and commit
- Update task status to "IN_REVIEW" via `/task-status`
- Create handoff in `docs/tasks/TASK-ID/handoff/`

#### 2. Code Review Agent
- Read task + handoff from `docs/tasks/TASK-ID/handoff/`
- Review code changes using `git diff --unified=3`
- Check against CLAUDE.md coding standards
- Verify unit test coverage
- Create review report at `docs/tasks/TASK-ID/handoff/review-report.md`
- Approve or request changes
- Update task status via `/task-status`

#### 3. Test Agent
- Read approved code + specs from `docs/tasks/TASK-ID/`
- Create test scenarios → `docs/tasks/TASK-ID/deliveries/test-cases/`
- Execute all automated tests
- Create test report at `docs/tasks/TASK-ID/deliveries/test-reports/test-report.md`
- If tests fail, create bug report in `docs/tasks/TASK-ID/bugs/`
- Update task status via `/task-status`

#### 4. Documentation Agent
- Review all changes and test results
- Update API specs in `docs/tasks/TASK-ID/deliveries/api-specs/`
- Update final specs in `docs/tasks/TASK-ID/deliveries/final-specs/`
- Update README.md if needed
- Update task status to "DONE" via `/task-status`

### Agent Guidelines

**Token Optimization:**
- Use MCP tools first when available
- Never load full logs (use grep with limits)
- Use quiet flags for commands (`-q`)
- Use targeted file reads with line ranges

**Communication:**
- Update task status via `/task-status TASK-ID STATUS`
- Create structured handoffs in `docs/tasks/TASK-ID/handoff/`
- Reference task IDs in commits
- Use templates from `docs/templates/`

**Quality Gates:**
- Implementation → Review: Code compiles, tests pass, coverage ≥80%
- Review → Testing: Code approved, no critical issues
- Testing → Documentation: ALL tests pass (100%)
- Documentation → Done: All docs updated

---

## Code Style Guidelines

See [CLAUDE.md](CLAUDE.md) for detailed guidelines.

**Quick Reference:**
- Follow language/framework conventions
- Use meaningful variable/function names
- Keep functions focused and reasonably sized
- Add comments for complex logic only
- Write tests for critical functionality
- Use proper error handling
- Follow established patterns in codebase

---

## Reporting Issues

### Bug Reports

Create an issue with:
- **Title**: Clear, concise description
- **Description**:
  - What happened
  - What you expected
  - Steps to reproduce
  - Environment (OS, version, etc.)
- **Screenshots/Logs**: If applicable

### Feature Requests

- **Title**: Feature name
- **Description**:
  - Use case / problem to solve
  - Proposed solution
  - Alternatives considered
  - Additional context

---

## Community Guidelines

### Code of Conduct

- Be respectful and inclusive
- Accept constructive criticism gracefully
- Focus on what's best for the project
- Show empathy towards other contributors

### Communication Channels

- **Issues**: Bug reports, feature requests
- **Pull Requests**: Code contributions
- **Discussions**: Questions, ideas, general discussion
- [Add your team communication channels: Slack, Teams, Discord, etc.]

---

## License

By contributing, you agree that your contributions will be licensed under the same license as the project (see [LICENSE](LICENSE)).

---

## Questions?

- Check [PROJECT.md](PROJECT.md) for project-specific details
- Review [CLAUDE.md](CLAUDE.md) for development guidelines
- See [MULTI_AGENT_ORCHESTRATION.md](MULTI_AGENT_ORCHESTRATION.md) for multi-agent workflow
- Open an issue for questions not covered by documentation

---

**Thank you for contributing!** 🎉
