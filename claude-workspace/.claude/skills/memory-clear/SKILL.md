# Skill: memory-clear

## Description
Clear persistent memory for current project or all projects

## Invocation
```bash
/memory-clear                    # Clear current project only
/memory-clear --all              # Clear all projects (requires confirmation)
```

## Purpose
Remove stored observations and sessions from the memory database. Useful for:
- Starting fresh on a project
- Clearing sensitive data that was accidentally captured
- Resetting memory after major refactoring

## Usage Examples

```bash
# Clear current project memory
/memory-clear

# Clear all projects (will prompt for confirmation)
/memory-clear --all
```

## Safety Features
- Current project only by default
- Confirmation required for --all flag
- Cannot be undone (backup database first if unsure)

## Database Location
- Database: `~/.claude-mem/memory.db`
- Backup before clearing: `cp ~/.claude-mem/memory.db ~/.claude-mem/memory.db.backup`

---

**Last Updated:** 2026-02-03
