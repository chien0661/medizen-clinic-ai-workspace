---
id: TASK-123
type: bug
title: "[High] Rà soát hệ thống: enforcement bất biến billing↔services↔visit↔dispense (H-1/2/3/4 + siblings)"
status: DONE
priority: High
assigned: Documentation Agent
created: 2026-07-26
updated: 2026-07-26
branch: "fix/TASK-123-invariant-enforcement"
tags: [billing, services, visits, pharmacy, data-integrity, financial, systemic, high, e2e-finding]
affected-repos: [clinic-cms]
refs:
  other:
    - "docs/tasks/TASK-095/deliveries/test-reports/full-system-e2e-report.md (H-1/H-2/H-3/H-4 run3)"
    - "docs/tasks/TASK-108 (guard đường service issued), TASK-112 (reopen), TASK-119 (reversal), TASK-120 (rx guards)"
---

# TASK-123: [High] Đợt rà soát hệ thống — enforcement bất biến tài chính/hồ sơ

**Nguồn:** E2E re-run lần 3, H-1/2/3/4 — **đều là anh-em sinh đôi** của các fix trước (TASK-108/112/119/120). Gốc rễ: guard bất biến chỉ gắn ở MỘT SỐ entry point. **Mục tiêu: audit TOÀN BỘ entry point mutation của miền và gắn guard nhất quán MỘT LẦN** (không vá lẻ) — để lần E2E sau không lòi sibling.

## 4 lỗ hiện tại (fix + tìm mọi entry point cùng loại)
- **H-1 — dispense không trừ kho:** `POST /pharmacy/dispense/{id}` lật `dispensed` nhưng khi không còn PIB reserved thì `movements:[]`, kho không đổi, không ghi stock_movement. Fix: dispense phải là no-op/4xx nếu không có gì để trừ; KHÔNG lật status khi chưa ghi movement. File: `pharmacy/services/dispense_service.py ~113-153`, routes.
- **H-2 — dịch vụ thêm vào invoice DRAFT bị bỏ khi submit:** draft KHÔNG auto-resync (comment M-9 sai); `submit()` phát hành line cũ → thất thoát doanh thu, không cảnh báo. Fix: `submit()` re-pull/resync dòng dịch vụ từ visit trước khi issue (hoặc chặn issue draft stale + cảnh báo). File: `billing/services/invoice_service.py:522`, `services/services/visit_service_service.py`.
- **H-3 — visit COMPLETED với 0đ khi HĐ đã refunded:** `get_completion_blockers` lọc `status.notin_(('void',))` (bỏ sót refunded) + tính "unpaid" loại cả paid lẫn refunded → visit có dịch vụ billable + chỉ HĐ void/refunded vẫn complete được. Fix: completion-gate coi void **và** refunded là "không phủ"; visit có dịch vụ billable chưa được HĐ PAID phủ → chặn complete. File: `visits/services/visit_completion_service.py`, `visit_service.py`.
- **H-4 — sửa/hủy dòng dịch vụ trên visit COMPLETED+PAID:** `cancel_visit_service`/`update_status` KHÔNG gọi `raise_if_visit_closed` (chỉ add/delete/price có). Fix: gắn `raise_if_visit_closed` cho MỌI mutation dòng dịch vụ. File: `services/services/visit_service_service.py`, `services/api/routes.py`.

## Yêu cầu rà soát hệ thống (quan trọng)
- [ ] Liệt kê MỌI endpoint/hàm mutate: visit content, visit-service (add/update/update_status/cancel/delete/price), prescription/prescription-item, dispense/undispense, invoice line/submit/void/refund/recall. Với mỗi cái, xác định bất biến áp dụng: (a) `raise_if_visit_closed` khi visit đóng; (b) invoice-service sync khi issue; (c) completion-gate đúng với void/refunded; (d) dispense luôn ghi movement/trừ kho.
- [ ] Gắn guard nhất quán ở TẤT CẢ (không chỉ 4 repro), tái dùng helper sẵn có.
- [ ] Ghi bảng "entry point × bất biến" trong handoff để review kiểm tính đầy đủ.

## Acceptance Criteria
- [ ] H-1: dispense không lật status/không trừ kho ảo → no-op/4xx khi rỗng, ghi movement khi thực trừ.
- [ ] H-2: submit re-sync dịch vụ (hoặc chặn stale + cảnh báo) → không thất thoát doanh thu.
- [ ] H-3: visit không COMPLETED được khi dịch vụ billable chưa được HĐ PAID phủ (void/refunded không tính).
- [ ] H-4: mọi mutation dòng dịch vụ trên visit đóng → 409.
- [ ] Integration test cho cả 4 + vài entry-point sibling; không hồi quy TASK-108/112/119/120.

## Progress Checklist
- [x] Implementation | [x] Review | [x] Testing | [x] Documentation

## Blockers
Không. Đợt lớn — làm cẩn thận, audit đầy đủ để tránh whack-a-mole tiếp.

## Testing Completed (2026-07-26)
Dedicated invariant suite `test_task123_invariant_enforcement.py`: 8/8 passed (H-1, H-2, H-3 x2, H-4 x3). Broader sweep (billing/pharmacy/services/visits/prescriptions): 196/197 passed, 1 pre-existing out-of-scope teardown ERROR. No TASK-108/112/119/120 regression. See `deliveries/test-reports/test-report.md` and `handoff/test-to-documentation.md`.

## Documentation Completed (2026-07-26)
Final specification document: `docs/tasks/TASK-123/deliveries/final-specs/invariant-enforcement-sweep.md`. Complete audit of 19 entry points with explicit entry-point × invariant coverage matrix, all 4 hardening fixes detailed, and zero-regression verification.
