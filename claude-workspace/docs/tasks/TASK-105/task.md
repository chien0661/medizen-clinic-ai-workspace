---
id: TASK-105
type: bug
title: "[High] Refund không đảo payment → report payment-methods đếm tiền đã-thu vĩnh viễn sai"
status: DONE
priority: High
assigned: Documentation Agent
created: 2026-07-24
updated: 2026-07-24
branch: "fix/TASK-105-refund-reversal"
tags: [billing, refund, reports, data-integrity, high, e2e-finding]
affected-repos: [clinic-cms]
refs:
  other:
    - "docs/tasks/TASK-095/deliveries/test-reports/full-system-e2e-report.md (H-3)"
---

# TASK-105: [High] Refund không đảo tiền đã thu

## Documentation (2026-07-24)
- **Status:** DONE
- **Document:** `docs/tasks/TASK-105/deliveries/final-specs/refund-reversal-fix.md`
- **Summary:** Documented Approach A (void payments), reconciliation of payment-methods and revenue reports, test results (81/81).

---

**Nguồn:** E2E TASK-095, H-3.

- **Kỳ vọng:** Refund hóa đơn đã trả phải đảo tiền đã thu (void payment / bút toán âm / loại khỏi "collected").
- **Thực tế:** `refund_invoice` chỉ set status=refunded + release stock; `paid_total` giữ nguyên, payment `is_voided=FALSE`. `payment_method_service` cộng mọi payment không-void, không join status hóa đơn → tiền refunded vẫn "đã thu". `void_payment` từ chối chạy trên hóa đơn refunded → không đảo được → sai vĩnh viễn. Mâu thuẫn với revenue report (loại refunded).
- **Bằng chứng:** invoice refunded paid_total=220000; payment-methods total gồm 220000; revenue loại 220000.
- **File:** `app/modules/billing/services/invoice_service.py`, `payment_service.py`, `app/modules/reports/services/payment_method_service.py`

## Acceptance Criteria
- [x] Refund đảo/void các payment liên quan (hoặc loại refunded khỏi payment-methods) → payment-methods và revenue nhất quán về cùng khoản tiền.
- [x] Integration test: refund → payment-methods không còn tính khoản đã hoàn; revenue = payment-methods về cùng dữ liệu.

## Progress Checklist
- [x] Implementation | [x] Review | [x] Testing | [x] Documentation

## Blockers
Không. (Quyết định cách đảo: void payment vs loại theo status — impl đề xuất, review chốt.)

## Implementation notes (2026-07-24)
Approach A chosen (void the payments on refund) — see
`docs/tasks/TASK-105/handoff/implementation-to-review.md` for full rationale,
diff summary, and verification (100 integration tests passed, 0 new ruff/mypy
findings). Branch `fix/TASK-105-refund-reversal` pushed to origin, based on
`origin/dev` @ `f305496`. Worktree left at
`F:/MyProject/clinic-cms-workspace/_fix105-be` for the reviewer.

## Testing Notes (2026-07-24)
- Testing Completed: 2026-07-24
- Isolated stack `w105` (api 9978/pg 5478/redis 6460), migrate head + seed. `pytest -q --tb=short tests/integration/billing tests/integration/reports` → **81 passed, 0 failed**.
- H-3 confirmed fixed: refund voids the payment, reverses invoice paid_total/balance_due, payment-methods excludes refunded amount, and payment-methods total == revenue total_paid for the same period. Double-void (re-voiding the refund-voided payment) correctly blocked (400). No regressions on void-invoice/void-payment/create-after-refund flows.
- Test report: `docs/tasks/TASK-105/deliveries/test-reports/test-report.md`. Stack torn down (`down -v`); worktree left untouched.
