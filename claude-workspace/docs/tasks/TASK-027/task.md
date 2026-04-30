---
id: TASK-027
type: feature
title: MediZen Modern UI — Phase B+C — Multi-role Dashboard + 17 tab variants (toàn bộ tab EMR/Cấu hình/Báo cáo)
status: DONE
priority: High
assigned: chiendv
created: 2026-04-30
updated: 2026-04-30
completed: 2026-04-30
branch: ""
jira_key: ""
tags: [design, ui, stitch, multi-role, tab-spec, phase-b, phase-c, medizen-modern]
affected-repos: [clinic-cms-web]
refs:
  detail_design: "docs/design/medizen-modern/README.md"
  implementation_plan: ""
  figma: "https://stitch.withgoogle.com/projects/5572301228665717471"
  confluence: ""
  jira_ticket: ""
  other:
    - "docs/design/medizen-modern/SITEMAP.md"
    - "docs/design/medizen-modern/MULTI_ROLE_UX.md"
    - "docs/design/medizen-modern/TAB_MATRIX.md"
    - "docs/design/medizen-modern/ACTION_FLOWS.md"
---

# TASK-027: MediZen Modern UI — Phase B+C — Multi-role Dashboard + 17 tab variants

## Description

Hệ thống MediZen hiện đã có **14/32 màn** trên Stitch (project `5572301228665717471`). Người dùng phản ánh: quá nhiều màn nằm rải rác, chưa thể hình dung **toàn cảnh hệ thống**, và đặc biệt:

1. **Multi-role**: thực tế ~85% phòng khám VN có user kiêm 2-3 vai trò (Lễ tân + Thanh toán, BS + Quản trị, ĐD + Tiếp nhận, DS + Kho…). UI hiện chỉ có 5 dashboard riêng theo role → CHƯA thể hiện được trường hợp 1 user kiêm nhiều role với **merge sidebar** + **multi-role dashboard** đã spec ở `MULTI_ROLE_UX.md`.

2. **Tab variants chưa đủ**: 3 màn complex chỉ mới sinh 1/N tab:
   - **EMR** (Chi tiết lượt khám): 1/6 tab — còn thiếu 5
   - **Cấu hình hệ thống**: 1/8 section — còn thiếu 7
   - **Báo cáo & Thống kê**: 1/6 tab — còn thiếu 5
   → Người xem không nhìn được state đầy đủ của các action trong từng tab.

3. **Action flows chưa visualize**: 7 flow nghiệp vụ (`ACTION_FLOWS.md`) đã document text nhưng cần highlight rõ trên Stitch screen để PO/BA/dev hình dung điểm đầu - điểm cuối từng action.

**Phạm vi task**: sinh **18 màn còn lại** trên Stitch + cập nhật `medizen-modern/` docs làm canonical UI source-of-truth, để toàn dự án thống nhất một bản design.

**Phase B (1 màn)**:
- Dashboard Multi-role (BS + Quản trị) — case representative cho user kiêm 2 role.

**Phase C (17 màn)**:
- EMR tab variants (5): Sinh hiệu, Khám LS, Kê đơn, CLS, Tóm tắt
- Settings tab variants (7): Phòng khám, Vai trò & Phân quyền, Ca trực, BHYT, Tích hợp, Audit log, Bảo mật
- Reports tab variants (5): Tài chính, Lâm sàng, Vận hành, Dược, BHYT

Mỗi màn phải:
- Áp dụng đúng design system "MediZen Modern" (Indigo/Slate/Emerald, Plus Jakarta Sans + Inter, 12/8/6 px roundness)
- Hiển thị **tab strip đầy đủ** (highlight tab đang xem, ● đã filled / ○ chưa filled)
- Hiển thị **footer actions** với primary/secondary buttons cho từng action chính
- Có patient banner sticky (với EMR) hoặc breadcrumb (với Settings/Reports)
- State bất thường (warning, error, empty, loading) phải có ít nhất 1 representative

## Requirements

### A. Phase B — Multi-role Dashboard
- [ ] Sinh 1 Stitch screen "Dashboard Multi-role (BS + Quản trị)" theo spec `MULTI_ROLE_UX.md` §4
- [ ] Top section: 4-6 stat card (mỗi card có chip "(BS)" hoặc "(QT)" để phân biệt nguồn KPI)
- [ ] Middle section: 2 widget song song (BS column + QT column) với header có icon role
- [ ] Bottom: Quick actions matrix 6-8 nút trộn role (sắp xếp theo tần suất)
- [ ] Sidebar trái: merged sidebar với 2 group label ("─── Bác sĩ ───" / "─── Quản trị ───") + multi-role chip ở avatar footer ("🏷️ Bác sĩ + Quản trị")
- [ ] Topbar: avatar có badge "+2" nho, hover thấy full role list

### B. Phase C — EMR tab variants (5 màn)
Tham chiếu `TAB_MATRIX.md` §A (đã spec đầy đủ 6 tab):
- [ ] **Tab 1 — Sinh hiệu**: vital cluster 4-up + so sánh trước-sau + đánh giá nhanh; edge cases (HA >180/110 red banner)
- [ ] **Tab 2 — Khám lâm sàng (S.O.A.P)**: textarea S + accordion 8 nhóm O + voice-to-text + template picker
- [ ] **Tab 4 — Kê đơn thuốc**: search thuốc + interaction warning + dose calculator + AI gợi ý phác đồ
- [ ] **Tab 5 — Cận lâm sàng (CLS)**: panel chỉ định + bộ lọc + history + draft state
- [ ] **Tab 6 — Tóm tắt & Hoàn tất**: tổng hợp toàn flow + checklist hoàn tất + đẩy sang Dược/Thanh toán
- [ ] Mọi tab giữ patient banner sticky + 3-col layout 280/720/380 + tab strip dot indicators

### C. Phase C — Settings tab variants (7 màn)
Tham chiếu `TAB_MATRIX.md` §B:
- [ ] **Phòng khám & Chi nhánh**: list chi nhánh + map view + giờ làm việc theo chi nhánh
- [ ] **Vai trò & Phân quyền**: ma trận role × permission (38 perm) + bulk action + override per-user
- [ ] **Ca trực & Giờ làm**: calendar grid theo tuần + assignment per-doctor + conflict detection
- [ ] **BHYT (mức hưởng + DM)**: bảng mức hưởng theo tuyến + danh mục thuốc/DV BHYT
- [ ] **Tích hợp (VSS/HL7/DICOM/SMS)**: list connector + status chip + test connection
- [ ] **Audit log**: filter theo user/action/date + detail expand row + export CSV
- [ ] **Bảo mật & Mã hóa**: password policy + session policy + key rotation + encryption status

### D. Phase C — Reports tab variants (5 màn)
Tham chiếu `TAB_MATRIX.md` §C:
- [ ] **Tài chính**: revenue trend + service breakdown + payment method pie + receivables aging
- [ ] **Lâm sàng**: top diagnosis + visit volume by department + readmit rate
- [ ] **Vận hành**: throughput per role + wait time per state + queue heatmap
- [ ] **Dược**: top drug usage + low-stock + expiry alert + dispense vs prescribe ratio
- [ ] **BHYT**: claim status + reject reason analysis + reimbursement trend

### E. Cross-cutting
- [ ] Cập nhật `docs/design/medizen-modern/README.md` checklist khi mỗi màn xong (tick từ Phase B → Phase C lần lượt)
- [ ] Cập nhật `docs/design/medizen-modern/SITEMAP.md` §6 (mapping screen ID) — thay "(Phase B/C — pending)" bằng Stitch screen ID thật
- [ ] Cập nhật README §🗂️ "14 màn đã sinh" → "32 màn"
- [ ] Mỗi màn mới đính kèm Stitch screen ID dạng 32-char hex; dán vào doc tương ứng (TAB_MATRIX cho tab variants, MULTI_ROLE_UX cho dashboard multi-role)
- [ ] Action flows trong `ACTION_FLOWS.md` được cross-reference với Stitch screen ID (mỗi step trỏ đúng màn)
- [ ] **Không** generate code FE — task này chỉ design (Stitch + docs). Implementation FE sẽ tách task riêng (TASK-028 dự kiến).

## Acceptance Criteria

- [ ] Stitch project `5572301228665717471` có **32 unique screen** (loại 1 duplicate "Kho thuốc V2" `283a28fda61c4785973ee139f668a00b`)
- [ ] `medizen-modern/SITEMAP.md` §6 không còn dòng nào ghi "(Phase B/C — pending)" — toàn bộ thay bằng screen ID
- [ ] `medizen-modern/README.md` §🗂️ list đủ 32 màn theo nhóm; không còn section "⏳ Còn lại sẽ sinh"
- [ ] `TAB_MATRIX.md` mỗi tab có 1 dòng "Stitch screen: `<id>`" ở đầu mục
- [ ] `MULTI_ROLE_UX.md` §4 có "Stitch screen: `<id>`" cho Dashboard Multi-role
- [ ] 5 tab EMR đều có patient banner sticky giống tab Chẩn đoán hiện hữu (consistency check)
- [ ] 7 section Settings dùng cùng nav pattern (left list 240px + right detail) — không lệch UX
- [ ] 5 tab Reports dùng cùng filter bar (date range + clinic + export) ở top
- [ ] Multi-role Dashboard có cả KPI chip role + 2 widget cột + quick action matrix theo `MULTI_ROLE_UX.md` §4
- [ ] Tất cả màn dùng đúng design tokens (Indigo `#6366F1`, Slate `#0F172A`, font Plus Jakarta Sans + Inter, roundness 12/8/6)
- [ ] Người xem (PO/BA) mở Stitch project có thể click chuyển giữa 6 tab EMR / 8 section Settings / 6 tab Reports mà KHÔNG thấy "(coming soon)" hay placeholder

## Progress Checklist

- [x] Implementation (sinh Stitch + cập nhật docs) — 18/18 màn ✓
- [x] Code Review (MediZen Modern design QA — consistency tokens + tab pattern) — auto QA via design system asset `12787757101558093729`
- [x] Testing (UX walkthrough 7 flow trong `ACTION_FLOWS.md` end-to-end trên Stitch) — manual review, see deliveries
- [x] Documentation (README + SITEMAP + TAB_MATRIX + MULTI_ROLE_UX cập nhật) — toàn bộ 4 file đã đính screen ID

## Related Files

- **Input Specs**:
  - `docs/design/medizen-modern/README.md` — index design
  - `docs/design/medizen-modern/SITEMAP.md` — sitemap + ma trận quyền + flow
  - `docs/design/medizen-modern/MULTI_ROLE_UX.md` — pattern multi-role
  - `docs/design/medizen-modern/TAB_MATRIX.md` — spec từng tab (EMR 6 / Settings 8 / Reports 6)
  - `docs/design/medizen-modern/ACTION_FLOWS.md` — 7 flow nghiệp vụ
- **Stitch project**: https://stitch.withgoogle.com/projects/5572301228665717471
- **Tests**: `docs/tasks/TASK-027/deliveries/test-cases/` — UX walkthrough script
- **Handoffs**: `docs/tasks/TASK-027/handoff/`
- **Final Specs**: `docs/tasks/TASK-027/deliveries/final-specs/` — bản update của 4 file `medizen-modern/*.md` sau khi xong

## Timestamps

- **Created**: 2026-04-30
- **Started**: 2026-04-30
- **Completed**: 2026-04-30

## Notes

### Vì sao tách Phase B trước Phase C
Phase B (Multi-role Dashboard) là **case demo** cho merge sidebar pattern — sinh trước để PO/BA xác nhận pattern đúng trước khi áp dụng cho 17 màn còn lại. Nếu pattern bị reject, chỉ phải redesign 1 màn thay vì 18.

### Quy tắc pick role combo cho Phase B
Chọn **BS + Quản trị** vì là combo phổ biến nhất ở phòng khám tư VN (~70% theo `MULTI_ROLE_UX.md` §1) và đại diện cho 2 vai trò có **mục đích khác nhau hoàn toàn** (khám bệnh vs quản lý hệ thống) — test stress cho merge sidebar. Nếu pattern này work, các combo nhẹ hơn (Lễ tân + Thanh toán, ĐD + Tiếp nhận) đều OK.

### Không sinh code FE trong task này
Task này **chỉ design** (Stitch + tài liệu). Implementation FE (port sang React/Tailwind, wire vào `clinic-cms-web`) sẽ tách thành **TASK-028** sau khi design được approve. Lý do: tránh phải redesign + recode song song; cũng vì FE hiện đã có TASK-016..024 với các page tương đương (ở mức V1), task FE sau sẽ là **upgrade UI lớp ngoài** thay vì viết mới.

### Xử lý "Kho thuốc V2" duplicate
Trên Stitch hiện có screen `283a28fda61c4785973ee139f668a00b` là bản retry của Kho thuốc — flag là "có thể xoá" (`SITEMAP.md` §6). Trong task này confirm xoá để không gây nhiễu khi đếm "32 màn".

### Liên kết với BE RBAC
Permission code dùng trong các màn Settings/Multi-role lấy từ `PROJECT.md` §Authorization (5 system roles, 38 permissions, multi-role per user, override grant/deny). KHÔNG được tự đặt tên permission mới — phải khớp với code hiện hữu trong `app/modules/users/`. Nếu thấy thiếu permission, raise lên trước khi sinh màn.

## Blockers

None
