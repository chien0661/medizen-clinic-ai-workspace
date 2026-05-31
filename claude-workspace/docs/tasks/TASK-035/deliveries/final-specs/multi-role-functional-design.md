---
id: TASK-035-functional-design
title: "Thiết kế Chức năng: Multi-role + Applied Role Audit + SoD Framework"
date: 2026-05-01
status: DONE
task: TASK-035
completed_date: 2026-05-01
branch: feature/task-035-multi-role
---

# Thiết kế Chức năng: Multi-role Sidebar + Applied Role Audit + SoD Framework

**TASK**: TASK-035  
**Ngày**: 2026-05-01  
**Trạng thái**: DONE  
**Branch BE**: `feature/task-035-multi-role`  
**Branch FE**: `feature/task-035-multi-role-fe`

---

## Mục đích

Cho phép người dùng quản lý nhiều roles (RBAC-015–018):
1. **Sidebar merge**: Một sidebar duy nhất với nhóm nav items theo role, có dividers `─── Bác sĩ ───`, `─── Quản trị ───`
2. **Applied Role Audit**: Ghi lại `applied_role` trong audit_log để biết action được thực hiện dưới role nào
3. **Separation of Duties Framework**: Đảm bảo người dùng không thể vừa propose vừa approve cùng record (e.g. tạo hóa đơn rồi record thanh toán)

---

## Phạm vi

### BE (clinic-cms)
- Thêm cột `applied_role` vào `audit_log`
- Audit listener capture `applied_role` từ JWT header hoặc request context
- SoD framework (`check_no_self_approval`, `make_sod_dep`)
- SoD áp dụng tại: `add_payment`, `dispense_prescription`
- Schema `/users/{id}/roles` thêm `assigned_at` per role

### FE (clinic-cms-web)
- Refactor `Sidebar.tsx`: nhóm nav items theo role, render dividers
- New `lib/rbac.ts`: mapping role → nav sections
- Update `authStore`: thêm `appliedRole` state + `setAppliedRole()` action
- Topbar avatar: role chip (primary role + "+N" badge)
- Applied role context indicator (visual dot on active role section)
- Send `X-Applied-Role` header trên mỗi request
- Multi-role default landing: `/dashboard/multi-role` route

---

## Schema Migration `0026_audit_applied_role`

**File**: `alembic/versions/0026_audit_applied_role.py`

### Upgrade
```sql
ALTER TABLE audit_log ADD COLUMN applied_role VARCHAR(50) NULL;
CREATE INDEX idx_audit_applied_role_created ON audit_log(applied_role, created_at);
```

### Downgrade
```sql
DROP INDEX idx_audit_applied_role_created;
ALTER TABLE audit_log DROP COLUMN applied_role;
```

**Down Revision**: `0021_multi_clinic_account` (verified in codebase)  
**Composite Index**: `(applied_role, created_at)` — cho compliance queries (audit trail for specific role)

---

## BE Components

### 1. Audit Listener (`app/core/audit.py`)

**ContextVar** `current_applied_role: ContextVar[str | None]` được khởi tạo trong `app/core/tenancy.py:210`.

**Capture flow**:
- `write_audit()` (async) đọc `current_applied_role.get(None)` → truyền vào `AuditLog(..., applied_role=role)`
- `_write_audit_sync()` tương tự (fallback cho non-async context)
- Nếu `applied_role` là None → audit_log.applied_role = NULL (database sẽ track dựa trên JWT role)

**Reading from request**:
- Middleware / dependency đặt `current_applied_role` từ:
  1. Header `X-Applied-Role` (FE user explicitly set)
  2. JWT claim `role` (fallback — từ token cấp lúc login)

### 2. SoD Framework (`app/core/sod.py`)

#### a) `check_no_self_approval(record, record_creator_field: str)`

```python
def check_no_self_approval(record: Any, record_creator_field: str = "created_by") -> None:
    """
    Verify that current user is NOT the record creator.
    Raises 403 SOD_VIOLATION if same user.
    """
    creator_id = getattr(record, record_creator_field, None)
    if creator_id == current_user_id:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "SOD_VIOLATION",
                "message": "Người tạo record không thể approve",
                "field": record_creator_field
            }
        )
```

#### b) `make_sod_dep(get_record_fn, record_creator_field: str = "created_by")`

FastAPI dependency factory — inject vào endpoint với `record_id` path param:
```python
async def add_payment(
    invoice_id: int,
    sod_check: SoDCheckResult = Depends(make_sod_dep(get_invoice, "created_by"))
):
    # sod_check đã verify invoice.created_by != current_user
```

**Dead code removed**: `require_no_self_approval()` đã bị xóa (raise NotImplementedError).

### 3. SoD Endpoints Applied

| Endpoint | Creator Field | Status | Notes |
|----------|---------------|--------|-------|
| `POST /api/v1/invoices/{id}/payments` | `invoice.created_by` | ✅ Applied | Billing add_payment |
| `POST /api/v1/pharmacy/dispense/{id}` | `prescription.created_by` | ✅ Applied | Pharmacy dispense |
| `POST /api/v1/inventory/stocktake/approve/{id}` | — | ⏸️ Deferred | Endpoint chưa tồn tại |

### 4. `/users/{id}/roles` Schema

**Response schema** (`UserRoleResponse`):
```python
class UserRoleResponse(BaseModel):
    role_id: int
    role_name: str
    assigned_at: datetime | None = None  # Optional for backward compat
    created_at: datetime
```

**Endpoint** `GET /api/v1/users/{id}/roles`:
- Join `UserRole` + `Role` tables
- Populate `assigned_at` from `UserRole.assigned_at`

---

## FE Components

### 1. RBAC Library (`src/lib/rbac.ts`)

```typescript
export const ROLE_NAV_SECTIONS: Record<Role, NavItem[]> = {
  [Role.Doctor]: [
    { path: "/dashboard/doctor", icon: "stethoscope", label: "shell.nav.dashboard" },
    { path: "/patients", icon: "users", label: "shell.nav.patients" },
    // ...
  ],
  [Role.Admin]: [
    { path: "/dashboard/admin", icon: "settings", label: "shell.nav.dashboard" },
    { path: "/users", icon: "people", label: "shell.nav.users" },
    // ...
  ],
  // Cộng tác viên, Dược sĩ, Y tá, Kế toán, Quản lý HR
};

export function isMultiRole(roles: Role[]): boolean {
  return roles.length > 1;
}

export function getPrimaryRole(roles: Role[]): Role {
  // Trả về role đầu tiên hoặc theo priority
  return roles[0];
}

export function groupNavByRole(roles: Role[]): GroupedNav {
  // Nhóm nav items theo role
  return roles.map(role => ({ role, items: ROLE_NAV_SECTIONS[role] }));
}
```

### 2. Auth Store (`src/stores/authStore.ts`)

**New state field**:
```typescript
appliedRole: string | null = null;

actions: {
  setAppliedRole(role: string | null) {
    this.appliedRole = role;
    // Persist to Tauri secureStore
    window.secureStore?.set(APPLIED_ROLE, role);
  },
  
  setTokens(tokens) {
    // ... existing
    // Default appliedRole to first role
    this.appliedRole = user.roles[0] ?? null;
    window.secureStore?.set(APPLIED_ROLE, this.appliedRole);
  },
  
  logout() {
    this.appliedRole = null;
    window.secureStore?.remove(APPLIED_ROLE);
  },
  
  async loadFromStorage() {
    const stored = await window.secureStore?.get(APPLIED_ROLE);
    if (stored) this.appliedRole = stored;
  }
}
```

**Secure store key** (`src/lib/secureStore.ts`):
```typescript
export const APPLIED_ROLE = "auth.applied_role";
```

### 3. Sidebar (`src/components/shell/Sidebar.tsx`)

#### Single-role (1 role)
- Render `NAV_ITEMS` như hiện tại (không có dividers)
- `data-testid="sidebar-single-role"`

#### Multi-role (2+ roles)
- Shared section (dashboard, notifications, settings) ở đầu
- Per-role sections với `RoleDivider`:
  ```tsx
  {multiRole && <RoleDivider roleName={role} />}
  <div data-testid={`role-section-${role}`}>
    {/* Nav items for this role */}
  </div>
  ```
- Nav click: `setAppliedRole(sectionRole)` → update store + visual indicator

#### Applied role indicator
- Visual dot (•) trên active role section header
- `data-testid="applied-role-indicator-{roleKey}"`
- Persisted + restored qua `loadFromStorage()`

### 4. Topbar (`src/components/shell/Topbar.tsx`)

**Avatar button**:
- Show initials + `topbar-primary-role-chip` (translated primary role label)
- If multi-role: `topbar-multi-role-badge` với `+N` (N = roles.length - 1)
- `data-testid="topbar-avatar-button"`

**Multi-role dropdown** (on click):
- Header: "Vai trò của bạn"
- List all roles với translated labels
- `data-testid="topbar-roles-list"`

### 5. Multi-role Landing (`src/pages/dashboard/MultiRoleDashboardPage.tsx`)

**NEW stub page**:
```typescript
export default function MultiRoleDashboardPage() {
  const { user } = useAuth();
  return (
    <div>
      <h1>Bảng điều khiển {user.fullName}</h1>
      <p>Vai trò: {user.roles.join(", ")}</p>
      {/* Render widgets from all role sections */}
    </div>
  );
}
```

**Router** (`src/router/index.tsx`):
```typescript
{
  path: "/dashboard/multi-role",
  element: <MultiRoleDashboardPage />
}
```

**Login redirect** (`src/pages/auth/LoginPage.tsx`):
```typescript
const destination = user.roles.length > 1 && from === "/dashboard"
  ? "/dashboard/multi-role"
  : from || "/dashboard";
```

### 6. API Client (`src/lib/apiClient.ts`)

**Request interceptor** — thêm sau `X-Clinic-Id`:
```typescript
if (state.appliedRole) {
  headers.set("X-Applied-Role", state.appliedRole);
}
```

Gửi trên mọi authenticated request → BE audit listener capture.

---

## i18n Localization

### Namespace: `shell.roles`

**Vietnamese** (`locales/vi/shell.roles.json`):
```json
{
  "doctor": "Bác sĩ",
  "admin": "Quản trị",
  "receptionist": "Lễ tân",
  "pharmacist": "Dược sĩ",
  "nurse": "Điều dưỡng",
  "accountant": "Kế toán",
  "hr_manager": "Quản lý HR",
  "unknown": "Không xác định",
  "assignedAt": "Ngày gán",
  "rolesLabel": "Vai trò",
  "primaryRole": "Vai trò chính",
  "moreRoles": "Vai trò khác"
}
```

**English** (`locales/en/shell.roles.json`):
```json
{
  "doctor": "Doctor",
  "admin": "Administrator",
  "receptionist": "Receptionist",
  "pharmacist": "Pharmacist",
  "nurse": "Nurse",
  "accountant": "Accountant",
  "hr_manager": "HR Manager",
  "unknown": "Unknown",
  "assignedAt": "Assigned at",
  "rolesLabel": "Roles",
  "primaryRole": "Primary role",
  "moreRoles": "Additional roles"
}
```

---

## Test Coverage

### BE Test Suite

**Unit tests** (`tests/unit/`):
- `test_sod.py` (8 tests):
  - `TestCheckNoSelfApproval` (6): verify 403 + message format
  - `TestMakeSodDep` (2): dependency factory behavior
- `test_audit_applied_role.py` (3 tests):
  - Sync capture từ ContextVar
  - Sync with None (fallback)
  - Async capture

**Integration tests** (`tests/integration/`):
- `test_sod_violations.py` (3 NEW tests):
  - `TestSoDInvoicePayment::test_invoice_creator_cannot_record_payment_returns_403_sod_violation`
  - `TestSoDInvoicePayment::test_different_user_can_record_payment` (negative control)
  - `TestSoDPharmacyDispense::test_prescription_creator_cannot_dispense_returns_403`

**Total BE**: 14 tests pass ✅

### FE Test Suite

**Sidebar multi-role** (6 tests):
- Single-role: no dividers, `data-testid="sidebar-single-role"` present
- Multi-role: role sections rendered, dividers present, applied-role indicator dot visible

**Topbar role chip** (6 tests):
- Single-role: show primary role label
- Multi-role: show "+N" badge, dropdown lists all roles
- No roles: fallback gracefully

**Applied role context** (10 tests):
- `authStore.setAppliedRole()`: updates state + persists
- `authStore.setTokens()`: defaults to first role
- `authStore.logout()`: clears applied role
- `apiClient`: sends X-Applied-Role header when set, omits when null
- Login redirect: multi-role → `/dashboard/multi-role`, single-role → `/dashboard`

**Total FE**: 592 tests pass ✅  
**TypeScript**: 0 errors  
**ESLint**: 0 warnings

---

## Cross-task Coordination

### ⚠️ CRITICAL: Wave 2-A (TASK-037) `applied_role` Hash Chain Conflict

**Issue**: Both TASK-035 (applied_role column) + TASK-037 (hash chain columns) modify `audit_log`.

**Migration order** (at merge):
1. `0026_audit_applied_role` (TASK-035)
2. `0022_hash_chain` (TASK-037) — adds `prev_hash`, `row_hash`, `chain_seq`

**Recommended**: Execute `0026` first, then `0022`.

**Hash function**: TASK-037's `fn_audit_row_data_json()` must include `applied_role` in canonical JSON:
```sql
CREATE OR REPLACE FUNCTION fn_audit_row_data_json() RETURNS TRIGGER AS $$
BEGIN
  -- Include applied_role in JSON for hashing
  NEW.audit_data_json = jsonb_build_object(
    'entity_type', NEW.entity_type,
    'record_id', NEW.record_id,
    'action', NEW.action,
    'applied_role', NEW.applied_role,  -- ADD THIS
    'user_id', NEW.user_id,
    'changes', NEW.changes
  );
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

**Action at merge** (Wave 3-B merge commit):
- New migration `0027_audit_include_applied_role_in_hash` re-creates `fn_audit_row_data_json()` + re-backfills `row_hash`
- TASK-037 handoff already placed TODO comment

### TASK-040 (Pharmacy Stocktake/Expiry)

**Sidebar conflict**: TASK-040 adds pharmacy page routes, NO new top-level nav items.
**Action**: No ROLE_NAV_SECTIONS changes needed. ✅ No merge collision.

### TASK-044 (4 Role-specific Dashboards)

**Routes**: Reception, Nurse, Pharmacy, Admin dashboards (pending TASK-044).
**Action at merge**: Orchestrator adds 4 route objects to ROLE_NAV_SECTIONS:
```typescript
ROLE_NAV_SECTIONS[Role.Reception] = [
  { path: "/dashboard/reception", ... },
  // ...
];
```

### TASK-033 (Topbar ClinicSwitcher)

**Layout**: ClinicSwitcher (left flex) + controls + Avatar (right flex group).
**Status**: ✅ Coexists OK. No overlap.

### TASK-036 (Topbar Cmd+K Button)

**Layout**: Cmd+K button in controls section (right flex).
**Status**: ✅ Coexists OK.

---

## Decisions Deferred

1. **Stocktake Approve SoD** — endpoint not yet implemented; RBAC-016 note 3
2. **Audit Applied Role Hash** — merged in TASK-037 Wave 2-A; tracked as follow-up
3. **Topbar Popover with assigned_at** — visual enhancement; consider follow-up once user roles API fully wired

---

## Acceptance Criteria ✅

- [x] User with 1 role: sidebar no dividers (identical to current)
- [x] User with 2+ roles: sidebar shows dividers; nav grouped per role
- [x] Avatar role chip + "+N" badge
- [x] Audit log entries include `applied_role` field
- [x] SoD: same user cannot create + approve same invoice/prescription (403 test passes)
- [x] BE: 14 tests pass (audit + SoD)
- [x] FE: 592 tests pass (sidebar + topbar + applied_role context)

---

## Completion Notes (2026-05-01)

**Status**: DONE — all requirements + acceptance criteria met.

- All 14 BE targeted tests pass (8 SoD unit + 3 audit unit + 3 SoD integration)
- All 592 FE tests pass (TS clean, lint clean)
- F.5/F.6/F.7 implemented post-fix (applied_role state + X-Applied-Role header + /dashboard/multi-role route)
- 2/3 SoD endpoints applied (invoice payment + pharmacy dispense; stocktake deferred due to missing endpoint)
- Cross-task coordination: TASK-037 merge plan documented; TASK-040/044/033/036 coexistence verified
- i18n complete (vi + en role labels + UI text)

**Ready for production merge** (subject to Wave 2-A TASK-037 hash-chain follow-up at main branch merge).
