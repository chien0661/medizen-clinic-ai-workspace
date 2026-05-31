---
id: BUG-010
title: Doctor "My Queue" hiển thị patient UUID thay vì tên BN
severity: Medium
status: OPEN
discovered_in: TASK-049 Phase 4 — doctor mở My Queue
url: http://localhost:1420/#/doctor/queue
---

# BUG-010: Doctor "My Queue" — patient UUID thay vì tên

## Symptom
Trên trang "My Queue" của doctor (`#/doctor/queue`), mỗi visit card hiển thị:
- Visit number: `#20260504-002`
- Status badge: Waiting + Normal
- **Patient identifier**: `2a64a3fa-0262-4cd0-9c99-3e323841e593` ← UUID raw, KHÔNG phải "Nguyễn Văn E2E Test"
- Chief complaint (nếu có): "Đau đầu, sốt nhẹ 2 ngày"
- Waiting time
- Enter Consultation button

Doctor không thể nhận biết bệnh nhân nào sắp khám tiếp theo nếu không click vào — tệ UX, mất focus.

## Repro
1. Reception tạo Walk-In visit cho 1 BN
2. Login doctor (`dr_nguyen` / `Doctor@1234`) → My Queue
3. Card visit hiện UUID thay vì tên

## Expected
Hiển thị **tên BN + tuổi + giới** (e.g., "Nguyễn Văn E2E Test, 41, Nam") thay vì UUID. Có thể format giống Reception Queue Board.

## Files involved (estimated)
- `clinic-cms-web/src/pages/doctor/DoctorQueuePage.tsx` (hoặc `MyQueuePage.tsx`)
- Hook fetch queue: cần JOIN với patient table để lấy name/age/gender (BE include trong API response, hoặc separate query)

## Hypothesis
1. **BE API thiếu** — `/api/v1/visits?status=waiting&doctor_id={id}` không include patient.full_name → FE chỉ có patient_id UUID
2. **FE chưa map** — BE trả patient nested object nhưng FE quên render `.full_name`, fallback sang `.id`

Verify bằng inspect API response của `My Queue` query.

## Impact
- Medium UX — doctor phải click từng card để biết BN nào
- Không block create/save flow
- Affect daily workflow nghiêm trọng cho clinic real

## Related
- Reception Queue Board hiển thị visit number nhưng cũng KHÔNG hiển thị tên BN (chỉ visit#) → có thể cùng root cause cross-page
- TASK-040 QueueBoard 5-col + DoctorMyQueue port — có thể missing patient join
