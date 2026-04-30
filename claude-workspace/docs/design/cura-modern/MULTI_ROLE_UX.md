# Cura — UX cho User kiêm nhiều vai trò

**Cập nhật**: 2026-04-30 (Phase B done — Stitch screen `308fffe2883f4c1cad7e7441120158b9`)

---

## 1. Vấn đề thực tế ở phòng khám VN

Phòng khám tư hoặc đa khoa nhỏ ở VN **rất hiếm khi mỗi người 1 vai trò**. Các tổ hợp phổ biến:

| Tổ hợp role thực tế | Ai làm? | % phòng khám gặp |
|---|---|---|
| **Lễ tân + Thanh toán + Chăm sóc khách hàng** | Một nhân viên kiêm 3 việc | ~85% |
| **Bác sĩ + Trưởng khoa (Quản trị 1 phần)** | BS chính / chủ phòng khám | ~70% |
| **Điều dưỡng + Tiếp nhận** (PK nhỏ) | ĐD vào ca khi vắng lễ tân | ~60% |
| **Bác sĩ + Chủ phòng khám (Full Quản trị)** | Chủ sở hữu PK nhỏ | ~50% |
| **Dược sĩ + Kho + Mua hàng** | DS kiêm nhập kho | ~80% |
| **Lễ tân + Điều dưỡng tiền khám** | PK 1 người 2 ca | ~30% |
| **Bác sĩ + Dược sĩ** (PK rất nhỏ) | BS đa khoa kiêm bán thuốc | ~15% |

→ Backend Cura đã hỗ trợ **multi-role per user** + **per-user grant/deny override** (`PROJECT.md`, TASK-004 RBAC). UI cần thể hiện tốt việc này.

---

## 2. Pattern khuyến nghị: **Merge Sidebar** (gộp sidebar)

### Nguyên tắc cốt lõi

> **Một sidebar duy nhất hiển thị UNION tất cả module mà user có quyền truy cập.**
> User KHÔNG cần "chuyển vai trò" — toàn bộ workspace là của họ.

### Lý do chọn cách này (so với role-switcher)

| Tiêu chí | Merge Sidebar ✓ | Role Switcher ✗ |
|---|---|---|
| Số click để chuyển task | 1 (click module) | 3 (click switcher → chọn role → click module) |
| Phù hợp khám chữa bệnh | ✓ Bác sĩ vừa khám vừa duyệt thuốc liền mạch | ✗ Cắt context giữa khám và duyệt |
| Discoverability | ✓ Thấy hết module mình có quyền | ✗ Module ở role kia bị ẩn, dễ quên |
| Phù hợp PK đa khoa nhỏ VN | ✓ ĐÚNG NGỮ CẢNH | ✗ Tạo cảm giác "cồng kềnh" |
| Lỗi phổ biến tránh được | Không có vụ "tôi tưởng đã đăng nhập role kia" | Hay xảy ra |

**Trường hợp ngoại lệ** (dùng role-switcher): khi 2 role có **mục đích trái ngược** (vd: "Khám" vs "Audit chính BS đó") — không phải case của Cura.

### Anatomy sidebar khi user kiêm nhiều role

```
┌─ Sidebar (240px) ──────────────────────┐
│  [Logo Cura]                            │
│                                         │
│  🏠  Tổng quan                          │ ← Dashboard Multi-role (gộp KPI cả 2 role)
│                                         │
│  ─── Bác sĩ ───────────────             │ ← divider + group label
│  👥  Bệnh nhân của tôi                  │
│  🩺  Khám bệnh (EMR)                    │
│  💊  Đơn thuốc                          │
│  📋  CLS / Cận lâm sàng                 │
│  📅  Lịch ca trực                       │
│                                         │
│  ─── Quản trị ─────────────             │ ← group 2
│  🏥  Phòng khám                         │
│  👤  Nhân viên & Phân quyền             │
│  ⚙️   Cấu hình hệ thống                  │
│  📊  Báo cáo                            │
│  📜  Audit log                          │
│                                         │
│  ─────────────                          │
│                                         │
│  [Avatar 40px]                          │
│  BS. Nguyễn Hoàng An                    │
│  🏷️ Bác sĩ + Quản trị                   │ ← multi-role chip
│                                         │
└─────────────────────────────────────────┘
```

**Chi tiết visual**:

1. **Group label** (uppercase 11px, text-muted): tách module theo role gốc — giúp user mental-map module với role
2. **Multi-role chip ở avatar**: hiển thị tất cả role, max 3 dòng. Nếu >3, hiển thị "+N":
   ```
   🏷️ Bác sĩ · Trưởng khoa Nội · Quản trị
   ```
   hoặc
   ```
   🏷️ Bác sĩ + 2 vai trò ▾
   ```
   (click ▾ → tooltip xổ xuống full list + ngày được cấp)

3. **Search trong sidebar** (Ctrl+K hoặc cmd-palette): khi user gõ "thuốc" → cả "Đơn thuốc" (BS) và "Kho thuốc" (DS, nếu user kiêm) đều hiện ra

4. **Quyền theo override**: nếu user có override deny trên 1 module mà role mặc định cho phép → module đó **ẩn hoàn toàn** khỏi sidebar (không nên show disabled — gây nhầm lẫn)

5. **Quyền partial (R/P)**: vẫn hiện trong sidebar nhưng có **icon nhỏ** bên cạnh label:
   - `🩺 Khám bệnh 👁` (read-only, hover tooltip "Bạn chỉ có quyền xem, không thể tạo lượt khám mới")
   - `📊 Báo cáo ⚪` (partial — chỉ thấy 3/6 tab)

---

## 3. Visual indicator cho user multi-role

### 3.1 Avatar badge layered

```
┌─ Avatar block trong sidebar ────────┐
│                                       │
│        [Avatar 40px tròn]             │
│              ⌐⌐                       │
│              └─ badge "+2"            │ ← stack badges nếu nhiều role
│                                       │
│        BS. Nguyễn Hoàng An            │
│        nguyenhoangan@hongduc.vn       │
│        ─────                          │
│  🏷️ Bác sĩ Nội · Trưởng khoa · Quản trị│
│                                       │
│  [Đăng xuất] [Cài đặt]                │
└───────────────────────────────────────┘
```

### 3.2 Topbar — context indicator

Topbar **không có role switcher** (vì merge sidebar), nhưng có:

```
[<] Trang chủ / Khám bệnh / Lê Hà Vy        ⌘K Tìm...      [🔔] [PK Hồng Đức ▾] [BS. An 🏷️ +2]
```

- Avatar topbar có badge nhỏ "+2" → hover thấy full list role
- Nếu user kiêm nhiều **chi nhánh phòng khám** thì có thêm `[PK Hồng Đức ▾]` để switch chi nhánh

### 3.3 Action với role gốc

Khi user thực hiện action có ghi log audit, hệ thống tự động ghi:
```
2026-04-30 10:34 · An (BS+QT) · Sửa giá DV022 từ ₫350k → ₫400k · Vai trò áp dụng: Quản trị
```

→ Audit log nói rõ "vai trò áp dụng" để truy vết khi có sự cố.

---

## 4. Dashboard multi-role — cách design

**Stitch screen**: `308fffe2883f4c1cad7e7441120158b9` (BS + Quản trị — case representative cho merge sidebar)

### Nguyên tắc: **KHÔNG ép user xem 2 dashboard riêng biệt**

Một dashboard hợp nhất với:

#### Top section — KPI gộp (4-6 stat cards)
Trộn lẫn KPI từ cả 2 role, ưu tiên những thứ user thường check:

```
┌──────────┬──────────┬──────────┬──────────┐
│ BN đang  │ Đơn CLS  │ Doanh thu│ Cảnh báo │
│ khám: 1  │ chờ: 4   │ tuần:    │ hệ thống:│
│ (BS)     │ (BS)     │ ₫85.4M   │ 3        │
│          │          │ (QT)     │ (QT)     │
└──────────┴──────────┴──────────┴──────────┘
```

→ Mỗi card có **chip nhỏ** "(BS)" hoặc "(QT)" để user biết KPI đó thuộc role nào.

#### Middle section — 2 widget song song

| Widget BS                   | Widget QT                    |
|-----------------------------|------------------------------|
| Bệnh nhân của tôi (8 chờ)   | KPI doanh thu hôm nay        |
| Chart sinh hiệu BN cấp cứu  | Trạng thái hệ thống          |
| Lịch trực tuần              | Hoạt động nhân viên          |
| AI gợi ý ca khó             | Cảnh báo tồn kho             |

→ Layout grid 2 cột thay vì 1 cột, mỗi cột header có icon role.

#### Bottom — Quick actions matrix
```
┌─────────────────────────────────────────────┐
│  Thao tác nhanh                              │
├─────────┬─────────┬─────────┬───────────────┤
│ 🩺 Vào   │ 💊 Duyệt │ 📊 Xem  │ ⚙️ Cấu hình  │
│ phòng KB │ đơn CLS  │ báo cáo │ hệ thống     │
└─────────┴─────────┴─────────┴───────────────┘
```
6-8 nút action, **trộn role**, sắp xếp theo **tần suất sử dụng** (track theo user behavior, không cố định theo role).

---

## 5. Conflict & edge cases

### 5.1 Khi 2 role có quyền XUNG ĐỘT trên cùng resource

VD: BS+DS user. BS có quyền tạo đơn thuốc. DS có quyền duyệt đơn thuốc. **Có nên cho user duyệt đơn của chính mình không?**

**Quyết định**: KHÔNG. Hệ thống enforce **separation of duties** trên audit-critical action:
- Đơn thuốc do user X kê → user X bị disabled nút "Phát đơn" (UI hiện tooltip "Không thể tự duyệt đơn của chính mình — cần DS khác")
- Cấu hình giá → user X tạo đề xuất; chỉ user khác mới approve

### 5.2 Khi user mất role giữa session

VD: Quản trị thu hồi role "Bác sĩ" của user An lúc 14:00. An đang khám BN.

**Pattern**:
- JWT cache 15 phút (theo TASK-004) → an ninh có cap
- Khi An reload trang hoặc đổi route → backend trả 403 → frontend hiển thị **modal soft logout**:
  ```
  ⚠ Quyền truy cập đã thay đổi
  Vai trò "Bác sĩ" của bạn vừa được thu hồi.
  Phiên làm việc hiện tại sẽ kết thúc trong 30 giây.
  Vui lòng lưu công việc đang dở.
  
  [Lưu nháp ngay] [Đăng xuất]
  ```
- Nếu An đang ở giữa lượt khám → auto-save draft + redirect về Dashboard role còn lại
- Nếu An mất TẤT CẢ role → redirect về Login

### 5.3 Onboarding khi cấp role mới

VD: An đang là Bác sĩ. Quản trị cấp thêm role "Trưởng khoa" lúc 09:00.

**UX**:
- Lần login tiếp theo → modal welcome 1 lần:
  ```
  🎉 Bạn được cấp thêm vai trò: Trưởng khoa Nội
  
  Bạn vừa có thêm các quyền:
  • Xem báo cáo lâm sàng của khoa
  • Duyệt nghỉ phép cho điều dưỡng trong khoa
  • Phân công ca trực
  
  Mục mới đã được thêm vào sidebar ──→
  
  [Tour 30s] [Bỏ qua]
  ```
- Trong sidebar, các module mới có **dot indicator nhỏ "MỚI"** trong 7 ngày đầu

### 5.4 Khi sidebar quá dài (user 3-4 role)

- Sidebar có **collapsible group**: click vào group label → collapse cả group
- Pin: user pin module hay dùng lên top, bỏ qua group
- Recent: khu vực "Truy cập gần đây" 3-5 mục cuối, sticky top-right

---

## 6. Khi NÀO nên đổi sang Role Switcher?

Chỉ khi đáp ứng đủ **cả 3 điều kiện**:

1. ✅ User có ≥4 role
2. ✅ Có ít nhất 2 role với **ngữ cảnh hoàn toàn tách biệt** (vd: "phòng khám VN" vs "chi nhánh ở Mỹ")
3. ✅ User report là sidebar quá dài, scrollbar nhiều, gây mất tập trung

→ Hiện chưa có case này trong Cura. Có thể bật flag `multi_role_switcher_v2` về sau nếu phát sinh.

---

## 7. Implementation hint cho FE (clinic-cms-web)

### State (zustand)
```ts
interface UserStore {
  user: User
  roles: Role[]                          // multi
  effectivePermissions: Set<string>       // computed = role perms ∪ grants − denies
  primaryRole: Role                       // dùng cho greeting "Chào BS. An"
  
  hasPermission(code: string): boolean
  hasAnyRole(codes: string[]): boolean
}
```

### Sidebar render
```tsx
const groups = useMemo(() => {
  const visible = MODULES.filter(m =>
    m.requiredPermissions.some(p => store.effectivePermissions.has(p))
  )
  return groupBy(visible, m => m.primaryRoleGroup)  // "doctor" | "admin" | ...
}, [store.effectivePermissions])

return (
  <Sidebar>
    {Object.entries(groups).map(([role, modules]) => (
      <SidebarGroup key={role} label={ROLE_LABEL[role]}>
        {modules.map(m => <SidebarItem key={m.code} {...m} />)}
      </SidebarGroup>
    ))}
    <SidebarFooter>
      <UserAvatar />
      <MultiRoleChip roles={store.roles} />
    </SidebarFooter>
  </Sidebar>
)
```

### Backend contract
JWT payload (TASK-004) đã include cả role list + effective perms:
```json
{
  "sub": "user_uuid",
  "clinic_id": "clinic_uuid",
  "roles": ["doctor", "admin"],
  "perms": ["patient.read", "emr.write", "config.write", ...]
}
```

→ FE chỉ cần `roles.length > 1` để bật multi-role mode. Không cần API mới.
