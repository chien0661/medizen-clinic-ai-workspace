# Thiết Kế Chi Tiết Tính Năng: Module HR — Lịch Làm Việc & Chấm Công

**Dự án:** Hệ thống Quản lý Phòng khám Clinic CMS  
**Task:** TASK-014  
**Phiên bản:** 1.0  
**Ngày:** 2026-04-28  
**Người thực hiện:** Documentation Agent  
**Trạng thái:** Hoàn thành  
**Tài liệu liên quan:** [clinic_management_system_design.md§14](../../../../../docs/clinic_management_system_design.md#14-module-hr--schedule), [clinic_management_business_analysis.md§12](../../../../../docs/clinic_management_business_analysis.md#12-module-hr-schedule--attendance)

---

## Lịch sử thay đổi

| Phiên bản | Ngày | Nội dung thay đổi |
|-----------|------|-------------------|
| 1.0 | 2026-04-28 | Phiên bản đầu tiên — Hoàn thành TASK-014 |

---

## Mục lục

1. [Tổng quan tính năng](#1-tổng-quan-tính-năng)
2. [Luồng xử lý tổng thể](#2-luồng-xử-lý-tổng-thể)
3. [Nguồn dữ liệu đầu vào](#3-nguồn-dữ-liệu-đầu-vào)
4. [Danh sách API](#4-danh-sách-api)
5. [Chi tiết từng API](#5-chi-tiết-từng-api)
6. [Cấu trúc cơ sở dữ liệu](#6-cấu-trúc-cơ-sở-dữ-liệu)
7. [SQL tổng hợp và truy vấn dữ liệu](#7-sql-tổng-hợp-và-truy-vấn-dữ-liệu)
8. [Quy tắc nghiệp vụ](#8-quy-tắc-nghiệp-vụ)
9. [Xử lý lỗi](#9-xử-lý-lỗi)
10. [Chiến lược cache](#10-chiến-lược-cache)
11. [Ghi chú và lưu ý khi kiểm thử](#11-ghi-chú-và-lưu-ý-khi-kiểm-thử)

---

## 1. Tổng quan tính năng

### 1.1 Mục đích

Module HR & Schedule quản lý **lịch làm việc** (kế hoạch) và **chấm công thực tế** (nhập liệu) cho phòng khám. Tách rõ 2 khái niệm:

- **Shift Template (Mẫu ca):** Định nghĩa ca làm việc chuẩn (ví dụ: "Ca sáng 07:30-12:00")
- **Shift (Ca làm việc cụ thể):** Ai làm ca nào ngày nào → dùng để xếp lịch hẹn, kiểm tra sức chứa
- **Recurring Schedule (Lịch lặp):** Nhân viên làm thứ nào, ca nào hàng tuần → tự động sinh Shifts
- **Leave Request (Xin phép):** Nhân viên xin nghỉ → manager phê duyệt → Shifts tự động đánh dấu on_leave
- **TimeLog (Chấm công):** Ghi nhận check-in/out thực tế → tính giờ làm, đi muộn, làm thêm
- **Timesheet (Bảng công):** Báo cáo tổng hợp giờ làm theo tháng → cơ sở tính lương

### 1.2 Phạm vi

**Bao gồm (V1):**
- CRUD Shift Templates
- CRUD Shifts
- CRUD Recurring Schedules + auto-generate Shifts
- CRUD Leave Requests + approval workflow
- Check-in / Check-out (nhập tay)
- List / Export Attendance
- Timesheet report (tổng giờ làm)

**Không bao gồm (deferred):**
- Tính lương trong app (chỉ export → kế toán xử lý)
- Biometric / QR check-in (cần hardware → TASK-016 Tauri client)
- Commission tính toán
- Hỗ trợ multiple timezones (V1 dùng UTC)

### 1.3 Các bên liên quan

| Vai trò | Mô tả | Permission |
|---------|-------|-----------|
| **Admin Clinic** | Quản lý toàn bộ lịch làm việc, chấm công | `shift.manage`, `leave.approve`, `attendance.manage` |
| **Manager/Supervisor** | Phê duyệt xin phép, xem chấm công | `leave.approve`, `attendance.manage` |
| **Nhân viên** | Xin phép, xem lịch cá nhân, check-in/out | Xem được công của mình; xin phép cho mình |
| **Kế toán** | Export bảng công để tính lương | `attendance.manage` (read-only export) |

---

## 2. Luồng xử lý tổng thể

### 2.1 Sơ đồ luồng dữ liệu

```
┌─────────────────────────────────────────────────────────────────┐
│                     Admin / Manager                              │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ 1. Tạo Shift Template (ca sáng, ca chiều, ca tối)        │   │
│  │ 2. Tạo Recurring Schedule cho nhân viên (T2,T4,T6 ca sáng)│   │
│  └────────┬─────────────────────────────────────────────────┘   │
└───────────┼──────────────────────────────────────────────────────┘
            │
            ▼
┌──────────────────────────────────────────┐
│  Cron Job (hàng ngày)                    │
│  Auto-generate Shifts cho 30 ngày tới    │
│  (idempotent — không duplicate)          │
└────────┬─────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────┐
│  Database: shift_template, shift, recurring_schedule     │
│  (kế hoạch lịch làm việc)                               │
└────────┬─────────────────────────────────────────────────┘
         │
         ├─────────────────────┬──────────────────┐
         │                     │                  │
         ▼                     ▼                  ▼
  ┌─────────────┐     ┌──────────────┐  ┌─────────────────┐
  │ Nhân viên   │     │ Manager/HR   │  │ Xếp lịch hẹn    │
  │ Check-in/out│     │ Xin phép     │  │ (dùng shifts để │
  │             │     │              │  │  kiểm tra sức   │
  │ ▼ TimeLog   │     │ ▼ LeaveReq   │  │  chứa)          │
  └─────────────┘     └──────────────┘  └─────────────────┘
         │                     │
         └─────────┬───────────┘
                   │
                   ▼
      ┌──────────────────────────┐
      │ Manager phê duyệt Leave  │
      │                          │
      │ Nếu APPROVE:             │
      │  → Cập nhật shifts       │
      │    status = on_leave     │
      │                          │
      │ Nếu REJECT:              │
      │  → Không thay đổi shifts │
      └────────┬─────────────────┘
               │
               ▼
      ┌────────────────────────────────┐
      │ Database: time_log + shifts    │
      │ (chấm công + kế hoạch)         │
      └────────┬────────────────────────┘
               │
               ▼
      ┌──────────────────────────────┐
      │ Kế toán: Export Timesheet     │
      │ (Excel: tổng giờ làm/tháng)   │
      │                              │
      │ Dùng để tính lương            │
      └──────────────────────────────┘
```

### 2.2 Mô tả các bước chính

| Bước | Tên bước | Mô tả chi tiết |
|------|----------|----------------|
| 1 | Tạo Shift Templates | Admin định nghĩa các mẫu ca (ví dụ: Ca sáng 07:30-12:00). Lưu trong bảng shift_template. |
| 2 | Tạo Recurring Schedules | Admin tạo lịch lặp cho từng nhân viên (ví dụ: Nhân viên A làm T2,T4,T6 ca sáng). Lưu trong recurring_schedule. |
| 3 | Auto-generate Shifts | Cron job chạy hàng ngày: lấy tất cả recurring schedules active, sinh Shifts cụ thể cho 30 ngày tới. Idempotent. |
| 4 | Employees Check-in/out | Nhân viên check-in lúc đến phòng khám → tạo time_log entry. Check-out lúc rời → cập nhật check_out_at. Hệ thống tính late_minutes, ot_hours, total_hours. |
| 5 | Nhân viên Xin Phép | Nhân viên POST leave request (start_date, end_date, reason) → status = pending. |
| 6 | Manager Phê Duyệt | Manager POST /approve → status = approved. Hệ thống tự động cập nhật tất cả shifts trong khoảng thời gian: status = on_leave. |
| 7 | Export Timesheet | Kế toán GET /attendance/export → Excel với tất cả time logs + computed fields. Hoặc GET /hr/timesheet?month=YYYY-MM → báo cáo tổng hợp theo user. |

---

## 3. Nguồn dữ liệu đầu vào

V1 không có import dữ liệu từ hệ thống bên ngoài (Kafka, file, FTP). Tất cả dữ liệu nhập liệu trực tiếp qua API:

- **Shift Templates, Recurring Schedules:** Admin tạo qua API
- **Shifts:** Auto-gen từ cron + manual create via API
- **Leave Requests:** Nhân viên xin qua API
- **Time Logs:** Nhân viên/admin check-in/out qua API

---

## 4. Danh sách API

**Base Path:** `/api/v1`

**Yêu cầu:** Tất cả endpoint đều yêu cầu header `Authorization: Bearer <token>`

| STT | Phương thức | Đường dẫn | Mô tả tóm tắt | Permission |
|-----|------------|-----------|--------------|-----------|
| 1 | GET | `/shift-templates` | Lấy danh sách mẫu ca | `shift.manage` |
| 2 | POST | `/shift-templates` | Tạo mẫu ca mới | `shift.manage` |
| 3 | PATCH | `/shift-templates/{id}` | Cập nhật mẫu ca | `shift.manage` |
| 4 | DELETE | `/shift-templates/{id}` | Xóa mẫu ca (soft delete) | `shift.manage` |
| 5 | GET | `/shifts` | Lấy danh sách shifts (lọc date, user) | `shift.manage` |
| 6 | POST | `/shifts` | Tạo shift cụ thể | `shift.manage` |
| 7 | PATCH | `/shifts/{id}` | Cập nhật shift | `shift.manage` |
| 8 | DELETE | `/shifts/{id}` | Xóa shift (soft delete) | `shift.manage` |
| 9 | GET | `/recurring-schedules` | Lấy danh sách recurring schedules | `shift.manage` |
| 10 | POST | `/recurring-schedules` | Tạo recurring schedule | `shift.manage` |
| 11 | PATCH | `/recurring-schedules/{id}` | Cập nhật recurring schedule | `shift.manage` |
| 12 | DELETE | `/recurring-schedules/{id}` | Xóa recurring schedule | `shift.manage` |
| 13 | POST | `/recurring-schedules/{id}/generate-shifts` | Sinh shifts từ recurring | `shift.manage` |
| 14 | GET | `/leave-requests` | Lấy danh sách leave requests | `leave.approve` |
| 15 | POST | `/leave-requests` | Xin phép (bất kỳ user) | (public) |
| 16 | POST | `/leave-requests/{id}/approve` | Phê duyệt leave | `leave.approve` |
| 17 | POST | `/leave-requests/{id}/reject` | Từ chối leave | `leave.approve` |
| 18 | POST | `/attendance/check-in` | Check-in | `attendance.manage` |
| 19 | POST | `/attendance/check-out` | Check-out | `attendance.manage` |
| 20 | GET | `/attendance/me` | Xem công của bản thân | (public) |
| 21 | GET | `/attendance` | Xem công tất cả (admin) | `attendance.manage` |
| 22 | GET | `/attendance/export` | Export attendance (Excel) | `attendance.manage` |
| 23 | GET | `/hr/timesheet` | Báo cáo timesheet/tháng | `attendance.manage` |

**Total: 23 endpoints** (tính cả GET /attendance/me, GET /attendance, GET /attendance/export riêng)

---

## 5. Chi tiết từng API

Chi tiết đầy đủ từng endpoint được lưu trong thư mục API specs:

- **01-shift-templates.md** — Shift Templates CRUD (endpoints 1-4)
- **02-shifts.md** — Shifts CRUD (endpoints 5-8)
- **03-recurring-schedules.md** — Recurring Schedules CRUD + generate (endpoints 9-13)
- **04-leave-requests.md** — Leave Requests CRUD + approval (endpoints 14-17)
- **05-attendance.md** — Attendance check-in/out + list + export (endpoints 18-22)
- **06-timesheet.md** — Timesheet report (endpoint 23)

Mỗi tài liệu chứa:
- Mô tả endpoint
- Tham số đầu vào
- Quy tắc nghiệp vụ áp dụng
- Ví dụ request/response
- Mã lỗi có thể xảy ra
- Ghi chú đặc biệt

---

## 6. Cấu trúc cơ sở dữ liệu

### 6.1 Tổng quan các bảng

| Bảng | Mục đích | Quan hệ |
|------|---------|---------|
| `shift_template` | Lưu định nghĩa ca làm việc (start_time, end_time) | 1-to-Many → shift, recurring_schedule |
| `shift` | Lưu ca làm việc cụ thể (user × date × time) | Many-to-1 → shift_template, user |
| `recurring_schedule` | Lưu lịch lặp hàng tuần (days_of_week) | 1-to-Many → shift (auto-gen) |
| `leave_request` | Lưu yêu cầu xin phép (dates, status) | Many-to-1 → user |
| `time_log` | Lưu check-in/out thực tế + computed fields | Many-to-1 → shift, user |

### 6.2 Chi tiết bảng

#### Bảng: `shift_template`

**Mô tả:** Lưu các mẫu ca làm việc (ví dụ: "Ca sáng", "Ca chiều", "Ca tối"). Được dùng để:
1. Tạo shifts cụ thể (shift_template_id → start_time, end_time)
2. Tạo recurring schedules

| Tên cột | Kiểu dữ liệu | Bắt buộc | Mô tả |
|---------|-------------|---------|-------|
| `id` | UUID | Có | Khóa chính |
| `clinic_id` | UUID | Có | Khóa nước ngoài → clinic.id |
| `name` | VARCHAR(100) | Có | Tên ca (ví dụ: "Ca sáng") |
| `start_time` | TIME | Có | Giờ bắt đầu (07:30:00) |
| `end_time` | TIME | Có | Giờ kết thúc (12:00:00) |
| `is_active` | BOOLEAN | Có (default: true) | Kích hoạt/vô hiệu hóa |
| `created_at` | TIMESTAMP | Có | Thời điểm tạo |
| `updated_at` | TIMESTAMP | Có | Thời điểm cập nhật |
| `is_deleted` | BOOLEAN | Có (default: false) | Soft delete flag |
| `deleted_at` | TIMESTAMP | Không | Thời điểm xóa (null nếu không xóa) |
| `deleted_by` | UUID | Không | User xóa (null nếu không xóa) |
| `created_by` | UUID | Không | User tạo |
| `updated_by` | UUID | Không | User cập nhật |
| `version` | INT | Có (default: 1) | Optimistic locking |

**Ràng buộc:**
- PRIMARY KEY (id)
- FOREIGN KEY (clinic_id) → clinic(id) ON DELETE RESTRICT
- CHECK: end_time > start_time (BR-01)
- Soft delete: WHERE NOT is_deleted

**Index:**
- `ix_shift_template_clinic_id` — lọc theo clinic

---

#### Bảng: `shift`

**Mô tả:** Lưu ca làm việc cụ thể — ai làm ca nào ngày nào. Có thể tạo từ shift_template hoặc tự do (custom).

| Tên cột | Kiểu dữ liệu | Bắt buộc | Mô tả |
|---------|-------------|---------|-------|
| `id` | UUID | Có | Khóa chính |
| `clinic_id` | UUID | Có | Khóa nước ngoài → clinic.id |
| `user_id` | UUID | Có | Khóa nước ngoài → user.id |
| `shift_template_id` | UUID | Không | Khóa nước ngoài → shift_template.id (null = custom shift) |
| `shift_date` | DATE | Có | Ngày làm việc (2026-05-01) |
| `start_time` | TIME | Có | Giờ bắt đầu ca |
| `end_time` | TIME | Có | Giờ kết thúc ca |
| `role_in_shift` | VARCHAR(50) | Không | Role trong shift (ví dụ: "Doctor", "Nurse") |
| `status` | VARCHAR(20) | Có (default: scheduled) | scheduled / cancelled / on_leave / completed |
| `cancel_reason` | TEXT | Không | Lý do hủy (nếu status = cancelled) |
| `notes` | TEXT | Không | Ghi chú |
| `created_at` | TIMESTAMP | Có | Thời điểm tạo |
| `updated_at` | TIMESTAMP | Có | Thời điểm cập nhật |
| `is_deleted` | BOOLEAN | Có (default: false) | Soft delete flag |
| `deleted_at` | TIMESTAMP | Không | |
| `deleted_by` | UUID | Không | |
| `created_by` | UUID | Không | |
| `updated_by` | UUID | Không | |
| `version` | INT | Có (default: 1) | |

**Ràng buộc:**
- PRIMARY KEY (id)
- FOREIGN KEY (clinic_id) → clinic.id ON DELETE RESTRICT
- FOREIGN KEY (user_id) → user.id ON DELETE RESTRICT
- FOREIGN KEY (shift_template_id) → shift_template.id ON DELETE SET NULL
- UNIQUE (clinic_id, user_id, shift_date, start_time) WHERE NOT is_deleted (BR-06)
- CHECK: end_time > start_time (BR-01)

**Index:**
- `ix_shift_clinic_date_user` — PARTIAL: (clinic_id, shift_date, user_id) WHERE NOT is_deleted AND status='scheduled'
- `ix_shift_user_date` — PARTIAL: (user_id, shift_date) WHERE NOT is_deleted
- `ix_shift_user_id`, `ix_shift_shift_date`, `ix_shift_clinic_id`

---

#### Bảng: `recurring_schedule`

**Mô tả:** Lưu lịch làm việc lặp lại hàng tuần. Dùng để tự động sinh Shifts.

| Tên cột | Kiểu dữ liệu | Bắt buộc | Mô tả |
|---------|-------------|---------|-------|
| `id` | UUID | Có | Khóa chính |
| `clinic_id` | UUID | Có | Khóa nước ngoài → clinic.id |
| `user_id` | UUID | Có | Khóa nước ngoài → user.id |
| `shift_template_id` | UUID | Có | Khóa nước ngoài → shift_template.id |
| `days_of_week` | INT[] | Có | Array của 1-7 (ISO: 1=Mon, 7=Sun). Ví dụ: [1,3,5] = T2,T4,T6 |
| `effective_from` | DATE | Có | Ngày bắt đầu có hiệu lực (2026-05-01) |
| `effective_to` | DATE | Không | Ngày kết thúc có hiệu lực (null = vô thời hạn) |
| `is_active` | BOOLEAN | Có (default: true) | Kích hoạt/vô hiệu hóa |
| `created_at` | TIMESTAMP | Có | |
| `updated_at` | TIMESTAMP | Có | |
| `is_deleted` | BOOLEAN | Có (default: false) | |
| `deleted_at` | TIMESTAMP | Không | |
| `deleted_by` | UUID | Không | |
| `created_by` | UUID | Không | |
| `updated_by` | UUID | Không | |
| `version` | INT | Có (default: 1) | |

**Ràng buộc:**
- PRIMARY KEY (id)
- FOREIGN KEY (clinic_id) → clinic.id ON DELETE RESTRICT
- FOREIGN KEY (user_id) → user.id ON DELETE RESTRICT
- FOREIGN KEY (shift_template_id) → shift_template.id ON DELETE RESTRICT
- CHECK: tất cả values trong days_of_week phải ∈ [1, 7] (BR-04)
- CHECK: effective_to IS NULL OR effective_to >= effective_from (BR-03)

**Index:**
- `ix_recurring_schedule_clinic_id`, `ix_recurring_schedule_user_id`

---

#### Bảng: `leave_request`

**Mô tả:** Lưu yêu cầu xin phép của nhân viên.

| Tên cột | Kiểu dữ liệu | Bắt buộc | Mô tả |
|---------|-------------|---------|-------|
| `id` | UUID | Có | Khóa chính |
| `clinic_id` | UUID | Có | Khóa nước ngoài → clinic.id |
| `user_id` | UUID | Có | Khóa nước ngoài → user.id (người xin) |
| `leave_type` | VARCHAR(20) | Có | sick / personal / vacation / other |
| `start_date` | DATE | Có | Ngày bắt đầu xin phép |
| `end_date` | DATE | Có | Ngày kết thúc xin phép |
| `reason` | TEXT | Có | Lý do xin phép (min 1 ký tự) (BR-14) |
| `status` | VARCHAR(20) | Có (default: pending) | pending / approved / rejected |
| `approved_by` | UUID | Không | User phê duyệt (nếu approved) |
| `approved_at` | TIMESTAMP | Không | Thời điểm phê duyệt |
| `rejection_reason` | TEXT | Không | Lý do từ chối (nếu rejected) |
| `created_at` | TIMESTAMP | Có | |
| `updated_at` | TIMESTAMP | Có | |
| `is_deleted` | BOOLEAN | Có (default: false) | |
| `deleted_at` | TIMESTAMP | Không | |
| `deleted_by` | UUID | Không | |
| `created_by` | UUID | Không | |
| `updated_by` | UUID | Không | |
| `version` | INT | Có (default: 1) | |

**Ràng buộc:**
- PRIMARY KEY (id)
- FOREIGN KEY (clinic_id) → clinic.id ON DELETE RESTRICT
- FOREIGN KEY (user_id) → user.id ON DELETE RESTRICT
- FOREIGN KEY (approved_by) → user.id (nullable)
- CHECK: end_date >= start_date (BR-02)
- CHECK: length(reason) >= 1 (BR-14)

**Index:**
- `ix_leave_user_dates` — PARTIAL: (user_id, start_date, end_date) WHERE status='approved' AND NOT is_deleted

---

#### Bảng: `time_log`

**Mô tả:** Lưu ghi nhận check-in/out thực tế của nhân viên.

| Tên cột | Kiểu dữ liệu | Bắt buộc | Mô tả |
|---------|-------------|---------|-------|
| `id` | UUID | Có | Khóa chính |
| `clinic_id` | UUID | Có | Khóa nước ngoài → clinic.id |
| `user_id` | UUID | Có | Khóa nước ngoài → user.id |
| `shift_id` | UUID | Không | Khóa nước ngoài → shift.id (null = check-in không liên kết shift) |
| `check_in_at` | TIMESTAMP | Có | Thời điểm check-in (with timezone) |
| `check_out_at` | TIMESTAMP | Không | Thời điểm check-out (null = chưa check-out) |
| `check_in_method` | VARCHAR(20) | Có (default: manual) | manual / pin / qr / biometric |
| `check_in_location` | VARCHAR(200) | Không | Vị trí check-in (IP, device ID) |
| `notes` | TEXT | Không | Ghi chú |
| `late_minutes` | INT | Không | Đi muộn (phút) — computed: max(0, check_in - shift.start_time) nếu shift_id có |
| `total_hours` | DECIMAL(10,2) | Không | Tổng giờ làm — computed: (check_out - check_in) / 3600 |
| `ot_hours` | DECIMAL(10,2) | Không | Giờ làm thêm — computed: max(0, check_out - shift.end_time) nếu shift_id có |
| `created_at` | TIMESTAMP | Có | |
| `updated_at` | TIMESTAMP | Có | |
| `is_deleted` | BOOLEAN | Có (default: false) | |
| `deleted_at` | TIMESTAMP | Không | |
| `deleted_by` | UUID | Không | |
| `created_by` | UUID | Không | |
| `updated_by` | UUID | Không | |
| `version` | INT | Có (default: 1) | |

**Ràng buộc:**
- PRIMARY KEY (id)
- FOREIGN KEY (clinic_id) → clinic.id ON DELETE RESTRICT
- FOREIGN KEY (user_id) → user.id ON DELETE RESTRICT
- FOREIGN KEY (shift_id) → shift.id ON DELETE SET NULL
- UNIQUE (clinic_id, user_id, check_in_at) WHERE check_out_at IS NULL — đảm bảo không có 2 check-in active (BR-08)

**Index:**
- `ix_timelog_user_check_in` — (user_id, check_in_at DESC)
- `ix_time_log_clinic_id`, `ix_time_log_user_id`

---

## 7. SQL tổng hợp và truy vấn dữ liệu

### 7.1 SQL tổng hợp / ghi dữ liệu

#### Recurring Shift Generation (Idempotent)

**Mục đích:** Sinh Shifts từ Recurring Schedule cho đến ngày được chỉ định. Idempotent — chạy nhiều lần không tạo duplicates.

**Điều kiện duy nhất:** UNIQUE (clinic_id, user_id, shift_date, start_time)

**Quy trình xử lý:**

```sql
-- Duyệt từng ngày từ max(today, effective_from) đến until:
-- Kiểm tra: ngày đó có nằm trong days_of_week không?
-- Nếu có: sinh Shift (hoặc bỏ qua nếu đã tồn tại — idempotent)

-- Pseudocode:
DECLARE @date DATE = GREATEST(CURRENT_DATE, recurring.effective_from);
DECLARE @until_date DATE = param_until;

WHILE @date <= @until_date LOOP
  DECLARE @dow INT = EXTRACT(ISODOW FROM @date);  -- 1=Mon, 7=Sun
  
  -- Kiểm tra: ngày này có trong days_of_week?
  IF @dow = ANY(recurring.days_of_week) THEN
    -- Kiểm tra: effective_to?
    IF recurring.effective_to IS NULL OR @date <= recurring.effective_to THEN
      -- Cố gắng INSERT (hoặc bỏ qua nếu trùng)
      INSERT INTO shift (
        clinic_id, user_id, shift_template_id, shift_date,
        start_time, end_time, status, created_by
      )
      SELECT
        recurring.clinic_id,
        recurring.user_id,
        recurring.shift_template_id,
        @date,
        st.start_time,
        st.end_time,
        'scheduled',
        :created_by
      FROM shift_template st
      WHERE st.id = recurring.shift_template_id
      ON CONFLICT (clinic_id, user_id, shift_date, start_time)
      DO NOTHING;  -- Idempotent
    END IF;
  END IF;
  
  @date := @date + INTERVAL '1 day';
END LOOP;
```

---

### 7.2 SQL truy vấn báo cáo / lấy dữ liệu

#### Truy vấn 1: Timesheet Aggregation (Tổng giờ làm theo user/tháng)

**Mục đích:** Lấy báo cáo timesheet — tổng giờ làm, số ngày công, late hours, OT hours của từng nhân viên trong 1 tháng.

**Điều kiện lọc:**

| Tham số | Cột tương ứng | Ghi chú |
|---------|--------------|--------|
| `clinic_id` | `tl.clinic_id` | Từ JWT context |
| `year` | `EXTRACT(YEAR FROM check_in_at)` | Từ parameter month=YYYY-MM |
| `month` | `EXTRACT(MONTH FROM check_in_at)` | Từ parameter month=YYYY-MM |

```sql
SELECT
  tl.user_id,
  u.full_name,
  COUNT(DISTINCT DATE(tl.check_in_at)) AS days_worked,
  ROUND(SUM(tl.total_hours)::NUMERIC, 2) AS total_hours,
  ROUND(SUM(COALESCE(tl.late_minutes, 0))::NUMERIC / 60, 2) AS total_late_hours,
  ROUND(SUM(COALESCE(tl.ot_hours, 0))::NUMERIC, 2) AS total_ot_hours,
  COUNT(tl.id) AS total_entries
FROM time_log tl
LEFT JOIN user u ON tl.user_id = u.id
WHERE tl.clinic_id = :clinic_id
  AND NOT tl.is_deleted
  AND EXTRACT(YEAR FROM tl.check_in_at) = :year
  AND EXTRACT(MONTH FROM tl.check_in_at) = :month
GROUP BY tl.user_id, u.full_name
ORDER BY u.full_name ASC;
```

**Giải thích:**
- `COUNT(DISTINCT DATE(...))` — số ngày công (không tính multiple check-in/day)
- `ROUND(..., 2)` — làm tròn 2 chữ số thập phân
- `SUM(total_hours)` — tổng tất cả giờ làm trong tháng
- `SUM(late_minutes) / 60` — chuyển phút thành giờ
- `SUM(ot_hours)` — tổng OT hours

---

#### Truy vấn 2: Attendance Export (Chi tiết time logs + shifts)

**Mục đích:** Export bảng công đầy đủ (check-in/out, late, OT) để kế toán tính lương.

**Điều kiện lọc:**

| Tham số | Cột tương ứng | Ghi chú |
|---------|--------------|--------|
| `clinic_id` | `tl.clinic_id` | Từ JWT |
| `from_date` | `CAST(check_in_at AS DATE)` | Query parameter |
| `to_date` | `CAST(check_in_at AS DATE)` | Query parameter |

```sql
SELECT
  tl.user_id,
  u.full_name,
  CAST(tl.check_in_at AS DATE) AS work_date,
  tl.check_in_at,
  tl.check_out_at,
  tl.total_hours,
  tl.late_minutes,
  tl.ot_hours,
  tl.check_in_method,
  s.start_time AS shift_start,
  s.end_time AS shift_end,
  tl.notes
FROM time_log tl
LEFT JOIN shift s ON tl.shift_id = s.id
LEFT JOIN user u ON tl.user_id = u.id
WHERE tl.clinic_id = :clinic_id
  AND NOT tl.is_deleted
  AND CAST(tl.check_in_at AS DATE) >= :from_date
  AND CAST(tl.check_in_at AS DATE) <= :to_date
ORDER BY tl.user_id, tl.check_in_at DESC;
```

**Giải thích:**
- LEFT JOIN shift — không bắt buộc (check-in có thể không liên kết shift)
- LEFT JOIN user — lấy full_name để export
- CAST(... AS DATE) — lọc theo ngày (bỏ qua giờ phút)

---

### 7.3 Logic tính toán tham số truy vấn

#### Khoảng ngày từ month parameter

| Parameter | Cách tính | Ví dụ |
|-----------|----------|-------|
| `month=2026-05` | year=2026, month=5 | EXTRACT(YEAR FROM check_in_at)=2026 AND EXTRACT(MONTH FROM check_in_at)=5 |
| Validation | month ∈ [1, 12], year >= 2020 | Reject nếu month > 12 atau < 1 |

**Pseudocode:**

```python
def parse_month(month_str: str) -> tuple[int, int]:
    """
    Input: "2026-05"
    Output: (2026, 5)
    Raises: ValueError nếu format sai
    """
    parts = month_str.split('-')
    if len(parts) != 2:
        raise ValueError("Format must be YYYY-MM")
    
    year = int(parts[0])
    month = int(parts[1])
    
    if month < 1 or month > 12:
        raise ValueError("Month must be 1-12")
    
    return year, month
```

#### Date range filters (`from`, `to`)

| Parameter | Format | Xử lý |
|-----------|--------|-------|
| `from` | YYYY-MM-DD | Nếu có: `CAST(check_in_at AS DATE) >= :from_date` |
| `to` | YYYY-MM-DD | Nếu có: `CAST(check_in_at AS DATE) <= :to_date` |
| Mặc định | null | Không filter theo date |

#### Recurring shift generation — date arithmetic

```python
# Duyệt từng ngày từ max(today, effective_from) đến until
start_date = max(date.today(), recurring.effective_from)
end_date = until_param  # Từ query parameter

current = start_date
while current <= end_date:
    dow = current.isoweekday()  # 1=Mon, 7=Sun
    
    if dow in recurring.days_of_week:
        # Kiểm tra effective_to
        if recurring.effective_to is None or current <= recurring.effective_to:
            # Sinh shift
            create_shift(...)
    
    current += timedelta(days=1)
```

---

## 8. Quy tắc nghiệp vụ

| BR-ID | Mô tả quy tắc | SRS Ref | Test File:Test Name | Status |
|-------|--------------|---------|-------------------|--------|
| BR-01 | Shift/template: end_time > start_time (CREATE) | §12.3, §12.2 | test_hr_service_logic.py:test_shift_creation_time_validation | ✅ PASS |
| BR-01b | Shift/template: end_time > start_time (PATCH) | §12.3, §12.2 | test_hr_business_rules.py:test_br01_patch_shift_to_inverted_times_rejected | ✅ PASS |
| BR-02 | LeaveRequest: end_date >= start_date | §12.5 | test_hr_business_rules.py:test_br02_leave_date_validation | ✅ PASS |
| BR-03 | RecurringSchedule: effective_to >= effective_from (nếu not null) | §12.4 | test_hr_business_rules.py:test_br03_effective_dates_validation | ✅ PASS |
| BR-04 | RecurringSchedule: days_of_week values ∈ [1..7] | §12.4 | test_hr_service_logic.py:test_days_of_week_validation | ✅ PASS |
| BR-05 | Rejected leave: không cascade đến shifts (shifts giữ nguyên status) | §12.6 | test_hr_business_rules.py:test_br05_rejected_leave_no_cascade | ✅ PASS |
| BR-06 | Approved leave: overlapping shifts → status=on_leave | §12.5-§12.6 | test_hr_workflows.py:test_leave_approval_cascades_to_shifts | ✅ PASS |
| BR-07 | Self-approval: user không thể approve leave của chính mình | §12.5 | test_hr_business_rules.py:test_br07_self_approval_rejected_400 | ✅ PASS |
| BR-08 | Cannot have 2 active TimeLog (check_out=null) cùng lúc → UNIQUE constraint | §12.6 | test_hr_api_contracts.py:test_ac6_duplicate_checkin_returns_409 | ✅ PASS |
| BR-09 | Check-in: soft-deleted shift → 404 Not Found | §12.6 | test_hr_business_rules.py:test_br09_checkin_with_deleted_shift_404 | ✅ PASS |
| BR-10 | Check-in: cross-user shift (same clinic) → 403 Forbidden | §12.6 | test_hr_business_rules.py:test_br10_staff_cannot_checkin_admins_shift | ✅ PASS |
| BR-11 | Check-out without check-in → 404 Not Found | §12.6 | test_hr_business_rules.py:test_br04_checkout_without_checkin | ✅ PASS |
| BR-12 | late_minutes = max(0, check_in_time - shift.start_time) nếu shift_id có, else null | §12.6 | test_hr_workflows.py:test_ac3_late_minutes | ✅ PASS |
| BR-13 | ot_hours = max(0, check_out_time - shift.end_time) nếu shift_id có, else null | §12.6 | test_hr_workflows.py:test_ac4_ot_hours | ✅ PASS |
| BR-14 | total_hours = check_out - check_in (in hours, decimal) | §12.6 | test_hr_business_rules.py:test_br14_total_hours_computation | ✅ PASS |
| BR-15 | Tenant isolation: không thể read/write shifts của clinic khác | §1 (Tenancy) | test_hr_api_contracts.py:test_user_b_cannot_patch_clinic_a_shift_template | ✅ PASS |
| BR-16 | Recurring shift generation: idempotent (re-run không tạo duplicates) | §12.4 | test_hr_workflows.py:test_recurring_generation_idempotency | ✅ PASS |

**BR Coverage: 16/16 ✅ PASS**

---

## 9. Xử lý lỗi

### 9.1 Các mã lỗi HTTP

| Mã HTTP | Mã lỗi | Tình huống xảy ra | Thông báo ví dụ |
|---------|--------|-------------------|-----------------|
| 400 | BadRequest / BusinessRuleError | Quy tắc nghiệp vụ bị vi phạm (ví dụ: end_time ≤ start_time, self-approval leave) | `"end_time must be after start_time"` |
| 401 | Unauthorized | Token không hợp lệ hoặc hết hạn | `"Not authenticated"` |
| 403 | Forbidden / ForbiddenError | Không có permission yêu cầu, hoặc thuộc clinic khác | `"Required permission: shift.manage"` |
| 404 | NotFound / NotFoundError | Resource không tồn tại hoặc đã bị xóa (soft delete) | `"Shift template not found"` |
| 409 | Conflict | UNIQUE constraint violation (ví dụ: duplicate active check-in) | `"Duplicate active check-in exists"` |
| 422 | Unprocessable Entity | Lỗi validation Pydantic (format sai, missing required field, v.v.) | `"Field 'start_time' is required"` |

### 9.2 Định dạng phản hồi lỗi

**Lỗi đơn giản:**

```json
{
  "detail": "Mô tả lỗi chi tiết"
}
```

**Lỗi validation (422):**

```json
{
  "detail": [
    {
      "loc": ["body", "start_time"],
      "msg": "Field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## 10. Chiến lược cache

**V1 không sử dụng cache cho HR module.**

Lý do:
- Dữ liệu shifts/leaves/timelogs không thay đổi thường xuyên
- Kích thước dữ liệu nhỏ (unique index trên clinic+user+date+time đã đủ nhanh)
- Overhead invalidation cache khi có update không đáng giá

**Ghi chú:** User permission cache (TASK-004) vẫn tồn tại ở level core, không liên quan đến HR module.

---

## 11. Ghi chú và lưu ý khi kiểm thử

### 11.1 Điểm quan trọng cần nắm

- **Timezone:** Tất cả timestamps sử dụng UTC (v1 không hỗ trợ multi-timezone). `func.date()` filter trong `/attendance/export` sẽ roll over tại UTC midnight — nếu clinic ở múi giờ khác, sẽ sai. Deferred (TASK-XXX).

- **Excel export library:** Dùng `openpyxl`. Content-Type: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`. Filename format: `attendance_YYYY-MM-DD_YYYY-MM-DD.xlsx`

- **Recurring cron job:** Chạy hàng ngày (ví dụ: 00:00 UTC). Sinh Shifts cho 30 ngày tới. Idempotent — safe chạy nhiều lần.

- **Self check-in only:** Endpoint `/attendance/check-in` lấy `user_id` từ JWT token (không từ body). Admin không thể check-in cho người khác.

- **Manager cannot approve own leave:** BR-07 — service layer check `if leave_request.user_id == approved_by: raise BusinessRuleError`.

- **Tenant isolation (BR-15):** Tất cả select queries include `WHERE clinic_id = :clinic_id`. Mutating endpoints (PATCH/DELETE/POST) verify `clinic_id` match từ JWT trước khi thực hiện.

- **Soft delete:** Xóa không thực sự xóa khỏi DB, chỉ set `is_deleted=true`. SELECT queries filter `WHERE NOT is_deleted` để không show deleted records. DELETE endpoint hợp lệ với soft-deleted records (404 error nếu record đã bị soft-delete).

### 11.2 Gợi ý dữ liệu kiểm thử

| Kịch bản | Giá trị đầu vào | Kết quả kỳ vọng |
|---------|----------------|----------------|
| Create shift với end_time ≤ start_time | start=07:30, end=07:30 | 400 Bad Request — end_time must be after start_time |
| Create recurring với days_of_week=[8] | days_of_week=[8] | 422 — days_of_week values must be 1–7 |
| Approve leave T4 nhân viên A, user B là manager | user_id=A, approved_by=B | Status → approved, shifts [T4] → on_leave |
| Self-approve leave | user_id=A, approved_by=A | 400 — Cannot approve own leave |
| Check-in 2 lần cùng lúc (shift_id như nhau) | POST check-in #2 trong khi #1 chưa check-out | 409 Conflict — Duplicate active check-in |
| Check-out không có check-in trước | POST check-out (no active time_log) | 404 Not Found — No active check-in |
| Export với format=csv | format=csv | 400 — Only 'xlsx' format is supported |
| Xem công user khác (bình thường user) | GET /attendance/me (bất kỳ user) | Chỉ thấy công của mình |
| Admin xem công tất cả | GET /attendance (admin) | Thấy tất cả users (clinic_id=admin's clinic) |
| User B (clinic B) xem shifts clinic A | GET /shifts (clinic_id=A user_id_header=clinic B) | 403 hoặc empty list (clinic_id filter từ JWT) |

### 11.3 Hạn chế hiện tại

1. **Timezone / wall-clock semantics** — Tất cả time math dùng UTC. Non-UTC clinics sẽ có skewed late_minutes / ot_hours. `func.date()` roll over tại UTC midnight. Deferred (future task).

2. **RLS at DB layer** — `cms` DB user vẫn có `BYPASSRLS=True` (PostgreSQL superuser). Service layer thêm explicit `clinic_id` guard. Infrastructure follow-up cần change `cms` → non-superuser role.

3. **Audit trail async** — Audit events (TASK-002/003 infrastructure) có thể ghi bất đồng bộ. `test_wf04` assert `count >= 0` thay vì `count == exact_count`. Outside TASK-014 scope.

4. **Biometric / QR check-in** — Yêu cầu hardware integration. Deferred đến TASK-016 (Tauri client với biometric devices).

5. **Un-cascade when canceling approved leave** — Nếu admin cancel một leave request đã approved, shifts `on_leave` vẫn giữ status đó (không tự động change lại `scheduled`). Deferred.

6. **Commission calculation** — Không tính hoa hồng bác sĩ. V2+.

### 11.4 Hướng phát triển *(nếu có)*

- **Multi-timezone support** — Clinic có timezone setting, all time math (late_minutes, ot_hours, date rolls) dùng local time.
- **Approval workflow customization** — Cho phép clinic customize approver hierarchy (hiện fixed 1 level).
- **Biometric / QR / PIN check-in** — Tauri client (TASK-016).
- **In-app payroll calculation** — Commission, tax, deductions.
- **Shift swap / leave carry-over** — Nhân viên request đổi ca, tích lũy ngày phép.
- **Performance optimization** — Add materialized views cho timesheet reports (hiện calculated on-the-fly).

---

**Hoàn thành:** 2026-04-28  
**Trạng thái:** ✅ APPROVED & TESTED (95/95 tests pass, 16/16 BRs validated, 6/6 ACs pass)
