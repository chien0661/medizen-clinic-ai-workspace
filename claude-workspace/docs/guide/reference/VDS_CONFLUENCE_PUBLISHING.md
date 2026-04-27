# Publishing Documents to VDS Confluence

## Overview

This guide explains how to publish technical documentation (SRS, Detail Design) to VDS partner's Confluence server using the VDS HTML templates and MCP tools.

---

## Workflow

```
┌─────────────────────────────────────────────────────┐
│  1. Write Document Locally (Markdown in docs/)     │
│     - Use markdown for local documentation          │
│     - Track changes in Git                          │
└─────────────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────┐
│  2. Convert to VDS HTML Format                      │
│     - Use HTML templates in docs/templates/specs/            │
│     - Preserve VDS table structures                 │
│     - Add PlantUML diagrams with ac:structured-macro│
└─────────────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────┐
│  3. Publish to VDS Confluence via MCP               │
│     - Use confluence_create_page or                 │
│     - Use confluence_update_page                    │
│     - MCP: atlassian-vds                           │
└─────────────────────────────────────────────────────┘
```

---

## HTML Templates

Two HTML templates are available in `docs/templates/specs/`:

| Template | File | VDS Reference | Purpose |
|----------|------|---------------|---------|
| **SRS Template** | `vds-srs-template.html` | [Page 172694270](http://10.254.136.35:8090/pages/viewpage.action?pageId=172694270) | Software Requirements Specification |
| **Detail Design Template** | `vds-detail-design-template.html` | [Page 131710958](http://10.254.136.35:8090/pages/viewpage.action?pageId=131710958) | Service Detail Design Document |

---

## Template Structure

### VDS SRS Template

**Key Sections:**
- Change log table (Bảng ghi nhận thay đổi)
- Table of Contents (TOC macro)
- Overview (Tổng quan)
- Feature sections with:
  - Screen descriptions (Mô tả màn hình)
  - Sequence diagrams (PlantUML)
  - Activity diagrams (PlantUML)
  - Flow descriptions (Mô tả luồng)
- Data model (Mô hình dữ liệu)
- Business rules (Quy tắc nghiệp vụ)
- Non-functional requirements (Yêu cầu phi chức năng)
- Acceptance criteria (Tiêu chí chấp nhận)

### VDS Detail Design Template

**Key Sections:**
- Change log table
- References (Danh sách tài liệu tham khảo)
- Service name and description
- Features (Tính năng)
- Service API table
- Functional requirements
- Non-functional requirements (detailed)
- Technology stack (Stack công nghệ)
- Database design (Thiết kế CSDL)
- Detailed flow with PlantUML diagrams
- API specifications
- Data governance compliance

---

## Step-by-Step Publishing Guide

### Step 1: Prepare Your Content

1. **Write your document locally** in markdown (for team use)
2. **Identify the content sections** that need to be published to VDS
3. **Choose the appropriate template**: SRS or Detail Design

### Step 2: Fill the HTML Template

1. **Copy the template file**:
   ```bash
   cp docs/templates/specs/vds-srs-template.html docs/templates/specs/my-project-srs.html
   # or
   cp docs/templates/specs/vds-detail-design-template.html docs/templates/specs/my-service-detail-design.html
   ```

2. **Edit the HTML file**:
   - Replace all placeholder text `[...]` with your actual content
   - Update the change log table with version history
   - Replace PlantUML diagram code with your actual diagrams
   - Update tables with your specific data

3. **Preserve VDS-specific HTML structure**:
   - ✅ Keep table classes: `class="wrapped"`, `class="relative-table wrapped"`
   - ✅ Keep column group definitions: `<colgroup>` and `<col>` tags
   - ✅ Keep text styling: `<span style="color: rgb(0,51,102);">`
   - ✅ Keep PlantUML macros: `<ac:structured-macro ac:name="plantuml">`
   - ✅ Keep TOC macro: `<ac:structured-macro ac:name="toc">`

### Step 3: Add PlantUML Diagrams

VDS Confluence uses PlantUML for diagrams. Format:

```html
<ac:structured-macro ac:name="plantuml" ac:schema-version="1" ac:macro-id="unique-id">
<ac:parameter ac:name="atlassian-macro-output-type">INLINE</ac:parameter>
<ac:plain-text-body><![CDATA[@startuml Diagram_Name

' Your PlantUML code here
actor User
participant Service
database DB

User -> Service: Request
Service -> DB: Query
DB --> Service: Result
Service --> User: Response

@enduml]]></ac:plain-text-body>
</ac:structured-macro>
```

**Common diagram types:**
- **Sequence Diagram**: Show interaction between components
- **Activity Diagram**: Show process flow with conditions
- **ERD**: Show database entity relationships

### Step 4: Validate HTML Content

Before publishing, check:
- [ ] All placeholders `[...]` are replaced
- [ ] Tables have proper structure (headers, rows, cells)
- [ ] PlantUML syntax is valid (no syntax errors)
- [ ] Vietnamese characters display correctly
- [ ] Change log table is filled with initial version
- [ ] No broken HTML tags

### Step 5: Publish to VDS Confluence

#### Option A: Create New Page

Use Claude Code with MCP:

```
Create a new Confluence page in VDS server:
- Space key: [SPACE_KEY]
- Title: "[Project Name] - SRS"
- Parent page ID: [PARENT_PAGE_ID] (optional)
- Body: Read from docs/templates/specs/my-project-srs.html

Use mcp__atlassian-vds__confluence_create_page
```

#### Option B: Update Existing Page

```
Update existing Confluence page in VDS server:
- Page ID: [PAGE_ID]
- Title: "[Updated Title]"
- Version: [CURRENT_VERSION_NUMBER]
- Body: Read from docs/templates/specs/my-project-detail-design.html

Use mcp__atlassian-vds__confluence_update_page
```

---

## MCP Commands Reference

### Create New Page

**Tool**: `mcp__atlassian-vds__confluence_create_page`

**Parameters**:
```json
{
  "spaceKey": "PROJ",
  "title": "My Project - SRS v1.0",
  "body": "<p>HTML content here...</p>",
  "parentId": "123456789"  // optional
}
```

### Update Existing Page

**Tool**: `mcp__atlassian-vds__confluence_update_page`

**Parameters**:
```json
{
  "pageId": "172694270",
  "title": "My Project - SRS v1.1",
  "body": "<p>Updated HTML content...</p>",
  "version": 2  // Must be current version number
}
```

**⚠️ IMPORTANT**:
- You MUST provide the current version number
- Get current version first using `confluence_get_page`
- Confluence will reject if version doesn't match

### Get Page Version

```
Read page to get current version:
Use mcp__atlassian-vds__confluence_get_page with pageId=[PAGE_ID]

Check the response for: version.number
```

---

## Example Workflow

### Example 1: Publishing New SRS

```bash
# Step 1: Prepare HTML
cd docs/specs
cp vds-srs-template.html user-management-srs.html

# Step 2: Edit the HTML file with your content
# (Use your preferred editor)

# Step 3: Use Claude Code to publish
claude
```

Then in Claude Code:
```
Create a new Confluence page in VDS server (PROJ space):
- Title: "User Management - SRS v1.0"
- Read HTML content from: docs/templates/specs/user-management-srs.html
- Publish to VDS Confluence using atlassian-vds MCP server
```

### Example 2: Updating Detail Design

```
I need to update the Detail Design document for Auth Service:
- VDS Confluence page ID: 131710958
- First, get the current version number
- Then update with new content from: docs/templates/specs/auth-service-detail-design.html
- Use atlassian-vds MCP server
```

---

## Best Practices

### 1. Version Control

**Local markdown (for team)**:
- Store in `docs/api/`, `docs/features/`, etc.
- Track changes in Git
- Use for day-to-day team reference

**VDS HTML (for partner)**:
- Store in `docs/templates/specs/` with descriptive names
- Only publish major versions to VDS
- Keep HTML files in Git for history

### 2. Change Log Management

**Always update the change log table** when publishing updates:

```html
<tr>
<td style="text-align: left;">2026-01-27</td>
<td style="text-align: left;">Section 3.2</td>
<td style="text-align: left;">M</td>
<td style="text-align: left;">User feedback</td>
<td style="text-align: left;">CR-123</td>
<td style="text-align: left;">Updated authentication flow</td>
<td style="text-align: left;">1.1</td>
<td style="text-align: left;">John Doe</td>
</tr>
```

### 3. Diagram Management

**Store diagram source code**:
- Keep `.puml` files in `docs/diagrams/`
- Reference them in HTML templates
- Makes updates easier

**Example directory structure**:
```
docs/
├── specs/
│   ├── vds-srs-template.html
│   ├── vds-detail-design-template.html
│   ├── user-management-srs.html
│   └── auth-service-detail-design.html
├── diagrams/
│   ├── user-management-sequence.puml
│   ├── user-management-activity.puml
│   └── auth-service-flow.puml
└── api/
    └── user-management-api.md (local team docs)
```

### 4. Review Before Publishing

**Checklist**:
- [ ] Content reviewed by technical lead
- [ ] Diagrams render correctly in local PlantUML preview
- [ ] Tables are properly formatted
- [ ] All Vietnamese characters display correctly
- [ ] Version number updated
- [ ] Change log updated
- [ ] No placeholder text remaining

### 5. Coordinate with VDS Partner

**Before first publish**:
- [ ] Get VDS Confluence space key from partner
- [ ] Confirm document structure matches their standards
- [ ] Agree on version numbering scheme
- [ ] Establish approval workflow

**During updates**:
- [ ] Notify partner before major updates
- [ ] Get approval for structure changes
- [ ] Follow agreed-upon review process

---

## Troubleshooting

### Issue: "Version conflict" error

**Cause**: The page has been updated since you last checked

**Solution**:
1. Get current version: `confluence_get_page` with pageId
2. Merge your changes with latest version
3. Retry update with correct version number

### Issue: PlantUML diagram not rendering

**Cause**: Syntax error in PlantUML code

**Solution**:
1. Test diagram syntax at http://www.plantuml.com/plantuml/
2. Check for special characters that need escaping
3. Ensure `@startuml` and `@enduml` tags are present

### Issue: Table formatting broken

**Cause**: Missing or incorrect HTML table structure

**Solution**:
1. Verify `<colgroup>` matches number of columns
2. Check all `<tr>` have same number of `<td>` cells
3. Ensure no unclosed tags

### Issue: "Page not found" after creation

**Cause**: Wrong space key or insufficient permissions

**Solution**:
1. Verify space key with partner
2. Check VDS_CONFLUENCE_PAT has create permissions
3. Try creating in a different space (test space)

---

## FAQ

### Q: Should I write documentation in HTML from the start?

**A**: No! Write in markdown locally for your team. Only convert to HTML when ready to publish to VDS partner.

**Workflow**:
1. ✅ Write and maintain in markdown (`docs/api/`, `docs/features/`)
2. ✅ Convert to VDS HTML format when publishing milestone versions
3. ✅ VDS Confluence is for partner visibility, not primary documentation

### Q: How often should I publish to VDS Confluence?

**A**: Only publish significant milestones:
- ✅ Initial version (v1.0)
- ✅ Major feature additions
- ✅ Significant design changes
- ❌ Daily updates
- ❌ Minor bug fixes
- ❌ Work-in-progress

### Q: Can I use markdown in Confluence?

**A**: No, VDS Confluence requires HTML in their specific format. Use the templates provided.

### Q: What if the template doesn't match my needs?

**A**: You can modify the template, but:
1. Keep the change log table structure
2. Keep the TOC macro
3. Maintain Vietnamese section headers
4. Coordinate significant structure changes with VDS partner

### Q: How do I handle images/screenshots?

**A**:
1. Upload images to Confluence first (via UI or API)
2. Reference in HTML: `<ac:image><ri:attachment ri:filename="screenshot.png" /></ac:image>`
3. Or use external image URLs: `<ac:image><ri:url ri:value="https://..." /></ac:image>`

### Q: Can I automate the markdown to HTML conversion?

**A**: Yes! You can create a script to:
1. Parse markdown structure
2. Map sections to VDS HTML template
3. Convert diagrams to PlantUML format
4. Generate final HTML

Consider creating this if you publish frequently.

---

## Related Documentation

- [MCP_SETUP_PARTNER.md](MCP_SETUP_PARTNER.md) - Setup VDS MCP connection
- [.mcp.json](.mcp.json) - MCP server configuration
- [VDS SRS Template](specs/vds-srs-template.html) - SRS HTML template
- [VDS Detail Design Template](specs/vds-detail-design-template.html) - Detail Design HTML template

---

**Last Updated**: 2026-01-27
**Version**: 1.0
