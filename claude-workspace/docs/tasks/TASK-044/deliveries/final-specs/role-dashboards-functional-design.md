# Thiết kế chức năng: 4 Role-specific Dashboards

**Task**: TASK-044
**Ngày hoàn thành**: 2026-05-01
**Status**: DONE
**Branch**: `feature/task-044-role-dashboards`
**Worktree**: `clinic-cms-web-w4a`

---

## Mục đích

Xây dựng 4 dashboard riêng biệt theo vai trò người dùng, cung cấp thông tin và hành động phù hợp với công việc hàng ngày của từng role trong phòng khám:

- **Lễ tân (Reception)** — Quản lý hàng chờ và lịch hẹn, tiếp nhận BN mới
- **Điều dưỡng (Nurse)** — Theo dõi ghi sinh hiệu, cảnh báo dị ứng/bất thường
- **Dược sĩ (Pharmacist)** — Quản lý đơn phát thuốc, tồn kho thấp, hàng hết hạn
- **Admin** — Tổng quan doanh thu, phân bố bệnh nhân, nhật ký hoạt động, feature flags

---

## Phạm vi

- 4 trang FE mới: `ReceptionDashboardPage`, `NurseDashboardPage`, `PharmacyDashboardPage`, `AdminDashboardPage`
- Permission gates (RequirePermission) cho từng trang
- i18n vi/en namespace `dashboards` (plural) với 4 sub-namespace
- Mock data pattern tương thích với BE swap (useQuery + placeholderData)
- 25 unit tests + cập nhật route-guard tests (5 files, 572 tổng)

Ngoài phạm vi: sidebar nav entries (TASK-035 merge), multi-role landing page (TASK-040), BE seed migration (merge-time follow-up).

---

## Chi tiết từng Dashboard

### ReceptionDashboardPage (`/dashboards/reception`)

**Permission**: `reception.dashboard`

**KPI Cards (4 thẻ)**:
| testId | Nội dung |
|---|---|
| `kpi-waiting` | BN đang chờ tiếp nhận |
| `kpi-registered-today` | BN đã đăng ký hôm nay |
| `kpi-walkin-vs-appt` | Tỷ lệ Walk-in vs Appointment (dạng phân số) |
| `kpi-upcoming-appointments` | Lịch hẹn trong 1h tới |

**Widgets**:
- Queue mini-board: Top 5 BN đang chờ (số thứ tự, tên BN, thời gian chờ, loại visit). Empty state khi không có BN.
- Lịch hẹn hôm nay: Table hiển thị giờ hẹn, tên BN, loại visit, bác sĩ phụ trách. Empty state khi không có lịch.
- Quick action: Button `btn-new-walkin` — điều hướng đến `/reception/queue` để tiếp nhận BN mới nhanh.

**Data source**: `visitApi.queue()` (placeholderData = MOCK hàng chờ), `appointmentApi.list()` (placeholderData = MOCK lịch hẹn). refetchInterval = 30s.

---

### NurseDashboardPage (`/dashboards/nurse`)

**Permission**: `nurse.dashboard`

**KPI Cards (3 thẻ)**:
| testId | Nội dung |
|---|---|
| `kpi-waiting-vitals` | BN đang chờ ghi sinh hiệu |
| `kpi-needs-screening` | BN cần sàng lọc |
| `kpi-pending-prescriptions` | Đơn thuốc cần phát |

**Widgets**:
- Alert Panel (`alert-panel`): Cảnh báo dị ứng / sinh hiệu bất thường. Border đỏ (`border-red-500`), sticky top. Hiển thị tên BN, loại cảnh báo (ALLERGY/ABNORMAL_VITALS).
- BarChart bộ phận: Recharts BarChart (`bar-chart`) — số BN đang xử lý theo khoa (màu `#6366f1` indigo-500). Dữ liệu mock 5 khoa.
- Bảng lịch sử sinh hiệu (`table-vitals-history`): Thời gian, tên BN, nhiệt độ, huyết áp, mạch, SpO2, điều dưỡng phụ trách. Empty state.

**Data source**: Mock tĩnh (MOCK_VITALS_HISTORY, MOCK_ALERTS, MOCK_DEPT_STATS). staleTime = 60s.

---

### PharmacyDashboardPage (`/dashboards/pharmacy`)

**Permission**: `pharmacy.dashboard`

**KPI Cards (4 thẻ)**:
| testId | Nội dung |
|---|---|
| `kpi-pending-dispense` | Đơn đang chờ phát |
| `kpi-dispensed-today` | Đơn đã phát hôm nay |
| `kpi-near-expiry` | Lô sắp hết hạn (30/60/90 ngày) |
| `kpi-low-stock` | Mặt hàng tồn kho thấp (clickable — điều hướng inventory) |

**A11y note**: `kpi-low-stock` là thẻ clickable, render dưới dạng `<button type="button">` với `aria-label="Xem chi tiết tồn kho thấp"` để đảm bảo keyboard accessibility.

**Widgets**:
- Alert banner tồn kho thấp: Hiển thị khi `lowStockData.length > 0`.
- BarChart tồn kho thấp: Recharts BarChart — top 8 mặt hàng tồn kho thấp (màu `#f59e0b` amber-500).
- Bảng đơn chờ phát (`table-pending-rx`): Top 10 đơn, ưu tiên urgent/normal (badge màu đỏ/xám). Cột: Số đơn, BN, Thuốc, Số lượng, Giờ kê.
- Quick actions: `btn-inventory` (điều hướng `/pharmacy/inventory`), `btn-handle-expiry` (điều hướng `/pharmacy/adjustments`).

**Data source**: `pharmacyApi.listPendingDispense()` (refetchInterval 30s), `pharmacyApi.getStockStatus()` (staleTime 60s). placeholderData = MOCK tương ứng.

---

### AdminDashboardPage (`/dashboards/admin`)

**Permission**: `admin.dashboard`

**KPI Cards (6 thẻ — richer than spec's 4)**:
| testId | Nội dung |
|---|---|
| `kpi-revenue-today` | Doanh thu hôm nay (format VND) |
| `kpi-revenue-week` | Doanh thu tuần này |
| `kpi-revenue-month` | Doanh thu tháng này |
| `kpi-new-patients` | BN mới hôm nay |
| `kpi-return-patients` | BN tái khám hôm nay |
| `kpi-pending-invoices` | Hoá đơn chưa thu |

**Widgets**:
- LineChart doanh thu 30 ngày (`line-chart`): Recharts LineChart, stroke `#6366f1` indigo-500. Dữ liệu 30 ngày mock.
- PieChart phân bố BN theo khoa (`pie-chart`): 6 màu (indigo/emerald/amber/red/violet/slate). Recharts PieChart + Legend.
- Activity feed (`activity-feed`): Nhật ký hoạt động 24h gần nhất — tên nhân viên, hành động, thời gian. Empty state.
- Feature flags panel (`feature-flags-panel`): BHYT enabled (CheckCircle2 green / XCircle red), Multi-role enabled.

**Data source**: `dashboardApi.getSnapshot()` (refetchInterval 60s), mock tĩnh cho revenue trend, pie data, activity feed, feature flags.

---

## Routes

| Path | Component | Permission |
|---|---|---|
| `/dashboards/reception` | `ReceptionDashboardPage` | `reception.dashboard` |
| `/dashboards/nurse` | `NurseDashboardPage` | `nurse.dashboard` |
| `/dashboards/pharmacy` | `PharmacyDashboardPage` | `pharmacy.dashboard` |
| `/dashboards/admin` | `AdminDashboardPage` | `admin.dashboard` |

Routes được thêm vào `src/router/index.tsx`. Không xung đột với `/dashboard` (singular, TASK-024) hay `/dashboards/multi-role` (TASK-040).

---

## Permissions

**Convention**: 2-level dotted form, nhất quán với các permission hiện có (`pharmacy.view`, `admin.access`, `visit.read`, `shift.manage`).

| Permission | Áp dụng cho |
|---|---|
| `reception.dashboard` | ReceptionDashboardPage |
| `nurse.dashboard` | NurseDashboardPage |
| `pharmacy.dashboard` | PharmacyDashboardPage |
| `admin.dashboard` | AdminDashboardPage |

**Lưu ý**: 4 permission này chưa có trong BE seed (`alembic/versions/0007_seed_permissions_and_roles.py`). Cần thêm migration tại merge-time (xem §Merge-time TODOs).

Fallback khi thiếu permission: `<div>common:forbidden</div>` (consistent với RequirePermission pattern).

---

## i18n

Namespace `dashboards` (plural, coexist với `dashboard` singular từ TASK-024 — không collision):

```
dashboards:
  reception.*     (~80 keys vi + en)
  nurse.*         (~80 keys vi + en)
  pharmacy.*      (~80 keys vi + en)
  admin.*         (~80 keys vi + en)
```

Registered trong `src/lib/i18n.ts`. Key parity vi=en verified. Nội dung Vietnamese lâm sàng phù hợp (BN, ĐK, BS., ĐD., Sàng lọc, Sinh hiệu, Tồn kho, BHYT, Đa vai trò).

---

## Mock Data Pattern

Tất cả 4 dashboard dùng pattern nhất quán:

```tsx
const query = useQuery({
  queryKey: ["module", "key"],
  queryFn: async () => realApi.call(),
  placeholderData: MOCK_DATA,
  refetchInterval: 30_000, // hoặc staleTime
});

const data = query.data?.length > 0 ? query.data : MOCK_DATA;
```

Khi BE adapter sẵn sàng: chỉ cần thay `queryFn` và bỏ fallback về `MOCK_DATA` — không cần refactor component.

---

## Test Coverage

| File | Tests | Nội dung |
|---|---|---|
| `ReceptionDashboardPage.test.tsx` | 5 | Render, 4 KPI cards, queue, appointments, btn-new-walkin |
| `NurseDashboardPage.test.tsx` | 5 | Render, 3 KPI cards, alert panel, bar chart, vitals table |
| `PharmacyDashboardPage.test.tsx` | 5 | Render, 4 KPI cards, low-stock chart, pending Rx table |
| `AdminDashboardPage.test.tsx` | 6 | Render, 6 KPI cards, line chart, pie chart, activity feed, flags |
| `route-guard.test.tsx` | 4 | RequirePermission fallback khi thiếu từng permission |
| **Tổng** | **25** | 572 tests toàn dự án (55 files) |

---

## Cross-task Coordination

### TASK-035 Wave 3-B Sidebar

4 trang dashboard **chưa có nav entries** trong `Sidebar.tsx`. Merge-time action: orchestrator thêm 4 entries vào `ROLE_NAV_SECTIONS` trong `Sidebar.tsx` tương ứng với từng role:
- `reception.dashboard` → entry dưới nhóm Lễ tân
- `nurse.dashboard` → entry dưới nhóm Điều dưỡng
- `pharmacy.dashboard` → entry dưới nhóm Dược
- `admin.dashboard` → entry dưới nhóm Quản trị

Hiện tại 4 route vẫn reachable qua direct URL.

### TASK-040 `/dashboards/multi-role`

TASK-044 không thêm `/dashboards/multi-role`. Route này thuộc TASK-040. Không có path collision.

### TASK-039 Design Tokens

`tailwind.config.js` xác nhận Indigo `#6366f1` + Plus Jakarta Sans. Các trang dùng `bg-indigo-500`, `text-indigo-600`, `bg-emerald-100`, `bg-amber-100`, `bg-red-100` — nhất quán với token palette.

---

## Merge-time TODOs

1. **BE permission seed migration**: Thêm 4 permission mới vào alembic seed tiếp theo:
   ```python
   # Thêm vào alembic/versions/xxxx_seed_permissions.py
   ("reception.dashboard", "Xem dashboard lễ tân"),
   ("nurse.dashboard", "Xem dashboard điều dưỡng"),
   ("pharmacy.dashboard", "Xem dashboard dược sĩ"),
   ("admin.dashboard", "Xem dashboard admin"),
   ```
   Gán cho roles tương ứng: `receptionist`, `nurse`, `pharmacist`, `admin`.

2. **Sidebar nav entries**: Orchestrator tại TASK-035 merge thêm 4 entries vào `ROLE_NAV_SECTIONS`.

3. **Real BE endpoints**: Khi adapter layer sẵn sàng (TASK-041), thay `queryFn` trong các dashboard để gọi API thực. Components không cần refactor.
