# Handoff: TASK-066 → Code Implementation Agent

**From**: Test Agent
**To**: Code Implementation Agent
**Status**: IN_PROGRESS
**Date**: 2026-05-31

---

## Summary

Tests FAILED (945/947). Core implementation is correct and verified — the failure is **2 stale FE unit tests** that still test the old MOCK_DATA fallback behavior which was correctly removed in TASK-066.

BE integration tests: 29/29 PASS
FE unit tests: 912/914 PASS (2 fail — stale test code)
Playwright E2E: 4/4 PASS — no mock data visible in UI

**Bug report**: `docs/tasks/TASK-066/bugs/BUG-066-001.md`

---

## Failures

### Failing Tests

File: `clinic-cms-web/src/tests/reports/ARAgingReportPage.test.tsx`

1. **`renders with mock fallback data when BE unavailable`** (line 90-103)
   - Mocks `api.get` to reject, then expects `"Chi tiết theo bệnh nhân"` heading to appear
   - **Why it fails**: The patient table section (`"Chi tiết theo bệnh nhân"`) is only rendered when `data` is truthy. When API fails, `data` is undefined and the error state (`data-testid="ar-aging-error"`) is shown instead.
   - **Fix**: Update test name + assertions → assert `data-testid="ar-aging-error"` is visible and `"Không thể tải dữ liệu báo cáo công nợ"` is shown.

2. **`renders mock patient data in table`** (line 105-111)
   - Mocks `api.get` to reject, expects `"Nguyễn Văn An"` patient from old MOCK_DATA
   - **Why it fails**: Old MOCK_DATA (which had "Nguyễn Văn An") was removed. API rejection now shows error state.
   - **Fix**: Change `api.get` mock to **resolve** with a valid `ARAgingResponse` fixture containing test patient data, then assert the patient appears in the table.

---

## Required Fix (test code only — do NOT touch implementation files)

### Suggested test changes in `src/tests/reports/ARAgingReportPage.test.tsx`

Replace the two failing tests:

```typescript
// OLD (line 90): renders with mock fallback data when BE unavailable
// REPLACE WITH:
it("shows error state when BE unavailable", async () => {
  render(<ARAgingReportPage />, { wrapper: Wrapper });

  await waitFor(() => {
    expect(screen.getByTestId("ar-aging-error")).toBeInTheDocument();
  });

  // Patient table should NOT be visible
  expect(screen.queryByText("Chi tiết theo bệnh nhân")).not.toBeInTheDocument();
});

// OLD (line 105): renders mock patient data in table
// REPLACE WITH — mock api.get to RESOLVE, not reject:
it("renders patient data in table when API succeeds", async () => {
  const { api } = await import("../../lib/apiClient");
  vi.mocked(api.get).mockResolvedValueOnce({
    as_of_date: "2026-05-31",
    total_0_30: 500000,
    total_31_60: 0,
    total_61_90: 0,
    total_over_90: 0,
    grand_total: 500000,
    patients: [{
      patient_id: "p-001",
      patient_code: "BN001",
      patient_name: "Nguyễn Văn An",
      bucket_0_30: 500000,
      bucket_31_60: 0,
      bucket_61_90: 0,
      bucket_over_90: 0,
      total_outstanding: 500000,
    }],
  });

  render(<ARAgingReportPage />, { wrapper: Wrapper });

  await waitFor(() => {
    expect(screen.getByText("Nguyễn Văn An")).toBeInTheDocument();
  });
});
```

Note: The top-level `vi.mock` for `api.get` already mocks it to reject. For the success test, use `mockResolvedValueOnce` to override per-test.

---

## What Passed (do not regress)

- `smoke: renders without error` — PASS
- `renders page title` — PASS
- All 29 BE integration tests — PASS
- All 4 Playwright E2E scenarios — PASS

The implementation is correct. Only the test file needs updating.

---

## Test Report

Full test report: `docs/tasks/TASK-066/deliveries/test-reports/test-report.md`
Screenshots: `docs/tasks/TASK-066/deliveries/test-reports/screenshots/`
