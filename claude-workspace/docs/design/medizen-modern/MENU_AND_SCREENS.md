# MediZen — Sườn menu & Chi tiết màn hình

**Cập nhật**: 2026-04-30 (v1 — sườn menu role-aware + screen catalog 40+ màn)

Tài liệu này:
1. Vẽ sườn menu (sidebar + topbar + drawers) theo từng vai trò
2. Mô tả chi tiết mỗi màn hình ứng với từng menu item
3. Bổ sung các màn mới (Chọn phòng khám, Profile multi-clinic, Cmd+K palette) chưa có trên Stitch

Đọc kèm:
- [SITEMAP.md](SITEMAP.md) — cây tổ chức module + ma trận quyền
- [TAB_MATRIX.md](TAB_MATRIX.md) — spec đầy đủ tab cho EMR/Settings/Reports
- [MULTI_ROLE_UX.md](MULTI_ROLE_UX.md) — pattern user kiêm nhiều role
- [ACTION_FLOWS.md](ACTION_FLOWS.md) — 7 flow nghiệp vụ end-to-end

---

## A. Pre-login flow (3 màn)

### A.1 — Đăng nhập

```
┌─────────────────────────────────────────────────────────────┐
│  [Logo MediZen — gradient indigo→violet]                    │
│                                                              │
│  Chào mừng đến với MediZen                                  │
│  Hệ thống quản lý phòng khám đa khoa                        │
│                                                              │
│  ┌──────────────────────────────────────────────┐          │
│  │ 📧 Email                                      │          │
│  │ [bs.an@hongduc.vn               ]             │          │
│  │                                                │          │
│  │ 🔒 Mật khẩu                            👁     │          │
│  │ [•••••••••••••                    ]            │          │
│  │                                                │          │
│  │ ☑ Ghi nhớ tôi (30 ngày)                       │          │
│  │                                                │          │
│  │ [        ⚡ Đăng nhập         ]                │          │
│  │                                                │          │
│  │ Quên mật khẩu? · Cần hỗ trợ?                  │          │
│  └──────────────────────────────────────────────┘          │
│                                                              │
│  © 2026 VISSoft · v1.2.0                                    │
└─────────────────────────────────────────────────────────────┘
```

| Field | Giá trị |
|---|---|
| **Stitch ID** | `e98de272bc7249f39f9a233c7adb17f2` (đã có — cần update bỏ trường `clinic_code`) |
| **Path** | `/login` |
| **Permissions** | Public (chưa cần auth) |
| **Function refs** | AUTH-001, AUTH-013 (show password), AUTH-014 (remember me) |
| **Layout** | Centered card 400px width trên page-bg slate-50, KHÔNG sidebar/topbar |
| **Validation** | Email format · Password ≥1 ký tự (không hint complexity ở client) |
| **Error states** | "Email hoặc mật khẩu không đúng" (generic, không tiết lộ user tồn tại) · "Tài khoản bị khoá — thử lại sau X phút" (AUTH-006) · "Mạng lỗi" |
| **Action sau success** | Trigger AUTH-020 auto-resolve clinic → redirect đến A.2 (chooser) hoặc dashboard |

**Edge cases**:
- Account chỉ có 1 clinic → skip A.2, vào thẳng dashboard
- Account có default clinic → skip A.2, vào thẳng dashboard của default
- Account có ≥2 clinic + chưa set default → bắt buộc chuyển A.2

---

### A.2 — Chọn phòng khám (NEW — chưa có Stitch)

```
┌─────────────────────────────────────────────────────────────┐
│  [Logo MediZen]                                              │
│                                                              │
│  Chào BS. Nguyễn Hoàng An                                   │
│  Bạn có quyền truy cập 3 phòng khám — chọn 1 để bắt đầu    │
│                                                              │
│  ┌─────────────────┬─────────────────┬─────────────────┐   │
│  │ 🏥 Hồng Đức     │ 🏥 Đa khoa Mai  │ 🏥 Phòng khám   │   │
│  │ Trung Tâm       │ Lan             │ tư của tôi       │   │
│  │                  │                  │                  │   │
│  │ 142 Lê Lai · Q1 │ 56 NTMK · Q3    │ 88 Trần Phú     │   │
│  │                  │                  │                  │   │
│  │ Vai trò:         │ Vai trò:         │ Vai trò:         │   │
│  │ 🏷️ BS · Quản trị │ 🏷️ Bác sĩ        │ 🏷️ Owner        │   │
│  │                  │                  │                  │   │
│  │ Cấp ngày 12/02   │ Cấp ngày 03/04   │ Cấp ngày 28/03   │   │
│  │                  │                  │                  │   │
│  │ [Vào phòng khám →]│ [Vào phòng khám →]│ [Vào phòng khám →]│
│  │ ☐ Đặt làm mặc định│ ☐ Đặt làm mặc định│ ☐ Đặt làm mặc định│
│  └─────────────────┴─────────────────┴─────────────────┘   │
│                                                              │
│  💡 Lần sau bạn có thể đổi nhanh giữa các phòng khám       │
│     bằng dropdown cạnh avatar (góc phải trên).              │
│                                                              │
│  [Đăng xuất]                                                 │
└─────────────────────────────────────────────────────────────┘
```

| Field | Giá trị |
|---|---|
| **Stitch ID** | (chưa có — TODO Phase D) |
| **Path** | `/login/select-clinic` |
| **Permissions** | Authenticated nhưng chưa chọn clinic context |
| **Function refs** | AUTH-018 (multi-clinic mapping), AUTH-019 (set default), AUTH-020 (auto-resolve) |
| **Layout** | Center card, mỗi clinic là 1 card 320px |
| **Trigger** | Sau login OK, BE trả `clinics[]` >1 và `default_clinic_id == null` |
| **Action click vào card** | POST `/auth/select-clinic {clinic_id, set_default: bool}` → JWT nhận clinic_id → redirect dashboard |

**Edge cases**:
- User có >5 clinic → grid xuống dòng + search box trên cùng
- Clinic bị suspend → card disabled với chip "Tạm ngưng dịch vụ"
- Click checkbox "Đặt làm mặc định" trước "Vào phòng khám" → lưu default + vào

---

### A.3 — Quên mật khẩu (chưa có Stitch)

| Field | Giá trị |
|---|---|
| **Stitch ID** | (chưa có) |
| **Path** | `/login/forgot-password` |
| **Permissions** | Public |
| **Function refs** | AUTH-009 (forgot password v2) |
| **Layout** | Centered card 400px — input email + nút "Gửi link reset" |
| **Flow** | Email link 15p TTL → màn `/reset-password?token=xxx` → nhập mật khẩu mới + confirm → success → redirect login |

**Status**: v2 (Phase 2). Phase 1 dùng AUTH-008 (admin reset).

---

## B. App shell — components dùng chung

### B.1 — Topbar (56px height, sticky top)

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│  [Logo Cura]│ Trang chủ / Khám bệnh / Lê Hà Vy    ⌘K Tìm...    🔔  🏥 Hồng Đức ▾  👤 An🏷️+2▾│
└─────────────────────────────────────────────────────────────────────────────────────────┘
   240px         center: breadcrumb              right: search · noti · clinic · avatar
```

| Vùng | Thành phần | Function refs |
|---|---|---|
| **Logo (left, 240px)** | Logo MediZen, click → /home | — |
| **Breadcrumb** | "Trang chủ / Module / Resource" — click level cao quay về | NAV-008 |
| **Quick search** | Click hoặc Ctrl+K → mở popup NAV-001 | NAV-001..005 |
| **Notifications bell** | Badge số chưa đọc · click → popover 480px list 10 noti gần nhất + link "Xem tất cả" | NOTI-* |
| **Clinic switcher** | Dropdown `🏥 [Tên PK hiện tại] ▾` — list PK user có quyền + chỉ báo current. Ẩn nếu user chỉ có 1 PK | NAV-002, AUTH-021 |
| **Avatar + chip** | Avatar 32px + tên + multi-role chip ("+2" nếu >3 role) → menu Profile/Đăng xuất | RBAC-018 |

---

### B.2 — Sidebar (left, 240px collapsed 72px)

Cấu trúc theo pattern **merge sidebar** (xem `MULTI_ROLE_UX.md`):

```
┌─ Sidebar (240px) ────────────┐
│  [Logo MediZen]               │
│                               │
│  🏠 Tổng quan (Dashboard)    │ ← luôn hiện cho mọi role
│                               │
│  ─── [Group 1: Role A] ───── │ ← divider + label uppercase
│  📋 Module 1.1                │
│  📋 Module 1.2                │
│  ...                          │
│                               │
│  ─── [Group 2: Role B] ───── │ ← chỉ xuất hiện khi user có role B
│  📊 Module 2.1                │
│  ...                          │
│                               │
│  ─── Cá nhân ─────────────── │
│  👤 Profile                   │
│  ❓ Trợ giúp (?)              │
│                               │
│  ──────────────────────────── │
│  [Avatar 40px]                │
│  BS. Nguyễn Hoàng An          │
│  🏷️ Bác sĩ + Quản trị        │
│  [Đăng xuất]                  │
└───────────────────────────────┘
```

**Visibility rules**:
- Group label = role name; mục con = module mà role đó cấp
- User có quyền qua nhiều role → nhiều group hiện
- Permission deny override → ẩn module bất kể role có
- Feature flag tắt (vd `bhyt_enabled=false`) → ẩn module BHYT
- Module có quyền partial → chip nhỏ `👁` (read-only) hoặc `⚪` (partial)

**Collapsible**: Click chevron đầu group → collapse cả group. State persist per-user.

**Pin**: User có thể pin module yêu thích lên top (Phase 2).

---

### B.3 — Right drawer (360px, contextual, slide từ phải)

| Trigger | Nội dung |
|---|---|
| Trong EMR | Patient context (allergies, drugs đang dùng, vitals lịch sử) |
| Click row trong Audit log | JSON diff before/after |
| Click notification | Detail noti + link "Đi tới resource" |
| Click "Xem chi tiết" trong nhiều bảng | Detail panel của resource đó (vd patient summary) |

**Behavior**: Mở overlay không cản chính (page vẫn scroll được), Esc đóng.

---

### B.4 — Modal layer (overlay full screen, focus trap)

Loại modal phổ biến:
- **Confirm dialog**: "Hoàn tất khám?", "Xoá BN này?" — title + body + 2 button
- **Form modal**: Tạo BN mới, đặt hẹn, đổi giờ — form trong card 600-800px width
- **Onboarding tour**: Welcome modal + tooltip nối tiếp
- **Error modal**: Server error 500, mất kết nối — full-screen empty state với button "Thử lại"

Backdrop blur 12px (glassmorphism).

---

## C. Sườn menu theo vai trò

### C.1 — Lễ tân (Receptionist)

```
🏠 Tổng quan                          → Dashboard Lễ tân (e8ec8790)
─── Tiếp nhận ───
👥 Tiếp nhận BN                       → Đăng ký BN (8c84c7e3)
⏳ Phòng chờ                          → Queue card view (TODO)
👤 Hồ sơ bệnh nhân (read+write)       → Patient master list (TODO)
─── Lịch hẹn ───
📅 Lịch hẹn                           → Calendar tuần (2e1591c3)
─── Thanh toán ───
💰 Thanh toán hoá đơn                 → Billing (43971b42)
📜 Lịch sử hoá đơn                    → Invoice list (TODO)
🧾 Công nợ BN                         → AR list (TODO)
─── Báo cáo ───
📊 Báo cáo (Tổng quan + DT BHYT)      → Reports limited (d86ddd11 — read only)
```

### C.2 — Điều dưỡng (Nurse)

```
🏠 Tổng quan                          → Dashboard Điều dưỡng (41644527)
─── Phòng khám ───
⏳ Phòng chờ (sinh hiệu)              → Queue card "Chờ sinh hiệu" (TODO)
🩺 Sinh hiệu BN                       → EMR Tab 1 only (acef6986)
👤 Hồ sơ BN (read+write vital)        → Patient detail (TODO)
─── Lịch ───
📅 Lịch ca trực                       → Shift schedule view (TODO)
📅 Lịch hẹn (read-only)               → Appointment view-only (2e1591c3)
```

### C.3 — Bác sĩ (Doctor)

```
🏠 Tổng quan                          → Dashboard Bác sĩ (ccc8e775)
─── Khám bệnh ───
👥 Bệnh nhân của tôi                  → My patients today (TODO)
🩺 Khám bệnh (EMR)                    → EMR full 6 tabs (fbb61911 default)
   ├── Tab 1 Sinh hiệu                → acef6986
   ├── Tab 2 Khám LS (S.O.A.P)        → c12bf23a
   ├── Tab 3 Chẩn đoán                → fbb61911
   ├── Tab 4 Kê đơn thuốc             → 7e32e3c8
   ├── Tab 5 Cận lâm sàng             → b8f84b40
   └── Tab 6 Tóm tắt & Hoàn tất       → 41e3a324
💊 Đơn thuốc đã kê                    → Prescription history (TODO)
📋 Chỉ định CLS                       → CLS orders by me (TODO)
─── Lịch ───
📅 Lịch ca trực                       → My shifts (TODO)
📅 Lịch hẹn của tôi                   → My appointments (2e1591c3 filtered)
```

### C.4 — Dược sĩ (Pharmacist)

```
🏠 Tổng quan                          → Dashboard Dược sĩ (0d856e6c)
─── Cấp phát ───
💊 Cấp phát đơn thuốc                 → Pharmacy dispense (434d73b9)
─── Kho ───
📦 Danh mục thuốc                     → Medicine catalog (TODO)
📥 Nhập kho                           → Stock import PO (TODO)
🔢 Kiểm kê                            → Stock count (TODO)
🗑 Xử lý hết hạn                      → Expiry disposal (TODO)
─── Báo cáo ───
📊 Báo cáo dược                       → Reports — Tab Dược (6b235c69)
```

### C.5 — Quản trị (Clinic Admin)

```
🏠 Tổng quan                          → Dashboard Quản trị (e1e5cfeb)
─── Phòng khám ───
🏥 Cấu hình hệ thống                  → Settings root (7c43ae65)
   ├── Phòng khám & Chi nhánh         → 5f5f1093 (chứa toggle BHYT)
   ├── Vai trò & Phân quyền           → 1cb79779
   ├── Ca trực & Giờ làm              → 31b1b71d
   ├── Bảng giá dịch vụ               → 7c43ae65
   ├── BHYT (mức hưởng + DM)*         → 7ff9fe5b *(chỉ khi bhyt_enabled)
   ├── Tích hợp                       → 1d6fc539
   ├── Audit log                      → e7735b5a
   └── Bảo mật & Mã hoá               → b15b5015
─── Nhân sự ───
👥 Nhân viên                          → User CRUD (TODO)
🛡 Phân quyền                         → RBAC matrix (1cb79779)
─── Báo cáo ───
📊 Báo cáo & Thống kê                 → Reports root (d86ddd11)
   ├── Tổng quan                      → d86ddd11
   ├── Tài chính                      → e471372c
   ├── Lâm sàng                       → eb2d0661
   ├── Vận hành                       → 9431a116
   ├── Dược                           → 6b235c69
   └── BHYT*                          → 12334fcf *(chỉ khi bhyt_enabled)
─── Hệ thống ───
📜 Audit log                          → e7735b5a
🔔 Thông báo gửi đi                   → Notifications log (TODO)
```

### C.6 — Multi-role (BS + Quản trị)

Sidebar gộp UNION C.3 + C.5 với 2 group label tách rõ. Ví dụ user kiêm BS + Quản trị:

```
🏠 Tổng quan                          → Dashboard Multi-role (308fffe2)
─── Bác sĩ ───
👥 Bệnh nhân của tôi
🩺 Khám bệnh (EMR)
💊 Đơn thuốc đã kê
📋 Chỉ định CLS
📅 Lịch ca trực
─── Quản trị ───
🏥 Cấu hình hệ thống
👤 Nhân viên & Phân quyền
📊 Báo cáo
📜 Audit log
─── Cá nhân ───
👤 Profile
```

Multi-role chip ở avatar: `🏷️ Bác sĩ + Quản trị`. Greeting topbar: "Chào BS. An".

Xem chi tiết [MULTI_ROLE_UX.md](MULTI_ROLE_UX.md).

---

## D. Detail screen catalog

### D.1 — Auth & Onboarding (3 màn)

| ID | Màn | Stitch | Mục đích | Layout chính | Primary actions |
|---|---|---|---|---|---|
| D1.1 | Đăng nhập | `e98de272…` | Login email+password (no clinic_code) | Centered card 400px | "Đăng nhập" · "Quên MK" |
| D1.2 | Chọn phòng khám | TODO | Multi-clinic chooser | Card grid 320px each | "Vào PK" + checkbox set default |
| D1.3 | Quên mật khẩu | TODO (v2) | Reset password flow | Centered card | "Gửi link reset" |

### D.2 — Dashboards per role (6 màn)

Mỗi dashboard có cấu trúc chung: KPI cards row + 2-col widget grid + quick actions. Differ ở dữ liệu.

| ID | Màn | Stitch | KPI chính | Widget chính |
|---|---|---|---|---|
| D2.1 | Dashboard Lễ tân | `e8ec8790…` | BN trong queue · Lịch hẹn hôm nay · Hoá đơn pending · Thu hôm nay | Queue board · Lịch hôm nay · Pending payments |
| D2.2 | Dashboard Điều dưỡng | `41644527…` | BN chờ sinh hiệu · BN đã đo · Cảnh báo vital | Queue card "Chờ sinh hiệu" · Vital cảnh báo |
| D2.3 | Dashboard Bác sĩ | `ccc8e775…` | BN của tôi hôm nay · Đơn CLS chờ · Lượt khám tháng | My patients · AI gợi ý ca khó · Lịch trực |
| D2.4 | Dashboard Dược sĩ | `0d856e6c…` | Đơn chờ phát · Tồn kho cảnh báo · Sắp hết hạn | Pending dispense · Low stock · Expiry |
| D2.5 | Dashboard Quản trị | `e1e5cfeb…` | Doanh thu hôm nay · Lượt khám tháng · Cảnh báo HT | KPI doanh thu · Hoạt động NV · Cảnh báo |
| D2.6 | Dashboard Multi-role (BS+QT) | `308fffe2…` | KPI gộp 2 role với chip nguồn | 2 col widget song song theo role · Quick actions matrix mix |

**Common actions cho mọi dashboard**:
- Click KPI card → drill-down màn detail
- Click "Xem tất cả" mỗi widget → màn list đầy đủ
- Period switcher (hôm nay/tuần/tháng) ở topbar widget

---

### D.3 — Tiếp nhận & Bệnh nhân (4 màn)

#### D3.1 Tiếp nhận & Đăng ký BN

| Field | Giá trị |
|---|---|
| **Stitch** | `8c84c7e3270d4b729d83d1c5d4f60992` |
| **Path** | `/reception/register` |
| **Role** | Lễ tân, Quản trị |
| **Mục đích** | Tiếp nhận BN đến khám — search BN cũ hoặc tạo mới + tạo lượt khám |
| **Layout** | 2-col: form 60% trái + queue summary 40% phải |
| **Primary actions** | "Tìm BN" (autocomplete tên/SĐT/mã) · "+ Tạo BN mới" → modal · "Tạo lượt khám" → submit + push BN vào queue |
| **Field BHYT** | Hiện ô "Số thẻ BHYT" + button "Tra cứu VSS" CHỈ KHI `bhyt_enabled=true` |
| **Function refs** | PAT-001..014, VISIT-001..005, ACTION_FLOWS §1 |

#### D3.2 Phòng chờ / Queue board (TODO màn)

| Field | Giá trị |
|---|---|
| **Stitch** | (chưa có — Phase D) |
| **Path** | `/queue` |
| **Role** | Lễ tân, Điều dưỡng (read), Bác sĩ (read filter "of me") |
| **Layout** | Kanban board 5 cột theo state machine: Chờ tiếp nhận / Chờ sinh hiệu / Chờ BS / Đang khám / Chờ thanh toán |
| **Card** | Avatar BN + tên + mã + chip status + wait timer (đếm phút) + chip CC nếu cấp cứu |
| **Auto-update** | Polling mỗi 30s hoặc WebSocket push |
| **Color rule** | Wait time >30p → chip đỏ + alert ở dashboard |
| **Function refs** | APPT-* queue functions |

#### D3.3 Danh sách bệnh nhân (TODO màn)

| Field | Giá trị |
|---|---|
| **Stitch** | (chưa có — Phase D) |
| **Path** | `/patients` |
| **Role** | Lễ tân (R+W), Điều dưỡng (R+W), Bác sĩ (R+W), Quản trị |
| **Layout** | Table dày · filter bar sticky · pagination |
| **Columns** | Avatar · Mã · Tên · Tuổi · Giới · SĐT · Lần khám gần · Status · Actions |
| **Filter** | Tên/SĐT/mã/CCCD · Tuổi range · Giới · Lần khám range · Tag (mạn tính) · BHYT |
| **Actions per row** | Xem hồ sơ · Tạo lượt khám mới · Thêm note · Merge duplicate |
| **Function refs** | PAT-001..025 |

#### D3.4 Hồ sơ bệnh nhân chi tiết (TODO màn)

| Field | Giá trị |
|---|---|
| **Stitch** | (chưa có — Phase D) |
| **Path** | `/patients/:id` |
| **Layout** | 3-col: 280px summary trái + 720px tab nội dung + 380px right context |
| **Tabs** | Tổng quan · Lịch sử khám · Đơn thuốc · CLS · Hoá đơn · Tài liệu · Note · Audit |
| **Summary trái** | Avatar + tên + mã + tuổi/giới + chip "Mạn tính" + danh sách dị ứng + drugs đang dùng |
| **Right context** | "Liên hệ khẩn cấp" + "Lịch hẹn sắp tới" + "Tag" |
| **Function refs** | PAT-013..019 |

---

### D.4 — Lịch hẹn (1 màn)

#### D4.1 Lịch hẹn — Calendar tuần

| Field | Giá trị |
|---|---|
| **Stitch** | `2e1591c3fd534046932aaf2969fd571b` |
| **Path** | `/appointments` |
| **Role** | Lễ tân (R+W), Bác sĩ (R+W self), Điều dưỡng (R), Quản trị |
| **Layout** | Calendar grid 7 ngày × 24h (giờ ngày) + filter sidebar trái + actions topbar |
| **View toggles** | Tuần / Ngày / Tháng |
| **Cell** | Slot 30 phút · drag-drop appointment · color theo BS · chip status |
| **Modal** | Click empty cell → "Đặt hẹn mới" form · Click appointment → "Edit/Cancel" |
| **Filter** | BS · Phòng · Loại visit (mới/tái khám/CC) · Status |
| **Function refs** | APPT-001..014, ACTION_FLOWS §1 |

---

### D.5 — EMR / Khám bệnh (6 tab màn)

Tất cả 6 tab dùng layout chung:
- Patient banner sticky top (full width)
- Tab strip 6 tab với dot indicator (● filled / ○ chưa)
- 3-col content: 280px summary / 720px tab content / 380px right context
- Footer actions sticky bottom

Spec đầy đủ: [TAB_MATRIX.md §A](TAB_MATRIX.md#a-emr--chi-tiết-lượt-khám-6-tabs).

| Tab | Stitch | Tóm tắt nội dung |
|---|---|---|
| 1 — Sinh hiệu | `acef6986…` | Vital cluster 4-up + so sánh trước-sau + đánh giá nhanh + lịch sử HA |
| 2 — Khám LS (S.O.A.P) | `c12bf23a…` | Textarea S (lời kể BN) + accordion 8 nhóm O (khám thực thể) |
| 3 — Chẩn đoán | `fbb61911…` | ICD-10 autocomplete + S.O.A.P phần A+P + AI gợi ý |
| 4 — Kê đơn thuốc | `7e32e3c8…` | Search thuốc + 5-7 card thuốc + cảnh báo tương tác + **stock chip mỗi thuốc (RX-016)** |
| 5 — Cận lâm sàng | `b8f84b40…` | Chỉ định CLS + bảng đã chỉ định + kết quả từ lượt trước |
| 6 — Tóm tắt & Hoàn tất | `41e3a324…` | Read-only summary + tổng chi phí + lời dặn + tái khám + nút "Hoàn tất khám" emerald |

---

### D.6 — Dược / Kho thuốc (5 màn)

#### D6.1 Cấp phát đơn thuốc

| Field | Giá trị |
|---|---|
| **Stitch** | `434d73b9387947328139f56dfad5309f` |
| **Path** | `/pharmacy/dispense` |
| **Role** | Dược sĩ |
| **Layout** | Table queue đơn pending + drawer phải khi click row |
| **Columns** | Số RX · BN · BS kê · Số thuốc · Tổng tiền · Status · Wait time · Actions |
| **Drawer detail** | Chi tiết đơn + chọn lô FEFO + xác nhận thuốc + in nhãn |
| **Actions** | Phát đơn · Phát 1 phần · Reject (out of stock) · In lại |
| **SoD enforce** | Nếu đơn do user X kê (User RBAC-016) → nút "Phát" disabled |
| **Function refs** | PHRM-001..012 |

#### D6.2 Danh mục thuốc (TODO màn)

| Field | Giá trị |
|---|---|
| **Stitch** | (chưa có — Phase D) |
| **Path** | `/pharmacy/catalog` |
| **Layout** | Table · filter bar · CRUD inline + drawer detail |
| **Columns** | Mã · Tên thương mại · Hoạt chất · Hàm lượng · Đơn vị · Stock · Cảnh báo · DM BHYT |
| **Filter** | Nhóm · Phân loại · DM BHYT · Stock status · Sắp HSD |
| **Actions** | Add · Edit · Archive · Bulk import CSV · Export |
| **Function refs** | MED-001..018 |

#### D6.3 Nhập kho (PO)

| Field | Giá trị |
|---|---|
| **Stitch** | (chưa có — Phase D) |
| **Path** | `/pharmacy/po` |
| **Layout** | Form nhập + table line items |
| **Form** | Supplier · Số PO · Ngày nhập · Chứng từ |
| **Line items** | Thuốc + lô + HSD + qty + giá vốn |
| **Action** | "Lưu nháp" · "Xác nhận nhập kho" → cập nhật stock + audit |
| **Function refs** | MED-009 |

#### D6.4 Kiểm kê (Stock count)

| Field | Giá trị |
|---|---|
| **Stitch** | (chưa có — Phase D) |
| **Path** | `/pharmacy/count` |
| **Layout** | Wizard 3 bước: chọn category · đếm thực tế · adjustment |
| **Actions** | Nhập số đếm · So sánh · Submit adjustment (cần admin approve) |
| **Function refs** | MED-010, MED-011 |

#### D6.5 Xử lý hết hạn

| Field | Giá trị |
|---|---|
| **Stitch** | (chưa có — Phase D) |
| **Path** | `/pharmacy/expiry` |
| **Layout** | Table thuốc sắp hết hạn (30/60/90 ngày) + actions |
| **Actions** | Đánh dấu disposal · Đề xuất giảm giá · Trả NCC · In tem cảnh báo |
| **Function refs** | MED-007, MED-008 |

---

### D.7 — Thanh toán & Hoá đơn (3 màn)

#### D7.1 Thanh toán hoá đơn

| Field | Giá trị |
|---|---|
| **Stitch** | `43971b42ba2b4043a89e8aa32261ec16` |
| **Path** | `/billing/invoice/:id` |
| **Role** | Lễ tân, Quản trị |
| **Layout** | Header BN + table line items + section thanh toán bên phải |
| **Line items** | DV khám · CLS · Đơn thuốc · Discount · VAT |
| **Section BHYT** | Hiện CHỈ KHI `bhyt_enabled` — tách BHYT chi trả vs BN trả |
| **Multi-payment** | Tiền mặt · CK · POS · QR — nhiều phương thức cùng đơn |
| **Actions** | Print · Email PDF · Void · Refund · Print POS receipt |
| **Function refs** | BILL-001..019, ACTION_FLOWS §6 |

#### D7.2 Lịch sử hoá đơn (TODO màn)

| Field | Giá trị |
|---|---|
| **Stitch** | (chưa có — Phase D) |
| **Path** | `/billing/history` |
| **Layout** | Table · filter (date/status/method) · pagination |
| **Columns** | Số INV · BN · Ngày · Số tiền · Phương thức · Status · Actions |
| **Filter** | Date range · Status (paid/pending/void/refund) · Method · BS · Range tiền |

#### D7.3 Công nợ BN (TODO màn)

| Field | Giá trị |
|---|---|
| **Stitch** | (chưa có — Phase D) |
| **Path** | `/billing/ar` |
| **Layout** | Table BN có công nợ + aging buckets (0-30/30-60/60-90/>90 ngày) |
| **Actions** | Gửi nhắc nhở · Ghi nhận thanh toán · Write-off |

---

### D.8 — Cấu hình hệ thống (8 màn)

Mỗi section dùng layout chung: Sub-nav 240px (settings tree) + content right.

Spec đầy đủ: [TAB_MATRIX.md §B](TAB_MATRIX.md#b-cấu-hình-hệ-thống-8-sections).

| Section | Stitch | Tab strip | Đặc trưng |
|---|---|---|---|
| Phòng khám & Chi nhánh | `5f5f1093…` | Thông tin · Chi nhánh · Khoa · Phòng | **Chứa toggle BHYT bật/tắt** ở Tab Thông tin |
| Vai trò & Phân quyền | `1cb79779…` | Vai trò · Quyền · User · Audit | RBAC matrix 38 perms × 5 roles + override |
| Ca trực & Giờ làm | `31b1b71d…` | Mẫu ca · Lịch tuần · Lịch tháng · Off | Drag-drop assignment · conflict detection |
| Bảng giá DV | `7c43ae65…` | (single page) | Cột BHYT % ẩn khi `bhyt_enabled=false` |
| BHYT* | `7ff9fe5b…` | Mức hưởng · DM · Lý do từ chối · Sync | *Section ẩn khi `bhyt_enabled=false` |
| Tích hợp | `1d6fc539…` | VSS · HL7 · DICOM · SMS · Webhook · Logs | Tab VSS disabled khi `bhyt_enabled=false` |
| Audit log | `e7735b5a…` | (single page) | Filter + table + drawer diff JSON |
| Bảo mật & Mã hoá | `b15b5015…` | (sections stack) | Compliance checklist HIPAA + Nghị định 13 |

---

### D.9 — Báo cáo & Thống kê (6 màn)

Layout chung: Filter bar sticky + tab strip + KPI cards + charts grid + tables.

Spec đầy đủ: [TAB_MATRIX.md §C](TAB_MATRIX.md#c-báo-cáo--thống-kê-6-tabs).

| Tab | Stitch | Tóm tắt |
|---|---|---|
| Tổng quan | `d86ddd11…` | 4 KPI + combo chart 12 tháng + donut nguồn BN + top 10 DV |
| Tài chính | `e471372c…` | Doanh thu · Cash flow · BHYT vs Tự trả · P&L mini |
| Lâm sàng | `eb2d0661…` | Top 20 ICD-10 · Pyramid age × giới · Outcome metrics chronic |
| Vận hành | `9431a116…` | Heatmap wait time · Funnel BN journey · Bottleneck |
| Dược | `6b235c69…` | Top 20 thuốc · Inventory aging · Expiry curve · Reorder |
| BHYT* | `12334fcf…` | *Tab ẩn khi `bhyt_enabled=false`. Funnel duyệt · Top reject reason |

---

### D.10 — Profile & Cá nhân (3 màn)

#### D10.1 Profile cá nhân (TODO màn)

| Field | Giá trị |
|---|---|
| **Stitch** | (chưa có — Phase D) |
| **Path** | `/profile` |
| **Layout** | 2-col: avatar+thông tin trái + tab settings phải |
| **Tabs** | Thông tin · Mật khẩu · Phòng khám của tôi · Phiên · Thông báo |
| **Tab Thông tin** | Avatar upload · Họ tên · SĐT · Email (read-only) · CCCD |
| **Tab Mật khẩu** | Form 3 trường (current/new/confirm) + complexity hint |
| **Tab Phòng khám của tôi** | List PK user có quyền + role mỗi PK + radio "Mặc định" + button "Rời PK" |
| **Tab Phiên** | List session đang active (device + IP + last seen) + button "Đăng xuất" mỗi session |
| **Tab Thông báo** | Toggle email/SMS/in-app per loại notification |
| **Function refs** | AUTH-004 (đổi MK), AUTH-019 (default clinic), AUTH-018 (multi-clinic), NOTI-* |

#### D10.2 Notifications panel (drawer)

| Field | Giá trị |
|---|---|
| **Stitch** | (chưa có — Phase D) |
| **Trigger** | Click 🔔 topbar → popover 480px right |
| **Layout** | Header (filter All/Unread) + list 10 noti + footer "Xem tất cả" link |
| **Item** | Avatar source + title + body 1-line + relative time + chip type · click navigate |
| **Function refs** | NOTI-001..010 |

#### D10.3 Notifications full page (`/notifications`)

| Field | Giá trị |
|---|---|
| **Stitch** | (chưa có — Phase D) |
| **Path** | `/notifications` |
| **Layout** | Table dày + filter (date/type/source) + bulk actions |
| **Bulk actions** | Mark read · Delete · Archive |

---

## E. Modal & secondary screens

### E.1 — Cmd+K Quick search palette (modal)

```
┌──────────────────────────────────────────────────────────────┐
│  ⌘K  [/bn ha vy                                          ]   │ ← input
│  ──────────────────────────────────────────────────────────  │
│  TAB: 🔍 Tất cả · 👥 Bệnh nhân · 💊 Thuốc · 📋 Tính năng     │
│  ──────────────────────────────────────────────────────────  │
│  👥 Lê Hà Vy · 45 · Nữ · BN-2026-00427 · "Đang khám"        │
│  👥 Hà Văn Vỹ · 32 · Nam · BN-2026-00198 · 28/03/2026       │
│  👥 Nguyễn Hà Vy · 8 · Nữ · BN-2026-00532 · 22/04/2026      │
│  ──────────────────────────────────────────────────────────  │
│  ↑↓ Chọn · ↵ Mở · Esc Đóng · / Filter                        │
└──────────────────────────────────────────────────────────────┘
```

| Field | Giá trị |
|---|---|
| **Trigger** | Ctrl+K / ⌘K bất cứ màn nào |
| **Stitch** | TODO Phase D |
| **Modes** | Default (feature search) · `/bn ` (BN) · `/thuoc ` (thuốc) · `/inv ` (hoá đơn) · `/rx ` (đơn) · `/lk ` (lượt khám) |
| **Keyboard** | ↑↓ navigate · Enter open · Esc close · `/` switch mode |
| **Performance** | Debounce 200ms · BE response p95 <300ms (NFR-019) |
| **Function refs** | NAV-001..005 |

---

### E.2 — Clinic switcher dropdown (popover)

```
┌─ Clinic switcher dropdown 280px ──────────┐
│ [🔍 Tìm phòng khám...]                    │
│ ──────────────────────────────────────── │
│ ✓ 🏥 Hồng Đức Trung Tâm    [Hiện tại]    │
│   142 Lê Lai, Q1                          │
│   🏷️ Bác sĩ + Quản trị                   │
│ ──────────────────────────────────────── │
│   🏥 Đa khoa Mai Lan                      │
│   56 NTMK, Q3                             │
│   🏷️ Bác sĩ                               │
│ ──────────────────────────────────────── │
│   🏥 Phòng khám tư của tôi                │
│   88 Trần Phú, Q5                         │
│   🏷️ Owner                                │
│ ──────────────────────────────────────── │
│ [⚙️ Cấu hình clinic]  [↗ Đăng xuất]      │
└────────────────────────────────────────────┘
```

| Field | Giá trị |
|---|---|
| **Trigger** | Click `🏥 [Tên PK ▾]` ở topbar |
| **Visibility** | Ẩn nếu user chỉ có 1 PK |
| **Action click PK** | POST `/auth/switch-clinic` → JWT mới + clear cache (xem AUTH-021) |
| **Function refs** | NAV-002, AUTH-021 |

---

### E.3 — Modals các loại

| Modal | Trigger | Width | Function refs |
|---|---|---|---|
| Đăng ký BN mới | Reception "+ Tạo BN" | 800px | PAT-001 |
| Đặt hẹn mới | Lịch hẹn click empty cell | 600px | APPT-001 |
| Đổi/Hủy hẹn | Lịch hẹn click appt | 500px | APPT-005 |
| Confirm hoàn tất khám | EMR Tab 6 | 480px | VISIT-005 |
| Confirm void hoá đơn | Billing actions | 480px | BILL-014 |
| Gán role cho user | Settings User detail | 600px | RBAC-004, RBAC-005 |
| Tạo PO nhập kho | Pharmacy "+Nhập kho" | 800px | MED-009 |
| Welcome onboarding | Lần đầu login | 720px | AUTH-* |
| Soft logout (mất role) | Backend trả 403 | 480px | MULTI_ROLE_UX §5.2 |

---

## F. Tổng kết visibility theo role

Bảng tóm tắt số màn hiển thị trên sidebar mỗi role (tính cả Common):

| Role | Số menu top-level | Số sub-menu | Tổng màn truy cập |
|---|:---:|:---:|:---:|
| Lễ tân | 6 | 4 | 10 |
| Điều dưỡng | 5 | 2 | 7 |
| Bác sĩ | 6 | 8 | 14 |
| Dược sĩ | 6 | 4 | 10 |
| Quản trị | 7 | 22 | 29 |
| Multi-role (BS+QT) | 12 | 30 | 42 (UNION, có overlap) |

**Quy tắc đếm**:
- Sub-menu = tab/section trong 1 màn (vd EMR có 6 tab tính 6 sub-menu)
- Multi-role = UNION (deduplicate Tổng quan + Profile)
- KHÔNG tính modal/drawer

---

## G. Việc cần làm tiếp (Phase D — sinh thêm Stitch)

Sau khi Phase B+C đã sinh đủ 18 màn từ TASK-027, các màn dưới đây cần sinh trong Phase D:

| Nhóm | Số màn | Priority |
|---|:---:|---|
| Auth pre-login bổ sung (Chọn PK + Forgot pass) | 2 | High |
| Patient master list + detail (Tổng quan + 7 tab) | 2 | High |
| Queue board kanban | 1 | High |
| Patient profile detail (8 tabs) | 1 | High |
| Pharmacy 4 màn (catalog + PO + count + expiry) | 4 | Medium |
| Billing 2 màn (history + AR) | 2 | Medium |
| Profile 1 màn (multi-tab) | 1 | High |
| Notifications full page | 1 | Medium |
| Cmd+K palette modal | 1 | High |
| Clinic switcher popover | 1 | High |

**Tổng Phase D**: ~16 màn × ~5 phút sinh Stitch = ~80 phút wall-clock.

→ Sau Phase D: 32 (B+C) + 16 (D) = **48 unique screens** trên Stitch project.
