---
id: BUG-011
title: Receptionist thấy menu Admin + HR + Reports/Inventory + Doctor/Pharmacy trong sidebar
severity: Medium
status: OPEN
discovered_in: TASK-049 Phase 2 — receptionist dashboard sau login
url: http://localhost:1420/ (sau login recept_anh)
---

# BUG-011: Receptionist sidebar gating — thấy quá nhiều menu không thuộc role

## Symptom
Login `recept_anh` (role `receptionist`, 17 permissions) → sidebar hiển thị (từ screenshot `02-reception-dashboard.png`, `08-search-bn0020-result.png`):

- ✅ Reception (Patients, Appointments, Queue Board) — **đúng**
- ❌ Doctor (My Queue, Dashboard) — sai role
- ❌ Pharmacy (chỉ thấy collapsed) — sai role
- ✅ Billing (Invoices) — có thể đúng nếu reception cũng tạo invoice
- ❌ Reports (Inventory, Visit Volume, Prescriptions) — admin-level
- ❌ HR (Schedule, Time Log, Leave) — sai role
- ❌ Admin (collapsed) — sai role hoàn toàn
- ✅ Settings — có thể OK
- ✅ Notifications — OK

## Expected
Receptionist sidebar chỉ thấy:
- Reception (Patients, Appointments, Queue Board)
- Billing (Invoices) — nếu reception assist cashier
- Notifications
- Settings (cá nhân)

## Hypothesis
1. Sidebar component check `role === 'admin'` chứ không check **per-link permission**
2. Hoặc: applied_role context không sync với rendered sidebar
3. Hoặc: dev mode bypass tất cả gating

Verify: kiểm `clinic-cms-web/src/components/shell/Sidebar.tsx` — coi cách filter nav items.

## Repro
1. Logout
2. Login `recept_anh` / `Recept@1234`
3. Quan sát sidebar

## Impact
- Medium — UX confusion: BN/khách thấy reception dùng máy có Admin menu trông không chuyên nghiệp
- Khi click vào menu cấm, BE sẽ 403 — đã verify gián tiếp (e.g., `/api/v1/notifications/unread-count` 403 trên reception session) — chứng tỏ BE permission gate đúng nhưng FE sidebar không gate
- Không phải security hole vì BE từ chối, nhưng vi phạm principle of least surprise

## Files involved
- `clinic-cms-web/src/components/shell/Sidebar.tsx` (1 file modified hiện đang trong unstaged changes của branch print-receipts → có thể đã bắt đầu fix?)
- Likely: `nav-items` config có flag `requiredPermission` per item, sidebar component cần filter

## Related
- TASK-035 Multi-role merge sidebar UX (RBAC-015..018) — chính TASK-035 đã có "applied_role audit + SoD framework". Có thể BUG-011 là regression hoặc TASK-035 chưa ship đầy đủ
- BUG-002: User roles cell rỗng — có thể cùng class bug (RBAC FE display)
- File `Sidebar.tsx` đang có local modifications → tracker có thể đã biết
