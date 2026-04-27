# Thiết kế chi tiết — Mô-đun RBAC (Role-Based Access Control)

**Dự án:** Clinic Management System  
**Task:** TASK-004  
**Ngày:** 2026-04-27  
**Phiên bản:** v1.0  
**Trạng thái:** Hoàn thành, 289/289 tests pass  
**Tài liệu liên quan:** BA §13 (Module Auth + RBAC), TASK-003 (Authentication)

---

## Lịch sử thay đổi

| Phiên bản | Ngày | Nội dung thay đổi |
|-----------|------|-------------------|
| 1.0 | 2026-04-27 | Phiên bản đầu tiên, hoàn thành iteration 2 |

---

## Mục lục

- [1. Tổng quan tính năng](#1-tổng-quan-tính-năng)
- [2. Phạm vi](#2-phạm-vi)
- [3. Luồng xử lý tổng thể](#3-luồng-xử-lý-tổng-thể)
- [4. Mô hình dữ liệu](#4-mô-hình-dữ-liệu)
- [5. Quy tắc nghiệp vụ](#5-quy-tắc-nghiệp-vụ)
- [6. Danh sách API](#6-danh-sách-api)
- [7. Chi tiết từng API](#7-chi-tiết-từng-api)
- [8. Phân quyền mặc định](#8-phân-quyền-mặc-định)
- [9. Bảo mật](#9-bảo-mật)
- [10. Chiến lược cache](#10-chiến-lược-cache)
- [11. Ghi chú khi kiểm thử](#11-ghi-chú-khi-kiểm-thử)

---

## 1. Tổng quan tính năng

### Mục đích

Mô-đun RBAC (Role-Based Access Control) cung cấp cơ chế phân quyền linh hoạt cho hệ thống quản lý phòng khám. Nó cho phép:

- Gán **vai trò** (Role) cho người dùng — mỗi role bao gồm một tập hợp các quyền (Permission)
- Một người dùng có thể sở hữu **nhiều role** đồng thời
- Cấp hoặc từ chối **quyền riêng lẻ** cho người dùng (extra_permission)
- Xác thực API request dựa trên quyền của người dùng (decorator `@require_permission`)
- Cache quyền hiệu lực trong JWT payload hoặc Redis để tối ưu hiệu suất

### Phạm vi v1

**Những gì có**:
- 5 hệ thống role được cấp sẵn: Admin, Doctor, Nurse, Pharmacist, Receptionist (không được chỉnh sửa)
- ~38 quyền từ catalog BA §13.5 (patient.read, visit.write, prescription.write, v.v.)
- Cơ sở dữ liệu: 5 bảng RBAC (role, permission, role_permission, user_role, user_extra_permission)
- 15 endpoints API quản lý Users, Roles, Permissions, User-Roles, Extra-Permissions
- Quyền hiệu lực = (∪ quyền từ các role) + extra_grants − extra_denies
- Cache quyền trong JWT hoặc Redis với TTL 5 phút
- Multi-role hỗ trợ đầy đủ (union của tất cả quyền)
- Bảo vệ system role: không cho phép xóa, chỉnh sửa, thêm/xóa quyền

**Những gì không có (phase sau)**:
- `pharmacy.dispense` guard (phòng khám dược chưa được xây dựng — AC3 defer)
- JWT inflation monitoring (m1 defer)
- Redis connection pooling (m2 defer)
- Clone system role endpoint (m4 scaffold, chờ onboarding)
- Multi-clinic per user (cấu hình sau)

### Các bên liên quan

| Vai trò | Mô tả |
|---------|-------|
| **Clinicians/Doctors** | Sử dụng ứng dụng, quyền được kiểm tra trên mỗi API request |
| **Admin/Manager** | Quản lý user, gán role, cấp quyền riêng lẻ |
| **DevOps** | Quản lý Redis dependency, JWT_SECRET, TTL cache |

---

## 2. Phạm vi

### Bao gồm

- User CRUD (quản lý người dùng trong phòng khám)
- Role CRUD (tạo custom role, quản lý quyền của role)
- Permission catalog (38 quyền từ BA, read-only)
- User-Role assignment/revocation (M2M)
- User extra-permission grant/deny (per-user override)
- Permission checking (decorator `@require_permission` trên API route)
- Cache invalidation (trên role/permission change)

### Không bao gồm

- AC3: `POST /pharmacy/dispense` guard → defer cho khi phòng khám dược được xây
- m1: JWT inflation monitoring → ADR sau (hiện ~700 bytes cho admin)
- m2: Redis connection pooling → optimize sau
- m4: `clone_system_role` endpoint → chờ TASK-onboarding
- Multi-clinic per user → phase sau

---

## 3. Luồng xử lý tổng thể

### 3.1 Luồng Login (từ TASK-003 Auth, tích hợp quyền)

```
┌──────────────────────────────┐
│ POST /auth/login             │
│ (username, password, clinic) │
└──────────────┬───────────────┘
               │
               ├─ Verify password (bcrypt) — từ TASK-003
               │
               ├─ Lấy user.clinic_id từ AUTH_SERVICE
               │
               ├─ Truy vấn quyền hiệu lực của user:
               │  • Lấy tất cả role của user (user_role)
               │  • ∪ quyền của mỗi role (role_permission)
               │  • ∪ extra_grants của user
               │  − extra_denies của user
               │
               ├─ Ghi quyền vào JWT payload (signed)
               │  {
               │    "sub": "<user_id>",
               │    "clinic_id": "<clinic_id>",
               │    "permissions": ["patient.read", "visit.write", ...],
               │    "roles": ["doctor"],
               │    "exp": <15 phút sau>
               │  }
               │
               ├─ Lưu vào Redis cache:
               │  KEY: "user:perms:{user_id}"
               │  VALUE: <set của permission codes>
               │  TTL: 5 phút
               │
               └─ Trả access_token + refresh_token
```

### 3.2 Luồng API Request (Permission Check)

```
┌──────────────────────────────┐
│ ANY REQUEST to /api/v1/...   │
└──────────────┬───────────────┘
               │
               ├─ Extract Authorization header
               │
               ├─ Verify JWT signature (secret)
               │
               ├─ Decode JWT → lấy permissions array
               │
               ├─ Check @require_permission decorator:
               │  • Yêu cầu permission có trong decoded JWT?
               │  • YES → 200 (tiếp tục)
               │  • NO  → 403 Forbidden
               │
               └─ Execute handler
```

### 3.3 Luồng Gán Role cho User

```
┌────────────────────────────────┐
│ POST /users/{id}/roles         │
│ Body: { "role_id": "..." }     │
└────────────────┬───────────────┘
                 │
                 ├─ Verify user.role has "role.manage"
                 │
                 ├─ Find Role by ID
                 │
                 ├─ Insert UserRole(user_id, role_id)
                 │
                 ├─ Invalidate Redis cache:
                 │  DEL "user:perms:{user_id}"
                 │
                 ├─ Audit log: "user_role_assigned"
                 │
                 └─ 201 Created
```

### 3.4 Luồng Cấp Extra Permission (Grant/Deny)

```
┌────────────────────────────────────────────────┐
│ POST /users/{id}/extra-permissions             │
│ Body: {                                        │
│   "permission_code": "invoice.void",           │
│   "type": "grant" | "deny",                    │
│   "reason": "Special approval from manager"    │
│ }                                              │
└────────────────┬───────────────────────────────┘
                 │
                 ├─ Verify user.role has "role.manage"
                 │
                 ├─ Find or create UserExtraPermission:
                 │  • Soft-delete old row (if exists) → is_deleted = TRUE
                 │  • INSERT new row (type="grant" | "deny")
                 │
                 ├─ Invalidate Redis cache:
                 │  DEL "user:perms:{user_id}"
                 │
                 ├─ Audit log: "extra_permission_created"
                 │
                 └─ 201 Created
```

---

## 4. Mô hình dữ liệu

### 4.1 Tổng quan các bảng

| Bảng | Mục đích |
|------|---------|
| `permission` | Catalog toàn hệ thống, ~38 quyền từ BA (immutable, seed) |
| `role` | Vai trò (admin, doctor, nurse, pharmacist, receptionist hệ thống + custom clinic-level) |
| `role_permission` | M2M: role ↔ permission (composite PK) |
| `user_role` | M2M: user ↔ role (RLS via user.clinic_id) |
| `user_extra_permission` | Override per-user (grant/deny quyền cụ thể) |

### 4.2 Chi tiết bảng

#### Bảng: `permission`

**Mô tả:** Catalog quyền toàn hệ thống. Seed sẵn từ BA §13.5. Không có RLS (tất cả user đều có thể đọc danh sách quyền).

| Tên cột | Kiểu dữ liệu | Bắt buộc | Mô tả |
|---------|------------|---------|-------|
| `code` | VARCHAR(100) | Có | PK — định danh quyền, e.g. `"patient.read"`, `"invoice.void"` |
| `description` | TEXT | Có | Mô tả chi tiết quyền |
| `category` | VARCHAR(50) | Không | Danh mục (patient, visit, vital, service, pharmacy, invoice, v.v.) |
| `created_at` | TIMESTAMP | Có | Thời điểm tạo |

#### Bảng: `role`

**Mô tả:** Vai trò trong hệ thống. 5 system roles (admin, doctor, nurse, pharmacist, receptionist) với `clinic_id = NULL` và `is_system = TRUE`. Có RLS theo clinic_id.

| Tên cột | Kiểu dữ liệu | Bắt buộc | Mô tả |
|---------|------------|---------|-------|
| `id` | UUID | Có | PK — sinh từ uuid5(NAMESPACE_OID, role_code) cho system roles |
| `clinic_id` | UUID | Không | FK → clinic. NULL = system role; NOT NULL = clinic-scoped custom role |
| `code` | VARCHAR(50) | Có | Định danh: "admin", "doctor", "custom_doctor_extended", v.v. |
| `name` | VARCHAR(200) | Có | Tên hiển thị, e.g. "Administrator", "Doctor", "Nurse" |
| `description` | TEXT | Không | Mô tả vai trò |
| `is_system` | BOOLEAN | Có | `TRUE` → không cho phép xóa/chỉnh sửa/quản lý quyền (403); `FALSE` → cho phép |
| `is_deleted` | BOOLEAN | Có | Soft-delete flag |
| `created_at`, `updated_at` | TIMESTAMP | Có | Thời gian tạo/cập nhật |
| `created_by`, `updated_by` | UUID | Không | Audit trail |
| `version` | INTEGER | Có | Optimistic lock |

**Unique constraint:** (clinic_id, code) khi clinic_id ≠ NULL (không được trùng lặp custom role per clinic); hoặc code khi clinic_id IS NULL (system roles).

#### Bảng: `role_permission`

**Mô tả:** M2M mapping giữa role và permission. Composite PK.

| Tên cột | Kiểu dữ liệu | Bắt buộc | Mô tả |
|---------|------------|---------|-------|
| `role_id` | UUID | Có | FK → role (cascade delete) |
| `permission_code` | VARCHAR(100) | Có | FK → permission |
| `granted_at` | TIMESTAMP | Có | Thời điểm gán quyền |
| `granted_by` | UUID | Không | Audit: ai đã gán |

**PK:** (role_id, permission_code)

#### Bảng: `user_role`

**Mô tả:** M2M mapping: user ↔ role. Hỗ trợ multi-role (một user có nhiều role). RLS via user.clinic_id.

| Tên cột | Kiểu dữ liệu | Bắt buộc | Mô tả |
|---------|------------|---------|-------|
| `id` | UUID | Có | PK |
| `user_id` | UUID | Có | FK → user |
| `role_id` | UUID | Có | FK → role |
| `assigned_at` | TIMESTAMP | Có | Thời điểm gán |
| `assigned_by` | UUID | Không | Audit: ai đã gán |
| `is_deleted` | BOOLEAN | Có | Soft-delete |

**Index:** ix_user_role_user_id (tối ưu query "lấy tất cả role của user")

#### Bảng: `user_extra_permission`

**Mô tả:** Per-user grant/deny override. Khi user đó có quyền từ role nhưng muốn từ chối, hoặc ngược lại. Soft-delete cũ trước khi thêm cái mới (idempotent).

| Tên cột | Kiểu dữ liệu | Bắt buộc | Mô tả |
|---------|------------|---------|-------|
| `id` | UUID | Có | PK |
| `user_id` | UUID | Có | FK → user |
| `permission_code` | VARCHAR(100) | Có | FK → permission |
| `type` | ENUM('grant', 'deny') | Có | grant = thêm quyền; deny = loại bỏ quyền |
| `reason` | TEXT | Không | Ghi chú lý do |
| `created_at` | TIMESTAMP | Có | Thời điểm tạo |
| `created_by` | UUID | Không | Audit |
| `is_deleted` | BOOLEAN | Có | Soft-delete (khi override bị hủy) |

**Unique constraint (partial):** (user_id, permission_code) WHERE NOT is_deleted (không cho phép 2 active row cho cùng user+permission)

### 4.3 ERD (Sơ đồ quan hệ)

```
┌─────────────────────┐
│      permission     │
├─────────────────────┤
│ code (PK)           │
│ description         │
│ category            │
│ created_at          │
└────────┬────────────┘
         │ 1:N
         │
         ├──────────────────┐
         │                  │
┌────────▼──────────────┐  ┌──────────────────────┐
│    role_permission    │  │      user_extra_     │
├───────────────────────┤  │    permission        │
│ role_id (PK, FK)      │  ├──────────────────────┤
│ permission_code (PK)  │  │ id (PK)              │
│ granted_at            │  │ user_id (FK)         │
│ granted_by            │  │ permission_code (FK) │
└────────┬──────────────┘  │ type (grant|deny)    │
         │                  │ reason               │
         │ M:N              │ created_at           │
┌────────▼──────────────┐  │ is_deleted           │
│       role            │  └──────────────────────┘
├───────────────────────┤
│ id (PK, UUID5)        │         │
│ clinic_id (FK)        │         │
│ code                  │         │ 1:N
│ name                  │         │
│ is_system             │         │
│ is_deleted            │         │
│ created_at/by         │         │
└────────┬──────────────┘         │
         │                         │
         │ M:N              ┌──────▼───────────────┐
         │            ├─────│    user              │
         │            │     ├──────────────────────┤
┌────────▼──────────────┐   │ id (PK)              │
│    user_role         │   │ clinic_id (FK)       │
├───────────────────────┤   │ username             │
│ id (PK)               │   │ email                │
│ user_id (FK)          │   │ password_hash        │
│ role_id (FK)          │   │ is_active            │
│ assigned_at           │   │ created_at/by        │
│ is_deleted            │   └──────────────────────┘
└───────────────────────┘
```

---

## 5. Quy tắc nghiệp vụ

| Mã | Mô tả | Hành vi khi vi phạm |
|----|-------|---------------------|
| BR-001 | Quyền hiệu lực = (∪ quyền của tất cả role) + extra_grants − extra_denies | Tính toán union chính xác, extra_deny có độ ưu tiên cao hơn role grant |
| BR-002 | System role (admin, doctor, nurse, pharmacist, receptionist) không được xóa, chỉnh sửa, thêm/xóa quyền | API trả về 403 Forbidden, message: "System roles are immutable; clone the role first" |
| BR-003 | Extra permission đơn lẻ (grant/deny) độc lập với role membership — không bị xóa khi user bị hủy role | Soft-delete user_extra_permission khi role bị revoke, nhưng row vẫn tồn tại với is_deleted=TRUE |
| BR-004 | Một user có thể sở hữu nhiều role đồng thời | Union tất cả quyền từ mỗi role, không có conflict |
| BR-005 | Khi thay đổi user role hoặc extra permission, Redis cache phải được invalidate ngay lập tức | DEL "user:perms:{user_id}" → request tiếp theo fetch từ DB và lưu cache mới |
| BR-006 | JWT token mang theo danh sách permission codes trong payload (để tránh query DB trên mỗi request) | Cập nhật JWT khi quyền thay đổi; TTL cache Redis 5 phút; fallback to DB nếu Redis miss |
| BR-007 | User anonymous (không có JWT valid) không được truy cập bất kỳ endpoint /api/v1 nào | 401 Unauthorized |
| BR-008 | Authenticated user nhưng không có permission yêu cầu → 403 Forbidden | Chi tiết: "You do not have permission: patient.read" |

---

## 6. Danh sách API

**Đường dẫn gốc:** `/api/v1`  
**Xác thực:** Bắt buộc JWT token trong header `Authorization: Bearer {token}` (ngoại trừ `/permissions` có ghi chú riêng)

| STT | Phương thức | Đường dẫn | Quyền yêu cầu | Mô tả |
|-----|-----------|----------|--------------|-------|
| 1 | GET | `/users` | user.manage | Danh sách user trong clinic |
| 2 | POST | `/users` | user.manage | Tạo user mới |
| 3 | GET | `/users/{id}` | user.manage | Chi tiết user |
| 4 | PATCH | `/users/{id}` | user.manage | Cập nhật user |
| 5 | DELETE | `/users/{id}` | user.manage | Xóa mềm user |
| 6 | GET | `/users/{id}/roles` | user.manage | Danh sách role của user |
| 7 | POST | `/users/{id}/roles` | role.manage | Gán role cho user |
| 8 | DELETE | `/users/{id}/roles/{role_id}` | role.manage | Hủy role từ user |
| 9 | GET | `/users/{id}/extra-permissions` | user.manage | Extra permission của user |
| 10 | POST | `/users/{id}/extra-permissions` | role.manage | Thêm extra permission (grant/deny) |
| 11 | DELETE | `/users/{id}/extra-permissions/{ep_id}` | role.manage | Xóa extra permission |
| 12 | GET | `/roles` | user.manage | Danh sách role |
| 13 | POST | `/roles` | role.manage | Tạo custom role |
| 14 | GET | `/roles/{id}` | user.manage | Chi tiết role |
| 15 | PATCH | `/roles/{id}` | role.manage | Cập nhật role (403 nếu system) |
| 16 | DELETE | `/roles/{id}` | role.manage | Xóa role (403 nếu system) |
| 17 | GET | `/roles/{id}/permissions` | user.manage | Danh sách quyền của role |
| 18 | POST | `/roles/{id}/permissions` | role.manage | Thêm quyền vào role (403 nếu system) |
| 19 | DELETE | `/roles/{id}/permissions/{code}` | role.manage | Xóa quyền từ role (403 nếu system) |
| 20 | GET | `/permissions` | Xác thực | Danh sách catalog quyền (read-only) |

---

## 7. Chi tiết từng API

### 7.1 Danh sách User — GET /users

#### Thông tin chung

| Thuộc tính | Giá trị |
|------------|--------|
| **Phương thức** | `GET /api/v1/users` |
| **Quyền yêu cầu** | `user.manage` |
| **Xác thực** | Bắt buộc |

#### Tham số đầu vào

| Tham số | Kiểu | Bắt buộc | Mô tả | Mặc định |
|--------|------|---------|-------|---------|
| `skip` | int | Không | Số bản ghi bỏ qua (offset) | 0 |
| `limit` | int | Không | Số bản ghi trả về (0-200) | 50 |

#### Kết quả trả về

**Thành công (200 OK):**

```json
{
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "clinic_id": "550e8400-e29b-41d4-a716-446655440001",
      "username": "dr_hung",
      "email": "hung@clinic.com",
      "is_active": true,
      "created_at": "2026-04-27T10:30:00Z"
    }
  ],
  "total": 42,
  "skip": 0,
  "limit": 50
}
```

**Lỗi (403 Forbidden):**

```json
{
  "code": "FORBIDDEN",
  "message": "You do not have permission: user.manage"
}
```

---

### 7.2 Tạo User — POST /users

#### Thông tin chung

| Thuộc tính | Giá trị |
|------------|--------|
| **Phương thức** | `POST /api/v1/users` |
| **Quyền yêu cầu** | `user.manage` |
| **Xác thực** | Bắt buộc |

#### Tham số đầu vào

```json
{
  "username": "dr_minh",
  "email": "minh@clinic.com",
  "password": "SecurePass123!",
  "full_name": "Dr. Minh Nguyen",
  "is_active": true
}
```

#### Kết quả trả về

**Thành công (201 Created):**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440002",
  "clinic_id": "550e8400-e29b-41d4-a716-446655440001",
  "username": "dr_minh",
  "email": "minh@clinic.com",
  "full_name": "Dr. Minh Nguyen",
  "is_active": true,
  "created_at": "2026-04-27T10:30:00Z"
}
```

**Lỗi (400 Bad Request — username trùng lặp):**

```json
{
  "code": "CONFLICT",
  "message": "User already exists"
}
```

---

### 7.3 Gán Role cho User — POST /users/{id}/roles

#### Thông tin chung

| Thuộc tính | Giá trị |
|------------|--------|
| **Phương thức** | `POST /api/v1/users/{id}/roles` |
| **Quyền yêu cầu** | `role.manage` |
| **Xác thực** | Bắt buộc |

#### Tham số đầu vào

```json
{
  "role_id": "1d156e88-38da-4ae8-bbec-d3ffff6eef6a"
}
```

#### Quy trình xử lý

1. Verify user.role có quyền `role.manage`
2. Tìm Role theo ID
3. Insert vào user_role(user_id, role_id)
4. DEL "user:perms:{user_id}" khỏi Redis (invalidate cache)
5. Ghi audit log: "user_role_assigned"
6. Trả 201

#### Kết quả trả về

**Thành công (201 Created):**

```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440002",
  "role_id": "1d156e88-38da-4ae8-bbec-d3ffff6eef6a",
  "role_code": "doctor",
  "role_name": "Doctor",
  "assigned_at": "2026-04-27T10:30:00Z"
}
```

**Lỗi (404 Not Found):**

```json
{
  "code": "NOT_FOUND",
  "message": "Role not found"
}
```

---

### 7.4 Thêm Extra Permission (Grant/Deny) — POST /users/{id}/extra-permissions

#### Thông tin chung

| Thuộc tính | Giá trị |
|------------|--------|
| **Phương thức** | `POST /api/v1/users/{id}/extra-permissions` |
| **Quyền yêu cầu** | `role.manage` |
| **Xác thực** | Bắt buộc |

#### Tham số đầu vào

```json
{
  "permission_code": "invoice.void",
  "type": "deny",
  "reason": "Manager revoked per audit findings on 2026-04-27"
}
```

**Giá trị hợp lệ của `type`:**

| Giá trị | Ý nghĩa |
|---------|---------|
| `grant` | Thêm quyền cho user (ngay cả khi role không có) |
| `deny` | Loại bỏ quyền từ user (ngay cả khi role có) |

#### Quy trình xử lý

1. Verify user.role có quyền `role.manage`
2. Tìm hoặc tạo UserExtraPermission:
   - Nếu (user_id, permission_code) đã có active row → soft-delete cũ (is_deleted=TRUE)
   - INSERT row mới với type và reason
   - Flush trước để satisfy partial unique index
3. DEL "user:perms:{user_id}" khỏi Redis
4. Ghi audit log: "extra_permission_created"
5. Trả 201

#### Kết quả trả về

**Thành công (201 Created):**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440003",
  "user_id": "550e8400-e29b-41d4-a716-446655440002",
  "permission_code": "invoice.void",
  "type": "deny",
  "reason": "Manager revoked per audit findings on 2026-04-27",
  "created_at": "2026-04-27T10:30:00Z"
}
```

*(Các endpoint khác (GET, PATCH, DELETE) được triển khai tương tự, chi tiết đầy đủ ở file `rbac-api-spec.md`)*

---

## 8. Phân quyền mặc định

### 8.1 Mapping System Roles → Permissions (BA §13.6)

5 system roles được seed với quyền mặc định theo bảng dưới. Mỗi ô "✓" có nghĩa role đó được cấp quyền; trống = không có.

| Permission | Admin | Doctor | Nurse | Pharmacist | Receptionist |
|-----------|-------|--------|-------|------------|--------------|
| patient.read | ✓ | ✓ | ✓ | ✓ | ✓ |
| patient.write | ✓ | ✓ | ✓ | | ✓ |
| patient.merge | ✓ | | | | |
| patient.delete | ✓ | | | | |
| visit.read | ✓ | ✓ | ✓ | | ✓ |
| visit.write | ✓ | ✓ | | | ✓ |
| visit.cancel | ✓ | ✓ | | | |
| vital.read | ✓ | ✓ | ✓ | | ✓ |
| vital.write | ✓ | ✓ | ✓ | | |
| vital.delete | ✓ | | | | |
| service.catalog.manage | ✓ | | | | |
| service.perform | ✓ | ✓ | ✓ | | ✓ |
| service.price_override | ✓ | ✓ | | | |
| prescription.write | ✓ | ✓ | | | |
| prescription.cancel | ✓ | ✓ | | | |
| prescription.print | ✓ | ✓ | ✓ | ✓ | ✓ |
| pharmacy.dispense | ✓ | | | ✓ | |
| pharmacy.substitute_batch | ✓ | | | ✓ | |
| pharmacy.adjust_stock | ✓ | | | ✓ | |
| inventory.read | ✓ | | | ✓ | |
| inventory.manage_catalog | ✓ | | | | |
| inventory.purchase_in | ✓ | | | ✓ | |
| inventory.adjust | ✓ | | | ✓ | |
| invoice.create | ✓ | ✓ | | | ✓ |
| invoice.modify | ✓ | ✓ | | | ✓ |
| invoice.void | ✓ | | | | |
| invoice.refund | ✓ | | | | |
| payment.receive | ✓ | | | | ✓ |
| shift.manage | ✓ | | | | |
| attendance.manage | ✓ | | | | |
| leave.approve | ✓ | | | | |
| user.manage | ✓ | | | | |
| role.manage | ✓ | | | | |
| report.view | ✓ | ✓ | | | |
| report.financial | ✓ | | | | |
| settings.clinic | ✓ | | | | |
| settings.vital_schema | ✓ | | | | |
| settings.service_catalog | ✓ | | | | |

**Tổng cộng:** 38 permissions × 5 roles

**Ghi chú:**
- Admin: 38/38 quyền (tất cả)
- Doctor: 18 quyền (khám bệnh, kê đơn, hóa đơn)
- Nurse: 11 quyền (chỉ số, hỗ trợ khám, dịch vụ)
- Pharmacist: 9 quyền (phòng khám dược, kho)
- Receptionist: 11 quyền (tiếp tân, hóa đơn, payment)

---

## 9. Bảo mật

### 9.1 RLS (Row Level Security)

- **role table:** RLS policy cho phép user xem system role (clinic_id IS NULL) hoặc clinic-scoped role của clinic của họ
- **user_role table:** RLS via user.clinic_id (user chỉ xem role assignment của user cùng clinic)
- **user_extra_permission table:** RLS via user.clinic_id
- **permission table:** Không có RLS (catalog toàn hệ thống, ai cũng có thể đọc)

### 9.2 System Role Immutability

5 system roles có flag `is_system = TRUE` và được bảo vệ:
- DELETE → 403 Forbidden
- PATCH (update) → 403 Forbidden
- POST `/roles/{id}/permissions` (thêm quyền) → 403 Forbidden
- DELETE `/roles/{id}/permissions/{code}` (xóa quyền) → 403 Forbidden

**Lý do:** System roles định nghĩa vai trò cơ bản cho tất cả phòng khám; không cho phép chỉnh sửa toàn cục.

**Giải pháp:** Nếu clinic muốn custom role, dùng `clone_system_role()` (scaffold, chờ TASK-onboarding) để tạo clinic-specific role.

### 9.3 JWT Signing & Verification

- **Algorithm:** HS256 (HMAC SHA-256)
- **Secret:** từ env var `JWT_SECRET` (do Auth module TASK-003 quản lý)
- **Signature verification:** Trên mỗi request (FastAPI dependency)
- **Payload:** Bao gồm `permissions` array (đã ký, không thể giả mạo)

### 9.4 Permission Checking

Decorator `@require_permission("code")` kiểm tra:
1. JWT token hợp lệ?
2. `permissions` array trong JWT chứa code yêu cầu?
3. Nếu không → 403 Forbidden (tư nhân không có quyền này)

---

## 10. Chiến lược cache

### 10.1 Mục đích

Tối ưu hiệu suất: không query database mỗi request để lấy quyền của user. Thay vào đó:
- Lưu quyền vào JWT payload → không cần Redis (stateless)
- Hoặc lưu vào Redis cache → tối ưu cho token refresh

### 10.2 Quy tắc lưu và xóa cache

| Nội dung cache | TTL | Điều kiện xóa |
|----------------|-----|---------------|
| `user:perms:{user_id}` (set permission codes) | 5 phút | Ngay lập tức khi user role hoặc extra permission thay đổi (DEL key) |

### 10.3 Cách tạo khóa cache

```
user:perms:{user_id}
```

**Ví dụ:** `user:perms:550e8400-e29b-41d4-a716-446655440002`

**Giá trị cached:** Redis SET chứa các permission code:
```
{
  "patient.read",
  "patient.write",
  "visit.read",
  "visit.write",
  "vital.read",
  "vital.write",
  ...
}
```

### 10.4 Fallback Strategy

- **Redis available:** Lấy từ cache (5 phút TTL)
- **Redis down/miss:** Query database trực tiếp (graceful degradation)
- **Token refresh:** auth_service cập nhật JWT payload với quyền mới từ DB

---

## 11. Ghi chú khi kiểm thử

### 11.1 Điểm quan trọng

- **Multi-role:** User có thể gán 2+ role cùng lúc; quyền = union tất cả role
- **Extra-perm idempotence:** POST `/users/{id}/extra-permissions` 2 lần với cùng body → 1 row trong DB, không duplicate
- **Cache invalidation:** Sau khi gán role, DEL cache ngay; request tiếp theo query DB
- **System role guard:** Không thể xóa hoặc chỉnh sửa quyền của system role → 403 error
- **JWT cache:** Admin user JWT ~700 bytes (38 permission codes) — chấp nhận được ở m1 defer

### 11.2 Gợi ý dữ liệu kiểm thử

| Kịch bản | Giá trị đầu vào | Kết quả kỳ vọng |
|---------|----------------|----------------|
| User bình thường (doctor) gọi /users (cần user.manage) | token doctor | 403 Forbidden |
| User admin gọi /users | token admin | 200 OK + danh sách |
| Gán role doctor cho user, rồi request API | POST /users/{id}/roles, body {"role_id":"..."} | 201 Created + cache invalidated |
| Extra-deny invoice.void dù role có quyền | POST /users/{id}/extra-permissions {"permission_code":"invoice.void","type":"deny"} | 201 Created + 403 khi request API |
| Delete system role admin | DELETE /roles/{id} (id=system admin) | 403 Forbidden ("System roles are immutable") |
| PATCH system role (update name) | PATCH /roles/{id} (system role) | 403 Forbidden |
| Danh sách permission (không cần role.manage) | GET /permissions | 200 OK (catalog read-only) |

### 11.3 Hạn chế hiện tại

- **AC3 defer:** Doctor role không có `pharmacy.dispense` (phòng khám dược chưa build) — sẽ test khi module ship
- **JWT inflation:** Admin ~700 bytes cho 38 permissions — chấp nhận; monitoring defer (m1)
- **Redis pool:** Mỗi call `_redis()` mở connection mới — acceptable; optimize later (m2)
- **`clone_system_role` unused:** Scaffolding sẵn, endpoint chưa; chờ TASK-onboarding (m4)

### 11.4 Hướng phát triển (phase sau)

- Multi-clinic per user (hiện 1-to-1 user-clinic)
- Permission bitmap thay vì array (khi catalog > 100 quyền)
- Redis connection pool (perf optimization)
- JWT inflation monitoring ADR
- `clone_system_role` endpoint + UI onboarding flow

---

## Tài liệu liên quan

- [BA §13 Module Auth + RBAC](../../../../docs/clinic_management_system_business_analysis.md)
- [TASK-003 Auth Functional Design](../../../TASK-003/deliveries/final-specs/auth-functional-design.md)
- [API Specification (chi tiết endpoint)](rbac-api-spec.md)
- [SQL Scripts (DDL + Seed)](../sql-scripts/)
- [Test Cases](../test-cases/rbac-test-cases.md)
- [Test Report](../test-reports/rbac-test-report.md)

---

**Phê duyệt**

| Vai trò | Họ tên | Ngày |
|---------|--------|------|
| Trưởng nhóm kỹ thuật | — | 2026-04-27 |
| Documentation Agent | Claude Code | 2026-04-27 |
