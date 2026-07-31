---
id: TASK-132
type: feature
title: "Danh mục đơn vị (unit) quản lý được + dropdown creatable (gõ mới → tự thêm)"
status: IN_REVIEW
priority: Medium
assigned: Code Review Agent
created: 2026-07-31
updated: 2026-07-31
branch: "feature/TASK-132"
tags: [inventory, units, catalog, medicines, feature]
affected-repos: [clinic-cms, clinic-cms-web]
refs:
  detail_design: ""
  implementation_plan: "docs/tasks/TASK-132/refs/implementation-plan.md"
  figma: ""
  confluence: ""
  jira_ticket: ""
  other: []
---

# TASK-132: Danh mục đơn vị + dropdown creatable

**Nguồn:** Yêu cầu 2026-07-31 (mở rộng TASK-131). Danh sách đơn vị hiện đang **hardcode** trong dropdown "Đơn vị dùng" (viên/vỉ/gói/ống/chai/lọ/tuýp/ml/gam/miếng/cái) → chuyển thành **danh mục quản lý được** + cho **tạo đơn vị mới ngay tại dropdown**.

## Description
- **BE:** tạo bảng danh mục `unit` (đơn vị) — per-clinic, admin quản lý được, **seed 11 mặc định** (viên/vỉ/gói/ống/chai/lọ/tuýp/ml/gam/miếng/cái) với `is_system=true`. API CRUD `/units`. Mirror đúng pattern TASK-125 `service_type` (StrEnum→bảng cấu hình). **Kiểm tra trước** xem đã có khái niệm unit-catalog nào chưa (TASK-050 seed có nhắc "units") — nếu có thì tái dùng/mở rộng, tránh trùng.
- **FE:** dropdown "Đơn vị dùng" (và các ô đơn vị trong form thuốc: đơn vị nhập/bán/cơ bản nếu hợp lý) đổi thành **combobox creatable**: options nạp từ danh mục `/units`; gõ đơn vị chưa có + xác nhận → **POST tạo mới** vào danh mục rồi chọn luôn.
- **FE admin:** trang "Danh mục đơn vị" quản lý (CRUD, khoá `is_system`) — mirror ServiceTypesPage (TASK-125).

## Requirements
- [x] BE: model `unit` (per-clinic: code/name, is_system, is_active, sort_order) + migration **0075** (down_revision head hiện tại 0074; additive + seed per-clinic 11 mặc định). CRUD service + `/units` API. Hook seed cho clinic mới (như service_type).
- [x] FE: component combobox creatable dùng chung; áp cho "Đơn vị dùng" (TASK-131) — và cả base_unit/purchase_unit/sell_unit cùng form; nạp options từ `/units`; tạo mới on-the-fly.
- [x] FE: trang admin "Danh mục đơn vị" (CRUD + khoá is_system).
- [x] Không hồi quy form thuốc + kê đơn (TASK-124/129/131) — `medicine.*_unit` vẫn là chuỗi tự do, không thêm FK.

## Acceptance Criteria
- [x] Danh mục đơn vị: 11 mặc định seed sẵn (khoá is_system), admin thêm/sửa/ẩn đơn vị mới được.
- [x] Dropdown "Đơn vị dùng": chọn từ danh mục HOẶC gõ đơn vị mới → tự thêm vào danh mục + chọn.
- [x] Unit test BE (10 passed, mock-based) + FE test (vitest, all passed) written and run. Integration test (real DB) written but **unverified** — no DB stack available in this environment (see handoff). Migration additive, single head confirmed = 0075.

## Progress Checklist
- [x] Planning | [x] Implementation | [ ] Code Review | [ ] Testing | [ ] Documentation

## Notes / Dependencies
- Mirror TASK-125 (service_type configurable catalog + is_system lock + per-clinic seed). Xây trên TASK-131 (usage_unit dropdown).
- Migration mới = **0075** (head dev hiện tại 0074, xác nhận `alembic heads` → single head 0075).
- **Chốt:** danh mục per-clinic (như service_type) — mỗi phòng khám tự thêm đơn vị của mình.
- Đã kiểm tra: không có bảng danh mục unit nào tồn tại trước đây — `unit_service.py`/`UnitConversion` (TASK-124) là resolver quy đổi hệ số cho 1 medicine, không phải danh mục mã đơn vị. Đã tạo mới, không trùng lặp.
- Quyền dùng lại: `inventory.read` / `inventory.manage_catalog` (không thêm quyền mới).
- Implementation hoàn tất trên `feature/TASK-132` (BE + FE worktrees), đã push, CHƯA merge vào `dev` — chờ Code Review Agent. Xem `handoff/implementation-to-review.md`.

## Blockers
Không.
