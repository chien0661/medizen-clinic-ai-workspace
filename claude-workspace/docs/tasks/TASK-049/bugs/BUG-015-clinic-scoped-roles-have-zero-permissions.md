---
id: BUG-015
title: Tất cả clinic-scoped roles có 0 permissions trong DEMO clinic — RBAC seeding gap
severity: Critical
status: OPEN
discovered_in: TASK-049 Phase 6 — cashier_em login Billing trả "Không có quyền truy cập"
url: DB account_clinic_role / role_permission
---

# BUG-015: Clinic-scoped roles thiếu permissions; cashier role không có system template

## Symptom

Login `cashier_em` (role `cashier`, DEMO clinic) → navigate `/#/billing/invoices` → page hiện "**Không có quyền truy cập**". JWT claims:

```json
{
  "role_codes": ["cashier"],
  "permissions": [],   // ← 0 perms
  "active_clinic_id": "a0000000-..."
}
```

## DB state observation

```sql
SELECT r.code, r.clinic_id, COUNT(rp.permission_code)
FROM role r LEFT JOIN role_permission rp ON rp.role_id = r.id
GROUP BY r.id, r.code, r.clinic_id ORDER BY r.code, r.clinic_id;
```

| code | clinic_id | perm_count |
|---|---|---|
| admin | DEMO | **0** |
| admin | (system NULL) | 56 |
| cashier | DEMO | **0** |
| cashier | (system NULL) | **— (missing!)** |
| doctor | DEMO | **0** |
| doctor | (system NULL) | 22 |
| nurse | DEMO | **0** |
| nurse | (system NULL) | 16 |
| pharmacist | DEMO | **0** |
| pharmacist | (system NULL) | 14 |
| receptionist | DEMO | **0** |
| receptionist | (system NULL) | 17 |

→ 2 vấn đề:
1. **Mọi clinic-scoped role có 0 perms** — chỉ template-level (NULL clinic_id) có perms
2. **Cashier không có system template** — không có row `role(code='cashier', clinic_id=NULL)`

## Why admin/doctor/etc still work?

Tokens issued cho admin/doctor/receptionist vẫn chứa perms khi login → nghĩa là `rbac_service.get_user_effective_permissions(user_id, active_clinic_id)` đang **resolve qua system template** (fallback to NULL clinic_id) cho 5 roles có template. Cashier không có template → 0 perms → page block.

## Repro
1. Login `cashier_em` / `Cashier@1234`
2. Decode JWT → `permissions: []`
3. Navigate `/#/billing/invoices` → "Không có quyền truy cập"

## Suggested fix

**Quick fix (seed)**:
```sql
-- Tạo system template cho cashier
INSERT INTO role (id, code, clinic_id, ...)
VALUES (uuid_generate_v4(), 'cashier', NULL, ...);

-- Gán perms typical cho cashier
INSERT INTO role_permission (role_id, permission_code) VALUES
  ((SELECT id FROM role WHERE code='cashier' AND clinic_id IS NULL), 'invoice.read'),
  (..., 'invoice.create'),
  (..., 'invoice.modify'),
  (..., 'payment.receive'),
  (..., 'patient.read');
```

**Architectural fix**: investigate why DEMO clinic-scoped role rows are 0-perm. Có thể:
- TASK-004 RBAC seeding chỉ tạo template, không clone-down vào tenant-scoped
- Onboarding wizard (TASK-006) phải tạo clinic-scoped role + clone perms từ template — verify chưa làm

Recommend audit `clinic-cms-merge/alembic/versions/0007_seed_permissions_and_roles.py` + onboarding service để xác nhận expected behavior.

## Impact (CRITICAL)
- Cashier role 100% unusable — block Phase 6 billing flow
- Có khả năng các role khác cũng bị phụ thuộc fragile vào system template (nếu BE đổi resolve logic, vỡ mọi role)
- Onboarding clinic mới có thể tạo clinic-scoped roles 0-perm → all roles broken cho tenant mới

## Related
- TASK-004 RBAC: 5 system roles seeded (cashier không trong list ban đầu? cần kiểm)
- TASK-006 Tenant Onboarding Wizard: roles phải được clone hoặc grant per clinic
- BUG-002 (User roles cell empty): có thể cùng class — RBAC seeding/resolution gaps
