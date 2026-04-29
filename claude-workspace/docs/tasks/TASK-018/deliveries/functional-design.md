# TASK-018 Functional Design — Reception Module

**Status:** DONE  
**Date:** 2026-04-27  
**Branch:** feature/task-018-fe-reception

---

## Module Overview

Reception module provides UI for clinic front-desk staff:
- Patient registration, search, and management
- Guardian relationship management
- Patient record merging (admin)
- Walk-in visit creation
- Appointment calendar (STUB pending TASK-008 BE)
- Queue board with real-time auto-refresh

---

## Pages

### 1. Patient List (`/patients`)
- Debounced search (300ms) with auto-detection: phone/code/name
- Result table with patient_code, full_name, DOB/age, phone
- Quick "Khám ngay" button → opens WalkInModal
- "Đăng ký mới" → `/patients/new`

### 2. Patient Register (`/patients/new`)
- RHF + Zod validation
- Required: full_name, gender, dob/birth_year (one required), phone
- Optional: email, CCCD, address (province/district/ward), blood_type, allergies, chronic_conditions, occupation, referral_source, notes
- Duplicate detection warning from BE warnings[]

### 3. Patient Detail (`/patients/:id`)
- Tabbed: Info | Guardian | Visits (STUB) | Prescriptions (STUB) | Invoices (STUB) | Vitals (STUB) | Audit
- Inline edit with PATCH API
- STUB tabs show "pending BE integration" banner

### 4. Guardian Section (inside Patient Detail)
- List existing relations
- Add: search patient by name → select relation_type → optional is_primary_contact
- Remove with confirmation

### 5. Patient Merge (`/patients/merge`)
- Permission gated: `patient.merge`
- Two PatientPicker selectors (keep/drop)
- Side-by-side preview
- Reason field
- "Có thể undo trong 7 ngày" notice
- Undo button after successful merge (7-day window)

### 6. Walk-In Modal
- Search/select patient or navigate to create new
- Priority: 0 (Normal) | 5 (Priority) | 10 (Emergency)
- Chief complaint, is_returning checkbox
- Creates Visit via TASK-007 BE (real)
- Shows visit_number prominently after success
- Print ticket STUB (Tauri printer plugin pending)

### 7. Appointment Calendar (`/appointments`)
- **TASK-008 BE STUB** — "Beta" banner shown
- Week/Day view with mock slot data (randomized for UI)
- Slot colors: green (available), red (full/disabled)
- Click slot → AppointmentBookingModal (submit disabled, stub warning)

### 8. Queue Board (`/queue`)
- Auto-refresh every 10 seconds via TanStack Query refetchInterval
- Groups: WAITING | IN_PROGRESS | AWAITING_PAYMENT
- Sort: priority DESC → is_returning DESC → created_at ASC (BA §4.6)
- visit_number at 48px font (full-screen mode)
- Full-screen: Tauri setFullscreen + DOM fullscreen API fallback
- Audio chime: Web Audio API oscillator on new WAITING visit

---

## API Integration

| Endpoint | Status | Task |
|----------|--------|------|
| GET /patients | REAL | TASK-005 |
| GET /patients/search | REAL | TASK-005 |
| POST /patients | REAL | TASK-005 |
| PATCH /patients/:id | REAL | TASK-005 |
| GET /patients/:id | REAL | TASK-005 |
| GET /patients/:id/guardians | REAL | TASK-005 |
| POST /patients/:id/guardians | REAL | TASK-005 |
| DELETE /patients/guardians/:id | REAL | TASK-005 |
| POST /patients/merge | REAL | TASK-005 |
| POST /patients/merge/:id/undo | REAL | TASK-005 |
| POST /visits | REAL | TASK-007 |
| GET /visits/queue | REAL | TASK-007 |
| GET /appointments/slots | STUB | TASK-008 (not on demo) |
| GET /appointments | STUB | TASK-008 (not on demo) |
| POST /appointments | STUB | TASK-008 (not on demo) |

---

## Permissions

| Feature | Permission |
|---------|-----------|
| Patient search/list/view | `patient.read` (via API) |
| Patient create/edit | `patient.write` (via API) |
| Patient merge | `patient.merge` (RequirePermission gate) |
| Visit create (walk-in) | `visit.write` (via API) |
| Queue view | `visit.read` (via API) |
| Appointments | `appointment.read/write` (STUB) |

---

## i18n

- Namespace: `reception`
- Languages: `vi` (primary) + `en`
- 267 total keys, parity-tested in `src/tests/reception/i18n-reception.test.ts`
