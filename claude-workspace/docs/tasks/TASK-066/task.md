---
id: TASK-066
type: feature
title: BE AR aging endpoint + gỡ MOCK_DATA fallback im lặng (ARAgingReportPage)
status: DONE
priority: High
assigned: Documentation Agent
created: 2026-05-31
updated: 2026-05-31
branch: ""
jira_key: ""
tags: [backend, frontend, reports, billing, bugfix]
affected-repos: [clinic-cms-merge, clinic-cms-web]
refs:
  detail_design: ""
  implementation_plan: ""
  figma: ""
  confluence: ""
  jira_ticket: ""
  other:
    - "docs/tasks/TASK-053/deliveries/final-specs/functional-audit.md  # §3.2, §5"
    - "docs/tasks/TASK-053/deliveries/test-reports/runtime-verification.md  # §1 — screenshot 25"
    - "clinic-cms-web/src/pages/reports/ARAgingReportPage.tsx:53-159  # MOCK_DATA + fallback"
    - "clinic-cms-merge/app/modules/reports/  # BE reports module"
    - "PROJECT.md"
---

# TASK-066: BE AR aging endpoint + gỡ MOCK_DATA fallback im lặng

## Description

TASK-053 runtime audit phát hiện **phát hiện nghiêm trọng**: `ARAgingReportPage` hiển thị số liệu công nợ **bịa** (15.2M / 8.5M / 4.3M / 2.1M = 30.1M) khi BE endpoint `/reports/ar-aging` không tồn tại:

```typescript
// ARAgingReportPage.tsx:53
const MOCK_DATA: ARAgingResponse = { ... } // hardcoded 30.1M
// line 158-159:
} catch {
  // BE endpoint not yet live (TASK-041) — return mock data
  return MOCK_DATA;
}
```

Người xem màn hình demo sẽ tưởng hệ thống có chức năng AR aging hoạt động — nhưng thực chất là số liệu giả. Đây là **khoản nợ kỹ thuật** phải xử lý trước khi go-live.

Tương tự: `DoctorDashboardPage.tsx:122` có "// Mock weekly data (replace with real API when available)" cho biểu đồ tuần.

## Requirements

### BE (`clinic-cms-merge`)
- [ ] `GET /api/v1/reports/ar-aging?from=&to=&clinic_id=` — tổng hợp công nợ phải thu theo bucket 0-30/31-60/61-90/>90 ngày, tổng cộng per patient
- [ ] `GET /api/v1/reports/ar-aging/export` — xuất CSV AR aging (có thể dùng streaming)
- [ ] Logic: join `invoices` (status = UNPAID/PARTIAL) + `patients`, tính tuổi hoá đơn từ `issue_date`
- [ ] Permission gate: `report.financial`, RLS, integration test real-DB
- [ ] `GET /api/v1/reports/doctor-weekly` (hoặc extend endpoint hiện có) — dữ liệu tuần cho DoctorDashboard chart (nếu scope cho phép)

### FE (`clinic-cms-web`)
- [ ] `ARAgingReportPage.tsx` — xoá `MOCK_DATA` const + xoá `catch { return MOCK_DATA }` fallback. Thay bằng hiển thị error state rõ ràng khi API fail (dùng `PendingBEState` hoặc toast error)
- [ ] `DoctorDashboardPage.tsx:122` — thay mock weekly data bằng call API thật (sau khi BE có endpoint)
- [ ] Verify `Xuất CSV` button gọi `/reports/ar-aging/export` thật

## Acceptance Criteria

- [ ] `GET /reports/ar-aging` trả data thật từ DB (invoices unpaid) phân bucket đúng
- [ ] ARAgingReportPage không còn MOCK_DATA; khi BE lỗi → hiện error state rõ (không hiện số bịa)
- [ ] CSV export hoạt động
- [ ] DoctorDashboard weekly chart dùng data thật (hoặc ẩn chart nếu API chưa sẵn — không dùng mock)
- [ ] `ruff check` + `mypy` + integration tests pass

## Progress Checklist

- [ ] Implementation
- [ ] Code Review
- [ ] Testing
- [ ] Documentation

## Related Files

- **FE**: `clinic-cms-web/src/pages/reports/ARAgingReportPage.tsx` · `DoctorDashboardPage.tsx`
- **BE**: `clinic-cms-merge/app/modules/reports/` + `billing/` (invoices data source)
- **Evidence**: `docs/tasks/TASK-053/deliveries/test-reports/25-reports-ar-aging-GAP.png`

## Timestamps

- **Created**: 2026-05-31
- **Started**: 2026-05-31
- **Implementation Completed**: 2026-05-31
- **Review (CHANGES_REQUESTED, back to IN_PROGRESS)**: 2026-05-31
- **Fix Applied, Re-submitted for Review**: 2026-05-31
- **Review Round 2 APPROVED → IN_TESTING**: 2026-05-31
- **Testing FAILED → IN_PROGRESS**: 2026-05-31 (2 stale FE unit tests — BUG-066-001)
- **Fix Applied (BUG-066-001), Re-submitted for Review**: 2026-05-31
- **Testing Completed (Round 2 PASSED) → DOCUMENTING**: 2026-05-31

## Notes

- ⚠️ AR aging data phụ thuộc invoices — cần đảm bảo `invoice.issue_date` và `invoice.status` đã đúng trước khi xây report.
- TASK-056 (reports dimensions) có thể share cùng sprint nhưng khác scope — AR aging là financial core, TASK-056 là analytical extras.
- KHÔNG tạo MOCK_DATA mới để "giả tạm" — từ nay trở đi tất cả endpoint thiếu phải dùng error state hiển thị rõ.

## Blockers

None
