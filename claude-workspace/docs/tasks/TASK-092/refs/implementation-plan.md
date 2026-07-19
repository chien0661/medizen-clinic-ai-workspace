# Implementation Plan: TASK-092

**Task:** Nâng cấp màn hình Super Admin — tập trung quản lý hệ thống, tài khoản, người dùng & cấu hình hệ thống
**Date:** 2026-07-16
**Based on:**
- Yêu cầu người dùng + quyết định planning (4 câu hỏi, phiên `/task-plan`)
- Khảo sát code hiện trạng: `clinic-cms-web/src/{pages,modules,components}/superadmin*`, `router/index.tsx`, `components/shell/Sidebar.tsx`
- `clinic-cms/app/modules/superadmin/{api/routes.py,service.py,schemas.py}`
- Kế thừa TASK-070 (Super Admin console), TASK-071 (Analytics)

---

## Quyết định phạm vi (chốt tại planning)

| Chủ đề | Quyết định |
|---|---|
| "Tài khoản" vs "Người dùng" | **Gộp làm 1 màn** quản lý duy nhất (list + tạo/sửa/khóa/reset password). Không tách entity. |
| Nội dung "Cấu hình hệ thống" | Đủ 4 phần: (1) Feature flags mặc định toàn hệ thống, (2) Chính sách bảo mật/mật khẩu, (3) Email/SMTP & thông báo, (4) Thông tin & vận hành (maintenance mode, version). |
| Analytics + Audit Logs | **Giữ cả 2**, gom dưới nhóm "Quản lý hệ thống". |
| Backend | **Được phép thêm BE** khi cần (endpoint + migration mới cho system-config). |

---

## Hiện trạng (baseline)

**FE** (`clinic-cms-web`) — superuser CHỈ thấy khu Super Admin (`Sidebar.tsx`, `isSuperuser` ẩn nav nghiệp vụ):
- Pages: `SuperAdminDashboardPage`, `SuperAdminAnalyticsPage`, `SuperAdminClinicsPage`, `SuperAdminAccountsPage`, `SuperAdminAuditLogsPage`
- Routes `/superadmin[/analytics|/clinics|/accounts|/audit-logs]` — tất cả bọc `RequireSuperuser`
- Sidebar `SUPERADMIN_NAV_ITEMS`: Tổng quan · Thống kê · Phòng khám · Tài khoản · Audit Logs (danh sách phẳng, không phân nhóm)
- Module: `modules/superadmin/{api.ts,types.ts}`

**BE** (`clinic-cms/app/modules/superadmin/`) — endpoint đã có (mọi endpoint yêu cầu `is_superuser`, bypass RLS):
`stats` · `clinics` (list/create/update/export) · `clinics/{id}/features` (get/put) · `accounts` (list/create/update/reset-password/export) · `roles` · `permissions` · `audit-logs` (list/export) · `analytics/{overview,timeseries,clinics}`

**Khoảng trống chính:** chưa có màn/BE "Cấu hình hệ thống" toàn cục. Chỉ có: env-based (`app/core/config.py`), email client (`app/integrations/email/`), per-clinic feature toggle. → cần tạo mới platform-level `system_config`.

---

## Approach

Chia làm 2 nhánh song song: **(A) Tái tổ chức + gom điều hướng FE** quanh 4 nhóm (chủ yếu dùng lại API sẵn có), và **(B) Xây mới màn + BE cho "Cấu hình hệ thống"**. Ưu tiên A trước (thấy kết quả nhanh, ít rủi ro), B là phần lớn công sức mới.

**Cấu trúc điều hướng Super Admin sau nâng cấp** (Sidebar phân nhóm có tiêu đề):

```
QUẢN LÝ HỆ THỐNG
  • Tổng quan            /superadmin              (stats dashboard)
  • Phòng khám           /superadmin/clinics      (clinics/tenants + feature toggle)
  • Thống kê             /superadmin/analytics
  • Audit Logs           /superadmin/audit-logs

TÀI KHOẢN & NGƯỜI DÙNG
  • Tài khoản            /superadmin/accounts     (màn gộp duy nhất)

CẤU HÌNH HỆ THỐNG
  • Cấu hình hệ thống    /superadmin/system-config   (MỚI — dạng tabbed 4 phần)
```

> Nguyên tắc: superuser tuyệt đối không thấy nav nghiệp vụ phòng khám (logic `!isSuperuser` hiện có giữ nguyên). Không thêm mục ngoài 4 nhóm.

---

## Components

### Frontend (`clinic-cms-web`)

| Component | Action | Notes |
|-----------|--------|-------|
| `components/shell/Sidebar.tsx` | modify | Chuyển `SUPERADMIN_NAV_ITEMS` (list phẳng) → cấu trúc **phân nhóm** (3 group header: Quản lý hệ thống / Tài khoản & Người dùng / Cấu hình hệ thống). Thêm item Cấu hình hệ thống. Reorder Audit Logs vào nhóm hệ thống. |
| `pages/superadmin/SuperAdminSystemConfigPage.tsx` | **create** | Màn mới, tabbed: 4 tab (Feature mặc định · Bảo mật/Mật khẩu · Email/Thông báo · Thông tin & Vận hành). react-hook-form + zod mỗi tab, lưu độc lập. |
| `pages/superadmin/SuperAdminAccountsPage.tsx` | modify | Xác nhận là màn gộp TK+Người dùng; bổ sung cột/hành động còn thiếu (họ tên, email, vai trò, khóa/mở, reset mật khẩu) trong 1 màn. Rà lại phân trang/export theo chuẩn TASK-091. |
| `pages/superadmin/SuperAdminDashboardPage.tsx` | modify | Chỉnh tiêu đề/nhóm cho khớp điều hướng mới (nếu có link nội bộ). |
| `modules/superadmin/api.ts` | modify | Thêm `superAdminSystemConfigApi` (get/update theo section). |
| `modules/superadmin/types.ts` | modify | Thêm types `SystemConfig`, `SystemConfigSection*` (features_default / security_policy / email / system_info). |
| `router/index.tsx` | modify | Thêm route `/superadmin/system-config` bọc `RequireSuperuser` + lazy import. |
| `locales/{vi,en}/admin.json` | modify | i18n nhãn nhóm + tab + field mới. |
| `tests/superadmin/*` | create/modify | Unit test cho SystemConfigPage + Sidebar phân nhóm + RequireSuperuser (đã có, mở rộng). |

### Backend (`clinic-cms/app/modules/superadmin/`)

| Component | Action | Notes |
|-----------|--------|-------|
| `alembic/versions/NNNN_system_config.py` | **create** | Bảng `system_config` **singleton, KHÔNG tenant-scoped** (không có `clinic_id`, không RLS) — chỉ superuser truy cập qua guard. Lưu dạng JSONB theo section, hoặc bảng key-value (`section` PK + `data` JSONB). Seed 1 dòng mặc định. |
| `models` (superadmin) | create | Model `SystemConfig` (JSONB per section). Cân nhắc `__auditable__ = True` + `__audit_exclude__` cho secret SMTP password. |
| `schemas.py` | modify | Pydantic: `SystemConfigResponse` + `FeatureDefaultsUpdate` / `SecurityPolicyUpdate` / `EmailConfigUpdate` / `SystemInfoUpdate`. SMTP password write-only (không trả về plaintext). |
| `service.py` | modify | `get_system_config()`, `update_system_config(section, data)`. Feature-defaults reconcile với `clinics/{id}/features` (nguồn default khi tạo clinic mới). |
| `api/routes.py` | modify | `GET /superadmin/system-config`, `PUT /superadmin/system-config/{section}` (hoặc 1 PUT nhận section). Giữ pattern superuser-guard + bypass RLS hiện có. |
| Enforce (tùy chọn) | modify | `maintenance_mode`: middleware/health chặn/hiện banner khi bật (có thể tách follow-up nếu quá lớn). Password policy: nối vào chỗ validate mật khẩu (TASK-038) nếu khả thi, nếu không → lưu cấu hình + follow-up wiring. |
| `tests/integration/test_superadmin_system_config*.py` | create | Real-DB: 403 non-superuser, get default, update mỗi section, SMTP password không lộ, feature-default áp cho clinic mới. |

---

## Implementation Steps

**Phase 1 — FE reorg (dùng API sẵn có, không chờ BE):**
1. Refactor `Sidebar.tsx`: chuyển nav Super Admin sang cấu trúc phân nhóm 3 tiêu đề; đưa Audit Logs vào nhóm hệ thống; giữ Tài khoản là 1 mục.
2. Rà `SuperAdminAccountsPage` = màn gộp TK + Người dùng đầy đủ (họ tên/email/vai trò/khóa/reset), phân trang + export chuẩn.
3. Cập nhật i18n nhãn nhóm mới (vi/en). Cập nhật/na test Sidebar + Accounts.

**Phase 2 — BE System Config:**
4. Migration + model `system_config` (singleton, non-tenant, seed default).
5. Schemas + service (get/update theo section; SMTP password write-only; audit-exclude secret).
6. Routes `GET`/`PUT /superadmin/system-config` dưới superuser guard.
7. Reconcile feature-defaults với per-clinic features (default khi onboard clinic mới).
8. Integration tests real-DB (403 gate, get/update từng section, secret không lộ).

**Phase 3 — FE System Config page:**
9. `modules/superadmin/{api,types}` thêm system-config.
10. `SuperAdminSystemConfigPage` tabbed 4 phần (rhf + zod), route + lazy + RequireSuperuser + nav item.
11. i18n + unit tests (render tab, validate, submit từng section).

**Phase 4 — Enforce + hoàn thiện:**
12. (Tùy chọn/scope) maintenance_mode banner/guard; nối password-policy vào luồng validate mật khẩu.
13. E2E: đăng nhập superuser → thấy đúng 3 nhóm/4 khối, non-superuser bị chặn mọi route `/superadmin/*`; CRUD account + lưu từng section config end-to-end với BE thật.

---

## Dependencies

- Không thêm thư viện mới (dùng react-hook-form + zod + TanStack Query + Radix Tabs đã có ở FE; SQLAlchemy/Alembic/Pydantic ở BE).
- Email/SMTP tận dụng `app/integrations/email/client.py` sẵn có (chỉ thêm nguồn cấu hình).
- Cân nhắc phụ thuộc TASK-038 (security NFR: password policy/MFA) khi wiring chính sách bảo mật — nếu chưa nối được thì lưu config + đánh dấu follow-up.

## Risks / Notes

- **Ranh giới config env vs DB:** một số cấu hình hiện nằm ở `app/core/config.py` (env, ví dụ SMTP/JWT). Cần chốt cái nào chuyển sang `system_config` (DB, sửa runtime) vs giữ ở env (secret hạ tầng). Đề xuất: DB lưu chính sách/cờ nghiệp vụ; secret hạ tầng (JWT_SECRET, DB URL) GIỮ ở env. SMTP: host/port/from ở DB, password cân nhắc secret.
- **Bảo mật system_config:** bảng non-tenant → phải chắc guard superuser trên MỌI route; không để rò qua RLS/middleware tenancy. Test 403 bắt buộc.
- **Secret trong audit/response:** SMTP password phải write-only + `__audit_exclude__` (theo Override #5 PROJECT.md).
- **maintenance_mode** có thể phình scope (middleware chặn toàn hệ thống) → nếu lớn, tách thành follow-up, task này chỉ lưu + hiển thị cờ.
- **Password policy enforcement** phụ thuộc luồng validate hiện tại; nếu rủi ro cao có thể chỉ lưu cấu hình + follow-up.
- **Migration numbering:** theo quy ước tuần tự của repo; kiểm tra single-head trước khi tạo (Override #2).
- **Không mock ở integration test** (Override #4): chạy real Postgres + Redis.
- Priority task hiện đặt **Medium** (yêu cầu gốc không nêu) — cân nhắc nâng nếu ưu tiên cao như các task Super Admin trước (TASK-070/071 đều High).

---

## Chi tiết CẦN CẤU HÌNH NHỮNG GÌ (nội dung màn "Cấu hình hệ thống")

Màn `/superadmin/system-config` dạng tabbed 4 phần. Giá trị "mặc định" bên dưới lấy từ code thật
(`app/core/config.py`, `app/core/features.py`). Cột **Nguồn**:
`env→DB` = giá trị đang ở biến môi trường, chuyển sang lưu DB để superuser sửa runtime ·
`MỚI` = chưa tồn tại, tạo mới · `secret` = giữ ở env, KHÔNG đưa lên UI.

### Tab 1 — Feature flags mặc định toàn hệ thống
Đặt on/off mặc định áp cho **phòng khám tạo mới** (nguồn hiện là `FEATURE_REGISTRY` hardcode trong `core/features.py` → chuyển default sang `system_config`; per-clinic override vẫn dùng màn Phòng khám).

| Khóa | Nhãn | Mặc định hiện tại | Nguồn |
|---|---|---|---|
| `appointments` | Lịch hẹn | ON | env→DB (features.py) |
| `pharmacy` | Nhà thuốc | ON | env→DB |
| `billing` | Thanh toán | ON | env→DB |
| `reports` | Báo cáo | ON | env→DB |
| `hr` | Nhân sự | ON | env→DB |
| `bhyt` | BHYT | OFF | env→DB |

### Tab 2 — Chính sách bảo mật / mật khẩu

**Mật khẩu** (phần lớn MỚI — hiện chưa có policy cấu hình được):
| Trường | Kiểu | Mặc định đề xuất | Nguồn |
|---|---|---|---|
| `password_min_length` | int | 8 | MỚI |
| `require_uppercase` | bool | true | MỚI |
| `require_lowercase` | bool | true | MỚI |
| `require_digit` | bool | true | MỚI |
| `require_special` | bool | false | MỚI |
| `password_history_count` | int | 5 | env→DB (đã có history ở TASK-038) |
| `password_expiry_days` | int (0=tắt) | 0 | MỚI |

**Khóa tài khoản (lockout)** — đang ở env:
| Trường | Kiểu | Mặc định | Nguồn |
|---|---|---|---|
| `lockout_max_attempts` | int | 5 | env→DB |
| `lockout_window_minutes` | int | 15 | env→DB |
| `lockout_duration_minutes` | int | 30 | env→DB |

**Phiên / token**:
| Trường | Kiểu | Mặc định | Nguồn |
|---|---|---|---|
| `access_token_expire_minutes` | int | 15 | env→DB |
| `refresh_token_expire_days` | int | 7 | env→DB |
| `idle_timeout_minutes` | int (0=tắt) | 0 | MỚI (tùy chọn) |

**MFA & phân tách nhiệm vụ (SoD)**:
| Trường | Kiểu | Mặc định | Nguồn |
|---|---|---|---|
| `mfa_requirement` | enum: off/optional/required | optional | env→DB (TOTP đã có TASK-038) |
| `sod_enforcement` | bool | false | env→DB (`SOD_ENFORCEMENT`) |

**OTP / đặt lại mật khẩu qua email**:
| Trường | Kiểu | Mặc định | Nguồn |
|---|---|---|---|
| `password_reset_ttl_minutes` | int | 30 | env→DB |
| `email_otp_ttl_minutes` | int | 5 | env→DB |
| `email_otp_max_attempts` | int | 5 | env→DB |

### Tab 3 — Email / SMTP & thông báo
| Trường | Kiểu | Mặc định | Nguồn |
|---|---|---|---|
| `email_provider` | enum: console/noop/smtp | console | env→DB |
| `email_from` | string | no-reply@medizen.local | env→DB |
| `email_from_name` | string | MediZen | env→DB |
| `smtp_host` | string | (trống) | env→DB |
| `smtp_port` | int | (trống) | env→DB |
| `smtp_user` | string | (trống) | env→DB |
| `smtp_password` | string **write-only** | (trống) | **secret** (audit-exclude, không trả plaintext) |
| `smtp_use_tls` | bool | true | env→DB |
| `enable_email_notifications` | bool | true | MỚI |
| Nút **Gửi thử** | action | — | MỚI (test SMTP) |
| `slack_webhook_url` / `pagerduty_routing_key` | string | (trống) | env→DB, tùy chọn (cảnh báo vận hành) |

### Tab 4 — Thông tin & vận hành hệ thống
| Trường | Kiểu | Mặc định | Nguồn |
|---|---|---|---|
| `system_name` | string | MediZen | MỚI |
| `default_logo` | url/upload | (trống) | MỚI |
| `support_email` | string | (trống) | MỚI |
| `support_phone` | string | (trống) | MỚI |
| `default_locale` | enum: vi/en | vi | MỚI |
| `default_timezone` | string | Asia/Ho_Chi_Minh | MỚI |
| `currency` | string | VND | MỚI |
| `date_format` | string | DD/MM/YYYY | MỚI |
| `frontend_base_url` | string | http://localhost:1420 | env→DB |
| `maintenance_mode` | bool | false | MỚI |
| `maintenance_message` | text | (trống) | MỚI |
| `maintenance_allowed_ips` | list<string> | [] | MỚI (tùy chọn) |
| `audit_retention_days` | int (0=vô hạn) | 0 | MỚI (tùy chọn) |
| `environment` / `app_version` | read-only | (từ env/build) | hiển thị, không sửa |

### Giữ ở ENV — KHÔNG đưa lên màn cấu hình (secret hạ tầng)
`JWT_SECRET`, `DATABASE_URL`, `REDIS_URL`, `KMS_PROVIDER`/`VAULT_*`/`LOCAL_DEV_MASTER_KEY`,
`EMAIL_HASH_KEY`, `VSS_API_KEY`, `GATEWAY_URL`, `CORS_ORIGINS`. Các giá trị này thuộc bí mật/hạ tầng,
sửa qua deployment chứ không qua UI.

### Cách lưu (BE)
Bảng `system_config` singleton (non-tenant), 4 dòng theo `section` ∈
{`feature_defaults`, `security_policy`, `email`, `system_info`}, mỗi dòng 1 cột `data` JSONB.
`GET /superadmin/system-config` trả cả 4 (secret ẩn); `PUT /superadmin/system-config/{section}`
cập nhật từng phần. Migration seed 1 bộ mặc định từ bảng trên. `smtp_password` write-only +
`__audit_exclude__`.

