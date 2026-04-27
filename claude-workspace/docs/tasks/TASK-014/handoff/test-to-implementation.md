# Handoff: TASK-014 Test → Implementation (Round 2 Fix)

**From**: Test Agent  
**To**: Code Implementation Agent  
**Status**: IN_PROGRESS (returned from IN_TESTING due to 9 test failures)  
**Date**: 2026-04-27  
**Branch**: `feature/task-014-hr-schedule` (worktree: `clinic-cms-task014`)  
**Commit**: `796de42` (test files added)

---

## Why Returned

The Test Agent added 64 new complementary tests (API contracts, business rules, E2E workflows). **9 of 64 fail**, covering 4 bugs:

| Bug | Severity | Summary |
|-----|----------|---------|
| BUG-001 | CRITICAL | BYPASSRLS: app DB user is superuser → cross-clinic PATCH/approve allowed |
| BUG-002 | MAJOR | PATCH /shifts and /shift-templates accept inverted end_time ≤ start_time |
| BUG-003 | MAJOR | Leave self-approval not rejected (UUID type mismatch in service check) |
| BUG-004 | CRITICAL | check-in allowed on soft-deleted shift + cross-user shift (UUID type mismatch + ORM cache) |

Full bug details in:
- `docs/tasks/TASK-014/bugs/BUG-001.md`
- `docs/tasks/TASK-014/bugs/BUG-002.md`
- `docs/tasks/TASK-014/bugs/BUG-003.md`
- `docs/tasks/TASK-014/bugs/BUG-004.md`

---

## What Still Passes (Do Not Break)

- All 31 existing HR tests: `tests/unit/test_hr_service_logic.py` (17) + `tests/integration/test_hr_e2e.py` (14) — all PASS
- All 6 Acceptance Criteria: PASS
- All 7 workflow tests: PASS
- 55 of 64 new tests: PASS

**Run this to verify before submitting for re-review:**
```bash
cd E:/MyProject/clinic-cms-workspace/clinic-cms-task014
# or inside Docker:
docker exec clinic_cms_api sh -c "cd /app && python -m pytest tests/ -q --no-header --tb=no --ignore=tests/integration/test_alembic.py -k 'hr' 2>&1"
```

---

## Specific Fixes Required

### FIX-1 (BUG-001): Cross-Clinic Mutation via BYPASSRLS

**Root cause**: `db.get(ShiftTemplate, id)`, `db.get(Shift, id)`, `db.get(LeaveRequest, id)`, `db.get(RecurringSchedule, id)` bypass RLS because the `cms` DB user has `BYPASSRLS=True` (superuser).

**Service layer fix** (immediate, belt-and-suspenders): Add `clinic_id` check in every `get_*()` function. This protects even when BYPASSRLS is set.

In `shift_service.py`:
```python
async def get_shift_template(db: AsyncSession, template_id: UUID, clinic_id: UUID | None = None) -> ShiftTemplate:
    tmpl = await db.get(ShiftTemplate, template_id)
    if tmpl is None or tmpl.is_deleted:
        raise NotFoundError("ShiftTemplate not found")
    if clinic_id is not None and str(tmpl.clinic_id) != str(clinic_id):
        raise NotFoundError("ShiftTemplate not found")  # Don't leak existence
    return tmpl

async def get_shift(db: AsyncSession, shift_id: UUID, clinic_id: UUID | None = None) -> Shift:
    shift = await db.get(Shift, shift_id)
    if shift is None or shift.is_deleted:
        raise NotFoundError("Shift not found")
    if clinic_id is not None and str(shift.clinic_id) != str(clinic_id):
        raise NotFoundError("Shift not found")
    return shift
```

In `leave_service.py`:
```python
async def get_leave_request(db: AsyncSession, leave_id: UUID, clinic_id: UUID | None = None) -> LeaveRequest:
    lr = await db.get(LeaveRequest, leave_id)
    if lr is None or lr.is_deleted:
        raise NotFoundError("LeaveRequest not found")
    if clinic_id is not None and str(lr.clinic_id) != str(clinic_id):
        raise NotFoundError("LeaveRequest not found")
    return lr
```

In `recurring_service.py` — same pattern for `get_recurring_schedule()`.

**Route fix** (`routes.py`): Pass `clinic_id=_clinic_id()` to all `get_*` calls that are called from route handlers (via update/delete/approve/reject calls).

**Failing tests fixed by this**:
- `test_user_b_cannot_patch_clinic_a_shift_template`
- `test_user_b_cannot_patch_clinic_a_shift`
- `test_user_b_cannot_approve_clinic_a_leave`

### FIX-2 (BUG-002): Inverted Times Accepted by PATCH

**Root cause**: The `BusinessRuleError` raised in `update_shift()` / `update_shift_template()` is not converted to HTTP 400. The exception handler for `BusinessRuleError` may not be registered, or the `db.flush()` before the check silently commits the mutation.

**Fix options**:
1. Move the time-order check BEFORE `db.flush()` in `update_shift()` and `update_shift_template()`.
2. Verify `BusinessRuleError` is registered in `app/core/exceptions.py` exception handlers.

In `shift_service.py`, reorder `update_shift()`:
```python
async def update_shift(db, shift_id, *, updated_by=None, **fields):
    shift = await get_shift(db, shift_id)
    for key, val in fields.items():
        if val is not None and hasattr(shift, key):
            setattr(shift, key, val)
    # Check BEFORE flush
    if shift.end_time <= shift.start_time:
        raise BusinessRuleError("end_time must be after start_time")
    shift.updated_by = updated_by
    db.add(shift)
    await db.flush([shift])
    await db.refresh(shift)
    return shift
```
(This is already the order in the code — so the issue is the exception handler not catching it properly.)

Check `app/core/exceptions.py` for `BusinessRuleError` → HTTP 400 mapping.

**Failing tests fixed by this**:
- `test_br01_patch_shift_to_inverted_times_rejected`
- `test_br01_patch_shift_template_equal_times_rejected`

### FIX-3 (BUG-003): Leave Self-Approval UUID Type Mismatch

**Root cause**: `lr.user_id == approved_by` comparison fails when `lr.user_id` is `uuid.UUID` and `approved_by` is `str` (or vice versa).

**Fix** in `leave_service.py`:
```python
if str(lr.user_id) == str(approved_by):
    raise BusinessRuleError("Cannot approve your own leave request")
```

**Failing test fixed by this**:
- `test_br07_self_approval_rejected_400`

### FIX-4a (BUG-004): check-in on soft-deleted shift

**Root cause**: `db.get(Shift, shift_id)` returns ORM-cached version that may not reflect `is_deleted=True` after a soft-delete in a different request context.

**Fix** in `attendance_service.py`, use explicit SELECT:
```python
from sqlalchemy import select

result = await db.execute(
    select(Shift).where(Shift.id == shift_id, Shift.is_deleted.is_(False))
)
shift = result.scalars().first()
if shift is None:
    raise NotFoundError("Shift not found")
```

**Failing test fixed by this**:
- `test_br09_checkin_with_deleted_shift_404`

### FIX-4b (BUG-004): cross-user check-in UUID type mismatch

**Root cause**: `shift.user_id != user_id` fails when types differ (same as BUG-003).

**Fix** in `attendance_service.py`:
```python
if str(shift.user_id) != str(user_id) or str(shift.clinic_id) != str(clinic_id):
    raise ForbiddenError("Cannot check in to a shift that does not belong to you")
```

**Failing tests fixed by this**:
- `test_br10_staff_cannot_checkin_admins_shift`
- `test_check_in_with_cross_clinic_shift_id_forbidden` (BUG-001/004 overlap)

---

## Affected Files

```
app/modules/hr/services/shift_service.py        — FIX-1, FIX-2
app/modules/hr/services/leave_service.py        — FIX-1, FIX-3
app/modules/hr/services/recurring_service.py   — FIX-1
app/modules/hr/services/attendance_service.py   — FIX-4a, FIX-4b
app/modules/hr/api/routes.py                   — FIX-1 (pass clinic_id)
app/core/exceptions.py                         — FIX-2 (verify BusinessRuleError handler)
```

---

## Verification Checklist

After fixing, re-run:
```bash
docker exec clinic_cms_api sh -c "cd /app && python -m pytest tests/integration/test_hr_api_contracts.py tests/integration/test_hr_business_rules.py tests/integration/test_hr_workflows.py tests/unit/test_hr_service_logic.py tests/integration/test_hr_e2e.py -q --no-header --tb=no 2>&1"
```

Expected: **95/95 pass** (0 failures in the 95 HR-related tests).

Then submit for **Code Review Round 3** with this handoff:
- `docs/tasks/TASK-014/handoff/test-to-implementation.md` (this file)
- Bug reports: `docs/tasks/TASK-014/bugs/BUG-001.md` through `BUG-004.md`
- Test report: `docs/tasks/TASK-014/deliveries/test-reports/test-report.md`

---

## What to Keep Unchanged

- All 3 new test files (`test_hr_api_contracts.py`, `test_hr_business_rules.py`, `test_hr_workflows.py`) — **do not modify tests**
- Existing 35 developer tests — must remain passing
- All 6 Acceptance Criteria — must remain passing

---

## Out of Scope for This Fix

- BYPASSRLS at DB user level (recommended but requires infra change — optional for V1 if service-layer fix provides adequate protection)
- Multi-timezone support (documented as deferred)
- Biometric/QR check-in (hardware dependency)
