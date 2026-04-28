# FE Consumed HR APIs — TASK-022

Source of truth: `clinic-cms/app/modules/hr/api/routes.py` (TASK-014)

## Base URL

`/api/v1` — all endpoints relative to `VITE_API_URL` env var (default `http://localhost:8000`).

All endpoints require `Authorization: Bearer <access_token>` header (handled by `apiClient.ts`).

---

## Shift Templates

| Method | Endpoint | Permission | Description |
|--------|----------|-----------|-------------|
| GET | `/shift-templates` | `shift.manage` | List all shift templates |
| POST | `/shift-templates` | `shift.manage` | Create shift template |
| PATCH | `/shift-templates/{id}` | `shift.manage` | Update shift template |
| DELETE | `/shift-templates/{id}` | `shift.manage` | Delete shift template |

### ShiftTemplateResponse

```typescript
{
  id: string (UUID)
  clinic_id: string
  name: string
  start_time: string // "HH:MM:SS"
  end_time: string
  is_active: boolean
  created_at: string
  updated_at: string
}
```

---

## Shifts

| Method | Endpoint | Permission | Description |
|--------|----------|-----------|-------------|
| GET | `/shifts?from=&to=&user_id=` | `shift.manage` | List shifts in date range |
| POST | `/shifts` | `shift.manage` | Create shift |
| PATCH | `/shifts/{id}` | `shift.manage` | Update shift (used for drag-drop reschedule) |
| DELETE | `/shifts/{id}` | `shift.manage` | Delete shift |

### ShiftResponse

```typescript
{
  id: string
  user_id: string
  shift_template_id: string | null
  shift_date: string // "YYYY-MM-DD"
  start_time: string
  end_time: string
  role_in_shift: string | null
  status: "scheduled" | "cancelled" | "on_leave" | "completed"
  cancel_reason: string | null
  notes: string | null
}
```

---

## Recurring Schedules

| Method | Endpoint | Permission | Description |
|--------|----------|-----------|-------------|
| GET | `/recurring-schedules` | `shift.manage` | List recurring schedules |
| POST | `/recurring-schedules` | `shift.manage` | Create recurring schedule |
| PATCH | `/recurring-schedules/{id}` | `shift.manage` | Update |
| DELETE | `/recurring-schedules/{id}` | `shift.manage` | Delete |
| POST | `/recurring-schedules/{id}/generate-shifts?until=YYYY-MM-DD` | `shift.manage` | Trigger background shift generation |

Response from generate: `{ "created": number }`

### days_of_week encoding

ISO integers: 1=Monday, 7=Sunday. Stored as JSON array, e.g. `[1, 3, 5]` = Mon/Wed/Fri.

---

## Leave Requests

| Method | Endpoint | Permission | Description |
|--------|----------|-----------|-------------|
| GET | `/leave-requests?status=&user_id=` | `leave.approve` | List (manager view) |
| POST | `/leave-requests` | (any authenticated) | Submit leave request |
| POST | `/leave-requests/{id}/approve` | `leave.approve` | Approve |
| POST | `/leave-requests/{id}/reject` | `leave.approve` | Reject with reason |

### LeaveRequestResponse

```typescript
{
  id: string
  user_id: string
  leave_type: "sick" | "personal" | "vacation" | "other"
  start_date: string
  end_date: string
  reason: string
  status: "pending" | "approved" | "rejected"
  approved_by: string | null
  approved_at: string | null
  rejection_reason: string | null
}
```

---

## Attendance

| Method | Endpoint | Permission | Description |
|--------|----------|-----------|-------------|
| POST | `/attendance/check-in` | `attendance.manage` | Check in |
| POST | `/attendance/check-out` | `attendance.manage` | Check out |
| GET | `/attendance/me?from=&to=` | (any authenticated) | My time logs |
| GET | `/attendance?user_id=&from=&to=` | `attendance.manage` | All users (admin) |
| GET | `/attendance/export?from=&to=&format=xlsx` | `attendance.manage` | Export XLSX (blob response) |

### CheckInRequest

```typescript
{
  shift_id?: string        // optional shift to link
  check_in_method?: "manual" | "pin" | "qr" | "biometric"
  check_in_location?: string
  notes?: string
}
```

### TimeLogResponse

```typescript
{
  id: string
  shift_id: string | null
  check_in_at: string      // ISO datetime
  check_out_at: string | null
  check_in_method: string
  late_minutes: number | null
  early_leave_minutes: number | null
  total_hours: number | null
  ot_hours: number | null
}
```

**409 Conflict**: Returned by check-in if user already has an active (not checked-out) TimeLog for the shift.

---

## Timesheet

| Method | Endpoint | Permission | Description |
|--------|----------|-----------|-------------|
| GET | `/hr/timesheet?month=YYYY-MM` | `attendance.manage` | Aggregate report |

---

## Error Handling (FE)

All errors flow through `apiClient.ts`:
- 401 → auto-refresh once → if fails, logout + redirect `/login`
- 409 (check-in) → toast "Đã check-in" (AC8)
- 4xx/5xx → throw error data → caught in `useMutation.onError` → toast.error

## Notes

- CSV export format is not yet supported by BE (only xlsx). CSV radio button in FE is disabled with "soon" label.
- QR scan and biometric check-in are deferred to Phase 2.
