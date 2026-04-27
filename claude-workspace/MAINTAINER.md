# Template Maintainer Notes

Guidelines and lessons learned for maintaining this template. **Not copied to projects.**

---

## Before Deleting Any Skill

**Always grep `.claude/agents/` first** before removing a skill:

```bash
grep -r "/skill-name" .claude/agents/
```

A skill may appear unused from the user-facing side but be actively called by agents internally.

**Lesson**: `/handoff` skill was deleted as "redundant" but `code-implementation.md`, `code-review.md`, and `test.md` all called it to create handoff files. Required significant rework to replace with direct Write tool instructions in all 3 agent files.

---

## Do NOT Delete

| File | Reason |
|------|--------|
| `scripts/send-release-notification.js` | Required by `/release` skill Step 7 (Telegram notification). Was accidentally deleted and had to be recovered from git history. |

---

## Release Checklist

When running `/release X.X.X TYPE`:

1. Use `sonnet` model (`/model sonnet` before invoking) — all steps are mechanical
2. After Telegram preview, verify message before sending to team channel
3. Confluence pages to always update: `147624565` (9.0 index) — every release
4. Move tag if post-release commits are made: delete + recreate tag at HEAD

---

## Skill Dependency Map

Skills that agents call internally (not just user-facing):

| Skill | Called by agents |
|-------|-----------------|
| `/task-status` | All 4 agents (update task state) |
| `/auto-build` | code-implementation, code-review, test |
| `/memory-search` | All 4 agents (first step) |

---

## File Not Copied to Projects

`/project-setup` copies: `CLAUDE.md`, `PROJECT.md`, `.claude/`, `scripts/`, `docs/templates/`, `.mcp.json.example`, `.env.example`, `.gitignore`

**Not copied**: `MAINTAINER.md`, `CHANGELOG.md`, `README.md`, `deployment/`, `mcp-servers/`
