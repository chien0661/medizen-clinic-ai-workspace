---
id: TASK-029
type: feature
title: MediZen UI Phase D — Edit Stitch hiện hữu + sinh ~16 màn mới theo function list v1.3 + SECURITY.md
status: IN_REVIEW
priority: High
assigned: chiendv
created: 2026-05-01
updated: 2026-05-01
completed_partial: 2026-05-01
branch: ""
jira_key: ""
tags: [design, ui, stitch, phase-d, multi-clinic, search, security, medizen-modern]
affected-repos: [clinic-cms-web]
refs:
  detail_design: "docs/design/medizen-modern/MENU_AND_SCREENS.md"
  implementation_plan: ""
  figma: "https://stitch.withgoogle.com/projects/5572301228665717471"
  confluence: ""
  jira_ticket: ""
  other:
    - "docs/design/medizen-modern/README.md"
    - "docs/design/medizen-modern/SITEMAP.md"
    - "docs/design/medizen-modern/MULTI_ROLE_UX.md"
    - "docs/design/medizen-modern/TAB_MATRIX.md"
    - "docs/design/medizen-modern/SECURITY.md"
    - "../../../docs/clinic_management_function_list.md"
    - "../../tasks/TASK-027/task.md"
---

# TASK-029: MediZen UI Phase D — Edit Stitch hiện hữu + sinh ~16 màn mới

## Description

Sau TASK-027 sinh 18 màn (Phase B + C — multi-role + tab variants), function list đã được expand lên v1.3 với nhiều chức năng mới:
- **AUTH-001 update** (bỏ `clinic_code`) + **AUTH-018..022** (multi-clinic per account, default, switcher, JWT reset)
- **RX-016** (hiển thị stock thuốc real-time khi kê đơn)
- **RBAC-015..018** (applied role audit, SoD, merge sidebar, multi-role chip)
- **NAV-001..008** (Cmd+K palette, clinic switcher, quick search BN/thuốc/feature, breadcrumb)
- **CFG-017** (toggle BHYT bật/tắt — default OFF)
- **NFR-023..046** (security PII/PHI deep)
- **MENU_AND_SCREENS.md §G** liệt kê **Phase D backlog ~16 màn** chưa có Stitch

Hiện 32 unique màn trên Stitch project `5572301228665717471` đã lệch với function list mới. TASK này:

**A. EDIT 8 màn hiện hữu** để reflect function mới:
1. Login `e98de272` — bỏ trường `clinic_code`, hiện chỉ email + password (AUTH-001)
2. EMR Tab 4 Kê đơn `7e32e3c8` — thêm stock chip mỗi card thuốc + warning vượt tồn kho (RX-016)
3. Cấu hình Phòng khám `5f5f1093` — thêm Section "Tính năng" với toggle BHYT (CFG-017)
4. Bảng giá DV `7c43ae65` — ẩn cột BHYT % khi `bhyt_enabled=false` (CFG-017 ripple)
5. Tích hợp `1d6fc539` — disable tab VSS với banner "Bật BHYT trước" khi off
6. Báo cáo Tổng quan `d86ddd11` — tab strip 5 vs 6 tab tuỳ flag BHYT
7. Topbar mọi dashboard (5 role + multi-role) — thêm ⌘K search + clinic switcher dropdown
8. Cấu hình Bảo mật `b15b5015` — expand thêm card "PII inventory" + "Anomaly detection rules" theo SECURITY.md

**B. GENERATE 16 màn mới** từ MENU_AND_SCREENS.md §G:

| # | Nhóm | Màn | Priority |
|---|---|---|---|
| 1 | Auth | Chọn phòng khám (multi-clinic chooser sau login) | High |
| 2 | Auth | Quên mật khẩu | Medium |
| 3 | BN | Danh sách bệnh nhân (master list) | High |
| 4 | BN | Hồ sơ BN chi tiết (8 tab) | High |
| 5 | Queue | Phòng chờ kanban board (5 cột state machine) | High |
| 6 | Pharmacy | Danh mục thuốc | Medium |
| 7 | Pharmacy | Nhập kho (PO) | Medium |
| 8 | Pharmacy | Kiểm kê (stock count wizard) | Medium |
| 9 | Pharmacy | Xử lý hết hạn | Medium |
| 10 | Billing | Lịch sử hoá đơn | Medium |
| 11 | Billing | Công nợ BN (AR aging) | Medium |
| 12 | Profile | Profile cá nhân (5 tab — info/MK/PK của tôi/phiên/thông báo) | High |
| 13 | Notifications | Notifications full page | Medium |
| 14 | Modal | Cmd+K Quick search palette | High |
| 15 | Popover | Clinic switcher dropdown | High |
| 16 | Reception | (Optional) Tiếp nhận BN cập nhật — ẩn ô BHYT khi off | Low |

→ Sau TASK-029: **~48 unique canonical screens** (32 hiện tại + 16 mới).

## Requirements

### A. Edit 8 màn hiện hữu

- [ ] Login `e98de272`: Bỏ trường `clinic_code`, để 2 field email + password. Cập nhật helper text "Đăng nhập bằng email — không cần mã phòng khám"
- [ ] EMR Tab 4 Kê đơn `7e32e3c8`: Mỗi card thuốc thêm chip stock real-time (emerald `Còn 320v ✓` / amber `⚠ Sắp hết` / red `✕ Hết hàng`). Thêm filter chip "Chỉ hiện thuốc còn hàng" default ON
- [ ] Cấu hình Phòng khám `5f5f1093`: Tab Thông tin thêm Section "Tính năng" với 3 toggle: BHYT (default OFF), Cấp cứu (default ON), Telehealth (default OFF v2)
- [ ] Bảng giá DV `7c43ae65`: Conditional hide cột "BHYT %" + "BN trả (sau BHYT)" khi `bhyt_enabled=false`
- [ ] Tích hợp `1d6fc539`: Tab VSS hiện banner "⚠ Cần bật BHYT ở Cấu hình → Phòng khám trước khi config VSS" khi off
- [ ] Báo cáo `d86ddd11`: Tab strip render conditional 5 vs 6 tab dựa trên flag BHYT
- [ ] **TẤT CẢ topbar 5 dashboard role + multi-role**: thêm ⌘K search box + clinic switcher dropdown bên cạnh avatar (NAV-001, NAV-002)
- [ ] Cấu hình Bảo mật `b15b5015`: Thêm 3 card mới: "PII inventory" (link tới SECURITY.md §1), "Anomaly detection rules 7 quy tắc" (NFR-042), "Hash chain verify status" (NFR-044)

### B. Sinh 16 màn mới (Phase D)

#### B.1 Auth (2 màn)
- [ ] Chọn phòng khám: Card grid sau login multi-clinic — mỗi card 1 PK với role chip + "Vào phòng khám →" + checkbox "Đặt làm mặc định"
- [ ] Quên mật khẩu: Form input email + button "Gửi link reset" + back to login

#### B.2 Bệnh nhân (2 màn)
- [ ] Danh sách BN: Table dày + filter bar sticky (tên/SĐT/mã/CCCD/tag/BHYT) + pagination + actions per row
- [ ] Hồ sơ BN chi tiết: 3-col layout (summary 280 + tab content 720 + right context 380), 8 tabs (Tổng quan/Lịch sử khám/Đơn thuốc/CLS/Hoá đơn/Tài liệu/Note/Audit)

#### B.3 Queue board (1 màn)
- [ ] Phòng chờ kanban: 5 cột state machine (Chờ tiếp nhận / Chờ sinh hiệu / Chờ BS / Đang khám / Chờ thanh toán) + card BN với wait timer + chip cấp cứu

#### B.4 Pharmacy (4 màn)
- [ ] Danh mục thuốc: Table + filter + CRUD inline + drawer detail
- [ ] Nhập kho (PO): Form supplier + line items thuốc + lô + HSD + qty + giá vốn
- [ ] Kiểm kê: Wizard 3 bước (chọn category → đếm thực tế → adjustment cần admin approve)
- [ ] Xử lý hết hạn: Table thuốc 30/60/90 ngày HSD + actions (disposal/giảm giá/trả NCC)

#### B.5 Billing (2 màn)
- [ ] Lịch sử hoá đơn: Table + filter date/status/method + pagination
- [ ] Công nợ BN (AR aging): Table BN có công nợ + aging buckets (0-30/30-60/60-90/>90 ngày)

#### B.6 Profile (1 màn)
- [ ] Profile cá nhân: 2-col layout, 5 tabs:
  - Thông tin (avatar + tên + SĐT + email + CCCD)
  - Mật khẩu (form 3 trường + complexity hint)
  - **Phòng khám của tôi** — list PK user có quyền + role mỗi PK + radio "Mặc định" + button "Rời PK"
  - Phiên (list active sessions với device/IP/last seen + button đăng xuất per session)
  - Thông báo (toggle email/SMS/in-app per loại)

#### B.7 Notifications (1 màn)
- [ ] Notifications full page: Table dày + filter (date/type/source) + bulk actions

#### B.8 Modals & popovers (2 màn — represent dạng full screen mock)
- [ ] **Cmd+K Quick search palette**: Modal full overlay với input + tab strip (Tất cả/BN/Thuốc/Tính năng) + result list group theo entity + footer keyboard hint
- [ ] **Clinic switcher dropdown**: Popover 280px với search box + list PK user có quyền + chỉ báo current + footer cấu hình/đăng xuất

#### B.9 Optional (1 màn)
- [ ] Tiếp nhận BN updated (`8c84c7e3` re-gen): Hide ô "Số thẻ BHYT" + button "Tra cứu VSS" khi `bhyt_enabled=false`

### C. Cross-cutting

- [ ] Cập nhật `cura-modern/README.md` (đổi tên thành medizen-modern) — bảng "32 màn" → "48 màn"
- [ ] Cập nhật `medizen-modern/SITEMAP.md` §6 — thêm 16 màn mới + screen ID thật
- [ ] Cập nhật `medizen-modern/MENU_AND_SCREENS.md` — đính screen ID cho 16 màn mới (đang là TODO)
- [ ] Cập nhật `medizen-modern/TAB_MATRIX.md` — không thêm tab nhưng update screen ID nếu re-gen
- [ ] Apply Cura Modern design system v2 (`assets/12787757101558093729`) cho mọi màn
- [ ] **KHÔNG** generate code FE — task này chỉ design (Stitch + docs). Implementation FE sẽ tách task riêng (TASK-030 dự kiến).

## Acceptance Criteria

- [ ] 8 màn hiện hữu được EDIT (qua `mcp__stitch__edit_screens`) — không tạo bản duplicate
- [ ] 16 màn mới sinh thành công (verified qua `mcp__stitch__list_screens`)
- [ ] Stitch project có **48 unique canonical** screens (sau khi xoá thủ công 4 duplicate cũ từ TASK-027)
- [ ] `medizen-modern/SITEMAP.md` §6 — toàn bộ 48 màn có screen ID thật, không còn dòng "(Phase D — pending)"
- [ ] `medizen-modern/MENU_AND_SCREENS.md` §G — toàn bộ 16 mục Phase D có screen ID thật
- [ ] `medizen-modern/README.md` — bảng "32 màn (đã đủ)" → "48 màn"
- [ ] Login screen mới KHÔNG hiển thị trường "Mã phòng khám"
- [ ] EMR Tab 4 Kê đơn có chip stock cho mọi card thuốc (test 5 thuốc, ít nhất 3 trạng thái stock)
- [ ] Cấu hình Phòng khám có Section "Tính năng" với toggle BHYT
- [ ] Bảng giá DV: 2 phiên bản — bhyt_enabled=true (full cột) và =false (ẩn cột BHYT) — chọn 1 generate, document phiên bản kia trong note
- [ ] Mọi topbar có ⌘K search + clinic switcher visible
- [ ] Profile có tab "Phòng khám của tôi" với multi-clinic management
- [ ] Cmd+K palette modal có sub-mode `/bn /thuoc /inv /rx /lk` (text input prefix)
- [ ] Clinic switcher popover có 3+ clinic mock với role chip
- [ ] Tất cả màn tuân thủ design tokens MediZen Modern (Indigo `#6366F1`, Slate, Emerald, Amber, Red, Plus Jakarta Sans + Inter, 12px radius)
- [ ] Người xem (PO/BA) mở Stitch project có thể click qua tất cả 48 màn KHÔNG thấy placeholder

## Progress Checklist

- [x] **APPROACH PIVOT**: Tạo NEW Stitch project `2542650746708884228` thay vì cleanup old project (per user decision)
- [x] Implementation — Sinh 32/47 màn mới trong fresh project ✓ (~68% done, 6 batches fired)
- [ ] Implementation — 15 màn còn lại (TASK-030 backlog): Quên MK, Danh sách BN, Hồ sơ BN 8 tabs, Queue board, Reports BHYT, Pharmacy 4, Billing 2, Profile multi-tab, Cmd+K palette, Clinic switcher, Notifications
- [x] Documentation: `MEDIZEN_FRESH_PROJECT.md` mapping 32 screen IDs canonical + 15 màn pending
- [x] Documentation: README.md updated với new project URL
- [ ] Documentation: SITEMAP/MENU_AND_SCREENS/TAB_MATRIX cập nhật mapping mới (defer cho TASK-030)
- [ ] Code Review + Testing (defer cho TASK-030 sau khi đủ 47 màn)

## Related Files

- **Input Specs**:
  - `docs/design/medizen-modern/MENU_AND_SCREENS.md` — danh sách màn Phase D + spec từng màn
  - `docs/design/medizen-modern/SITEMAP.md` §6 — bảng mapping screen ID
  - `docs/design/medizen-modern/TAB_MATRIX.md` — spec tab cho EMR/Settings/Reports
  - `docs/design/medizen-modern/MULTI_ROLE_UX.md` — pattern multi-role merge sidebar
  - `docs/design/medizen-modern/SECURITY.md` — spec bảo mật cho UI Bảo mật & Mã hoá
  - `../../../docs/clinic_management_function_list.md` v1.3 — function definitions tham chiếu (~468 functions)
- **Stitch project**: https://stitch.withgoogle.com/projects/5572301228665717471
- **Tests**: `docs/tasks/TASK-029/deliveries/test-cases/` — UX walkthrough script
- **Handoffs**: `docs/tasks/TASK-029/handoff/`
- **Final Specs**: `docs/tasks/TASK-029/deliveries/final-specs/screen-mapping.md` — bản tổng hợp 48 screen IDs

## Timestamps

- **Created**: 2026-05-01

## Notes

### Phân chia EDIT vs GENERATE

**EDIT** (8 màn hiện hữu) tiết kiệm thời gian + giữ screen ID không đổi → các doc đang đính ID không cần update. Nhưng `mcp__stitch__edit_screens` có thể fail nếu prompt không rõ. Nếu fail → fallback re-generate + update doc với ID mới + xoá thủ công bản cũ.

**GENERATE** (16 màn mới) — pattern timeout-then-verify giống TASK-027 (fire batch → wait 4-5 phút → list_screens verify → docs).

### Batch strategy đề xuất

Để tránh quá tải Stitch + dễ verify:
- **Batch 1** (8 EDIT): fire song song 8 `edit_screens` → wait 5p → verify
- **Batch 2** (8 GENERATE high-priority): Auth chooser + Quên MK + BN list + BN detail + Queue + Profile + Cmd+K + Clinic switcher
- **Batch 3** (8 GENERATE medium): Pharmacy 4 + Billing 2 + Notifications + Forgot pass

Tổng wall-clock ước tính: ~30 phút (2-3 batch × ~10 phút verify).

### Risk + mitigation

| Risk | Mitigation |
|---|---|
| `edit_screens` fail mid-batch → state lệch | Verify từng màn sau edit; nếu fail thì re-generate (chấp nhận screen ID mới + update doc) |
| Stitch generate duplicate khi MCP timeout retry | Như TASK-027: fire 1 lần, đợi 5p, kiểm tra; KHÔNG retry call đã fire |
| Inconsistency design tokens | Pre-batch verify design system asset `12787757101558093729` đang active |
| Conditional UI (BHYT toggle) khó render trong 1 screen | Generate phiên bản phổ biến (bhyt_enabled=true cho hầu hết PK đa khoa); document conditional state trong note |
| Multi-clinic switcher cần data 3+ clinic mock | Hardcode 3 PK mock với tên VN + role mix trong prompt |

### Dependency với TASK-028

TASK-028 (Landing Page) tạo Stitch project MỚI riêng cho marketing site — không đụng tới project app `5572301228665717471` của TASK-029. 2 task có thể chạy song song không conflict.

### Sau TASK-029

- **TASK-030 (đề xuất)**: Implement FE Phase D (port 16 màn mới sang React/Tailwind, wire vào `clinic-cms-web`)
- **TASK-031 (đề xuất)**: Implement BE security NFR-024..046 (column-level encryption + bcrypt 12 + hash chain audit + anomaly detection)

## Blockers

None
