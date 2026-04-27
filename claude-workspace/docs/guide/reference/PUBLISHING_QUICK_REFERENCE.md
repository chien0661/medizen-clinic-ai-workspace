# Publishing Documentation - Quick Reference

## Two Publishing Destinations

### 1️⃣ Vissoft Internal Confluence
**For**: Internal team documentation
**URL**: https://confluence.vissoft.vn
**MCP Server**: `atlassian` (remote via mcp-client.js)
**Format**: Auto-generated from task artifacts
**Command**: `/publish-confluence TASK-001`

### 2️⃣ VDS Partner Confluence
**For**: Partner documentation following VDS standards
**URL**: http://10.254.136.35:8090
**MCP Server**: `atlassian-vds` (local server)
**Format**: VDS HTML templates (SRS or Detail Design)
**Command**: `/publish-confluence TASK-001 --vds --template [srs|detail-design]`

---

## Quick Command Reference

### Publishing (docs/ → Confluence)

```bash
# ═══════════════════════════════════════════════════
# VISSOFT INTERNAL (Default)
# ═══════════════════════════════════════════════════

# Publish single task (auto-generated content)
/publish-confluence TASK-001

# Update existing page
/publish-confluence TASK-001 --update

# Publish all completed tasks
/publish-confluence --all-done

# Publish to specific space with parent
/publish-confluence TASK-001 --space PROJ --parent "API Documentation"


# ═══════════════════════════════════════════════════
# VDS PARTNER
# ═══════════════════════════════════════════════════

# Publish Detail Design (service/API documentation)
/publish-confluence TASK-001 --vds --template detail-design

# Publish SRS (requirements/features documentation)
/publish-confluence TASK-001 --vds --template srs

# Update existing VDS page
/publish-confluence TASK-001 --vds --template detail-design --update
```

### Importing (Confluence → docs/)

```bash
# ═══════════════════════════════════════════════════
# VISSOFT INTERNAL (Default)
# ═══════════════════════════════════════════════════

# Import single page by title
/import-confluence "User Profile API"

# Import by page ID
/import-confluence --page-id 123456

# Import all pages from space
/import-confluence --space PROJ

# Import all child pages under parent
/import-confluence --parent "API Documentation"


# ═══════════════════════════════════════════════════
# VDS PARTNER
# ═══════════════════════════════════════════════════

# Import SRS template (page ID: 172694270)
/import-confluence --page-id 172694270 --vds --folder docs/templates/specs/

# Import Detail Design template (page ID: 131710958)
/import-confluence --page-id 131710958 --vds --folder docs/templates/specs/

# Import any VDS page by ID
/import-confluence --page-id [PAGE_ID] --vds --folder docs/templates/specs/
```

---

## Template Files

| Template | Location | Use For |
|----------|----------|---------|
| **VDS SRS** | `docs/templates/specs/vds-srs-template.html` | Requirements, features, user stories |
| **VDS Detail Design** | `docs/templates/specs/vds-detail-design-template.html` | Service design, API specs, database |

---

## Publishing Workflow

### For Internal (Vissoft)

```
1. Complete task → docs/tasks/dashboard.md, docs/api/, docs/reviews/
2. Run: /publish-confluence TASK-001
3. ✅ Published to https://confluence.vissoft.vn
```

### For Partner (VDS)

```
1. Copy template:
   cp docs/templates/specs/vds-detail-design-template.html \
      docs/templates/specs/auth-service-detail-design.html

2. Fill template with your content:
   - Update change log
   - Fill all sections
   - Add PlantUML diagrams
   - Replace all [placeholders]

3. Run: /publish-confluence TASK-001 --vds --template detail-design

4. ✅ Published to http://10.254.136.35:8090
```

---

## MCP Server Configuration

### Vissoft Internal (`atlassian`)
```json
{
  "atlassian": {
    "command": "node",
    "args": ["mcp-client.js"],
    "env": {
      "MCP_SERVER_URL": "https://mcp-server.vissoft.vn",
      "CONFLUENCE_URL": "https://confluence.vissoft.vn",
      "CONFLUENCE_TOKEN": "${CONFLUENCE_TOKEN}"
    }
  }
}
```
**Environment Variable**: `CONFLUENCE_TOKEN`

### VDS Partner (`atlassian-vds`)
```json
{
  "atlassian-vds": {
    "command": "node",
    "args": ["mcp-servers/mcp-vds-server/dist/index.js"],
    "env": {
      "CONFLUENCE_BASE_URL": "http://10.254.136.35:8090",
      "CONFLUENCE_PAT": "${VDS_CONFLUENCE_PAT}",
      "TRANSPORT": "stdio"
    }
  }
}
```
**Environment Variable**: `VDS_CONFLUENCE_PAT`

---

## Key Differences

| Aspect | Vissoft Internal | VDS Partner |
|--------|-----------------|-------------|
| **MCP Server** | `atlassian` (remote) | `atlassian-vds` (local) |
| **Template** | Auto-generated | Manual HTML templates |
| **Format** | English, Confluence macros | Vietnamese headers, PlantUML |
| **Source** | Task artifacts (docs/) | Filled HTML templates |
| **Audience** | Internal team | VDS partner |
| **Standards** | Flexible | VDS-specific format |

---

## Decision Matrix

**Choose Vissoft Internal when:**
- ✅ Internal documentation
- ✅ Auto-generate from task artifacts
- ✅ English content
- ✅ Flexible formatting

**Choose VDS Partner when:**
- ✅ Partner visibility required
- ✅ Must follow VDS standards
- ✅ Vietnamese section headers
- ✅ Formal SRS/Detail Design format

---

## Common Workflows

### Workflow 1: Import VDS Template → Customize → Publish Back
```bash
# 1. Import VDS template
/import-confluence --page-id 131710958 --vds --folder docs/templates/specs/

# 2. Copy and customize for your service
cp docs/templates/specs/vds-detail-design-luong-xac-thuc-openapi.html \
   docs/templates/specs/my-service-detail-design.html
# (Edit and fill content)

# 3. Publish back to VDS
/publish-confluence TASK-001 --vds --template detail-design
```

### Workflow 2: Internal Documentation Sync
```bash
# Import from Vissoft Confluence
/import-confluence "User Profile API" --update

# Edit locally in docs/api/user-profile-api.md

# Publish back to Vissoft Confluence
/publish-confluence TASK-001 --update
```

### Workflow 3: Cross-Publish (Internal + Partner)
```bash
# Publish to internal Confluence (team)
/publish-confluence TASK-001
# → https://confluence.vissoft.vn

# Also publish to VDS partner (formal docs)
/publish-confluence TASK-001 --vds --template detail-design
# → http://10.254.136.35:8090
```

## Related Documentation

- **Publishing Skill**: [.claude/skills/publish-confluence/SKILL.md](../.claude/skills/publish-confluence/SKILL.md)
- **Import Skill**: [.claude/skills/import-confluence/SKILL.md](../.claude/skills/import-confluence/SKILL.md)
- **VDS Publishing Guide**: [docs/VDS_CONFLUENCE_PUBLISHING.md](VDS_CONFLUENCE_PUBLISHING.md)
- **VDS MCP Setup**: [docs/MCP_SETUP_PARTNER.md](MCP_SETUP_PARTNER.md)
- **Templates**:
  - [docs/templates/specs/vds-srs-template.html](specs/vds-srs-template.html)
  - [docs/templates/specs/vds-detail-design-template.html](specs/vds-detail-design-template.html)

---

## Troubleshooting

### "MCP Server not found: atlassian-vds"
**Fix**: VDS MCP server not configured or not started
```bash
# Check .mcp.json configuration
# Verify VDS_CONFLUENCE_PAT environment variable set
# Restart Claude Code
```

### "Template file not found"
**Fix**: VDS HTML template doesn't exist
```bash
# Copy template
cp docs/templates/specs/vds-detail-design-template.html \
   docs/templates/specs/my-service-detail-design.html

# Fill content and retry
```

### "Permission denied" on VDS Confluence
**Fix**: PAT token doesn't have write permissions
```bash
# Contact VDS admin to verify token permissions
# Ensure token has "Write" access to target space
```

---

**Quick Tip**:
- For **internal docs** → Use default command: `/publish-confluence TASK-001`
- For **partner docs** → Add `--vds --template detail-design` flag

---

**Last Updated**: 2026-01-27
