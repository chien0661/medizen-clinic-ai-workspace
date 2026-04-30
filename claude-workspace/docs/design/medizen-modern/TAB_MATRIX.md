# MediZen — Tab Matrix (states đầy đủ của các trang nhiều tab)

**Cập nhật**: 2026-04-30 (Phase C done — đã đính screen ID cho mọi tab)

Mục đích: liệt kê **mọi tab** của các màn complex, mô tả nội dung + state + actions của từng tab. Sau khi Phase C done, mỗi tab có 1 Stitch screen riêng — screen ID đã đính ngay đầu mục tab tương ứng.

---

## A. EMR — Chi tiết lượt khám (6 tabs)

**Layout chung**: Patient banner sticky + tab strip + 3-col layout (left summary 280px / center content 720px / right context 380px). Chuyển tab giữ nguyên patient banner & 2 cột phụ.

**Tab strip**:
```
1. Sinh hiệu ●  2. Khám LS ●  3. Chẩn đoán ●  4. Kê đơn ○  5. CLS ●  6. Tóm tắt ○
```
- ● = đã filled (emerald dot)
- ○ = chưa filled (slate dot)
- Click tab navigate without losing data (auto-save draft)

### Tab 1: Sinh hiệu

**Stitch screen**: `acef698641904014bf33326dcdd90813`

**Center content**:
- Vital cluster 4-up (HA / Mạch / SpO2 / Nhiệt) — input lớn
- Phụ: Cân nặng / Chiều cao (auto-calc BMI) / Vòng bụng / Đường huyết test
- Section "So sánh trước-sau":
  - Bảng 5 cột: Chỉ số · Hôm nay · Lần trước · Δ · Trend chart 6 lần đo
  - Từng row có sparkline + delta arrow
- Section "Đánh giá nhanh":
  - Chip: Bình thường / Cảnh báo nhẹ / Cảnh báo vừa / Nguy cấp
  - Auto-set theo logic ngưỡng

**Right context**:
- Card "Lịch sử HA của BN" (line chart 12 lần đo gần)
- Card "Thuốc đang dùng có ảnh hưởng vital" (Amlodipine, Losartan)

**Footer actions**:
- "Lưu nháp" (auto)
- "Đo lại" (clear form)
- "Lưu & Chuyển BS →" (primary indigo)

**Edge cases UI**:
- HA >180/110 → red border + banner Red full-width "Tăng HA cấp tính - paging BS?"
- Sốt >39 → tương tự
- BN từ chối đo → checkbox "BN từ chối" + textarea lý do (UI thay form)

---

### Tab 2: Khám lâm sàng (S.O.A.P phần S+O)

**Stitch screen**: `c12bf23adc844cfc8b3d4f632111b501`

**Center content**:

**Section "S — Subjective" (Lời kể BN)**:
- Textarea lớn 4-6 dòng + voice-to-text mic icon
- Toolbar: B I U · bullet · template (popover chọn template "Tăng HA tái khám", "Đau ngực", v.v.)
- Word count + auto-save indicator

**Section "O — Objective" (Khám thực thể)** — accordion 8 nhóm:
1. Toàn thân (BMI, da niêm, hạch, dấu sinh tồn, ý thức)
2. Đầu - cổ - mũi họng
3. Tim mạch (T1, T2, tiếng thổi, mạch ngoại vi)
4. Hô hấp (rì rào phế nang, ran, gõ)
5. Tiêu hóa (bụng mềm, gan lách, dấu hiệu đặc biệt)
6. Tiết niệu - sinh dục
7. Cơ - xương - khớp
8. Thần kinh (cảm giác, vận động, phản xạ)

Mỗi nhóm:
- Có nút "Bình thường" (1 click fill "không có bất thường")
- Có textarea cho free-text mô tả khi cần
- Có chip "Đã khám / Chưa khám / Không cần"

**Right context**:
- Card "Triệu chứng đã ghi nhận" — chip list từ S
- Card "Bất thường khám phát hiện" — chip list từ O (auto extract)
- Card "Template khám gợi ý" — link "Áp dụng template Tăng HA tái khám"

**Footer**:
- "Lưu nháp" / "Trở lại Sinh hiệu" / "Tiếp Chẩn đoán →"

---

### Tab 3: Chẩn đoán

**Stitch screen**: `fbb61911b4f0496392836546150d2cb9`

**Center content**:
- Field "Chẩn đoán chính (ICD-10)" — combobox autocomplete
- Field "Chẩn đoán phụ" — multi-chip
- Field "Mức độ" — segmented (Nhẹ / TB / Nặng / Nguy cấp)
- Field "Tình trạng" — radio (Cấp / Mạn / Tái phát / Hồi phục / Theo dõi)
- Card "S.O.A.P phần A (Assessment)":
  - Tab nhỏ trong card: S · O · **A** · P (đã chọn A)
  - Textarea lớn với template
- Card "S.O.A.P phần P (Plan)":
  - Checklist 5-7 mục đề xuất
  - Nút "+ Thêm hướng xử trí"

**Right context**:
- AI gợi ý chẩn đoán (MediZen AI) với confidence %
- Đường liên kết tới hướng dẫn lâm sàng (ESC/Bộ Y tế guidelines)

---

### Tab 4: Kê đơn thuốc

**Stitch screen**: `7e32e3c8c27043dfae12c8409a1acc2a`

**Center content**:

**Section "Tìm & Thêm thuốc"**:
- Search bar autocomplete (tên / hoạt chất / mã ATC / tên thương mại)
- Filter chips: "Trong DM BHYT · Có sẵn trong kho · Không tương tác"
- Button: "Áp dụng đơn thuốc cũ" (gợi ý từ lượt khám trước)

**Section "Đơn thuốc hiện tại"** — bảng dạng card mỗi thuốc:
```
┌─ Card thuốc ───────────────────────────────────────┐
│ [×] Losartan 50mg                  [Stock 240 ✓]   │
│     Hoạt chất: Losartan potassium                  │
│     Liều: [2 viên/ngày ▾]  Thời gian: ☑Sáng ☑Tối  │
│     Hướng dẫn: [Sau ăn ▾]                          │
│     Số ngày: [30]    Tổng: 60 viên                 │
│     ₫168,000 (BHYT 80% chi trả ₫134,400)          │
└─────────────────────────────────────────────────────┘
```

5-7 thuốc dạng card xếp dọc.

**Section "Cảnh báo"** (border-left red/amber):
- Tương tác thuốc-thuốc (check qua API DrugBank/MediZen DB)
- Tương tác thuốc-bệnh (vd: Diclofenac cho BN suy thận)
- Dị ứng (auto-block thuốc dị ứng)
- Trùng lặp với thuốc đang dùng

**Section "Tổng đơn"** (sticky bottom hoặc right):
- Tổng tiền: ₫280,000
- BHYT chi trả: ₫170,400
- BN trả: ₫109,600
- Số mục: 5

**Right context**:
- Card "Thuốc BN đang dùng" (từ lượt khám trước) — để tránh kê trùng
- Card "Dị ứng đã ghi nhận" (border-left red)
- Card "Mẫu đơn nhanh" (favorites của BS) — click apply

**Footer**:
- "Lưu nháp" / "Áp dụng template" / "Tiếp CLS →"

---

### Tab 5: Cận lâm sàng (CLS)

**Stitch screen**: `b8f84b4034da4ebda2040f1260a01a0a`

**Center content**:

**Section "Chỉ định CLS"**:
- Search dịch vụ CLS (X-quang, XN máu, Siêu âm, Nội soi, ...)
- Filter: "Theo khoa · Theo phòng · Theo giá"

**Section "CLS đã chỉ định"** — bảng:
| Mã | Dịch vụ | Phòng | Phí | BHYT | BN trả | Lý do | Thời gian dự kiến |
|---|---|---|---|---|---|---|---|
| XN-CHO | Cholesterol toàn phần | P. XN | ₫85k | 80% | ₫17k | Theo dõi RL lipid | 30' |
| XN-TRI | Triglyceride | P. XN | ₫65k | 80% | ₫13k | ... | 30' |
| ECG-12 | Điện tim 12 chuyển đạo | P. ECG | ₫120k | 80% | ₫24k | ... | 10' |
| SAU-TIM | Siêu âm tim Doppler | P. SA | ₫350k | 80% | ₫70k | ... | 20' |

**Section "Kết quả CLS đã có"** (từ lượt trước hoặc lượt này):
- Mỗi result là card với:
  - Loại CLS, ngày, KTV, status
  - Preview (text result + ảnh/PDF nếu có)
  - Chip status: ✓ Bình thường / ⚠ Bất thường nhẹ / ✕ Bất thường nặng
  - Nút "Mở chi tiết" → modal viewer DICOM hoặc PDF

**Right context**:
- Card "Lịch sử CLS BN" (timeline 12 mục)
- Card "Hướng dẫn chuẩn bị BN" (vd: nhịn ăn 8h trước XN máu)

**Footer**:
- "Lưu nháp" / "Tiếp Tóm tắt →"

---

### Tab 6: Tóm tắt & Hoàn tất

**Stitch screen**: `41e3a324001a4c469864e4538ad5539a`

**Center content** — Read-only summary toàn bộ 5 tab trước:

**Section "1. Sinh hiệu"** (collapsed):
- 1 dòng tóm tắt: "HA 138/89 · Mạch 78 · SpO2 98% · Nhiệt 36.8 — Cảnh báo nhẹ"
- Click expand thấy chi tiết

**Section "2. Khám lâm sàng"**:
- S: "BN tái khám tăng HA, kèm khó ngủ 1 tuần"
- O: 3-5 dòng quan trọng nhất

**Section "3. Chẩn đoán"**:
- Chip lớn: "I10 — Tăng huyết áp nguyên phát"
- Chip phụ: E78.5, G47.0
- Mức độ: Trung bình · Mạn tính

**Section "4. Đơn thuốc"**:
- Bảng mini 5 thuốc

**Section "5. CLS"**:
- Bảng mini 4 chỉ định + status

**Section "Tổng chi phí"** (highlight indigo bg):
- DV khám: ₫770,000
- Đơn thuốc: ₫280,000
- Tổng: ₫1,050,000
- BHYT 80%: −₫786,400
- BN trả: ₫264,000

**Section "Lời dặn BN"** (textarea):
- Template "Theo dõi HA tại nhà mỗi ngày 2 lần..."
- Voice-to-text

**Section "Tái khám"** (form):
- Date picker: "28/05/2026"
- Slot: "09:00 BS. Bình"
- Auto-tạo lịch hẹn mới

**Right context**:
- Card "Sẽ đẩy đi đâu?" — preview các đích sau khi hoàn tất:
  - Đơn thuốc → DS
  - CLS → KTV phòng XN/SA
  - Hoá đơn → Lễ tân thanh toán
  - Lịch hẹn tái khám → tự động tạo

**Footer actions chính**:
- "Lưu nháp" (ghost)
- "← Trở lại CLS" (secondary)
- "✓ Hoàn tất khám" (primary emerald lớn)

**Validation trước khi hoàn tất**:
- Phải có ≥1 chẩn đoán
- Phải có ≥1 trong (đơn thuốc / CLS / lời dặn theo dõi)
- Confirm modal: "Hoàn tất khám LK-...0042?"

---

## B. Cấu hình hệ thống (8 sections)

**Layout chung**: Sub-nav 240px (settings tree) + content + drawer phải khi sửa item.

**Sub-nav tree** (đã design):
```
Phòng khám
  • Thông tin chung
  • Chi nhánh & Phòng khám
  • Khoa / Chuyên khoa
  • Phòng & Giường
Nhân sự
  • Vai trò & Phân quyền
  • Ca trực & Giờ làm
  • Mẫu chữ ký số
Dịch vụ y tế
  • Bảng giá dịch vụ ✓ (đã có mock)
  • Danh mục ICD-10
  • Danh mục thuốc
  • Mẫu đơn thuốc
BHYT
  • Cấu hình mức hưởng
  • Danh mục BHYT
  • Lý do từ chối
Tài chính
  • Phương thức thanh toán
  • Thuế & Hóa đơn
  • Mã giảm giá
Tích hợp
  • Cổng BHYT VSS
  • Máy XN (HL7)
  • Máy CĐHA (DICOM)
  • SMS / Email gateway
  • Webhook & API key
Hệ thống
  • Thông báo
  • Sao lưu & Khôi phục
  • Audit log
  • Bảo mật & Mã hóa
  • Lý lịch phiên bản
```

### Section: Phòng khám (Thông tin chung + Chi nhánh)

**Stitch screen**: `5f5f1093c7114782aaf063043443395d`

**Content**:
- Header card: tên PK + logo upload + tagline
- Tab strip: "Thông tin · Chi nhánh · Khoa · Phòng"
- **Tab Thông tin**: form phẳng (tên, mã số thuế, địa chỉ, hotline, website, giờ mở cửa, chứng chỉ hành nghề)
- **Tab Chi nhánh**: bảng chi nhánh (mã, tên, địa chỉ, SL phòng, status), nút "+ Thêm chi nhánh"
- **Tab Khoa**: cây phân khoa (Nội → Tim mạch / Hô hấp / Tiêu hóa, Sản, Nhi, ...) — drag-drop sắp xếp
- **Tab Phòng**: bảng phòng từng chi nhánh + capacity + thiết bị

### Section: Vai trò & Phân quyền (RBAC matrix)

**Stitch screen**: `1cb79779d2f145efb13f3d1223f70fc0`

**Content**:
- Tab strip: "Vai trò · Quyền · User · Audit"
- **Tab Vai trò**: cards 5 system roles (Lễ tân/Điều dưỡng/BS/DS/QT) + custom roles
  - Mỗi card: số user · số quyền · created by · last modified
- **Tab Quyền**: ma trận **38 permissions × 5 roles** (checkbox grid)
  - Group quyền theo module
  - Diff view khi role có override khỏi default
- **Tab User**: bảng user → role assignment, drag-drop để gán role
  - Per-user grant/deny override (column expand)
- **Tab Audit**: list thay đổi RBAC 90 ngày qua

### Section: Ca trực & Giờ làm

**Stitch screen**: `31b1b71d30bd4de88048648db5ab158f`

**Content**:
- Tab: "Mẫu ca · Lịch ca tuần · Lịch ca tháng · Off"
- **Tab Mẫu ca**: cards các ca (Sáng 7-14h, Chiều 14-21h, Đêm 21-7h, ...)
- **Tab Lịch ca tuần**: calendar 7 ngày × 24h, drag-drop nhân viên vào slot
  - Group theo bộ phận (BS, ĐD, ...)
  - Cảnh báo conflict (1 người 2 ca cùng giờ)
- **Tab Lịch ca tháng**: heatmap 30 ngày
- **Tab Off**: list yêu cầu nghỉ phép, approve workflow

### Section: BHYT

**Stitch screen**: `7ff9fe5bc8d541ecb7844f8965ddbf2b`

**Content**:
- Tab: "Mức hưởng · Danh mục · Lý do từ chối · Lịch sử đồng bộ"
- **Tab Mức hưởng**: matrix nhóm BN × loại hình (đúng tuyến/trái tuyến/cấp cứu)
  - Hộ nghèo · Trẻ em <6 · Người già >70 · ...
- **Tab Danh mục**: 1000+ items đồng bộ Bộ Y tế
  - Search + filter "Đang áp dụng / Sắp hết / Mới"
- **Tab Lý do từ chối**: catalog lý do thường gặp (thẻ hết hạn, sai tuyến, mã sai, ...) — dùng để báo BN
- **Tab Lịch sử đồng bộ**: log mỗi lần sync với BYT, kết quả, conflicts

### Section: Tích hợp

**Stitch screen**: `1d6fc53966d541c4abb1f3c6949fc20f`

**Content**:
- Tab: "VSS · HL7 · DICOM · SMS/Email · Webhook · Logs"
- **Tab VSS**: input API key + endpoint, test connection, retry policy
- **Tab HL7**: list máy XN tích hợp (mã, model, hostname, last sync), nút "Add device"
- **Tab DICOM**: list máy CĐHA + viewer config
- **Tab SMS/Email**: provider (Twilio/Sendgrid/...), template variables, throttle
- **Tab Webhook**: URL endpoints + events subscribe (visit.created, prescription.dispensed, ...)
- **Tab Logs**: integration call logs (filterable), failure rate

### Section: Audit log

**Stitch screen**: `e7735b5a24944273b631b514409be668`

**Content**:
- Filter bar (sticky): Date range, User, Action type (CRUD, login, config change), Module, Severity
- Bảng log:
  - Timestamp · User (avatar+role chip) · Action · Module · Resource · Severity · IP · Device
  - Mỗi row click → drawer phải xem diff (before/after JSON tree)
- Toolbar: Export CSV, Saved filter views

### Section: Bảo mật & Mã hóa

**Stitch screen**: `b15b501502274b55999bc61ac70f5045`

**Content**:
- Section "Mật khẩu policy": min length, complexity, rotation, history
- Section "MFA": enforce per role, supported methods (TOTP, SMS, Email)
- Section "Session": timeout, concurrent session limit, force logout
- Section "Data encryption": status RLS, audit của model, key rotation
- Section "PII handling": list field auto-redact, retention policy
- Section "Compliance": HIPAA/Nghị định 13 checklist với status ✓/⚠/✕

---

## C. Báo cáo & Thống kê (6 tabs)

**Layout chung**: Filter bar (period, khoa, BS) + tab strip + KPI cards + charts grid + tables.

### Tab 1: Tổng quan

**Stitch screen**: `d86ddd116f614b41b7f6536af01f86dc`

- 4 KPI: Lượt khám / Doanh thu / BN mới / Tỉ lệ tái khám
- Combo chart 12 tháng
- Donut phân bố nguồn BN
- Top 10 dịch vụ
- Heatmap giờ/ngày
- Top 5 BS

### Tab 2: Tài chính

**Stitch screen**: `e471372c45ce42da827ce03c7f14559c`

**KPI cards**:
- Tổng doanh thu kỳ
- Doanh thu BHYT vs Tự trả (%)
- Công nợ outstanding
- AR turnover days

**Charts**:
- Bar chart "Doanh thu theo tháng" stacked (BHYT vs Tự trả vs Hợp đồng)
- Line "Cash flow ngày" 30 ngày
- Donut "Phương thức thanh toán" (Tiền mặt / CK / POS / QR)
- Bar "Top 10 dịch vụ doanh thu"
- Bar "Doanh thu theo BS / Khoa"

**Tables**:
- Hoá đơn pending overdue
- Hoàn tiền / điều chỉnh trong kỳ
- Phân tích chi phí (lương + thuốc + vận hành)

**P&L statement** (mini): Revenue - COGS - OPEX = Net

### Tab 3: Lâm sàng

**Stitch screen**: `eb2d066147e2472180010db35b66333e`

**KPI**:
- Tổng lượt khám
- Avg thời gian khám (phút)
- Tỉ lệ tái khám 30/60/90 ngày
- Tỉ lệ chuyển viện

**Charts**:
- Top 20 chẩn đoán (ICD-10)
- Pyramid age × giới của BN
- Time-to-diagnosis distribution
- Procedure mix
- Outcome metrics (theo dõi HA, đường huyết...) — Patient-level

**Tables**:
- Hiệu suất BS (lượt, doanh thu, đánh giá, tỉ lệ tái khám)
- BN mạn tính cần follow-up

### Tab 4: Vận hành

**Stitch screen**: `9431a116c63b4045a9798698d0826d41`

**KPI**:
- Avg wait time tổng
- No-show rate
- Cancel rate
- Phòng utilization %

**Charts**:
- Heatmap wait time theo giờ/ngày
- Funnel: Hẹn → Check-in → Sinh hiệu → Khám → Thanh toán → Ra về
  (mỗi bước hiển thị conversion + drop-off + avg time)
- Bottleneck analysis

**Tables**:
- Phòng/thiết bị utilization
- Nhân sự utilization (giờ làm vs giờ idle)
- BN no-show pattern (BN nào hay no-show)

### Tab 5: Dược

**Stitch screen**: `6b235c69f8e047c7a5798990e9665c81`

**KPI**:
- Tổng giá trị tồn kho
- Inventory turnover
- Stock-out events
- Expired waste %

**Charts**:
- Top 20 thuốc bán chạy (revenue + volume)
- Inventory aging (FIFO check)
- Expiry curve 6 tháng tới
- Demand forecast (theo lịch sử)

**Tables**:
- Reorder list (thuốc dưới min)
- Slow-movers (>90 ngày không bán)
- Disposal log (thuốc hết hạn)
- Vendor performance

### Tab 6: BHYT

**Stitch screen**: `12334fcf1bec408a80075ea361164ad4`

**KPI**:
- Tỉ lệ duyệt
- Avg time to approve
- Tổng số tiền BHYT chi trả
- Số đơn pending VSS

**Charts**:
- Funnel duyệt: Submit → Pending → Approved/Rejected
- Bar lý do từ chối top 10
- Trend tỉ lệ duyệt 12 tháng
- Phân bố mức hưởng (80% / 95% / 100%)

**Tables**:
- Đơn pending >7 ngày (action needed)
- Đơn rejected gần đây với lý do
- Phân tích BN BHYT theo nhóm (đúng tuyến, hộ nghèo, ...)
- Sync history với VSS API

---

## Tổng kết generation Phase C — DONE (TASK-027, 2026-04-30)

**EMR**: 5/5 màn ✓ (Sinh hiệu / Khám LS / Kê đơn / CLS / Tóm tắt)
**Settings**: 7/7 màn ✓ (Phòng khám / Vai trò / Ca trực / BHYT / Tích hợp / Audit / Bảo mật)
**Reports**: 5/5 màn ✓ (Tài chính / Lâm sàng / Vận hành / Dược / BHYT)

**Total**: 17/17 màn Phase C + 1/1 màn Phase B (Multi-role Dashboard) = **18/18 hoàn tất**.

Mỗi tab/section đã có Stitch screen ID đính ở đầu mục — click qua Stitch project để xem state đầy đủ.
