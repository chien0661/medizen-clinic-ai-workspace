---
id: BUG-003
title: Add User flow KHÔNG assign clinic — user mới không login được
severity: Critical
status: OPEN
discovered_in: TASK-049 Phase 1 — admin add user + test login
url: https://ff02-210-245-74-43.ngrok-free.app/#/admin/users
---

# BUG-003: Add User flow KHÔNG assign clinic — user mới không login được

## Symptom
Sau khi admin tạo user mới qua "Add User" modal, user không thể login. Login form hiện alert:
> **"Tài khoản chưa được gán phòng khám nào. Vui lòng liên hệ quản trị viên."**

## Reproduction
1. Login admin (`admin` / `Demo@1234`) trên DEMO clinic
2. Vào `Admin → Users` → click "Add User"
3. Fill: username `test_e2e_dr`, full name, email, password `Test@1234`, tick role "Doctor"
4. Submit → user xuất hiện trong list (count tăng), KHÔNG có error
5. Logout, đến login page
6. Login với `test_e2e_dr` / `Test@1234`
7. → Error: "Tài khoản chưa được gán phòng khám nào..."

## Root cause (suspected)
- Multi-tenant: user_clinic relationship table không được populate khi tạo user
- Add User modal **thiếu field**: chọn clinic (hoặc auto-default vào current admin's active clinic)
- API endpoint `POST /api/v1/users` (hoặc tương tự) không gán user vào clinic của caller (admin) bằng default

## Impact (CRITICAL)
- **Admin không thể tạo user mới qua UI** — feature hoàn toàn không dùng được
- Workflow tạo nhân sự mới (BS, ĐD, LT, DS, TN) hiện đang bị BLOCK
- User-facing: tăng support load, admin nghi ngờ data integrity
- Workaround duy nhất hiện tại: seed user qua DB script (như `seed_demo_data.py`)

## Expected behavior
**Option A — auto-default**: Add User auto-gán vào active clinic của admin (DEMO) — đây là hành vi reasonable nhất cho single-clinic admin.

**Option B — explicit field**: Add field "Phòng khám" (single-select hoặc multi-select) trong modal, default vào active clinic.

→ Khuyến nghị **Option A** cho v1, Option B nếu cần multi-clinic assignment.

## Files involved
- BE: `clinic-cms-merge/app/modules/users/api/routes.py` (POST /users) + service layer
- BE: `clinic-cms-merge/app/modules/users/models/user_clinic.py` (hoặc tương đương)
- FE: `clinic-cms-web/src/pages/admin/users/AddUserModal.tsx` (ước đoán)

## Suggested fix
**BE change** (Option A):
```python
# In user creation service
async def create_user(payload, ctx):
    user = User(...)
    db.add(user)
    # Auto-assign to active clinic
    db.add(UserClinic(user_id=user.id, clinic_id=ctx.active_clinic_id))
    await db.commit()
```

## Related
- BUG-002: Roles cell rỗng — có thể cùng root cause (FK constraint violation prevents role + clinic assignment when create)
