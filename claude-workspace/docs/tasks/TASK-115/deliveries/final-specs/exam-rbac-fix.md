# TASK-115: Exam RBAC — Receptionist Gate Fix

## Issue
`POST /visits/{id}/exam` only checked `visit.write` permission, allowing receptionist (who has no clinical privileges) to:
- Create/overwrite exam clinical data
- Auto-promote visit state from WAITING → IN_PROGRESS (bypassing clinical start gate)

Meanwhile, `/exam-templates` and vitals endpoints properly required clinical capabilities.

## Fix Applied
Added role-based access control to exam submission:
- **Before**: `visit.write` → accepts receptionist
- **After**: `require_role([doctor, nurse, admin])` → rejects receptionist with 403

Matches existing gates for `/start` and `/complete` endpoints.

### Files Changed
- `app/modules/exam_templates/api/routes.py`
- `services/visit_exam_service.py`

## Verification
- **Unit & Integration Tests**: 85/85 passed on isolated stack `x115`
- **Live API Verification** (real per-role tokens, not admin):
  - Receptionist: `POST /exam` → 403, visit stays WAITING ✓
  - Doctor: `POST /exam` → 200, visit auto-transitions to IN_PROGRESS ✓
  - Nurse: `POST /exam` → 200, visit auto-transitions to IN_PROGRESS ✓

## Result
Receptionist can no longer write exam data or auto-start visits. Clinical roles (doctor/nurse) retain full functionality.
