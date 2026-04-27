# Hướng dẫn Cấu hình MCP Server cho Partner's Confluence

## Tổng quan

Khi làm việc với các đối tác (partners), bạn có thể cần truy cập vào Confluence server của họ để đọc tài liệu kỹ thuật, template, hoặc SRS. Tài liệu này hướng dẫn cách cấu hình MCP server để kết nối với Confluence của partner.

---

## Kiến trúc MCP Multi-Partner

```
┌─────────────────────────────────────────────────────────┐
│  Claude Code                                            │
└─────────────────────────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│  .mcp.json (Multiple MCP Servers)                      │
├─────────────────────────────────────────────────────────┤
│  ✓ atlassian (Vissoft internal)                        │
│    - Jira: https://jira.vissoft.vn                     │
│    - Confluence: https://confluence.vissoft.vn          │
│                                                         │
│  ✓ confluence-vds (Partner VDS)                        │
│    - Confluence: http://10.254.136.35:8090             │
│                                                         │
│  ✓ confluence-partner-abc (Partner ABC - example)      │
│    - Confluence: https://partner-abc.com/confluence    │
└─────────────────────────────────────────────────────────┘
```

---

## Bước 1: Xác định thông tin Partner Confluence

Thu thập các thông tin sau từ partner:

| Thông tin | Ví dụ | Ghi chú |
|-----------|-------|---------|
| **Confluence URL** | `http://10.254.136.35:8090` | URL đầy đủ của Confluence server |
| **Loại server** | `Confluence Server/Data Center` | Cloud hoặc On-premises |
| **API Token** | `NzYxMjM0NTY3ODkwOkFCQ0RFRkdISUpLTE1OT1A=` | **Personal Access Token (PAT)** - Chỉ cần token |
| **Network access** | VPN required? | Kiểm tra xem có cần VPN không |

**Lưu ý:** Chỉ cần API Token, KHÔNG cần username/password

---

## Bước 2: Chọn Approach phù hợp

Có **HAI CÁCH** để kết nối với Partner Confluence:

### 📌 Approach 1: Local MCP Server (✅ RECOMMENDED cho On-premises Partners)

**Khi nào dùng:**
- Partner có Confluence Server/Data Center on-premises
- Partner server chỉ accessible từ local network/VPN
- Cần full control về security và network
- **Ví dụ: VDS Partner**

**Ưu điểm:**
- ✅ MCP server chạy local, không cần remote server
- ✅ Kết nối trực tiếp đến partner Confluence
- ✅ Phù hợp với on-premises infrastructure
- ✅ Full control về authentication

**Nhược điểm:**
- ❌ Cần setup và maintain local MCP server
- ❌ Cần install dependencies (node_modules)

### 📌 Approach 2: Remote MCP Server via mcp-client.js

**Khi nào dùng:**
- Partner có Confluence Cloud
- Partner server accessible từ internet
- Đã có sẵn deployed remote MCP server (như Vissoft MCP Server)
- Muốn setup đơn giản, không maintain local server

**Ưu điểm:**
- ✅ Setup đơn giản, chỉ cần config
- ✅ Không cần install dependencies
- ✅ Dùng chung infrastructure với internal

**Nhược điểm:**
- ❌ Phụ thuộc vào remote server availability
- ❌ Network latency cao hơn
- ❌ Partner server phải accessible từ remote MCP server

---

## Bước 2A: Setup với Approach 1 - Local MCP Server (VDS Example)

### 1. Copy Vissoft MCP Server source

```bash
# Rebuild source ở project gốc
cd D:\01. PROJECTS\Vissoft-Atlassian-MCP-Server
npm install
npm run build

# Copy dist và package.json vào project
cd D:\01. PROJECTS\DEMO MULTIPLE AGENTS\template-ai-team
mkdir -p mcp-servers/mcp-[partner-name]-server
cp -r D:\01. PROJECTS\Vissoft-Atlassian-MCP-Server\dist mcp-servers/mcp-[partner-name]-server/
cp D:\01. PROJECTS\Vissoft-Atlassian-MCP-Server\package.json mcp-servers/mcp-[partner-name]-server/

# Install dependencies
cd mcp-servers/mcp-[partner-name]-server
npm install
```

### 2. Thêm vào .mcp.json

```json
{
  "$schema": "https://github.com/modelcontextprotocol/specification/blob/main/schema/mcp.schema.json",
  "mcpServers": {
    "atlassian": {
      "command": "node",
      "args": ["mcp-client.js"],
      "env": {
        "MCP_SERVER_URL": "https://mcp-server.vissoft.vn",
        "JIRA_URL": "https://jira.vissoft.vn",
        "JIRA_TOKEN": "${JIRA_TOKEN}",
        "CONFLUENCE_URL": "https://confluence.vissoft.vn",
        "CONFLUENCE_TOKEN": "${CONFLUENCE_TOKEN}"
      },
      "disabled": false,
      "alwaysAllow": []
    },
    "atlassian-vds": {
      "command": "node",
      "args": ["mcp-servers/mcp-vds-server/dist/index.js"],
      "env": {
        "JIRA_BASE_URL": "http://localhost:8080",
        "JIRA_PAT": "dummy-token-not-used",
        "CONFLUENCE_BASE_URL": "http://10.254.136.35:8090",
        "CONFLUENCE_PAT": "${VDS_CONFLUENCE_PAT}",
        "TRANSPORT": "stdio"
      },
      "disabled": false,
      "alwaysAllow": []
    }
  }
}
```

**⚠️ LƯU Ý QUAN TRỌNG về Environment Variables:**

Local MCP server sử dụng **TÊN BIẾN KHÁC** so với remote:
- ✅ **CONFLUENCE_BASE_URL** (không phải CONFLUENCE_URL)
- ✅ **CONFLUENCE_PAT** (không phải CONFLUENCE_TOKEN)
- ✅ **JIRA_BASE_URL** và **JIRA_PAT** (phải set dummy nếu không dùng Jira)

**Tại sao cần dummy Jira values?**
- MCP server source code validation yêu cầu cả Jira và Confluence config
- Nếu chỉ dùng Confluence, set dummy values: `http://localhost:8080` và `dummy-token-not-used`

### 3. Set Environment Variable

```powershell
# Windows PowerShell
[System.Environment]::SetEnvironmentVariable('VDS_CONFLUENCE_PAT', 'your-personal-access-token', 'User')

# Linux/macOS
export VDS_CONFLUENCE_PAT="your-personal-access-token"
```

---

## Bước 2B: Setup với Approach 2 - Remote MCP Server

### Template chuẩn cho Remote approach

```json
{
  "mcpServers": {
    "atlassian-[partner-name]": {
      "command": "node",
      "args": ["mcp-client.js"],
      "env": {
        "MCP_SERVER_URL": "https://mcp-server.vissoft.vn",
        "JIRA_URL": "",
        "JIRA_TOKEN": "",
        "CONFLUENCE_URL": "[partner-confluence-url]",
        "CONFLUENCE_TOKEN": "${[PARTNER]_CONFLUENCE_TOKEN}"
      },
      "disabled": false,
      "alwaysAllow": []
    }
  }
}
```

**Lưu ý:**
- ✅ Để JIRA_URL và JIRA_TOKEN trống nếu chỉ dùng Confluence
- ✅ Sử dụng **CONFLUENCE_TOKEN** (không phải CONFLUENCE_PAT)
- ✅ Sử dụng **CONFLUENCE_URL** (không phải CONFLUENCE_BASE_URL)

---

## Bước 3: Thiết lập Environment Variables

**⚠️ TÊN BIẾN KHÁC NHAU tùy theo approach:**

### Approach 1 - Local MCP Server
Variable name: `[PARTNER]_CONFLUENCE_PAT`

### Approach 2 - Remote MCP Server
Variable name: `[PARTNER]_CONFLUENCE_TOKEN`

### Windows PowerShell

```powershell
# Approach 1 - Local MCP Server (VDS Example)
[System.Environment]::SetEnvironmentVariable('VDS_CONFLUENCE_PAT', 'your-personal-access-token', 'User')

# Approach 2 - Remote MCP Server (ABC Example)
[System.Environment]::SetEnvironmentVariable('ABC_CONFLUENCE_TOKEN', 'your-personal-access-token', 'User')
```

### Linux / macOS

```bash
# Approach 1 - Local MCP Server (VDS Example)
export VDS_CONFLUENCE_PAT="your-personal-access-token"

# Approach 2 - Remote MCP Server (ABC Example)
export ABC_CONFLUENCE_TOKEN="your-personal-access-token"

# Reload shell
source ~/.bashrc  # hoặc source ~/.zshrc
```

**⚠️ QUAN TRỌNG:**
- Chỉ cần **Personal Access Token (PAT)**, KHÔNG cần username/password
- Tên biến phải khớp với tên trong `.mcp.json`
- `_PAT` cho local server, `_TOKEN` cho remote server

### Cách lấy API Token từ Partner

Yêu cầu partner tạo **Personal Access Token (PAT)** cho bạn:

**Confluence Server/Data Center:**
1. Login vào Confluence
2. Profile → Settings → Personal Access Tokens
3. Create Token với quyền **Read**
4. Copy token (chỉ hiển thị 1 lần)
5. Gửi token qua kênh bảo mật (không qua email/chat công khai)

**⚠️ BẢO MẬT QUAN TRỌNG:**
- **KHÔNG BAO GIỜ** commit credentials vào Git
- File `.mcp.json` đã có trong `.gitignore`
- Sử dụng biến môi trường thay vì hardcode
- Chỉ lưu credentials trên máy cá nhân

---

## Bước 4: Khởi động lại Claude Code

Sau khi cấu hình:

1. **Đóng Claude Code hiện tại** (gõ `/exit`)
2. **Đóng terminal/PowerShell**
3. **Mở terminal mới**
4. **Khởi động Claude Code trong project:**
   ```bash
   cd D:\01. PROJECTS\DEMO MULTIPLE AGENTS\template-ai-team
   claude
   ```

---

## Bước 5: Kiểm tra MCP Server đã kết nối

Trong Claude Code, gõ:

```
/mcp
```

Kết quả mong đợi:
```
Available MCP servers:
✓ atlassian (Vissoft internal)
✓ confluence-vds (Partner VDS)
✓ mariadb (disabled)
✓ figma (disabled)
```

---

## Bước 6: Test kết nối

### Kiểm tra Confluence Spaces

Prompt cho Claude:
```
List all Confluence spaces from confluence-vds server
```

Hoặc sử dụng tool trực tiếp:
```
Use mcp__confluence-vds__confluence_list_spaces to list all spaces
```

### Đọc một trang cụ thể

Prompt cho Claude:
```
Read page ID 172694270 from confluence-vds server
```

Hoặc:
```
Use mcp__confluence-vds__confluence_get_page with pageId=172694270
```

---

## Bước 7: Sử dụng MCP trong Workflow

### Đọc SRS từ Partner Confluence

```
Read the SRS template from partner VDS Confluence:
- Page ID: 172694270
- URL: http://10.254.136.35:8090/pages/viewpage.action?pageId=172694270

Extract the structure and save to docs/templates/specs/partner-srs-template.md
```

### Đọc Detail Design Template

```
Read the Detail Design template from partner VDS Confluence:
- Page ID: 131710958
- URL: http://10.254.136.35:8090/pages/viewpage.action?pageId=131710958

Extract the structure and save to docs/templates/specs/partner-detail-design-template.md
```

---

## Naming Convention cho MCP Servers

| Server Name | Purpose | Example |
|-------------|---------|---------|
| `atlassian` | Vissoft internal (Jira + Confluence) | Default internal |
| `confluence-[partner-code]` | External partner Confluence | `confluence-vds`, `confluence-abc` |
| `jira-[partner-code]` | External partner Jira (nếu cần) | `jira-vds` |

**Quy tắc đặt tên:**
- Chữ thường, không dấu
- Dùng dấu gạch ngang `-` để phân cách
- Partner code ngắn gọn (2-4 ký tự): VDS, ABC, XYZ
- Rõ ràng về mục đích: `confluence-`, `jira-`

---

## Troubleshooting

### Lỗi: "Unable to connect to server"

**Nguyên nhân:**
- Partner Confluence server không truy cập được từ máy local
- Cần kết nối VPN
- URL sai
- Firewall chặn

**Giải pháp:**
1. Kiểm tra VPN đã kết nối chưa
2. Ping thử địa chỉ server:
   ```bash
   ping 10.254.136.35
   ```
3. Test bằng browser:
   ```
   http://10.254.136.35:8090
   ```
4. Kiểm tra firewall/proxy settings

### Lỗi: "401 Unauthorized"

**Nguyên nhân:**
- Username/password sai
- Token hết hạn
- Tài khoản không có quyền truy cập

**Giải pháp:**
1. Kiểm tra lại API token
2. Verify environment variable:
   ```powershell
   echo $env:VDS_CONFLUENCE_TOKEN
   ```
3. Thử login bằng browser với token đó (nếu có UI test)
4. Yêu cầu partner cấp lại token mới

### Lỗi: "404 Page Not Found"

**Nguyên nhân:**
- Page ID sai
- Không có quyền xem page
- Page đã bị xóa

**Giải pháp:**
1. Kiểm tra URL của page trong browser
2. Lấy Page ID từ URL:
   ```
   http://confluence/pages/viewpage.action?pageId=172694270
                                           └── Page ID
   ```
3. Yêu cầu partner share page

### MCP Server không xuất hiện sau restart

**Giải pháp:**
1. Kiểm tra `.mcp.json` syntax hợp lệ:
   ```bash
   cat .mcp.json | jq .
   ```
2. Kiểm tra `"disabled": false`
3. Restart lại Claude Code
4. Check logs trong terminal

---

## Best Practices

### 1. Tách biệt API tokens cho từng partner

```bash
# ✅ ĐÚNG: Tách biệt rõ ràng
VDS_CONFLUENCE_TOKEN="token_from_vds_partner"
ABC_CONFLUENCE_API_TOKEN="token_from_abc_partner"
XYZ_CONFLUENCE_API_TOKEN="token_from_xyz_partner"

# ❌ SAI: Dùng chung
PARTNER_CONFLUENCE_API_TOKEN="shared_token"  # Không nên!
```

### 2. Document partner access trong PROJECT.md

Thêm vào `PROJECT.md`:

```markdown
## External Partner Access

### Partner: VDS
- **Confluence URL**: http://10.254.136.35:8090
- **MCP Server Name**: `confluence-vds`
- **Environment Variable**: `VDS_CONFLUENCE_TOKEN`
- **VPN Required**: Yes
- **Contact**: partner-admin@vds.com
- **Purpose**: Read SRS and Detail Design templates
```

### 3. Sử dụng READ-ONLY access

Khi yêu cầu credentials từ partner:
- Chỉ yêu cầu quyền **đọc (Read)**
- KHÔNG yêu cầu quyền ghi (Write/Edit)
- Giới hạn access vào các spaces cần thiết

### 4. Định kỳ kiểm tra và rotate credentials

- Review credentials mỗi 3 tháng
- Update khi nhân sự thay đổi
- Revoke access khi không còn cần thiết

---

## Template Checklist

Khi thêm partner Confluence mới:

### Planning Phase
- [ ] Thu thập thông tin từ partner (URL, server type, VPN requirements)
- [ ] Quyết định approach: Local hay Remote?
- [ ] Yêu cầu partner cấp Personal Access Token (PAT) với quyền Read

### Setup Phase - Local Approach
- [ ] Copy và build Vissoft MCP Server vào `mcp-servers/mcp-[partner]-server/`
- [ ] Install dependencies: `npm install`
- [ ] Thêm MCP server vào `.mcp.json` với config local
- [ ] Set environment variable: `[PARTNER]_CONFLUENCE_PAT`
- [ ] Kiểm tra dummy Jira values đã set chưa

### Setup Phase - Remote Approach
- [ ] Download `mcp-client.js` (nếu chưa có)
- [ ] Thêm MCP server vào `.mcp.json` với config remote
- [ ] Set environment variable: `[PARTNER]_CONFLUENCE_TOKEN`
- [ ] Verify partner server accessible từ remote MCP server

### Testing Phase
- [ ] Restart Claude Code
- [ ] Test kết nối với `/mcp` command
- [ ] Test list spaces: `confluence_list_spaces`
- [ ] Test đọc một page mẫu: `confluence_get_page`

### Documentation Phase
- [ ] Document trong `PROJECT.md` (approach, URL, contact, purpose)
- [ ] Update team documentation với setup steps
- [ ] Share cấu hình với team (KHÔNG share credentials)
- [ ] Thêm vào onboarding guide cho member mới

---

## Ví dụ Thêm Partner Mới (Partner ABC)

### 1. Thêm vào .mcp.json

```json
{
  "mcpServers": {
    "confluence-abc": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-confluence"],
      "env": {
        "CONFLUENCE_URL": "https://confluence.partner-abc.com",
        "CONFLUENCE_API_TOKEN": "${ABC_CONFLUENCE_API_TOKEN}"
      },
      "disabled": false,
      "alwaysAllow": []
    }
  }
}
```

### 2. Set environment variable

```powershell
[System.Environment]::SetEnvironmentVariable('ABC_CONFLUENCE_API_TOKEN', 'your-api-token', 'User')
```

### 3. Restart và test

```bash
# Restart Claude Code
/exit

# Sau khi mở lại
/mcp

# Test
List spaces from confluence-abc
```

### 4. Document trong PROJECT.md

```markdown
### Partner: ABC Corporation
- **Confluence URL**: https://confluence.partner-abc.com
- **MCP Server Name**: `confluence-abc`
- **Environment Variable**: `ABC_CONFLUENCE_API_TOKEN`
- **VPN Required**: No
- **Contact**: tech-admin@partner-abc.com
- **Purpose**: Read API specifications
```

---

## So sánh các Approach

| Aspect | Vissoft Internal | Partner - Local Server | Partner - Remote Server |
|--------|-----------------|----------------------|------------------------|
| **MCP Server** | Remote (deployed) | Local (stdio) | Remote (deployed) |
| **Command** | `node mcp-client.js` | `node dist/index.js` | `node mcp-client.js` |
| **Server Location** | https://mcp-server.vissoft.vn | Local process | https://mcp-server.vissoft.vn |
| **Environment Vars** | `CONFLUENCE_TOKEN` | `CONFLUENCE_PAT` | `CONFLUENCE_TOKEN` |
| **Config Keys** | `CONFLUENCE_URL` | `CONFLUENCE_BASE_URL` | `CONFLUENCE_URL` |
| **Dependencies** | None (remote handles it) | Need `npm install` locally | None (remote handles it) |
| **Network** | Internal network | Direct to partner | Partner must be accessible from remote |
| **Tools prefix** | `mcp__atlassian__` | `mcp__atlassian-vds__` | `mcp__atlassian-[partner]__` |
| **Setup Complexity** | Low | Medium (need local server) | Low |
| **Best for** | Vissoft internal | On-premises partners | Cloud partners |
| **Maintenance** | Vissoft DevOps | Local updates | Vissoft DevOps |

---

## FAQ

### Q: Có thể kết nối nhiều partner cùng lúc không?
**A**: Có! Mỗi partner có một MCP server riêng trong `.mcp.json`. Tất cả hoạt động đồng thời.

### Q: Cần username/password không?
**A**: **KHÔNG**! Chỉ cần **Personal Access Token (PAT)**.
- ✅ **PAT**: Bảo mật hơn, có thể revoke dễ dàng, độc lập với password
- ✅ Token đã bao gồm thông tin xác thực đầy đủ
- ✅ Works với cả Confluence Server và Confluence Cloud
- ❌ **KHÔNG cần username/password**

### Q: Nên dùng Local hay Remote approach?
**A**: Tùy vào tình huống:
- ✅ **Local**: Partner có on-premises server, cần VPN, hoặc security requirements
- ✅ **Remote**: Partner có Confluence Cloud, accessible từ internet
- ✅ **Tip**: Thử Remote trước (đơn giản hơn), nếu không được thì dùng Local

### Q: Partner không cấp credentials được, làm sao?
**A**: Các lựa chọn thay thế:
1. Yêu cầu partner export pages ra Word/PDF và gửi
2. Yêu cầu partner cấp read-only guest account
3. Screen share và copy-paste nội dung
4. Yêu cầu partner publish pages ra public space

### Q: Có cần restart Claude Code mỗi khi thêm partner mới?
**A**: Có, phải restart để MCP server mới được load.

### Q: Làm sao biết đang dùng MCP server nào?
**A**: Prefix của tool name:
- `mcp__atlassian__confluence_get_page` → Internal Vissoft
- `mcp__confluence-vds__confluence_get_page` → Partner VDS
- `mcp__confluence-abc__confluence_get_page` → Partner ABC

---

## Tài liệu liên quan

- [MCP_SETUP.md](MCP_SETUP.md) - Setup MCP cơ bản
- [MCP_SETUP_VISSOFT.md](MCP_SETUP_VISSOFT.md) - Setup Vissoft internal MCP
- [PROJECT.md](../PROJECT.md) - Document partner access ở đây
- [Confluence MCP Official](https://github.com/modelcontextprotocol/servers/tree/main/src/confluence) - Official documentation

---

**Cập nhật lần cuối:** 27/01/2026
**Người tạo:** AI Team Template
**Version:** 1.0
