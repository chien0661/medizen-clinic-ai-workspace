# Skill: memory-export

## Description
Export persistent memory to markdown file for review or backup

## Invocation
```bash
/memory-export                           # Export to docs/memory-export.md
/memory-export --file custom.md          # Export to custom file
/memory-export --project myproject       # Export specific project
```

## Purpose
Export captured observations and session summaries to a markdown file for:
- Reviewing past work
- Creating project documentation
- Backing up memory before clearing
- Sharing context with team members

## Usage Examples

```bash
# Export current project to default file
/memory-export

# Export to custom location
/memory-export --file reports/memory-backup.md

# Export specific project
/memory-export --project template-ai-team

# Export with date range
/memory-export --from 2026-01-01 --to 2026-02-01
```

## Output Format

Markdown timeline with:
- Session summaries
- Key observations
- Decisions made
- Lessons learned
- Next steps

## Integration
Queries memory database and formats as readable markdown documentation.

---

**Last Updated:** 2026-02-03
