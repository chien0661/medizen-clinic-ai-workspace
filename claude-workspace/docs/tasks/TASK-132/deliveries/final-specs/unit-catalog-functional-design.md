# Thiết Kế Chi Tiết Tính Năng: Unit — Danh mục đơn vị cấu hình được + Combobox creatable

**Dự án:** Clinic CMS
**Task:** TASK-132
**Phiên bản:** 1.0
**Ngày:** 2026-07-31
**Người thực hiện:** Code Implementation Agent
**Trạng thái:** Đã triển khai (BE + FE) — chờ Code Review / Test
**Tài liệu liên quan:** TASK-125 (Service Type — mẫu tham chiếu bảng cấu hình per-clinic), TASK-131 (usage_unit dropdown — nguồn gốc yêu cầu mở rộng), TASK-124 (unit_conversion — factor table KHÔNG PHẢI danh mục unit), task.md

---

## Lịch sử thay đổi

| Phiên bản | Ngày | Nội dung thay đổi |
|-----------|------|-------------------|
| 1.0 | 2026-07-31 | Phiên bản đầu tiên — hoàn tất Implementation, sẵn sàng Review |

---

## Mục lục

- [1. Tổng quan tính năng](#1-tổng-quan-tính-năng)
- [2. Kiểm tra khái niệm unit đã tồn tại](#2-kiểm-tra-khái-niệm-unit-đã-tồn-tại)
- [3. Luồng xử lý tổng thể](#3-luồng-xử-lý-tổng-thể)
- [4. Danh sách API](#4-danh-sách-api)
- [5. Cấu trúc cơ sở dữ liệu](#5-cấu-trúc-cơ-sở-dữ-liệu)
- [6. Quy tắc nghiệp vụ](#6-quy-tắc-nghiệp-vụ)
- [7. Combobox creatable (FE)](#7-combobox-creatable-fe)
- [8. Giao diện người dùng](#8-giao-diện-người-dùng)
- [9. Ghi chú và lưu ý khi kiểm thử](#9-ghi-chú-và-lưu-ý-khi-kiểm-thử)

---

## 1. Tổng quan tính năng

### 1.1 Mục đích

Các ô "đơn vị" trong form thuốc (`base_unit` / `sell_unit` / `purchase_unit` / `usage_unit` — TASK-124/TASK-131) hiện là các cột `String` tự do, và FE dùng dropdown **hardcode** danh sách 11 giá trị (viên/vỉ/gói/ống/chai/lọ/tuýp/ml/gam/miếng/cái). TASK-132 bổ sung:

1. Bảng cấu hình **`unit`** — per-clinic, admin quản lý được (giống TASK-125 `service_type`), seed sẵn 11 đơn vị mặc định.
2. Component **combobox creatable** dùng chung: chọn từ danh mục HOẶC gõ đơn vị chưa có + xác nhận → tự động `POST` tạo mới vào danh mục rồi chọn luôn — không cần rời màn hình thuốc để vào trang quản trị riêng.

Đây **không** thay đổi kiểu dữ liệu của các cột `base_unit`/`sell_unit`/`purchase_unit`/`usage_unit` trên `medicine` — chúng vẫn là chuỗi tự do (không có FK tới `unit`). Danh mục `unit` chỉ là nguồn gợi ý/tạo nhanh cho combobox và trang quản trị; không ép buộc constraint DB giữa `medicine.*_unit` và `unit.code`.

### 1.2 Phạm vi

**Bao gồm:**
- Bảng cấu hình **`unit`** — mỗi clinic tự quản lý danh sách đơn vị riêng (per-clinic, giống `service_type`, khác `dosage_form` toàn cục).
- Seed sẵn **11 đơn vị mặc định** cho mỗi clinic đang tồn tại tại thời điểm migration: viên/vỉ/gói/ống/chai/lọ/tuýp/ml/gam/miếng/cái — `is_system=true`.
- Clinic tạo mới sau này cũng được seed 11 đơn vị mặc định tương tự (hook trong `clinic_service.create_clinic`).
- API CRUD `/units` (list/create/get/update/delete) + `/units/quick-create` (get-or-create theo tên, dùng cho combobox) — dùng lại quyền `inventory.read` / `inventory.manage_catalog` sẵn có, **không thêm quyền mới**.
- FE: component `CreatableCombobox` dùng chung (`src/components/ui/creatable-combobox.tsx`), áp dụng cho cả 4 ô đơn vị của form thuốc (`base_unit`, `purchase_unit`, `sell_unit`, `usage_unit`).
- FE admin: trang **"Danh mục đơn vị"** (`/admin/units`) — CRUD, khóa `is_system`, mirror `ServiceTypesPage`.

**Không bao gồm:**
- Không thêm FK ràng buộc giữa `medicine.*_unit` và `unit.code` — các cột vẫn là chuỗi tự do (giữ tương thích ngược tuyệt đối, không có rủi ro chặn lưu dữ liệu cũ).
- Không thay đổi bảng `unit_conversion` (TASK-124 — bảng hệ số quy đổi giữa 2 đơn vị của MỘT thuốc cụ thể, khái niệm hoàn toàn khác với danh mục `unit` mới này).
- Không mở rộng combobox creatable ra các picker đơn vị khác ngoài form thuốc (ví dụ PrescriptionTab bác sĩ) — nằm ngoài phạm vi yêu cầu TASK-132 ("tối thiểu áp cho form thuốc").

### 1.3 Các bên liên quan

| Vai trò | Mô tả |
|---------|-------|
| **Quản trị viên phòng khám (admin)** | Quyền `inventory.manage_catalog` — quản lý danh mục đơn vị (thêm/sửa/ẩn; đơn vị hệ thống chỉ xem). |
| **Dược sĩ (pharmacist)** | Quyền `inventory.manage_catalog`/`medicine.manage` — chỉnh sửa thuốc, tạo đơn vị mới ngay tại combobox. |
| **Bác sĩ/Điều dưỡng** | Quyền `inventory.read` — xem danh mục (không sửa). |

---

## 2. Kiểm tra khái niệm unit đã tồn tại

Trước khi tạo bảng mới, đã rà soát toàn bộ BE để tránh trùng khái niệm (theo yêu cầu task — TASK-050 seed có nhắc "units"):

| Đã tìm thấy | Vai trò thực tế | Có phải danh mục unit không? |
|-------------|------------------|-------------------------------|
| `app/modules/inventory/services/unit_service.py` | Resolver quy đổi số lượng giữa `base_unit` và unit khác của **một medicine cụ thể** (TASK-124) — đọc từ `Medicine.unit_conversions`, không có bảng riêng. | **Không** — đây là logic tính toán, không phải danh mục mã đơn vị. |
| `app/modules/inventory/models/unit_conversion.py` (`UnitConversion`) | Bảng hệ số quy đổi `(medicine_id, from_unit, to_unit, factor)` — `from_unit`/`to_unit` vẫn là **chuỗi tự do**, không tham chiếu tới danh mục nào. | **Không** — không phải danh mục, không có `code`/`name`/`is_system`. |
| `DosageForm.unit` (cột đơn lẻ trên `dosage_form`) | Một cột string đơn (đơn vị mặc định gợi ý theo dạng bào chế), không phải bảng danh mục. | **Không**. |
| `medicine.base_unit` / `sell_unit` / `purchase_unit` / `usage_unit` | Cột `String` tự do trên `medicine`, giá trị nhập tay hoặc chọn từ dropdown hardcode FE. | **Không** — đây chính là nơi cần danh mục hỗ trợ, không phải bản thân danh mục. |

**Kết luận:** Không có bảng danh mục unit (danh sách mã + tên đơn vị dùng chung, quản lý CRUD được) tồn tại trước TASK-132. Quyết định: **tạo mới** bảng `unit`, KHÔNG tái sử dụng `unit_conversion`/`unit_service.py` (khác mục đích hoàn toàn — factor quy đổi vs. danh mục mã đơn vị).

---

## 3. Luồng xử lý tổng thể

```
[Migration 0075]
      │  Tạo bảng unit + seed 11 đơn vị mặc định cho MỖI clinic hiện có
      ▼
[Admin UI /admin/units]                    [Form thuốc /admin/medicines]
      │  CRUD đơn vị (đơn vị hệ thống          │  4 ô: base_unit / purchase_unit /
      │  chỉ đọc — không sửa/xóa được)          │  sell_unit / usage_unit
      ▼                                         ▼
[unit_catalog_service — BE]            [CreatableCombobox — FE]
      │  Validate: code duy nhất/clinic,        │  gõ mới + xác nhận "Tạo '<x>'"
      │  is_system chặn sửa/xóa                 ▼
      ▼                                   POST /units/quick-create (get-or-create theo tên)
[unit table] ◄─────────────────────────────────┘
      │
      ▼
GET /units nạp danh sách gợi ý cho combobox (không ép buộc FK — medicine.*_unit
vẫn là chuỗi tự do, lưu được cả giá trị không có trong danh mục)

[Tạo phòng khám mới] ──► clinic_service.create_clinic ──► seed_defaults_for_clinic (11 đơn vị mặc định)
```

**Điểm khác biệt quan trọng so với TASK-125 (service_type → service.service_type_id là FK bắt buộc kiểm tra):**
Ở đây `medicine.base_unit`/`sell_unit`/`purchase_unit`/`usage_unit` **không** có FK tới `unit.code` — vì các cột này đã tồn tại từ trước (TASK-012/124/131) dưới dạng chuỗi tự do, và hàng nghìn medicine/prescription/invoice lịch sử đã lưu giá trị theo cách đó. Thêm FK constraint sẽ có rủi ro phá vỡ dữ liệu cũ (giá trị lịch sử không khớp `unit.code` nào). Vì vậy `unit` chỉ đóng vai trò "nguồn gợi ý + tạo nhanh", không phải ràng buộc toàn vẹn dữ liệu — đúng tinh thần "additive, behavior-neutral" mà migration yêu cầu.

---

## 4. Danh sách API

**Đường dẫn gốc (Base Path):** `/api/v1`

| STT | Phương thức | Đường dẫn | Quyền yêu cầu | Mô tả tóm tắt |
|-----|------------|-----------|---------------|--------------|
| 1 | GET | `/api/v1/units` | `inventory.read` | Danh sách đơn vị của clinic hiện tại |
| 2 | POST | `/api/v1/units` | `inventory.manage_catalog` | Tạo đơn vị tùy chỉnh mới (dùng bởi trang admin) |
| 3 | POST | `/api/v1/units/quick-create` | `inventory.manage_catalog` | Get-or-create theo tên hiển thị (dùng bởi combobox creatable) |
| 4 | GET | `/api/v1/units/{id}` | `inventory.read` | Xem chi tiết 1 đơn vị |
| 5 | PATCH | `/api/v1/units/{id}` | `inventory.manage_catalog` | Sửa đơn vị (403 nếu là đơn vị hệ thống) |
| 6 | DELETE | `/api/v1/units/{id}` | `inventory.manage_catalog` | Xóa mềm đơn vị (403 nếu là đơn vị hệ thống) |

> **Không có quyền mới** — `/units` dùng lại `inventory.read`/`inventory.manage_catalog` (đã seed từ migration `0017a`, gán cho `admin` + `pharmacist`) — cùng ranh giới quyền với `/medicines` và các danh mục inventory khác (`/dosage-forms` dùng `dosage_form.read/manage` riêng; `units` chọn `inventory.*` vì phạm vi sử dụng chính là form thuốc, do admin+pharmacist thao tác).

Chi tiết đầy đủ (request/response mẫu, mã lỗi) xem [`unit-api.md`](../api-specs/unit-api.md).

---

## 5. Cấu trúc cơ sở dữ liệu

### Bảng: `unit`

| Tên cột | Kiểu dữ liệu | Bắt buộc | Mô tả |
|---------|-------------|---------|-------|
| `id` | UUID | Có | Khóa chính |
| `clinic_id` | UUID | Có | FK → `clinic.id` (RESTRICT) — **NOT NULL** (per-clinic, giống `service_type`) |
| `code` | VARCHAR(50) | Có | Mã đơn vị, chữ thường ascii (vd `vien`, `ong-hut`) |
| `name` | VARCHAR(200) | Có | Tên hiển thị (vd "viên", "Ống hút") |
| `description` | VARCHAR(500) | Không | Mô tả |
| `is_active` | Boolean | Có | Mặc định `true` |
| `sort_order` | Integer | Có | Mặc định `0` |
| `is_system` | Boolean | Có | `true` = 1 trong 11 đơn vị seed sẵn, không sửa/xóa được |
| `is_deleted`, `deleted_at`, `deleted_by` | — | — | Soft-delete (BaseEntity) |
| `created_at`, `updated_at`, `created_by`, `updated_by`, `version` | — | — | Audit + optimistic lock (BaseEntity) |

**Ràng buộc duy nhất:** `UNIQUE (clinic_id, code) WHERE is_deleted = false` (index `uq_unit_clinic_code_active`).

**RLS:** bật tenant isolation tiêu chuẩn (`apply_rls_with_tenant_isolation`) + grant `cms_app`. Seed chạy **trước** khi bật RLS (giống thứ tự migration `0070`) để an toàn khi chạy với role không phải superuser.

### Seed 11 đơn vị mặc định

| `code` | `name` | `sort_order` |
|--------|--------|--------------|
| `vien` | viên | 1 |
| `vi` | vỉ | 2 |
| `goi` | gói | 3 |
| `ong` | ống | 4 |
| `chai` | chai | 5 |
| `lo` | lọ | 6 |
| `tuyp` | tuýp | 7 |
| `ml` | ml | 8 |
| `gam` | gam | 9 |
| `mieng` | miếng | 10 |
| `cai` | cái | 11 |

Seed chạy ở 2 nơi, cùng logic (idempotent — kiểm tra code đã tồn tại trước khi chèn), mã/tên **phải khớp** giữa migration `0075` và `unit_catalog_service.DEFAULT_UNITS`:
1. **Migration `0075`** (raw SQL, `id` sinh bằng `uuid5(NAMESPACE_OID, f"unit:{clinic_id}:{code}")`) — cho mọi clinic **đang tồn tại** tại thời điểm chạy migration.
2. **`clinic_service.create_clinic`** (gọi `unit_catalog_service.seed_defaults_for_clinic` qua ORM) — cho clinic **tạo sau** thời điểm migration.

---

## 6. Quy tắc nghiệp vụ

| Mã | Mô tả quy tắc | Hành vi khi vi phạm |
|----|--------------|---------------------|
| BR-001 | Mỗi clinic được seed đúng 11 đơn vị mặc định, đánh dấu `is_system=true`. | — (tự động) |
| BR-002 | Đơn vị có `is_system=true` **không thể sửa hoặc xóa** qua API. | `403 Forbidden` |
| BR-003 | Đơn vị tự thêm (`is_system=false`, qua trang admin HOẶC qua combobox quick-create) có thể sửa/ẩn/xóa mềm tự do bởi người có quyền `inventory.manage_catalog`. | — |
| BR-004 | `code` của đơn vị duy nhất theo clinic (không phân biệt hoa/thường), chỉ tính bản ghi chưa xóa. | `409 Conflict` (áp dụng cho `POST /units`) |
| BR-005 | `POST /units/quick-create` là **idempotent theo `name`** (không phân biệt hoa/thường, đã trim khoảng trắng) — gọi lại nhiều lần với cùng tên trả về **cùng một row**, không tạo trùng. | — (get-or-create, không lỗi 409) |
| BR-006 | `medicine.base_unit`/`sell_unit`/`purchase_unit`/`usage_unit` **không** bị ràng buộc phải khớp với `unit.code`/`unit.name` — vẫn là chuỗi tự do; combobox chỉ gợi ý, không chặn lưu giá trị "lạ". | — (behavior-neutral, không hồi quy dữ liệu cũ) |
| BR-007 | Code cho `quick-create` được suy ra tự động từ tên hiển thị (bỏ dấu, chuyển thường, thay khoảng trắng bằng `-`); nếu trùng code đã tồn tại, tự thêm hậu tố số (`-2`, `-3`, ...). | — |

---

## 7. Combobox creatable (FE)

### 7.1 Component

`src/components/ui/creatable-combobox.tsx` — `CreatableCombobox` là primitive dùng chung (không riêng cho `unit`), nhận:
- `value: string`, `onChange: (label: string) => void` — controlled, giống input thường (dùng qua `Controller` của react-hook-form vì đây không phải input thô).
- `options: ComboboxOption[]` — danh sách gợi ý (map từ `Unit[]` sang `{id, label: name, isActive}`).
- `onCreate: (label: string) => Promise<ComboboxOption>` — gọi `POST /units/quick-create`.

### 7.2 Hành vi

1. Gõ chữ → lọc option theo substring (không phân biệt hoa/thường, **có** phân biệt dấu — "vi" không khớp "vỉ").
2. Gõ trùng khớp chính xác (không phân biệt hoa/thường) với 1 option → dropdown hiển thị option đó, có dấu tick, **không** hiện "Tạo".
3. Gõ giá trị chưa có → dòng cuối dropdown hiện `Tạo "<giá trị>"`. Click hoặc nhấn Enter → gọi `onCreate` → khi thành công, chọn giá trị mới tạo (input + form field cập nhật theo tên trả về từ BE).
4. **Không bắt buộc phải xác nhận "Tạo"** — mọi keystroke đều gọi `onChange` ngay lập tức, giữ đúng hành vi cũ của `<select>` (free text vẫn lưu được nếu người dùng không confirm) — không có rủi ro chặn lưu form thuốc.
5. Guard chống double-submit: dùng `useRef` đồng bộ (không chỉ dựa vào state React, vì state không đảm bảo cập nhật đồng bộ trong cùng tick sự kiện) để click/Enter liên tiếp không gọi `onCreate` 2 lần.
6. Lỗi khi tạo (network/permission) — component **nuốt lỗi** (không crash, giữ dropdown mở để thử lại); phía gọi (`MedicinesPage`) chịu trách nhiệm hiển thị toast qua try/catch quanh lệnh gọi `adminUnitsApi.quickCreate`.

### 7.3 Áp dụng vào form thuốc

Cả 4 ô đơn vị trong `MedicinesPage.tsx` đã chuyển sang `CreatableCombobox` (qua `Controller`):
- `base_unit` (Đơn vị tồn kho — bắt buộc, `min(1)`)
- `purchase_unit` (Đơn vị nhập — tùy chọn)
- `sell_unit` (Đơn vị bán/cấp phát — tùy chọn)
- `usage_unit` (Đơn vị dùng, TASK-131 — tùy chọn)

Danh sách gợi ý dùng chung 1 query `["admin", "units"]` (`adminUnitsApi.list({is_active:true})`) cho cả 4 ô — tạo mới ở bất kỳ ô nào cũng invalidate cache, các ô khác thấy ngay đơn vị mới.

---

## 8. Giao diện người dùng

| Màn hình | Mô tả |
|----------|-------|
| **`/admin/units`** (mới) | Trang cấu hình danh sách đơn vị — bảng CRUD (mã, tên, mô tả, thứ tự, trạng thái, badge Hệ thống/Tùy chỉnh). Đơn vị hệ thống ẩn nút sửa/xóa (mirror `/admin/service-types` TASK-125). Quyền: `inventory.manage_catalog`. |
| **`/admin/medicines`** (mở rộng) | 4 ô đơn vị chuyển từ `<select>` sang `CreatableCombobox` — gõ mới + xác nhận tạo ngay tại chỗ. |

Sidebar: mục điều hướng mới `admin:nav.units` (icon `Tags`), quyền `inventory.manage_catalog`.

---

## 9. Ghi chú và lưu ý khi kiểm thử

### 9.1 Điểm quan trọng cần nắm

- `unit` là bảng **per-clinic** (giống `service_type`, khác `dosage_form`) — không có "đơn vị hệ thống dùng chung toàn cục"; mỗi clinic có 11 dòng `is_system=true` **riêng của mình**.
- KHÔNG có FK giữa `medicine.*_unit` và `unit` — xem mục 1.1/6/BR-006. Test không cần lo về ràng buộc toàn vẹn giữa 2 bảng.
- `quick-create` là **get-or-create theo `name`** (không phải theo `code`) — gọi 2 lần cùng tên (khác hoa/thường, có/không khoảng trắng thừa) trả về cùng 1 row.

### 9.2 Hạn chế hiện tại

- Chưa mở rộng combobox creatable sang các picker đơn vị khác ngoài form thuốc (vd PrescriptionTab bác sĩ) — nằm ngoài phạm vi tối thiểu yêu cầu.
- Chưa kiểm thử tích hợp với DB thật trong phiên làm việc này (không khởi động DB stack ngoài stack `w2e` theo chỉ đạo). Test tích hợp đã viết sẵn (`tests/integration/inventory/test_task132_unit_catalog_e2e.py`), sẵn sàng chạy khi có DB qua `docker-api:latest`.
- Unit tests (mock, không cần DB) đã chạy và PASS (10/10) qua `docker run --rm docker-api:latest pytest tests/unit/services/test_unit_catalog_service.py`.

### 9.3 Hướng phát triển

- Cân nhắc mở rộng combobox creatable sang PrescriptionTab (bác sĩ kê đơn) nếu có nhu cầu tương lai.
- Cân nhắc thêm cột "Số thuốc đang dùng" trên trang `/admin/units` để admin biết trước khi ẩn 1 đơn vị tùy chỉnh có đang được tham chiếu tự do bởi medicine nào không (hiện tại không kiểm tra, vì không có FK ràng buộc).

---

**Phê duyệt**

| Vai trò | Họ tên | Ngày |
|---------|--------|------|
| Trưởng nhóm kỹ thuật | | |
| Tester phụ trách | | |
| Khách hàng / PO | | |
