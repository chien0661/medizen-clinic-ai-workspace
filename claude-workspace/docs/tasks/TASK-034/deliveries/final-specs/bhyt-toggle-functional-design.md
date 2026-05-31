---
task: TASK-034
title: BHYT Feature Toggle — Thiết kế chức năng
date: 2026-05-01
status: DONE
author: documentation-agent
---

# TASK-034: BHYT Feature Toggle — Thiết kế chức năng

**Task:** TASK-034 | **Ngày hoàn thành:** 2026-05-01 | **Status:** DONE

---

## Mục đích

CFG-017 yêu cầu một feature flag `bhyt_enabled` cấp phòng khám để kiểm soát toàn bộ tính năng Bảo hiểm Y tế (BHYT) trong hệ thống. Khi tắt (mặc định), mọi UI liên quan BHYT bị ẩn và mọi API `/bhyt/*` trả về 404. Khi bật, 11 khu vực UI được mở khoá đồng thời, giúp phòng khám áp dụng BHYT theo tiến trình của mình mà không ảnh hưởng các phòng khám chưa đăng ký BHYT.

---

## Phạm vi

- **10/11 UI gates được wire** trong TASK-034.
- **1 gate tạm hoãn** (Gate #7 — LabOrdersTab): component `LabOrdersTab` chưa tồn tại trong codebase; phụ thuộc TASK-033/041.
- **BE:** Python/FastAPI, Alembic migration, Redis cache.
- **FE:** React/TypeScript, Zustand store, react-i18next.

---

## Schema Migration — `0024_bhyt_toggle`

| Thành phần | Chi tiết |
|------------|---------|
| `down_revision` | `65fc9ae59ba5` (rescue đã sửa từ `0020b` — giải quyết multi-head conflict) |
| Cột thêm vào `clinic` | `bhyt_enabled BOOLEAN NOT NULL DEFAULT false` |
| Cột thêm vào `clinic` | `bhyt_facility_code VARCHAR(50) NULL` (regex: `^[0-9]{5}[A-Z]{4}$`) |
| Index | `ix_clinic_bhyt_enabled` (fast flag lookup) |
| Rollback | Xoá index → drop columns → DELETE seeded perms theo `code` |

**Permissions seeded** (INSERT `(code, description, category)` với `ON CONFLICT (code) DO NOTHING`):

| Code | Category |
|------|----------|
| `bhyt:read` | bhyt |
| `bhyt:write` | bhyt |
| `bhyt:config` | bhyt |
| `bhyt:reports` | bhyt |
| `vss:read` | vss |
| `vss:sync` | vss |

---

## Feature Flag Primitive (`app/core/feature_flags.py`)

### `require_feature(flag: str)` — FastAPI Dependency

- Đọc `current_clinic_id` từ **ContextVar** (forward-compatible với TASK-033 multi-clinic JWT).
- Trả về `404 Not Found` khi flag OFF.
- Trả về `401 Unauthorized` khi không có clinic context.
- Flag không xác định → trả về `False` (fail-safe, log warning).
- Clinic không tồn tại → trả về `False` (fail-safe).

### Redis Cache

- Key pattern: `clinic:flags:{clinic_id}:{flag}`
- TTL: **5 phút**
- Graceful degradation: nếu Redis lỗi, fallback về DB query.
- Invalidation: `invalidate_feature_flag_cache(clinic_id, flag=None)` — hỗ trợ xoá per-flag hoặc pattern delete toàn bộ flag của clinic.

---

## RBAC Permission Filter

Hàm `_apply_feature_flag_gates()` trong `rbac_service.py`:

- Strips toàn bộ `bhyt:*`, `vss:*`, `report.bhyt.*` khỏi effective permissions khi flag OFF.
- **Fast path:** bỏ qua DB lookup nếu user không có quyền BHYT nào trong set.
- Tái sử dụng `_cache_get_flag` / `_cache_set_flag` từ `feature_flags` module (single source of truth cho cache).

> **Lưu ý stale-cache (Finding 3 từ review):** `get_user_effective_permissions` cache post-gate result tại `user:perms:{user_id}` 5 phút. Sau khi toggle, user có cache cũ giữ perm set stale tối đa 5 phút. Tác động thực tế là cosmetic vì `require_feature` là primary gate ở endpoint level (endpoint đã 404 trước khi perm check có nghĩa). Follow-up: thêm `invalidate_user_cache` loop cho tất cả user của clinic khi toggle.

---

## API Endpoint — `PATCH /api/v1/settings/bhyt`

| Thuộc tính | Giá trị |
|-----------|---------|
| Method | `PATCH` |
| Path | `/api/v1/settings/bhyt` |
| Auth | `Depends(require_permission("bhyt:config"))` |
| Request body | `{enabled: bool, facility_code: str \| null}` |
| Validation | `facility_code` bắt buộc khi `enabled=True`; regex `^[0-9]{5}[A-Z]{4}$`; auto-clear khi disable |
| Side effect | Gọi `invalidate_feature_flag_cache(clinic_id, "bhyt")` |
| GET không gated | Endpoint GET không require feature flag (cần để bootstrap toggle UI khi flag đang OFF) |

> **Audit log (Finding 2 từ review — deferred):** Hiện tại chỉ có `log.info("bhyt_settings_updated", ...)` vào structlog. `app.core.audit.audit_write` tồn tại và các setting khác đã ghi vào `audit_log` table. Follow-up: gọi `audit_write(action="settings.bhyt.toggle", entity_type="clinic", entity_id=clinic_id, old_data, new_data)`.

---

## 11 UI Areas — Gate Table

| # | Khu vực | Status | Gate location | Ghi chú |
|---|---------|--------|--------------|---------|
| 1 | Settings tab "BHYT" | WIRED ✅ | `SettingsPage.tsx` | BHYT tab hidden khi flag OFF qua dynamic TABS array |
| 2 | Reports tab "BHYT" | WIRED ✅ | `Sidebar.tsx` | Dynamic sub-item injection dưới Reports group |
| 3 | VSS Integrations panel | WIRED ✅ | `BhytReportPage.tsx` | Folded vào BHYT report page; pragma: extract khi IntegrationsPage ra đời (TASK-040+) |
| 4 | ServicesPage "Giá BHYT" column | WIRED ✅ | `ServicesPage.tsx` | Column ẩn khi flag OFF |
| 5 | PatientRegisterPage "Số thẻ BHYT" field | WIRED ✅ | `PatientRegisterPage.tsx` | `{bhytEnabled && <div data-testid="bhyt-card-field">}` |
| 6 | PrescriptionTab "BHYT line" | WIRED ✅ | `PrescriptionTab.tsx` | Checkbox + hint text gated |
| 7 | LabOrdersTab "BHYT chỉ định" | DEFERRED ⏸ | N/A | Component chưa tồn tại; phụ thuộc TASK-033/041 |
| 8 | InvoiceDetailPage "BHYT line" | WIRED ✅ | `InvoiceDetailPage.tsx` | Column header + cells gated symmetrically; grand_total không bị ảnh hưởng |
| 9 | Sidebar nav "BHYT" | WIRED ✅ | `Sidebar.tsx` | Sub-item `reports-bhyt`, idempotent (`alreadyHasBhyt` check), perm: `bhyt:reports` |
| 10 | PatientDetail "Lịch sử BHYT" tab | WIRED ✅ | `PatientDetailPage.tsx` | DevPlaceholder per TASK-040 coordination |
| 11 | MedicinesPage "Có BHYT" filter | WIRED ✅ | `MedicinesPage.tsx` | Filter checkbox gated |

**Tổng kết: 10/11 implemented. Gate #7 deferred.**

---

## i18n Coverage

### Namespaces mới

| File | Keys |
|------|------|
| `vi/admin.json` + `en/admin.json` | `bhyt.*` block (config + report keys), `settings.tabs.bhyt` |
| `vi/reception.json` + `en/reception.json` | `detail.tabs.bhytHistory`, `detail.bhytHistoryStub`, `register.fields.bhyt*` |
| `vi/reports.json` + `en/reports.json` | `nav.bhyt` |

### 4 keys bổ sung sau review (post-fix TASK-034)

| Key | vi | en | File |
|-----|----|----|------|
| `services.columns.bhytPrice` | `"Giá BHYT"` (đã có) | `"BHYT Price"` (thêm mới) | `admin.json` |
| `medicines.filterBhyt` | `"Có BHYT"` (đã có) | `"BHYT Coverage"` (thêm mới) | `admin.json` |
| `billing:invoiceDetail.lines.bhytLine` | `"Dòng BHYT"` (thêm mới) | `"BHYT Line"` (thêm mới) | `billing.json` |
| `doctor:prescription.bhytLine` | `"Có BHYT"` (thêm mới) | `"BHYT Eligible"` (thêm mới) | `doctor.json` |
| `doctor:prescription.bhytLineHint` | `"Đánh dấu thuốc thuộc danh mục BHYT"` (thêm mới) | `"Mark medicine as BHYT-covered"` (thêm mới) | `doctor.json` |

---

## Test Coverage

| Layer | Tests | Result |
|-------|-------|--------|
| BE — `test_feature_flags.py` | 18 | ✅ Pass |
| BE — `test_bhyt_settings.py` | 15 | ✅ Pass |
| BE — `test_bhyt_endpoints_gated.py` (integration) | 10 | ✅ Pass |
| **BE Total** | **33** | **✅ 33/33** |
| FE — Vitest full suite | 547 | ✅ Pass |
| FE — TypeScript | 0 errors | ✅ |
| FE — ESLint | 0 warnings | ✅ |
| **FE Total** | **547** | **✅ 547/547** |

---

## Cross-Task Coordination

### Wave 3-A Column Encryption

`bhyt_facility_code` là organizational identifier (không phải personal PII), nhưng mã cơ sở VSS có thể được coi là sensitive theo quy định bảo hiểm y tế Việt Nam. **Flag cho SECURITY.md review** trong Wave 3-A encryption planning — quyết định có đưa `clinic.bhyt_facility_code` vào Tier-3 encrypted columns không.

### Wave 3-B Sidebar Refactor

BHYT sub-item hiện được inject vào Reports group qua dynamic `effectiveNavItems` mapping. Khi sidebar refactor sang role-grouped layout, đảm bảo injection logic được preserve và xem xét lại placement của BHYT (có thể chuyển sang group Insurance/Integrations mới).

### TASK-033 Multi-Clinic

Forward-compatible: `current_clinic_id` ContextVar dùng cùng tên; `bhyt_enabled` column là per-clinic.

---

## Decisions Deferred

| Item | Lý do | Follow-up |
|------|-------|-----------|
| Gate #7 LabOrdersTab | `LabOrdersTab` component chưa tồn tại | Khi TASK-033/041 tạo component, wrap BHYT chỉ định block với `bhytEnabled && (...)` |
| Audit log trên settings PATCH | Finding 2 từ review — không blocking | Thêm `audit_write(action="settings.bhyt.toggle")` trong follow-up |
| User-perm cache invalidation khi toggle | Finding 3 từ review — tác động cosmetic | Thêm `invalidate_user_cache` loop cho clinic users khi toggle |
| VssSyncPanel extraction | Hiện co-located với BhytReportPage | Extract sang `pages/integrations/VssIntegrationPage.tsx` khi IntegrationsPage ra đời |
