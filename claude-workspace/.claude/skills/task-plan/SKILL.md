# /task-plan - Interactive Task Planning

## Usage

```bash
/task-plan TASK-001          # Plan task interactively
/task-plan TASK-001 --update # Re-plan: overwrite implementation-plan.md + update refs
```

## What This Command Does

Runs an **interactive planning session** với user để:
1. Thu thập tài liệu đầu vào và requirements
2. Cùng user xây dựng implementation plan
3. Lưu plan vào `docs/tasks/TASK-ID/refs/implementation-plan.md`
4. Cập nhật `refs` trong frontmatter của `task.md` (reference đến tất cả input docs)

**Optional** — bỏ qua nếu task đã có đủ thông tin, hoặc khi dùng `/complete-task`.

---

## When to Use

| Scenario | Recommendation |
|----------|----------------|
| Có DetailDesign từ BA/Tech Lead | `/task-plan` để review, clarify, tạo impl plan |
| Có Figma, Confluence, Jira links | `/task-plan` để collect refs và plan |
| Task description còn mơ hồ | `/task-plan` để clarify với user |
| Task đơn giản, tự giải thích | Bỏ qua — điền `task.md` thủ công |
| Chạy `/complete-task` automation | Bỏ qua |

---

## Interactive Flow

### Step 1 — Đọc task hiện tại
- Đọc `docs/tasks/TASK-ID/task.md`
- Liệt kê files trong `docs/tasks/TASK-ID/refs/` nếu có
- Nếu tìm thấy files → thông báo: *"Tìm thấy trong refs/: [list]. Sẽ dùng làm tài liệu đầu vào."*

### Step 2 — Thu thập requirements
Hỏi user:

> "Mô tả task **TASK-ID** — yêu cầu, bối cảnh, mục tiêu.
> Nếu có tài liệu tham chiếu (Figma, Confluence, Jira, file trong refs/), cung cấp link hoặc path."

User cung cấp:
- Text description
- Path file đã đặt trong `refs/` (DetailDesign, SRS, v.v.)
- Figma URL / Confluence URL / Jira ticket key
- Bất kỳ ref nào khác

### Step 3 — Đọc tài liệu đầu vào
- Đọc files trong `refs/` được đề cập
- Fetch Confluence page qua MCP nếu cấu hình
- Đọc Jira ticket qua MCP nếu cấu hình
- Đặt câu hỏi làm rõ nếu requirements còn mơ hồ

### Step 4 — Xây dựng implementation plan
Đề xuất plan, thảo luận với user, điều chỉnh đến khi **confirm**.

Plan bao gồm:
- **Approach**: hướng giải quyết kỹ thuật
- **Components**: modules/files/services cần tạo hoặc thay đổi
- **Steps**: các bước implementation theo thứ tự
- **Dependencies**: thư viện, services cần tích hợp thêm
- **Risks / Notes**: rủi ro, lưu ý đặc biệt

### Step 5 — Lưu implementation plan
Tạo file: `docs/tasks/TASK-ID/refs/implementation-plan.md`

```markdown
# Implementation Plan: TASK-ID

**Task:** [Title]
**Date:** [YYYY-MM-DD]
**Based on:** [list input docs used]

---

## Approach

[Hướng giải quyết kỹ thuật — ngắn gọn, rõ ràng]

## Components

| Component | Action | Notes |
|-----------|--------|-------|
| [file/module] | create / modify / delete | [ghi chú] |

## Implementation Steps

1. [Bước 1]
2. [Bước 2]
3. [Bước 3]

## Dependencies

- [Library/service cần thêm hoặc tích hợp]

## Risks / Notes

- [Rủi ro hoặc lưu ý đặc biệt]
```

### Step 6 — Cập nhật `refs` trong task.md
Chỉ cập nhật **frontmatter** — điền `refs` với tất cả tài liệu đã thu thập:

```yaml
refs:
  detail_design: "docs/tasks/TASK-ID/refs/DetailDesign.md"   # để trống nếu không có
  implementation_plan: "docs/tasks/TASK-ID/refs/implementation-plan.md"
  figma: "https://figma.com/..."                             # để trống nếu không có
  confluence: "https://..."                                  # để trống nếu không có
  jira_ticket: "PROJ-123"                                    # để trống nếu không có
  other: []
```

> **Không** chỉnh sửa Description, Requirements, Acceptance Criteria trong task.md —
> nội dung đó do agent hoặc user tự điền. `/task-plan` chỉ quản lý `refs`.

---

## Output

| File | Thay đổi |
|------|----------|
| `docs/tasks/TASK-ID/refs/implementation-plan.md` | Tạo mới (hoặc overwrite nếu `--update`) |
| `docs/tasks/TASK-ID/task.md` | Cập nhật frontmatter `refs` |

**Không thay đổi status** của task.

---

## Related Commands

- `/task-create` — Tạo task (chạy trước)
- `/dev-task` — Implement (chạy sau, đọc refs từ task.md)
- `/complete-task` — Full automation (bỏ qua `/task-plan`)

---

**Skill Type**: Planning (Prompt-based, Interactive)
