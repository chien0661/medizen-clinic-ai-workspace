# Implementation Plan: TASK-125

**Task:** Phân loại danh mục dịch vụ (service_type) — **cấu hình được** (admin tự quản lý danh sách loại)
**Date:** 2026-07-30
**Based on:** Code investigation on dev worktree (head `0070`).
**SCOPE DECISION (2026-07-30):** user chốt "cho cấu hình được" → service_type là **bảng cấu hình do admin quản lý**, KHÔNG phải enum cứng. Commission (TASK-128) tính **% theo loại dịch vụ** → khoá theo `service_type_id` của bảng này.

---

## Approach
Tạo bảng cấu hình **`service_type`** (per-clinic, admin CRUD) thay vì StrEnum cố định. `service` tham chiếu qua `service_type_id` (FK, nullable). Giữ nguyên `category` free-text (mục đích khác). Seed sẵn 3 loại mặc định (Khám / Thủ thuật / Xét nghiệm) cho clinic hiện có + clinic mới, nhưng admin có thể thêm/sửa/ẩn.

## Components
| Component | Action | Notes |
|-----------|--------|-------|
| `app/modules/services/models/service_type.py` | create | bảng cấu hình: id, clinic_id, code, name, is_active, sort_order; BaseEntity (soft-delete, audit). `__auditable__=True` |
| `app/modules/services/models/service.py` | modify | thêm `service_type_id` (FK→service_type.id, nullable) |
| `alembic/versions/0071_service_type.py` | create | tạo bảng service_type + seed 3 mặc định/clinic + cột `service.service_type_id`; **down_revision="0070"** |
| `app/modules/services/schemas/` | modify | `ServiceTypeCreate/Update/Response` + thêm `service_type_id`(+`service_type` name) vào Service schemas (Create/Update/Response) |
| `app/modules/services/services/service_type_service.py` | create | CRUD loại dịch vụ (list active, create, update, deactivate) |
| `app/modules/services/services/service_catalog_service.py` | modify | thread `service_type_id` qua create/update/list + filter; thêm vào `service_cache` params_key |
| `app/modules/services/api/routes.py` | modify | CRUD `/service-types` (gated bằng quyền quản lý danh mục); query param `service_type_id` cho list_services; cột export |
| FE `src/pages/admin/ServicesPage.tsx` + `src/modules/admin/{types,api}.ts` | modify | select loại (load từ /service-types), cột/badge, CSV import theo code loại |
| FE `src/pages/admin/ServiceTypesPage.tsx` (mới) | create | màn cấu hình danh sách loại dịch vụ (CRUD) |
| FE `src/components/doctor/ServicesTab.tsx` | modify | badge + filter theo loại |

## Implementation Steps
1. Model `service_type` + FK trên `service` + migration 0071 (seed 3 mặc định/clinic).
2. `service_type_service` CRUD + routes `/service-types`.
3. Thread `service_type_id` qua catalog service/schemas/list-filter/cache/export.
4. FE: ServiceTypesPage (cấu hình) + ServicesPage (select+badge) + ServicesTab (badge/filter).
5. Tests: CRUD loại; gán loại cho dịch vụ; filter; backfill dòng cũ = NULL (chưa phân loại) không vỡ billing.

## Dependencies
Không lib mới. **Blocker cho TASK-126** (nhóm theo loại) + **TASK-128** (`% theo service_type` khoá theo `service_type_id`).

## Risks / Notes
- Per-clinic seeding trong multi-tenant: migration phải seed cho mọi clinic hiện có (loop qua clinic) + hook tạo clinic mới cũng seed. Cân nhắc `is_system` để phân biệt loại mặc định vs admin tự thêm.
- `service_cache` params_key phải gồm `service_type_id` nếu không filter trả cache sai.
- Dòng service cũ `service_type_id=NULL` (chưa phân loại) — hợp lệ; admin phân loại dần. Commission chỉ áp cho service đã gán loại.

## Open Decisions (còn lại — không chặn)
- Có seed 3 mặc định hay để trống hoàn toàn cho admin tự tạo? (Kế hoạch: seed 3 + cho sửa.)
- Quyền quản lý `/service-types`: dùng quyền quản lý danh mục hiện có hay thêm quyền mới?
