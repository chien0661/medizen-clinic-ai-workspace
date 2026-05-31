---
id: BUG-022
title: Admin Users page crash — `Cannot read properties of undefined (reading 'map')` on user.roles
severity: Critical
status: OPEN
discovered_in: TASK-049 admin section walkthrough — re-test sau BUG-008 fix
url: http://localhost:1420/#/admin/users
---

# BUG-022: Admin Users page React crash — user.roles undefined

## Symptom
Login admin → navigate `/#/admin/users` → page crash với React error: **"Cannot read properties of undefined (reading 'map')"** ở `UsersPage.tsx:1022:164` (transformed line) inside `Array.map`. Global ErrorBoundary catch + show "Something went wrong / Reload" — block toàn bộ admin user management UX.

## API response (verified 200 OK)
```json
{
  "data": [
    {
      "id": "...",
      "username": "dr_le",
      "full_name": "BS. Lê Thị Mai",
      "email": "...",
      "phone": null,
      "is_active": true,
      "is_locked": false,
      "license_number": null,
      "specialty_subfield": null,
      "clinic_id": "..."
    },
    ...
  ],
  "total": 15
}
```

→ **API response KHÔNG include `roles` field cho từng user.** FE đang gọi `user.roles.map(...)` (or similar) → crash vì `roles === undefined`.

Cùng root cause với **BUG-002** (User roles cell empty): API thiếu roles → FE expects array → undefined.map crashes.

## Repro
1. Admin login (`admin` / `Demo@1234`)
2. Navigate `/#/admin/users`
3. → Page crash + error boundary

## Files involved
- BE: `clinic-cms-merge/app/modules/users/api/routes.py` (GET /api/v1/users) + `schemas/user_schemas.py` (response shape)
- BE: `clinic-cms-merge/app/modules/users/services/user_service.py` (data assembly)
- FE: `clinic-cms-web/src/pages/admin/UsersPage.tsx:~978,1022` (the .map call)

## Suggested fix

**Option A (BE — preferred)**: Include `roles: list[str]` in user list response. Source from `account_clinic_role.role_codes` for the active clinic. This also closes BUG-002.

```python
# user_service.list_users()
# Join with account_clinic_role to populate role_codes per user
result = await db.execute(
    select(User, AccountClinicRole.role_codes)
    .outerjoin(AccountClinicRole, ...)
    .where(...)
)
```

**Option B (FE — defensive)**: `(user.roles ?? []).map(...)` — quick patch, but doesn't solve underlying data gap.

→ **Recommend Option A**. Closes BUG-002 + BUG-022 + makes admin UX functional.

## Impact (CRITICAL)
- 100% block admin user management feature
- Cannot list, edit, search, deactivate users via UI
- Workaround: query DB directly (admin-only ops via SQL)

## Related
- BUG-002 (Medium): roles cell empty in user list — same data gap
- BUG-003: Add User no clinic assignment — fixed by Agent 1 (running)
- TASK-035: applied_role audit + multi-role context — needs roles array to function

## Test gap
- No FE unit test for UsersPage rendering with API response missing roles field
- No BE integration test asserting `GET /users` includes roles
