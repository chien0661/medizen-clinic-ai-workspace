# Skill: memory-search

## Description
Search persistent memory for relevant past work across all sessions

## Invocation
```bash
/memory-search "query"
/memory-search "authentication JWT" --limit 10
/memory-search "database" --type Read --project myproject
```

## Purpose
Search through captured observations from previous sessions to find relevant context, decisions, and patterns. Uses token-efficient three-layer search workflow.

## Usage Examples

```bash
# Basic search
/memory-search "authentication login"

# Search specific tool type
/memory-search "database migration" --type Bash

# Limit results
/memory-search "API endpoint" --limit 5

# Search specific project
/memory-search "bug fix" --project template-ai-team
```

## How It Works

Uses MCP tools via three-layer progressive disclosure:
1. **Layer 1:** Compact index search (~50-100 tokens per result)
2. **Layer 2:** Timeline context for selected results (~200-300 tokens)
3. **Layer 3:** Full details for final 1-3 observations (~500-1000 tokens)

## Integration
Works with persistent memory MCP server automatically. No manual setup required.

---

**Token Efficiency:** Very High (10x savings vs traditional RAG)
**Last Updated:** 2026-02-03
