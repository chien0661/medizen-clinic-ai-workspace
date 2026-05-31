---
id: BUG-002
title: User list — roles cell rỗng cho nhiều user + duplicate roles trong filter dropdown
severity: Medium
status: OPEN
discovered_in: TASK-049 Phase 1 — admin user management
url: https://ff02-210-245-74-43.ngrok-free.app/#/admin/users
---

# BUG-002: User list — roles cell rỗng cho nhiều user + duplicate roles trong filter dropdown

## Symptoms

### A. Roles cell rỗng cho nhiều user
Bảng `User Management` hiển thị 14 users nhưng cột "Roles" rỗng cho 9/14 user:

| Username | Role cell |
|---|---|
| dr_nguyen | doctor (badge OK) |
| dr_le | **rỗng** |
| dr_tran | **rỗng** |
| dr_pham | **rỗng** |
| dr_hoang | doctor (badge OK) |
| nurse_lan | **rỗng** |
| nurse_huong | **rỗng** |
| nurse_linh | nurse (badge OK) |
| recept_anh | **rỗng** |
| recept_binh | **rỗng** |
| pharm_cuong | pharmacist (badge OK) |
| pharm_dung | **rỗng** |
| cashier_em | **rỗng** |
| admin | Administrator (badge OK) |

### B. Filter dropdown duplicate + inconsistent casing
Dropdown filter "All roles" liệt kê:
- Administrator, **Doctor, Nurse, Pharmacist, Receptionist** (Title Case — kiểu BE roles)
- **doctor, nurse, receptionist, pharmacist, cashier, admin** (lowercase — kiểu legacy?)

→ User thấy 11 options cho 6 vai trò thực sự.

## Root cause (suspected)
- A: Có thể do user có >1 role, hoặc dùng role lowercase mà display logic chỉ render khi role match Title Case
- B: DB có 2 set role records — cũ (lowercase) + mới (Title Case từ TASK-007/seed). Cần migration hoặc data cleanup

## Impact
- Admin không biết vai trò user → không assign permissions chính xác
- Filter không reliable
- Data integrity nghi ngờ — có thể ảnh hưởng RBAC

## Files involved
- BE: `clinic-cms-merge/app/modules/users/` + `roles/`
- FE: `clinic-cms-web/src/pages/admin/users/UserListPage.tsx` (ước đoán)

### C. Tạo user mới với role "Doctor" (Title Case) → roles cell vẫn rỗng
Test reproducer:
1. Click "Add User"
2. Fill form: username `test_e2e_dr`, password `Test@1234`, tick checkbox "Doctor" (Title Case)
3. Click Create → user xuất hiện trong list, count tăng 14→15
4. Roles cell của row mới: **rỗng** (giống các seeded user khác)

→ Confirm: việc gán role qua Add User UI không reflect lên display. Cần verify backend xem role có thực sự assign vào DB không (test bằng cách login as test_e2e_dr → nếu access được màn doctor → role có assign, chỉ display broken).

## Suggested fix
- Migration cleanup: chỉ giữ 1 set role names, drop legacy lowercase
- FE: render role badge cho mọi user_role record (case-insensitive lookup)
- Verify list endpoint trả về user.roles array đầy đủ (debug network request)
