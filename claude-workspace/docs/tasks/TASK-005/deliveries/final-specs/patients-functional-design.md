# Thiết Kế Chi Tiết Tính Năng: Quản Lý Bệnh Nhân

**Dự án:** Clinic CMS  
**Task:** TASK-005  
**Phiên bản:** 1.0  
**Ngày:** 2026-04-27  
**Người thực hiện:** Code Implementation Agent, Code Review Agent, Test Agent  
**Trạng thái:** Đã duyệt  
**Tài liệu liên quan:** `docs/clinic_management_system_design.md#6-module-patients`, `docs/clinic_management_business_analysis.md#4-module-patient--reception`

---

## Lịch sử thay đổi

| Phiên bản | Ngày | Nội dung thay đổi |
|-----------|------|-------------------|
| 1.0 | 2026-04-27 | Phiên bản đầu tiên — hoàn thành Phase 1-3 (Implement, Review, Test) |

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

Hệ thống quản lý hồ sơ bệnh nhân với đầy đủ chức năng CRUD, tìm kiếm nhanh theo SĐT/tên/mã bệnh nhân, quản lý mối quan hệ người giám hộ/thân nhân, gộp 2 hồ sơ trùng lặp (với khả năng hoàn tác trong 7 ngày), và ghi log tất cả các thao tác đọc để đảm bảo audit trail.

### 1.2 Phạm vi

**Bao gồm:**
- CRUD đầy đủ cho bệnh nhân (tạo, đọc, cập nhật, xóa mềm)
- Tìm kiếm nhanh bệnh nhân theo: số điện thoại (trigram GIN), tên đầy đủ (full-text + fuzzy), mã bệnh nhân (exact match)
- Sinh mã bệnh nhân tự động (`BN0001`, `BN0002`, ...) theo clinic, không tái sử dụng
- Quản lý quan hệ người thân (parent, spouse, child, other) — gọi là "guardian relationship"
- Gộp 2 hồ sơ bệnh nhân trùng với ghi log chi tiết những hàng dữ liệu nào được chuyển
- Hoàn tác gộp trong vòng 7 ngày, sau đó trả HTTP 410 Gone
- Ghi log tất cả thao tác đọc bệnh nhân (async, không chặn request)
- Cơ sở dữ liệu ngăn cách theo clinic (RLS)

**Không bao gồm:**
- Giao diện web (frontend xử lý ở TASK-006)
- Module Visit, Appointment, Prescription, Invoice (sẽ tích hợp lại ở các task khác)
- Tìm kiếm bệnh nhân qua ảnh hoặc sinh trắc học

### 1.3 Các bên liên quan

| Vai trò | Mô tả |
|---------|-------|
| **Lễ tân** | Tạo hồ sơ bệnh nhân, tìm kiếm bệnh nhân, cập nhật thông tin liên hệ |
| **Bác sĩ** | Xem thông tin bệnh nhân, xem lịch sử merge (audit trail) |
| **Quản trị viên clinic** | Gộp hồ sơ trùng, hoàn tác gộp, quản lý quan hệ thân nhân |
| **Hệ thống** | Ghi log mỗi lần đọc bệnh nhân (audit), kiểm soát quyền hạn theo role |

---

## 2. Luồng xử lý tổng thể

### 2.1 Sơ đồ luồng dữ liệu

```
┌─────────────────────────────────────────────────────────────────┐
│                      REST API Client                              │
│           (Ứng dụng web/mobile, gửi JWT token)                   │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                  FastAPI Routes Layer                             │
│   /patients, /patients/search, /patients/merge, /guardians, ...  │
│   ✓ Kiểm tra token JWT, lấy clinic_id và user_id                │
│   ✓ Kiểm tra permission (patient.read/write/delete/merge)        │
│   ✓ Lọc null byte trong query string                             │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│             Business Logic Service Layer                          │
│  patient_service, guardian_service, merge_service, audit_service │
│   ✓ Validation (DOB không ở tương lai, phone format, etc)        │
│   ✓ Xử lý business logic (gộp, hoàn tác, sinh mã bệnh nhân)     │
│   ✓ Ghi audit log async (nền)                                    │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│          Database Layer (PostgreSQL with RLS)                    │
│   patient, patient_relation, patient_merge_log, audit_log        │
│   ✓ Row-Level Security (clinic_id = jwt clinic_id)              │
│   ✓ Indexes: trigram (phone), GIN full-text (name), unique code  │
│   ✓ Check constraint: dob OR birth_year, nếu cả 2 thì year match│
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
          ┌────────────────────────────┐
          │   JSON Response to Client   │
          │   Status: 200/201/400/404...│
          └────────────────────────────┘
```

### 2.2 Các bước chính theo quy trình

#### **(A) Luồng Tạo Bệnh Nhân**

| Bước | Tên bước | Mô tả chi tiết |
|------|---------|----------------|
| 1 | Lấy clinic_id từ JWT | Client gửi request với Authorization header chứa JWT; middleware lấy `clinic_id` từ JWT payload |
| 2 | Kiểm tra quyền | API kiểm tra user có permission `patient.write` không; nếu không → 403 Forbidden |
| 3 | Validate input | Pydantic schema kiểm tra: full_name not null, phone format, gender enum, DOB not future, dob/birth_year logic, v.v. Nếu lỗi → 422 Unprocessable Entity |
| 4 | Gọi `create_patient()` service | Service nhận clinic_id, user_id, và các trường bệnh nhân; tính toán các warning (nếu tên+DOB trùng) |
| 5 | Sinh patient_code | Service gọi function `fn_next_patient_code(clinic_id)` để lấy mã BN tiếp theo (BN0001, BN0002, ...). Mã không tái sử dụng ngay cả khi merge/undo |
| 6 | Lưu vào database | INSERT hàng mới vào bảng `patient`; RLS tự động gán `clinic_id = jwt clinic_id` |
| 7 | Trả response | API trả 201 Created với PatientResponse (id, patient_code, all fields, warnings) |
| 8 | Ghi audit log (async) | Background task `audit_patient_read` ghi vào bảng `audit_log` (CREATE action) — không chặn response |

#### **(B) Luồng Tìm Kiếm Bệnh Nhân**

| Bước | Tên bước | Mô tả chi tiết |
|------|---------|----------------|
| 1 | Nhận query string `q` | Client gửi `GET /api/v1/patients/search?q=<query>&type=phone|name|code&limit=20` |
| 2 | Kiểm tra null byte | Route kiểm tra `if '\x00' in q` → nếu có → 400 Bad Request (ngăn chặn injection) |
| 3 | Kiểm tra quyền | Kiểm tra `patient.read` permission; nếu không → 403 |
| 4 | Dispatch theo loại tìm kiếm | Dựa trên `type` parameter, gọi branch khác nhau: |
|   | — `type=phone` | Gọi `search_by_phone(q)`: dùng trigram GIN index, similarity operator. Query: `WHERE clinic_id = ... AND phone % q ORDER BY similarity DESC LIMIT 20`. p95 = 46.9 ms @ 100k patient (PASS AC1) |
|   | — `type=name` | Gọi `search_by_name(q)`: dùng full-text + fuzzy. Unaccent q để match "nguyen van an" ↔ "Nguyễn Văn An". Query: `WHERE clinic_id = ... AND to_tsvector(...) @@ plainto_tsquery(...) LIMIT 20`. p95 = 180.5 ms (no AC threshold) |
|   | — `type=code` | Gọi `search_by_code(q)`: exact match. Query: `WHERE clinic_id = ... AND patient_code = q LIMIT 20` |
| 5 | RLS tự động lọc | Mỗi truy vấn đều có RLS filter: chỉ trả hàng có `clinic_id` = user's clinic |
| 6 | Trả response | API trả 200 OK với danh sách PatientResponse (tối đa 20 hàng) |
| 7 | Ghi audit log (async) | Background task ghi "READ" action cho mỗi bệnh nhân được trả về |

#### **(C) Luồng Gộp Hồ Sơ Trùng**

| Bước | Tên bước | Mô tả chi tiết |
|------|---------|----------------|
| 1 | Lấy yêu cầu gộp | Client gửi `POST /api/v1/patients/merge` với body `{"keep_id": "...", "drop_id": "...", "reason": "..."}` |
| 2 | Kiểm tra quyền | Kiểm tra `patient.merge` permission (chỉ admin); nếu không → 403 |
| 3 | Validate request | Schema kiểm tra `keep_id ≠ drop_id` (BUG-003 fix); nếu bằng → 422 |
| 4 | Gọi `merge()` service | Service nhận keep_id, drop_id, clinic_id |
| 5 | Tìm cả 2 bệnh nhân | `db.get(Patient, keep_id)` + `db.get(Patient, drop_id)` với RLS clinic_id filter; nếu không tìm → 404 |
| 6 | Kiểm tra cùng clinic | Nếu keep.clinic_id ≠ drop.clinic_id → 404 Not Found (chặn cross-tenant, không expose enumeration) |
| 7 | Ghi snapshot | Trước khi merge, capture snapshot của drop_patient vào `source_patient_data` (JSON) |
| 8 | Ghi manifest reassign | Cho mỗi bảng trong `RELATED_PATIENT_TABLES` registry (future: Visit, Appointment, Prescription, Invoice), capture list row IDs thực sự được di chuyển từ drop_id → keep_id. Lưu vào `source_patient_data['reassigned_refs']` |
| 9 | Soft-delete drop_patient | Set `is_deleted = true`, `deleted_at = now()`, `deleted_by = user_id` trên drop_patient |
| 10 | Ghi merge_log | INSERT vào `patient_merge_log`: drop_patient_id, keep_patient_id, source_patient_data (kèm manifest), merged_by, merged_at, undo_deadline = now() + 7 days |
| 11 | Trả response | 201 Created với `{merge_log_id, keep_id, drop_id, undo_deadline, message: "Merge successful"}` |
| 12 | Ghi audit log | Ghi "MERGE" action vào audit_log (async) |

#### **(D) Luồng Hoàn Tác Gộp Hồ Sơ**

| Bước | Tên bước | Mô tả chi tiết |
|------|---------|----------------|
| 1 | Lấy yêu cầu hoàn tác | Client gửi `POST /api/v1/patients/merge/{merge_id}/undo` |
| 2 | Kiểm tra quyền | Kiểm tra `patient.merge` permission |
| 3 | Tìm merge_log | `db.get(PatientMergeLog, merge_id)` với RLS filter |
| 4 | Kiểm tra clinic ownership | Nếu `merge_log.clinic_id ≠ jwt clinic_id` → 404 Not Found (BUG-004 fix, ngăn cross-tenant) |
| 5 | Kiểm tra deadline | Nếu `now() > merge_log.undo_deadline` → 410 Gone "Undo deadline passed" |
| 6 | Kiểm tra chưa hoàn tác | Nếu `merge_log.undone = true` → 409 Conflict "Already undone" |
| 7 | Restore drop_patient | Set `is_deleted = false`, `deleted_at = null`, `deleted_by = null` trên drop_patient |
| 8 | Restore relations | Dùng `source_patient_data['reassigned_refs']` manifest, issue `UPDATE ... WHERE id = ANY(reassigned_row_ids) SET patient_id = drop_id` cho các hàng được di chuyển. Rows gốc của keep_patient không bị động |
| 9 | Cập nhật merge_log | Set `undone = true`, `undone_at = now()`, `undone_by = user_id` |
| 10 | Trả response | 200 OK với `{merge_log_id, keep_id, drop_id, undo_deadline, message: "Merge undone. Both patient records are now active."}` |
| 11 | Ghi audit log | Ghi "UNDO_MERGE" action (async) |

#### **(E) Luồng Thêm Quan Hệ Thân Nhân (Guardian)**

| Bước | Tên bước | Mô tả chi tiết |
|------|---------|----------------|
| 1 | Lấy yêu cầu | Client gửi `POST /api/v1/patients/{id}/guardians` với body `{"guardian_patient_id": "...", "relation_type": "parent|spouse|child|other", "is_primary_contact": bool}` |
| 2 | Kiểm tra quyền | Kiểm tra `patient.write` permission |
| 3 | Kiểm tra bệnh nhân | Tìm patient với id={id}; RLS filter clinic; nếu không → 404 |
| 4 | Kiểm tra guardian | Tìm patient với id=guardian_patient_id; phải ở cùng clinic |
| 5 | Kiểm tra trùng | Nếu đã có relation từ id → guardian_patient_id → 409 Conflict hoặc silent update (tùy design) |
| 6 | Tạo patient_relation | INSERT vào `patient_relation`: patient_id, guardian_patient_id, relation_type, is_primary_contact, clinic_id |
| 7 | Trả response | 201 Created với PatientRelationResponse |

### 2.3 Sơ đồ luồng chi tiết: Gộp → Hoàn Tác → Gộp lại (edge case)

```
Thời điểm T=0:
  Patient P1 (keep), P2 (drop)

T=0: Gộp P1 ← P2
  → merge_log_1.id = M1, undo_deadline = T+7 days
  → P2.is_deleted = true
  → P1 vẫn sống

T=3 days: Hoàn tác M1
  → P2.is_deleted = false (restore)
  → merge_log_1.undone = true
  → Cả P1, P2 giờ đều sống

T=3 days + 5 mins: Gộp lại P1 ← P2 (lần 2)
  → merge_log_2.id = M2, undo_deadline = T+7 days (từ lúc gộp lần 2)
  → P2.is_deleted = true lại
  → M1.undone = true (không bị động)
  → Hoàn tác M1 lần 2 sẽ FAIL (410 Gone) vì deadline đã qua (từ lúc gộp lần 1)

T=3 days + 5 mins + 2 days: Hoàn tác M2
  → P2.is_deleted = false (restore)
  → merge_log_2.undone = true
  → Cả P1, P2 lại sống
```

---

## 3. Nguồn dữ liệu đầu vào

Dữ liệu bệnh nhân chỉ đến từ người dùng qua REST API (không có queue, file import, batch job). Các yêu cầu đến từ:

1. **REST API body** (JSON): Thông tin bệnh nhân từ form tạo/cập nhật, gộp request, guardian relationship
2. **JWT context** (từ middleware): `clinic_id` và `user_id` (lấy từ access token)
3. **Query parameter**: Chuỗi tìm kiếm `q`, loại tìm kiếm `type`, limit, skip

Không có message queue, file import, hay hệ thống bên ngoài gửi dữ liệu vào.

---

## 4. Danh sách API

Tất cả API đều yêu cầu xác thực qua header:
```
Authorization: Bearer {token}
```

**Đường dẫn gốc (Base Path):** `/api/v1`

| STT | Phương thức | Đường dẫn | Permission | Mô tả tóm tắt |
|-----|------------|-----------|----------|--------------|
| 1 | GET | `/patients` | patient.read | Liệt kê bệnh nhân (phân trang) |
| 2 | POST | `/patients` | patient.write | Tạo bệnh nhân mới |
| 3 | GET | `/patients/search` | patient.read | Tìm kiếm theo phone/name/code |
| 4 | GET | `/patients/{id}` | patient.read | Lấy chi tiết 1 bệnh nhân |
| 5 | PATCH | `/patients/{id}` | patient.write | Cập nhật thông tin bệnh nhân |
| 6 | DELETE | `/patients/{id}` | patient.delete | Xóa mềm bệnh nhân |
| 7 | POST | `/patients/{id}/guardians` | patient.write | Thêm quan hệ thân nhân |
| 8 | GET | `/patients/{id}/guardians` | patient.read | Liệt kê các quan hệ (guardian/thân nhân) của 1 bệnh nhân |
| 9 | DELETE | `/patients/guardians/{rel_id}` | patient.write | Xóa mối quan hệ |
| 10 | POST | `/patients/merge` | patient.merge | Gộp 2 hồ sơ bệnh nhân |
| 11 | POST | `/patients/merge/{merge_id}/undo` | patient.merge | Hoàn tác gộp (trong vòng 7 ngày) |

---

## 5. Chi tiết từng API

### 5.1 Liệt kê bệnh nhân (List Patients)

#### Thông tin chung

| Thuộc tính | Giá trị |
|------------|--------|
| **Đường dẫn** | `GET /api/v1/patients` |
| **Mô tả** | Liệt kê danh sách bệnh nhân thuộc clinic của user, hỗ trợ phân trang (skip/limit) |
| **Xác thực** | Bắt buộc; permission `patient.read` |

#### Tham số đầu vào

| Tham số | Kiểu | Bắt buộc | Mô tả | Giá trị mặc định |
|---------|------|---------|-------|-----------------|
| `skip` | Integer | Không | Số hàng bỏ qua từ đầu | 0 |
| `limit` | Integer | Không | Số hàng trả về (tối đa 200) | 50 |

#### Quy trình xử lý

| Bước | Mô tả |
|------|-------|
| 1 | Kiểm tra JWT token valid; lấy clinic_id |
| 2 | Kiểm tra permission `patient.read` |
| 3 | Truy vấn `SELECT * FROM patient WHERE clinic_id = :clinic_id AND NOT is_deleted ORDER BY created_at DESC LIMIT :limit OFFSET :skip` |
| 4 | RLS tự động lọc (chỉ hàng của clinic này) |
| 5 | Trả danh sách PatientResponse + tổng số hàng |

#### Kết quả trả về

**Thành công (200 OK):**

```json
{
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "clinic_id": "550e8400-e29b-41d4-a716-446655440002",
      "patient_code": "BN0001",
      "full_name": "Nguyễn Văn An",
      "date_of_birth": "1990-05-15",
      "birth_year": 1990,
      "gender": "male",
      "phone": "0912345678",
      "email": "an@example.com",
      "id_number": null,
      "address_line": "123 Đường Lê Lợi",
      "ward": "Phường 1",
      "district": "Q.1",
      "province": "TP. HCM",
      "blood_type": "O+",
      "allergies": "Cephalosporin",
      "chronic_conditions": "Tiểu đường",
      "occupation": "Kỹ sư",
      "referral_source": "Đặc cách",
      "notes": "Bệnh nhân ưa thích bác sĩ A",
      "created_at": "2026-04-27T10:00:00Z",
      "updated_at": "2026-04-27T10:00:00Z",
      "is_deleted": false
    }
  ],
  "total": 150,
  "cursor": null
}
```

| Trường | Kiểu | Mô tả ý nghĩa |
|--------|------|-------------|
| `id` | UUID | ID duy nhất của bệnh nhân |
| `patient_code` | String | Mã bệnh nhân định danh trong clinic (BN0001, BN0002, ...) |
| `full_name` | String | Tên đầy đủ bệnh nhân |
| `date_of_birth` | Date | Ngày sinh (null nếu chỉ có birth_year) |
| `birth_year` | Integer | Năm sinh (fallback nếu không có ngày chính xác) |
| `gender` | String | Giới tính (male/female/other) |
| `phone` | String | Số điện thoại 10-11 chữ số |
| `allergies` | String | Dị ứng (text tự do) |
| `chronic_conditions` | String | Bệnh mãn tính (text tự do) |
| `total` | Integer | Tổng số bệnh nhân (không áp dụng limit/skip) |

---

### 5.2 Tạo bệnh nhân (Create Patient)

#### Thông tin chung

| Thuộc tính | Giá trị |
|------------|--------|
| **Đường dẫn** | `POST /api/v1/patients` |
| **Mô tả** | Tạo hồ sơ bệnh nhân mới; auto-sinh patient_code; cảnh báo nếu tên+DOB trùng nhưng vẫn tạo |
| **Xác thực** | Bắt buộc; permission `patient.write` |

#### Tham số đầu vào

| Tham số | Kiểu | Bắt buộc | Mô tả | Ghi chú |
|---------|------|---------|-------|---------|
| `full_name` | String | Có | Tên đầy đủ (1-200 ký tự) | — |
| `gender` | String | Có | Giới tính (male/female/other) | Enum, không case-sensitive |
| `date_of_birth` | Date | Không | Ngày sinh (format: YYYY-MM-DD) | Không được ở tương lai (BUG-002 fix) |
| `birth_year` | Integer | Không | Năm sinh (1900-2200) | Nếu cả 2 có → `year(date_of_birth)` phải = `birth_year` |
| `phone` | String | Không | SĐT (10-11 chữ số, bắt đầu 0) | Format: `0[0-9]{9,10}` (VN format) |
| `email` | String | Không | Email (tối đa 200 ký tự) | Không validate format email (chỉ length) |
| `id_number` | String | Không | CCCD/CMND (tối đa 20 ký tự) | Loại trừ khỏi audit log (`__audit_exclude__`) |
| `address_line` | String | Không | Địa chỉ cụ thể (tối đa 500 ký tự) | — |
| `ward`, `district`, `province` | String | Không | Phường, quận, tỉnh thành (100 ký tự) | — |
| `blood_type` | String | Không | Nhóm máu (tối đa 5 ký tự, ví dụ: O+, AB-) | — |
| `allergies` | String | Không | Dị ứng (text tự do) | — |
| `chronic_conditions` | String | Không | Bệnh mãn tính (text tự do) | — |
| `occupation` | String | Không | Nghề nghiệp (100 ký tự) | — |
| `referral_source` | String | Không | Nguồn chỉ định (100 ký tự) | — |
| `notes` | String | Không | Ghi chú tự do | — |

**Giá trị hợp lệ của `gender`:**

| Giá trị | Ý nghĩa |
|---------|---------|
| `male` | Nam |
| `female` | Nữ |
| `other` | Khác |

**Giá trị hợp lệ của `relation_type` (nếu có guardian relationship):**

| Giá trị | Ý nghĩa |
|---------|---------|
| `parent` | Cha/mẹ |
| `spouse` | Vợ/chồng |
| `child` | Con cái |
| `other` | Khác |

#### Quy trình xử lý

| Bước | Mô tả |
|------|-------|
| 1 | Kiểm tra token, clinic_id, user_id |
| 2 | Kiểm tra permission `patient.write` |
| 3 | Validate body: Pydantic schema kiểm tra tất cả rule (full_name not null, phone format, gender enum, DOB not future, dob/birth_year logic, etc.) |
| 4 | Gọi `patient_service.create_patient()` |
| 5 | Service kiểm tra: có bệnh nhân nào có `full_name` + `date_of_birth` trùng không? Nếu có → thêm warning vào response |
| 6 | Service gọi `fn_next_patient_code(clinic_id)` để sinh patient_code |
| 7 | Service INSERT bệnh nhân mới vào bảng `patient` |
| 8 | Service trả response + warnings |
| 9 | Route trả 201 Created |
| 10 | Background task ghi audit log "CREATE" action (async, không chặn) |

#### Kết quả trả về

**Thành công (201 Created):**

```json
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "clinic_id": "550e8400-e29b-41d4-a716-446655440002",
    "patient_code": "BN0001",
    "full_name": "Nguyễn Văn An",
    "date_of_birth": "1990-05-15",
    "birth_year": 1990,
    "gender": "male",
    "phone": "0912345678",
    "email": "an@example.com",
    "id_number": null,
    "address_line": "123 Đường Lê Lợi",
    "ward": "Phương 1",
    "district": "Q.1",
    "province": "TP. HCM",
    "blood_type": "O+",
    "allergies": "Cephalosporin",
    "chronic_conditions": "Tiểu đường",
    "occupation": "Kỹ sư",
    "referral_source": "Đặc cách",
    "notes": "Bệnh nhân ưa thích bác sĩ A",
    "created_at": "2026-04-27T10:00:00Z",
    "updated_at": "2026-04-27T10:00:00Z",
    "is_deleted": false
  },
  "warnings": [
    "A patient with the same full_name and date_of_birth already exists in this clinic (ID: ...)"
  ]
}
```

| Trường | Kiểu | Mô tả |
|--------|------|-------|
| `data` | PatientResponse | Chi tiết bệnh nhân vừa tạo (bao gồm patient_code) |
| `warnings` | Array[String] | Danh sách cảnh báo (ví dụ: trùng tên+DOB); không block tạo |

**Lỗi:**

| HTTP Status | Trường hợp |
|-------------|-----------|
| 400 | Query string chứa null byte (`\x00`), hoặc input không hợp lệ (vd: phone format sai, gender không phải enum) |
| 401 | Token không hợp lệ hoặc hết hạn |
| 403 | User không có permission `patient.write` |
| 422 | Validation error (vd: `date_of_birth` ở tương lai, `birth_year` không match `date_of_birth.year`, `dob` + `birth_year` cùng null) |

---

### 5.3 Tìm kiếm bệnh nhân (Search Patients)

#### Thông tin chung

| Thuộc tính | Giá trị |
|------------|--------|
| **Đường dẫn** | `GET /api/v1/patients/search` |
| **Mô tả** | Tìm kiếm nhanh bệnh nhân theo SĐT (trigram), tên (full-text + fuzzy), hoặc mã BN (exact). Support 3 loại tìm kiếm khác nhau tối ưu hóa cho từng use case |
| **Xác thực** | Bắt buộc; permission `patient.read` |

#### Tham số đầu vào

| Tham số | Kiểu | Bắt buộc | Mô tả | Giá trị mặc định |
|---------|------|---------|-------|-----------------|
| `q` | String | Có | Chuỗi tìm kiếm (1-200 ký tự) | — |
| `type` | String | Không | Loại tìm kiếm (phone/name/code) | name |
| `limit` | Integer | Không | Số hàng trả về (1-100) | 20 |

**Giá trị hợp lệ của `type`:**

| Giá trị | Ý nghĩa | Cơ chế |
|---------|---------|--------|
| `phone` | Tìm theo SĐT | Trigram similarity (p95=46.9ms @ 100k) — fast exact/prefix match |
| `name` | Tìm theo tên | Full-text search + fuzzy matching (p95=180.5ms) — unaccent để match tên Việt |
| `code` | Tìm theo mã BN | Exact match — instant (~0.5ms) |

#### Quy trình xử lý

| Bước | Mô tả |
|------|-------|
| 1 | Kiểm tra JWT, clinic_id |
| 2 | Kiểm tra permission `patient.read` |
| 3 | Validate `q`: Nếu `'\x00' in q` → 400 Bad Request (BUG-001 fix) |
| 4 | Dispatch theo `type`: |
|   | **type=phone:** | `SELECT * FROM patient WHERE clinic_id = :clinic_id AND NOT is_deleted AND phone % q ORDER BY similarity(phone, q) DESC LIMIT :limit` (dùng gix_patient_phone_trgm GIN index) |
|   | **type=name:** | `SELECT * FROM patient WHERE clinic_id = :clinic_id AND NOT is_deleted AND to_tsvector('simple', immutable_unaccent(full_name)) @@ plainto_tsquery('simple', immutable_unaccent(q)) LIMIT :limit` (dùng gix_patient_name_search GIN index) |
|   | **type=code:** | `SELECT * FROM patient WHERE clinic_id = :clinic_id AND NOT is_deleted AND patient_code = q LIMIT :limit` (dùng uq_patient_clinic_code unique index) |
| 5 | RLS tự động lọc result |
| 6 | Trả danh sách PatientResponse |
| 7 | Background task ghi audit log "READ" action cho mỗi bệnh nhân trả về (async) |

#### Kết quả trả về

**Thành công (200 OK):**

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "clinic_id": "550e8400-e29b-41d4-a716-446655440002",
    "patient_code": "BN0001",
    "full_name": "Nguyễn Văn An",
    "date_of_birth": "1990-05-15",
    "birth_year": 1990,
    "gender": "male",
    "phone": "0912345678",
    "email": "an@example.com",
    "address_line": "123 Đường Lê Lợi",
    "created_at": "2026-04-27T10:00:00Z",
    "updated_at": "2026-04-27T10:00:00Z",
    "is_deleted": false
  }
]
```

**Trường hợp không tìm thấy (200 OK, danh sách rỗng):**

```json
[]
```

---

### 5.4 Lấy chi tiết bệnh nhân (Get Patient)

#### Thông tin chung

| Thuộc tính | Giá trị |
|------------|--------|
| **Đường dẫn** | `GET /api/v1/patients/{id}` |
| **Mô tả** | Lấy toàn bộ thông tin chi tiết 1 bệnh nhân theo ID |
| **Xác thực** | Bắt buộc; permission `patient.read` |

#### Tham số đầu vào

| Tham số | Kiểu | Bắt buộc | Mô tả |
|---------|------|---------|-------|
| `id` | UUID | Có | ID của bệnh nhân (path parameter) |

#### Quy trình xử lý

| Bước | Mô tả |
|------|-------|
| 1 | Kiểm tra JWT, clinic_id |
| 2 | Kiểm tra permission `patient.read` |
| 3 | Truy vấn `SELECT * FROM patient WHERE id = :id` + RLS filter (clinic_id = user's clinic) |
| 4 | Nếu không tìm → 404 Not Found |
| 5 | Trả PatientResponse |
| 6 | Background task ghi audit log "READ" action (async) |

#### Kết quả trả về

**Thành công (200 OK):** Như PatientResponse (see 5.1)

**Lỗi:**

| HTTP Status | Trường hợp |
|-------------|-----------|
| 404 | Bệnh nhân không tồn tại hoặc thuộc clinic khác (RLS chặn cross-clinic read) |

---

### 5.5 Cập nhật bệnh nhân (Update Patient)

#### Thông tin chung

| Thuộc tính | Giá trị |
|------------|--------|
| **Đường dẫn** | `PATCH /api/v1/patients/{id}` |
| **Mô tả** | Cập nhật thông tin bệnh nhân (partial update — chỉ fields được truyền mới được cập nhật) |
| **Xác thực** | Bắt buộc; permission `patient.write` |

#### Tham số đầu vào

Giống như Create Patient, nhưng tất cả fields tùy chọn (Partial Update). Ví dụ: có thể chỉ cập nhật `phone` mà không cần `full_name`.

#### Quy trình xử lý

| Bước | Mô tả |
|------|-------|
| 1 | Validate JWT, clinic_id, permission `patient.write` |
| 2 | Tìm bệnh nhân; nếu không → 404 |
| 3 | Validate input: tất cả validators giống Create (phone format, DOB not future, etc.) |
| 4 | UPDATE các fields được truyền |
| 5 | Trả PatientResponse (version mới) |
| 6 | Ghi audit log "UPDATE" action (async) |

---

### 5.6 Xóa mềm bệnh nhân (Delete Patient)

#### Thông tin chung

| Thuộc tính | Giá trị |
|------------|--------|
| **Đường dẫn** | `DELETE /api/v1/patients/{id}` |
| **Mô tả** | Xóa mềm bệnh nhân (đặt `is_deleted=true`, không xóa khỏi DB) |
| **Xác thực** | Bắt buộc; permission `patient.delete` |

#### Quy trình xử lý

| Bước | Mô tả |
|------|-------|
| 1 | Validate JWT, permission `patient.delete` |
| 2 | Tìm bệnh nhân; nếu không → 404 |
| 3 | SET `is_deleted=true`, `deleted_at=now()`, `deleted_by=user_id` |
| 4 | Trả 204 No Content hoặc 200 OK với response |
| 5 | Ghi audit log "DELETE" action (async) |

---

### 5.7 Thêm quan hệ thân nhân / Người giám hộ (Add Guardian)

#### Thông tin chung

| Thuộc tính | Giá trị |
|------------|--------|
| **Đường dẫn** | `POST /api/v1/patients/{id}/guardians` |
| **Mô tả** | Thêm mối quan hệ (parent/spouse/child/other) — một bệnh nhân có thể có nhiều quan hệ |
| **Xác thực** | Bắt buộc; permission `patient.write` |

#### Tham số đầu vào

| Tham số | Kiểu | Bắt buộc | Mô tả |
|---------|------|---------|-------|
| `guardian_patient_id` | UUID | Có | ID của bệnh nhân là người giám hộ/thân nhân |
| `relation_type` | String | Có | Loại quan hệ (parent/spouse/child/other) |
| `is_primary_contact` | Boolean | Không | Đánh dấu là liên hệ chính (mặc định false) |

#### Quy trình xử lý

| Bước | Mô tả |
|------|-------|
| 1 | Validate JWT, permission `patient.write` |
| 2 | Tìm patient (id) + guardian (guardian_patient_id); cả 2 phải ở cùng clinic; nếu không → 404 |
| 3 | Kiểm tra trùng: Có quan hệ từ patient → guardian_patient_id rồi không? Nếu có có thể update hoặc return 409 |
| 4 | INSERT vào `patient_relation` |
| 5 | Trả 201 Created với PatientRelationResponse |
| 6 | Ghi audit log (async) |

#### Kết quả trả về

**Thành công (201 Created):**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440003",
  "clinic_id": "550e8400-e29b-41d4-a716-446655440002",
  "patient_id": "550e8400-e29b-41d4-a716-446655440001",
  "guardian_patient_id": "550e8400-e29b-41d4-a716-446655440004",
  "relation_type": "parent",
  "is_primary_contact": true,
  "created_at": "2026-04-27T11:00:00Z"
}
```

---

### 5.8 Liệt kê quan hệ thân nhân (List Guardians)

#### Thông tin chung

| Thuộc tính | Giá trị |
|------------|--------|
| **Đường dẫn** | `GET /api/v1/patients/{id}/guardians` |
| **Mô tả** | Liệt kê toàn bộ quan hệ (thân nhân/người giám hộ) của 1 bệnh nhân |
| **Xác thực** | Bắt buộc; permission `patient.read` |

#### Quy trình xử lý

| Bước | Mô tả |
|------|-------|
| 1 | Validate JWT, permission `patient.read` |
| 2 | Truy vấn `SELECT * FROM patient_relation WHERE patient_id = :id AND clinic_id = :clinic_id AND NOT is_deleted` |
| 3 | RLS tự động lọc |
| 4 | Trả danh sách PatientRelationResponse |

#### Kết quả trả về

**Thành công (200 OK):**

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440003",
    "clinic_id": "550e8400-e29b-41d4-a716-446655440002",
    "patient_id": "550e8400-e29b-41d4-a716-446655440001",
    "guardian_patient_id": "550e8400-e29b-41d4-a716-446655440004",
    "relation_type": "parent",
    "is_primary_contact": true,
    "created_at": "2026-04-27T11:00:00Z"
  }
]
```

---

### 5.9 Xóa quan hệ thân nhân (Delete Relation)

#### Thông tin chung

| Thuộc tính | Giá trị |
|------------|--------|
| **Đường dẫn** | `DELETE /api/v1/patients/guardians/{rel_id}` |
| **Mô tả** | Xóa mềm 1 mối quan hệ (đặt `is_deleted=true`) |
| **Xác thực** | Bắt buộc; permission `patient.write` |

#### Quy trình xử lý

| Bước | Mô tả |
|------|-------|
| 1 | Validate JWT, permission `patient.write` |
| 2 | Tìm patient_relation (rel_id); nếu không → 404 |
| 3 | SET `is_deleted=true`, `deleted_at=now()`, `deleted_by=user_id` |
| 4 | Trả 204 No Content |
| 5 | Ghi audit log (async) |

---

### 5.10 Gộp 2 hồ sơ bệnh nhân (Merge Patients)

#### Thông tin chung

| Thuộc tính | Giá trị |
|------------|--------|
| **Đường dẫn** | `POST /api/v1/patients/merge` |
| **Mô tả** | Gộp hồ sơ drop_id vào keep_id; soft-delete drop_id; lưu manifest để hoàn tác. Chỉ admin với permission `patient.merge` |
| **Xác thực** | Bắt buộc; permission `patient.merge` |

#### Tham số đầu vào

| Tham số | Kiểu | Bắt buộc | Mô tả |
|---------|------|---------|-------|
| `keep_id` | UUID | Có | ID bệnh nhân được giữ lại (sẽ nhận toàn bộ dữ liệu liên quan) |
| `drop_id` | UUID | Có | ID bệnh nhân bị gộp vào (sẽ bị soft-delete) |
| `reason` | String | Không | Lý do gộp (tối đa 1000 ký tự) |

#### Quy trình xử lý

| Bước | Mô tả |
|------|-------|
| 1 | Validate JWT, permission `patient.merge` |
| 2 | Validate request: `keep_id ≠ drop_id` (BUG-003 fix); nếu bằng → 422 Unprocessable Entity |
| 3 | Tìm cả 2 bệnh nhân; RLS clinic_id filter; nếu không tìm → 404 |
| 4 | Kiểm tra clinic: `keep.clinic_id == drop.clinic_id`; nếu khác → 404 (chặn cross-tenant, không expose enumeration) |
| 5 | Snapshot drop_patient data vào JSON object |
| 6 | Ghi manifest: Duyệt qua bảng `RELATED_PATIENT_TABLES` registry (future: Visit, Appointment, Prescription, Invoice), capture row IDs di chuyển từ drop_id → keep_id |
| 7 | Soft-delete drop_patient: `is_deleted=true`, `deleted_at=now()`, `deleted_by=user_id` |
| 8 | INSERT vào `patient_merge_log`: drop_patient_id, keep_patient_id, source_patient_data (kèm manifest), merged_by, merged_at=now(), undo_deadline=now()+7days |
| 9 | Trả 201 Created với PatientMergeResponse |
| 10 | Ghi audit log "MERGE" action (async) |

#### Kết quả trả về

**Thành công (201 Created):**

```json
{
  "merge_log_id": "550e8400-e29b-41d4-a716-446655440005",
  "keep_id": "550e8400-e29b-41d4-a716-446655440001",
  "drop_id": "550e8400-e29b-41d4-a716-446655440006",
  "undo_deadline": "2026-05-04T12:00:00Z",
  "message": "Merge successful. The drop_id patient has been soft-deleted. You can undo this merge within 7 days."
}
```

| Trường | Kiểu | Mô tả |
|--------|------|-------|
| `merge_log_id` | UUID | ID của merge_log để tham chiếu trong undo |
| `undo_deadline` | DateTime | Thời hạn cuối cùng để hoàn tác (now + 7 days) |

**Lỗi:**

| HTTP Status | Trường hợp |
|-------------|-----------|
| 404 | Một trong 2 bệnh nhân không tồn tại hoặc thuộc clinic khác (RLS chặn) |
| 422 | `keep_id == drop_id` (BUG-003 fix) |

---

### 5.11 Hoàn tác gộp hồ sơ (Undo Merge)

#### Thông tin chung

| Thuộc tính | Giá trị |
|------------|--------|
| **Đường dẫn** | `POST /api/v1/patients/merge/{merge_id}/undo` |
| **Mô tả** | Hoàn tác gộp: restore drop_patient (is_deleted=false), di chuyển lại các dữ liệu liên quan, đánh dấu merge_log.undone=true |
| **Xác thực** | Bắt buộc; permission `patient.merge` |

#### Tham số đầu vào

| Tham số | Kiểu | Bắt buộc | Mô tả |
|---------|------|---------|-------|
| `merge_id` | UUID | Có | ID của patient_merge_log cần hoàn tác (path parameter) |

#### Quy trình xử lý

| Bước | Mô tả |
|------|-------|
| 1 | Validate JWT, permission `patient.merge`, clinic_id |
| 2 | Tìm merge_log (merge_id) |
| 3 | Kiểm tra clinic ownership: `merge_log.clinic_id == jwt clinic_id` (BUG-004 fix); nếu khác → 404 (ngăn cross-tenant, không expose enumeration) |
| 4 | Kiểm tra deadline: Nếu `now() > merge_log.undo_deadline` → 410 Gone "Undo deadline passed" |
| 5 | Kiểm tra chưa hoàn tác: Nếu `merge_log.undone == true` → 409 Conflict "Already undone" |
| 6 | Restore drop_patient: `is_deleted=false`, `deleted_at=null`, `deleted_by=null` |
| 7 | Restore relations: Dùng manifest `merge_log.source_patient_data['reassigned_refs']`, issue UPDATE cho các hàng được di chuyển lúc merge; các hàng gốc của keep_patient không bị động |
| 8 | Cập nhật merge_log: `undone=true`, `undone_at=now()`, `undone_by=user_id` |
| 9 | Trả 200 OK với response |
| 10 | Ghi audit log "UNDO_MERGE" action (async) |

#### Kết quả trả về

**Thành công (200 OK):**

```json
{
  "merge_log_id": "550e8400-e29b-41d4-a716-446655440005",
  "keep_id": "550e8400-e29b-41d4-a716-446655440001",
  "drop_id": "550e8400-e29b-41d4-a716-446655440006",
  "undo_deadline": "2026-05-04T12:00:00Z",
  "message": "Merge undone successfully. Both patient records are now active."
}
```

**Lỗi:**

| HTTP Status | Trường hợp |
|-------------|-----------|
| 404 | Merge log không tồn tại hoặc thuộc clinic khác (BUG-004 fix) |
| 409 | Merge đã được hoàn tác trước đó (undone=true) |
| 410 | Hết hạn hoàn tác (now > undo_deadline) |

---

## 6. Cấu trúc cơ sở dữ liệu

### 6.1 Tổng quan các bảng

| Bảng | Mục đích |
|------|---------|
| `patient` | Lưu thông tin bệnh nhân (CRUD + soft-delete + audit) |
| `patient_relation` | Lưu quan hệ thân nhân (parent/spouse/child/other) |
| `patient_merge_log` | Lưu lịch sử gộp hồ sơ (merge + undo với 7-day window) |

### 6.2 Chi tiết bảng

#### Bảng: `patient`

**Mô tả:** Bảng chính lưu thông tin bệnh nhân toàn phần, hỗ trợ soft-delete, audit trail, và multi-tenant (RLS)

| Tên cột | Kiểu dữ liệu | Bắt buộc | Mô tả |
|---------|-------------|---------|-------|
| `id` | UUID | Có | Khóa chính, tự sinh |
| `clinic_id` | UUID | Có | Clinic sở hữu bệnh nhân (FK → clinic.id) |
| `patient_code` | VARCHAR(20) | Có | Mã bệnh nhân (BN0001, BN0002, ...) định danh trong clinic |
| `full_name` | VARCHAR(200) | Có | Tên đầy đủ (dùng cho full-text search) |
| `date_of_birth` | DATE | Không | Ngày sinh (có thể null nếu chỉ có birth_year) |
| `birth_year` | INT | Không | Năm sinh (1900-2200); fallback nếu không có ngày |
| `gender` | VARCHAR(10) | Có | Giới tính (male/female/other) |
| `phone` | VARCHAR(20) | Không | Số điện thoại VN (0912345678) — not unique |
| `email` | VARCHAR(200) | Không | Email — not unique |
| `id_number` | VARCHAR(20) | Không | CCCD/CMND — **loại trừ khỏi audit log** (`__audit_exclude__`) |
| `address_line` | VARCHAR(500) | Không | Địa chỉ cụ thể |
| `ward` | VARCHAR(100) | Không | Phường/xã |
| `district` | VARCHAR(100) | Không | Quận/huyện |
| `province` | VARCHAR(100) | Không | Tỉnh/thành phố |
| `blood_type` | VARCHAR(5) | Không | Nhóm máu (O+, AB-, etc.) |
| `allergies` | TEXT | Không | Dị ứng (text tự do) |
| `chronic_conditions` | TEXT | Không | Bệnh mãn tính (text tự do) |
| `occupation` | VARCHAR(100) | Không | Nghề nghiệp |
| `referral_source` | VARCHAR(100) | Không | Nguồn chỉ định |
| `notes` | TEXT | Không | Ghi chú tự do |
| `created_at` | TIMESTAMP | Có | Thời điểm tạo (server default: now()) |
| `updated_at` | TIMESTAMP | Có | Thời điểm cập nhật cuối (server default: now()) |
| `created_by` | UUID | Không | User tạo bệnh nhân |
| `updated_by` | UUID | Không | User cập nhật cuối |
| `is_deleted` | BOOLEAN | Có | Xóa mềm (mặc định false) |
| `deleted_at` | TIMESTAMP | Không | Thời điểm xóa |
| `deleted_by` | UUID | Không | User xóa |
| `version` | INT | Có | Optimistic locking version (mặc định 1) |

**Ràng buộc:**
- **Primary Key:** `pk_patient` on `id`
- **Foreign Key:** `fk_patient_clinic_id_clinic` on `clinic_id` → `clinic.id` (RESTRICT on delete)
- **Check Constraint:** `ck_patient_dob_or_birth_year` — `(date_of_birth IS NOT NULL OR birth_year IS NOT NULL) AND (date_of_birth IS NULL OR birth_year IS NULL OR EXTRACT(year FROM date_of_birth)::integer = birth_year)` — đảm bảo có ít nhất 1 trong 2 field DOB/birth_year, và nếu cả 2 có thì year phải match
- **Unique Partial:** `uq_patient_clinic_code` on `(clinic_id, patient_code)` WHERE NOT is_deleted — đảm bảo mã BN duy nhất per clinic (không count soft-deleted)
- **Indexes:**
  - `ix_patient_clinic_id` on `(clinic_id)`
  - `ix_patient_clinic_phone` on `(clinic_id, phone)` WHERE NOT is_deleted (phone search)
  - `gix_patient_name_search` GIN on `to_tsvector('simple', immutable_unaccent(full_name))` WHERE NOT is_deleted (full-text name search)
  - `gix_patient_phone_trgm` GIN on `phone gin_trgm_ops` WHERE NOT is_deleted (trigram phone match — p95=46.9ms)
  - `gix_patient_name_trgm` GIN on `full_name gin_trgm_ops` (fuzzy name match, no WHERE to support similarity())

**RLS (Row-Level Security):** Bảng có RLS bật; policy cho phép user của clinic A chỉ xem/edit bệnh nhân của clinic A

---

#### Bảng: `patient_relation`

**Mô tả:** Lưu quan hệ thân nhân (guardian/family) — 1 bệnh nhân có thể có nhiều quan hệ

| Tên cột | Kiểu dữ liệu | Bắt buộc | Mô tả |
|---------|-------------|---------|-------|
| `id` | UUID | Có | Khóa chính |
| `clinic_id` | UUID | Có | Clinic sở hữu (FK → clinic.id) |
| `patient_id` | UUID | Có | Bệnh nhân (FK → patient.id) |
| `guardian_patient_id` | UUID | Có | Người giám hộ/thân nhân (FK → patient.id) — có thể là bệnh nhân khác hoặc không |
| `relation_type` | VARCHAR(20) | Có | Loại quan hệ (parent/spouse/child/other) |
| `is_primary_contact` | BOOLEAN | Có | Đánh dấu liên hệ chính (mặc định false) |
| `created_at` | TIMESTAMP | Có | Thời điểm tạo |
| `updated_at` | TIMESTAMP | Có | Thời điểm cập nhật |
| `created_by` | UUID | Không | User tạo |
| `updated_by` | UUID | Không | User cập nhật |
| `is_deleted` | BOOLEAN | Có | Xóa mềm (mặc định false) |
| `deleted_at` | TIMESTAMP | Không | Thời điểm xóa |
| `deleted_by` | UUID | Không | User xóa |
| `version` | INT | Có | Optimistic locking version |

**Ràng buộc:**
- **Primary Key:** `pk_patient_relation` on `id`
- **Foreign Keys:** FK trên clinic_id, patient_id, guardian_patient_id → tương ứng (RESTRICT)
- **Indexes:** on `clinic_id`, `patient_id`, `guardian_patient_id`
- **RLS:** Mỗi user chỉ xem quan hệ của clinic mình

---

#### Bảng: `patient_merge_log`

**Mô tả:** Ghi lịch sử gộp hồ sơ; hỗ trợ hoàn tác trong 7 ngày

| Tên cột | Kiểu dữ liệu | Bắt buộc | Mô tả |
|---------|-------------|---------|-------|
| `id` | UUID | Có | Khóa chính |
| `clinic_id` | UUID | Có | Clinic sở hữu (FK → clinic.id) |
| `keep_patient_id` | UUID | Có | Bệnh nhân được giữ lại (FK → patient.id) |
| `drop_patient_id` | UUID | Có | Bệnh nhân bị gộp/xóa (FK → patient.id) |
| `source_patient_data` | JSONB | Có | Snapshot drop_patient (JSON) — bao gồm tất cả fields + manifest `reassigned_refs` (list row IDs di chuyển lúc merge) |
| `merged_by` | UUID | Có | User thực hiện gộp |
| `merged_at` | TIMESTAMP | Có | Thời điểm gộp (server default: now()) |
| `reason` | TEXT | Không | Lý do gộp |
| `undo_deadline` | TIMESTAMP | Có | Thời hạn hoàn tác (merged_at + 7 days) |
| `undone` | BOOLEAN | Có | Đã hoàn tác? (mặc định false) |
| `undone_at` | TIMESTAMP | Không | Thời điểm hoàn tác |
| `undone_by` | UUID | Không | User hoàn tác |
| `created_at`, `updated_at`, `is_deleted`, etc. | — | — | Các field audit tiêu chuẩn (dùng soft-delete nếu cần xóa lịch sử) |

**Ràng buộc:**
- **Primary Key:** on `id`
- **Indexes:** on `clinic_id`, `keep_patient_id`, `drop_patient_id`
- **RLS:** User chỉ xem merge_log của clinic mình

---

## 7. SQL tổng hợp và truy vấn dữ liệu

### 7.1 SQL tổng hợp / ghi dữ liệu

#### **7.1.1 Sinh mã bệnh nhân tự động: `fn_next_patient_code(clinic_id)`**

**Mục đích:** Trả mã bệnh nhân tiếp theo (`BN0001`, `BN0002`, ...) cho 1 clinic. Mã không tái sử dụng ngay cả khi merge/undo (M5 fix).

```sql
CREATE OR REPLACE FUNCTION fn_next_patient_code(clinic_id UUID)
  RETURNS VARCHAR(20)
  LANGUAGE SQL
  STABLE
  PARALLEL SAFE
AS $$
  SELECT CONCAT(
    'BN',
    LPAD(
      COALESCE(
        MAX(CAST(SUBSTRING(patient_code FROM 3) AS INTEGER)),
        0
      ) + 1,
      4,
      '0'
    )
  )
  FROM patient
  WHERE patient.clinic_id = $1
  -- Note: NOT is_deleted removed (M5 fix) — includes soft-deleted to prevent code reuse
$$;
```

**Giải thích:**
- `SUBSTRING(patient_code FROM 3)` lấy phần số sau "BN" (BN0001 → "0001")
- `CAST(...AS INTEGER)` chuyển "0001" → 1, "9999" → 9999 (không bị mắc kẹt ở "0001" nếu có "BN10000")
- `MAX(...)` tìm số lớn nhất, +1 để lấy mã tiếp theo
- `LPAD(..., 4, '0')` đệm bằng 0 để luôn có 4 chữ số (0001, 0002, ..., 10000)
- Nếu chưa có mã nào (MAX returns NULL) → COALESCE → 0 → mã đầu tiên là BN0001
- Duyệt **tất cả** hàng (kể soft-deleted) để ngăn tái sử dụng (M5)

---

#### **7.1.2 Hàm unaccent bất biến: `immutable_unaccent(text)`**

**Mục đích:** Wrapper IMMUTABLE xung quanh `unaccent()` để dùng trong index expression. Stock `unaccent()` là STABLE, PostgreSQL từ chối STABLE functions trong GIN index.

```sql
CREATE OR REPLACE FUNCTION immutable_unaccent(text)
  RETURNS TEXT
  LANGUAGE SQL
  IMMUTABLE
  STRICT
  PARALLEL SAFE
AS $$
  SELECT unaccent('public.unaccent', $1)
$$;
```

**Giải thích:**
- `unaccent('public.unaccent', text)` — xóa accents (ä → a, ứ → u, etc.)
- `IMMUTABLE` cho phép dùng trong index expression
- `STRICT` — nếu input NULL → output NULL (không tính toán)
- `PARALLEL SAFE` — có thể chạy song song

---

#### **7.1.3 Tạo bảng và soft-delete**

```sql
INSERT INTO patient (
  id, clinic_id, patient_code, full_name, gender, date_of_birth, birth_year,
  created_by, created_at, is_deleted
) VALUES (
  :id, :clinic_id, :patient_code, :full_name, :gender, :date_of_birth, :birth_year,
  :user_id, now(), false
)
RETURNING *;
```

**Soft-delete:**

```sql
UPDATE patient
SET is_deleted = true, deleted_at = now(), deleted_by = :user_id
WHERE id = :patient_id AND clinic_id = :clinic_id;
```

---

#### **7.1.4 Gộp hồ sơ: lưu merge_log + soft-delete drop_patient**

```sql
-- 1. Soft-delete drop_patient
UPDATE patient
SET is_deleted = true, deleted_at = now(), deleted_by = :user_id, version = version + 1
WHERE id = :drop_id AND clinic_id = :clinic_id;

-- 2. Ghi merge_log với manifest reassigned_refs
INSERT INTO patient_merge_log (
  id, clinic_id, keep_patient_id, drop_patient_id, source_patient_data,
  merged_by, merged_at, undo_deadline, reason
) VALUES (
  :merge_id, :clinic_id, :keep_id, :drop_id,
  jsonb_build_object(
    'patient_code', :drop_code,
    'full_name', :drop_name,
    'reassigned_refs', :manifest  -- manifest = {table: [list of row IDs moved]}
  ),
  :user_id, now(), now() + INTERVAL '7 days', :reason
);
```

**Giải thích:**
- Manifest `reassigned_refs` capture từng bảng và list row IDs thực sự di chuyển (M4 fix)
- Ví dụ: `{"table": "visit", "row_ids": [uuid1, uuid2, ...]}`
- Hoàn tác sẽ dùng manifest để chỉ restore những hàng thực sự được move

---

#### **7.1.5 Hoàn tác gộp: restore drop_patient + reverse reassignments**

```sql
-- 1. Restore drop_patient
UPDATE patient
SET is_deleted = false, deleted_at = null, deleted_by = null, version = version + 1
WHERE id = :drop_id AND clinic_id = :clinic_id;

-- 2. Restore patient_relation rows (ví dụ)
-- Dùng manifest từ merge_log.source_patient_data['reassigned_refs']
UPDATE patient_relation
SET patient_id = :drop_id
WHERE id = ANY(:reassigned_relation_row_ids::UUID[]);

-- 3. Đánh dấu merge_log.undone
UPDATE patient_merge_log
SET undone = true, undone_at = now(), undone_by = :user_id, version = version + 1
WHERE id = :merge_id;
```

---

### 7.2 SQL truy vấn báo cáo / lấy dữ liệu

#### **7.2.1 Tìm kiếm theo SĐT (trigram, p95=46.9ms @ 100k)**

**Mục đích:** Tìm nhanh bệnh nhân theo số điện thoại (prefix, partial match)

```sql
SELECT *
FROM patient
WHERE clinic_id = :clinic_id
  AND NOT is_deleted
  AND phone % :q  -- trigram similarity operator
ORDER BY similarity(phone, :q) DESC
LIMIT :limit;
```

**Điều kiện lọc:**

| Tham số | Cột tương ứng | Ghi chú |
|---------|--------------|--------|
| `:clinic_id` | `clinic_id` | Từ JWT context |
| `:q` | `phone` | Chuỗi tìm kiếm (ví dụ: "0912") |
| `:limit` | — | Tối đa 20 hàng |

**Index:** `gix_patient_phone_trgm` GIN on `phone gin_trgm_ops` WHERE NOT is_deleted

**Performance:** p95 = 46.9 ms @ 100k patients (PASS AC1 threshold 100ms)

---

#### **7.2.2 Tìm kiếm theo tên (full-text + fuzzy, p95=180.5ms)**

**Mục đích:** Tìm bệnh nhân theo tên với hỗ trợ tên Việt (unaccent), dịp các dấu — "nguyen van an" match "Nguyễn Văn An"

```sql
SELECT *
FROM patient
WHERE clinic_id = :clinic_id
  AND NOT is_deleted
  AND to_tsvector('simple', immutable_unaccent(full_name))
      @@ plainto_tsquery('simple', immutable_unaccent(:q))
LIMIT :limit;
```

**Giải thích:**
- `immutable_unaccent(full_name)` loại accents từ tên lưu (Nguyễn → Nguyen)
- `immutable_unaccent(:q)` loại accents từ chuỗi tìm (người dùng gõ "nguyen van an")
- `to_tsvector('simple', ...)` tạo token từ tên (không stemming, chỉ split by space)
- `plainto_tsquery('simple', ...)` tạo token từ query (xử lý đặc biệt: không fail trên apostrophe, dấu phẩy, etc. — M3 fix)
- `@@` là toán tử match full-text

**Index:** `gix_patient_name_search` GIN on `to_tsvector('simple', immutable_unaccent(full_name))` WHERE NOT is_deleted

**Performance:** p95 = 180.5 ms @ 100k patients (no AC threshold, informational)

---

#### **7.2.3 Tìm kiếm theo mã bệnh nhân (exact, ~0.5ms)**

**Mục đích:** Tìm exact match mã BN (ví dụ: "BN0001")

```sql
SELECT *
FROM patient
WHERE clinic_id = :clinic_id
  AND NOT is_deleted
  AND patient_code = :q
LIMIT :limit;
```

**Index:** `uq_patient_clinic_code` unique on `(clinic_id, patient_code)` WHERE NOT is_deleted

---

#### **7.2.4 List bệnh nhân với phân trang**

```sql
SELECT *
FROM patient
WHERE clinic_id = :clinic_id
  AND NOT is_deleted
ORDER BY created_at DESC
LIMIT :limit
OFFSET :skip;
```

---

#### **7.2.5 Get chi tiết 1 bệnh nhân**

```sql
SELECT *
FROM patient
WHERE id = :id
  AND clinic_id = :clinic_id;
```

**RLS tự động filter:** Nếu user thuộc clinic khác → truy vấn trả 0 hàng

---

#### **7.2.6 List quan hệ thân nhân của 1 bệnh nhân**

```sql
SELECT *
FROM patient_relation
WHERE patient_id = :patient_id
  AND clinic_id = :clinic_id
  AND NOT is_deleted
ORDER BY created_at DESC;
```

---

### 7.3 Logic tính toán tham số truy vấn

#### **Cách dispatch query string `q` theo `type`:**

| type | Xử lý q | Cơ chế lọc |
|------|---------|-----------|
| `phone` | Giữ nguyên (ví dụ: "0912") | Trigram similarity operator (%) |
| `name` | Unaccent (nếu người dùng gõ "nguyen") | Full-text + plainto_tsquery |
| `code` | Giữ nguyên (ví dụ: "BN0001") | Exact match (=) |

#### **Validation query string:**

```python
if "\x00" in q:
    raise HTTPException(status_code=400, detail="Query contains invalid characters")
# BUG-001 fix — null byte guard trước khi truyền DB
```

---

## 8. Quy tắc nghiệp vụ

| Mã | Mô tả quy tắc | Hành vi khi vi phạm | Tham chiếu test |
|----|--------------|---------------------|-----------------|
| BR-PAT-001 | Mã bệnh nhân (`patient_code`) có format `BN` + 4+ chữ số (BN0001, BN0002, ...), tự động sinh qua `fn_next_patient_code(clinic_id)`, duy nhất per clinic, không tái sử dụng ngay cả khi merge/undo (M5 fix) | Ứng dụng không thể tự chỉ định mã; nếu cố gắng → 422 Validation Error | test_create_patient_auto_generates_code, test_patient_code_not_reused_after_merge_and_undo_succeeds, test_fn_next_patient_code_numeric_ordering |
| BR-PAT-002 | Số điện thoại (phone) và tên đầy đủ + ngày sinh không bắt buộc phải duy nhất (cảnh báo cô lập). Nếu tạo bệnh nhân trùng tên+DOB → API trả `warnings: ["..."]` nhưng vẫn 201 Create | Không block tạo, chỉ cảnh báo | test_create_duplicate_name_dob_warns, test_create_patient_duplicate_phone_allowed |
| BR-PAT-003 | Phải có `date_of_birth` HOẶC `birth_year` (ít nhất 1); nếu có cả 2 → năm trong DOB phải = `birth_year` | Nếu cả 2 null → 422; nếu năm không match → 422 | test_create_patient_dob_or_birth_year_required, test_create_patient_dob_year_mismatch_rejects |
| BR-PAT-004 | `date_of_birth` không được ở tương lai (BUG-002 fix — field_validator trên Create + Update) | Nếu DOB > hôm nay → 422 | test_create_future_dob_returns_422, test_update_future_dob_returns_422 |
| BR-PAT-005 | `id_number` (CCCD/CMND) loại trừ khỏi audit log (`__audit_exclude__`) | Audit log không bao giờ record giá trị `id_number` | test_audit_log_excludes_id_number |
| BR-PAT-006 | Query string `q` không được chứa null byte (`\x00`) — ngăn injection (BUG-001 fix). Null byte được strip/reject trước khi truyền DB | Nếu `q` có `%00` → 400 Bad Request | test_search_null_byte_q_returns_400 |
| BR-MERGE-001 | Không được self-merge: `keep_id ≠ drop_id` (BUG-003 fix — model_validator trên PatientMergeRequest) | Nếu `keep_id == drop_id` → 422 Unprocessable Entity | test_merge_same_id_returns_422 |
| BR-MERGE-002 | Chỉ gộp bệnh nhân cùng clinic (đơn tenant). Nếu `keep.clinic_id ≠ drop.clinic_id` → 404 Not Found (chặn cross-tenant, không expose enumeration) | Cross-clinic merge → 404 | test_merge_different_clinic_returns_404 |
| BR-MERGE-003 | Manifest reassignment (`source_patient_data['reassigned_refs']`) capture list row IDs thực sự di chuyển từ drop_id → keep_id. Hoàn tác chỉ reverse những hàng đó, không động rows gốc của keep_patient (M4 fix) | Hoàn tác có thể restore phần đúng của dữ liệu liên quan; unit test verify từng bảng | test_undo_only_moves_manifested_rows, test_undo_does_not_reassign_keep_patient_own_relations |
| BR-MERGE-004 | Hoàn tác gộp chỉ được trong vòng 7 ngày từ lúc gộp. Sau deadline → 410 Gone | Nếu `now() > merge_log.undo_deadline` → 410 Gone | test_undo_merge_after_7_days_returns_410, test_undo_merge_at_deadline_boundary |
| BR-MERGE-005 | Hoàn tác bị hạn chế theo clinic ownership: user phải ở clinic giống merge_log.clinic_id (BUG-004 fix). Cross-clinic undo → 404 Not Found | Cross-clinic undo → 404 (prevent enumeration) | test_undo_merge_from_different_clinic_returns_404 |
| BR-MERGE-006 | Registry `RELATED_PATIENT_TABLES` (trong merge_service) là danh sách các bảng sẽ được di chuyển khi gộp. Hiện tại là placeholder (Visit, Appointment, Prescription, Invoice chưa tồn tại); future tasks (TASK-007/008/011/013) sẽ extend | Merge chỉ di chuyển các bảng đã register; tables mới phải được thêm vào registry | — (future) |

---

## 9. Xử lý lỗi

### 9.1 Các mã HTTP và tình huống

| HTTP Status | Mã lỗi nội bộ | Tình huống xảy ra | Thông báo trả về |
|------------|----------|----------|----------|
| **400** | INVALID_REQUEST | Query string chứa null byte; input format sai (vd: phone không phải VN format) | "Query contains invalid characters" hoặc "Phone must be a 10-digit Vietnamese number starting with 0" |
| **401** | UNAUTHORIZED | Token JWT không hợp lệ, hết hạn, hoặc không present | "Not authenticated" |
| **403** | FORBIDDEN | User không có permission cần thiết (`patient.read` / `write` / `delete` / `merge`) | "Insufficient permissions" |
| **404** | NOT_FOUND | Bệnh nhân/merge_log/relation không tồn tại; hoặc cross-clinic access (RLS chặn, route trả 404 để ngăn enumeration) | "Patient not found" hoặc "Merge log not found" |
| **409** | CONFLICT | Merge đã được hoàn tác trước đó (undone=true); hoặc attempt double-undo | "This merge has already been undone" |
| **410** | GONE | Hết hạn hoàn tác merge (now > undo_deadline) | "Undo deadline for this merge has passed" |
| **422** | UNPROCESSABLE_ENTITY | Pydantic validation error: full_name null, phone format sai, gender không phải enum, dob ở tương lai, dob+birth_year logic sai, keep_id==drop_id (self-merge), etc. | "Validation failed: [chi tiết từng field]" |
| **500** | INTERNAL_ERROR | Lỗi database, async task crash, etc. (hiếm gặp sau 117/117 tests pass) | "Internal server error" |

### 9.2 Định dạng phản hồi lỗi

**Standard error response (FastAPI default):**

```json
{
  "detail": "error message"
}
```

**Validation error response (422):**

```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "date_of_birth"],
      "msg": "Value error, date_of_birth cannot be in the future",
      "input": "2099-01-01"
    }
  ]
}
```

---

## 10. Chiến lược cache

**Không áp dụng** — tính năng này không sử dụng patient-level cache ở lớp API:
- **Frontend (TanStack Query):** Read cache ở client-side TanStack Query (TASK-006); không liên quan task này
- **Permission cache:** Kế thừa từ TASK-004 RBAC — Redis cache permission → TTL 60s
- **Database:** PostgreSQL native indexes (trigram, GIN full-text, unique) — không cần application-layer cache

Mỗi request đến API sẽ hit database; không có Redis cache cho patient data trong v1 backend.

---

## 11. Ghi chú và lưu ý khi kiểm thử

### 11.1 Các điểm quan trọng cần nắm

- **Mã bệnh nhân không tái sử dụng:** Ngay cả sau merge/undo, mã BN không được gán lại (M5 fix). Tester phải verify rằng `fn_next_patient_code` tăng liên tục (BN0001 → BN0002 → ... → BN10000, không bao giờ lùi).

- **RLS ngăn cross-clinic:** Clinic-A user không thể thấy patient của Clinic-B (ngay cả với biết ID). Database có RLS bật; API route cũng kiểm tra clinic_id từ JWT. Test DB có role `cms` với BYPASSRLS (tạo thuận tiện), production dùng `cms_app` role (no BYPASSRLS) — RLS thực sự áp dụng.

- **Merge + undo độc lập:** Có thể gộp → hoàn tác → gộp lại (lần 2 là merge mới khác). Deadline hoàn tác của merge #1 không bị ảnh hưởng bởi merge #2.

- **Audit log không record `id_number`:** CCCD/CMND không bao giờ xuất hiện trong audit_log (marked `__audit_exclude__`).

- **Tên + DOB trùng chỉ cảnh báo:** Có thể tạo 2 bệnh nhân với tên + DOB giống nhau (không unique constraint). API trả warnings nhưng vẫn 201.

- **Phone không unique:** Multiple bệnh nhân có thể cùng 1 SĐT (không block). Tìm kiếm theo phone sẽ trả danh sách.

- **Performance:** Phone search p95=46.9ms @ 100k patients (AC1 PASS). Fuzzy name p95=180.5ms (no threshold).

### 11.2 Gợi ý dữ liệu kiểm thử

| Kịch bản | Giá trị đầu vào | Kết quả kỳ vọng |
|---------|----------------|----------------|
| **Tạo bệnh nhân bình thường** | full_name="Nguyễn Văn An", gender="male", phone="0912345678", dob="1990-05-15" | 201 Created, patient_code="BN0001", warnings=[] |
| **Tạo trùng tên+DOB** | full_name="Nguyễn Văn An", dob="1990-05-15" (lần 2) | 201 Created, patient_code="BN0002", warnings=["A patient with the same full_name..."] |
| **DOB tương lai** | dob="2099-01-01" | 422, error: "date_of_birth cannot be in the future" |
| **Phone không hợp lệ** | phone="123" | 422, error: "Phone must be a 10-digit..." |
| **Chỉ birth_year, không DOB** | birth_year=1990 | 201 Created (valid, DOB not required if birth_year set) |
| **DOB + birth_year mismatch** | dob="1990-05-15", birth_year=1991 | 422, error: "birth_year must match..." |
| **Tìm kiếm theo phone** | q="0912", type="phone" | 200 OK, trả list bệnh nhân có phone match "0912" (prefix/partial) |
| **Tìm kiếm fuzzy tên** | q="nguyen van an", type="name" | 200 OK, trả "Nguyễn Văn An" (unaccent match) |
| **Tìm kiếm code** | q="BN0001", type="code" | 200 OK, trả bệnh nhân exact match |
| **Gộp: self-merge** | keep_id=P1, drop_id=P1 | 422, error: "keep_id and drop_id must be different" |
| **Gộp cross-clinic** | Clinic-A user gộp patient của Clinic-B | 404 Not Found (RLS + ownership check) |
| **Gộp → hoàn tác same day** | Merge lúc T=0, undo lúc T=1 day | 200 OK, hoàn tác thành công, drop_patient restore, is_deleted=false |
| **Hoàn tác sau 7 ngày** | Merge lúc T=0, undo lúc T=7 days + 1 second | 410 Gone, error: "Undo deadline has passed" |
| **Double undo** | Undo merge lần 1, sau đó undo lại merge_id cũ | 409 Conflict, error: "Already undone" |
| **Null byte trong search** | q="test%00name" (URL-encoded null byte) | 400 Bad Request, error: "Query contains invalid characters" |
| **Thêm guardian** | patient_id=P1, guardian_patient_id=P2, relation_type="parent" | 201 Created, patient_relation record tạo thành công |
| **Liệt kê guardian** | GET /patients/{id}/guardians | 200 OK, trả danh sách relations của patient |
| **Xóa relation** | DELETE /patients/guardians/{rel_id} | 204 No Content hoặc 200 OK, relation soft-deleted |

### 11.3 Hạn chế hiện tại

- **Visit/Appointment/Prescription/Invoice chưa tồn tại:** Merge registry có placeholder cho các bảng này (sẽ thêm ở TASK-007/008/011/013). Hiện tại merge chỉ soft-delete drop_patient, không di chuyển dữ liệu liên quan (vì chưa có).

- **Không có caching patient-level:** Mỗi request hit database; TanStack Query ở frontend sẽ handle read cache.

- **RLS ở test DB không như production:** Test DB `cms` role có BYPASSRLS=true (thuận tiện); production `cms_app` role có BYPASSRLS=false. RLS đã verify đúng với unit test dùng `_query_as_cms_app` helper.

- **Audit log là async:** Ghi log không chặn response HTTP. Nếu background task crash, log có thể mất (hiếm gặp sau testing, nhưng tester nên biết).

### 11.4 Hướng phát triển

- **TASK-007 (Visit):** Thêm `visit` table + FK patient_id → extend merge registry
- **TASK-008 (Appointment):** Thêm `appointment` table + extend merge registry
- **TASK-011 (Prescription):** Thêm `prescription` table + extend merge registry
- **TASK-013 (Invoice):** Thêm `invoice` table + extend merge registry
- **TASK-006 (Frontend):** Giao diện web dùng API này, TanStack Query cache
- **V2 optimizations:** Có thể thêm Redis cache cho permission (already in v1), patient metadata cache (future)

---

## Kết luận

Tính năng Quản Lý Bệnh Nhân (TASK-005) cung cấp backend API hoàn chỉnh cho CRUD bệnh nhân, tìm kiếm nhanh (trigram phone p95=46.9ms, fuzzy name p95=180.5ms), quản lý quan hệ thân nhân, và gộp hồ sơ với hoàn tác trong 7 ngày. Tất cả 11 endpoint đều có permission check, RLS tenant isolation, audit trail, và 117/117 test pass (94% coverage). Sẵn sàng cho tích hợp frontend ở TASK-006.

---

**Phê duyệt**

| Vai trò | Họ tên | Ngày |
|---------|--------|------|
| Code Review Agent | — | 2026-04-27 (APPROVED, iter 3) |
| Test Agent | — | 2026-04-27 (PASSED, 117/117) |
| Documentation Agent | — | 2026-04-27 |
