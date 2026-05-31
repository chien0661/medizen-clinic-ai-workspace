---
id: BUG-009
title: Patient detail page — labels chồng lên values (CSS layout overlap)
severity: Medium
status: OPEN
discovered_in: TASK-049 Phase 2 — sau khi Register New patient redirect đến detail
url: http://localhost:1420/#/patients/{uuid}
---

# BUG-009: Patient detail page — labels overlap values

## Symptom
Sau khi tạo BN mới (Register New) FE auto-redirect đến `/#/patients/{uuid}`. Trang detail render với:
- Header card: avatar + tên + tuổi + giới + BN code — OK
- Card "thông tin liên hệ" (phone, birth year, address) — OK ở left column
- Right column: labels (`name`, `phone number`, `Email`, `Blood type`, `Allergies`, `Chronic conditions`) **chồng** lên values

Specific overlap (từ screenshot `06-patient-detail-after-create.png`):
- `name` chồng `Nguyễn Văn E2E Test`
- `number` chồng `0987654321`
- `Blood type` chồng `Email`
- `Chronic conditions` chồng `Allergies`

→ Render layout broken: 2 column nội dung trong 1 column width hoặc absolute positioning sai.

## Repro
1. Login receptionist → Patients
2. Click "Register New", fill required fields, Submit
3. URL → `/#/patients/{uuid}`, observe right-card layout

## Hypothesis
- Grid/flex template misaligned (column `auto auto` thay vì 2 separate columns)
- OR: i18n string lengths Vietnamese gây overflow chưa wrap
- OR: missing CSS gap / column gap / padding
- OR: 2 `<dl>` lists rendered chồng nhau qua absolute positioning

## Files involved (estimated)
- `clinic-cms-web/src/pages/patients/PatientDetailPage.tsx` (or similar)
- Component card "Thông tin chi tiết" / "Optional information"

## Suggested fix
- Inspect DOM in DevTools → confirm grid template
- Add `display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 1rem` cho 2-column layout
- Or wrap với `<dl class="space-y-2">` + each row `<div class="flex justify-between gap-4">`

## Impact
- Medium — Patient detail không đọc được clearly
- Block visual review nhưng không block API/business logic
- BN mới detail là entry point sau Register, ảnh hưởng UX nhất

## Related
- TASK-039b component restyle — có thể có residual layout từ MediZen port
- TASK-040 PatientDetailPage 8-tab refactor — có thể là regression
