---
id: TASK-104
type: bug
title: "[High] substitute_batch cho phép thay sang lô ĐÃ HẾT HẠN (bỏ qua FEFO)"
status: DONE
priority: High
assigned: Documentation Agent
created: 2026-07-24
updated: 2026-07-24
branch: "fix/TASK-104-substitute-expiry"
tags: [pharmacy, reservation, patient-safety, high, e2e-finding]
affected-repos: [clinic-cms]
refs:
  other:
    - "docs/tasks/TASK-095/deliveries/test-reports/full-system-e2e-report.md (H-2)"
---

# TASK-104: [High] substitute_batch cho lô hết hạn

## Documentation (2026-07-24)
- **Status:** DONE
- **Document:** `docs/tasks/TASK-104/deliveries/final-specs/substitute-batch-expiry-fix.md`
- **Summary:** Documented expiry_date guard implementation, test results (22/22), and verification steps.

---

**Nguồn:** E2E TASK-095, H-2. Cùng hàm với TASK-099 (đã fix guard khác-thuốc); đây là guard **hết hạn**.

- **Kỳ vọng:** substitution từ chối lô có `expiry_date <= hôm nay` (reserve đã enforce `expiry_date > date.today()` ở line 80).
- **Thực tế:** HTTP 200, chuyển sang lô hết hạn (vd expiry 2026-06-22) → dispense sẽ cấp thuốc hết hạn. Query lô mới (line 220-231) chỉ lọc clinic_id/is_deleted/is_recalled, thiếu `expiry_date > today`.
- **File:** `app/modules/pharmacy/services/reservation_service.py`

## Acceptance Criteria
- [x] substitute_batch từ chối (400/409) lô có expiry_date <= hôm nay.
- [x] Integration test: lô hết hạn → bị chặn; lô còn hạn cùng thuốc → OK (không hồi quy TASK-099 guard).

## Progress Checklist
- [x] Implementation | [x] Review | [x] Testing | [x] Documentation

## Blockers
Không. (Base nên off `dev` để có sẵn guard khác-thuốc của TASK-099.)

## Implementation Notes (2026-07-24)
- Branch `fix/TASK-104-substitute-expiry` off `origin/dev` @ `f305496`, commit `bf69604`, pushed.
- Fix: added `new_batch.expiry_date <= date.today()` guard in `substitute_batch()` → `ConflictError`
  (409), placed before the existing TASK-099 different-medicine guard. See
  `docs/tasks/TASK-104/handoff/implementation-to-review.md` for full detail.
- Tests: 2 new integration tests added; full pharmacy suite 13/13 passed (isolated Docker stack,
  project `fix104`, ports 9979/5479/6461). `ruff`/`mypy`: 0 new findings.
- Worktree: `F:/MyProject/clinic-cms-workspace/_fix104-be` (left in place for reviewer).

## Testing Notes (2026-07-24)
- Testing Completed: 2026-07-24
- Isolated stack `w104` (api 9979/pg 5479/redis 6461), migrate head + seed. `pytest -q --tb=short tests/integration/pharmacy tests/unit/pharmacy` → **22 passed, 0 failed**.
- H-2 confirmed fixed: expired-batch substitution → 400/409, reservation unchanged. No regression on TASK-099 cross-medicine guard or base substitute flow.
- Test report: `docs/tasks/TASK-104/deliveries/test-reports/test-report.md`. Stack torn down (`down -v`); worktree left untouched.
