# Release Process

**IMPORTANT: This document is ONLY for releasing the AI Team Template project itself, NOT for projects using this template.**

---

## Overview

This document describes the standardized release process for the **AI Team Template** repository. Follow these steps when creating a new release.

## Version Numbering

We follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html):

- **MAJOR.MINOR.PATCH** (e.g., 1.2.2)
- **MAJOR**: Breaking changes, major architectural changes
- **MINOR**: New features, enhancements (backward compatible)
- **PATCH**: Bug fixes, minor improvements (backward compatible)

**Tag Format**: `X.X.X-RELEASE` (e.g., `1.2.2-RELEASE`)

### Version Guidelines

| Version Type | When to Use | Example |
|--------------|-------------|---------|
| **PATCH** (1.2.X) | Bug fixes, documentation updates, minor enhancements | 1.2.1 → 1.2.2 |
| **MINOR** (1.X.0) | New features, new slash commands, new agents | 1.2.2 → 1.3.0 |
| **MAJOR** (X.0.0) | Breaking changes, major refactoring, workflow changes | 1.3.0 → 2.0.0 |

## Release Checklist

### 1. Pre-Release Preparation

- [ ] **Test all changes** - Ensure new features work correctly
- [ ] **Update CHANGELOG.md** - Document all changes in `[Unreleased]` section
- [ ] **Review documentation** - Update README.md, skill docs, agent docs if needed
- [ ] **Check for breaking changes** - If yes, consider MAJOR version bump
- [ ] **Verify all commits** - Ensure commit messages follow conventional commits

### 2. Version Update

Update version numbers in these files:

#### Files to Update:
1. **CHANGELOG.md**
   - Change `[Unreleased]` → `[X.X.X] - YYYY-MM-DD`
   - Add release date
   - Summarize all changes under appropriate categories:
     - **Added** - New features
     - **Changed** - Changes to existing functionality
     - **Enhanced** - Improvements to existing features
     - **Fixed** - Bug fixes
     - **Deprecated** - Soon-to-be removed features
     - **Removed** - Removed features
     - **Security** - Security improvements

2. **README.md** (2 locations)
   - Line ~7: `**Version**: X.X.X (YYYY-MM-DD)`
   - Bottom section: `**Version**: X.X.X` and `**Last Updated**: YYYY-MM-DD`

#### Example Updates:

**CHANGELOG.md:**
```markdown
## [Unreleased]

---

## [1.2.2] - 2026-01-27

### Enhanced
- Enhanced `/project-setup` skill...
```

**README.md:**
```markdown
**Version**: 1.2.2 (2026-01-27)
```

### 3. Git Operations

Execute these commands in order:

```bash
# Step 1: Stage all changes
git add CHANGELOG.md README.md [other-modified-files]

# Step 2: Create commit (use conventional commit format)
git commit -m "$(cat <<'EOF'
release: version X.X.X - brief description

Detailed description of changes:
- First change
- Second change
- Third change

Additional notes if needed.
EOF
)"

# Step 3: Create annotated tag (format: X.X.X-RELEASE)
git tag -a X.X.X-RELEASE -m "Version X.X.X - Brief description"

# Step 4: Verify commit and tag
git log -1 --oneline
git tag -l | tail -5

# Step 5: Push to remote (if ready)
git push origin master
git push origin X.X.X-RELEASE
```

### 4. Post-Release Tasks

- [ ] **Verify remote** - Check GitHub/GitLab shows new tag
- [ ] **Create release notes** - Create GitHub/GitLab release from tag
- [ ] **Send Telegram notification** - Automated release announcement (see step 5)
- [ ] **Update documentation** - If needed for external docs
- [ ] **Notify additional channels** - Email, Slack, etc. (if needed)
- [ ] **Test installation** - Clone fresh copy and verify setup works

### 5. Send Release Notification (Final Step) 🎉

**IMPORTANT: Always send release notification after successful push to remote.**

#### Setup (One-time only)

If this is your first release, set up Telegram notification:

1. **Create Telegram bot** (if not exists):
   - Open Telegram, search for `@BotFather`
   - Send `/newbot` and follow prompts
   - Copy bot token

2. **Get Chat ID**:
   - Add bot to your channel/group
   - Send a message to get chat ID
   - See [TELEGRAM_NOTIFICATION_SETUP.md](TELEGRAM_NOTIFICATION_SETUP.md) for detailed instructions

3. **Set environment variables** (one-time):
   ```bash
   # Windows PowerShell (Persistent)
   [System.Environment]::SetEnvironmentVariable('TELEGRAM_BOT_TOKEN', 'YOUR_TOKEN', 'User')
   [System.Environment]::SetEnvironmentVariable('TELEGRAM_CHAT_ID', 'YOUR_CHAT_ID', 'User')
   [System.Environment]::SetEnvironmentVariable('REPO_URL', 'https://bitbucket.vissoft.vn/projects/CT/repos/template-ai-team', 'User')

   # Linux/macOS (Add to ~/.bashrc or ~/.zshrc)
   export TELEGRAM_BOT_TOKEN="YOUR_TOKEN"
   export TELEGRAM_CHAT_ID="YOUR_CHAT_ID"
   export REPO_URL="https://bitbucket.vissoft.vn/projects/CT/repos/template-ai-team"
   ```

4. **Restart terminal** to apply environment variables

#### Send Notification (Every Release)

After pushing to remote, run:

```bash
# Send release notification to Telegram
node scripts/send-release-notification.js
```

**Expected output:**
```
🚀 Starting release notification...

📊 Gathering release information...
   Version: 1.2.2-RELEASE
   Type: PATCH
   Date: 2026-01-27
   Commits: 2

📝 Reading CHANGELOG.md...

📤 Formatting Telegram message...

📨 Sending to Telegram...
✅ Release notification sent successfully!
   Message ID: 123
   Chat ID: -987654321
   Chat Title: AI Team Releases

✨ Done!
```

**Telegram message format:**
```
🔧 AI Team Template 1.2.2-RELEASE

📅 Release Date: 2026-01-27
🏷️ Type: PATCH
📝 Commits: 2 commits
🔗 Commit: b913109

Version 1.2.2 - Enhanced project-setup skill

What's New:
### Enhanced
- Enhanced /project-setup command for better existing project integration
- NEW: Prompts user to input full path to existing project directory
[...more entries...]

🔗 View Release
📖 Full Changelog

Released by AI Team Template Maintainers
```

**Troubleshooting:**
- If error occurs, see [TELEGRAM_NOTIFICATION_SETUP.md](TELEGRAM_NOTIFICATION_SETUP.md)
- Verify environment variables are set: `echo $TELEGRAM_BOT_TOKEN`
- Ensure bot is added to channel/group
- Check bot has "Post Messages" permission

### 6. Release Notes Template

When creating GitHub/GitLab release, use this template:

```markdown
# Version X.X.X - Brief Title

**Release Date**: YYYY-MM-DD
**Type**: [PATCH/MINOR/MAJOR]
**Breaking Changes**: [Yes/No]

## What's New

### [Category: Added/Enhanced/Fixed]
- **Feature Name** - Description
  - Benefit or impact
  - Usage example (if applicable)

## Changes Summary

- Total files changed: X
- Total lines added: +X
- Total lines removed: -X

## Documentation

- [CHANGELOG.md](CHANGELOG.md) - Complete changelog
- [README.md](README.md) - Updated quick start
- [Skill/Agent docs] - Updated documentation

## Upgrade Instructions

For existing users:
```bash
git pull origin master
git fetch --tags
git checkout X.X.X-RELEASE
```

## Breaking Changes (if any)

- List breaking changes here
- Migration guide if needed

## Contributors

- @username
- Claude Sonnet 4.5 (AI Assistant)

---

**Full Changelog**: https://github.com/your-org/template-ai-team/compare/PREVIOUS-TAG...X.X.X-RELEASE
```

## Commit Message Format

Follow [Conventional Commits](https://www.conventionalcommits.org/):

### Format:
```
<type>: <subject>

<body>

<footer>
```

### Types:
- **release**: Version release commits
- **feat**: New features
- **fix**: Bug fixes
- **docs**: Documentation changes
- **chore**: Maintenance tasks
- **refactor**: Code refactoring
- **test**: Test additions/changes
- **perf**: Performance improvements

### Examples:

**Release commit:**
```
release: version 1.2.2 - enhanced project-setup skill

Enhanced /project-setup skill for better existing project workflow:
- Prompts user to input existing project directory path
- Automatically navigates to provided directory
- Improves team member onboarding experience
```

**Feature commit:**
```
feat: add /test-task command for automated testing

Implements Test Agent automation via slash command.
Supports API, integration, and E2E testing modes.

Closes #123
```

**Bug fix commit:**
```
fix: resolve MariaDB BigInt serialization error

Added safeJSONStringify() helper to convert BigInt to string.
Prevents "Do not know how to serialize a BigInt" error.

Fixes #456
```

## Tag Format

**Always use annotated tags:**
```bash
git tag -a X.X.X-RELEASE -m "Version X.X.X - Brief description"
```

**Tag naming convention:**
- Format: `X.X.X-RELEASE`
- Examples: `1.2.2-RELEASE`, `1.3.0-RELEASE`, `2.0.0-RELEASE`

**Never use:**
- Lightweight tags (without `-a` flag)
- Different formats like `vX.X.X` or `release-X.X.X`

## Rollback Procedure

If a release needs to be rolled back:

```bash
# Step 1: Revert the commit
git revert HEAD

# Step 2: Delete local tag
git tag -d X.X.X-RELEASE

# Step 3: Delete remote tag (if already pushed)
git push origin :refs/tags/X.X.X-RELEASE

# Step 4: Update CHANGELOG.md
# Move [X.X.X] back to [Unreleased] section

# Step 5: Create new commit
git add CHANGELOG.md
git commit -m "chore: rollback version X.X.X release"

# Step 6: Push changes
git push origin master
```

## Release History

| Version | Date | Type | Description |
|---------|------|------|-------------|
| 1.2.2 | 2026-01-27 | PATCH | Enhanced project-setup skill, improved .gitignore |
| 1.2.1 | 2026-01-26 | PATCH | Fixed MariaDB MCP BigInt serialization |
| 1.2.0 | 2026-01-26 | MINOR | Full task automation, granular agent control |
| 1.1.2 | - | PATCH | Skills restructure |
| 1.1.1 | - | PATCH | Bug fixes |
| 1.1.0 | - | MINOR | Project setup skill, MariaDB MCP |
| 1.0.0 | - | MAJOR | Initial release |

## Best Practices

### DO:
- ✅ Test changes thoroughly before release
- ✅ Update all version numbers consistently
- ✅ Write clear, descriptive commit messages
- ✅ Create annotated tags (not lightweight tags)
- ✅ Document breaking changes clearly
- ✅ Follow semantic versioning strictly
- ✅ Use conventional commit format

### DON'T:
- ❌ Skip CHANGELOG.md updates
- ❌ Create releases without testing
- ❌ Use inconsistent version numbers
- ❌ Push breaking changes in PATCH versions
- ❌ Forget to push tags to remote
- ❌ Use lightweight tags
- ❌ Modify released tags (create new version instead)

## Quick Reference

**For PATCH release (1.2.X):**
```bash
# Update CHANGELOG.md: [Unreleased] → [1.2.X]
# Update README.md: version numbers
git add CHANGELOG.md README.md [other-files]
git commit -m "release: version 1.2.X - description"
git tag -a 1.2.X-RELEASE -m "Version 1.2.X - description"
git push origin master
git push origin 1.2.X-RELEASE

# Send release notification (FINAL STEP)
node scripts/send-release-notification.js
```

**For MINOR release (1.X.0):**
```bash
# Same as PATCH, but ensure new features documented
# Bump MINOR version: 1.2.X → 1.3.0
git commit -m "release: version 1.X.0 - new features"
git tag -a 1.X.0-RELEASE -m "Version 1.X.0 - new features"
git push origin master
git push origin 1.X.0-RELEASE

# Send release notification (FINAL STEP)
node scripts/send-release-notification.js
```

**For MAJOR release (X.0.0):**
```bash
# Document all breaking changes clearly
# Create migration guide if needed
# Bump MAJOR version: 1.X.X → 2.0.0
git commit -m "release: version X.0.0 - breaking changes"
git tag -a X.0.0-RELEASE -m "Version X.0.0 - breaking changes"
git push origin master
git push origin X.0.0-RELEASE

# Send release notification (FINAL STEP)
node scripts/send-release-notification.js
```

---

## Questions?

- Check [CHANGELOG.md](CHANGELOG.md) for examples
- Review previous release commits: `git log --grep="release:" --oneline`
- Check existing tags: `git tag -l | sort -V`
- Telegram notification setup: [TELEGRAM_NOTIFICATION_SETUP.md](TELEGRAM_NOTIFICATION_SETUP.md)

---

## Related Documentation

- **[TELEGRAM_NOTIFICATION_SETUP.md](TELEGRAM_NOTIFICATION_SETUP.md)** - Telegram bot setup and configuration
- **[CHANGELOG.md](../CHANGELOG.md)** - Version history
- **[README.md](../README.md)** - Project overview

---

**Last Updated**: 2026-01-27
**Template Version**: 1.2.2
**Document Type**: Release Process Guide
**Audience**: Template Maintainers Only
