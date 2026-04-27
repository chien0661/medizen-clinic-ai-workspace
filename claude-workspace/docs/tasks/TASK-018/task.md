---
id: TASK-018
type: feature
title: FE — Reception (Patient Register/Search/Merge + Walk-in + Appointment Booking + Queue Board)
status: TODO
priority: High
assigned: Unassigned
created: 2026-04-26
updated: 2026-04-26
branch: ""
tags: [frontend, reception, patient, queue, sprint-15]
affected-repos: [clinic-cms]
refs:
  detail_design: "../../../../docs/clinic_management_system_design.md#6-module-patients"
  other:
    - "../../../../docs/clinic_management_business_analysis.md#4-module-patient--reception"
    - "../../../../docs/clinic_management_business_analysis.md#5-module-appointment"
---

# TASK-018: FE — Reception Module (Patient + Walk-in + Appointment + Queue)

## Description

UI cho lễ tân: tra cứu/tạo bệnh nhân (search SĐT/tên/mã), guardian relationship, merge hồ sơ trùng (admin), walk-in check-in tạo Visit, đặt lịch hẹn với calendar slot capacity, queue board real-time hiển thị visit đang chờ.

## Requirements

- [ ] **Patient list & search** (`/patients`)
  - Search bar: SĐT (10 digits, debounce 300ms), tên (fuzzy unaccent), patient_code (BN0001)
  - Result table: code, full_name, dob/age, phone, last_visit_at
  - Quick action: "Khám ngay" → walk-in flow
- [ ] **Patient detail** (`/patients/:id`)
  - Info section + edit inline
  - Guardian section: list relations, add/remove
  - History tab: visits, prescriptions, invoices, vitals timeline (chart)
  - Audit log tab (admin)
- [ ] **Patient register form** (modal hoặc `/patients/new`)
  - Required: full_name, dob (or birth_year), gender, phone
  - Optional: CCCD, address (province/district/ward dropdown), blood_type, allergies, chronic_diseases, email, occupation, referral_source
  - Duplicate detection cảnh báo nếu phone+name trùng (không block)
- [ ] **Patient merge** (admin only, perm `patient.merge`)
  - Select 2 patients → preview side-by-side → choose keep + drop → confirm
  - Show "Có thể undo trong 7 ngày"
  - Undo button trong audit history
- [ ] **Walk-in check-in flow**
  - Search/select patient (or create new) → optional pre-assign doctor → set priority (0/5/10) → click "Tạo visit"
  - Auto generate visit_number, status WAITING
  - Print "phiếu xếp số" qua POS printer (hardware từ TASK-016)
- [ ] **Appointment booking** (`/appointments`)
  - Calendar view (week/day) hiển thị slot capacity (3/5 = booked/total)
  - Click slot → mở form đặt lịch (chọn patient, optional doctor, ghi chú)
  - Slot full → disabled + tooltip "Hết slot"
  - Drag & drop reschedule (optional)
- [ ] **Queue board** (`/queue`, full-screen mode option)
  - Auto-refresh 10s
  - Group: WAITING, IN_PROGRESS (theo doctor), AWAITING_PAYMENT
  - Sort theo priority + is_returning + check_in_at (theo §4.6 BA)
  - Hiển thị visit_number lớn (font size 48px) cho TV display
  - Audio chime khi có visit mới WAITING
- [ ] Permissions: `patient.read/write/merge`, `visit.write`

## Acceptance Criteria

- [ ] Search SĐT 10 chữ số trả < 200ms (network + render)
- [ ] Search "nguyen vn an" match "Nguyễn Văn An" (fuzzy unaccent)
- [ ] Tạo patient mới → toast success + auto-fill ở walk-in form nếu trong flow
- [ ] Walk-in tạo visit → queue board hiện ngay record mới (không cần F5)
- [ ] Calendar slot 9:00 với 2 BS đã book 2 → slot disabled
- [ ] Merge 2 patient → history transfer đúng, drop record có badge "Đã merge vào BNxxx"
- [ ] Queue board hiển thị tốt trên màn hình 1920×1080 + 4K

## Progress Checklist

- [ ] Implementation
- [ ] Code Review
- [ ] Testing
- [ ] Documentation

## Related Files

- **Code**: `clinic-cms/desktop/src/modules/reception/`

## Timestamps

- **Created**: 2026-04-26

## Notes

Queue board nên cho phép full-screen (kiosk mode) vì thường mở trên TV phòng chờ. Tauri có API `setFullscreen`.

## Blockers

- TASK-017 (FE foundation), TASK-005 (Patient API), TASK-007 (Visit API), TASK-008 (Appointment API)
