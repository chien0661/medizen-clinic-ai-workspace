# Skill: confluence

## Description
Bidirectional Confluence sync: **import** pages from Confluence into local markdown files, or **publish** local documentation back to Confluence.

## Invocation
```bash
# IMPORT: Confluence → docs/
/confluence import "Page Title"                    # Import by title
/confluence import --page-id 123456                # Import by page ID
/confluence import --space PROJ                    # Import all pages from space
/confluence import --parent "API Docs"             # Import child pages
/confluence import "Page Title" --update           # Update existing local docs
/confluence import --page-id 172694270 --vds       # Import from VDS partner Confluence

# PUBLISH: docs/ → Confluence
/confluence publish TASK-001                       # Publish task documentation
/confluence publish TASK-001 --update              # Update existing page
/confluence publish --all-done                     # Publish all completed tasks
/confluence publish TASK-001 --space PROJ --parent "API Docs"
/confluence publish TASK-001 --vds --template detail-design  # VDS partner Confluence
/confluence publish TASK-001 --vds --template srs
```

## Two Confluence Instances

| Aspect | Vissoft Internal (default) | VDS Partner (`--vds`) |
|--------|---------------------------|----------------------|
| **MCP Server** | `atlassian` | `atlassian-vds` |
| **URL** | https://confluence.vissoft.vn | http://10.254.136.35:8090 |
| **Import output** | Markdown (auto-converted) | HTML preserved (VDS format) |
| **Publish template** | Auto-generated from artifacts | VDS HTML templates from docs/templates/specs/ |

---

## IMPORT Mode (`/confluence import`)

Import Confluence pages as local markdown files. **Read-only from Confluence.**

### Step 1: Find Page
- By title: Search via Confluence MCP, prompt if multiple matches
- By page ID: Direct fetch
- By space: Get all pages in space
- By parent: Get child pages of parent

### Step 2: Read Content
Get page metadata (title, space, dates, author, labels) and body in storage format.

### Step 3: Convert to Markdown
| Confluence Element | Markdown |
|-------------------|----------|
| `<h1>` | `#` |
| `<strong>` | `**bold**` |
| Code macro | ` ```language ``` ` |
| Info panel | `> **Info:** text` |
| HTML table | Markdown table |
| Status macro | Badge text |

### Step 4: Determine Local Location
Auto-classify by keywords in title/labels:

| Keywords | Destination |
|----------|-------------|
| API, Endpoint, REST | `docs/api/` |
| Feature, Guide, How to | `docs/features/` |
| SRS, Specification, Architecture | `docs/templates/specs/` |
| Tutorial, Setup | `docs/guide/setup/` |
| Default | `docs/confluence-imports/` |

Override with `--folder docs/custom/`.

### Step 5: Save File
Generate YAML frontmatter (title, source URL, page ID, space, dates, labels) + converted content.

### Import Parameters

| Parameter | Description |
|-----------|-------------|
| `"Title"` | Search by page title |
| `--page-id ID` | Fetch by exact page ID |
| `--space KEY` | Import all pages from space |
| `--parent "Title"` | Import child pages under parent |
| `--vds` | Import from VDS partner Confluence |
| `--folder path` | Override destination folder |
| `--update` | Overwrite existing local file |
| `--if-newer` | Only import if Confluence page is newer |
| `--with-attachments` | Download attachments |
| `--dry-run` | Preview without saving |

### VDS Common Page IDs
- `172694270` - SRS template (KBNV_Thong ke MiniApp)
- `131710958` - Detail Design template (Luong xac thuc OpenAPI)

### Import Error Handling
| Error | Solution |
|-------|----------|
| Page not found | Check title spelling, use `--page-id` instead |
| Multiple matches | Specify `--space` to disambiguate |
| Permission denied | Verify token has read access |
| Conversion issues | Unsupported macros saved as HTML comments |
| File exists | Use `--update` to overwrite |

---

## PUBLISH Mode (`/confluence publish`)

Generate documentation from task artifacts and publish to Confluence.

### Step 1: Gather Sources
Read from local docs/:
- `docs/tasks/TASK-XXX/task.md` - title, description, requirements, Jira link
- `docs/tasks/TASK-XXX/deliveries/api-specs/` - API endpoints, request/response
- `docs/tasks/TASK-XXX/deliveries/final-specs/` - feature description
- `docs/tasks/TASK-XXX/handoff/review-report.md` - review decision, issues
- `docs/tasks/TASK-XXX/deliveries/test-reports/test-report.md` - test results, coverage
- Code examples from implementation files
- Git info (branch, commits, files changed)

### Step 2: Generate Confluence Page

**Page title convention**: `[Task Title] - Implementation Documentation`

Convert markdown to Confluence storage format (XHTML):
- Code blocks → `<ac:structured-macro ac:name="code">` with language
- Status badges → `<ac:structured-macro ac:name="status">` with colour
- Info panels → `<ac:structured-macro ac:name="info">`
- Tables → HTML `<table><tr><th>...</th></tr><tr><td>...</td></tr></table>`

Page sections: Overview, API Documentation, Implementation Details, Code Examples, Test Results, Review Summary, Related Links.

### Step 3: Create/Update Page

**Create**: `confluence_create_page(spaceKey, title, body, parentId)`
**Update**: `confluence_update_page(pageId, title, body, version)` — version **required** for conflict detection

Steps:
1. Find space and verify write permission
2. Check if page exists (search by title)
3. Find parent page (if specified)
4. Create or update via Confluence MCP
5. Get page URL from response

### Step 4: Link Back
- Update task file with Confluence link
- Optionally sync status to Jira via `/jira export`

### VDS Publishing Workflow
1. Copy VDS template: `cp docs/templates/specs/vds-detail-design-template.html docs/templates/specs/my-service-detail-design.html`
2. Fill all sections with content
3. Publish: `/confluence publish TASK-001 --vds --template detail-design`
4. Verify at http://10.254.136.35:8090

VDS templates: `docs/templates/specs/vds-srs-template.html`, `docs/templates/specs/vds-detail-design-template.html`
See: `docs/guide/reference/VDS_CONFLUENCE_PUBLISHING.md` for full VDS guide.

### Publish Parameters

| Parameter | Description |
|-----------|-------------|
| `TASK-ID` | Task to publish documentation for |
| `--update` | Update existing page (preserve page ID) |
| `--all-done` | Publish all DONE tasks |
| `--space KEY` | Target Confluence space |
| `--parent "Title"` | Create as child of this page |
| `--vds` | Publish to VDS partner Confluence |
| `--template [srs\|detail-design]` | VDS template type |
| `--title "Custom Title"` | Override page title |
| `--dry-run` | Preview without publishing |

### Publish Error Handling
| Error | Solution |
|-------|----------|
| Page already exists | Use `--update` flag |
| Permission denied | Verify CONFLUENCE_TOKEN has write access |
| Parent page not found | Create parent in Confluence first |
| Missing documentation | Run Documentation Agent first, or use `--partial` |
| Storage format invalid | Use `--dry-run` to preview |

---

## Related Skills
- `/jira` - Import/export Jira tasks
- `/publish-lesson-learn` - Publish lessons learned to Confluence
- `/complete-task` - Complete task before publishing

---

**Skill Type**: Confluence Integration (Bidirectional)
**MCP Servers**: `atlassian` (Vissoft), `atlassian-vds` (VDS partner)
**Directions**: Confluence → docs/ (import) | docs/ → Confluence (publish)
