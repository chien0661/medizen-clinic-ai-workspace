# /release - Template Release Automation

## Usage

```bash
/release 1.4.0 MINOR
/release 1.4.1 PATCH
/release 2.0.0 MAJOR
```

**Parameters:**
- `VERSION` - Version number (X.X.X format) - REQUIRED
- `TYPE` - PATCH, MINOR, or MAJOR - REQUIRED

**CRITICAL**: This skill is ONLY for releasing the template repository itself, NOT for projects using this template.

**Model**: Run with `sonnet` — all steps are mechanical (git ops, string replacements, MCP calls). No deep reasoning needed. Switch with `/model sonnet` before invoking.

## Version Type Guidelines

| Type | When to Use | Bump | Example |
|------|-------------|------|---------|
| PATCH | Bug fixes, docs, minor improvements | X.X.N+1 | 1.4.0 → 1.4.1 |
| MINOR | New features, backward compatible | X.N+1.0 | 1.4.1 → 1.5.0 |
| MAJOR | Breaking changes, major refactoring | N+1.0.0 | 1.5.0 → 2.0.0 |

## Step-by-Step Workflow

### Step 1: Validate Prerequisites

```bash
git status
git branch --show-current
grep -n "\[Unreleased\]" CHANGELOG.md
```

**STOP if**: uncommitted changes, not on master, no `[Unreleased]` section, version tag already exists, invalid VERSION format.

### Step 2: Update CHANGELOG.md

Replace `## [Unreleased]` with:
```markdown
## [Unreleased]

---

## [X.X.X] - YYYY-MM-DD
```

Ensure changes are categorized: Added, Changed, Enhanced, Fixed, Deprecated, Removed, Security.

### Step 3: Update README.md (2 locations)

**Location 1** (near line 6-7): `**Version**: X.X.X (YYYY-MM-DD)`

**Location 2** (What's New, ~line 13): `## 🎯 What's New in X.X.X-RELEASE (YYYY-MM-DD)`

### Step 4: Stage and Commit

```bash
git add CHANGELOG.md README.md [other-modified-files]
```

**CRITICAL** - Use exact commit format:
```bash
git commit -m "$(cat <<'EOF'
release: version X.X.X - brief description

Detailed description of changes:
- First major change
- Second major change
- Third major change
EOF
)"
```

### Step 5: Create Annotated Tag

**CRITICAL** - Tag format must be `X.X.X-RELEASE`:
```bash
git tag -a X.X.X-RELEASE -m "Version X.X.X - Brief description"
```

- CORRECT: `1.4.0-RELEASE`
- WRONG: `v1.4.0`, `1.4.0`, `release-1.4.0`

### Step 6: Verify and Push

```bash
git log -1 --oneline
git tag -l | grep "X.X.X-RELEASE"
git push origin master
git push origin X.X.X-RELEASE
```

### Step 7: Telegram Notification (Two-Step)

**Step 7a - Preview** (sends to private chat for review):
```bash
node scripts/send-release-notification.js --preview
```

Review the message in your private chat. If correct, proceed to 7b. If not, fix and re-run `--preview`.

**Step 7b - Send** (sends to team channel after approval):
```bash
node scripts/send-release-notification.js --send
```

**Required env vars**: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` (-5194367684), `TELEGRAM_PRIVATE_CHAT_ID`, `REPO_URL`

### Step 8: Update Confluence User Guide

Update relevant pages in the user guide on Vissoft Confluence based on what changed in this release.

**MCP Server**: `atlassian` | **Space**: `KS`

**Known page map (do NOT re-fetch IDs):**

| Page | ID | Update when... |
|------|----|----------------|
| 9.0 Main (index) | `147624565` | **Every release** — version + date in info macro |
| 9.1 Tổng quan Template | `147624567` | Architecture changed, feature list changed |
| 9.2 Hướng dẫn cài đặt & Quick Start | `147624568` | Setup steps changed, new config, new commands |
| 9.3 Hệ thống Multi-Agent Orchestration | `147624569` | Agent behavior/workflow changed, new agent, fast-track changes |
| 9.4 Danh mục Skills | `147624570` | Skills added, removed, or renamed |
| 9.5 Hệ thống Task Tracking | `147624571` | Task system changed, new status, frontmatter changes |
| 9.6 Persistent Memory | `147624572` | Memory architecture changed, new hooks, new commands |
| 9.7 Tích hợp MCP & Best Practices | `147624573` | MCP servers added/removed, best practices updated |

**8a - Determine which pages need updating:**

Read the `[X.X.X]` section from `CHANGELOG.md` and map to pages:

| CHANGELOG keywords | Pages to update |
|-------------------|-----------------|
| skill, `/command` | 9.0, 9.4 |
| agent, workflow, fast-track, review, dispatch | 9.0, 9.3 |
| setup, install, project-setup, mcp.json | 9.2 |
| task, status, frontmatter, dashboard | 9.5 |
| memory, hook, session | 9.6 |
| MCP, Jira, Confluence, SonarQube, Playwright | 9.7 |
| architecture, overview, cost, token | 9.1 |

**Always update 9.0** regardless of change type.

**8b - For each page to update:**

1. Fetch current version + body:
```
mcp__atlassian__confluence_get_page(pageId: "{ID}", expand: ["version", "body.storage"])
```

2. Apply changes that reflect this release — update facts, numbers, commands, descriptions. Preserve Vietnamese content and page structure.

3. Save:
```
mcp__atlassian__confluence_update_page(
  pageId: "{ID}",
  title: "{same title}",
  body: [updated storage format body],
  version: [version.number + 1]
)
```

**8c - Known structure of 9.0 (main index page):**
```
[INFO MACRO] "Version: X.X.X | Last Updated: YYYY-MM-DD | Repository: ..."  ← update every release
[PARAGRAPH]  intro text
[H2] Mục lục → table of child pages 9.1–9.7                                ← never change
[H2] Đối tượng sử dụng → audience list                                      ← rarely changes
[H2] Tính năng nổi bật → feature table (skill count, agent count, etc.)     ← update if relevant
[NOTE MACRO] "Lưu ý: Template hỗ trợ mọi ngôn ngữ..."                       ← never change
```

**If MCP unavailable**: Skip and append to Telegram message: "⚠️ Confluence manual update needed: https://confluence.vissoft.vn/pages/viewpage.action?pageId=147624565"

### Step 9: Final Verification

```bash
git ls-remote --tags origin | grep "X.X.X-RELEASE"
git log origin/master -1 --oneline
```

Success: tag on remote, commit on master, Telegram sent, Confluence updated, no errors.

## Rollback Procedure

```bash
git revert HEAD
git tag -d X.X.X-RELEASE
git push origin :refs/tags/X.X.X-RELEASE
# Move [X.X.X] back to [Unreleased] in CHANGELOG.md
git add CHANGELOG.md && git commit -m "chore: rollback version X.X.X due to [reason]"
git push origin master
```

## Error Handling

| Error | Fix |
|-------|-----|
| Uncommitted changes | `git stash` or commit first |
| Not on master | `git checkout master && git pull origin master` |
| Version tag exists | Use different version or delete mistaken tag |
| No [Unreleased] section | Add section to CHANGELOG.md, document changes |
| Telegram failed | Check env vars; see `docs/guide/setup/TELEGRAM_NOTIFICATION_SETUP.md` |

## Related Skills

- `/commit-push-pr` - For regular commits (not releases)
- `/upgrade-template` - For projects consuming template updates

---

**Skill Type**: Release Automation
**Audience**: Template Maintainers Only
