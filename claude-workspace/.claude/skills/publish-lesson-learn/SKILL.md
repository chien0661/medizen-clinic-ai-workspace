# /publish-lesson-learn - Publish Lessons Learned

## Usage

```bash
/publish-lesson-learn
```

**When to use**: After fixing a difficult technical issue, discovering a non-obvious solution, or resolving an issue that took significant effort.

## What It Does

1. **Gathers Information** (interactive prompts): Issue title, category, problem description, root cause, solution, key takeaways
2. **Creates Local Backup**: `docs/lessons-learned/LESSON-XXX.md` with YAML frontmatter
3. **Publishes to Confluence**: Updates VISSoft Confluence page (ID: 147621793) via MCP
   - Reads existing page
   - Adds entry to table of contents
   - Appends formatted lesson content (XHTML)

## Prerequisites

- VISSoft Confluence MCP server (`atlassian`) configured in `.mcp.json`
- Environment variables: `ATLASSIAN_USERNAME`, `ATLASSIAN_API_TOKEN`

## Local File Format

`docs/lessons-learned/LESSON-XXX.md`:
```markdown
---
id: LESSON-001
date: 2026-02-03
category: Database
severity: High
tags: [postgresql, connection-pool]
---
# LESSON-001: Title
## Problem
## Root Cause
## Solution
## Key Takeaways
## References
```

## Confluence Format

Converts to XHTML with `<h2>`, `<h3>`, `<ac:structured-macro ac:name="code">` for code blocks.

## Categories

Database, API, Performance, Security, Infrastructure, Integration, Frontend, Backend

## Error Handling

| Error | Solution |
|-------|----------|
| Confluence MCP unavailable | Local file created; publish manually later |
| Page version conflict | Retries with latest version; saves to temp file if still fails |
| Authentication fails | Check ATLASSIAN_USERNAME and ATLASSIAN_API_TOKEN |

## Related Skills

- `/task-status` - Update task status
- `/confluence import` - Import from Confluence (reverse direction)

---

**Skill Type**: Knowledge Management (Confluence Integration)
**MCP Server**: `atlassian` (VISSoft)
**Direction**: docs/lessons-learned/ → Confluence page 147621793
