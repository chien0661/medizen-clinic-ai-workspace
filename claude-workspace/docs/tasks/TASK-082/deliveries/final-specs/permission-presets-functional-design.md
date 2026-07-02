# Thiết Kế Chi Tiết Tính Năng: Permission Preset — Cấu hình phân quyền đơn giản hóa

**Dự án:** Clinic CMS  
**Task:** TASK-082  
**Phiên bản:** 1.0  
**Ngày:** 2026-07-03  
**Người thực hiện:** Code Implementation Agent / Code Review Agent / Test Agent  
**Trạng thái:** Hoàn thành  
**Tài liệu liên quan:** TASK-004 (RBAC system), TASK-082 task brief, implementation-plan.md

---

## Lịch sử thay đổi

| Phiên bản | Ngày | Nội dung thay đổi |
|-----------|------|-------------------|
| 1.0 | 2026-07-03 | Phiên bản đầu tiên — hoàn tất sau giai đoạn kiểm thử |

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

Hệ thống phân quyền RBAC hiện tại của Clinic CMS có 38 quyền được tổ chức theo vai trò (system role: admin, doctor, nurse, pharmacist, receptionist, cashier, super_admin) kết hợp với cơ chế cho phép bổ sung quyền (`grant`) hoặc từ chối quyền (`deny`) dành riêng cho từng người dùng. Thiết kế này rất linh hoạt nhưng gây khó khăn cho các phòng khám nhỏ (chỉ có 1 bác sĩ vừa chẩn đoán vừa quản lý toàn bộ hệ thống).

**Permission Preset** là giải pháp đơn giản hóa: cho phép quản trị viên phòng khám **với một cú nhấp chuột** cấp cho một bác sĩ **đủ quyền** để vận hành toàn bộ hệ thống (tiếp nhận, khám, kê đơn, dược, thanh toán, báo cáo), mà không cần phải hiểu hoặc cấu hình từng quyền riêng lẻ. Tính năng này giữ nguyên ranh giới bảo mật: bác sĩ KHÔNG thể truy cập các quyền hệ thống/nền tảng (quản trị nền tảng, tạo/xóa phòng khám, siêu quản trị) và KHÔNG thể nhìn thấy dữ liệu của các phòng khám khác.

### 1.2 Phạm vi

**Bao gồm:**
- **Khái niệm Permission Preset**: Một bộ mã quyền có tên, có thể là hệ thống (được seed sẵn, không chỉnh sửa được) hoặc do phòng khám tạo (tùy chỉnh).
- **System Preset `small_clinic_doctor`**: Một preset được seed sẵn chứa đủ quyền vận hành (tất cả quyền TRỪ các quyền nền tảng như `system.manage`, `clinic.create/read/update/delete/list`).
- **Luồng 1-click cấp quyền**: Quản trị viên bấm nút "Cấp bác sĩ toàn quyền" → chọn tài khoản bác sĩ → hệ thống tự động tạo một role từ preset `small_clinic_doctor` và gán cho bác sĩ đó.
- **Giao diện cấu hình**: Trang quản lý preset và role, cho phép xem danh sách preset, tạo preset tùy chỉnh, áp preset vào một role có sẵn.
- **API mới**: 6 endpoint mới hỗ trợ thao tác CRUD trên preset và áp preset vào role.

**Không bao gồm:**
- Thay đổi các role hệ thống (admin, doctor, nurse, v.v.) — chúng vẫn là bất biến.
- Thay đổi thuật toán tính toán quyền hiệu dụng (`effective permissions`) — preset chỉ là cách tạo role và thiết lập quyền, không làm thay đổi logic cộng trừ quyền.
- Giao diện quản lý toàn bộ 38 quyền chi tiết (vẫn sử dụng ma trận quyền hiện có) — preset là lớp tiện lợi phía trên.

### 1.3 Các bên liên quan

| Vai trò | Mô tả |
|---------|-------|
| **Quản trị viên phòng khám** | Người dùng có quyền `role.manage`, sử dụng tính năng để cấp quyền cho bác sĩ/nhân viên một cách nhanh chóng. |
| **Bác sĩ / Nhân viên phòng khám** | Người dùng cuối nhận được quyền từ preset, có thể vận hành hệ thống theo phạm vi đó. |
| **Hệ thống RBAC** | Backend RBAC (TASK-004) quản lý vai trò, quyền, hiệu lực quyền; cache permission qua Redis (TTL 5 phút) + JWT (TTL 15 phút). |

---

## 2. Luồng xử lý tổng thể

### 2.1 Sơ đồ luồng dữ liệu

```
[Quản trị viên phòng khám]
      │
      ├─► Nút "Cấp bác sĩ toàn quyền" (1-click)
      │   └─► Chọn tài khoản bác sĩ
      │       └─► POST /roles/from-preset (small_clinic_doctor + assign_user_id)
      │           └─► Backend: Tạo clinic role từ preset
      │               └─► Gán role cho bác sĩ
      │                   └─► Invalidate cache permission của bác sĩ
      │                       └─► Toastify thành công
      │                           └─► Bác sĩ truy cập được tất cả module vận hành
      │
      ├─► Nút "Tạo role từ preset" (modal)
      │   └─► Chọn preset + tên role
      │       └─► POST /roles/from-preset
      │
      └─► Nút "Áp preset vào role" (quick action)
          └─► Chọn role + preset
              └─► POST /roles/{id}/apply-preset
                  └─► Backend: Thay thế quyền của role từ preset

[Quản lý preset]
      │
      ├─► GET /permission-presets — Liệt kê system + clinic preset
      ├─► POST /permission-presets — Tạo preset tùy chỉnh (tự strip quyền nền tảng)
      ├─► PATCH /permission-presets/{id} — Cập nhật preset (không cho sửa system preset)
      └─► DELETE /permission-presets/{id} — Xóa preset tùy chỉnh
```

### 2.2 Mô tả các bước chính

| Bước | Tên bước | Mô tả chi tiết |
|------|---------|----------------|
| 1 | **Quản trị viên mở giao diện Roles** | Truy cập trang /admin/roles, ghi dó các hành động nhanh (quick actions) cho role và nút toolbar "Cấp bác sĩ toàn quyền". |
| 2 | **Chọn mô hình cấp quyền** | Chọn 1 trong 3 lựa chọn: (a) nút "Cấp bác sĩ toàn quyền" → chọn BS, (b) nút "Tạo role từ preset" → đặt tên role, (c) hành động "Áp preset" trên role có sẵn. |
| 3 | **Gửi yêu cầu API** | FE gửi POST/PATCH request tới backend với thông tin preset + role/user. |
| 4 | **Backend xác thực quyền** | Kiểm tra token và quyền `role.manage` — từ chối nếu không có quyền (403). |
| 5 | **Kiểm tra clinic context** | Đảm bảo có `clinic_id` hoạt động trong token — từ chối nếu không (400). |
| 6 | **Lấy preset từ database** | Tìm preset theo `code` — bối ưu tiên clinic-scoped, sau đó system preset. |
| 7 | **Lọc quyền, loại bỏ quyền nền tảng** | Tính toán tập quyền vận hành (operational set) = tất cả quyền − quyền nền tảng. Giao tập hợp này với quyền trong preset → `safe_codes`. Điều này đảm bảo KHÔNG quyền nào từ blacklist (`system.manage`, `clinic.*`) có thể vào role clinic. |
| 8 | **Tạo/cập nhật role** | (Nếu `create_role_from_preset`) Tạo clinic-scoped role mới với `display_name` dễ nhìn. (Nếu `apply_preset_to_role`) Cập nhật quyền của role có sẵn. |
| 9 | **Gán role cho user (tùy chọn)** | Nếu API request có `assign_user_id`, gọi luôn `assign_role` để gán role mới cho user đó. |
| 10 | **Invalidate cache** | Xóa khóa Redis `user:perms:{user_id}` của user vừa nhận role → lần truy cập tiếp theo sẽ tính toán lại quyền. |
| 11 | **Trả kết quả** | Backend trả về role đã tạo/cập nhật; FE hiển thị toast thành công và cập nhật giao diện. |
| 12 | **Bác sĩ truy cập tính năng** | Bác sĩ đăng nhập → JWT bao gồm quyền từ role vừa gán → truy cập được các endpoint vận hành (tiếp nhận, khám, v.v.). |

---

## 3. Nguồn dữ liệu đầu vào

Không áp dụng — tính năng này không có nguồn dữ liệu bên ngoài (Message Queue, File Import). Dữ liệu (quyền, role, preset) đều được quản lý thông qua API từ người dùng trực tiếp.

---

## 4. Danh sách API

Tất cả API đều yêu cầu xác thực:
```
Authorization: Bearer {token}
```

**Đường dẫn gốc (Base Path):** `/api/v1`

| STT | Phương thức | Đường dẫn | Mô tả tóm tắt |
|-----|------------|-----------|--------------|
| 1 | GET | `/permission-presets` | Liệt kê các preset (system + clinic-owned) |
| 2 | POST | `/permission-presets` | Tạo preset tùy chỉnh cho phòng khám |
| 3 | PATCH | `/permission-presets/{preset_id}` | Cập nhật preset tùy chỉnh |
| 4 | DELETE | `/permission-presets/{preset_id}` | Xóa preset tùy chỉnh |
| 5 | POST | `/roles/from-preset` | Tạo clinic-role từ preset + gán user (optional) |
| 6 | POST | `/roles/{role_id}/apply-preset` | Áp preset vào role có sẵn, thay thế quyền |

---

## 5. Chi tiết từng API

### 5.1 Lấy danh sách Permission Preset

#### Thông tin chung

| Thuộc tính | Giá trị |
|------------|---------|
| **Đường dẫn** | `GET /api/v1/permission-presets` |
| **Mô tả** | Liệt kê tất cả preset (system preset + các preset do phòng khám hiện tại tạo). Bao gồm các preset khác nhau từ các phòng khám. Dùng để hiển thị danh sách preset khi quản trị viên cấu hình quyền. |
| **Xác thực** | Bắt buộc (authenticated user) — không yêu cầu quyền cụ thể, bất kỳ người dùng đã đăng nhập nào cũng có thể xem. |

#### Tham số đầu vào

Không có tham số (request body hoặc query params).

#### Quy trình xử lý

| Bước | Mô tả |
|------|-------|
| 1 | Nhận yêu cầu từ ứng dụng client |
| 2 | Kiểm tra token xác thực — từ chối nếu không hợp lệ (401) |
| 3 | Lấy `clinic_id` từ context (từ token) |
| 4 | Truy vấn database: lấy tất cả preset có `clinic_id = NULL` (system) HOẶC `clinic_id = current_clinic_id` (clinic-owned) |
| 5 | Sắp xếp: system preset ưu tiên (is_system=True), sau đó theo code |
| 6 | Trả danh sách preset về client |

#### Kết quả trả về

**Thành công (200 OK):**

```json
{
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "clinic_id": null,
      "code": "small_clinic_doctor",
      "name": "Bác sĩ toàn quyền (phòng khám nhỏ)",
      "description": "Quyền vận hành đầy đủ: tiếp nhận, khám, kê đơn, dược, thanh toán, báo cáo; không bao gồm quyền nền tảng",
      "permission_codes": ["exam.create", "exam.read", "exam.update", "prescription.create", ..., "report.read"],
      "is_system": true
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "clinic_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
      "code": "custom_specialist",
      "name": "Bác sĩ chuyên khoa",
      "description": "Chỉ khám và kê đơn, không có thanh toán",
      "permission_codes": ["exam.create", "exam.read", "exam.update", "prescription.create", "prescription.read"],
      "is_system": false
    }
  ],
  "total": 2
}
```

**Mô tả các trường kết quả:**

| Trường | Kiểu | Mô tả ý nghĩa nghiệp vụ |
|--------|------|------------------------|
| `data` | Array | Danh sách các preset |
| `data[].id` | UUID | Mã định danh duy nhất của preset |
| `data[].clinic_id` | UUID \| null | Phòng khám chủ sở hữu preset; `null` = preset hệ thống |
| `data[].code` | String | Mã preset để sử dụng trong các API khác (ví dụ: `small_clinic_doctor`) |
| `data[].name` | String | Tên hiển thị dễ hiểu bằng tiếng Việt |
| `data[].description` | String \| null | Mô tả chi tiết (optional) |
| `data[].permission_codes` | Array\<String\> | Danh sách mã quyền trong preset |
| `data[].is_system` | Boolean | `true` = preset hệ thống (không chỉnh sửa), `false` = preset phòng khám (có thể sửa/xóa) |
| `total` | Integer | Tổng số preset |

---

### 5.2 Tạo Permission Preset

#### Thông tin chung

| Thuộc tính | Giá trị |
|------------|---------|
| **Đường dẫn** | `POST /api/v1/permission-presets` |
| **Mô tả** | Tạo một preset tùy chỉnh mới cho phòng khám hiện tại. Quản trị viên cấp quyền tùy chỉnh dựa trên mô hình vận hành của phòng khám. Hệ thống tự động loại bỏ các quyền nền tảng (platform blacklist) — ngay cả nếu client cố gắng gửi chúng, server cũng sẽ bỏ qua. |
| **Xác thực** | Bắt buộc quyền `role.manage` |

#### Tham số đầu vào

| Tham số | Kiểu | Bắt buộc | Mô tả | Giá trị mặc định |
|---------|------|---------|-------|-----------------|
| `code` | String | Có | Mã định danh duy nhất của preset (ví dụ: `custom_specialist`, tối đa 50 ký tự). Phải là unique trong phòng khám (không trùng với preset khác của cùng clinic). | — |
| `name` | String | Có | Tên hiển thị bằng tiếng Việt, dễ nhớ (ví dụ: "Bác sĩ chuyên khoa", tối đa 200 ký tự). | — |
| `description` | String | Không | Mô tả chi tiết về preset này (optional). | `null` |
| `permission_codes` | Array\<String\> | Có | Danh sách mã quyền trong preset. Nếu client gửi quyền nền tảng (blacklist), server sẽ tự động loại bỏ. | `[]` |

**Ví dụ request:**

```json
{
  "code": "custom_specialist",
  "name": "Bác sĩ chuyên khoa",
  "description": "Quyền khám và kê đơn, không thanh toán",
  "permission_codes": ["exam.create", "exam.read", "exam.update", "prescription.create", "prescription.read"]
}
```

#### Quy trình xử lý

| Bước | Mô tả |
|------|-------|
| 1 | Nhận yêu cầu, kiểm tra token + quyền `role.manage` |
| 2 | Lấy `clinic_id` từ context → từ chối (400) nếu không có |
| 3 | Kiểm tra `code` không trùng với preset khác của clinic này → từ chối (409) nếu trùng |
| 4 | Tính operational set = (tất cả quyền − blacklist) |
| 5 | Giao tập hợp `permission_codes` với operational set → `safe_codes` (loại quyền nền tảng) |
| 6 | Lưu preset vào database: `{clinic_id, code, name, description, permission_codes=safe_codes, is_system=False}` |
| 7 | Trả preset vừa tạo về client (201 Created) |

#### Kết quả trả về

**Thành công (201 Created):**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "clinic_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "code": "custom_specialist",
  "name": "Bác sĩ chuyên khoa",
  "description": "Quyền khám và kê đơn, không thanh toán",
  "permission_codes": ["exam.create", "exam.read", "exam.update", "prescription.create", "prescription.read"],
  "is_system": false
}
```

**Lỗi:**
- **409 Conflict**: Code đã tồn tại cho phòng khám này
- **400 Bad Request**: `clinic_id` không hợp lệ hoặc thiếu, validation error

---

### 5.3 Cập nhật Permission Preset

#### Thông tin chung

| Thuộc tính | Giá trị |
|------------|---------|
| **Đường dẫn** | `PATCH /api/v1/permission-presets/{preset_id}` |
| **Mô tả** | Cập nhật một preset tùy chỉnh (chỉ clinic-owned preset, system preset không cho sửa). |
| **Xác thực** | Bắt buộc quyền `role.manage` |

#### Tham số đầu vào

| Tham số | Kiểu | Bắt buộc | Mô tả |
|---------|------|---------|-------|
| `preset_id` | UUID | Có (trong URL path) | Mã định danh của preset cần cập nhật |
| `name` | String | Không | Tên mới (nếu có) |
| `description` | String | Không | Mô tả mới (nếu có) |
| `permission_codes` | Array\<String\> | Không | Danh sách quyền mới (nếu có); platform blacklist sẽ tự động bị loại |

**Ví dụ request:**

```json
{
  "name": "Bác sĩ chuyên khoa (cập nhật)",
  "permission_codes": ["exam.create", "exam.read", "exam.update", "prescription.create", "prescription.read", "prescription.update"]
}
```

#### Quy trình xử lý

| Bước | Mô tả |
|------|-------|
| 1 | Kiểm tra token + quyền `role.manage` |
| 2 | Tìm preset theo `preset_id` + `clinic_id` (từ context) — từ chối (404) nếu không tìm thấy |
| 3 | Kiểm tra nó không phải system preset (`is_system=false`) — từ chối (403) nếu là system preset |
| 4 | Nếu `permission_codes` được cung cấp, lọc bỏ blacklist (loại quyền nền tảng) |
| 5 | Cập nhật các trường (name, description, permission_codes) → `updated_at`, `updated_by` |
| 6 | Trả preset đã cập nhật về client |

#### Kết quả trả về

**Thành công (200 OK):**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "clinic_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "code": "custom_specialist",
  "name": "Bác sĩ chuyên khoa (cập nhật)",
  "description": "Quyền khám, kê đơn, cập nhật đơn",
  "permission_codes": ["exam.create", "exam.read", "exam.update", "prescription.create", "prescription.read", "prescription.update"],
  "is_system": false
}
```

**Lỗi:**
- **403 Forbidden**: Cố gắng sửa system preset
- **404 Not Found**: Preset không tồn tại

---

### 5.4 Xóa Permission Preset

#### Thông tin chung

| Thuộc tính | Giá trị |
|------------|---------|
| **Đường dẫn** | `DELETE /api/v1/permission-presets/{preset_id}` |
| **Mô tả** | Xóa một preset tùy chỉnh (chỉ clinic-owned preset, system preset không cho xóa). Xóa là soft-delete (đánh dấu `is_deleted=true`). |
| **Xác thực** | Bắt buộc quyền `role.manage` |

#### Tham số đầu vào

| Tham số | Kiểu | Bắt buộc |
|---------|------|---------|
| `preset_id` | UUID | Có (trong URL path) |

#### Quy trình xử lý

| Bước | Mô tả |
|------|-------|
| 1 | Kiểm tra token + quyền `role.manage` |
| 2 | Tìm preset theo `preset_id` + `clinic_id` — từ chối (404) nếu không tìm |
| 3 | Kiểm tra không phải system preset — từ chối (403) nếu là system preset |
| 4 | Soft-delete: `is_deleted = true`, `deleted_at = now()`, `deleted_by = current_user()` |
| 5 | Trả 204 No Content |

#### Kết quả trả về

**Thành công (204 No Content):** Không có body trả về.

**Lỗi:**
- **403 Forbidden**: Cố gắng xóa system preset
- **404 Not Found**: Preset không tồn tại

---

### 5.5 Tạo Role từ Permission Preset

#### Thông tin chung

| Thuộc tính | Giá trị |
|------------|---------|
| **Đường dẫn** | `POST /api/v1/roles/from-preset` |
| **Mô tả** | Tạo một clinic-scoped role mới từ một permission preset. Đây là bước cốt lõi của luồng "Cấp bác sĩ toàn quyền 1-click": từ preset tính toán quyền vận hành (bỏ quyền nền tảng), tạo role, gán vào user (nếu có `assign_user_id`). |
| **Xác thực** | Bắt buộc quyền `role.manage` |

#### Tham số đầu vào

| Tham số | Kiểu | Bắt buộc | Mô tả |
|---------|------|---------|-------|
| `preset_code` | String | Có | Mã preset để tạo role từ (ví dụ: `small_clinic_doctor`). Hệ thống sẽ tìm preset có code này (ưu tiên clinic-scoped, sau đó system). |
| `role_name` | String | Có | Tên role mới, ví dụ: "Bác sĩ Nguyễn Văn A" (tối đa 200 ký tự). Đây là tên hiển thị; `role_code` được tự động sinh từ tên hoặc chỉ định rõ. |
| `role_code` | String | Không | Mã code của role (tối đa 50 ký tự). Nếu không chỉ định, hệ thống sẽ sinh tự động từ `role_name` bằng cách chuyển thành lowercase, bỏ dấu, thay space bằng `_`. |
| `assign_user_id` | UUID | Không | (Optional) Mã user để gán role này ngay sau khi tạo. Nếu có, role sẽ được gán cho user và cache permission của user sẽ bị invalidate (để lần truy cập tiếp theo tính quyền mới). |

**Ví dụ request:**

```json
{
  "preset_code": "small_clinic_doctor",
  "role_name": "Bác sĩ Nguyễn Văn A",
  "role_code": "doctor_nguyen_van_a",
  "assign_user_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479"
}
```

#### Quy trình xử lý

| Bước | Mô tả |
|------|-------|
| 1 | Kiểm tra token + quyền `role.manage` |
| 2 | Lấy `clinic_id` từ context — từ chối (400) nếu không có |
| 3 | Tìm preset theo `preset_code` và `clinic_id` (ưu tiên clinic-owned, sau đó system) — từ chối (404) nếu không tìm |
| 4 | Tính operational set (tất cả quyền − blacklist) |
| 5 | Giao tập `preset.permission_codes` với operational set → `safe_codes` (đảm bảo loại quyền nền tảng) |
| 6 | Sinh `role_code` từ `role_name` nếu không được cung cấp |
| 7 | Kiểm tra `role_code` không trùng trong clinic — từ chối (409) nếu trùng |
| 8 | Tạo role mới: `{clinic_id, code=role_code, display_name=role_name, is_system=false}` |
| 9 | Tạo các row `role_permission` cho role này, mỗi quyền trong `safe_codes` |
| 10 | Nếu `assign_user_id` được cung cấp, gọi `assign_role(user_id, role_id)` → tạo `user_role` |
| 11 | Invalidate cache permission của user (xóa Redis key `user:perms:{user_id}`) |
| 12 | Trả role vừa tạo về client (201 Created) |

#### Kết quả trả về

**Thành công (201 Created):**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440010",
  "clinic_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "code": "doctor_nguyen_van_a",
  "name": "Bác sĩ Nguyễn Văn A",
  "description": null,
  "is_system": false,
  "permission_count": 64
}
```

**Lỗi:**
- **404 Not Found**: Preset hoặc user không tồn tại
- **409 Conflict**: Role code đã tồn tại
- **400 Bad Request**: `clinic_id` không hợp lệ

---

### 5.6 Áp Permission Preset vào Role

#### Thông tin chung

| Thuộc tính | Giá trị |
|------------|---------|
| **Đường dẫn** | `POST /api/v1/roles/{role_id}/apply-preset` |
| **Mô tả** | Thay thế tất cả quyền của một role có sẵn bằng quyền từ một preset. Dùng khi quản trị viên muốn áp một preset vào một role đã tạo từ trước. Quy trình: lấy role, loại bỏ tất cả quyền cũ, thêm quyền từ preset (sau khi lọc bỏ blacklist), invalidate cache các user có role này. |
| **Xác thực** | Bắt buộc quyền `role.manage` |

#### Tham số đầu vào

| Tham số | Kiểu | Bắt buộc | Mô tả |
|---------|------|---------|-------|
| `role_id` | UUID | Có (trong URL path) | Mã định danh của role cần áp preset vào |
| `preset_code` | String | Có | Mã preset để áp dụng |

**Ví dụ request:**

```json
{
  "preset_code": "small_clinic_doctor"
}
```

#### Quy trình xử lý

| Bước | Mô tả |
|------|-------|
| 1 | Kiểm tra token + quyền `role.manage` |
| 2 | Lấy `clinic_id` từ context — từ chối (400) nếu không có |
| 3 | Tìm role theo `role_id` + `clinic_id` — từ chối (404) nếu không tìm |
| 4 | Kiểm tra role không phải system role — từ chối (403) nếu cố áp preset vào system role |
| 5 | Tìm preset theo `preset_code` — từ chối (404) nếu không tìm |
| 6 | Tính operational set (tất cả quyền − blacklist) |
| 7 | Giao tập `preset.permission_codes` với operational set → `safe_codes` |
| 8 | Xóa tất cả `role_permission` row của role này (atomic delete) |
| 9 | Tạo các row `role_permission` mới cho `safe_codes` |
| 10 | Tìm tất cả user có role này → invalidate cache permission của từng user (Redis SCAN delete `user:perms:{user_id}`) |
| 11 | Trả role (với quyền cập nhật) về client |

#### Kết quả trả về

**Thành công (200 OK):**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440010",
  "clinic_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "code": "doctor_nguyen_van_a",
  "name": "Bác sĩ Nguyễn Văn A",
  "description": null,
  "is_system": false,
  "permission_count": 64
}
```

**Lỗi:**
- **403 Forbidden**: Cố áp preset vào system role hoặc permission_codes gửi lên chứa blacklist
- **404 Not Found**: Role hoặc preset không tồn tại
- **400 Bad Request**: `clinic_id` không hợp lệ

---

## 6. Cấu trúc cơ sở dữ liệu

### 6.1 Tổng quan các bảng

| Bảng | Mục đích |
|------|---------|
| `permission_preset` | Lưu các permission preset (hệ thống + phòng khám); mỗi preset là tập quyền có tên |
| `role` | (Hiện có) Lưu các role; clinic-scoped role sẽ được tạo để chứa quyền từ preset |
| `role_permission` | (Hiện có) Link giữa role và permission; khi áp preset, các row này sẽ được cập nhật |
| `permission` | (Hiện có) Danh mục tất cả quyền hệ thống; preset sẽ tham chiếu đến các quyền này |

### 6.2 Chi tiết bảng

#### Bảng: `permission_preset`

**Mô tả:** Bảng lưu các permission preset — tập quyền có tên được sử dụng để cấu hình quyền dễ dàng. System preset (`clinic_id=NULL`) được seed sẵn, không chỉnh sửa. Clinic preset (`clinic_id=<uuid>`) do phòng khám tạo, có thể sửa/xóa.

| Tên cột | Kiểu dữ liệu | Bắt buộc | Mô tả |
|---------|-------------|---------|-------|
| `id` | UUID | Có | Khóa chính, duy nhất |
| `clinic_id` | UUID | Không | Ngoại khóa → `clinic.id`; NULL = system preset |
| `code` | VARCHAR(50) | Có | Mã định danh preset (ví dụ: `small_clinic_doctor`) |
| `name` | VARCHAR(200) | Có | Tên hiển thị dễ hiểu bằng tiếng Việt |
| `description` | TEXT | Không | Mô tả chi tiết (optional) |
| `permission_codes` | TEXT[] | Có | Mảng mã quyền trong preset (ví dụ: `["exam.create", "exam.read", ...]`) |
| `is_system` | BOOLEAN | Có | `true` = preset hệ thống (không chỉnh sửa), `false` = preset phòng khám |
| `is_deleted` | BOOLEAN | Có | Soft-delete flag; `true` = preset đã bị xóa (ẩn khỏi query) |
| `created_at` | TIMESTAMP | Có | Thời điểm tạo bản ghi (auto, UTC) |
| `created_by` | UUID | Không | User tạo preset (audit trail) |
| `updated_at` | TIMESTAMP | Có | Thời điểm cập nhật cuối cùng |
| `updated_by` | UUID | Không | User cập nhật gần nhất |
| `deleted_at` | TIMESTAMP | Không | Thời điểm xóa (nếu `is_deleted=true`) |
| `deleted_by` | UUID | Không | User xóa |
| `version` | INTEGER | Có | Optimistic lock version (increment mỗi khi cập nhật) |

**Tính duy nhất (Unique Key):** 
- `(clinic_id, code) WHERE is_deleted=false` — phải duy nhất **theo clinic**: tương tự bảng `role`, system preset (`clinic_id IS NULL`) có code duy nhất, clinic preset của cùng phòng khám cũng phải có code duy nhất.
- Cụ thể: 2 index unique partial:
  - `uq_permission_preset_system_code`: `(code) WHERE clinic_id IS NULL AND is_deleted=false`
  - `uq_permission_preset_clinic_code`: `(clinic_id, code) WHERE clinic_id IS NOT NULL AND is_deleted=false`

**Script tạo bảng:**

```sql
CREATE TABLE permission_preset (
    id UUID NOT NULL PRIMARY KEY DEFAULT gen_random_uuid(),
    clinic_id UUID REFERENCES clinic(id) ON DELETE RESTRICT,
    code VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    permission_codes TEXT[] NOT NULL DEFAULT '{}',
    is_system BOOLEAN NOT NULL DEFAULT false,
    is_deleted BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by UUID,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_by UUID,
    deleted_at TIMESTAMP,
    deleted_by UUID,
    version INTEGER NOT NULL DEFAULT 1,
    
    -- RLS: Row-level security (system + clinic scoped)
    -- Partial unique constraints
    CONSTRAINT uq_permission_preset_system_code UNIQUE (code) 
        WHERE clinic_id IS NULL AND is_deleted = false,
    CONSTRAINT uq_permission_preset_clinic_code UNIQUE (clinic_id, code) 
        WHERE clinic_id IS NOT NULL AND is_deleted = false,
    
    -- Index for clinic_id lookup
    INDEX idx_permission_preset_clinic (clinic_id),
    INDEX idx_permission_preset_is_deleted (is_deleted)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Row-Level Security Policy (enable via Postgres extension)
-- Allows: clinic_id IS NULL (system, cross-clinic) OR clinic_id = current_setting('app.current_clinic_id')
-- Plus superadmin_bypass for superusers
ALTER TABLE permission_preset ENABLE ROW LEVEL SECURITY;
CREATE POLICY permission_preset_tenant_isolation ON permission_preset
    USING (clinic_id IS NULL OR clinic_id = (current_setting('app.current_clinic_id')::uuid));
```

---

## 7. SQL tổng hợp và truy vấn dữ liệu

Không áp dụng — tính năng này không có logic tổng hợp dữ liệu (ETL, analytics, aggregation). Đây là tính năng CRUD đơn giản trên các bảng `permission_preset`, `role`, `role_permission`. Các truy vấn là các phép SELECT/INSERT/UPDATE/DELETE cơ bản không có tính toán phức tạp hay UNION.

---

## 8. Quy tắc nghiệp vụ

| Mã | Mô tả quy tắc | Hành vi khi vi phạm |
|----|--------------|---------------------|
| BR-001 | **System preset bất biến**: Preset hệ thống (`is_system=true`) không thể sửa hoặc xóa qua API. Chỉ có thể đọc (list). | API trả về 403 Forbidden với message "System presets are immutable" |
| BR-002 | **Clinic preset duy nhất theo code**: Trong mỗi phòng khám, mã code của preset phải là duy nhất. Hai preset khác nhau của cùng phòng khám không được có cùng code. | Hệ thống trả 409 Conflict: "A preset with this code already exists for this clinic" |
| BR-003 | **Platform blacklist bất chối**: Mọi API tạo/cập nhật preset, tạo role từ preset, hoặc áp preset vào role đều PHẢI loại bỏ các quyền nền tảng (`system.manage`, `clinic.create/read/update/delete/list`) trước khi lưu. Điều này được áp dụng **server-side** và **KHÔNG** phụ thuộc vào client gửi gì. | Quyền nền tảng sẽ được tự động loại bỏ (soft-removed) từ `permission_codes`; không gây lỗi, nhưng client sẽ nhận được kết quả đã lọc. |
| BR-004 | **Clinic context bắt buộc**: Mọi mutation API (POST/PATCH/DELETE /permission-presets, POST /roles/from-preset, POST /roles/{id}/apply-preset) đều yêu cầu token phải mang `clinic_id` hợp lệ. | Hệ thống trả 400 Bad Request: "active clinic context required" |
| BR-005 | **Gating quyền**: Chỉ user có quyền `role.manage` mới được tạo/sửa/xóa preset, hoặc tạo/áp preset vào role. User không có quyền này sẽ nhận 403. | API trả 403 Forbidden |
| BR-006 | **Cache invalidation tức thì**: Khi áp preset vào role (hoặc tạo role từ preset với `assign_user_id`), hệ thống phải invalidate cache permission của tất cả user có role đó (xóa Redis key `user:perms:{user_id}`), để lần truy cập tiếp theo tính toán quyền mới. | Nếu cache không được xóa, user sẽ vẫn thấy quyền cũ cho đến khi JWT hết hạn (15 phút) hoặc user đăng nhập lại. |
| BR-007 | **RLS: Clinic isolation**: System preset (`clinic_id IS NULL`) có thể nhìn thấy từ bất kỳ phòng khám nào, nhưng clinic preset (`clinic_id != NULL`) chỉ có thể nhìn thấy từ phòng khám chủ sở hữu. Các phòng khám khác sẽ nhận 404 Not Found. | Hệ thống áp dụng RLS filter tự động; không trả lỗi, chỉ ẩn dữ liệu không có quyền. |
| BR-008 | **Role từ preset không phải system role**: Khi tạo role từ preset, role mới luôn là clinic-scoped (có `clinic_id` và `is_system=false`). System role không thể được tạo qua API này. | Quy tắc này được enforce bằng code; không có lỗi user-facing vì API không tiếp nhận request để tạo system role. |
| BR-009 | **Không áp preset vào system role**: Một API call cố gắng áp preset vào một system role (ví dụ: role `admin`) sẽ bị từ chối. | API trả 403 Forbidden: "System roles are immutable; cannot apply preset" |
| BR-010 | **Operational set động**: Các quyền vận hành (operational set) được tính động từ bảng `permission` hiện tại (tất cả quyền TRỪ blacklist). Khi thêm quyền mới vào hệ thống, quyền đó sẽ tự động được bao gồm trong operational set, không cần thay đổi code hoặc preset đã seed. | Nếu một quyền mới được thêm vào catalog, preset sẽ không tự động cập nhật; nhưng khi áp preset, backend sẽ giao tập quyền trong preset với operational set hiện tại, đảm bảo quyền mới được bao gồm nếu nó trong preset snapshot. |

---

## 9. Xử lý lỗi

### 9.1 Các mã lỗi phổ biến

| Mã HTTP | Mã lỗi nội bộ | Tình huống xảy ra | Thông báo trả về |
|---------|--------|-------------------|-----------------|
| 400 | BAD_REQUEST | Clinic context không hợp lệ hoặc thiếu (token không có `clinic_id`) | "active clinic context required" |
| 400 | VALIDATION_ERROR | Tham số đầu vào không hợp lệ (ví dụ: `code` quá dài, `name` rỗng) | "Yêu cầu không hợp lệ: [chi tiết]" |
| 401 | UNAUTHORIZED | Token không hợp lệ hoặc hết hạn | "Yêu cầu xác thực để truy cập tài nguyên này" |
| 403 | FORBIDDEN | User không có quyền `role.manage`, hoặc cố sửa/xóa system preset, hoặc cố áp preset vào system role | "Forbidden: [chi tiết — system preset immutable / system role immutable / insufficient permission]" |
| 404 | NOT_FOUND | Preset, role, hoặc user không tồn tại trong phòng khám hiện tại | "Not found: Permission preset / Role / User not found" |
| 409 | CONFLICT | Mã code của preset trùng lặp trong phòng khám, hoặc role code trùng lặp | "A preset/role with this code already exists in this clinic" |
| 500 | INTERNAL_ERROR | Lỗi hệ thống (database, cache, v.v.) | "Lỗi hệ thống, vui lòng thử lại sau" |

### 9.2 Định dạng phản hồi lỗi

```json
{
  "code": "[Mã lỗi nội bộ, ví dụ: 'system_preset_immutable']",
  "message": "[Mô tả lỗi chi tiết bằng tiếng Việt]"
}
```

---

## 10. Chiến lược cache

### 10.1 Mục đích

Permission Preset là khái niệm cấp phòng khám (clinic-level), không phải user-level. Tuy nhiên, khi áp preset vào role hoặc tạo role từ preset và gán user, **quyền hiệu dụng của user thay đổi**, nên cache permission của user phải bị invalidate ngay. Điều này đảm bảo rằng lần truy cập tiếp theo của user sẽ tính toán quyền mới (từ JWT mới hoặc từ Redis, không dùng bộ đệm cũ).

### 10.2 Quy tắc lưu và xóa cache

| Nội dung cache | Thời gian lưu (TTL) | Điều kiện xóa cache |
|----------------|---------------------|---------------------|
| User permission (Redis) | 5 phút | Khi `apply_preset_to_role` hoặc `assign_role` được gọi → tìm tất cả user có role đó → xóa khóa `user:perms:{user_id}` của từng user |
| JWT (client-side) | 15 phút | Hết hạn tự động; user phải đăng nhập lại hoặc làm mới token |

### 10.3 Cách tạo khóa cache

Permission cache trong Redis sử dụng khóa:

```
user:perms:{user_id}
```

Ví dụ: `user:perms:f47ac10b-58cc-4372-a567-0e02b2c3d479`

Giá trị là JSON chứa:
- `clinic_id`: phòng khám mà cache này áp dụng cho
- `permission_codes`: danh sách quyền hiệu dụng của user trong phòng khám đó
- `expires_at`: timestamp hết hạn (5 phút từ lúc tạo)

**Quy trình invalidate:**
1. Khi `apply_preset_to_role(role_id, preset_code)` được gọi, backend tìm tất cả `UserRole` row có `role_id` đó
2. Với mỗi `user_id` tìm được, xóa khóa Redis `user:perms:{user_id}` (SCAN delete)
3. Lần truy cập tiếp theo của user sẽ query database để tính quyền mới

---

## 11. Ghi chú và lưu ý khi kiểm thử

### 11.1 Điểm quan trọng cần nắm

- **Preset hệ thống `small_clinic_doctor` là snapshot**: Preset được seed trong migration với danh sách quyền **tại thời điểm migration được chạy** (gồm 64 quyền vận hành từ bảng `permission` hiện có). Khi thêm quyền mới vào catalog sau này, preset này không tự động cập nhật — nhưng khi backend áp preset, nó vẫn sẽ giao tập với operational set hiện tại, nên quyền mới **sẽ được bao gồm** nếu nó ở trong operational set.

- **Platform blacklist là không thể vượt qua**: Ngay cả nếu client cố gắng gửi quyền nền tảng (ví dụ: `system.manage`) trong `permission_codes` của một POST request, server sẽ tự động loại bỏ nó. Đây là bảo vệ server-side, không phụ thuộc vào validation client.

- **Clinic isolation qua RLS**: Khi user từ phòng khám A truy cập `/permission-presets`, họ chỉ nhìn thấy system preset + các preset của phòng khám A. User từ phòng khám B sẽ không nhìn thấy preset của A (403 Not Found nếu cố truy cập trực tiếp bằng ID).

- **Cache invalidation tức thì**: Sau khi áp preset hoặc gán role, cache permission của user sẽ bị xóa ngay. Lần truy cập tiếp theo của user sẽ cho thấy quyền mới (cách nhanh nhất là reload ứng dụng FE hoặc gọi lại `/current-user` endpoint).

### 11.2 Gợi ý dữ liệu kiểm thử

| Kịch bản | Giá trị đầu vào | Kết quả kỳ vọng |
|---------|----------------|----------------|
| **Cấp bác sĩ toàn quyền 1-click** | POST /roles/from-preset với preset_code="small_clinic_doctor" + assign_user_id=<bs_id> | Role được tạo, user nhận role, lần truy cập tiếp theo user có 64 quyền vận hành, KHÔNG có quyền nền tảng |
| **Kiểm tra blacklist** | POST /permission-presets với permission_codes=["exam.create", "system.manage", "clinic.create"] | Quyền nền tảng bị loại bỏ; result chỉ có ["exam.create"] |
| **RLS isolation** | Clinic A và B đều có user với quyền role.manage; user A tạo preset A1, user B cố DELETE /permission-presets/{preset_A1_id} | User B nhận 404 Not Found (không nhìn thấy preset của A) |
| **System preset immutability** | PATCH /permission-presets/{small_clinic_doctor_id} với name="Mới" | 403 Forbidden: "System presets are immutable" |
| **Cache invalidation** | Tạo role + assign user, user truy cập endpoint yêu cầu quyền → nhận 403; sau 1 giây truy cập lại | Lần 2 nhận 200 (cache đã tính lại quyền) |
| **Clinic context bắt buộc** | Token không có clinic_id, POST /permission-presets | 400 Bad Request: "active clinic context required" |
| **Quyền role.manage bắt buộc** | User có quyền exam.read nhưng không có role.manage, cố POST /permission-presets | 403 Forbidden |
| **Clinic preset duy nhất** | Tạo preset "code1", rồi tạo lại "code1" ở cùng clinic | 409 Conflict: "already exists" |
| **Role code từ role_name** | POST /roles/from-preset với role_name="Bác sĩ Nguyễn" mà không chỉ định role_code | Role được tạo với code tự động = "bac_si_nguyen" (slug hóa) |

### 11.3 Hạn chế hiện tại

- **Refresh preset khi thêm quyền mới**: Khi quyền mới được thêm vào catalog, system preset `small_clinic_doctor` không tự động cập nhật. Nếu muốn preset bao gồm quyền mới, phải chạy migration lại hoặc gọi một helper function (không có endpoint công khai cho việc này). Giải pháp: phòng khám có thể tạo preset tùy chỉnh với quyền mới.

- **Không có endpoint "suggest preset"**: Hệ thống không có API để đề xuất quyền cần thiết cho một vai trò cụ thể (ví dụ: "suggest preset for a receptionist"). Admin phải tự biết quyền nào là phù hợp, hoặc sử dụng preset hệ thống.

- **Hiệu năng clinic với 1000+ user**: Khi áp preset vào một role có 1000+ user, cache invalidation sẽ SCAN tất cả khóa Redis (có thể mất vài giây). Đây không phải vấn đề lớn vì thao tác này hiếm khi xảy ra, nhưng nên có giám sát nếu clinic có số lượng user lớn.

### 11.4 Hướng phát triển (nếu có)

- **Preset mục đích (Purpose-based presets)**: Trong các phiên bản tiếp theo, có thể thêm các preset được xây dựng sẵn cho các vai trò khác nhau (ví dụ: "Bác sĩ chuyên khoa", "Dược sĩ", "Nhân viên tiếp nhận"), không chỉ `small_clinic_doctor`.

- **Ghi đè preset tạm thời**: Cho phép quản trị viên sửa quyền của một user tạm thời (trên và dưới preset) mà không ảnh hưởng đến role và các user khác trong role đó — dùng cơ chế grant/deny hiện tại.

- **Audit log preset**: Ghi lại lịch sử ai đã áp preset nào vào role nào; hiển thị trong một audit UI.

- **Gap follow-up (pre-existing)**: Endpoint `POST /roles/{id}/permissions` (add_role_permission) hiện không áp dụng platform blacklist — đây là gap bảo mật cần khắc phục trong một task riêng để đảm bảo tất cả đường dẫn thêm quyền vào role đều được bảo vệ.

---

## Phê duyệt

| Vai trò | Họ tên | Ngày |
|---------|--------|------|
| Code Implementation | Code Implementation Agent | 2026-07-02 |
| Code Review | Code Review Agent | 2026-07-03 |
| Testing | Test Agent | 2026-07-03 |
| Documentation | Documentation Agent | 2026-07-03 |
