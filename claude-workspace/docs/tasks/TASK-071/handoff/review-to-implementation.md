# Review → Implementation Handoff — TASK-071 (Round 1)

**Verdict**: CHANGES_REQUESTED
**Date**: 2026-05-31
**Full report**: `handoff/review-report.md`

## What passed
- Security: all 3 analytics endpoints behind `require_superuser` (403 confirmed). No SQL injection — `granularity`/`metric`/`sort_by` are allowlist-validated, `clinic_id` is a bound UUID param.
- BE 33 tests pass, FE 17 tests pass, 0 new TS errors.
- SQL columns all match the source models; SYSTEM clinic excluded; div-by-zero guarded.

## Required changes (must fix to re-submit)

1. **[MAJOR] Enforce date-range limits** on all 3 analytics endpoints (`/overview`, `/timeseries`, `/clinics`):
   - Reject `date_from > date_to` → HTTP 422.
   - Reject range `> 365 days` (`(date_to - date_from).days > 365`) → HTTP 422.
   - This is a stated acceptance requirement ("tối đa 365 ngày") and a scan/performance guard.
   - Add at least one test for the rejection path (BE).

2. **[MINOR] Bound the `limit` param** on `/analytics/clinics`:
   - `limit: int = Query(20, ge=1, le=200)` (or your chosen ceiling).

## Optional / record-only (no code change required)
3. Add a code comment near the revenue queries noting `invoice.updated_at` is a paid-proxy and can misbucket refunded invoices (already in handoff — make it visible in code for the DB-index follow-up).

## Notes for manager (not an implementation task)
- The BE branch diff vs `main` includes unrelated modules (tags, entity_tags migration, inventory, services) because it was cut from a base ahead of `main`. Ensure the PR targets the correct base before merge.

After fixes: re-run BE + FE tests, update `handoff/implementation-to-review.md`, set `status: IN_REVIEW`. Round 2 of max 3.
