# Handoff: TASK-120 → Test Agent

**From**: Code Review Agent
**To**: Test Agent
**Status**: IN_TESTING
**Decision**: APPROVED

## Summary
Reviewed the two prescription mutation guards (H-1 pending-block, H-4 invoice-issued-block) in `prescription_service.py`. All three reported H-1 entry points (`update`, `add_item`, `update_item`) plus `delete_item` are guarded; the H-4 guard is a byte-for-byte mirror of the TASK-108/M-9 service-add precedent with the correct status set. 8 genuine tests. No critical/major issues.

## Key Findings (MINOR)
- No dedicated compose test (pending Rx + issued invoice). Blocked outcome is guaranteed by guard ordering (pending 409 fires first) but untested — worth adding.
- `delete_item` has the pending guard but NOT the invoice-issued guard (implementer-flagged follow-up, outside H-4 scope). Latent billing-drift on delete-after-issue; track separately.

## Focus Areas for Testing
1. **Re-run the suite** — host ruff/mypy could not execute (Exec format error); the 79-passed run is documented, not independently reproduced by review. Confirm 8 new + pre-existing prescription/billing integration tests pass on a clean isolated stack.
2. **Compose case**: pending prescription on a visit with an issued invoice → confirm 409 with a clear error (pending message expected, since it short-circuits first).
3. **Status-set boundaries for H-4**: verify `void` and `refunded` invoices do NOT block item edits (only issued/partially_paid/paid do); verify `draft` invoice still allows edit + auto-resyncs.
4. **Stock re-reservation** on the blocked PATCH item path — confirm no partial reservation side-effect occurs when the guard 409s (guard runs before `_add_item_to_prescription`/re-reserve logic).
5. **Draft happy path** no-regression: draft Rx header/item edits + add still succeed.
