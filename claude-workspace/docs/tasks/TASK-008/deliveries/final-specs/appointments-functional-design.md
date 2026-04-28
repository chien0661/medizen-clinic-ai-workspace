# Thiết Kế Chức Năng: Module Appointment (TASK-008)

**Phiên bản**: 1.0  
**Ngày**: 2026-04-29  
**Trạng thái**: DONE  

---

## 1. Tổng Quan

Module Appointment quản lý lịch hẹn khám bệnh với cơ chế slot capacity dựa trên số bác sĩ on-shift, state machine đầy đủ, và logic smart queue để quyết định ưu tiên walk-in vs appointment.

### 1.1 Phạm Vi

- Tạo/quản lý lịch hẹn với slot capacity enforcement
- State machine: scheduled → confirmed → checked_in → completed / cancelled / no_show
- Smart queue: tính toán xem walk-in có được phục vụ trước appointment không
- Auto no-show: cron job 5 phút tự động đánh dấu các appointment quá hạn
- Check-in: tự động tạo Visit khi bệnh nhân check-in

### 1.2 Các Bên Liên Quan

| Bên | Vai Trò |
|-----|---------|
| Lễ tân (Receptionist) | Tạo, xác nhận, check-in, huỷ appointment |
| Bác sĩ (Doctor) | Xem appointment, xác nhận |
| Admin | Toàn quyền quản lý |
| Bệnh nhân | Đặt lịch (qua lễ tân) |

---

## 2. State Machine

```
                 ┌──────────────┐
                 │  scheduled   │──────────────┐
                 └──────┬───────┘              │
                        │ confirm              │
                        ▼                      │ cancel
                 ┌──────────────┐              │
                 │  confirmed   │──────────────┤
                 └──────┬───────┘              │
                        │ check-in             │ no_show
                        ▼                      │
                 ┌──────────────┐         ┌────▼──────┐
                 │  checked_in  │         │  no_show  │ (terminal)
                 └──────┬───────┘         └───────────┘
                        │ (complete via Visit)    │
                        ▼                    ┌────▼──────┐
                 ┌──────────────┐            │ cancelled │ (terminal)
                 │  completed   │            └───────────┘
                 └──────────────┘ (terminal)
```

### 2.1 Transitions

| Từ | Tới | Trigger |
|----|-----|---------|
| scheduled | confirmed | POST /confirm |
| scheduled | cancelled | POST /cancel |
| scheduled | no_show | auto_no_show_job hoặc POST /no-show |
| confirmed | checked_in | POST /check-in (tạo Visit) |
| confirmed | cancelled | POST /cancel |
| confirmed | no_show | auto_no_show_job |
| checked_in | completed | Thông qua Visit COMPLETED |
| checked_in | cancelled | POST /cancel |

---

## 3. Slot Capacity

### 3.1 Công Thức

```
capacity = số bác sĩ on-shift trong interval [slot_start, slot_end)
available = capacity - count(appointments với status IN (scheduled, confirmed, checked_in) trong slot)
```

**Hiện tại**: Stub với capacity = 2 bác sĩ/slot  
**TODO(TASK-014)**: Thay bằng query thực tế từ shift/leave tables

### 3.2 Giờ Hoạt Động Mặc Định

- Bắt đầu: 09:00 UTC
- Kết thúc: 17:00 UTC
- Slot mặc định: 30 phút

**TODO**: Đọc từ clinic_settings khi TASK-006 được merge.

### 3.3 Kiểm Tra Capacity (AC1 & AC2)

```
GET /api/v1/appointments/slots?date=2026-05-01&duration=30
→ [
    {"start_time": "2026-05-01T09:00:00+00:00", "capacity": 2, "booked": 0, "available": 2},
    {"start_time": "2026-05-01T09:30:00+00:00", "capacity": 2, "booked": 0, "available": 2},
    ...
  ]
```

Khi slot đầy (booked = capacity = 2), POST /appointments → 409 Conflict.

---

## 4. Smart Queue (AC3)

### 4.1 Logic

Walk-in được phục vụ trước appointment **chỉ khi**:

```
estimated_end_walkin <= next_appointment_at - buffer_minutes
```

**Ví dụ (AC3)**:
- Walk-in lúc: 8:45, ước tính 25 phút
- Appointment tiếp theo: 9:00
- Buffer: 15 phút
- estimated_end = 8:45 + 25 = 9:10
- appointment_buffer_start = 9:00 - 15 = 8:45
- 9:10 <= 8:45 → **FALSE** → Appointment được ưu tiên ✓

### 4.2 API

```python
should_walk_in_jump_appointment(
    walk_in_estimated_minutes=25,
    next_appointment_at=datetime(2026, 1, 1, 9, 0, tzinfo=UTC),
    now=datetime(2026, 1, 1, 8, 45, tzinfo=UTC),
    buffer_minutes=15
) → False  # Appointment có ưu tiên
```

---

## 5. Auto No-Show Job (AC4)

### 5.1 Cấu Hình

- Tần suất: 5 phút (Arq cron: `minute={0,5,10,...,55}`)
- Ngưỡng: `APPOINTMENT_NO_SHOW_MINUTES` (mặc định: 15 phút)
- Logic: `scheduled_at < now() - interval 'N minutes'`

### 5.2 Hành Vi

1. Tìm tất cả clinic có appointment overdue
2. Với mỗi clinic, set RLS context
3. Cập nhật `status = 'no_show'`, `no_show_at = now()`
4. Dùng `SELECT FOR UPDATE SKIP LOCKED` để tránh conflict

---

## 6. Check-In & Tạo Visit Tự Động (AC5)

### 6.1 Quy Trình

```
POST /appointments/{id}/check-in
→ 1. Assert status = 'confirmed' (hoặc raise 409)
→ 2. Tạo Visit:
      clinic_id = appointment.clinic_id
      patient_id = appointment.patient_id
      assigned_doctor_id = appointment.assigned_doctor_id
      appointment_id = appointment.id
      status = 'WAITING'
      visit_number = fn_next_visit_number(clinic_id, today)
→ 3. Cập nhật appointment:
      status = 'checked_in'
      checked_in_at = now()
      visit_id = visit.id
→ 4. Return {appointment, visit_id}
```

### 6.2 FK Circular

`appointment.visit_id → visit.id` và `visit.appointment_id → appointment.id` tạo ra circular FK. Khi cần xóa, phải NULL out `appointment.visit_id` trước.

---

## 7. Phân Quyền

| Permission | Mô Tả | Roles Mặc Định |
|------------|-------|---------------|
| appointment.read | Xem lịch hẹn và slots | admin, doctor, receptionist |
| appointment.write | Tạo và cập nhật lịch hẹn | admin, doctor, receptionist |
| appointment.cancel | Huỷ lịch hẹn | admin, receptionist |

---

## 8. Indexes Database

| Index | Columns | Where Clause | Mục Đích |
|-------|---------|-------------|---------|
| ix_appointment_clinic_time | (clinic_id, scheduled_at) | is_deleted=false AND status IN (...) | Slot query |
| ix_appointment_patient_id | patient_id | - | Patient history |
| ix_appointment_assigned_doctor | (clinic_id, assigned_doctor_id) | assigned_doctor_id IS NOT NULL | Doctor schedule |

---

## 9. Deferrals

| Hạng Mục | Lý Do | Task Phụ Thuộc |
|----------|-------|----------------|
| Real shift-based capacity | HR module chưa có shift query theo interval | TASK-014 |
| Clinic operating hours từ settings | clinic_settings chưa merge | TASK-006 |
| Concurrent booking (true multi-process test) | Test env single event loop | N/A |
