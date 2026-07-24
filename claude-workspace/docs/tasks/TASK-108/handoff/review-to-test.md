# Handoff: TASK-108 → Test Agent

**From**: Code Review Agent
**To**: Test Agent
**Status**: IN_TESTING
**Decision**: APPROVED
**Date**: 2026-07-24
**Branch**: `fix/TASK-108-visit-service-guards` (commit `54c31f1`)

## Summary

M-8 (missing visit → 404 instead of 500) and M-9 (block 409 when the visit has
an active issued/partially_paid/paid invoice, to prevent silent under-billing)
are both correctly implemented and well-scoped to `add_to_visit`. The M-9 status
set was verified complete and correct against the full invoice enum. Passed review
with only MINOR/INFO notes.

## Key Findings (for awareness)

- MINOR: `is_deleted == False` (noqa'd) vs `.is_(False)` style inconsistency.
- MINOR: handoff prose loosely equates M-9's set with `create_from_visit`'s
  idempotency set (that one includes `draft`); actual behavior is correct.
- INFO: two extra `db.execute` round-trips per add — acceptable, not a hot path.
- Static analysis on host is broken (`WinError 193`); verified by inspection.

## Focus Areas for Testing

1. **M-8**: `POST /visits/{unknown}/services` → 404 (not 500). Also confirm a
   *soft-deleted* visit behaves like missing.
2. **M-9 block**: add service when invoice is `issued`, `partially_paid`, and
   `paid` — all must 409; invoice total must stay untouched while blocked.
3. **M-9 non-block (no over-block)**: add still works with a `draft` invoice,
   with no invoice, and after `void`/`refund` (post-void re-add allowed).
4. **Escape hatch**: `recall` (issued+unpaid → draft) then re-add → 201, and the
   recalled invoice auto-resyncs the new line.
5. **No regression**: normal pre-invoice add still 201; existing closed-visit
   409 (CANCELLED) still holds; full billing lifecycle (submit/void/refund/payment) intact.
