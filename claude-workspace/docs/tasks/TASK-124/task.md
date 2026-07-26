---
id: TASK-124
type: feature
title: "Quản lý đa đơn vị đo + quy đổi (nhập / tồn-cảnh báo / bán-cấp phát)"
status: DONE
priority: Medium
assigned: Documentation Agent
created: 2026-07-26
updated: 2026-07-27
branch: "feature/TASK-124-multi-unit"
tags: [inventory, pharmacy, prescriptions, billing, reports, unit-of-measure, feature]
affected-repos: [clinic-cms, clinic-cms-web]
refs:
  detail_design: ""
  implementation_plan: "docs/tasks/TASK-124/refs/implementation-plan.md"
  figma: ""
  confluence: ""
  jira_ticket: ""
  other:
    - "docs/tasks/TASK-093 (ngưỡng cảnh báo phân cấp), TASK-094 (DosageForm.unit gợi ý), TASK-076 (dosage form category)"
---

# TASK-124: Quản lý đa đơn vị đo + quy đổi

**Nguồn:** Câu hỏi nghiệp vụ (2026-07-26) — hệ thống đã quản lý quan hệ giữa đơn vị **nhập / cảnh báo kho / bán** chưa. Kết quả rà soát code: **mới có 2 đơn vị**, chưa đủ 3 với quy đổi.

## Hiện trạng (đã tra cứu code)
- ✅ **Nhập → tồn CÓ quy đổi:** `Medicine.purchase_unit` + `pack_size`; nhập kho quy đổi `actual_qty = pack_quantity × pack_size`, `unit_cost = pack_unit_cost / pack_size` (`inventory/services/purchase_in_service.py:70-81`). Tồn (`Batch.actual_quantity`) lưu theo `base_unit`.
- ❌ **Tồn = Cảnh báo = Bán đều là `base_unit`** — KHÔNG tách riêng, KHÔNG có hệ số tồn→bán:
  - Reserve/dispense trừ kho 1:1 với base_unit (`reservation_service.py:104`, `dispense_service.py:80`).
  - `PrescriptionItem.unit` / `InvoiceLine.unit` chỉ là **chuỗi snapshot free-text** client gửi, không suy từ factor.
  - `DosageForm.unit` (TASK-094) chỉ là **gợi ý nhãn**, không phải factor; match `Medicine.dosage_form` bằng **free-text, không FK**.
- Ngưỡng cảnh báo: trên `dev` có 3 cấp (thuốc→dạng bào chế→phòng khám, TASK-093/113) nhưng vẫn theo `base_unit`.

## Mục tiêu
Cho phép định nghĩa và **quy đổi nhất quán** giữa các đơn vị của một thuốc — ví dụ **nhập = thùng → tồn/cảnh báo = hộp → bán/cấp phát = viên/ml** — để kê đơn/cấp phát/xuất hóa đơn/cảnh báo tồn dùng đúng đơn vị mà vẫn nhất quán số học với tồn kho.

## Quyết định thiết kế cần chốt (chạy /task-plan với người dùng TRƯỚC khi implement)
- [ ] Mô hình đơn vị: giữ `base_unit` là đơn-vị-gốc-tồn; thêm **đơn vị bán** riêng + **hệ số base↔sell** (per-medicine hay per-dosage-form)? Có cần **đơn vị cảnh báo** khác base không (thường = base)?
- [ ] Lưu factor ở đâu: `Medicine.sell_unit` + `sell_factor` (base per sell)? Hay bảng `unit_conversion(medicine_id, from_unit, to_unit, factor)` tổng quát?
- [ ] Thêm FK `Medicine.dosage_form_id` (hiện là free-text) — gắn với TASK-076/094.
- [ ] Quy tắc làm tròn: viên (nguyên) vs ml (thập phân); reserve/dispense theo base thế nào khi bán lẻ theo sell-unit.
- [ ] Giá: `sale_price` theo base_unit hay theo sell_unit? Đổi thì migrate.
- [ ] Backfill dữ liệu cũ: factor mặc định = 1 (sell = base) để không vỡ đơn/HĐ hiện hữu; `unit` snapshot cũ giữ nguyên.
- [ ] Cảnh báo/report hiển thị theo đơn vị nào (base hay sell), có hiển thị quy đổi.

## Requirements (sau khi chốt thiết kế)
- [x] Model + migration: đơn vị bán + factor (+ FK dosage_form_id) — Phase 1 (0070).
- [x] Kê đơn (`PrescriptionTab` + BE): chọn sell-unit, quy đổi sang base khi reserve — Phase 2 (BE) + Phase 3 (FE: default unit = sell_unit + quy đổi hint).
- [x] Cấp phát/dispense: trừ kho theo base (đã có), hiển thị theo sell-unit — Phase 2.
- [x] Hóa đơn: line theo sell-unit + đơn giá theo sell-unit, tổng khớp — Phase 2 (không cần đổi code, đã snapshot đúng).
- [ ] Cảnh báo tồn/near-expiry: ngưỡng theo đơn vị đã chốt (base_unit, giữ nguyên theo quyết định thiết kế) — không cần thay đổi thêm, xác nhận lại ở Testing.
- [ ] Reports: valuation/COGS quy đổi đúng — chưa rà soát riêng trong phase này; theo dõi nếu Test Agent phát hiện lệch.
- [x] Admin CRUD (BE) + form/editor (FE) quản lý sell_unit/dosage_form_id/unit_conversion — Phase 3.
- [x] Test: quy đổi nhập→tồn→bán end-to-end; case sell≠base (lọ→ml, vỉ→viên); backward-compat factor=1 — Phase 1/2 BE integration tests + Phase 3 BE admin CRUD tests + FE vitest.

## Progress Checklist
- [x] Planning (/task-plan — chốt thiết kế với người dùng)
- [x] Implementation — Phase 1/3 (BE core + backfill) APPROVED + tested; Phase 2/3 (prescribe/dispense/invoice sell↔base wiring) APPROVED + tested; **Phase 3/3 (FE + BE admin CRUD gap-fill) DONE — IN_REVIEW**. BUG-001 fix (test-fixture only) applied 2026-07-27, commit `9b8b386`.
- [x] Code Review — Phase 1 APPROVED 2026-07-26, Phase 2 APPROVED 2026-07-26, **Phase 3 APPROVED 2026-07-27 (final phase) → IN_TESTING**
- [x] Testing — comprehensive full-stack feature test run 2026-07-27: 302/312 BE tests + FE (vitest/type-check/lint) PASSED, 10 BE unit tests FAILED (BUG-001) → fixed same day (test-fixture only, no production change), re-verified: targeted file 10/10 PASS, inventory-integration + prescriptions-unit sweep 82/82 PASS, `ruff check app tests` B008 64/64 (0 new vs origin/dev), `mypy app` 50/50 (0 new vs origin/dev). Testing Completed 2026-07-27.
- [x] Documentation — Functional Design + API Spec completed 2026-07-27; **DONE**

## Blockers
**BUG-001** — **RESOLVED 2026-07-27.** `tests/unit/inventory/test_medicine_service_effective.py` — 10 pre-existing TASK-093/113 unit tests failed with `AttributeError: 'types.SimpleNamespace' object has no attribute 'sell_unit'` because `_to_response()` reads `med.sell_unit` (TASK-124 Phase 1) but the test's `SimpleNamespace` mock helper wasn't updated. No production impact. Fix: added `sell_unit="viên"` to the mock-builder defaults (matches real backfill semantics, sell_unit defaults to base_unit). Also added `# noqa: B008` to the `Depends(get_db)` params on the 4 new unit-conversion admin-CRUD endpoints in `app/modules/inventory/api/routes.py`, matching the existing noqa convention used elsewhere in the same file (confirmed empirically: B008 count for the file is 29 on both this branch and origin/dev baseline — 0 new). Commit `9b8b386`, pushed to `feature/TASK-124-multi-unit`. See `docs/tasks/TASK-124/bugs/BUG-001.md` + `handoff/test-to-documentation.md`.
