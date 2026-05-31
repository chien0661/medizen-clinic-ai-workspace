# Review → Test Handoff — TASK-066 (Round 2 APPROVED)

**Date:** 2026-05-31
**Reviewer:** Code Review Agent
**Decision:** APPROVED (round-2 fix verification)
**Status transition:** IN_REVIEW → IN_TESTING

## Round-2 commits verified

| Repo | Commit | Subject |
|------|--------|---------|
| clinic-cms-merge (`feature/TASK-066-ar-aging-report`) | `476d61a` | fix(reports): neutralize CSV formula injection in AR aging export |
| clinic-cms-web (`feature/TASK-066-remove-mock-data`) | `e6e956e` | fix(reports): neutralize CSV formula injection in client-side AR aging export |

## Fix verification

### 1. BE `_csv_safe()` — CSV formula injection neutralization
File: `app/modules/reports/services/ar_aging_service.py:46-52`
```python
def _csv_safe(v: str) -> str:
    return "'" + v if v and v[0] in ("=", "+", "-", "@", "\t", "\r") else v
```
- Char set covered: `=`, `+`, `-`, `@`, TAB (`\t`), CR (`\r`) — all 6 required triggers. ✅
- Applied to ALL user-controlled string fields: `patient_code` (line 224) + `patient_name` (line 225). ✅
- Numeric columns (buckets, total) are not user-controlled — correctly left unguarded. ✅

### 2. FE `csvSafe()` — matches BE char set
File: `src/pages/reports/ARAgingReportPage.tsx:60-61`
```ts
const csvSafe = (v: string): string =>
  /^[=+\-@\t\r]/.test(v) ? `'${v}` : v;
```
- Regex `^[=+\-@\t\r]` matches the BE tuple exactly (same 6 chars). ✅
- Applied to `patient_code` (line 66) + `patient_name` (line 67, inside quoted cell). ✅

### 3. BE integration test added
File: `tests/integration/reports/test_ar_aging_e2e.py:712`
`test_ar_aging_csv_export_neutralizes_formula_injection` — seeds patient named `=SUM(A1:A10)`, asserts the exported CSV cell is neutralized to `'=SUM(A1:A10)` and that no unguarded `,=SUM` / line-starting `=SUM` appears. ✅

### 4. `doctor_weekly_service.py` — AWAITING_PAYMENT inclusion documented
File: `app/modules/reports/services/doctor_weekly_service.py:26-30`
Comment explains AWAITING_PAYMENT counts as completed work (consultation done, billing pending) to avoid undercounting weekly volume. `_COMPLETED_STATUSES = ("COMPLETED", "AWAITING_PAYMENT")`. ✅

## Test run

```
docker exec clinic_cms_w2e_api pytest -q tests/integration/ --tb=short -k "ar_aging or report"
→ 29 passed, 688 deselected, 26 warnings in 27.70s
```
All passing. Warnings are pre-existing (unknown `integration` mark, FastAPI ORJSONResponse deprecation) — not introduced by this task.

## Notes for Test Agent

- Functional E2E focus areas: (a) AR aging bucketing correctness against real unpaid invoices, (b) CSV export download + formula-injection neutralization (already unit-covered, verify via UI), (c) ARAgingReportPage error state (no MOCK_DATA fallback — confirm error UI shows on API failure, no fabricated 30.1M figures), (d) DoctorDashboard weekly chart uses real `/reports/doctor-weekly` data.
- Permission gate `report.financial` + RLS tenant scoping should be exercised.
- FE branch is `feature/TASK-066-remove-mock-data`; BE branch is `feature/TASK-066-ar-aging-report`.

---

## Round 3 fix-verification (2026-05-31) — APPROVED

**Scope:** Verify the round-3 FE commit fixing 2 stale `ARAgingReportPage` tests.

**Commit checked:** `8269f5c` — fix(TASK-066): update ARAgingReportPage tests to expect error state instead of mock fallback

**Files changed:** `src/tests/reports/ARAgingReportPage.test.tsx` only — no production code touched. ✅

**Diff summary:**
- Test 1 "shows error state when BE unavailable" — now asserts `ar-aging-error` testid visible and "Chi tiết theo bệnh nhân" NOT present (no MOCK_DATA fallback). ✅
- Test 2 "renders patient data in table when API succeeds" — uses `vi.mocked(api.get).mockResolvedValueOnce(fixture)` instead of rejection + MOCK_DATA. ✅
- `beforeEach` now defaults `api.get` to reject (BE unavailable); QueryClient gets `retryDelay: 0`. Sensible test hygiene.

**Test runs:**
- Full FE suite: `npm test --silent` → **88 files / 914 tests passed**, 0 failures.
- Targeted: `vitest run src/tests/reports/ARAgingReportPage.test.tsx` → **4 passed**.

**Verdict: APPROVED.** Task moved to IN_TESTING. BE branch unchanged from Round 2 (already approved).
