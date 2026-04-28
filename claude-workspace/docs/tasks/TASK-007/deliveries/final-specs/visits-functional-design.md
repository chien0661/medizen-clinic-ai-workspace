# Thiết Kế Chi Tiết Tính Năng: Quản lý Lịch sử Khám bệnh (Visit)

**Dự án:** Clinic CMS  
**Task:** TASK-007  
**Phiên bản:** 1.0  
**Ngày:** 2026-04-28  
**Trạng thái:** Đã duyệt (Testing PASSED, 117/117 tests)  
**Tài liệu liên quan:** Task brief TASK-007, SRS (docs/clinic_management_business_analysis.md §6)

---

## Lịch sử thay đổi

| Phiên bản | Ngày | Nội dung thay đổi |
|-----------|------|-------------------|
| 1.0 | 2026-04-28 | Phiên bản đầu tiên — chuyển giao từ Test Agent |

---

## Mục lục

- [1. Tổng quan tính năng](#1-tổng-quan-tính-năng)
- [2. Luồng xử lý tổng thể](#2-luồng-xử-lý-tổng-thể)
- [3. Nguồn dữ liệu đầu vào](#3-nguồn-dữ-liệu-đầu-vào)
- [4. Danh sách API](#4-danh-sách-api)
- [5. Chi tiết từng API](#5-chi-tiết-từng-api)
- [6. Cấu trúc cơ sở dữ liệu](#6-cấu-trúc-cơ-sở-dữ-liệu)
- [7. SQL tổng hợp và truy vấn dữ liệu](#7-sql-tổng-hợp-và-truy-vấn-dữ-liệu)
- [8. Quy tắc nghiệp vụ](#8-quy-tắc-nghiệp-vụ)
- [9. Xử lý lỗi](#9-xử-lý-lỗi)
- [10. Chiến lược cache](#10-chiến-lược-cache)
- [11. Ghi chú và lưu ý khi kiểm thử](#11-ghi-chú-và-lưu-ý-khi-kiểm-thử)

---

## 1. Tổng quan tính năng

### 1.1 Mục đích

Module **Visit** quản lý các lịch sử khám bệnh của bệnh nhân trong phòng khám. Mỗi visit là một tương tác giữa bệnh nhân, bác sĩ, và hệ thống y tế, cung cấp cơ chế xếp hàng ưu tiên, theo dõi trạng thái thanh toán, và tích hợp với các module khác (Appointment, Vitals, Services, Prescriptions, Invoices).

Visit là **entity trung tâm** trong Clinic CMS, kết nối các yếu tố:
- Patient (bệnh nhân)
- Doctor (bác sĩ phục vụ)
- Appointment (cuộc hẹn, nếu có)
- Vitals (dấu hiệu sức khỏe)
- Services (dịch vụ khám, điều trị)
- Prescriptions (toa thuốc)
- Invoices (hóa đơn thanh toán)

### 1.2 Phạm vi

**Bao gồm:**
- Tạo visit mới (walk-in registration)
- State machine quản lý trạng thái visit (WAITING → IN_PROGRESS → AWAITING_PAYMENT → COMPLETED)
- Sinh số thứ tự visit (visit_number) dạng `YYYYMMDD-NNN`, reset hàng ngày, an toàn khi đồng thời
- Xếp hàng ưu tiên (queue) dựa trên priority, assigned_doctor_id, created_at
- Gọi visit tiếp theo (call-next) với logic ưu tiên (bác sĩ được gán > không được gán > bác sĩ khác)
- Hủy visit với lý do bắt buộc
- Đánh dấu thanh toán (mark-paid) để hoàn tất
- Row-level security (RLS) đảm bảo tenant isolation

**Không bao gồm:**
- Quản lý appointment (TASK-008)
- Tính phí dịch vụ / hóa đơn (TASK-013)
- Toa thuốc (TASK-011)
- Dấu hiệu sức khỏe (TASK-006)

### 1.3 Các bên liên quan

| Vai trò | Mô tả |
|---------|-------|
| **Bác sĩ (Doctor)** | Bắt đầu khám, hoàn tất khám, xem queue, hủy visit nếu cần |
| **Lễ tân (Receptionist)** | Tạo walk-in visit, xem queue, đánh dấu thanh toán |
| **Quản trị (Admin)** | Toàn quyền quản lý visit |
| **Hệ thống Appointment** | Có thể cung cấp appointment_id khi tạo visit |
| **Hệ thống Billing** | Nhận thông báo AWAITING_PAYMENT, cập nhật khi thanh toán |

---

## 2. Luồng xử lý tổng thể

### 2.1 Sơ đồ trạng thái (State Machine)

```
                      ┌─────────────────────────────────────────┐
                      │  Bất kỳ trạng thái nào trừ COMPLETED    │
                      └─────────────────────────────────────────┘
                                      │
                                      ▼
                                 [CANCEL]
                                      │
                                      ▼
    ┌──────────────────────────────────────────────────────────────┐
    │                                                              │
    │         [POST /api/v1/visits/{id}/cancel]                  │
    │    Hủy visit (cần cancel_reason, min 3 ký tự)             │
    │    Ghi cancel_reason + cancelled_at vào DB                 │
    │                                                              │
    └──────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
                                  CANCELLED

    ┌─────────┐
    │ WAITING │  ◄────────────────── [POST /api/v1/visits]
    │ (khám   │                       Tạo visit mới
    │ chờ)    │
    └────┬────┘
         │
         │ [POST /api/v1/visits/{id}/start]
         │ Bác sĩ bắt đầu khám
         │ Ghi doctor_id, started_at
         ▼
    ┌──────────────┐
    │ IN_PROGRESS  │
    │ (đang khám)  │
    └────┬─────────┘
         │
         │ [POST /api/v1/visits/{id}/complete]
         │ Hoàn tất khám
         │ Ghi completed_at
         ▼
    ┌──────────────────┐
    │ AWAITING_PAYMENT │  ◄────── Chờ thanh toán
    │ (chờ TT)         │
    └────┬─────────────┘
         │
         │ [POST /api/v1/visits/{id}/mark-paid]
         │ Đánh dấu thanh toán (admin/lễ tân)
         ▼
    ┌───────────┐
    │ COMPLETED │  ◄────── Terminal state, không thay đổi
    │ (hoàn tất)│
    └───────────┘
```

**Lưu ý:** 
- COMPLETED là terminal state (immutable)
- CANCELLED cũng là terminal state
- Chỉ được phép cancel từ WAITING, IN_PROGRESS, AWAITING_PAYMENT (không được cancel từ COMPLETED)
- Transition không hợp lệ (ví dụ WAITING → COMPLETED trực tiếp) trả về HTTP 409

### 2.2 Luồng call-next (Gọi visit tiếp theo)

```
[POST /api/v1/visits/call-next]
         │
         ▼
[Xác thực user + clinic]
         │
         ▼
[SELECT FROM visit WHERE clinic_id = ? AND status = 'WAITING'
 ORDER BY (CASE WHEN assigned_doctor_id = ? THEN 2
                WHEN assigned_doctor_id IS NULL THEN 1
                ELSE 0 END) DESC,
          priority DESC,
          created_at ASC
 FOR UPDATE SKIP LOCKED
 LIMIT 1]
         │
         ▼
  ┌──────┴──────┐
  │             │
  │ Có visit    │ Không có
  │             │
  ▼             ▼
[UPDATE      [Return 404
 visit.status = IN_PROGRESS
 visit.doctor_id = calling_doctor]
              │
  │           │
  ▼           ▼
[200 OK]   [Empty queue]
 reason = "assigned_doctor_match" |
          "unassigned" |
          "other"
```

**Đặc điểm:**
- Sử dụng `SELECT ... FOR UPDATE SKIP LOCKED` để đảm bảo không race condition
- Khi nhiều bác sĩ gọi cùng lúc, mỗi bác sĩ nhận visit khác nhau
- Priority logic: assigned_doctor_match > unassigned > other doctor

### 2.3 Quy trình Sinh visit_number

```
[POST /api/v1/visits] (create walk-in)
         │
         ▼
[Validate patient_id (FK constraint)]
         │
         ▼
[SELECT fn_next_visit_number(clinic_id, visit_date)
 → Gọi function PL/pgSQL]
         │
         ▼
[INSERT INTO visit_number_counter (clinic_id, visit_date, last_seq)
 VALUES (clinic_id, today, 1)
 ON CONFLICT (clinic_id, visit_date)
 DO UPDATE SET last_seq = last_seq + 1
 RETURNING last_seq]
         │
         ▼
[Format: to_char(date, 'YYYYMMDD') || '-' || lpad(seq, 3, '0')
 Ví dụ: 20260428-001, 20260428-002, ...]
         │
         ▼
[INSERT visit { visit_number, status='WAITING', ... }]
         │
         ▼
[201 Created]
```

**Đảm bảo:**
- Số thứ tự tăng liên tục: 001, 002, 003, ...
- Reset hàng ngày (per date)
- Reset per clinic (mỗi phòng khám độc lập)
- Race-safe: `ON CONFLICT DO UPDATE` serializes concurrent calls

---

## 3. Nguồn dữ liệu đầu vào

*Dữ liệu đến từ người dùng qua API (walk-in registration, action endpoints), không có message queue hay file import. Phần này được bỏ qua.*

---

## 4. Danh sách API

Tất cả API đều yêu cầu xác thực qua header:
```
Authorization: Bearer {token}
```

**Đường dẫn gốc (Base Path):** `/api/v1/visits`

| STT | Phương thức | Đường dẫn | Mô tả tóm tắt | Permission |
|-----|------------|-----------|--------------|------------|
| 1 | GET | `/visits` | Danh sách visit với bộ lọc | `visit.read` |
| 2 | POST | `/visits` | Tạo visit mới (walk-in) | `visit.write` |
| 3 | GET | `/visits/queue` | Xem active queue (WAITING + IN_PROGRESS) | `visit.read` |
| 4 | POST | `/visits/call-next` | Gọi visit tiếp theo | `visit.write` |
| 5 | GET | `/visits/{id}` | Chi tiết visit | `visit.read` |
| 6 | PATCH | `/visits/{id}` | Cập nhật visit (non-status fields) | `visit.write` |
| 7 | POST | `/visits/{id}/start` | WAITING → IN_PROGRESS | `visit.write` |
| 8 | POST | `/visits/{id}/complete` | IN_PROGRESS → AWAITING_PAYMENT | `visit.write` |
| 9 | POST | `/visits/{id}/cancel` | Hủy visit (yêu cầu reason) | `visit.cancel` |
| 10 | POST | `/visits/{id}/mark-paid` | AWAITING_PAYMENT → COMPLETED | `payment.receive` |

---

## 5. Chi tiết từng API

### 5.1 Lấy danh sách visit

#### Thông tin chung

| Thuộc tính | Giá trị |
|------------|--------|
| **Đường dẫn** | `GET /api/v1/visits` |
| **Mô tả** | Lấy danh sách visit của phòng khám hiện tại, hỗ trợ lọc theo status, doctor, ngày |
| **Xác thực** | Bắt buộc |

#### Tham số đầu vào

| Tham số | Kiểu | Bắt buộc | Mô tả | Giá trị mặc định |
|---------|------|---------|-------|-----------------|
| `status` | String | Không | Lọc theo trạng thái (WAITING, IN_PROGRESS, AWAITING_PAYMENT, COMPLETED, CANCELLED) | Không lọc |
| `doctor_id` | UUID | Không | Lọc theo bác sĩ được gán | Không lọc |
| `visit_date` | Date (YYYY-MM-DD) | Không | Lọc theo ngày khám | Không lọc |
| `skip` | Integer ≥ 0 | Không | Bỏ qua N bản ghi đầu tiên | 0 |
| `limit` | Integer 1-500 | Không | Giới hạn số lượng bản ghi | 50 |

#### Quy trình xử lý

| Bước | Mô tả |
|------|-------|
| 1 | Xác thực token, kiểm tra quyền `visit.read` |
| 2 | Lấy clinic_id từ context (RLS enforcement) |
| 3 | Xây dựng WHERE clause từ các tham số lọc (nếu có) |
| 4 | Truy vấn từ bảng visit (chỉ visit của clinic hiện tại, nhờ RLS) |
| 5 | Trả về danh sách + tổng số lượng (pagination) |

#### Kết quả trả về

**Thành công (200 OK):**

```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "clinic_id": "550e8400-e29b-41d4-a716-446655440001",
      "patient_id": "550e8400-e29b-41d4-a716-446655440002",
      "doctor_id": "550e8400-e29b-41d4-a716-446655440003",
      "assigned_doctor_id": "550e8400-e29b-41d4-a716-446655440004",
      "appointment_id": null,
      "visit_number": "20260428-001",
      "visit_date": "2026-04-28",
      "status": "IN_PROGRESS",
      "priority": 5,
      "chief_complaint": "Đau đầu, chóng mặt",
      "notes": "Bệnh nhân có tiền sử cao huyết áp",
      "is_follow_up": false,
      "is_returning": true,
      "cancel_reason": null,
      "started_at": "2026-04-28T09:15:00+07:00",
      "completed_at": null,
      "cancelled_at": null,
      "created_at": "2026-04-28T09:10:00+07:00",
      "updated_at": "2026-04-28T09:15:00+07:00",
      "created_by": "550e8400-e29b-41d4-a716-446655440003",
      "updated_by": "550e8400-e29b-41d4-a716-446655440003",
      "version": 2
    }
  ],
  "total": 15,
  "skip": 0,
  "limit": 50
}
```

| Trường | Kiểu | Mô tả |
|--------|------|-------|
| `items[]` | Array | Danh sách visit |
| `total` | Integer | Tổng số visit trong phòng khám (không tính skip/limit) |
| `skip` | Integer | Giá trị skip được sử dụng |
| `limit` | Integer | Giá trị limit được sử dụng |

---

### 5.2 Tạo visit mới

#### Thông tin chung

| Thuộc tính | Giá trị |
|------------|--------|
| **Đường dẫn** | `POST /api/v1/visits` |
| **Mô tả** | Tạo visit mới (walk-in registration) với trạng thái WAITING |
| **Xác thực** | Bắt buộc |
| **Status Code** | 201 Created |

#### Tham số đầu vào (Request Body)

| Trường | Kiểu | Bắt buộc | Mô tả | Ví dụ |
|--------|------|---------|-------|-------|
| `patient_id` | UUID | Có | ID của bệnh nhân | `"550e8400-e29b-41d4-a716-446655440002"` |
| `chief_complaint` | String | Không | Triệu chứng chính | `"Đau đầu"` |
| `priority` | Integer (0-100) | Không | Ưu tiên (0=bình thường, cao hơn = ưu tiên cao) | `5` |
| `appointment_id` | UUID | Không | ID appointment nếu khám có hẹn | `"550e8400-..."` |
| `assigned_doctor_id` | UUID | Không | ID bác sĩ được gán trước | `"550e8400-..."` |
| `is_follow_up` | Boolean | Không | Có phải khám theo dõi không | `false` |
| `is_returning` | Boolean | Không | Có phải bệnh nhân cũ không | `true` |
| `notes` | String | Không | Ghi chú thêm | `"Bệnh nhân có tiền sử..."` |

#### Ví dụ request

```json
POST /api/v1/visits
Authorization: Bearer <token>
Content-Type: application/json

{
  "patient_id": "550e8400-e29b-41d4-a716-446655440002",
  "chief_complaint": "Đau đầu, chóng mặt",
  "priority": 5,
  "is_returning": true,
  "notes": "Bệnh nhân có tiền sử cao huyết áp"
}
```

#### Quy trình xử lý

| Bước | Mô tả |
|------|-------|
| 1 | Xác thực token, kiểm tra quyền `visit.write` |
| 2 | Lấy clinic_id từ context |
| 3 | Validate `patient_id` tồn tại và thuộc clinic hiện tại |
| 4 | Gọi `fn_next_visit_number(clinic_id, today)` để sinh visit_number |
| 5 | INSERT visit với status=WAITING, visit_number, clinic_id, ... |
| 6 | Trả về HTTP 201 + VisitResponse |

#### Kết quả trả về

**Thành công (201 Created):**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "clinic_id": "550e8400-e29b-41d4-a716-446655440001",
  "patient_id": "550e8400-e29b-41d4-a716-446655440002",
  "doctor_id": null,
  "assigned_doctor_id": null,
  "appointment_id": null,
  "visit_number": "20260428-001",
  "visit_date": "2026-04-28",
  "status": "WAITING",
  "priority": 5,
  "chief_complaint": "Đau đầu, chóng mặt",
  "notes": "Bệnh nhân có tiền sử cao huyết áp",
  "is_follow_up": false,
  "is_returning": true,
  "cancel_reason": null,
  "started_at": null,
  "completed_at": null,
  "cancelled_at": null,
  "created_at": "2026-04-28T09:10:00+07:00",
  "updated_at": "2026-04-28T09:10:00+07:00",
  "created_by": "550e8400-e29b-41d4-a716-446655440003",
  "updated_by": null,
  "version": 1
}
```

**Lỗi:**

- `422 Unprocessable Entity`: Tham số không hợp lệ (ví dụ priority > 100)
- `403 Forbidden`: Thiếu quyền `visit.write`
- `404 Not Found`: Patient ID không tồn tại (hoặc non-existent patient_id → hiện tại là FK IntegrityError, xem BUG-001)
- `400 Bad Request`: Clinic ID thiếu trong context

---

### 5.3 Xem active queue

#### Thông tin chung

| Thuộc tính | Giá trị |
|------------|--------|
| **Đường dẫn** | `GET /api/v1/visits/queue` |
| **Mô tả** | Lấy danh sách visit đang chờ và đang khám (WAITING + IN_PROGRESS), sắp xếp theo ưu tiên |
| **Xác thực** | Bắt buộc |

#### Tham số đầu vào

| Tham số | Kiểu | Bắt buộc | Mô tả |
|---------|------|---------|-------|
| `skip` | Integer ≥ 0 | Không | Bỏ qua N bản ghi | 0 |
| `limit` | Integer 1-500 | Không | Giới hạn số lượng | 100 |

#### Quy trình xử lý

| Bước | Mô tả |
|------|-------|
| 1 | Xác thực token, kiểm tra quyền `visit.read` |
| 2 | Lấy clinic_id từ context |
| 3 | Truy vấn: SELECT từ visit WHERE clinic_id = ? AND status IN ('WAITING', 'IN_PROGRESS') ORDER BY priority DESC, created_at ASC |
| 4 | Trả về danh sách (pagination) |

#### Kết quả trả về

**Thành công (200 OK):**

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "clinic_id": "550e8400-e29b-41d4-a716-446655440001",
    "patient_id": "550e8400-e29b-41d4-a716-446655440002",
    "doctor_id": "550e8400-e29b-41d4-a716-446655440003",
    "assigned_doctor_id": "550e8400-e29b-41d4-a716-446655440004",
    "visit_number": "20260428-001",
    "visit_date": "2026-04-28",
    "status": "IN_PROGRESS",
    "priority": 10,
    "chief_complaint": "Đau đầu",
    "notes": null,
    "is_follow_up": false,
    "is_returning": true,
    "cancel_reason": null,
    "started_at": "2026-04-28T09:15:00+07:00",
    "completed_at": null,
    "cancelled_at": null,
    "created_at": "2026-04-28T09:10:00+07:00",
    "updated_at": "2026-04-28T09:15:00+07:00",
    "created_by": "550e8400-e29b-41d4-a716-446655440003",
    "updated_by": "550e8400-e29b-41d4-a716-446655440003",
    "version": 2
  }
]
```

**Performance note:** Queue p95 = 13.6 ms cho 50 visit (AC threshold 50 ms, 73% headroom).

---

### 5.4 Gọi visit tiếp theo (call-next)

#### Thông tin chung

| Thuộc tính | Giá trị |
|------------|--------|
| **Đường dẫn** | `POST /api/v1/visits/call-next` |
| **Mô tả** | Gọi visit WAITING tiếp theo với logic ưu tiên (assigned_doctor_match > unassigned > other) |
| **Xác thực** | Bắt buộc |

#### Tham số đầu vào

Không có request body.

#### Quy trình xử lý

| Bước | Mô tả |
|------|-------|
| 1 | Xác thực token, kiểm tra quyền `visit.write` |
| 2 | Lấy clinic_id và current_user_id từ context |
| 3 | Truy vấn: SELECT từ visit WHERE clinic_id = ? AND status = 'WAITING' ORDER BY CASE WHEN assigned_doctor_id = ? THEN 2 WHEN assigned_doctor_id IS NULL THEN 1 ELSE 0 END DESC, priority DESC, created_at ASC FOR UPDATE SKIP LOCKED LIMIT 1 |
| 4 | Nếu không có visit → trả 404 |
| 5 | UPDATE visit.status = 'IN_PROGRESS', visit.doctor_id = current_user_id, visit.started_at = now |
| 6 | Trả về visit + reason (assigned_doctor_match / unassigned / other) |

**Đặc điểm:** Sử dụng `FOR UPDATE SKIP LOCKED` để đảm bảo an toàn khi nhiều bác sĩ gọi cùng lúc. Mỗi bác sĩ nhận visit khác nhau.

#### Kết quả trả về

**Thành công (200 OK):**

```json
{
  "visit": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "clinic_id": "550e8400-e29b-41d4-a716-446655440001",
    "patient_id": "550e8400-e29b-41d4-a716-446655440002",
    "doctor_id": "550e8400-e29b-41d4-a716-446655440003",
    "assigned_doctor_id": "550e8400-e29b-41d4-a716-446655440003",
    "visit_number": "20260428-001",
    "visit_date": "2026-04-28",
    "status": "IN_PROGRESS",
    "priority": 5,
    "chief_complaint": "Đau đầu",
    "notes": null,
    "is_follow_up": false,
    "is_returning": true,
    "cancel_reason": null,
    "started_at": "2026-04-28T09:15:00+07:00",
    "completed_at": null,
    "cancelled_at": null,
    "created_at": "2026-04-28T09:10:00+07:00",
    "updated_at": "2026-04-28T09:15:00+07:00",
    "created_by": "550e8400-e29b-41d4-a716-446655440003",
    "updated_by": "550e8400-e29b-41d4-a716-446655440003",
    "version": 2
  },
  "reason": "assigned_doctor_match"
}
```

| Trường | Mô tả |
|--------|-------|
| `visit` | Visit object |
| `reason` | `assigned_doctor_match` (visit.assigned_doctor_id = calling_doctor) \| `unassigned` (visit.assigned_doctor_id IS NULL) \| `other` (visit.assigned_doctor_id ≠ calling_doctor) |

**Lỗi:**

- `404 Not Found`: Không có visit WAITING nào
- `403 Forbidden`: Thiếu quyền `visit.write`

---

### 5.5 Chi tiết visit

#### Thông tin chung

| Thuộc tính | Giá trị |
|------------|--------|
| **Đường dẫn** | `GET /api/v1/visits/{visit_id}` |
| **Mô tả** | Lấy chi tiết visit theo ID |
| **Xác thực** | Bắt buộc |

#### Tham số đầu vào

| Tham số | Kiểu | Bắt buộc | Mô tả |
|---------|------|---------|-------|
| `visit_id` | UUID | Có | ID của visit |

#### Quy trình xử lý

| Bước | Mô tả |
|------|-------|
| 1 | Xác thực token, kiểm tra quyền `visit.read` |
| 2 | Lấy clinic_id từ context |
| 3 | SELECT visit WHERE id = visit_id AND clinic_id = clinic_id (RLS) |
| 4 | Nếu không tìm thấy → 404 |
| 5 | Trả về VisitResponse |

#### Kết quả trả về

**Thành công (200 OK):** Trả về VisitResponse (cùng format như create visit)

**Lỗi:**

- `404 Not Found`: Visit không tồn tại hoặc không thuộc clinic hiện tại
- `403 Forbidden`: Thiếu quyền `visit.read`

---

### 5.6 Cập nhật visit (non-status fields)

#### Thông tin chung

| Thuộc tính | Giá trị |
|------------|--------|
| **Đường dẫn** | `PATCH /api/v1/visits/{visit_id}` |
| **Mô tả** | Cập nhật các trường non-status (chief_complaint, notes, priority, assigned_doctor_id, is_follow_up, is_returning) |
| **Xác thực** | Bắt buộc |

#### Tham số đầu vào

| Trường | Kiểu | Bắt buộc | Mô tả |
|--------|------|---------|-------|
| `chief_complaint` | String | Không | Triệu chứng chính |
| `notes` | String | Không | Ghi chú |
| `priority` | Integer (0-100) | Không | Ưu tiên |
| `assigned_doctor_id` | UUID | Không | Bác sĩ được gán |
| `is_follow_up` | Boolean | Không | Có phải khám theo dõi |
| `is_returning` | Boolean | Không | Có phải bệnh nhân cũ |

#### Ví dụ request

```json
PATCH /api/v1/visits/{visit_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "priority": 10,
  "notes": "Cập nhật ghi chú"
}
```

#### Kết quả trả về

**Thành công (200 OK):** Trả về VisitResponse (bản ghi cập nhật)

**Lỗi:**

- `404 Not Found`: Visit không tồn tại
- `403 Forbidden`: Thiếu quyền `visit.write`

---

### 5.7 Bắt đầu khám (start)

#### Thông tin chung

| Thuộc tính | Giá trị |
|------------|--------|
| **Đường dẫn** | `POST /api/v1/visits/{visit_id}/start` |
| **Mô tả** | Transition từ WAITING → IN_PROGRESS, ghi doctor_id, started_at |
| **Xác thực** | Bắt buộc |

#### Tham số đầu vào

Không có request body.

#### Quy trình xử lý

| Bước | Mô tả |
|------|-------|
| 1 | Xác thực token, kiểm tra quyền `visit.write` |
| 2 | SELECT visit WHERE id = visit_id AND clinic_id = clinic_id |
| 3 | Kiểm tra state machine: status phải là WAITING |
| 4 | UPDATE status = IN_PROGRESS, doctor_id = current_user_id, started_at = now |
| 5 | Trả về 200 OK + VisitResponse |

#### Kết quả trả về

**Thành công (200 OK):** VisitResponse với status=IN_PROGRESS, doctor_id, started_at được set

**Lỗi:**

- `404 Not Found`: Visit không tồn tại
- `409 Conflict`: State transition không hợp lệ (status ≠ WAITING)
- `403 Forbidden`: Thiếu quyền `visit.write`

---

### 5.8 Hoàn tất khám (complete)

#### Thông tin chung

| Thuộc tính | Giá trị |
|------------|--------|
| **Đường dẫn** | `POST /api/v1/visits/{visit_id}/complete` |
| **Mô tả** | Transition từ IN_PROGRESS → AWAITING_PAYMENT, ghi completed_at |
| **Xác thực** | Bắt buộc |

#### Tham số đầu vào

Không có request body.

#### Quy trình xử lý

| Bước | Mô tả |
|------|-------|
| 1 | Xác thực token, kiểm tra quyền `visit.write` |
| 2 | SELECT visit WHERE id = visit_id AND clinic_id = clinic_id |
| 3 | Kiểm tra state machine: status phải là IN_PROGRESS |
| 4 | Kiểm tra: doctor_id phải trùng với current_user_id (defensive check) |
| 5 | UPDATE status = AWAITING_PAYMENT, completed_at = now |
| 6 | Trả về 200 OK + VisitResponse |

#### Kết quả trả về

**Thành công (200 OK):** VisitResponse với status=AWAITING_PAYMENT, completed_at được set

**Lỗi:**

- `404 Not Found`: Visit không tồn tại
- `409 Conflict`: State transition không hợp lệ (status ≠ IN_PROGRESS, hoặc doctor_id mismatch)
- `403 Forbidden`: Thiếu quyền `visit.write`

---

### 5.9 Hủy khám (cancel)

#### Thông tin chung

| Thuộc tính | Giá trị |
|------------|--------|
| **Đường dẫn** | `POST /api/v1/visits/{visit_id}/cancel` |
| **Mô tả** | Hủy visit từ bất kỳ trạng thái nào (trừ COMPLETED), yêu cầu cancel_reason |
| **Xác thực** | Bắt buộc |
| **Permission** | `visit.cancel` (chỉ admin, doctor) |

#### Tham số đầu vào (Request Body)

| Trường | Kiểu | Bắt buộc | Mô tả |
|--------|------|---------|-------|
| `cancel_reason` | String | Có | Lý do hủy, tối thiểu 3 ký tự, không được rỗng trắng |

#### Ví dụ request

```json
POST /api/v1/visits/{visit_id}/cancel
Authorization: Bearer <token>
Content-Type: application/json

{
  "cancel_reason": "Bệnh nhân yêu cầu dời lịch khám"
}
```

#### Quy trình xử lý

| Bước | Mô tả |
|------|-------|
| 1 | Xác thực token, kiểm tra quyền `visit.cancel` (chỉ admin/doctor) |
| 2 | Validate cancel_reason: min_length=3, not-blank |
| 3 | SELECT visit WHERE id = visit_id AND clinic_id = clinic_id |
| 4 | Kiểm tra state machine: status không được là COMPLETED |
| 5 | UPDATE status = CANCELLED, cancel_reason, cancelled_at = now |
| 6 | Trả về 200 OK + VisitResponse |

#### Kết quả trả về

**Thành công (200 OK):** VisitResponse với status=CANCELLED, cancel_reason, cancelled_at được set

**Lỗi:**

- `404 Not Found`: Visit không tồn tại
- `422 Unprocessable Entity`: cancel_reason không hợp lệ (< 3 ký tự, rỗng trắng, v.v.)
- `409 Conflict`: State transition không hợp lệ (status = COMPLETED)
- `403 Forbidden`: Thiếu quyền `visit.cancel` (chỉ admin/doctor được phép)

---

### 5.10 Đánh dấu thanh toán (mark-paid)

#### Thông tin chung

| Thuộc tính | Giá trị |
|------------|--------|
| **Đường dẫn** | `POST /api/v1/visits/{visit_id}/mark-paid` |
| **Mô tả** | Transition từ AWAITING_PAYMENT → COMPLETED |
| **Xác thực** | Bắt buộc |
| **Permission** | `payment.receive` (chỉ admin, receptionist) |

#### Tham số đầu vào

Không có request body.

#### Quy trình xử lý

| Bước | Mô tả |
|------|-------|
| 1 | Xác thực token, kiểm tra quyền `payment.receive` (chỉ admin/receptionist) |
| 2 | SELECT visit WHERE id = visit_id AND clinic_id = clinic_id |
| 3 | Kiểm tra state machine: status phải là AWAITING_PAYMENT |
| 4 | UPDATE status = COMPLETED |
| 5 | Trả về 200 OK + VisitResponse |

#### Kết quả trả về

**Thành công (200 OK):** VisitResponse với status=COMPLETED

**Lỗi:**

- `404 Not Found`: Visit không tồn tại
- `409 Conflict`: State transition không hợp lệ (status ≠ AWAITING_PAYMENT)
- `403 Forbidden`: Thiếu quyền `payment.receive` (chỉ admin/receptionist)

---

## 6. Cấu trúc cơ sở dữ liệu

### 6.1 Tổng quan các bảng

| Bảng | Mục đích |
|------|---------|
| `visit` | Lưu thông tin lịch sử khám bệnh của bệnh nhân |
| `visit_number_counter` | Đếm số thứ tự visit per (clinic, date) để sinh visit_number an toàn |

### 6.2 Chi tiết bảng

#### Bảng: `visit`

**Mô tả:** Bảng lưu thông tin chi tiết về mỗi lịch sử khám bệnh. Mỗi visit là một encounter giữa bệnh nhân và bác sĩ, ghi lại trạng thái, triệu chứng, và các mốc thời gian quan trọng.

| Tên cột | Kiểu dữ liệu | Bắt buộc | Mô tả |
|---------|-------------|---------|-------|
| `id` | UUID | Có | Primary Key, tự sinh UUID |
| `clinic_id` | UUID | Có | FK → clinic.id, phòng khám quản lý visit |
| `patient_id` | UUID | Có | FK → patient.id, bệnh nhân |
| `doctor_id` | UUID | Không | FK → user.id, bác sĩ thực tế phục vụ (set khi start) |
| `assigned_doctor_id` | UUID | Không | FK → user.id, bác sĩ được gán trước (cho queue priority) |
| `appointment_id` | UUID | Không | FK → appointment.id (khi TASK-008 hoàn tất) |
| `visit_number` | VARCHAR(30) | Có | Số thứ tự visit (ví dụ: 20260428-001), duy nhất per (clinic, visit_date) |
| `visit_date` | Date | Có | Ngày khám, default = CURRENT_DATE |
| `status` | VARCHAR(20) | Có | Trạng thái (WAITING, IN_PROGRESS, AWAITING_PAYMENT, COMPLETED, CANCELLED) |
| `priority` | Integer | Có | Mức ưu tiên (0-100), default = 0 |
| `is_follow_up` | Boolean | Có | Có phải khám theo dõi không, default = false |
| `is_returning` | Boolean | Có | Có phải bệnh nhân cũ không, default = false |
| `chief_complaint` | Text | Không | Triệu chứng chính |
| `notes` | Text | Không | Ghi chú thêm |
| `cancel_reason` | Text | Không | Lý do hủy khám (set khi cancel) |
| `started_at` | Timestamp with TZ | Không | Thời điểm bác sĩ bắt đầu khám |
| `completed_at` | Timestamp with TZ | Không | Thời điểm hoàn tất khám |
| `cancelled_at` | Timestamp with TZ | Không | Thời điểm hủy khám |
| `created_at` | Timestamp with TZ | Có | Thời điểm tạo visit |
| `updated_at` | Timestamp with TZ | Có | Thời điểm cập nhật lần cuối |
| `created_by` | UUID | Không | User ID tạo visit |
| `updated_by` | UUID | Không | User ID cập nhật lần cuối |
| `is_deleted` | Boolean | Có | Soft delete flag, default = false |
| `version` | Integer | Có | Optimistic lock version |

**Tính duy nhất (Unique Key):**
```
UNIQUE (clinic_id, visit_date, visit_number) 
WHERE NOT is_deleted
```
Đảm bảo visit_number là duy nhất trong mỗi ngày của mỗi phòng khám.

**Constraint:**
```
CHECK (status IN ('WAITING', 'IN_PROGRESS', 'AWAITING_PAYMENT', 'COMPLETED', 'CANCELLED'))
```

**Row-Level Security (RLS):**
- Policy: `tenant_isolation` (ALL, USING `clinic_id = app.current_clinic_id`)
- Tất cả users nhìn thấy chỉ visit của clinic hiện tại

---

#### Bảng: `visit_number_counter`

**Mô tả:** Bảng nhỏ lưu counter số thứ tự visit per (clinic, date). Sử dụng `ON CONFLICT DO UPDATE` với row-level lock để đảm bảo atomic, race-safe generation.

| Tên cột | Kiểu dữ liệu | Bắt buộc | Mô tả |
|---------|-------------|---------|-------|
| `clinic_id` | UUID | Có | FK → clinic.id, part of PK |
| `visit_date` | Date | Có | Ngày khám, part of PK |
| `last_seq` | Integer | Có | Số thứ tự cuối cùng được sinh (default = 0) |

**Primary Key:**
```
PRIMARY KEY (clinic_id, visit_date)
```

**Row-Level Security (RLS):**
- Policy: `tenant_isolation` (ALL, USING `clinic_id = app.current_clinic_id`)

---

### 6.3 Indexes

| Tên index | Cột(s) | Loại | Partial | Mục đích |
|-----------|--------|------|---------|---------|
| `pk_visit` | `id` | Primary Key | — | Primary key |
| `pk_visit_number_counter` | `clinic_id, visit_date` | Primary Key | — | Primary key |
| `ix_visit_clinic_status_priority` | `clinic_id, status, priority DESC, created_at` | B-tree | `WHERE NOT is_deleted` | Queue query optimization |
| `uq_visit_clinic_date_number` | `clinic_id, visit_date, visit_number` | Unique | `WHERE NOT is_deleted` | Unique constraint |
| `ix_visit_patient_id` | `patient_id` | B-tree | — | Patient history lookup |

---

### 6.4 SQL Script Tạo Bảng

```sql
-- Bảng visit_number_counter
CREATE TABLE visit_number_counter (
    clinic_id UUID NOT NULL,
    visit_date DATE NOT NULL,
    last_seq INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (clinic_id, visit_date),
    FOREIGN KEY (clinic_id) REFERENCES clinic(id) ON DELETE RESTRICT
);

-- Bảng visit
CREATE TABLE visit (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clinic_id UUID NOT NULL,
    patient_id UUID NOT NULL,
    doctor_id UUID,
    assigned_doctor_id UUID,
    appointment_id UUID,
    visit_number VARCHAR(30) NOT NULL,
    visit_date DATE NOT NULL DEFAULT CURRENT_DATE,
    status VARCHAR(20) NOT NULL DEFAULT 'WAITING',
    priority INTEGER NOT NULL DEFAULT 0,
    is_follow_up BOOLEAN NOT NULL DEFAULT FALSE,
    is_returning BOOLEAN NOT NULL DEFAULT FALSE,
    chief_complaint TEXT,
    notes TEXT,
    cancel_reason TEXT,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    cancelled_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by UUID,
    updated_by UUID,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    version INTEGER NOT NULL DEFAULT 1,
    
    FOREIGN KEY (clinic_id) REFERENCES clinic(id) ON DELETE RESTRICT,
    FOREIGN KEY (patient_id) REFERENCES patient(id) ON DELETE RESTRICT,
    FOREIGN KEY (doctor_id) REFERENCES "user"(id) ON DELETE RESTRICT,
    FOREIGN KEY (assigned_doctor_id) REFERENCES "user"(id) ON DELETE RESTRICT,
    
    UNIQUE (clinic_id, visit_date, visit_number) WHERE NOT is_deleted,
    
    CHECK (status IN ('WAITING', 'IN_PROGRESS', 'AWAITING_PAYMENT', 'COMPLETED', 'CANCELLED'))
);

-- Indexes
CREATE INDEX ix_visit_clinic_status_priority ON visit (clinic_id, status, priority DESC, created_at) WHERE NOT is_deleted;
CREATE INDEX ix_visit_patient_id ON visit (patient_id);

-- RLS (Row-Level Security)
ALTER TABLE visit ENABLE ROW LEVEL SECURITY;
ALTER TABLE visit FORCE ROW LEVEL SECURITY;
ALTER TABLE visit_number_counter ENABLE ROW LEVEL SECURITY;
ALTER TABLE visit_number_counter FORCE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY tenant_isolation ON visit
    USING (clinic_id = (current_setting('app.current_clinic_id')::UUID));
CREATE POLICY tenant_isolation ON visit_number_counter
    USING (clinic_id = (current_setting('app.current_clinic_id')::UUID));

-- Grant to cms_app role
GRANT SELECT, INSERT, UPDATE, DELETE ON visit TO cms_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON visit_number_counter TO cms_app;
```

---

## 7. SQL tổng hợp và truy vấn dữ liệu

### 7.1 SQL tổng hợp / ghi dữ liệu

Không áp dụng — tính năng này không có logic tổng hợp dữ liệu từ Kafka, ETL, hay batch job. Dữ liệu được ghi qua API endpoints.

---

### 7.2 SQL truy vấn báo cáo / lấy dữ liệu

#### 7.2.1 Sinh visit_number (call từ fn_next_visit_number)

**Mục đích:** Sinh số thứ tự visit dạng `YYYYMMDD-NNN` an toàn khi đồng thời, reset hàng ngày per clinic.

**PL/pgSQL Function:**

```sql
CREATE OR REPLACE FUNCTION fn_next_visit_number(
    p_clinic_id UUID,
    p_date      DATE
)
RETURNS TEXT
LANGUAGE plpgsql
AS $$
DECLARE
    v_seq INTEGER;
BEGIN
    -- Sử dụng ON CONFLICT DO UPDATE để serialized row-level lock
    -- Hai call đồng thời sẽ queue và mỗi call nhận số thứ tự khác nhau
    INSERT INTO visit_number_counter (clinic_id, visit_date, last_seq)
    VALUES (p_clinic_id, p_date, 1)
    ON CONFLICT (clinic_id, visit_date)
    DO UPDATE SET last_seq = visit_number_counter.last_seq + 1
    RETURNING last_seq INTO v_seq;

    -- Format: YYYYMMDD-NNN (ví dụ: 20260428-001)
    RETURN to_char(p_date, 'YYYYMMDD') || '-' || lpad(v_seq::text, 3, '0');
END;
$$;
```

**Ví dụ sử dụng:**

```sql
-- Sinh visit_number cho clinic A vào ngày 2026-04-28
SELECT fn_next_visit_number('550e8400-e29b-41d4-a716-446655440001'::UUID, '2026-04-28');
-- Kết quả: '20260428-001'

-- Gọi lại sẽ trả về '20260428-002'
SELECT fn_next_visit_number('550e8400-e29b-41d4-a716-446655440001'::UUID, '2026-04-28');
```

---

#### 7.2.2 Truy vấn Queue (WAITING + IN_PROGRESS)

**Mục đích:** Lấy danh sách visit đang chờ và đang khám, sắp xếp theo ưu tiên để hiển thị queue hoặc gọi visit tiếp theo.

```sql
SELECT 
    v.id,
    v.clinic_id,
    v.patient_id,
    v.doctor_id,
    v.assigned_doctor_id,
    v.visit_number,
    v.visit_date,
    v.status,
    v.priority,
    v.chief_complaint,
    v.notes,
    v.is_follow_up,
    v.is_returning,
    v.cancel_reason,
    v.started_at,
    v.completed_at,
    v.cancelled_at,
    v.created_at,
    v.updated_at,
    v.created_by,
    v.updated_by,
    v.version
FROM visit v
WHERE v.clinic_id = :clinic_id
  AND v.status IN ('WAITING', 'IN_PROGRESS')
  AND v.is_deleted = FALSE
ORDER BY 
    v.priority DESC,
    v.created_at ASC
LIMIT :limit
OFFSET :skip;
```

**Điều kiện lọc:**

| Tham số | Cột tương ứng | Ghi chú |
|---------|--------------|--------|
| `clinic_id` | `v.clinic_id` | Bắt buộc, từ RLS context |
| `limit` | — | Giới hạn số lượng (default 100, max 500) |
| `skip` | — | Pagination offset (default 0) |

**Hiệu suất:** Index `ix_visit_clinic_status_priority` trên `(clinic_id, status, priority DESC, created_at) WHERE NOT is_deleted` tối ưu hóa query này. P95 = 13.6 ms cho 50 visit.

---

#### 7.2.3 Call-next — Gọi visit tiếp theo (with SKIP LOCKED)

**Mục đích:** Atomic pick của next WAITING visit với priority logic, an toàn khi nhiều bác sĩ gọi cùng lúc. Sử dụng `FOR UPDATE SKIP LOCKED` để tránh race condition.

```sql
-- Câu SQL thực tế (được wrap bởi SQLAlchemy ORM):
SELECT 
    v.id,
    v.clinic_id,
    v.patient_id,
    v.doctor_id,
    v.assigned_doctor_id,
    v.visit_number,
    v.visit_date,
    v.status,
    v.priority,
    v.chief_complaint,
    v.notes,
    v.is_follow_up,
    v.is_returning,
    v.cancel_reason,
    v.started_at,
    v.completed_at,
    v.cancelled_at,
    v.created_at,
    v.updated_at,
    v.created_by,
    v.updated_by,
    v.version
FROM visit v
WHERE v.clinic_id = :clinic_id
  AND v.status = 'WAITING'
  AND v.is_deleted = FALSE
ORDER BY 
    -- Priority logic: assigned to me > unassigned > assigned to other
    CASE 
        WHEN v.assigned_doctor_id = :current_doctor_id THEN 2
        WHEN v.assigned_doctor_id IS NULL THEN 1
        ELSE 0 
    END DESC,
    v.priority DESC,
    v.created_at ASC
FOR UPDATE SKIP LOCKED
LIMIT 1;
```

**Giải thích:**
- `FOR UPDATE` — tạo row-level lock trên visit được chọn
- `SKIP LOCKED` — các row đã bị lock được bỏ qua (không wait)
- Nếu call 1 pick visit A, call 2 sẽ skip A và pick visit B
- Mỗi bác sĩ nhận visit khác nhau (AC #5 verified)

---

#### 7.2.4 Danh sách visit với bộ lọc

**Mục đích:** Lấy danh sách visit của phòng khám hiện tại, hỗ trợ lọc theo status, doctor, ngày.

```sql
SELECT 
    v.id,
    v.clinic_id,
    v.patient_id,
    v.doctor_id,
    v.assigned_doctor_id,
    v.visit_number,
    v.visit_date,
    v.status,
    v.priority,
    v.chief_complaint,
    v.notes,
    v.is_follow_up,
    v.is_returning,
    v.cancel_reason,
    v.started_at,
    v.completed_at,
    v.cancelled_at,
    v.created_at,
    v.updated_at,
    v.created_by,
    v.updated_by,
    v.version,
    (SELECT COUNT(*) FROM visit 
     WHERE clinic_id = :clinic_id 
       AND is_deleted = FALSE
       AND (:status IS NULL OR status = :status)
       AND (:doctor_id IS NULL OR doctor_id = :doctor_id)
       AND (:visit_date IS NULL OR visit_date = :visit_date)
    ) AS total_count
FROM visit v
WHERE v.clinic_id = :clinic_id
  AND v.is_deleted = FALSE
  AND (:status IS NULL OR v.status = :status)
  AND (:doctor_id IS NULL OR v.doctor_id = :doctor_id)
  AND (:visit_date IS NULL OR v.visit_date = :visit_date)
ORDER BY v.created_at DESC
LIMIT :limit
OFFSET :skip;
```

**Điều kiện lọc:**

| Tham số | Cột tương ứng | Ghi chú |
|---------|--------------|--------|
| `clinic_id` | `v.clinic_id` | Bắt buộc, từ RLS |
| `status` | `v.status` | Optional, ví dụ: WAITING, IN_PROGRESS, ... |
| `doctor_id` | `v.doctor_id` | Optional, lọc theo bác sĩ phục vụ |
| `visit_date` | `v.visit_date` | Optional, lọc theo ngày khám |
| `limit` | — | Pagination limit (default 50, max 500) |
| `skip` | — | Pagination offset (default 0) |

---

## 8. Quy tắc nghiệp vụ

| Mã | Mô tả quy tắc | Hành vi khi vi phạm | Tham chiếu test |
|----|--------------|---------------------|-----------------|
| **BR-VISIT-001** | **State machine:** Visit chỉ được transition theo đúng luồng: WAITING → IN_PROGRESS → AWAITING_PAYMENT → COMPLETED (từ bất kỳ state nào có thể CANCEL, trừ COMPLETED không cancel được). Transition không hợp lệ bị reject. | HTTP 409 Conflict (InvalidStateTransitionError) | `test_invalid_waiting_to_completed_returns_409`, `test_visit_lifecycle_with_cancel_at_each_state` |
| **BR-VISIT-002** | **Visit number duy nhất:** visit_number có format `YYYYMMDD-NNN` (ví dụ 20260428-001), duy nhất trong mỗi (clinic_id, visit_date). Mỗi ngày reset về 001, độc lập per clinic. | Unique constraint violation nếu insert trùng (không thể xảy ra do `fn_next_visit_number` serialized) | `test_create_visit_returns_201_with_correct_format`, `test_visit_numbers_independent_per_clinic`, `test_visit_numbers_reset_per_date` |
| **BR-VISIT-003** | **COMPLETED immutable:** Visit ở trạng thái COMPLETED không được revert về bất kỳ trạng thái nào (start, complete, cancel, mark-paid đều bị reject). | HTTP 409 Conflict | `test_completed_visit_cannot_revert`, `test_cancel_completed_visit_returns_409` |
| **BR-VISIT-004** | **Call-next priority:** Khi call-next, visit được ưu tiên theo thứ tự: 1) assigned_doctor_id = calling_doctor, 2) assigned_doctor_id IS NULL, 3) assigned_doctor_id = other doctors. Nếu priority bằng nhau, ưu tiên visit cũ hơn (created_at sớm nhất). | Nếu logic không đúng, visit sai thứ tự sẽ được pick (kiểm soát trong code, không phải lỗi HTTP) | `test_five_concurrent_call_next_no_double_assign` |
| **BR-VISIT-005** | **Cancel reason bắt buộc:** Khi cancel visit, `cancel_reason` phải được cung cấp, ít nhất 3 ký tự, không được rỗng trắng (chỉ spaces). | HTTP 422 Unprocessable Entity (ValidationError) | `test_cancel_requires_reason`, validation in `visit_schemas.py` |
| **BR-VISIT-006** | **Permission gate:** Hủy visit (cancel) yêu cầu `visit.cancel` (chỉ admin, doctor); Đánh dấu thanh toán (mark-paid) yêu cầu `payment.receive` (chỉ admin, receptionist). Ngoài những user này không được phép. | HTTP 403 Forbidden | `test_cancel_requires_visit_cancel_permission`, `test_mark_paid_requires_payment_receive_permission` |
| **BR-VISIT-007** | **Tenant isolation:** Mỗi phòng khám chỉ nhìn thấy visit của mình. Row-level security (RLS) enforcement trên bảng `visit` và `visit_number_counter`. Cross-clinic read bị deny. | RLS policy: visit WHERE clinic_id = current_clinic_id (implicit, không HTTP 403 mà nhìn không thấy row) | `test_visits_rls.py` (8 tests) |
| **BR-VISIT-008** | **Soft delete:** Visit có cột `is_deleted` boolean. Query visit chỉ bao gồm `is_deleted = FALSE`. Soft-deleted visit không xuất hiện trong queue hay danh sách. | Soft-deleted visit trả về 404 nếu GET/{id} | `test_get_soft_deleted_visit_returns_404` |

---

## 9. Xử lý lỗi

### 9.1 Các mã HTTP phổ biến

| Mã HTTP | Tình huống xảy ra | Thông báo mẫu | Ghi chú |
|---------|-------------------|--------------|--------|
| **200 OK** | Thành công (GET, PATCH, POST hành động) | `{ "id": "...", "status": "..." }` | Trả về VisitResponse |
| **201 Created** | Tạo visit thành công | `{ "id": "...", "status": "WAITING" }` | Trả về VisitResponse |
| **400 Bad Request** | Clinic ID thiếu trong context | `"clinic_id required"` | Check context headers |
| **401 Unauthorized** | Token không hợp lệ hoặc hết hạn | `"Not authenticated"` | Check Authorization header |
| **403 Forbidden** | Thiếu quyền (permission check fail) | `"Permission denied: visit.write"` | Check user role + seeded permissions |
| **404 Not Found** | Visit/Patient không tồn tại | `"Visit not found"` hoặc `"Patient not found"` | Check ID tồn tại + RLS |
| **409 Conflict** | State transition không hợp lệ | `"Cannot transition from IN_PROGRESS to COMPLETED with different doctor"` hoặc `"Cannot cancel from COMPLETED"` | Check current status |
| **422 Unprocessable Entity** | Dữ liệu không hợp lệ (validation) | `"cancel_reason must be at least 3 characters"` | Check schema validation |
| **500 Internal Server Error** | Lỗi hệ thống (DB, ...) | `"Internal server error"` | Check logs |

### 9.2 Error Matrix chi tiết per endpoint

| Endpoint | 404 Case | 409 Case | 422 Case | 403 Case |
|----------|----------|----------|----------|----------|
| GET /visits/{id} | Visit không tồn tại hoặc soft-deleted | — | — | Thiếu visit.read |
| POST /visits | Patient ID không tồn tại* | — | Priority > 100 | Thiếu visit.write |
| POST /visits/{id}/start | Visit không tồn tại | Status ≠ WAITING | — | Thiếu visit.write |
| POST /visits/{id}/complete | Visit không tồn tại | Status ≠ IN_PROGRESS | — | Thiếu visit.write |
| POST /visits/{id}/cancel | Visit không tồn tại | Status = COMPLETED | cancel_reason < 3 chars | Thiếu visit.cancel |
| POST /visits/{id}/mark-paid | Visit không tồn tại | Status ≠ AWAITING_PAYMENT | — | Thiếu payment.receive |
| POST /visits/call-next | — | — | — | Thiếu visit.write |

**Ghi chú:** `*` BUG-001 — hiện tại trả FK IntegrityError (unhandled), nên là HTTP 500 chứ không phải 404. Fix trong iteration tiếp theo.

---

## 10. Chiến lược cache

Không áp dụng — tính năng Queue truy vấn trực tiếp từ database (indexed query p95 = 13.6 ms). Không cần cache.

---

## 11. Ghi chú và lưu ý khi kiểm thử

### 11.1 Điểm quan trọng cần nắm

1. **State machine immutable**: COMPLETED và CANCELLED đều là terminal states — không thay đổi sau khi set. Các test phải verify rằng transition từ 2 state này bị reject (409).

2. **Race-safe call-next**: Sử dụng `FOR UPDATE SKIP LOCKED` để đảm bảo concurrent safety. Khi 5 bác sĩ gọi call-next cùng lúc với 5 visit WAITING, mỗi bác sĩ nhận visit khác nhau (không overlap, không ai nhận 2 lần).

3. **Visit number reset hàng ngày**: Mỗi ngày counter reset. Ngày hôm trước là 20260427-XXX, hôm nay lại bắt đầu từ 20260428-001. Per clinic độc lập.

4. **RLS enforcement**: Tất cả queries (GET, POST, PATCH) đều có RLS enforced. Cross-clinic user không thấy visit của clinic khác (nhìn không thấy row, không có lỗi 403).

5. **Permission granular**: Cancel cần `visit.cancel` (doctor/admin), Mark-paid cần `payment.receive` (receptionist/admin). Không phải chỉ `visit.write`.

6. **BUG-001 limitation**: `POST /visits` với `patient_id` không tồn tại hiện tại trả FK IntegrityError thay vì 404. Document để tester biết test này sẽ thấy exception.

### 11.2 Gợi ý dữ liệu kiểm thử

| Kịch bản | Giá trị đầu vào | Kết quả kỳ vọng |
|---------|----------------|----------------|
| **Tạo visit thành công** | Valid patient_id, clinic_id | 201 Created, status=WAITING, visit_number=YYYYMMDD-001 |
| **Visit number tăng liên tục** | Tạo 5 visit cùng ngày, cùng clinic | visit_number: -001, -002, -003, -004, -005 |
| **Reset per date** | Tạo visit ngày 27, rồi ngày 28 | Ngày 27: 20260427-001, Ngày 28: 20260428-001 |
| **Reset per clinic** | 2 clinics, cùng ngày | Clinic A: 20260428-001, Clinic B: 20260428-001 (độc lập) |
| **Invalid state transition** | POST /visits/{id}/start với status=IN_PROGRESS | 409 Conflict |
| **COMPLETED immutable** | POST /visits/{id}/cancel với status=COMPLETED | 409 Conflict |
| **Cancel reason validation** | cancel_reason = "OK" (2 chars) | 422 Validation error |
| **Cancel reason whitespace** | cancel_reason = "   " (3 spaces) | 422 Validation error |
| **Concurrent call-next** | 5 AsyncClient gọi call-next, 5 visit WAITING | Mỗi client 200, 5 visit_id khác nhau, 5 visit IN_PROGRESS |
| **Queue performance** | 50 visit WAITING, GET /visits/queue 100 lần | p95 < 50 ms (AC #6, observed 13.6 ms) |
| **RLS cross-clinic** | User clinic A GET /visits/{clinic_B_visit_id} | 404 (not 403, không leak existence) |

### 11.3 Hạn chế hiện tại

- **BUG-001**: `POST /visits` với non-existent `patient_id` trả FK IntegrityError (unhandled) thay vì 404. Fix đơn giản (add patient existence check trước flush). Deferred để tránh scope creep, sẽ fix trong TASK-008 hoặc Billing.
- **Appointment FK**: Bảng `appointment` chưa tồn tại (TASK-008). Column `visit.appointment_id` là plain UUID, chưa có FK constraint. Sẽ wire khi appointment table sẵn sàng.
- **Paid-at timestamp**: Bảng visit không có `paid_at` column. TASK-013 (Billing) có thể muốn thêm để audit trail đầy đủ.

### 11.4 Hướng phát triển

- **TASK-008 (Appointment)**: Wire `appointment_id` FK constraint.
- **TASK-013 (Billing)**: Tạo invoice khi visit → AWAITING_PAYMENT, mark-paid sẽ update invoice status.
- **Performance tuning**: Nếu queue query < 20 ms p95 không đủ, có thể cache queue 30s hoặc thêm read replicas.

---

## Phê duyệt

| Vai trò | Họ tên | Ngày | Ghi chú |
|---------|--------|------|--------|
| **Reviewer (Code)** | Code Review Agent | 2026-04-27 | APPROVED (iter 2) |
| **Tester** | Test Agent | 2026-04-28 | PASSED (117 tests, AC 1-6 all PASS) |
| **Documentation** | Documentation Agent | 2026-04-28 | Delivered |

---

**End of Document**
