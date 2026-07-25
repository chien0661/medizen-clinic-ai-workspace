# TASK-118: Frontend UX Cluster Fix (M-13, M-14, M-16)

## Issue M-13: Service Dropdown Shows 0đ Price
Service picker ("Thêm dịch vụ") displayed all services with price=0đ; real prices only appeared after adding the item to exam.

**Root cause**: Picker component used `default_price: 0` instead of fetching `unit_price` from service data.

## Issue M-14: Doctor Dashboard Fires Permission-Denied Requests
Doctor's dashboard page repeatedly called endpoints they couldn't access:
- `/reports/revenue` → 403 (requires `report.financial`)
- `/shifts` → 403 (requires `shift.manage`)
- `/attendance/me` → 400 (HR not integrated)

Result: Console spam, broken KPI cards, misleading 403 errors.

## Issue M-16: Appointment Card Shows UUID Instead of Patient Name
Appointment cards displayed truncated UUID (e.g., 'f7ff6af4...') instead of patient name + code like the queue board.

## Fixes Applied

### M-13: Use Correct Price Field
- Changed picker to display `unit_price` from service entity (not `default_price: 0`)
- Aligns with existing exam/CLS services display

### M-14: Gate Requests by Permission
- **Revenue card/chart**: Hidden if `report.financial` permission missing
- **Shifts query** (`hrApi.myShifts`): Only fires if `shift.manage` permission present
- No request fired → no 403/400 spam, no broken cards

### M-16: Resolve Patient Name on Cards
- Appointment card now resolves patient ID to `patient.name` + `patient.code`
- Falls back to UUID if name unavailable (e.g., deleted patient)
- Matches queue board display pattern

### Files Changed
- FE: Service picker, Dashboard components, Appointment card components
- 4 test files updated with permission-gated scenarios

## Verification
- **Frontend Tests**: 21/21 vitest passed (`ServicesTab.test.tsx`, `AttendanceWidget.test.tsx`, `MainDashboardPage.test.tsx`, `AppointmentPage.test.tsx`)
- **Type-check**: `tsc --noEmit` clean ✓
- **Key scenarios confirmed**:
  - Service price shown in picker (not 0đ) ✓
  - Shifts query does NOT fire without `shift.manage`; does fire with it ✓
  - Revenue KPI/chart hidden without `report.financial` ✓
  - Appointment card shows patient name (+ code) with UUID fallback ✓

## Result
Doctor dashboard no longer spams permission errors; prices display correctly; patient names appear on appointment cards.

## Follow-up Items
- **getRangeStats** in revenue module may call revenue endpoint unconditionally (gated queries caller-side, not backend) — review if dashboard calls it without permission check
