# MediZen — Action Flows chi tiết

**Cập nhật**: 2026-04-30

Mỗi flow ghi rõ: **trigger · ai chạy · steps · UI elements · backend events · edge cases**.

---

## Flow 1: Tiếp nhận bệnh nhân BHYT có hẹn

**Trigger**: BN đến quầy lễ tân, mã hẹn `HEN-2456`
**Actor**: Lễ tân (Mai Anh)
**Mục tiêu**: Tạo lượt khám + đẩy vào hàng đợi

```
Step 1 — Tìm lịch hẹn
  UI: Topbar Cmd+K → gõ "Lê Hà Vy" hoặc "HEN-2456"
  Element: Command palette overlay (full-width 720px, ESC để đóng)
  Result: Hiển thị "Lê Hà Vy · BHYT · Hẹn 09:30 · BS. Bình"
  Click → mở màn "Tiếp nhận & Đăng ký" với BN selected

Step 2 — Kiểm tra hồ sơ BN
  UI: Cột phải hiện avatar + thông tin BN, cột trái queue (12 BN)
  Element: Patient banner đầu (sticky), tabs "Thông tin tiếp nhận" active
  Lễ tân scan: BHYT chip xanh "GD4-DN-7898 · 80%"
  Cảnh báo dị ứng "Penicillin" → chip Red sticky bên phải

Step 3 — Tra cứu BHYT VSS (1 click)
  UI: Section "2. Bảo hiểm y tế" → nút "Tra cứu VSS" secondary
  Action: Click → spinner 1.5s → return 3 chip kết quả:
    ✓ Hợp lệ (Emerald)
    Hết hạn 02/11/2026 (slate)
    Đúng tuyến (Emerald)
  Backend: POST /api/v1/bhyt/verify { card: "GD4-DN-7898" }
  Edge: Nếu fail → chip Red "Không tra được — kiểm tra mạng" + nút retry

Step 4 — Chọn dịch vụ chỉ định
  UI: Section "3. Dịch vụ chỉ định" → nút "+ Thêm dịch vụ"
  Modal: Search dịch vụ → click chọn → thêm vào bảng
  Auto-calc BHYT 80% trên đơn giá
  Total row update real-time

Step 5 — Xác nhận tiếp nhận
  UI: Cột phải sticky → button lớn primary indigo "Xác nhận tiếp nhận"
  Action: Click → confirm modal "Tạo lượt khám LK-2026-04-30-0042?"
  Sau confirm:
    • Tạo record patient_visits
    • Tạo invoice draft (status: draft)
    • Đẩy BN vào queue với status "Chờ sinh hiệu"
    • Auto-print phiếu chờ khám (số TT 005)
    • SMS thông báo cho BN: "Số TT 005, vui lòng vào phòng 102"
  Toast emerald: "✓ Đã tiếp nhận. Số TT 005"

Step 6 — Quay về queue
  UI: Tự động chuyển sang BN tiếp theo trong queue
  Lễ tân thấy BN-2456 biến mất khỏi "Chờ tiếp nhận", xuất hiện trong "Chờ sinh hiệu" với chip Amber

Edge cases:
  • BHYT hết hạn → chip Red, hiện gợi ý "Chuyển sang Tự trả?"
  • BN chưa từng khám → button "Đăng ký BN mới" thay vì queue card
  • Cấp cứu (red badge) → button extra "Bỏ qua thanh toán, đẩy thẳng phòng cấp cứu"
```

---

## Flow 2: Đo sinh hiệu (Vitals) — Điều dưỡng

**Trigger**: BN-005 chuyển sang trạng thái "Chờ sinh hiệu"
**Actor**: Điều dưỡng Hà
**Mục tiêu**: Đo + nhập 4 chỉ số chính (HA, mạch, SpO2, nhiệt) trong <2 phút

```
Step 1 — Nhận BN tiếp theo
  UI: Dashboard Điều dưỡng → row 1 trong queue (highlighted indigo soft, "Tiếp theo")
  Element: Nút "Bắt đầu đo" primary indigo
  Click → mở màn EMR tab "Sinh hiệu" (đây là tab 1 của 6)

Step 2 — Nhập sinh hiệu
  UI: Form 4 ô nhập lớn:
    Huyết áp:  [138]/[89] mmHg
    Mạch:      [78]      lần/phút
    SpO2:      [98]      %
    Nhiệt:     [36.8]    °C
  Mỗi field có:
    • Auto-focus next field khi enter
    • Validation real-time: HA >180/110 → red border + warning
    • So sánh với lần đo trước → delta arrow ⬆⬇ + chữ "Trước: 145/92"
  Phụ:
    Cân nặng:  [62]   kg
    Chiều cao: [158]  cm  (auto BMI tính 24.8 = chip Emerald "Bình thường")
    Vòng bụng: [76]   cm
    Đường huyết test nhanh: [_] mmol/L (optional)

Step 3 — AI cảnh báo (nếu có bất thường)
  Khi HA = 138/89 (Tăng HA độ I):
  Banner Amber phía trên form: "⚠ Huyết áp cao hơn mục tiêu (<130/80) — đề xuất đo lại lần 2 sau 5 phút"
  Nút trong banner: "Đặt nhắc 5 phút" (tạo timer trên topbar)

  Khi HA >180/110 (Tăng HA độ III) → banner Red:
  "⚠ Tăng HA cấp tính — gửi paging cho BS. Bình ngay?"
  Nút: "Gửi paging" (auto-trigger SMS/notification)

Step 4 — Lưu & Chuyển BS
  UI: Nút phải dưới form: "Lưu & Chuyển BS"
  Action:
    • Save record patient_vitals
    • Update queue: status "Chờ bác sĩ", phòng = "102 (BS. Bình)"
    • Notify BS qua web socket → dot đỏ trên menu "Bệnh nhân của tôi"
  Toast: "✓ Đã chuyển BN-005 sang BS. Bình"

Step 5 — Quay về queue
  UI: Tự động về Dashboard Điều dưỡng, highlight BN tiếp theo

Edge cases:
  • Đo lại lần 2 trong 5 phút → tạo bản ghi vitals thứ 2, sparkline 2 điểm
  • Vital nguy hiểm (sốt 39.5+, HA >180/110, SpO2 <92%) → tự động tạo alert ưu tiên đỏ
  • BN từ chối đo (vd: cao huyết áp do stress) → checkbox "BN từ chối" + ghi chú lý do
```

---

## Flow 3: Khám bệnh — Bác sĩ (multi-tab EMR)

**Trigger**: BN-005 ở trạng thái "Chờ bác sĩ" trong queue BS. Bình
**Actor**: BS. Bình
**Mục tiêu**: Hoàn thành 6 tab S.O.A.P + đẩy đơn sang Dược + Thanh toán

```
Step 1 — Vào phòng khám
  UI: Dashboard Bác sĩ → row 1 highlighted "Sẵn sàng"
  Click "Bắt đầu khám" → màn EMR mở với BN-005

Step 2 — Tab 1: Sinh hiệu (đã có data từ ĐD Hà)
  BS quan sát Vital Cluster (4 ô) đã có:
    HA: 138/89 (chip Amber)
    Mạch: 78
    SpO2: 98%
    Nhiệt: 36.8
  Tab dot: ● emerald (đã filled)
  BS click tab "Khám lâm sàng" để qua tab 2

Step 3 — Tab 2: Khám lâm sàng (S.O.A.P — phần Subjective + Objective)
  S — Subjective (lời kể BN):
    Textarea + voice-to-text button (sử dụng Web Speech API)
    BS đọc: "BN nữ 41 tuổi tái khám tăng huyết áp, kèm khó ngủ 1 tuần"
    → Text auto-fill
  
  O — Objective (khám thực thể):
    Form theo cấu trúc:
      Toàn thân: [tỉnh táo] [da niêm hồng] [...] (multi-chip checkboxes)
      Tim mạch: T1, T2 đều, ko tiếng thổi → free text
      Hô hấp: ...
      Tiêu hóa: ...
      Thần kinh: ...
    Mỗi section có shortcut "Bình thường" (1 click fill toàn bộ "không có bất thường")
  
  Tab dot: chuyển từ ○ → ● khi user gõ ≥10 từ

Step 4 — Tab 3: Chẩn đoán (đã design chi tiết — đây là tab default đã có mock)
  • Combobox tìm ICD-10 (vd: gõ "tăng huyết" → autocomplete I10, I11.0,...)
  • Chip lớn cho main dx + multi-chip cho phụ
  • Mức độ + Tình trạng (segmented)
  • S.O.A.P phần A — Assessment textarea
  • S.O.A.P phần P — Plan checklist
  
  AI gợi ý dựa trên symptoms + vitals + history → 2-3 dx suggestion với confidence %

Step 5 — Tab 4: Kê đơn thuốc
  Search thuốc (autocomplete tên + hoạt chất)
  Mỗi thuốc click thêm → row trong bảng với:
    • Tên thuốc + hàm lượng
    • Liều: dropdown "1 viên/lần · 2 lần/ngày" (preset có sẵn theo guideline)
    • Chip thời gian: ☑ Sáng ☑ Tối (default theo loại thuốc)
    • Hướng dẫn: "Sau ăn no" / "Trước ăn" / "Trước ngủ"
    • Số ngày: input + auto-calc tổng số viên
    • BHYT chip (auto từ DM thuốc)
    • Stock badge (real-time từ Kho)
  
  Tổng đơn calc real-time
  Cảnh báo tương tác:
    Banner Amber: "⚠ Losartan + Indapamide → có thể hạ K+ máu — đề xuất xét nghiệm điện giải đồ"
    Nút: "Thêm chỉ định CLS điện giải đồ" (auto fill tab 5)
  Cảnh báo dị ứng:
    Banner Red: "🚫 BN dị ứng Penicillin — Amoxicillin BỊ CHẶN" (button "Phát" disabled)

Step 6 — Tab 5: Cận lâm sàng
  Search dịch vụ CLS (giống Tiếp nhận màn) → multi-select
  Auto fill nếu có chỉ định từ AI ở tab 4
  Mỗi CLS có:
    • Giá + BHYT mức hưởng
    • Phòng chỉ định (auto theo loại: XN máu → P. XN, X-quang → P. CĐHA)
    • Thời gian dự kiến trả kết quả
    • Ghi chú cho kỹ thuật viên
  Tổng phí CLS calc real-time

Step 7 — Tab 6: Tóm tắt & Hoàn tất
  Read-only summary toàn bộ 5 tab:
    • Sinh hiệu (1 dòng)
    • Triệu chứng (lượt qua)
    • Chẩn đoán (chip)
    • Thuốc (mini bảng 5 thuốc)
    • CLS (mini bảng 3 mục)
    • Tổng chi phí: ₫1,050,000 (BHYT 80% = ₫786K, BN trả ₫264K)
  
  Buttons:
    [Lưu nháp]  [Trở lại tab 5]  [✓ Hoàn tất khám] (primary emerald lớn)
  
  Click "Hoàn tất khám":
    • Validate: Bắt buộc có chẩn đoán + ít nhất 1 trong (đơn thuốc OR CLS OR theo dõi)
    • Backend: Update visit status = "completed_exam"
    • Đẩy đơn thuốc → queue Dược
    • Đẩy CLS → queue kỹ thuật viên (nếu có)
    • Đẩy invoice → Lễ tân Thanh toán
    • Update BN status: "Chờ thanh toán" (hoặc "Chờ CLS" nếu có CLS chưa làm)
  Toast: "✓ Hoàn tất khám LK-...0042. Thời gian khám: 14 phút"

Step 8 — Quay về Dashboard
  UI tự động về Dashboard BS → BN tiếp theo highlight

Edge cases:
  • Tạm dừng khám (nghỉ 5 phút, BN cần đi WC) → button "Tạm dừng" → status "Pause", auto-save
  • BS phát hiện cần thêm chuyên khoa → button "Chuyển khoa" → tạo lượt khám mới ở khoa khác, link với lượt hiện tại
  • BS muốn refer BN ra ngoài (vd: chụp MRI ở BV TW) → tab Plan có template "Giấy chuyển viện" auto-gen PDF
```

---

## Flow 4: Cấp phát thuốc — Dược sĩ

**Trigger**: BN-005 thanh toán xong → đơn thuốc đẩy vào queue Dược
**Actor**: DS Hằng
**Mục tiêu**: Lấy thuốc theo lô đúng + in nhãn + tư vấn BN

```
Step 1 — Quét QR đơn thuốc
  UI: Dashboard Dược → click "Quét mã đơn" topbar
  Modal: Camera scanner
  BN đưa phiếu in có QR → scan
  Auto navigate đến đơn ĐT-2456 trong panel "Đơn cấp phát đang xử lý"

Step 2 — Kiểm tra đơn
  UI: Panel phải shows full đơn 5 thuốc
  BS kê: BS. Bình · 14:32
  BN: Lê Hà Vy · BHYT · không dị ứng (đã filter Penicillin từ trước)

Step 3 — Chọn lô cho từng thuốc
  Mỗi thuốc trong đơn:
    • Click → drawer mở với danh sách lô có sẵn (FIFO sort theo HSD gần)
    • Lô gợi ý: hiển thị stock badge "Còn 240 viên" + HSD
    • DS chọn lô → checkbox xanh
    • Cảnh báo nếu chọn lô HSD <30 ngày: chip Amber "Sắp hết hạn 12 ngày — BN có dùng kịp không?"

Step 4 — Cảnh báo tương tác (nếu chưa tick từ BS)
  Banner Sky info: "ℹ Diclofenac + Amoxicillin: uống cách nhau 2h"
  DS phải click "✓ Đã đọc" để enable nút "Xác nhận cấp phát"

Step 5 — In nhãn thuốc
  Nút secondary: "In nhãn + hướng dẫn"
  Auto-print nhãn cho từng thuốc:
    "LOSARTAN 50MG
     BN: Lê Hà Vy (41N)
     2 viên/ngày sáng-tối, sau ăn
     Trong 30 ngày
     [QR code]"
  + Tờ hướng dẫn dùng thuốc (1 tờ A5 tổng hợp)

Step 6 — Cấp phát thực tế
  Lấy thuốc từ kho theo nhãn lô
  Check lại với BN: tên thuốc, liều, thời gian
  Tư vấn ngắn (template card sticky bên phải):
    "Bà uống Losartan và Indapamide cùng buổi sáng được, nhưng Indapamide nên uống sau ăn no. Tránh đứng lên đột ngột vì có thể chóng mặt..."

Step 7 — Xác nhận cấp phát
  Nút primary emerald lớn "Xác nhận cấp phát ✓"
  Confirm modal "Đã cấp phát đầy đủ 5 thuốc cho BN-005?"
  Sau confirm:
    • Backend: Update prescription status = "dispensed"
    • Trừ stock theo từng lô
    • Audit log: "DS Hằng cấp phát ĐT-2456 lúc 14:38"
    • Update queue BN: "Hoàn tất ✓"
    • SMS BN: "Bà có thể ra về. Hẹn tái khám 28/05/2026"
  Toast emerald: "✓ Cấp phát ĐT-2456. Doanh thu thuốc tích lũy hôm nay: ₫8.79M"

Edge cases:
  • Hết thuốc trong kho → button "Đặt mua khẩn" → tạo PO + thông báo BS để thay thuốc thay thế
  • BN từ chối lấy 1 thuốc → checkbox "BN từ chối" + ghi chú → đơn partial dispense, audit log đặc biệt
  • BS muốn đổi đơn sau khi đã đẩy → chat-flow nội bộ giữa DS-BS qua màn EMR (không edit trực tiếp đơn đã đẩy)
```

---

## Flow 5: Cấu hình giá dịch vụ (Quản trị)

**Trigger**: Quản trị cần update giá Siêu âm tim Doppler từ ₫350k → ₫400k áp dụng từ 01/06
**Actor**: Quản trị Bảo Minh
**Mục tiêu**: Lên lịch tăng giá có hiệu lực tương lai, không phá BN đang có hẹn

```
Step 1 — Vào Cấu hình > Bảng giá DV
  UI: Sidebar Quản trị → "Cấu hình hệ thống"
  Sub-nav: Dịch vụ y tế > Bảng giá dịch vụ (active)
  Search "Siêu âm tim Doppler" → 1 result DV022

Step 2 — Mở drawer sửa nhanh
  Click row DV022 → drawer phải slide ra 320px
  Hiển thị form đầy đủ + tab "Lịch giá"

Step 3 — Lên lịch giá mới (KHÔNG sửa giá hiện tại)
  Trong tab "Lịch giá", click "+ Lên lịch giá mới"
  Modal:
    Có hiệu lực từ: [01/06/2026]
    Đơn giá mới: [400,000]
    Mức BHYT: [80%] (giữ nguyên hoặc đổi)
    Lý do thay đổi: textarea "Tăng theo bảng giá BV mới của Bộ Y tế" (BẮT BUỘC)
    Người duyệt: [Auto = Quản trị hiện tại] hoặc chọn GĐ
  
  Validation:
    • Ngày hiệu lực phải > today
    • Cảnh báo nếu có ≥10 lịch hẹn đã đặt sau ngày này với DV022 cũ
      → modal con: "Có 47 lịch hẹn dùng DV022 sau 01/06. Áp dụng giá mới sẽ làm 47 invoice tăng tổng ₫2.35M. Bạn xác nhận?"
      Options: [Áp dụng cho lịch mới sau ngày này] vs [Áp dụng cho cả lịch đã đặt]

Step 4 — Lưu draft (chờ duyệt)
  Status mới: "Chờ duyệt" Amber
  Hiển thị trong bảng row DV022 với chip "Sắp tăng giá 01/06"
  Audit log: "BảoMinh tạo đề xuất tăng giá DV022 → 400k, hiệu lực 01/06"

Step 5 — Duyệt (nếu có separation of duties)
  GĐ (role khác) login → notification "Có 1 đề xuất giá chờ duyệt"
  Click → màn list draft → review → button "Duyệt" (primary)
  Sau duyệt: trạng thái thành "Đã duyệt, sẽ áp dụng 01/06"
  Notification về BảoMinh + audit log

Step 6 — Effect at runtime
  Cron job 00:00 ngày 01/06/2026 tự activate:
    • Old price record: status = "expired"
    • New price record: status = "active"
    • Cache redis invalidate
    • Tất cả invoice mới sau thời điểm này tự apply giá mới

Edge cases:
  • Cần rollback gấp (sai giá) → có nút "Hủy lịch giá" trước ngày hiệu lực
  • Cần áp giá ngay không chờ → có toggle "Áp dụng ngay" (yêu cầu 2FA của user role cao hơn)
  • Có nhiều draft giá overlap → hệ thống hiện cảnh báo và yêu cầu chọn 1
```

---

## Flow 6: Cấp BHYT hết hạn → upsell BHYT tự nguyện

**Trigger**: Lễ tân tra BHYT BN-007 → kết quả "Đã hết hạn 28/04/2026"
**Actor**: Lễ tân Mai Anh + BN
**Mục tiêu**: Vẫn cho BN khám + đề xuất BHYT tự nguyện

```
Step 1 — Tra BHYT trong màn Tiếp nhận
  Click "Tra cứu VSS" → return Red chip "Hết hạn từ 28/04/2026"
  Banner Amber phía trên section: "⚠ BHYT đã hết hạn 2 ngày — BN sẽ phải tự trả 100%"

Step 2 — UI đề xuất tùy chọn
  3 chip lớn full-width:
    [💳 Tiếp tục Tự trả] (primary)
    [📋 Hướng dẫn gia hạn BHYT online]  (secondary, link sang VSS)
    [🛡️ Mua bảo hiểm tự nguyện ngay] (ghost, mở modal nội bộ)

Step 3 — Tiếp tục Tự trả (path A)
  Click → form Tiếp nhận switch sang Tự trả mode
  Bảng dịch vụ tự động bỏ mức "BHYT 80%", BN trả 100%
  Total update real-time

Step 4 — (Path B) Lễ tân in tờ rơi gia hạn
  Hiển thị PDF 1 trang hướng dẫn:
    1. Vào https://baohiemxahoi.gov.vn
    2. Đăng nhập VSS-ID
    3. Chọn "Gia hạn BHYT hộ gia đình"
    4. Đóng phí qua MoMo/ZaloPay/...
  Print → đưa BN

Step 5 — (Path C) Bán bảo hiểm tự nguyện qua đối tác
  Mở modal nội bộ (nếu PK có hợp tác Bảo Việt/Manulife):
    Thông tin BN auto-fill
    3 gói bảo hiểm: Cơ bản 500k/năm · Tiêu chuẩn 1.2M · Cao cấp 2.5M
    Click chọn → redirect sang portal đối tác qua SSO
  Lễ tân nhận hoa hồng → log riêng

Edge cases:
  • BHYT chưa hết hạn nhưng trái tuyến → vẫn được BHYT 40% thay vì 80%, banner Sky info
  • BHYT báo "Không tìm thấy" → nhập tay số thẻ + ngày hiệu lực dự kiến (lễ tân chịu trách nhiệm)
```

---

## Flow 7: Xử lý kết quả CLS bất thường (Sky alert)

**Trigger**: Kỹ thuật viên CĐHA upload kết quả X-quang BN-007 với phát hiện "Bóng tim to nhẹ"
**Actor**: BS. Bình (đang khám BN khác)
**Mục tiêu**: BS thấy alert ngay + quyết định emergency hay routine

```
Step 1 — Notification
  WebSocket push → topbar BS có dot đỏ + popover:
    "🆕 Kết quả CLS mới: BN-007 Đỗ Thanh Hà · X-quang ngực · ⚠ Bóng tim to"
  Sound notification (nếu BS bật)

Step 2 — Xem nhanh từ Dashboard
  Card "Kết quả CLS cần xem" có badge "4 mới"
  Row đầu là BN-007 (highlighted với chip Amber)
  Click → modal preview ảnh X-quang + report KTV

Step 3 — Quyết định
  Modal preview có 3 nút:
    [📞 Gọi BN ngay] (red, dùng khi nguy cấp — auto-dial qua VoIP nếu tích hợp)
    [📅 Đặt tái khám gấp 24-48h] (amber)
    [✓ Theo dõi định kỳ] (emerald — for routine cases)

Step 4 — Gọi BN trường hợp nguy cấp
  BS click "Gọi BN ngay"
  Modal con: pre-filled script
    "Anh/chị Hà ơi, kết quả X-quang của anh/chị có hiện bóng tim to nhẹ.
     Tôi cần anh/chị quay lại phòng khám trong vòng 48 giờ tới để..."
  Auto-call qua VoIP / hoặc generate SMS link
  Sau call: BS log notes vào EMR BN-007

Step 5 — Đặt tái khám gấp
  Modal đặt hẹn nhanh:
    Slot khả dụng next 24-48h: hiển thị 4-5 slot
    BS chọn 1 slot + chế độ "Ưu tiên cấp 1" (BN sẽ được gọi đầu queue)
    Auto-SMS BN: "Bs. Bình đề nghị anh/chị quay lại 02/05/2026 09:00..."

Step 6 — Đánh dấu đã xử lý
  Sau khi BS chọn 1 trong 3 path:
    Card alert đổi từ "Mới" → "Đã xử lý"
    Audit log: "BS. Bình xử lý CLS X-quang BN-007 lúc ... — quyết định: tái khám 48h"

Edge cases:
  • BS đang trong giữa lượt khám BN khác → notification chỉ flash, không auto-mở modal
  • BS đang offline (giờ nghỉ) → fallback gửi cho BS trực hôm đó
  • Kết quả critical (vd: TBMMN trên CT) → escalate lên Trưởng khoa + gửi cho 2 BS cùng lúc
```

---

## Tổng hợp pattern UX dùng chung

Các pattern xuất hiện nhiều flow ở trên — dùng cho consistency:

| Pattern | Khi nào | Mô tả |
|---|---|---|
| **Confirm modal** | Action không thể undo | "Bạn xác nhận hoàn tất khám?" với 2 button |
| **Toast** | Success/info ngắn (5s) | Bottom-right, emerald cho ✓, amber cho ⚠ |
| **Banner sticky** | Cảnh báo persistent | Top of section, có nút action inline |
| **Drawer phải** | Edit nhanh không cần full page | 320-360px, slide-in từ phải, ESC đóng |
| **Auto-save draft** | Form dài (EMR, Settings) | 4s debounce, hiện "Đã lưu nháp 3s trước" |
| **Optimistic UI** | Action nhanh (mark done, archive) | Update UI ngay, rollback nếu BE fail |
| **Skeleton loader** | Load >300ms | Hiện thay thế cho spinner, giữ layout |
| **Empty state** | List trống | Illustration + microcopy + 1 primary action |
| **Sticky action footer** | Form dài | 2-3 nút ở footer, sticky bottom + có border-top |
| **Cmd palette** | Power-user search | ⌘K → search across all entities |

---

## Phụ lục: SLA target cho action

| Action | Target latency | Cách đạt |
|---|---|---|
| Cmd-K search | <100ms | Index FE local + debounce |
| Tra BHYT VSS | <2s | Cache + retry 1 lần |
| Lưu lượt khám | <500ms | Backend optimistic |
| Render màn EMR mới | <200ms TTI | Lazy load tab content |
| Print phiếu | <3s | Pre-render PDF khi mở màn |
