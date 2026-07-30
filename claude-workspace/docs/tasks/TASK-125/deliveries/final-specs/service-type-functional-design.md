# Thiết Kế Chi Tiết Tính Năng: Service Type — Phân loại danh mục dịch vụ cấu hình được

**Dự án:** Clinic CMS
**Task:** TASK-125
**Phiên bản:** 1.0
**Ngày:** 2026-07-30
**Người thực hiện:** Code Implementation Agent
**Trạng thái:** Đã triển khai (BE + FE) — chờ Code Review / Test
**Tài liệu liên quan:** TASK-010 (Service Catalog), TASK-076 (Dosage Form — mẫu tham chiếu cho bảng cấu hình), implementation-plan.md, task.md

---

## Lịch sử thay đổi

| Phiên bản | Ngày | Nội dung thay đổi |
|-----------|------|-------------------|
| 1.0 | 2026-07-30 | Phiên bản đầu tiên — hoàn tất Implementation, sẵn sàng Review |

---

## Mục lục

- [1. Tổng quan tính năng](#1-tổng-quan-tính-năng)
- [2. Luồng xử lý tổng thể](#2-luồng-xử-lý-tổng-thể)
- [3. Danh sách API](#3-danh-sách-api)
- [4. Chi tiết từng API](#4-chi-tiết-từng-api)
- [5. Cấu trúc cơ sở dữ liệu](#5-cấu-trúc-cơ-sở-dữ-liệu)
- [6. Quy tắc nghiệp vụ](#6-quy-tắc-nghiệp-vụ)
- [7. Xử lý lỗi](#7-xử-lý-lỗi)
- [8. Chiến lược cache](#8-chiến-lược-cache)
- [9. Giao diện người dùng](#9-giao-diện-người-dùng)
- [10. Ghi chú và lưu ý khi kiểm thử](#10-ghi-chú-và-lưu-ý-khi-kiểm-thử)

---

## 1. Tổng quan tính năng

### 1.1 Mục đích

Danh mục dịch vụ (`service`) hiện chỉ có một cột `category` dạng chữ tự do (free-text), không có khái niệm "loại dịch vụ" rõ ràng để lọc, báo cáo, hay làm căn cứ tính chiết khấu. TASK-125 bổ sung khái niệm **service_type** — một bảng cấu hình do admin từng phòng khám tự quản lý (KHÔNG phải enum cứng trong code) — để:

- Phân loại dịch vụ thành các nhóm có ý nghĩa nghiệp vụ (Khám / Thủ thuật / Xét nghiệm / do admin tự thêm).
- Làm nền tảng cho **TASK-128** (chiết khấu hoa hồng % theo loại dịch vụ, khóa theo `service_type_id`) và **TASK-126** (thống kê/báo cáo nhóm theo loại).
- Không được phá vỡ luồng hiện có `service → visit_service → billing`: dữ liệu cũ (`service_type_id = NULL`, "chưa phân loại") vẫn hợp lệ và hoạt động bình thường.

### 1.2 Phạm vi

**Bao gồm:**
- Bảng cấu hình **`service_type`** — mỗi phòng khám (clinic) tự quản lý danh sách loại dịch vụ riêng (không dùng chung/toàn cục như `dosage_form`).
- Seed sẵn **3 loại mặc định** cho mỗi phòng khám đang tồn tại tại thời điểm chạy migration: `consultation` (Khám), `procedure` (Thủ thuật), `test` (Xét nghiệm) — đánh dấu `is_system=true`.
- Phòng khám tạo mới sau này cũng được seed 3 loại mặc định tương tự (hook trong `clinic_service.create_clinic`).
- API CRUD `/service-types` (list/create/get/update/delete) — dùng lại quyền `service.read` / `service.manage` sẵn có, **không thêm quyền mới**.
- Cột `service.service_type_id` (FK, nullable) — dịch vụ có thể gắn 0 hoặc 1 loại.
- Luồng tạo/sửa/lọc/liệt kê/xuất Excel của Service Catalog được nối thêm `service_type_id`.
- FE: trang cấu hình `/admin/service-types` (CRUD), select + badge trong `/admin/services`, nhập CSV theo mã loại (`service_type_code`), badge trong picker dịch vụ ở màn khám bệnh (ServicesTab).

**Không bao gồm:**
- Logic tính chiết khấu/hoa hồng theo loại dịch vụ (thuộc TASK-128).
- Báo cáo/thống kê theo loại dịch vụ (thuộc TASK-126).
- Thay đổi cột `category` (chữ tự do) hiện có — `category` và `service_type` tồn tại song song, phục vụ hai mục đích khác nhau.

### 1.3 Các bên liên quan

| Vai trò | Mô tả |
|---------|-------|
| **Quản trị viên phòng khám (admin)** | Có quyền `service.manage` — quản lý danh sách loại dịch vụ (thêm/sửa/ẩn loại tùy chỉnh; loại hệ thống chỉ xem). |
| **Nhân viên tiếp nhận / bác sĩ** | Có quyền `service.read` — nhìn thấy loại dịch vụ khi chọn dịch vụ cho lượt khám. |
| **TASK-128 (Commission/Chiết khấu)** | Hệ thống tiêu thụ tương lai — khóa % chiết khấu theo `service_type_id` ổn định. |
| **TASK-126 (Báo cáo)** | Hệ thống tiêu thụ tương lai — nhóm doanh thu/số lượt theo loại dịch vụ. |

---

## 2. Luồng xử lý tổng thể

### 2.1 Sơ đồ luồng dữ liệu

```
[Migration 0071]
      │  Tạo bảng service_type + seed 3 loại mặc định cho MỖI clinic hiện có
      │  Thêm cột service.service_type_id (nullable, FK → service_type.id, ON DELETE SET NULL)
      ▼
[Admin UI /admin/service-types]
      │  CRUD loại dịch vụ (loại hệ thống chỉ đọc — không sửa/xóa được)
      ▼
[service_type_service — BE]
      │  Validate: code duy nhất/clinic, is_system chặn sửa/xóa
      ▼
[service_type table] ──► [service.service_type_id FK] ──► [Service Catalog CRUD/list/filter/export]
                                                                  │
                                                                  ▼
                                                    [ServicesTab — chọn dịch vụ khi khám bệnh]
                                                                  │
                                                                  ▼
                                            (KHÔNG đổi) [visit_service → billing/invoice]

[Tạo phòng khám mới] ──► clinic_service.create_clinic ──► seed_defaults_for_clinic (3 loại mặc định)
```

### 2.2 Mô tả các bước chính

| Bước | Tên bước | Mô tả chi tiết |
|------|---------|----------------|
| 1 | Migration tạo bảng + seed | Migration `0071` tạo bảng `service_type` (RLS tenant isolation), lặp qua toàn bộ `clinic` hiện có và chèn 3 dòng mặc định (`consultation`/`procedure`/`test`) với `is_system=true`, id sinh bằng `uuid5` (deterministic) để chạy lại không bị trùng. Sau đó thêm cột `service.service_type_id` (nullable FK). |
| 2 | Admin cấu hình loại dịch vụ | Trang `/admin/service-types` cho phép xem danh sách (loại hệ thống + loại tự thêm), tạo mới, sửa/ẩn (chỉ áp dụng cho loại tự thêm — loại hệ thống bị khóa). |
| 3 | Gán loại dịch vụ | Khi tạo/sửa dịch vụ ở `/admin/services`, admin chọn loại từ danh sách đang tải (`GET /service-types`); BE kiểm tra `service_type_id` phải thuộc cùng clinic. |
| 4 | Lọc/liệt kê/xuất Excel | `GET /services?service_type_id=...` lọc theo loại; export Excel có thêm cột "Loại dịch vụ". |
| 5 | Sử dụng ở màn khám bệnh | `ServicesTab` (bác sĩ) hiển thị badge loại dịch vụ trong picker tìm dịch vụ khi thêm vào lượt khám — không đổi luồng billing hiện có. |
| 6 | Phòng khám mới | Khi tạo clinic mới qua `clinic_service.create_clinic`, hệ thống tự động seed 3 loại mặc định giống migration, đảm bảo mọi clinic đều có cùng bộ loại khởi đầu. |

---

## 3. Danh sách API

Tất cả API đều yêu cầu xác thực qua header:
```
Authorization: Bearer {token}
```

**Đường dẫn gốc (Base Path):** `/api/v1`

| STT | Phương thức | Đường dẫn | Quyền yêu cầu | Mô tả tóm tắt |
|-----|------------|-----------|---------------|--------------|
| 1 | GET | `/api/v1/service-types` | `service.read` | Danh sách loại dịch vụ của clinic hiện tại |
| 2 | POST | `/api/v1/service-types` | `service.manage` | Tạo loại dịch vụ tùy chỉnh mới |
| 3 | GET | `/api/v1/service-types/{id}` | `service.read` | Xem chi tiết 1 loại dịch vụ |
| 4 | PATCH | `/api/v1/service-types/{id}` | `service.manage` | Sửa loại dịch vụ (403 nếu là loại hệ thống) |
| 5 | DELETE | `/api/v1/service-types/{id}` | `service.manage` | Xóa mềm loại dịch vụ (403 nếu là loại hệ thống) |
| 6 | GET | `/api/v1/services?service_type_id=...` | `service.read` | *(đã có, mở rộng)* Lọc danh mục dịch vụ theo loại |
| 7 | POST / PATCH | `/api/v1/services` | `service.manage` | *(đã có, mở rộng)* Gán/đổi `service_type_id` khi tạo/sửa dịch vụ |
| 8 | GET | `/api/v1/services/export` | `service.read` | *(đã có, mở rộng)* Excel thêm cột "Loại dịch vụ" |

> **Không có quyền mới** — `/service-types` dùng lại `service.read`/`service.manage` (đã được seed từ TASK-010), theo đúng quyết định trong implementation-plan ("dùng quyền quản lý danh mục hiện có").

---

## 4. Chi tiết từng API

### 4.1 Danh sách loại dịch vụ

| Thuộc tính | Giá trị |
|------------|---------|
| **Đường dẫn** | `GET /api/v1/service-types` |
| **Mô tả** | Trả về toàn bộ loại dịch vụ (hệ thống + tùy chỉnh) thuộc clinic hiện tại, sắp theo `sort_order` rồi `name`. |
| **Quyền** | `service.read` |

**Tham số đầu vào**

| Tham số | Kiểu | Bắt buộc | Mô tả |
|---------|------|---------|-------|
| `is_active` | Boolean | Không | Lọc theo trạng thái kích hoạt |

**Kết quả trả về (200 OK)**

```json
{
  "items": [
    {
      "id": "uuid",
      "clinic_id": "uuid",
      "code": "consultation",
      "name": "Khám",
      "description": null,
      "is_active": true,
      "sort_order": 1,
      "is_system": true,
      "is_deleted": false,
      "created_at": "2026-07-30T00:00:00Z",
      "updated_at": "2026-07-30T00:00:00Z",
      "created_by": null,
      "updated_by": null,
      "version": 1
    }
  ],
  "total": 3
}
```

### 4.2 Tạo loại dịch vụ

| Thuộc tính | Giá trị |
|------------|---------|
| **Đường dẫn** | `POST /api/v1/service-types` |
| **Quyền** | `service.manage` |

**Body**

| Trường | Kiểu | Bắt buộc | Ghi chú |
|--------|------|---------|--------|
| `code` | String | Có | Chỉ chữ thường, số, `_`, `-`; 1-50 ký tự; duy nhất theo clinic (chỉ tính bản ghi chưa xóa) |
| `name` | String | Có | 1-200 ký tự |
| `description` | String | Không | Tối đa 500 ký tự |
| `sort_order` | Integer | Không | Mặc định `0` |
| `is_active` | Boolean | Không | Mặc định `true` |

Loại tạo mới luôn `is_system=false` (BE tự set, không nhận từ client).

**Lỗi:** `409 Conflict` nếu `code` đã tồn tại (kể cả khác hoa/thường) cho clinic đó.

### 4.3 Sửa loại dịch vụ

| Thuộc tính | Giá trị |
|------------|---------|
| **Đường dẫn** | `PATCH /api/v1/service-types/{id}` |
| **Quyền** | `service.manage` |

Chỉ nhận `name`, `description`, `sort_order`, `is_active` — **không** cho đổi `code` hay `is_system`. Nếu bản ghi có `is_system=true` → **403 Forbidden** ("Không thể sửa/xóa loại dịch vụ hệ thống").

### 4.4 Xóa (mềm) loại dịch vụ

| Thuộc tính | Giá trị |
|------------|---------|
| **Đường dẫn** | `DELETE /api/v1/service-types/{id}` |
| **Quyền** | `service.manage` |

Cùng quy tắc 403 với loại hệ thống như mục 4.3. Xóa mềm (`is_deleted=true`), không xóa vật lý.

### 4.5 Service Catalog — mở rộng lọc theo loại

| Thuộc tính | Giá trị |
|------------|---------|
| **Đường dẫn** | `GET /api/v1/services?service_type_id={id}` |
| **Quyền** | `service.read` |

Khi truyền `service_type_id`, chỉ trả về dịch vụ có đúng `service_type_id` đó — dịch vụ "chưa phân loại" (`service_type_id IS NULL`) sẽ **không** xuất hiện trong kết quả lọc này (đây là hành vi có chủ đích, không phải lỗi).

### 4.6 Service Catalog — tạo/sửa với `service_type_id`

`POST /api/v1/services` và `PATCH /api/v1/services/{id}` nhận thêm trường `service_type_id` (UUID, tùy chọn). BE kiểm tra `service_type_id` phải thuộc cùng `clinic_id` với dịch vụ đang tạo/sửa — nếu không tồn tại hoặc thuộc clinic khác → **404 Not Found** (cùng cách xử lý như tham chiếu `visit_id` không tồn tại, mục đích chống rò rỉ giữa các phòng khám — tenant isolation).

**Giới hạn đã biết:** giống hành vi hiện có của trường `category`, PATCH chỉ *set* giá trị khi được truyền khác `null`; hiện **chưa có cách xóa** `service_type_id` đã gán về lại `NULL` qua API (phải tạo dịch vụ khác nếu cần "bỏ phân loại"). Đây là giới hạn nhất quán với `category`, không phải riêng cho tính năng này.

---

## 5. Cấu trúc cơ sở dữu liệu

### 5.1 Tổng quan các bảng

| Bảng | Mục đích |
|------|---------|
| `service_type` | Bảng cấu hình loại dịch vụ — **per-clinic** (mỗi dòng thuộc đúng 1 clinic, khác với `dosage_form` là bảng dùng chung/toàn cục). |
| `service` | *(đã có từ TASK-010)* — thêm cột `service_type_id`. |

### 5.2 Chi tiết bảng

#### Bảng: `service_type`

| Tên cột | Kiểu dữ liệu | Bắt buộc | Mô tả |
|---------|-------------|---------|-------|
| `id` | UUID | Có | Khóa chính |
| `clinic_id` | UUID | Có | FK → `clinic.id` (RESTRICT) — **NOT NULL** (khác `dosage_form.clinic_id` cho phép NULL) |
| `code` | VARCHAR(50) | Có | Mã loại, chữ thường (vd `consultation`) |
| `name` | VARCHAR(200) | Có | Tên hiển thị (vd "Khám") |
| `description` | VARCHAR(500) | Không | Mô tả |
| `is_active` | Boolean | Có | Mặc định `true` |
| `sort_order` | Integer | Có | Mặc định `0` |
| `is_system` | Boolean | Có | `true` = 1 trong 3 loại seed sẵn, không sửa/xóa được |
| `is_deleted`, `deleted_at`, `deleted_by` | — | — | Soft-delete (BaseEntity) |
| `created_at`, `updated_at`, `created_by`, `updated_by`, `version` | — | — | Audit + optimistic lock (BaseEntity) |

**Ràng buộc duy nhất:** `UNIQUE (clinic_id, code) WHERE is_deleted = false` (index `uq_service_type_clinic_code_active`).

**RLS:** bật tenant isolation tiêu chuẩn (`apply_rls_with_tenant_isolation`) + grant `cms_app`.

#### Bảng: `service` (mở rộng)

| Tên cột | Kiểu dữ liệu | Bắt buộc | Mô tả |
|---------|-------------|---------|-------|
| `service_type_id` | UUID | **Không** (nullable) | FK → `service_type.id`, `ON DELETE SET NULL`. `NULL` = "chưa phân loại" — hợp lệ, không phải lỗi. |

Index: `ix_service_service_type_id`.

### 5.3 Seed dữ liệu mặc định

3 loại mặc định — **mã và tên phải khớp giữa migration `0071` và `service_type_service.DEFAULT_SERVICE_TYPES`** (đã đối chiếu, xem ghi chú trong code):

| `code` | `name` | `sort_order` |
|--------|--------|--------------|
| `consultation` | Khám | 1 |
| `procedure` | Thủ thuật | 2 |
| `test` | Xét nghiệm | 3 |

Seed chạy ở 2 nơi, cùng logic (idempotent — kiểm tra code đã tồn tại trước khi chèn):
1. **Migration `0071`** (raw SQL, `id` sinh bằng `uuid5(NAMESPACE_OID, f"service_type:{clinic_id}:{code}")`) — cho mọi clinic **đang tồn tại** tại thời điểm chạy migration.
2. **`clinic_service.create_clinic`** (gọi `service_type_service.seed_defaults_for_clinic` qua ORM) — cho clinic **tạo sau** thời điểm migration.

---

## 6. Quy tắc nghiệp vụ

| Mã | Mô tả quy tắc | Hành vi khi vi phạm |
|----|--------------|---------------------|
| BR-001 | Mỗi clinic được seed đúng 3 loại mặc định (`consultation`/`procedure`/`test`), đánh dấu `is_system=true`. | — (tự động, không cần thao tác) |
| BR-002 | Loại dịch vụ có `is_system=true` **không thể sửa hoặc xóa** qua API — giữ id ổn định cho TASK-128 (Commission) khóa % chiết khấu theo `service_type_id`. | `403 Forbidden` |
| BR-003 | Loại dịch vụ tự thêm (`is_system=false`) có thể sửa/ẩn/xóa mềm tự do bởi admin có quyền `service.manage`. | — |
| BR-004 | `code` của loại dịch vụ duy nhất theo clinic (không phân biệt hoa/thường), chỉ tính bản ghi chưa xóa. | `409 Conflict` |
| BR-005 | Dịch vụ (`service`) có thể **không gắn loại nào** (`service_type_id = NULL`) — trạng thái "chưa phân loại" hợp lệ, áp dụng cho toàn bộ dữ liệu cũ trước TASK-125 và dịch vụ mới chưa được admin phân loại. | — |
| BR-006 | `service.service_type_id` phải thuộc **cùng clinic** với dịch vụ — chống rò rỉ tham chiếu chéo giữa các phòng khám. | `404 Not Found` |
| BR-007 | Bộ lọc `GET /services?service_type_id=X` **loại trừ** các dịch vụ `service_type_id IS NULL` — lọc theo loại nghĩa là chỉ lấy dịch vụ đã phân loại đúng loại đó. | — (hành vi có chủ đích) |
| BR-008 | Xóa loại dịch vụ tự thêm chỉ là xóa mềm; dịch vụ đang tham chiếu loại đó **không** bị xóa theo — cột `service_type_id` của các dịch vụ đó vẫn giữ nguyên giá trị (không tự động chuyển về `NULL` trừ khi xóa vật lý dòng `service_type`, mà hệ thống không làm vậy). | — |

---

## 7. Xử lý lỗi

### 7.1 Các mã lỗi phổ biến

| Mã HTTP | Tình huống xảy ra | Thông báo trả về |
|---------|-------------------|-----------------|
| 403 | Sửa/xóa loại dịch vụ hệ thống (`is_system=true`) | "Không thể sửa/xóa loại dịch vụ hệ thống" |
| 404 | `service_type_id` không tồn tại hoặc thuộc clinic khác khi tạo/sửa dịch vụ | "Service type {id} not found" |
| 404 | Thao tác trên `service_type_id` không tồn tại (get/update/delete trực tiếp) | "Service type {id} not found" |
| 409 | Trùng `code` loại dịch vụ trong cùng clinic | "Service type with code '{code}' already exists for this clinic" |
| 401/403 | Thiếu/sai quyền `service.read` / `service.manage` | Chuẩn RBAC hiện có |

---

## 8. Chiến lược cache

Danh sách `/service-types` **không có cache riêng** (bảng cấu hình, thay đổi hiếm, danh sách rất nhỏ — không cần).

Danh sách `/services` (Service Catalog) tiếp tục dùng cache Redis theo phiên bản clinic (`services:ver:{clinic_id}`, TTL 120s — cơ chế có sẵn từ TASK-010/OPT-3). **Điểm cần lưu ý:** `service_type_id` đã được thêm vào `params_key` của cache — nếu không, một truy vấn lọc theo loại có thể bị trả nhầm kết quả cache của truy vấn khác (chưa lọc hoặc lọc loại khác). Mọi thao tác tạo/sửa/xóa dịch vụ hoặc loại dịch vụ **không** tự động invalidate cache `service-types` (vì không cache), nhưng tạo/sửa/xóa **dịch vụ** vẫn bump version cache `services:list` như trước.

---

## 9. Giao diện người dùng

| Màn hình | Mô tả |
|----------|-------|
| **`/admin/service-types`** (mới) | Trang cấu hình danh sách loại dịch vụ — bảng CRUD (mã, tên, mô tả, thứ tự, trạng thái, badge Hệ thống/Tùy chỉnh). Loại hệ thống ẩn nút sửa/xóa (mirror giao diện `/admin/dosage-forms` TASK-076). Quyền: `service.manage`. |
| **`/admin/services`** (mở rộng) | Thêm select "Loại dịch vụ" (tải từ `/service-types`) trong modal tạo/sửa; thêm cột badge "Loại dịch vụ" trong bảng danh sách; nhập CSV/Excel có thêm cột `service_type_code` (map sang `service_type_id` tại thời điểm import, mã không khớp = bỏ trống/chưa phân loại, không báo lỗi import). |
| **ServicesTab (bác sĩ, màn khám bệnh)** | Picker tìm dịch vụ hiển thị badge loại dịch vụ cạnh tên dịch vụ (nếu có); dịch vụ chưa phân loại không hiển thị badge. |

Sidebar: mục điều hướng mới `admin:nav.serviceTypes` (icon `Tags`), quyền `service.manage`.

---

## 10. Ghi chú và lưu ý khi kiểm thử

### 10.1 Điểm quan trọng cần nắm

- `service_type` là bảng **per-clinic** (khác `dosage_form` — bảng toàn cục/dùng chung). Không có khái niệm "loại hệ thống dùng chung cho mọi clinic" ở đây — mỗi clinic có 3 dòng `is_system=true` **riêng của mình** (id khác nhau giữa các clinic dù cùng `code`).
- Dữ liệu `service` cũ (tạo trước migration `0071`) có `service_type_id = NULL` — đây là trạng thái hợp lệ, không phải lỗi cần fix.
- Đổi tên loại dịch vụ hệ thống **không** ảnh hưởng `id` — TASK-128 khóa theo `service_type_id`, không theo `name`/`code`. (Nhưng hiện tại loại hệ thống bị khóa hoàn toàn, không sửa được kể cả tên — xem BR-002; đây là quyết định thiết kế ưu tiên an toàn, có thể nới lỏng sau nếu cần).

### 10.2 Gợi ý dữ liệu kiểm thử

| Kịch bản | Giá trị đầu vào | Kết quả kỳ vọng |
|---------|----------------|----------------|
| Tạo dịch vụ không chọn loại | `service_type_id` bỏ trống | Tạo thành công, `service_type_id = NULL`, hiển thị "Chưa phân loại" |
| Lọc theo loại `consultation` | `GET /services?service_type_id={consultation_id}` | Chỉ trả dịch vụ đã gán đúng loại đó; dịch vụ NULL bị loại trừ |
| Gán `service_type_id` của clinic khác | `service_type_id` thuộc clinic B khi đang thao tác clinic A | `404 Not Found` |
| Sửa loại dịch vụ hệ thống | `PATCH /service-types/{consultation_id}` với `name` mới | `403 Forbidden` |
| Xóa loại tự thêm | Tạo loại mới → `DELETE` | `200 OK`, `is_deleted=true`; dịch vụ đang gán loại đó vẫn giữ nguyên `service_type_id` (không bị ảnh hưởng) |
| Nhập CSV với `service_type_code` không tồn tại | `service_type_code=unknown_code` | Dịch vụ vẫn được tạo, `service_type_id` để trống (không báo lỗi, không chặn import) |

### 10.3 Hạn chế hiện tại

- Không có cách xóa `service_type_id` đã gán về `NULL` qua API PATCH (giới hạn kế thừa từ `category`, xem mục 4.6).
- Loại dịch vụ hệ thống bị khóa hoàn toàn (không sửa tên/mô tả) — nếu về sau cần cho phép đổi tên (nhưng vẫn giữ id), cần nới lỏng `_ensure_editable` trong `service_type_service.py`.
- Chưa kiểm thử tích hợp với DB thật trong phiên làm việc này (môi trường không có sẵn stack Docker khả dụng ngoài stack `w2e` — theo chỉ đạo không được khởi động). Test tích hợp đã viết sẵn (`tests/integration/services/test_task125_service_type_e2e.py`), sẵn sàng chạy khi có DB.

### 10.4 Hướng phát triển

- TASK-128: Commission/chiết khấu % theo `service_type_id`.
- TASK-126: Báo cáo/thống kê nhóm theo `service_type_id`.
- Cân nhắc thêm bộ lọc loại dịch vụ ngay trên trang `/admin/services` (hiện tại chỉ có trong modal tạo/sửa và badge cột — chưa có dropdown lọc nhanh trên toolbar).

---

**Phê duyệt**

| Vai trò | Họ tên | Ngày |
|---------|--------|------|
| Trưởng nhóm kỹ thuật | | |
| Tester phụ trách | | |
| Khách hàng / PO | | |
