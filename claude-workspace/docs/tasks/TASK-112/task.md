---
id: TASK-112
type: bug
title: "[Medium] Đảo tiền (void/refund) trên visit COMPLETED không mở khóa visit"
status: DONE
priority: High
assigned: Documentation Agent
created: 2026-07-25
updated: 2026-07-25
branch: "fix/TASK-112-unlock-visit-on-reversal"
tags: [visits, billing, data-integrity, state-machine, medium, e2e-finding]
affected-repos: [clinic-cms]
refs:
  other:
    - "docs/tasks/TASK-095/deliveries/test-reports/full-system-e2e-report.md (M-5)"
---

# TASK-112: [Medium→cao] Đảo tiền không gỡ khóa visit COMPLETED (M-5)

**Nguồn:** E2E TASK-095, M-5. Đây chính là lỗ hổng đã phát hiện ở test luồng hủy-hóa-đơn (TASK-095): "hủy HĐ rồi sửa" không liền mạch vì visit không gỡ khóa.

- **Kỳ vọng:** Khi đảo tiền (void payment / recall / refund) trên visit COMPLETED, visit về `AWAITING_PAYMENT` (mở lại để sửa/thu lại), hoặc chặn đảo.
- **Thực tế:** Visit vẫn COMPLETED + khóa nội dung (PATCH/exam/vitals→409) trong khi invoice về issued/unpaid. Không có transition COMPLETED→AWAITING_PAYMENT → kẹt. `completion-blockers` báo visit KHÔNG completable dù đang COMPLETED.
- **File:** `app/modules/visits/services/state_machine.py`, `billing/services/payment_service.py`, `invoice_service.py`, `visits/services/visit_service.py`

## Hướng fix (đề xuất — khớp luồng người dùng "hủy hóa đơn → sửa")
Thêm transition/code path: khi void payment / recall / refund làm invoice của visit không còn paid-đủ, đưa visit `COMPLETED → AWAITING_PAYMENT` (gỡ khóa nội dung). Đảm bảo nhất quán với TASK-094 lock rule (COMPLETED/CANCELLED khóa; AWAITING_PAYMENT sửa được).

## Acceptance Criteria
- [x] Void payment / recall / refund trên visit COMPLETED → visit về AWAITING_PAYMENT, nội dung sửa được lại (PATCH/exam 200).
- [x] Sau đó thu tiền lại → visit COMPLETED lại (round-trip sạch).
- [x] Integration test round-trip: complete → void → editable → re-pay → complete.

## Progress Checklist
- [x] Implementation | [x] Review | [x] Testing | [x] Documentation

## Documentation Completed
Documentation Completed: 2026-07-25 — Final specs in `docs/tasks/TASK-112/deliveries/final-specs/reopen-visit-on-payment-reversal-fix.md`

## Testing — 2026-07-25 (PASSED -> DOCUMENTING)
178/178 tests passed (`tests/integration/billing`, `tests/integration/visits`,
`tests/unit/visits`) in isolated stack `w112`. Round-trip (complete -> void ->
AWAITING_PAYMENT -> re-pay -> COMPLETED) verified, recall/refund variants OK,
regression guard (COMPLETED->complete still 409) confirmed. See
`handoff/test-to-documentation.md` and `deliveries/test-reports/test-report.md`.

## Review — 2026-07-25 (APPROVED → IN_TESTING)
Review Completed: 2026-07-25. Decision APPROVED, no critical/major issues.
Shared `ALLOWED_TRANSITIONS` table confirmed behaviorally unchanged (key risk cleared);
reopen path separate + self-guarded. See `handoff/review-report.md` and `handoff/review-to-test.md`.

## Blockers
Không (fix ở tầng app; không phụ thuộc RLS).

## Implementation — 2026-07-25
Branch `fix/TASK-112-unlock-visit-on-reversal` (base `origin/dev` @ `6d91053`), pushed.
Commit `c27b860`. See `handoff/implementation-to-review.md` for full detail.
