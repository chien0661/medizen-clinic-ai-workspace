# MediZen — Modern · Sitemap toàn hệ thống

**Project Stitch**: https://stitch.withgoogle.com/projects/5572301228665717471
**Cập nhật**: 2026-04-30 (Phase B + C done — 32 màn)

---

## 1. Sơ đồ module (cây tổ chức)

```
MediZen — Modern
│
├── 🔐 Auth
│   ├── Đăng nhập (e98de272)        ← role-aware redirect
│   ├── Quên mật khẩu                ← TODO
│   ├── MFA setup / verify           ← TODO
│   └── Đổi mật khẩu                 ← thuộc Profile
│
├── 🏠 Dashboard (per-role)
│   ├── Dashboard Lễ tân (e8ec8790)
│   ├── Dashboard Điều dưỡng (41644527)
│   ├── Dashboard Bác sĩ (ccc8e775)
│   ├── Dashboard Dược sĩ (0d856e6c)
│   ├── Dashboard Quản trị (e1e5cfeb)
│   └── Dashboard Multi-role (Phase B — sẽ sinh)
│
├── 👥 Tiếp nhận & Bệnh nhân
│   ├── Phòng chờ / Hàng đợi          ← Lễ tân, Điều dưỡng
│   ├── Tiếp nhận & Đăng ký (8c84c7e3)
│   ├── Danh sách bệnh nhân           ← TODO (master list)
│   ├── Hồ sơ bệnh nhân (Patient profile) ← TODO
│   └── Đăng ký BN mới (modal)
│
├── 📅 Lịch hẹn
│   ├── Lịch hẹn — tuần view (2e1591c3)
│   ├── Lịch hẹn — ngày/tháng         ← variant
│   ├── Đặt hẹn mới (modal)
│   ├── Đổi giờ / Hủy hẹn (modal)
│   └── Lịch ca trực bác sĩ           ← TODO
│
├── 🩺 Khám bệnh (EMR) — Bác sĩ
│   └── Chi tiết lượt khám (fbb61911) — chứa 6 TAB:
│       ├── ① Sinh hiệu               ← Phase C
│       ├── ② Khám lâm sàng (S.O.A.P) ← Phase C
│       ├── ③ Chẩn đoán (ICD-10)      ✓ đã sinh — đây là default
│       ├── ④ Kê đơn thuốc            ← Phase C
│       ├── ⑤ Cận lâm sàng (CLS)      ← Phase C
│       └── ⑥ Tóm tắt & Hoàn tất      ← Phase C
│
├── 💊 Dược / Kho thuốc
│   ├── Cấp phát đơn thuốc (434d73b9) — tab "Cấp phát hôm nay"
│   ├── Danh mục thuốc                ← tab khác cùng màn
│   ├── Nhập kho                       ← tab khác
│   ├── Kiểm kê                        ← tab khác
│   └── Báo cáo dược                   ← tab khác (link sang Reports)
│
├── 💰 Thanh toán & Hoá đơn
│   ├── Thanh toán hoá đơn (43971b42)
│   ├── Lịch sử hoá đơn               ← TODO
│   ├── Công nợ BN                     ← TODO
│   └── Hoàn tiền / Điều chỉnh        ← TODO
│
├── 📊 Báo cáo & Thống kê
│   └── Báo cáo (d86ddd11) — chứa 6 TAB:
│       ├── ① Tổng quan                ✓ đã sinh
│       ├── ② Tài chính                ← Phase C
│       ├── ③ Lâm sàng                 ← Phase C
│       ├── ④ Vận hành                 ← Phase C
│       ├── ⑤ Dược                     ← Phase C
│       └── ⑥ BHYT                     ← Phase C
│
├── ⚙️ Cấu hình hệ thống — Quản trị
│   └── Cấu hình (7c43ae65) — chứa 8 SECTION:
│       ├── Phòng khám                 ← chứa toggle "Cho phép BHYT" (default OFF)
│       ├── Vai trò & Phân quyền       ← RBAC matrix
│       ├── Ca trực & Giờ làm
│       ├── Bảng giá dịch vụ
│       ├── BHYT (mức hưởng + DM)      ← ⚠ chỉ hiện khi bhyt_enabled = true
│       ├── Tích hợp (VSS/HL7/DICOM)   ← tab VSS chỉ hiện khi bhyt_enabled = true
│       ├── Audit log
│       └── Bảo mật & Mã hóa
│
└── 👤 Profile cá nhân
    ├── Thông tin cá nhân
    ├── Đổi mật khẩu
    ├── Cài đặt thông báo
    ├── Phiên đăng nhập đang hoạt động
    └── Đăng xuất
```

---

## 2. Ma trận hiển thị module theo vai trò

MediZen backend (`PROJECT.md`) định nghĩa **5 system roles + 38 permissions**. Một user có thể giữ **nhiều role** đồng thời + có **per-user grant/deny override**. Ma trận dưới đây là default — override sẽ được áp dụng sau cùng.

| Module                        | Lễ tân | Điều dưỡng | Bác sĩ | Dược sĩ | Quản trị |
|-------------------------------|:------:|:----------:|:------:|:-------:|:--------:|
| Đăng nhập / Auth              |   ✓    |     ✓      |   ✓    |    ✓    |    ✓     |
| Dashboard (riêng theo role)   |   ✓    |     ✓      |   ✓    |    ✓    |    ✓     |
| **Tiếp nhận BN**              |   ✓    |     —      |   —    |    —    |    ✓     |
| Phòng chờ / Hàng đợi          |   ✓    |     ✓      |   ✓ (R)|    —    |    ✓     |
| Hồ sơ bệnh nhân               |   ✓ (R)|     ✓      |   ✓    |    —    |    ✓     |
| Đăng ký BN mới                |   ✓    |     —      |   —    |    —    |    ✓     |
| **Lịch hẹn**                  |   ✓    |     ✓ (R)  |   ✓    |    —    |    ✓     |
| Đặt hẹn / Đổi giờ             |   ✓    |     —      |   ✓    |    —    |    ✓     |
| Lịch ca trực                  |   —    |     ✓      |   ✓    |    ✓    |    ✓     |
| **Sinh hiệu (đo / nhập)**     |   —    |     ✓      |   ✓ (R)|    —    |    ✓     |
| **EMR — Khám bệnh**           |   —    |     ✓ (P)  |   ✓    |    —    |    ✓ (R) |
| Kê đơn thuốc                  |   —    |     —      |   ✓    |    ✓ (R)|    ✓ (R) |
| Chỉ định CLS                  |   —    |     —      |   ✓    |    —    |    ✓ (R) |
| **Cấp phát thuốc**            |   —    |     —      |   —    |    ✓    |    ✓     |
| Quản lý kho thuốc             |   —    |     —      |   —    |    ✓    |    ✓     |
| Nhập kho / Kiểm kê            |   —    |     —      |   —    |    ✓    |    ✓     |
| **Thanh toán hoá đơn**        |   ✓    |     —      |   —    |    —    |    ✓     |
| Hoàn tiền / Điều chỉnh        |   —    |     —      |   —    |    —    |    ✓     |
| **Báo cáo — Tổng quan**       |   ✓ (R)|     —      |   ✓ (R)|    —    |    ✓     |
| Báo cáo — Tài chính           |   —    |     —      |   —    |    —    |    ✓     |
| Báo cáo — Lâm sàng            |   —    |     —      |   ✓ (R)|    —    |    ✓     |
| Báo cáo — Dược                |   —    |     —      |   —    |    ✓    |    ✓     |
| **Cấu hình — Bảng giá**       |   —    |     —      |   —    |    —    |    ✓     |
| Cấu hình — Vai trò & Quyền    |   —    |     —      |   —    |    —    |    ✓     |
| Cấu hình — Tích hợp           |   —    |     —      |   —    |    —    |    ✓     |
| Audit log                     |   —    |     —      |   —    |    —    |    ✓     |

**Chú thích**:
- **✓** = full access (read + write)
- **✓ (R)** = read-only
- **✓ (P)** = partial — chỉ một số field/section trong module
- **—** = không thấy module trên sidebar

**Override examples**:
- Một bác sĩ có thể được cấp thêm quyền `payment.read` → thấy tab "Hoá đơn" trong patient profile
- Một lễ tân có thể bị thu hồi quyền `appointment.cancel` → nút "Hủy hẹn" disabled, hover hiển thị "Bạn không có quyền — liên hệ quản trị"

**Feature flag BHYT** (`clinic.bhyt_enabled`, default OFF):
- Toggle ở Cấu hình → Phòng khám → Tab Thông tin
- Khi OFF: ẩn module "BHYT (mức hưởng + DM)" + tab "VSS" trong Tích hợp + tab "Báo cáo BHYT" + cột BHYT trong Bảng giá DV + ô BHYT khi tiếp nhận + dòng BHYT trong đơn thuốc/CLS/hoá đơn — bất kể role có quyền `bhyt.*` hay không
- Permission `bhyt.*` chỉ áp dụng khi flag ON. Khi flag OFF, permission grant không phát huy tác dụng (UI vẫn ẩn).
- Xem chi tiết các vùng UI ảnh hưởng tại [TAB_MATRIX.md](TAB_MATRIX.md#feature-flag-toàn-cục-bhyt-bậttắt)

---

## 3. Quan hệ flow giữa các module (đường đi của BN)

```
┌─────────────────────────────────────────────────────────────────────┐
│                    HÀNH TRÌNH 1 LƯỢT KHÁM                            │
└─────────────────────────────────────────────────────────────────────┘

  ① Đặt hẹn          → Lịch hẹn (Lễ tân/BN tự đặt)
        ↓
  ② Đến phòng khám   → Tiếp nhận (Lễ tân) → tra BHYT → tạo lượt khám
        ↓
  ③ Chờ khám         → Phòng chờ (queue card "Chờ sinh hiệu")
        ↓
  ④ Đo sinh hiệu     → EMR Tab 1: Sinh hiệu (Điều dưỡng)
        ↓                  → cảnh báo bất thường → BS
  ⑤ Khám bệnh        → EMR Tab 2-5: Khám LS / Chẩn đoán / Kê đơn / CLS (Bác sĩ)
        ↓                  → AI gợi ý + tương tác thuốc
  ⑥ Hoàn tất khám    → EMR Tab 6: Tóm tắt → đẩy đơn sang Dược + Thanh toán
        ↓
  ⑦ Cấp phát thuốc   → Kho thuốc (Dược sĩ) → in nhãn + tư vấn
        ↓
  ⑧ Thanh toán       → Hoá đơn (Lễ tân) → BHYT split + nhiều phương thức
        ↓
  ⑨ Ra về            → SMS nhắc tái khám / khảo sát hài lòng
```

Mỗi bước có thể **rẽ nhánh**:
- Cấp cứu (⚡) → bỏ qua bước ① → vào thẳng phòng khám
- BN không BHYT → bước ② skip tra cứu VSS
- Khám không cần CLS / không kê đơn → tab 4-5 ở trạng thái "trống" + emerald check
- BN nội trú (sau này) → có thêm flow Nhập viện / Theo dõi nội trú

---

## 4. Flow rẽ nhánh khẩn cấp

```
⚡ Cấp cứu (Triage)
    ↓
   Tiếp nhận FAST → tạo lượt khám với status "Cấp cứu" (red badge)
    ↓
   BN được đẩy lên TOP queue ở mọi role dashboard
    ↓
   Điều dưỡng được paged (notification + sound)
    ↓
   Sinh hiệu đo nhanh + chuyển BS trực CC
    ↓
   EMR mở với template "Cấp cứu" (form rút gọn)
    ↓
   Sau khi ổn → quyết định: chuyển khoa nội / cho ra viện / chuyển BV tuyến trên
```

---

## 5. Trạng thái của BN trong queue (state machine)

```
[Đã hẹn]
   ↓ check-in
[Chờ tiếp nhận]
   ↓ Lễ tân tiếp nhận
[Đã tiếp nhận]
   ↓ → [Chờ sinh hiệu]
        ↓ ĐD đo xong
       [Chờ bác sĩ]
        ↓ BS gọi
       [Đang khám]
        ↓ BS hoàn tất
       [Chờ thanh toán] ← (nếu có chỉ định CLS, chèn [Chờ CLS] giữa)
        ↓ Lễ tân thu tiền
       [Chờ phát thuốc] ← (chỉ khi có đơn)
        ↓ DS phát xong
       [Hoàn tất] ✓
```

Mỗi state có **chip màu khác nhau** và **wait timer** (đếm phút từ lúc vào state đó). Sau 30' → chip chuyển đỏ + alert ở Dashboard.

---

## 6. Mapping màn hiện tại — Stitch ID

| Màn hình                                    | Stitch Screen ID                       | Status                |
|---------------------------------------------|----------------------------------------|-----------------------|
| Đăng nhập                                   | `e98de272bc7249f39f9a233c7adb17f2`     | ✓ Done                |
| Dashboard Lễ tân                            | `e8ec8790c76f4a04b42400c78f3e934a`     | ✓ Done                |
| Dashboard Điều dưỡng                        | `416445275b17462e87c4dd6f29d42106`     | ✓ Done                |
| Dashboard Bác sĩ                            | `ccc8e77578684bd98a03a7d4344f70ff`     | ✓ Done                |
| Dashboard Dược sĩ                           | `0d856e6c35484cd2bffc967b23ce8268`     | ✓ Done                |
| Dashboard Quản trị                          | `e1e5cfeb40ce4de49b9be9e922fc3ab2`     | ✓ Done                |
| **Dashboard Multi-role (BS + Quản trị)**    | `308fffe2883f4c1cad7e7441120158b9`     | ✓ Done (Phase B)      |
| Tiếp nhận & Đăng ký BN                      | `8c84c7e3270d4b729d83d1c5d4f60992`     | ✓ Done                |
| Lịch hẹn (week view)                        | `2e1591c3fd534046932aaf2969fd571b`     | ✓ Done                |
| EMR Tab 1 — Sinh hiệu                       | `acef698641904014bf33326dcdd90813`     | ✓ Done (Phase C)      |
| EMR Tab 2 — Khám LS (S.O.A.P)               | `c12bf23adc844cfc8b3d4f632111b501`     | ✓ Done (Phase C)      |
| EMR Tab 3 — Chẩn đoán                       | `fbb61911b4f0496392836546150d2cb9`     | ✓ Done                |
| EMR Tab 4 — Kê đơn thuốc                    | `7e32e3c8c27043dfae12c8409a1acc2a`     | ✓ Done (Phase C)      |
| EMR Tab 5 — Cận lâm sàng (CLS)              | `b8f84b4034da4ebda2040f1260a01a0a`     | ✓ Done (Phase C)      |
| EMR Tab 6 — Tóm tắt & Hoàn tất              | `41e3a324001a4c469864e4538ad5539a`     | ✓ Done (Phase C)      |
| Kho thuốc & Cấp phát                        | `434d73b9387947328139f56dfad5309f`     | ✓ Done                |
| Thanh toán hoá đơn                          | `43971b42ba2b4043a89e8aa32261ec16`     | ✓ Done                |
| Cấu hình — Phòng khám & Chi nhánh           | `5f5f1093c7114782aaf063043443395d`     | ✓ Done (Phase C)      |
| Cấu hình — Vai trò & Phân quyền (RBAC)      | `1cb79779d2f145efb13f3d1223f70fc0`     | ✓ Done (Phase C)      |
| Cấu hình — Ca trực & Giờ làm                | `31b1b71d30bd4de88048648db5ab158f`     | ✓ Done (Phase C)      |
| Cấu hình — Bảng giá DV                      | `7c43ae65ba4346fea4685212f222866b`     | ✓ Done                |
| Cấu hình — BHYT (Mức hưởng + DM)            | `7ff9fe5bc8d541ecb7844f8965ddbf2b`     | ✓ Done (Phase C)      |
| Cấu hình — Tích hợp (VSS/HL7/DICOM/SMS)     | `1d6fc53966d541c4abb1f3c6949fc20f`     | ✓ Done (Phase C)      |
| Cấu hình — Audit Log                        | `e7735b5a24944273b631b514409be668`     | ✓ Done (Phase C)      |
| Cấu hình — Bảo mật & Mã hoá                 | `b15b501502274b55999bc61ac70f5045`     | ✓ Done (Phase C)      |
| Báo cáo — Tab Tổng quan                     | `d86ddd116f614b41b7f6536af01f86dc`     | ✓ Done                |
| Báo cáo — Tab Tài chính                     | `e471372c45ce42da827ce03c7f14559c`     | ✓ Done (Phase C)      |
| Báo cáo — Tab Lâm sàng                      | `eb2d066147e2472180010db35b66333e`     | ✓ Done (Phase C)      |
| Báo cáo — Tab Vận hành                      | `9431a116c63b4045a9798698d0826d41`     | ✓ Done (Phase C)      |
| Báo cáo — Tab Dược                          | `6b235c69f8e047c7a5798990e9665c81`     | ✓ Done (Phase C)      |
| Báo cáo — Tab BHYT                          | `12334fcf1bec408a80075ea361164ad4`     | ✓ Done (Phase C)      |

**Tổng**: 32 unique canonical screens.

**Duplicates (cần xoá thủ công khỏi Stitch)**:
| Screen ID                              | Lý do                                                             |
|----------------------------------------|-------------------------------------------------------------------|
| `283a28fda61c4785973ee139f668a00b`     | Kho thuốc V2 — bản retry cũ                                       |
| `4da3b971f72b410a8a44f6ed76149b18`     | Kho thuốc V3 incomplete (no screenshot)                           |
| `692bb83d5b254461ad1abdef1ae7b0f3`     | "Dashboard Đa vai trò" — auto-retry sinh khi MCP batch 1 timeout  |
| `a83fc3556c1f438eb070d7708e017902`     | "Dashboard Đa vai trò v3" — auto-retry sinh từ batch 1 timeout    |
