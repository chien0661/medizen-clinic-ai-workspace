# Hướng dẫn sử dụng MCP Server Atlassian để viết tài liệu Confluence

## 1. Cài đặt và Cấu hình MCP Server

### 1.1 Yêu cầu hệ thống
- Node.js >= 18.x
- npm hoặc yarn
- Git
- Claude Code CLI đã cài đặt

### 1.2 Download MCP Client

Download file `mcp-client.js` từ CDN và lưu vào thư mục project:

**Cách 1: Dùng curl**
```bash
# Download file từ CDN vào thư mục project
curl -o mcp-client.js https://cdn.vissoft.vn/raw-file/mcp-client.js
```

**Cách 2: Download từ trình duyệt**
- Truy cập: https://cdn.vissoft.vn/raw-file/mcp-client.js
- Lưu file `mcp-client.js` vào thư mục gốc của project (cùng cấp với file `.mcp.json`)

### 1.3 Cấu hình Claude Code MCP

Tạo file `.mcp.json` trong thư mục gốc của project (cùng cấp với file `mcp-client.js` đã download).

### 1.4 Nội dung file mcp.json

```json
{
  "mcpServers": {
    "atlassian": {
      "command": "node",
      "args": ["mcp-client.js"],
      "env": {
        "MCP_SERVER_URL": "https://mcp-server.vissoft.vn",
        "JIRA_URL": "https://jira.vissoft.vn",
        "JIRA_TOKEN": "your-jira-token",
        "CONFLUENCE_URL": "https://confluence.vissoft.vn",
        "CONFLUENCE_TOKEN": "your-confluence-token"
      }
    }
  }
}
```

**Lưu ý:**
- File `mcp-client.js` phải nằm cùng thư mục với file `.mcp.json`, hoặc chỉ định đường dẫn đầy đủ
- Thay `your-jira-token` và `your-confluence-token` bằng token thực của bạn

### 1.5 Giải thích cấu hình

| Tham số | Mô tả | Ví dụ |
|---------|-------|-------|
| `command` | Lệnh chạy server | `node` |
| `args` | Đường dẫn đến file mcp-client.js đã download | `mcp-client.js` |
| `MCP_SERVER_URL` | URL MCP Server | `https://mcp-server.vissoft.vn` |
| `JIRA_URL` | URL Jira server | `https://jira.vissoft.vn` |
| `JIRA_TOKEN` | Personal Access Token của Jira | `your-jira-token` |
| `CONFLUENCE_URL` | URL Confluence server | `https://confluence.vissoft.vn` |
| `CONFLUENCE_TOKEN` | Personal Access Token của Confluence | `your-confluence-token` |

### 1.6 Xác nhận cài đặt

Khởi động lại Claude Code và kiểm tra MCP server đã kết nối:

```bash
# Trong Claude Code, gõ lệnh
/mcp
```

Nếu thấy `atlassian` trong danh sách servers là đã cấu hình thành công.

### 1.7 Cấu hình cho từng project (tuỳ chọn)

Tạo file `.mcp.json` trong thư mục gốc project:

```json
{
  "mcpServers": {
    "atlassian": {
      "command": "node",
      "args": ["mcp-client.js"],
      "env": {
        "MCP_SERVER_URL": "https://mcp-server.vissoft.vn",
        "JIRA_URL": "https://jira.vissoft.vn",
        "JIRA_TOKEN": "your-jira-token",
        "CONFLUENCE_URL": "https://confluence.vissoft.vn",
        "CONFLUENCE_TOKEN": "your-confluence-token"
      }
    }
  }
}
```

**Lưu ý:**
- Copy file `mcp-client.js` vào thư mục gốc project (cùng cấp với file `.mcp.json`)
- Thay các token bằng Personal Access Token thực của bạn
- Có thể sử dụng biến môi trường để không hardcode credentials

---

## 2. Tổng quan

MCP (Model Context Protocol) Server Atlassian cho phép Claude Code tương tác trực tiếp với Confluence để đọc, tạo, và cập nhật tài liệu.

---

## 3. Chuẩn bị

### 3.1 Personal Access Token (PAT)
- Truy cập Confluence → Profile → Personal Access Tokens
- Tạo token mới với quyền đọc/ghi
- Lưu token để cấu hình trong file `.mcp.json`

### 3.2 Thông tin cần có

| Thông tin | Mô tả | Ví dụ |
|-----------|-------|-------|
| Space Key | Mã space Confluence | `TDOV` |
| Parent Page ID | ID trang cha (lấy từ URL) | `87410476` |
| Template mẫu | Trang có format cần follow | Page ID hoặc URL |

---

## 4. Các MCP Tools có sẵn

Tất cả tools đều sử dụng token đã cấu hình trong `.mcp.json`. Không cần truyền token trong prompt.

### 4.1 Tools đọc dữ liệu

```
mcp__atlassian__confluence_list_spaces      - Liệt kê tất cả spaces
mcp__atlassian__confluence_get_page         - Đọc nội dung 1 trang
mcp__atlassian__confluence_get_page_by_title - Tìm trang theo title
mcp__atlassian__confluence_search_pages     - Tìm kiếm trang (CQL)
mcp__atlassian__confluence_get_space        - Thông tin space
```

### 4.2 Tools ghi dữ liệu

```
mcp__atlassian__confluence_create_page      - Tạo trang mới
mcp__atlassian__confluence_update_page      - Cập nhật trang
mcp__atlassian__confluence_delete_page      - Xóa trang
```

---

## 5. Mẫu Prompt hiệu quả

### 5.1 Tạo tài liệu thiết kế API mới

```
Từ tài liệu technical spec [tên file hoặc đường dẫn], hãy viết tài liệu
thiết kế chi tiết cho API [tên API] lên Confluence.

- Parent page: [URL hoặc Page ID của trang cha]
- Template tham khảo: [URL trang mẫu có format cần follow]
```

**Ví dụ thực tế:**

```
Từ tài liệu miniapp-dashboard-technical-spec-final-v3.md trong app-center-be,
hãy viết tài liệu thiết kế chi tiết cho API /dashboard/breakdown/distribution
lên Confluence.

- Parent page: http://10.254.136.35:8090/pages/viewpage.action?pageId=87410476
- Template: BM06_Tài liệu thiết kế chi tiết-CORE-Global
```

### 5.2 Cập nhật tài liệu có sẵn

```
Cập nhật trang Confluence [URL hoặc Page ID] với nội dung sau:
[Mô tả thay đổi]
```

### 5.3 Tìm và đọc tài liệu

```
Tìm tất cả trang trong space [SPACE_KEY] có chứa từ khóa "[keyword]"
```

```
Đọc nội dung trang Confluence: [URL hoặc Page ID]
```

---

## 6. Format nội dung Confluence

### 6.1 HTML cơ bản

```html
<h2>Tiêu đề</h2>
<p>Đoạn văn</p>
<ul>
  <li>Item 1</li>
  <li>Item 2</li>
</ul>
<table>
  <tr><th>Header</th></tr>
  <tr><td>Data</td></tr>
</table>
```

### 6.2 Macro đặc biệt

**Table of Contents:**

```html
<ac:structured-macro ac:name="toc" ac:schema-version="1" />
```

**Code block:**

```html
<ac:structured-macro ac:name="code" ac:schema-version="1">
  <ac:parameter ac:name="language">sql</ac:parameter>
  <ac:plain-text-body><![CDATA[SELECT * FROM table]]></ac:plain-text-body>
</ac:structured-macro>
```

**PlantUML diagram:**

```html
<ac:structured-macro ac:name="plantuml" ac:schema-version="1">
  <ac:parameter ac:name="atlassian-macro-output-type">INLINE</ac:parameter>
  <ac:plain-text-body><![CDATA[@startuml
... diagram code ...
@enduml]]></ac:plain-text-body>
</ac:structured-macro>
```

---

## 7. Quy trình làm việc đề xuất

```
┌─────────────────────────────────────────────────────────────┐
│  1. Xác định yêu cầu                                        │
│     - API/feature cần document                              │
│     - Source: technical spec, code, requirements            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  2. Tìm template mẫu                                        │
│     Prompt: "Đọc trang [URL] để xem format template"        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  3. Đọc source documentation                                │
│     - Claude tự đọc file technical spec                     │
│     - Hoặc bạn paste nội dung vào prompt                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  4. Tạo trang Confluence                                    │
│     - Claude tạo page với format chuẩn                      │
│     - Token đã được cấu hình sẵn trong .mcp.json            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│  5. Review và chỉnh sửa                                     │
│     - Kiểm tra trang đã tạo                                 │
│     - Prompt chỉnh sửa nếu cần                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 8. Tips & Best Practices

### 8.1 Prompt hiệu quả

| DO | DON'T |
|----|-------|
| Chỉ rõ parent page ID/URL | Để Claude tự đoán vị trí |
| Cung cấp template mẫu | Mô tả format bằng lời |
| Đưa link technical spec | Copy-paste toàn bộ spec dài |
| Chia nhỏ nhiều API thành nhiều prompt | Yêu cầu viết 10 API một lúc |

### 8.2 Bảo mật Token

```
⚠️ QUAN TRỌNG:
- Không commit file .mcp.json chứa credentials vào git
- Thêm .mcp.json vào .gitignore
- Sử dụng biến môi trường thay vì hardcode token
- Định kỳ rotate token để đảm bảo an toàn
```

### 8.3 Xử lý lỗi thường gặp

| Lỗi | Nguyên nhân | Giải pháp |
|-----|-------------|-----------|
| MCP server not found | Chưa cấu hình đúng path | Kiểm tra đường dẫn mcp-client.js trong mcp.json |
| Connection refused | Server Confluence không truy cập được | Kiểm tra VPN, network |
| 401 Unauthorized | Token sai/hết hạn | Tạo token mới |
| 404 Not Found | Page ID không tồn tại | Kiểm tra lại URL/ID |
| 403 Forbidden | Không có quyền ghi | Kiểm tra quyền space |

---

## 9. Ví dụ Prompt thực tế

### Ví dụ 1: Tạo tài liệu API mới

```
Tạo tài liệu thiết kế chi tiết cho API GET /dashboard/overview theo template BM06.

Thông tin API:
- Endpoint: GET /app-center/api/v1/public/dashboard/overview
- Mô tả: Lấy tổng quan dashboard với metrics tổng hợp
- Request params: timePeriod, miniappCode, partnerCode
- Response: totalSessions, activeUsers, newUsers, ...

Parent page: 87410476
Space: TDOV
```

### Ví dụ 2: Cập nhật tài liệu

```
Cập nhật trang 175583659 - thêm phần Error Codes mới:
- MAC-100: Invalid timePeriod
- MAC-101: Missing required parameter
```

### Ví dụ 3: Tạo nhiều trang

```
Từ technical spec dashboard, tạo 3 trang tài liệu cho:
1. API /dashboard/overview
2. API /dashboard/overview/trend
3. API /dashboard/breakdown/distribution

Mỗi trang là child của page 87410476, theo template BM06.
```

---

## 10. Quick Reference

```bash
# Lấy Page ID từ URL
URL: http://confluence/pages/viewpage.action?pageId=87410476
                                              └── Page ID

# Lấy Space Key từ URL
URL: http://confluence/display/TDOV/Page+Title
                               └── Space Key

# CQL Search syntax
"space = TDOV AND title ~ 'API'"
"parent = 87410476"
"text ~ 'dashboard'"
```

---

## 11. Troubleshooting

### 11.1 Kiểm tra MCP Server hoạt động

```bash
# Test chạy server trực tiếp (trong thư mục project)
node mcp-client.js

# Nếu không có lỗi, file đã download thành công
```

### 11.2 Debug cấu hình

```bash
# Kiểm tra file .mcp.json hợp lệ
cat .mcp.json | jq .

# Kiểm tra file mcp-client.js tồn tại
ls -la mcp-client.js
```

### 11.3 Log lỗi

Khi gặp lỗi, Claude Code sẽ hiển thị message từ MCP server. Đọc kỹ message để xác định nguyên nhân.

---

## 12. Tài liệu tham khảo

- [MCP Protocol Specification](https://modelcontextprotocol.io/)
- [Confluence REST API Documentation](https://developer.atlassian.com/cloud/confluence/rest/)
- [Confluence Storage Format](https://confluence.atlassian.com/doc/confluence-storage-format-790796544.html)

---

**Cập nhật lần cuối:** 16/01/2026
