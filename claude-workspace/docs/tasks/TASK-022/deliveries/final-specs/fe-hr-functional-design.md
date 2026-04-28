# Thiết Kế Chức Năng FE — Module HR (TASK-022)

**Trạng thái:** DONE  
**Ngày hoàn thành:** 2026-04-27  
**Nhánh:** `feature/task-022-fe-hr`  
**BE phụ thuộc:** TASK-014 (HR API — đã merge vào main)  
**FE nền tảng:** TASK-017 (Auth + Shell + i18n + Design System)

---

## 1. Phạm Vi Chức Năng

Module HR FE cung cấp giao diện người dùng cho quản lý ca làm việc, lịch định kỳ, đơn nghỉ phép và chấm công.

---

## 2. Cấu Trúc File

```
src/
├── modules/hr/
│   ├── types.ts          — TypeScript interfaces (mirrors BE Pydantic schemas)
│   ├── api.ts            — Tất cả HR API calls qua apiClient.ts
│   └── helpers.ts        — Hàm tính toán thuần (calcLateMinutes, calcOtHours, v.v.)
├── pages/hr/
│   ├── ShiftCalendarPage.tsx    — /hr/schedule
│   ├── RecurringSchedulePage.tsx — /hr/recurring
│   ├── ShiftTemplatesPage.tsx   — /hr/shift-templates
│   ├── LeaveNewPage.tsx         — /hr/leave/new
│   ├── LeaveApprovePage.tsx     — /hr/leave/approve
│   ├── TimeLogPage.tsx          — /hr/me/timelog
│   └── AttendanceExportPage.tsx — /hr/attendance/export
├── components/hr/
│   ├── AttendanceWidget.tsx     — Widget check-in/out (nhúng trong Dashboard)
│   └── ShiftEditModal.tsx       — Modal chỉnh sửa ca từ calendar
├── locales/
│   ├── vi/hr.json               — Ngôn ngữ tiếng Việt
│   └── en/hr.json               — Ngôn ngữ tiếng Anh
└── tests/hr/
    ├── helpers.test.ts           — Unit tests cho calculation helpers
    ├── i18n-hr.test.ts           — i18n key parity + diacritics tests
    ├── AttendanceWidget.test.tsx — Component tests (AC5, AC6, AC8)
    ├── LeaveNewPage.test.tsx     — Form component tests (AC3)
    └── RequirePermission.hr.test.tsx — Permission gating tests
```

---

## 3. Trang và Chức Năng Chi Tiết

### 3.1 Lịch Ca (`/hr/schedule`)

**Thư viện:** `react-big-calendar` với `date-fns` localizer  
**Locale:** Vi (Thứ 2 là ngày đầu tuần)

| Tính năng | Mô tả | Permission |
|-----------|--------|-----------|
| Xem tuần/tháng | Toggle view button | Tất cả |
| Hiển thị ca | Events màu theo status: xanh=scheduled, xanh lá=completed, đỏ=cancelled, vàng=on_leave | Tất cả |
| Kéo thả | Dời ca sang ngày khác → PATCH /shifts/{id} | `shift.manage` |
| Click ca | Mở ShiftEditModal | Tất cả |
| Lọc | Filter theo user_id | Tất cả |
| Modal edit | React Hook Form + Zod validation | `shift.manage` |

**API calls:**
- `GET /api/v1/shifts?from=&to=&user_id=` — load events
- `PATCH /api/v1/shifts/{id}` — drag-drop reschedule

**Query key:** `["hr", "shifts", fromDate, toDate, filterUserId]`

### 3.2 Lịch Định Kỳ (`/hr/recurring`)

| Tính năng | Mô tả |
|-----------|--------|
| Bảng danh sách | User, mẫu ca, ngày trong tuần (T2-CN), ngày hiệu lực |
| Thêm mới | Modal form với multi-select ngày trong tuần (checkbox toggle) |
| Tạo ca | Nút RefreshCw mở GenerateModal → POST generate-shifts?until=YYYY-MM-DD |
| Xóa | DELETE với icon Trash2 |

**API calls:**
- `GET /api/v1/recurring-schedules`
- `POST /api/v1/recurring-schedules`
- `DELETE /api/v1/recurring-schedules/{id}`
- `POST /api/v1/recurring-schedules/{id}/generate-shifts?until=YYYY-MM-DD`

### 3.3 Quản Lý Mẫu Ca (`/hr/shift-templates`)

Chỉ hiển thị với người dùng có quyền `shift.manage`. Người dùng không có quyền thấy fallback text.

| Tính năng | Mô tả |
|-----------|--------|
| CRUD | Tên ca, giờ bắt đầu, giờ kết thúc |
| Toggle is_active | Click badge Active/Inactive → PATCH |

### 3.4 Đăng Ký Nghỉ Phép (`/hr/leave/new`)

Form đơn giản với React Hook Form + Zod:
- **Loại phép:** sick / personal / vacation / other
- **Ngày bắt đầu / kết thúc:** date picker, end_date >= start_date validation
- **Lý do:** textarea, required
- On success → toast + navigate to `/hr/me/timelog`

### 3.5 Duyệt Đơn Nghỉ (`/hr/leave/approve`)

Chỉ dành cho `leave.approve`. Bảng với filter status:

| Tính năng | Mô tả |
|-----------|--------|
| Filter | Dropdown: pending / approved / rejected / tất cả |
| Approve | POST /leave-requests/{id}/approve → toast |
| Reject | Mở RejectModal → nhập lý do → POST /leave-requests/{id}/reject |
| Badge status | Màu vàng=pending, xanh=approved, đỏ=rejected |

### 3.6 Widget Chấm Công (Dashboard)

Widget nhúng vào `DashboardPage`.

| Tính năng | Mô tả |
|-----------|--------|
| Ca hôm nay | GET /shifts?from=today&to=today |
| Check-in button | POST /attendance/check-in {shift_id, method: "manual"} |
| Check-out button | Xuất hiện sau khi đã check-in |
| Method tabs | Manual (click trực tiếp) / PIN (input + submit) / QR (stub "Coming soon") / Biometric (stub) |
| Late display | Hiển thị "Trễ X phút" nếu late_minutes > 0 |
| OT display | Hiển thị "OT H:MM" sau check-out nếu ot_hours > 0 |
| Error 409 | Toast "Đã check-in" |

**State logic:**
- `activeTimelog` = time log không có `check_out_at` → trạng thái đã check-in
- `lastCompletedLog` = time log có `check_out_at` → hiển thị OT

### 3.7 Nhật Ký Chấm Công (`/hr/me/timelog`)

Calendar tháng với TanStack Query:
- Mỗi ô: ca dự kiến + giờ check-in/check-out thực tế
- Màu: xanh lá = đúng giờ, vàng = trễ, đỏ = vắng mặt, xám = không có ca
- Nav tháng: nút prev/next
- Footer stats: tổng giờ, số lần trễ, giờ OT

### 3.8 Xuất Báo Cáo (`/hr/attendance/export`)

Chỉ dành cho `attendance.manage`:
- Date range picker
- Format radio: XLSX (active) / CSV (disabled — BE chưa hỗ trợ)
- File download via `Blob + a.click()`
- Raw fetch (không qua apiRequest) để xử lý blob response

---

## 4. Quản Lý State

| Pattern | Dùng cho |
|---------|---------|
| TanStack Query `useQuery` | Tất cả GET requests |
| TanStack Query `useMutation` | POST/PATCH/DELETE với `invalidateQueries` on success |
| Zustand `useAuthStore` | Auth state, permissions check |
| Local state (`useState`) | Modal open/close, filter values, current date |

**Query key convention:**
```
["hr", "shifts", fromDate, toDate, userId]
["hr", "recurring-schedules"]
["hr", "shift-templates"]
["hr", "leave-requests", statusFilter]
["hr", "attendance", "me", date]
```

---

## 5. Phân Quyền

| Permission | Tính năng được bảo vệ |
|-----------|----------------------|
| `shift.manage` | ShiftTemplatesPage (full page gate), drag-drop calendar, create/edit/delete shifts, recurring schedules |
| `leave.approve` | LeaveApprovePage (full page gate) |
| `attendance.manage` | AttendanceExportPage (full page gate), check-in/out API |

Dùng `RequirePermission` component từ TASK-017 cho UI gating. API-level permission enforced by BE.

---

## 6. i18n

Namespace: `hr` — file: `src/locales/{vi,en}/hr.json`

Tất cả chuỗi user-facing sử dụng `t("hr:...")`. Tiếng Việt bảo đảm dấu đầy đủ UTF-8.

Key quan trọng cho AC:
- `hr:attendance.late` = "Trễ {{minutes}} phút" (AC5)
- `hr:attendance.ot` = "OT {{hours}}" (AC6)
- `hr:attendance.alreadyCheckedIn` = "Đã check-in" (AC8)
- `hr:schedule.badge.onLeave` = "Nghỉ phép" (AC4)

---

## 7. Schema BE

Xem chi tiết: `clinic-cms/app/modules/hr/schemas/hr_schemas.py` (TASK-014).  
**Ghi chú:** BE schema là nguồn đáng tin cậy — FE chỉ tiêu thụ API, không quản lý DB.

SQL aggregation: **không áp dụng — FE chỉ tiêu thụ API**.

---

## 8. Tính Năng Trì Hoãn (Phase 2)

| Tính năng | Lý do trì hoãn |
|-----------|----------------|
| QR scan check-in | Cần Tauri camera plugin cấu hình thêm |
| Biometric check-in | Cần phần cứng — stub placeholder |
| CSV export | BE chỉ hỗ trợ XLSX hiện tại |

---

## 9. Testing

Xem test report: `deliveries/test-reports/test-report.md`

Tests bao gồm:
- Unit tests cho `calcLateMinutes`, `calcOtHours`, `formatOtHours`, days serialization
- i18n parity vi/en + diacritics validation
- Component tests: AttendanceWidget (AC5, AC6, AC8), LeaveNewPage (AC3)
- Permission gating: 3 pages × 2 scenarios
