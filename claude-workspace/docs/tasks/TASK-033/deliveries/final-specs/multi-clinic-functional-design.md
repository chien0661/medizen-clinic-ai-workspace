---
id: TASK-033-functional-design
title: Thiết kế chức năng — Nhiều phòng khám trên một tài khoản (Multi-clinic per account)
status: DONE
completed: 2026-05-01
auth: AUTH-018, AUTH-019, AUTH-020, AUTH-021, AUTH-022
scope: Backend (B.1–B.13) + Frontend (F.1–F.11)
---

# Thiết kế chức năng — Nhiều phòng khám trên một tài khoản (TASK-033)

**Ngày**: 2026-05-01  
**Trạng thái**: ✅ DONE  
**Chi nhánh**: `feature/task-033-multi-clinic`

---

## Mục đích (Purpose)

Thay thế mô hình "một phòng khám trên một tài khoản" bằng mô hình "một tài khoản có thể thuộc nhiều phòng khám". Điều này cho phép:
- Một nhân viên/bác sĩ làm việc tại nhiều chi nhánh phòng khám
- Quản lý quyền hạn (role/permission) riêng biệt cho từng phòng khám
- Tự động hóa chọn phòng khám mặc định để nhân viên không phải nhập lại trên mỗi lần đăng nhập
- Nền tảng cho các tính năng multi-tenant trong Wave 1 (TASK-035, TASK-037, TASK-041, v.v.)

---

## Phạm vi (Scope)

### Backend (clinic-cms) — 13 file thay đổi

| B.# | Mục tiêu | Mô tả |
|-----|----------|--------|
| B.1 | Bảng pivot | Tạo `account_clinic_role(account_id, clinic_id, role_codes[], is_default, granted_at, granted_by)` với PK composite + FK cascade |
| B.2 | Migration | `0021_multi_clinic_account`: Backfill từ `user.clinic_id`, UNIQUE email, nullable clinic_id, pre-check dup email |
| B.3 | User model | Loại bỏ `TenantMixin` hoặc tách User → Account + ClinicMembership (quyết định: giữ User, loại bỏ TenantMixin) |
| B.4 | POST /auth/login | Xóa field `clinic_code`; trả về `{user, access_token, refresh_token, clinics: [...], active_clinic_id}` |
| B.5 | POST /auth/select-clinic | Mới: xác minh membership pivot (chống leo thang quyền); revoke + reissue JWT |
| B.6 | GET /auth/clinics | Mới: liệt kê clinic memberships của user |
| B.7 | PATCH /auth/clinics/{id}/default | Mới: đặt clinic mặc định |
| B.8 | JWT claims | `{user_id, active_clinic_id, role_codes, permissions}` — phạm vi đến active clinic |
| B.9 | TenancyMiddleware | Đọc `active_clinic_id` từ JWT (fallback: `clinic_id` cho backward compat) |
| B.10 | RBAC cache | `rbac_service.get_user_effective_permissions(user_id, active_clinic_id)` — lọc pivot membership |
| B.11 | Cache key | `user:perms:{user_id}` → `user:perms:{user_id}:{clinic_id}` (hay `:global` nếu clinic_id=None) |
| B.12 | Last-active clinic | Redis `user:last_clinic:{user_id}` cho AUTH-022 auto-resolve |
| B.13 | Call sites (~50+) | Cập nhật tất cả điểm tham chiếu `current_clinic_id` để sử dụng context var mới |

### Frontend (clinic-cms-web) — 18 file thay đổi

| F.# | Mục tiêu | Mô tả |
|-----|----------|--------|
| F.1 | LoginPage schema | Xóa field `clinic_code` từ Zod + UI form |
| F.2 | AuthStore | Thay thế scalar `clinicId/clinicCode` bằng `clinics: Clinic[] + activeClinicId + defaultClinicId` |
| F.3 | ClinicSelectorPage | Mới: màn hình post-login nếu `clinics.length > 1` và chưa có default |
| F.4 | ClinicSwitcher dropdown | Mới: 240px topbar dropdown (logo + role chip + "Hiện tại" + footer "Đổi mặc định" + "Quản lý") |
| F.5 | Topbar | Mount ClinicSwitcher (thay thế dòng hard-coded "Clinic CMS") |
| F.6 | apiClient | Gửi `Authorization: Bearer <new JWT>` sau switch |
| F.7 | React-Query cache | Clear `queryClient.clear()` trên clinic switch |
| F.8 | Tauri secureStore | Thêm `LAST_ACTIVE_CLINIC` key |
| F.9 | ProfilePage | Mới: skeleton với tab "Phòng khám của tôi" — liệt kê membership + radio set-default |
| F.10 | Routing | Thay thế `/profile` placeholder bằng ProfilePage mới |
| F.11 | i18n keys | `auth.clinicSelector`, `shell.clinicSwitcher`, `profile.myClinics` (vi + en) |

---

## Sơ đồ Schema (Database Diagram)

### Bảng Pivot: `account_clinic_role`

```
┌─────────────────────────────────────┐
│        account_clinic_role          │
├─────────────────────────────────────┤
│ account_id (UUID, FK→user.id)      │◄─── PK part 1
│ clinic_id (UUID, FK→clinic.id)     │◄─── PK part 2
│ role_codes (TEXT[], default='{}')  │     ["doctor", "nurse"]
│ is_default (BOOLEAN, default=false)│     Clinic mặc định cho account này
│ granted_at (TIMESTAMPTZ)           │     Khi được cấp quyền
│ granted_by (UUID, FK→user.id, NULL)│     Người cấp quyền (admin)
├─────────────────────────────────────┤
│ PRIMARY KEY (account_id, clinic_id)│
│ FOREIGN KEY (account_id) → user.id │
│ FOREIGN KEY (clinic_id) → clinic.id│
│ FOREIGN KEY (granted_by) → user.id │
│ INDEX ON (account_id, is_default)  │
│ INDEX ON (clinic_id)               │
└─────────────────────────────────────┘
```

### Bảng User: thay đổi

```
┌──────────────────────────────────────┐
│             user (trước)             │
├──────────────────────────────────────┤
│ id (UUID, PK)                        │
│ email (VARCHAR, UNIQUE)              │◄─── Mới: UNIQUE toàn cầu
│ username (VARCHAR, UNIQUE)           │
│ password_hash (VARCHAR)              │
│ clinic_id (UUID, FK→clinic)          │◄─── Cũ: NOT NULL; mới: NULLABLE
│ is_deleted (BOOLEAN, default=false)  │
│ created_at, updated_at               │
└──────────────────────────────────────┘
```

**Lý do giữ `user.clinic_id` nullable**:
- Rollback safety — nếu migration rollback, column vẫn tồn tại cho dữ liệu cũ
- Follow-up task sẽ drop column này sau 1 release (TASK-033-cleanup)

---

## Migration: `0021_multi_clinic_account`

### Metadata

```python
down_revision = "20260429_65fc9ae59ba5"  # merge_task_015_reports_notifications
revision = "0021_multi_clinic_account"
branch_labels = None
depends_on = None
```

### Bước thực thi

#### 1. Tạo bảng pivot
```python
op.create_table(
    'account_clinic_role',
    sa.Column('account_id', sa.UUID, sa.ForeignKey('user.id', ondelete='CASCADE'), nullable=False),
    sa.Column('clinic_id', sa.UUID, sa.ForeignKey('clinic.id', ondelete='CASCADE'), nullable=False),
    sa.Column('role_codes', postgresql.ARRAY(sa.String), nullable=False, server_default='{}'),
    sa.Column('is_default', sa.Boolean, nullable=False, server_default='false'),
    sa.Column('granted_at', sa.TIMESTAMPTZ, nullable=False, server_default='now()'),
    sa.Column('granted_by', sa.UUID, sa.ForeignKey('user.id', ondelete='SET NULL'), nullable=True),
    sa.PrimaryKeyConstraint('account_id', 'clinic_id'),
)
```

#### 2. Backfill pivot từ `user.clinic_id` hiện tại
```sql
-- Pre-flight check (thêm trong migration Python):
SELECT email, COUNT(*) c FROM "user" 
WHERE email IS NOT NULL 
GROUP BY email 
HAVING c > 1;
-- Nếu có kết quả, raise RuntimeError + chi tiết

-- SQL chính:
INSERT INTO account_clinic_role (account_id, clinic_id, role_codes, is_default, granted_at)
SELECT u.id, u.clinic_id,
  COALESCE(ARRAY_AGG(r.code ORDER BY r.code) FILTER (WHERE r.code IS NOT NULL), '{}'),
  TRUE, NOW()
FROM "user" u
LEFT JOIN user_role ur ON ur.user_id = u.id
LEFT JOIN role r ON r.id = ur.role_id AND r.is_deleted = FALSE
WHERE u.clinic_id IS NOT NULL AND u.is_deleted = FALSE
GROUP BY u.id, u.clinic_id
ON CONFLICT (account_id, clinic_id) DO NOTHING;
```

#### 3. Làm `user.clinic_id` nullable
```python
op.alter_column('user', 'clinic_id', nullable=True)
```

#### 4. Thêm ràng buộc UNIQUE trên email
```python
op.create_unique_constraint('uq_user_email', 'user', ['email'])
```

### Rollback (downgrade)

```python
def downgrade() -> None:
    op.drop_constraint('uq_user_email', 'user', type_='unique')
    op.alter_column('user', 'clinic_id', nullable=False)
    op.drop_table('account_clinic_role')
```

**Cảnh báo**: Downgrade sẽ THẤT BẠI nếu sau migration có user nào có `clinic_id IS NULL`. Toàn bộ backfill mặc định set `is_default=true` nên điều này không xảy ra trong rollback chuẩn.

### Xung đột migration (Streams A/B/C)

**Vấn đề**: Stream B (`0021_password_history`) và Stream C (`0021_add_mfa`) cũng tuyên bố revision `0021`. Tất cả ba có `down_revision = 65fc9ae59ba5` (cùng parent).

**Giải pháp (tại merge time)**:
- Đổi tên: Stream A giữ `0021_multi_clinic_account`, Stream B → `0022_password_history`, Stream C → `0023_add_mfa`
- Cập nhật `down_revision` chain tuyến tính:
  - `0021_multi_clinic_account.down_revision = "65fc9ae59ba5"`
  - `0022_password_history.down_revision = "0021_multi_clinic_account"`
  - `0023_add_mfa.down_revision = "0022_password_history"`

---

## Hợp đồng API (API Contract)

### POST `/auth/login` — Thay đổi

**Trước (TASK-032 và trước)**:
```json
{
  "username": "doctor@clinic-a.vn",
  "password": "...",
  "clinic_code": "clinic_a_001"
}

→ Response:
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "user": { "id": "uuid", "email": "...", "username": "..." },
  "clinic_id": "uuid",
  "clinic_name": "Clinic A"
}
```

**Sau (TASK-033)**:
```json
{
  "username": "doctor@clinic-a.vn",
  "password": "..."
}

→ Response:
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "user": { "id": "uuid", "email": "...", "username": "..." },
  "clinics": [
    { "id": "uuid-a", "name": "Clinic A", "role_codes": ["doctor"], "is_default": true },
    { "id": "uuid-b", "name": "Clinic B", "role_codes": ["admin"], "is_default": false }
  ],
  "active_clinic_id": "uuid-a"
}
```

**Logic auto-resolve**:
- 0 clinics → `active_clinic_id: null` (FE hiển thị lỗi)
- 1 clinic → `active_clinic_id: <that clinic>`
- 2+ clinics + có default → `active_clinic_id: <default>`
- 2+ clinics + no default → `active_clinic_id: null` (FE chuyển hướng đến ClinicSelectorPage)

### POST `/auth/select-clinic` — ENDPOINT MỚI

**Request**:
```json
{
  "clinic_id": "uuid"
}
```

**Response (200 OK)**:
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "active_clinic_id": "uuid",
  "permissions": ["patient.read", "patient.write", ...]
}
```

**Errors**:
- `403 FORBIDDEN` — User không phải thành viên của clinic này (pivot lookup thất bại)
- `404 NOT FOUND` — Clinic không tồn tại hoặc bị soft-delete
- `401 UNAUTHORIZED` — JWT cũ không hợp lệ

**Hành động server**:
1. Xác minh JWT hiện tại → `user_id`
2. Lookup `SELECT * FROM account_clinic_role WHERE account_id=user_id AND clinic_id=<req>` → null? → 403
3. Kiểm tra clinic active (không soft-delete)
4. Lấy permission scoped: `get_user_effective_permissions(user_id, clinic_id)`
5. Revoke refresh JTI cũ vào Redis blacklist
6. Tạo JWT mới với `active_clinic_id=<req>` + `role_codes` + `permissions`

**FE**: Clear React-Query cache + set `activeClinicId` trong authStore + có thể `window.location.reload()`

### GET `/auth/clinics` — ENDPOINT MỚI

**Request**: (Auth header required)

**Response (200 OK)**:
```json
{
  "clinics": [
    { "id": "uuid-a", "name": "Clinic A", "role_codes": ["doctor"], "is_default": true },
    { "id": "uuid-b", "name": "Clinic B", "role_codes": ["admin"], "is_default": false }
  ]
}
```

### PATCH `/auth/clinics/{id}/default` — ENDPOINT MỚI

**Request**: (Auth header required)
```json
{}
```

**Response (200 OK)**:
```json
{
  "clinics": [
    { "id": "uuid-a", "name": "Clinic A", "role_codes": ["doctor"], "is_default": true },
    { "id": "uuid-b", "name": "Clinic B", "role_codes": ["admin"], "is_default": false }
  ]
}
```

**Hành động server**:
1. Xác minh user là thành viên của clinic `{id}` (pivot lookup)
2. UPDATE `account_clinic_role SET is_default=false WHERE account_id=user_id AND clinic_id != {id}`
3. UPDATE `account_clinic_role SET is_default=true WHERE account_id=user_id AND clinic_id = {id}`
4. Invalidate RBAC cache cho user này
5. Trả về danh sách clinic cập nhật

---

## JWT Shape — Mới

### Access Token Claims

```json
{
  "sub": "user-uuid",
  "active_clinic_id": "clinic-uuid-or-null",
  "role_codes": ["doctor", "nurse"],
  "permissions": ["patient.read", "patient.write", "visit.read"],
  "type": "access",
  "jti": "token-id",
  "iat": 1714550000,
  "exp": 1714550900
}
```

### Refresh Token Claims

```json
{
  "sub": "user-uuid",
  "active_clinic_id": "clinic-uuid-or-null",
  "type": "refresh",
  "jti": "token-id",
  "iat": 1714550000,
  "exp": 1714636400
}
```

**Key differences** so với trước:
- `clinic_id` → `active_clinic_id` (can be null if clinic not selected yet)
- `roles: [...]` → `role_codes: [...]` (same semantic, clarified naming)
- `permissions` = scoped to `active_clinic_id` only (cross-clinic filtering)
- TenancyMiddleware reads `active_clinic_id || clinic_id` (backward compat)

---

## RBAC + Cache

### Thay đổi `get_user_effective_permissions`

**Trước**:
```python
def get_user_effective_permissions(db: Session, user_id: UUID) -> list[str]:
    # Lấy tất cả role của user, union permissions từ mọi role
    roles = db.query(UserRole).filter(UserRole.user_id == user_id).all()
    return union_of_permissions(roles)
```

**Sau (clinic-scoped)**:
```python
def get_user_effective_permissions(db: Session, user_id: UUID, clinic_id: UUID) -> list[str]:
    # Lấy role chỉ từ account_clinic_role ở clinic này
    pivot = db.query(AccountClinicRole).filter(
        AccountClinicRole.account_id == user_id,
        AccountClinicRole.clinic_id == clinic_id
    ).first()
    
    if not pivot:
        return []
    
    # Lấy Role objects từ role_codes[]
    roles = db.query(Role).filter(
        Role.code.in_(pivot.role_codes),
        (Role.clinic_id == clinic_id) | (Role.clinic_id.is_(None))  # clinic-scoped + system roles
    ).all()
    
    return union_of_permissions(roles)
```

### Cache Key Changes

**Trước**:
```
user:perms:550e8400-e29b-41d4-a716-446655440000
→ Set của tất cả permissions cho user này
```

**Sau (clinic-scoped)**:
```
user:perms:550e8400-e29b-41d4-a716-446655440000:clinic-uuid
→ Set của permission cho user này trong clinic X

user:perms:550e8400-e29b-41d4-a716-446655440000:global
→ System permissions (không clinic-scoped)
```

### Last-Active Clinic (AUTH-022 setup)

**Mới**:
```
user:last_clinic:550e8400-e29b-41d4-a716-446655440000 → "clinic-uuid"
```

Cập nhật mỗi lần user gọi `/auth/select-clinic` hoặc tạo access token mới.

### Cache Invalidation

```python
def invalidate_user_cache(user_id: UUID, clinic_id: UUID | None = None) -> None:
    if clinic_id:
        # Xóa clinic cụ thể
        redis.delete(f"user:perms:{user_id}:{clinic_id}")
    else:
        # Xóa tất cả clinic của user (SCAN pattern)
        pattern = f"user:perms:{user_id}:*"
        for key in redis.scan_iter(pattern):
            redis.delete(key)
```

---

## Call Sites Update (~50+)

### Affected Modules

| Module | File | Context | Change |
|--------|------|---------|--------|
| visits | `app/modules/visits/api/routes.py` | Reads `current_clinic_id` via ContextVar | ✅ Automatic (ContextVar fed from JWT) |
| billing | `app/modules/billing/api/routes.py` | Reads `current_clinic_id` | ✅ Automatic |
| prescriptions | `app/modules/prescriptions/api/routes.py` | Reads `current_clinic_id` | ✅ Automatic |
| inventory | `app/modules/inventory/api/routes.py` | Reads `current_clinic_id` | ✅ Automatic |
| reports | `app/modules/reports/api/routes.py` | Reads `current_clinic_id` | ✅ Automatic |
| services | `app/modules/services/services/visit_service_service.py` | Calls `_check_user_has_price_override(db, user_id, clinic_id)` | ✅ Clinic ID passed (Fix v1) |
| permissions | `app/core/permissions.py` `require_permission` decorator | Passes `clinic_id` to RBAC | ✅ Updated |
| auth | `app/modules/auth/services/lockout_service.py` | Lockout key không chứa clinic | ✅ Refactored |
| security | `app/core/security.py` | JWT creation / validation | ✅ Rewritten |

**Cơ chế**: TenancyMiddleware đặt `current_clinic_id` ContextVar từ `active_clinic_id` JWT claim. Tất cả điểm tham chiếu đọc từ ContextVar tự động nhận clinic ID mới.

---

## FE Flow (clinic-cms-web)

### 1. LoginPage → ClinicSelectorPage → Dashboard

```
┌──────────────┐
│  LoginPage   │
├──────────────┤
│ Remove:      │
│  clinic_code │
│              │
│ POST /login  │
└──────────────┘
        ↓
  ┌─────────────────────┐
  │ Clinics count check │
  └─────────────────────┘
        ↓
  ┌──────────────────┐
  │ Count = 0?       │ YES → Show error, stay on LoginPage
  └──────────────────┘     (Tài khoản chưa được gán phòng khám)
        │
       NO
        ↓
  ┌──────────────────┐
  │ Count = 1?       │ YES → Auto-select, go to /dashboard
  └──────────────────┘
        │
       NO (2+)
        ↓
  ┌─────────────────────────────────┐
  │ Has default?                    │ YES → Auto-select default, go to /dashboard
  └─────────────────────────────────┘
        │
       NO
        ↓
  ┌─────────────────────────────────┐
  │ ClinicSelectorPage              │
  │  - List 2+ clinics              │
  │  - Radio select                 │
  │  - POST /auth/select-clinic     │
  │  - Clear queryClient            │
  │  - Redirect to /dashboard       │
  └─────────────────────────────────┘
```

### 2. ClinicSwitcher (Topbar Dropdown)

**Kích thước**: 240px (`w-60`)

**Cấu trúc**:
```
┌──────────────────────────────────┐
│  [Clinic Logo] Clinic A          │  ← Header
├──────────────────────────────────┤
│  ○ role: doctor  [HIỆN TẠI]      │  ← Active clinic
│                                  │     (role chip + "HIỆN TẠI" badge)
│  ○ role: admin                   │  ← Inactive clinic
├──────────────────────────────────┤
│  [🔗] Đổi mặc định               │  ← Radio set-default
│  [⚙️] Quản lý phòng khám          │  ← Go to /profile?tab=clinics
└──────────────────────────────────┘
```

**Click action**:
1. Select clinic → POST `/auth/select-clinic {clinic_id}`
2. Nhận access + refresh token mới
3. `queryClient.clear()` (clear cache)
4. `window.location.reload()` (reload page)
5. TenancyMiddleware read JWT → set `current_clinic_id` → RLS filter applies tự động

### 3. ProfilePage "Phòng khám của tôi" Tab

```
ProfilePage
├── Tabs:
│   ├── Thông tin cá nhân (tên, email, password)
│   └── Phòng khám của tôi ✨
│       ├── List:
│       │   ○ [Clinic A] role: doctor, admin
│       │     [Radio: Set mặc định]
│       │   
│       │   ○ [Clinic B] role: nurse
│       │     [Radio: Set mặc định]
│       │
│       ├── [Leave] button (admin only) → POST /auth/clinics/{id}/leave
│       └── [+ Yêu cầu quyền] (future: TASK-035)
```

**Update flow**:
- PATCH `/auth/clinics/{id}/default` → Server update pivot
- authStore: `clinics.find(c => c.is_default).is_default = false; clinics.find(c => c.id == selected).is_default = true`
- Optimistic UI update (radio thay đổi ngay)

---

## Field Naming Convention

**BE + FE sử dụng consistently**:
- `active_clinic_id` — JWT claim + context var + API response
- `clinics: ClinicInfo[]` — array of memberships
- `defaultClinicId` — FE state (camelCase)
- `role_codes: string[]` — roles in pivot

---

## Test Coverage

### BE Unit Tests (27 TASK-033–specific)

✅ Location: `tests/unit/test_task033_multi_clinic.py`

| Category | Count | Examples |
|----------|-------|----------|
| JWT shape | 10 | `test_access_token_has_active_clinic_id`, `test_role_codes_in_token`, ... |
| RBAC cache | 5 | `test_cache_key_clinic_scoped`, `test_cache_invalidation_all_clinics`, ... |
| AccountClinicRole model | 4 | `test_pivot_pk_composite`, `test_role_codes_array`, ... |
| Schemas | 5 | `test_login_no_clinic_code`, `test_select_clinic_request_valid`, ... |
| Lockout | 3 | `test_lockout_key_no_clinic`, ... |

### BE Integration Tests (31 AUTH-specific)

✅ All PASS (post-Fix v2)

| Suite | Tests | Status |
|-------|-------|--------|
| `test_auth_login.py` | 8 | ✅ PASS |
| `test_auth_select_clinic.py` | 6 | ✅ PASS |
| `test_auth_clinics_list.py` | 5 | ✅ PASS |
| `test_auth_service_coverage.py` | 12 | ✅ PASS |

**Note**: 35+ existing integration tests removed `clinic_code` from login bodies (Fix v1 + v2 update)

### FE Unit Tests (568 total, 19 TASK-033–specific)

✅ Location: `src/tests/shell/task033-multi-clinic.test.ts`

| Category | Tests | Status |
|----------|-------|--------|
| LoginPage logic | 4 | ✅ PASS (clinic count branching) |
| AuthStore shape | 6 | ✅ PASS (clinics array, activeClinicId, defaultClinicId) |
| ClinicSwitcher | 5 | ✅ PASS (dropdown render, select action) |
| ClinicSelectorPage | 4 | ✅ PASS (list + radio) |

### E2E Smoke Tests

✅ Manual verification: Login → Multi-clinic response shape → No clinic_code required

---

## Decisions Deferred

| Item | Status | Rationale | Follow-up |
|------|--------|-----------|-----------|
| Drop `user.clinic_id` column | Kept nullable (1 release) | Rollback safety | TASK-033-cleanup (drop after Wave 1) |
| Email duplicate pre-check | In-migration check added (Fix v2) | Prevents silent partial migration | Operator runbook + migration error message |
| Redis flush window | Manual deploy-time | 5-min stale cache acceptable during deploy | Update deploy script to `FLUSHDB` or equivalent |
| `X-Active-Clinic` header | NOT implemented | JWT claim sufficient | None |
| `queryClient.clear()` vs `invalidateQueries` | Clear (broader) | Belt-and-suspenders (followed by `window.location.reload()`) | Could optimize in future (TASK-039?) |
| `UserRole` legacy table consolidation | Backfill only | Role assignment still dual-write | TASK-033b (migrate to pivot-only) |

---

## Migration Runbook

### Pre-flight (Before `alembic upgrade 0021_multi_clinic_account`)

```bash
# 1. Backup database
pg_dump clinic_cms_db > backup_2026-05-01.sql

# 2. Check for duplicate emails
psql clinic_cms_db -c "
  SELECT email, COUNT(*) c FROM \"user\" 
  WHERE email IS NOT NULL 
  GROUP BY email 
  HAVING c > 1;
"
# If any duplicates found, resolve before proceeding

# 3. Check for NULL clinic_id users (should be 0)
psql clinic_cms_db -c "
  SELECT COUNT(*) FROM \"user\" 
  WHERE clinic_id IS NULL AND is_deleted = false;
"
```

### Upgrade

```bash
cd clinic-cms/
alembic upgrade 0021_multi_clinic_account
```

**Migration script thực thi**:
1. Create `account_clinic_role` table
2. Pre-flight: scan for dup emails → raise if found (Fix v2)
3. Backfill pivot từ `user.clinic_id`
4. ALTER `user.clinic_id` nullable
5. ADD UNIQUE constraint trên `user.email`

**Expect**: 0.5–2 seconds (depending on user count)

### Post-upgrade Ops

```bash
# 1. Verify backfill (pivot row count = user row count)
psql clinic_cms_db -c "
  SELECT COUNT(*) FROM account_clinic_role;
  SELECT COUNT(*) FROM \"user\" WHERE is_deleted = false;
"

# 2. Flush Redis to purge old cache entries
redis-cli FLUSHDB

# 3. Force re-login: all active JWTs now use old clinic_id claim
#    TenancyMiddleware fallback handles this, but recommend clear sessions

# 4. Monitor application for 5 minutes
#    - Check logs for "active_clinic_id" claims
#    - Verify no cross-clinic data leaks
#    - Confirm ClinicSwitcher works in UI

# 5. If issues detected, rollback:
alembic downgrade -1
redis-cli FLUSHDB
```

### Rollback (Emergency)

```bash
# 1. Downgrade database
cd clinic-cms/
alembic downgrade -1

# 2. This removes:
#    - account_clinic_role table (all data lost)
#    - UNIQUE constraint on user.email
#    - Restores user.clinic_id to NOT NULL

# 3. Restore from backup if needed
pg_restore clinic_cms_db < backup_2026-05-01.sql

# 4. Old JWT claims (clinic_id) still work due to TenancyMiddleware fallback
#    No forced re-login needed (sessions remain valid)
```

---

## Tóm lược Thực thi (Implementation Summary)

### Backend

- **13 files** thay đổi (13 new/modified)
- **1 migration** (`0021_multi_clinic_account`) tạo pivot + backfill + email UNIQUE
- **3 new endpoints**: `/select-clinic`, `/clinics`, `/clinics/{id}/default`
- **JWT rewrite**: `clinic_id` → `active_clinic_id`, add `role_codes`
- **RBAC refactor**: clinic-scoped cache key + permission filter
- **TenancyMiddleware**: fallback to old `clinic_id` claim cho backward compat

### Frontend

- **18 files** thay đổi (3 new components + 6 new i18n)
- **3 new components**: `ClinicSelectorPage`, `ClinicSwitcher`, `ProfilePage`
- **AuthStore refactor**: scalar clinic ID → array + active + default
- **LoginPage**: remove `clinic_code` field + add 0-clinic guard
- **Topbar**: mount ClinicSwitcher dropdown
- **Profile**: new "Phòng khám của tôi" tab + set-default radio

### Testing

- ✅ **27 BE unit tests** (TASK-033–specific)
- ✅ **31 BE integration** (auth flow)
- ✅ **568 FE unit** (19 TASK-033–specific)
- ✅ **0 TS errors** (after Fix v2)
- ✅ **0 lint errors** (after Fix v2)
- ✅ **E2E smoke verified**: login shape + no clinic_code required

---

## Risks + Mitigations

| Risk | Severity | Mitigation |
|------|----------|-----------|
| Email duplicate crashes migration | HIGH | Pre-flight check in migration + operator runbook |
| Cross-clinic permission leakage | HIGH | Cache key clinic-scoped + pivot membership filter verified in review |
| Stale Redis cache during deploy | MEDIUM | Recommend FLUSHDB during deploy window + 5-min TTL acceptable |
| Parallel clinic switch race condition | MEDIUM | Refresh JTI revocation on select-clinic + access token TTL 15min |
| FE 0-clinic user falls through | MEDIUM | Added explicit guard in LoginPage (Fix v1) + error message |
| Integration test regression | MEDIUM | Fix v1 updated 35+ tests to remove clinic_code |
| Migration revision collision (Streams A/B/C) | MEDIUM | Merge-time rename strategy documented (0021a/0021b) |

---

## Tư liệu + Trích dẫn

- **Task định nghĩa**: `docs/tasks/TASK-033/task.md`
- **Handoff thực thi**: `docs/tasks/TASK-033/handoff/impl-to-review.md`
- **Báo cáo review**: `docs/tasks/TASK-033/handoff/review-to-test.md`
- **Báo cáo test**: `docs/tasks/TASK-033/handoff/test-to-documentation.md`
- **Design UX**: `docs/design/medizen-modern/MULTI_ROLE_UX.md`
- **Security docs**: `docs/design/medizen-modern/SECURITY.md`
- **Audit reports** (TASK-032): `docs/tasks/TASK-032/handoff/be-audit-report.md`, `fe-audit-report.md`

---

## Trạng thái Hoàn thành

✅ **Đã Hoàn Thành**: 2026-05-01

Tất cả yêu cầu B.1–B.13 (BE) + F.1–F.11 (FE) đã thực thi. Migration + auth flow + RBAC cache + FE flows thông qua 27 unit BE + 31 integration + 568 FE tests. Hai lần Fix (Fix v1 + Fix v2) giải quyết blocker review + integration test debt.

**Kế tiếp**: TASK-034 (Role-based access v2), TASK-035 (Multi-role per clinic), TASK-037 (Advanced RBAC) phụ thuộc vào nền tảng này.
