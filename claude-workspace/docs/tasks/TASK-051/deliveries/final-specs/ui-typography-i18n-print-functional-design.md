# Thiết Kế Chi Tiết Tính Năng: Cập Nhật UI — Typography, i18n, In Phiếu

**Dự án:** Clinic CMS — FE UI/UX Polish  
**Task:** TASK-051  
**Phiên bản:** 1.0  
**Ngày:** 2026-05-04  
**Người thực hiện:** Development Team  
**Trạng thái:** Hoàn thành  
**Tài liệu liên quan:** TASK-047 (Print Pattern Base), TASK-017 (i18n Baseline), TASK-039 (MediZen Design)

---

## Lịch sử thay đổi

| Phiên bản | Ngày | Nội dung thay đổi |
|-----------|------|-------------------|
| 1.0 | 2026-05-04 | Phiên bản đầu tiên — hoàn thành sau test cycle |

---

## Mục lục

- [1. Tổng quan tính năng](#1-tổng-quan-tính-năng)
- [2. Luồng xử lý tổng thể](#2-luồng-xử-lý-tổng-thể)
- [3. Nguồn dữ liệu đầu vào](#3-nguồn-dữ-liệu-đầu-vào)
- [4. Danh sách API](#4-danh-sách-api)
- [5. Chi tiết từng API](#5-chi-tiết-từng-api)
- [6. Cấu trúc cơ sở dữ liệu](#6-cấu-trúc-cơ-sở-dữ-liệu)
- [7. SQL tổng hợp và truy vấn dữ liệu](#7-sql-tổng-hợp-và-truy-vấn-dữ-liệu)
- [8. Quy tắc nghiệp vụ](#8-quy-tắc-nghiệp-vụ)
- [9. Xử lý lỗi](#9-xử-lý-lỗi)
- [10. Chiến lược cache](#10-chiến-lược-cache)
- [11. Ghi chú và lưu ý khi kiểm thử](#11-ghi-chú-và-lưu-ý-khi-kiểm-thử)
- [12. Quyết định khóa](#12-quyết-định-khóa)
- [13. Danh sách file thay đổi](#13-danh-sách-file-thay-đổi)

---

## 1. Tổng quan tính năng

### 1.1 Mục đích

Cập nhật giao diện người dùng (FE) của Clinic CMS với ba nội dung chính:

1. **Tăng cỡ chữ** — nâng kích cỡ font trên các trang chính từ 14px → 16px (text-sm → text-base) để cải thiện khả năng đọc cho người dùng ngành y tế phòng khám (lễ tân, dược sĩ, bác sĩ) làm việc cả ngày trên màn hình.

2. **Mặc định ngôn ngữ Việt** — đặt `fallbackLng: "vi"` và loại bỏ `navigator.language` từ detection order, sao cho app luôn hiển thị tiếng Việt khi người dùng mở lần đầu trên máy locale khác (ví dụ: EN, FR). Tôn trọng lựa chọn của người dùng đã chuyển sang EN trong app (persist via localStorage).

3. **Bốn template in mới** — mở rộng hệ thống in từ TASK-047:
   - **Phiếu khám** (VisitSlip) — A5, in từ QueueBoard  
   - **Phiếu chỉ định cận lâm sàng** (LabOrder) — A5, in từ PatientDetail  
   - **Phiếu thu** (PaymentReceipt) — POS 80mm thermal, in từ InvoiceDetail  
   - **Bệnh án tóm tắt** (MedicalSummary) — A4, in từ PatientDetail

### 1.2 Phạm vi

**Bao gồm:**
- Nâng font-size body từ 14px lên 16px (text-sm → text-base) trên 7 trang chính
- Loại bỏ browser language detection khỏi i18n config
- Bốn component printable mới + 4 modal wrapper cho mỗi template
- In browser native (window.print() + @page CSS), không ESC/POS raw commands
- Kiểm thử đầy đủ (838/838 tests pass, 0 regression)

**Không bao gồm:**
- Thay đổi root font-size CSS (tránh vỡ layout dày đặc)
- ESC/POS raw command cho máy in nhiệt (out of scope, follow-up nếu cần)
- E2E automation tests (Playwright MCP không có)
- Cập nhật README.md (internal UX polish)

### 1.3 Các bên liên quan

| Vai trò | Mô tả |
|---------|-------|
| **Người dùng cuối** | Lễ tân, dược sĩ, bác sĩ, quản trị viên — những người cần in phiếu hàng ngày |
| **Nhóm phòng khám (Clinic)** | Lợi ích: UI dễ đọc hơn, in phiếu nhanh hơn, mặc định tiếng Việt (not EN) |
| **FE Team** | Bảo trì template in, hỗ trợ tính năng in trong tương lai |
| **QA / Testing** | Kiểm thử manual typography, i18n behavior, print preview trên 3 browsers |

---

## 2. Luồng xử lý tổng thể

### 2.1 Luồng i18n (Phần A)

```
┌─────────────────────────────────────────────────────────┐
│  User opens app for first time                           │
│  (browser locale: EN, no localStorage.app.language)      │
└────────────────────┬────────────────────────────────────┘
                     │
        ┌────────────▼────────────┐
        │ i18next initialization  │
        │ detection.order:        │
        │ ["localStorage"]        │
        │ (navigator removed)     │
        └────────┬────────────────┘
                 │
        ┌────────▼────────────────────┐
        │ Check localStorage          │
        │ app.language                │
        └────────┬───────────────────┘
                 │
         ┌───────▴────────┐
         │                │
   ┌─────▼───┐      ┌─────▼──────┐
   │ Found   │      │ Not found  │
   │ (user   │      │ (first     │
   │  chose) │      │ time/empty)│
   └─────┬───┘      └─────┬──────┘
         │                │
    ┌────▼─────┐   ┌──────▼──────┐
    │ Use value│   │ Use fallback│
    │ (en/vi)  │   │ (vi)        │
    └────┬─────┘   └──────┬──────┘
         │                │
         └────────┬───────┘
                  │
         ┌────────▼─────────────────┐
         │ App renders UI in chosen │
         │ language (vi or en)       │
         └────────┬─────────────────┘
                  │
         ┌────────▼──────────────────┐
         │ User clicks language      │
         │ switcher (vi ↔ en)        │
         └────────┬──────────────────┘
                  │
         ┌────────▼──────────────────┐
         │ Save choice to localStorage│
         │ app.language = new value  │
         │ UI re-renders immediately │
         └──────────────────────────┘

Result: Fresh browser → VI. User chooses EN → EN persists. Refresh → EN.
```

### 2.2 Luồng Typography (Phần B)

```
Xác định trang có người dùng high-traffic:
Dashboard, PatientList, PatientDetail, QueueBoard, InvoiceDetail, 
PendingDispense, ARAgingReport

Cho mỗi trang:
  1. Xác định body content (text không phải badge/chip)
  2. Nâng text-xs → text-sm (12px → 14px)
  3. Nâng text-sm → text-base (14px → 16px)
  4. Giữ text-xs cho badge/chip/label (table header, status badge)
  5. Kiểm tra không vỡ layout (tránh overflow, truncate)
  6. Verify dark mode vẫn consistent

Kết quả: Body text ≥ 16px, badge/label tight, layout nguyên.
```

### 2.3 Luồng In Phiếu (Phần C)

Mỗi template in tuân theo pattern chung:

```
User action (click button/icon)
         │
         ▼
Print*Modal component opens
│  (Modal UI with preview button)
│  • Display patient/visit/payment info
│  • Show "In [template] ([size])" button
│
└─► User reviews preview
         │
         ▼
User clicks "In [template] ([size])" button
         │
         ▼
handlePrint() → window.print()
         │
         ▼
Browser print dialog opens
│  • Shows page size selector (dropdown)
│  • User confirms paper size: A5 / A4 / 80mm
│  • User selects printer destination
│  • User clicks "Print" or "Save as PDF"
│
└─► Print output (Printable* component only visible)
         │
         ▼
Success: Document printed or saved
```

#### 2.3.1 In Phiếu Khám (A5)

**Trigger:** QueueBoardPage — Printer icon on WAITING/registered visit cards

```
QueueBoardPage (visit card with print icon)
         │
         ▼
User clicks print icon
         │
         ▼
setPrintVisit(visit) → modal opens
         │
         ▼
PrintVisitSlipModal renders:
• Visit QR code, patient name, chief complaint, doctor
• "In Phiếu Khám (A5)" button at bottom
         │
         ▼
User clicks "In..." → window.print()
         │
         ▼
@page { size: A5; margin: 8mm } CSS active
         │
         ▼
PrintableVisitSlip (full width A5) renders
         │
         ▼
Browser print dialog → User confirms A5 → Print
```

#### 2.3.2 In Phiếu Chỉ Định CLS (A5)

**Trigger:** PatientDetailPage — "In phiếu chỉ định" button in header

```
PatientDetailPage header
         │
         ▼
User clicks "In phiếu chỉ định" button
         │
         ▼
PrintLabOrderModal opens:
• "Không có xét nghiệm" message if empty (awaiting TASK-041 BE)
• or List of lab orders with patient/doctor info
• "In Phiếu CLS (A5)" button
         │
         ▼
User clicks "In..." → window.print()
         │
         ▼
@page { size: A5; margin: 8mm }
         │
         ▼
PrintableLabOrder (table + header + footer) renders
         │
         ▼
Browser print dialog → A5 confirmation → Print
```

#### 2.3.3 In Phiếu Thu (POS 80mm)

**Trigger:** InvoiceDetailPage — Printer icon on each payment row

```
InvoiceDetailPage → payment table
         │
         ▼
User clicks printer icon on payment row
         │
         ▼
setPrintPaymentId(id) → modal opens
         │
         ▼
PrintPaymentReceiptModal renders:
• Payment amount (large font), method (cash/card/transfer/etc)
• Reference number, clinic logo
• "In Phiếu Thu (POS 80mm)" button
         │
         ▼
User clicks "In..." → window.print()
         │
         ▼
@page { size: 80mm auto; margin: 4mm }
         │
         ▼
PrintablePaymentReceipt (72mm content, monospace) renders
         │
         ▼
Browser print dialog → 80mm thermal width confirmation → Print
```

#### 2.3.4 In Bệnh Án Tóm Tắt (A4)

**Trigger:** PatientDetailPage — "In bệnh án" button in header

```
PatientDetailPage header
         │
         ▼
User clicks "In bệnh án" button
         │
         ▼
PrintMedicalSummaryModal opens:
• Patient demographics (name, DOB, phone, blood type, allergies)
• Chưa có lịch sử khám (if no visits)
• Chưa có đơn thuốc (if no prescriptions)
• Lab results section hidden if empty
• "In Bệnh Án (A4)" button
         │
         ▼
User clicks "In..." → window.print()
         │
         ▼
@page { size: A4; margin: 12mm }
         │
         ▼
PrintableMedicalSummary (multi-section, indigo accent) renders
         │
         ▼
Browser print dialog → A4 confirmation → Print
```

---

## 3. Nguồn dữ liệu đầu vào

**Không áp dụng** — Task này thuần về FE UI/UX. Không có message queue, file import, hay batch data ingestion. Tất cả dữ liệu đến từ:
- LocalStorage (app.language preference)
- React component props (patient, visit, payment data)
- REST API (clinic settings, patient info) — không thay đổi

---

## 4. Danh sách API

**Không áp dụng — task FE-only, không có API mới.** 

Các endpoint hiện tại được sử dụng để fetch dữ liệu từ các page đã tồn tại:
- Clinic settings (để hiển thị logo, tên, địa chỉ trong print header)
- Patient data (PatientDetailPage, QueueBoard)
- Không có POST/PUT/DELETE mới

---

## 5. Chi tiết từng API

**Không áp dụng — task FE-only, không có API mới.**

Dữ liệu từ API hiện tại được dùng để render component printable, nhưng không có thay đổi endpoint.

---

## 6. Cấu trúc cơ sở dữ liệu

**Không áp dụng** — Task này không có thay đổi schema database. Tất cả bảng và cột được sử dụng đã tồn tại từ các version trước (patient, visit, invoice, payment, lab_order, medical_summary).

---

## 7. SQL tổng hợp và truy vấn dữ liệu

**Không áp dụng — tính năng này không có logic tổng hợp dữ liệu.** Toàn bộ xử lý ở FE. Không có Kafka consumer, batch job, hay stored procedure mới.

---

## 8. Quy tắc nghiệp vụ

**Không áp dụng — task này thuần về UX/UI.** Không có quy tắc nghiệp vụ mới. Tất cả BR liên quan đến patient, visit, payment đã được định nghĩa ở các task khác (SRS).

---

## 9. Xử lý lỗi

### 9.1 Trạng thái dữ liệu rỗng (Empty States)

Task này cần xử lý graceful khi dữ liệu không đầy đủ:

#### 9.1.1 PrintableLabOrder — danh sách xét nghiệm rỗng

| Tình huống | Hành vi | Thông báo |
|-----------|--------|-----------|
| User click "In phiếu chỉ định" nhưng chưa có xét nghiệm nào (TASK-041 BE chưa merge) | Modal opens, preview khung trắng | "Không có xét nghiệm" (tiếng Việt) |
| User clicks "In..." dù rỗng | window.print() vẫn khởi động | Print output: heading "Danh sách xét nghiệm (0 chỉ định)" + empty tbody (NO crash) |

**Kế hoạch:** Khi TASK-041 BE merge với lab-orders endpoint, PatientDetailPage sẽ fetch real lab orders và wire vào modal. Hiện tại: stub data (empty array).

#### 9.1.2 PrintableMedicalSummary — visits/prescriptions/lab_results rỗng

| Tình huống | Hành vi | Thông báo |
|-----------|--------|-----------|
| Visits array is empty | Modal renders patient demographics normally | "Chưa có lịch sử khám" (section visible, graceful) |
| Prescriptions array is empty | Prescription section renders but empty | "Chưa có đơn thuốc" (section visible, graceful) |
| Lab_results array is empty | Lab results section hidden entirely (conditional render) | No message shown (section absent from DOM) |

**Kế hoạch:** When TASK-041 BE merge, PatientDetailPage will fetch visits/prescriptions/lab_results from a shared page-level query and wire real data. Currently: empty arrays, full graceful handling.

### 9.2 Window.print() user interactions

| Tình huống | Hành vi |
|-----------|--------|
| User opens print preview, then cancels | Modal stays open, preview not cleared. User can click "In..." again. |
| User opens print preview, prints to wrong paper size | Browser allows (browser responsibility). Actual print size depends on printer+browser settings. User should select correct paper in print dialog. |
| Browser print dialog blocked by popup blocker | window.print() may fail silently. User needs to allow popups in browser settings. (Not handled in code.) |

---

## 10. Chiến lược cache

**Không áp dụng** — Task này không thêm cache logic mới. 

Clinic settings API (fetch logo, clinic name) use existing cache strategy:
- Stale-time: 5 minutes
- Retry: 0 (fail fast for print UX)
- Inherited from adminSettingsApi query config (không thay đổi)

---

## 11. Ghi chú và lưu ý khi kiểm thử

### 11.1 Điểm quan trọng

1. **i18n default behavior là khó test tự động** — Clear localStorage.app.language, force-reload, và check language một lần trong quá trình manual test. Structural guarantee (no navigator + fallbackLng=vi) là solid, nhưng E2E tự động không khả dụng.

2. **Print preview chỉ là UI verification** — window.print() khởi động hộp thoại print browser. QA phải manually:
   - Verify page size dropdown shows correct size (A5/A4/80mm)
   - Verify ONLY printable content visible (no app shell, no modal chrome)
   - Cancel in print dialog or print to PDF để lưu bằng chứng

3. **Stub data (LabOrder, MedicalSummary)** — Hiện tại, PatientDetailPage passes `items: []` to LabOrder và `visits/prescriptions/lab_results: []` to MedicalSummary. Đây là intentional (awaiting TASK-041 BE). Empty-state messages render gracefully, KHÔNG crash.

4. **Browser support** — Task này target Chrome + Edge + Tauri webview (Chromium-based). Firefox/Safari out of scope.

### 11.2 Hướng dẫn kiểm thử manual

#### TC-1: i18n Default Language (Phần A)

**Pre-requisite:**
- Clear browser localStorage (`localStorage.clear()` in DevTools)
- Set browser locale to EN (simulator: check `navigator.language` = "en-US" or similar)
- Fresh reload of app

**Steps:**
1. Open app fresh
2. Verify UI displays in **Vietnamese** (not EN)
3. Look for language switcher (typically top-right or settings)
4. Click language switcher → choose EN
5. Verify UI switches to **English** immediately
6. Refresh page (Ctrl+R)
7. Verify UI still displays in **English** (persisted in localStorage)
8. Clear localStorage, refresh
9. Verify app reverts to **Vietnamese** (fallback)

**Expected result:** Fresh → VI, User chooses EN → EN persists across refresh.

#### TC-2: Typography on 7 Main Pages (Phần B)

**Setup:** Open app on desktop (1920x1080) + light mode

**Pages to check:**
1. **Dashboard** — KPI cards, section headings, loading/error text
2. **Patient List** — Search input, patient rows, empty state
3. **Patient Detail** — Tabs content, loading states, alerts section
4. **Queue Board** — Visit cards (complaint text, time), empty state message
5. **Invoice Detail** — Line items, payment section, totals
6. **Pending Dispense** — Modal grid, auto-refresh header, section headings
7. **AR Aging Report** — Summary cards, table, chart headings

**For each page:**
- Visual inspection: body text appears **readable, not cramped**
- Measure (DevTools): body content is `text-base` (16px) or larger
- Badge/chip/table-header: remain `text-xs` (12px) — tight, appropriate for secondary content
- NO layout breakage: sections don't overflow, truncate unexpectedly, or collapse
- Dark mode: same readability (color contrast OK)

**Expected:** All 7 pages visually balanced, readable, no regression.

#### TC-3: Print VisitSlip — A5 from QueueBoard (Phần C-1)

**Setup:** QueueBoard page with at least one visit in WAITING or registered state

**Steps:**
1. Locate visit card with printer icon (rightmost icon on card)
2. Click printer icon
3. **PrintVisitSlipModal** opens (full-screen modal with preview)
   - Verify modal title: "In Phiếu Khám"
   - Verify content: Visit QR code, patient name, chief complaint, doctor
   - Verify preview button text: "In Phiếu Khám (A5)"
4. Click "In Phiếu Khám (A5)" button
5. **Browser print dialog** appears
   - In "Paper size" dropdown, verify **A5** is available and selectable
   - (Optional) Select A5, then click "Preview" to see print layout
   - Verify print preview shows: QR code + patient info + doctor (NO app shell, NO modal chrome)
6. User can:
   - Click "Print" to print to physical printer
   - Click "Save as PDF" to save file
   - Click "Cancel" to close dialog
7. Modal remains open if user cancelled

**Expected:** Modal opens, print dialog shows A5 size, preview shows clean phiếu khám layout.

#### TC-4: Print LabOrder — A5 from PatientDetail (Phần C-2)

**Setup:** PatientDetailPage of any patient

**Steps:**
1. Scroll to header
2. Look for button: "In phiếu chỉ định" (or similar text)
3. Click button
4. **PrintLabOrderModal** opens
   - If no lab orders (stub): shows "Không có xét nghiệm" message
   - If data available: shows table of lab orders
   - Button: "In Phiếu CLS (A5)"
5. Click "In Phiếu CLS (A5)"
6. **Browser print dialog** appears
   - Verify paper size = **A5**
   - Print preview: table header + rows (or empty tbody if no data) + patient/doctor info at top
7. User prints or saves as PDF

**Expected:** Modal opens, empty state graceful, print dialog shows A5, layout clean.

#### TC-5: Print PaymentReceipt — POS 80mm from InvoiceDetail (Phần C-3)

**Setup:** InvoiceDetailPage with at least one payment record

**Steps:**
1. Scroll to payments section (table of paid/unpaid payments)
2. Find payment row → locate printer icon (right column)
3. Click printer icon
4. **PrintPaymentReceiptModal** opens
   - Verify content: large payment amount, payment method (cash/card/transfer/etc), reference #, clinic logo
   - Button: "In Phiếu Thu (POS 80mm)"
5. Click "In Phiếu Thu (POS 80mm)"
6. **Browser print dialog** appears
   - Paper size: **80mm** (custom size, may appear as "Custom" or "80mm x auto")
   - Print preview: monospace font, 72mm content width, divider lines, centered amount, payment method label
   - NO excess horizontal scrolling (width ≤ 80mm)
7. User prints or saves as PDF

**Expected:** Modal opens with payment detail, print dialog shows 80mm size, preview shows receipt-like layout with correct width.

#### TC-6: Print MedicalSummary — A4 from PatientDetail (Phần C-4)

**Setup:** PatientDetailPage of any patient

**Steps:**
1. Scroll to header
2. Look for button: "In bệnh án" (or similar)
3. Click button
4. **PrintMedicalSummaryModal** opens
   - Patient demographics always visible: name, DOB, phone, blood type, allergy, chronic conditions
   - Empty-state sections:
     - Visits: "Chưa có lịch sử khám"
     - Prescriptions: "Chưa có đơn thuốc"
     - Lab results: section hidden (no "Chưa có..." message — just absent)
   - Button: "In Bệnh Án (A4)"
5. Click "In Bệnh Án (A4)"
6. **Browser print dialog** appears
   - Paper size: **A4**
   - Print preview:
     - Header with clinic logo + name + address
     - Patient demographics section with indigo accent border
     - Alerts box (if allergies or chronic conditions)
     - Visits section (empty or with data)
     - Prescriptions section (empty or with data)
     - Lab results section (hidden if empty, otherwise visible with data)
     - Footer with print date
7. User prints or saves as PDF

**Expected:** Modal opens, all empty states graceful, print dialog shows A4, layout multi-section, readable.

### 11.3 Hạn chế hiện tại

1. **Modal unit tests** — 4 modal wrapper components (`PrintVisitSlipModal`, `PrintLabOrderModal`, `PrintPaymentReceiptModal`, `PrintMedicalSummaryModal`) not unit-tested. `window.print()` confirmed via code inspection, not automated test. This is a MINOR gap (modals are thin wrappers ~140 LOC each). E2E automation not available (Playwright MCP not configured).

2. **LabOrder data wiring** — Currently opens with `items: []`. Real data wiring depends on TASK-041 BE merge (lab-orders endpoint + LabOrdersTab component on PatientDetailPage). Intentional stub for now.

3. **MedicalSummary data wiring** — Currently passes `visits: []`, `prescriptions: []`, `lab_results: []` because these arrays are only fetched inside respective sub-tabs on PatientDetailPage, not at page level. Full integration will happen post-TASK-041 BE when shared query exists.

4. **Print CSS specificity** — All 4 printable components use `@media print { body > *:not(#[root-id]) { display: none } }` to hide app shell. This works for single modal open, but theoretically fails if two print modals were open simultaneously (each hides the other's root). Current UI prevents this (one modal per action), so not an issue now. Optional refactor to `data-print-root` attribute if multi-modal printing needed in future.

5. **Browser support** — Only Chrome + Edge + Tauri webview (Chromium). Firefox/Safari not tested. `window.print()` is standard, but CSS `@page { size: ... }` support varies by browser.

### 11.4 Dữ liệu kiểm thử

| Kịch bản | Giá trị đầu vào | Kết quả kỳ vọng |
|---------|----------------|----------------|
| Fresh app open, browser locale EN | No localStorage | UI in Vietnamese |
| User chooses EN in language picker | Click switcher → EN | UI in English, localStorage saved |
| Refresh page | No localStorage clear | UI remains English (persisted) |
| QueueBoard with 1 visit (WAITING) | Click print icon | PrintVisitSlipModal opens, A5 size available in print dialog |
| PatientDetail with no lab orders | Click "In phiếu chỉ định" | Modal shows "Không có xét nghiệm", A5 printable renders empty table |
| InvoiceDetail with 1 payment | Click printer icon on row | PrintPaymentReceiptModal opens, 80mm size in print dialog |
| PatientDetail with patient data | Click "In bệnh án" | Modal shows demographics, empty-state sections graceful, A4 printable renders cleanly |
| Print dialog opened, user cancels | Click "Cancel" in dialog | Dialog closes, modal remains open |
| Print dialog, user saves as PDF | Select A5 / A4 / 80mm → Save | PDF file created with correct page size |

### 11.5 Hướng phát triển

- **Print unit tests for modals** — Add unit tests for 4 modal wrappers (handlePrint, modal open/close logic, clinic settings fetch). Future task.
- **Multi-modal printing** — If future feature needs concurrent print previews, refactor to use `data-print-root` attribute instead of ID-based hiding.
- **ESC/POS thermal commands** — If receipt printers need raw ESC/POS codes (not CSS-based), create separate task with `tauri-plugin-printer` or equivalent. Out of scope now.
- **LabOrder real data wiring** — Depends on TASK-041 BE merge and LabOrdersTab component creation. Post-merge follow-up.
- **MedicalSummary shared query** — When PatientDetailPage refactors to fetch visits+prescriptions+lab_results at page level (not per-tab), update MedicalSummary wiring. Post-TASK-041 follow-up.

---

## 12. Quyết định khóa

| Quyết định | Giá trị | Lý do |
|---|---|---|
| In chiến lược POS 80mm | `window.print()` + `@page { size: 80mm auto; }` CSS | Nhất quán với TASK-047 (A4/A5 hóa đơn/đơn thuốc cũng dùng browser native print). Không dùng Tauri printer plugin / ESC-POS raw command. |
| ESC/POS raw | OUT OF SCOPE | Nếu follow-up cần, mở task riêng. |
| i18n default | `lng: "vi"` + `detection.order: ["localStorage"]` (loại bỏ navigator) | User báo: máy locale EN vẫn hiển thị EN dù fallbackLng=vi. Giải pháp: loại bỏ navigator detection — tôn trọng explicit user choice via localStorage `app.language`. |
| Typography baseline | Tailwind default 16px body giữ nguyên; audit + nâng `text-xs`/`text-sm` ở 7 page chính lên 1 bước (xs→sm, sm→base) | Không thay đổi root font-size tránh vỡ layout dày đặc. Nâng từng usage an toàn hơn. |
| Branch start point | `git stash --include-untracked` → checkout main → pull → create feature branch | WIP branch `feature/TASK-047-print-receipts` có 10 files modified, không liên quan TASK-051. Stash để user xử lý sau, KHÔNG `stash pop`. |
| Repo scope | `clinic-cms-web` ONLY | Không touch `clinic-cms`, `clinic-cms-merge`, `clinic-cms-landing`. Không touch BE. |
| Phasing | Phase 1 (typography + i18n) + Phase 2 (4 print templates mới) — implement cả 2 trong 1 PR | User chọn option C = full scope. |

---

## 13. Danh sách file thay đổi

Tổng cộng **21 file** được thay đổi/tạo mới:

### Phần A — i18n (1 file)
- `src/lib/i18n.ts` — Loại bỏ `"navigator"` từ `detection.order`, giữ `["localStorage"]` only

### Phần B — Typography (7 files)
- `src/pages/dashboard/MainDashboardPage.tsx` — 8 className swaps (text-xs→text-sm, text-sm→text-base)
- `src/pages/patients/PatientDetailPage.tsx` — Typography swaps + duplicate TABS fix
- `src/pages/patients/PatientListPage.tsx` — 5 className swaps
- `src/pages/queue/QueueBoardPage.tsx` — 5 className swaps + onPrint prop
- `src/pages/billing/InvoiceDetailPage.tsx` — Typography swaps + print wiring
- `src/pages/pharmacy/PendingDispensePage.tsx` — 7 className swaps
- `src/pages/reports/ARAgingReportPage.tsx` — 7 className swaps

### Phần C — Print Templates & Types (8 files)
- `src/components/billing/printTypes.ts` — Shared interfaces (ClinicInfo, PatientInfo)
- `src/components/visit/PrintableVisitSlip.tsx` — A5 phiếu khám component
- `src/components/visit/PrintVisitSlipModal.tsx` — Modal wrapper + window.print()
- `src/components/lab/PrintableLabOrder.tsx` — A5 phiếu CLS component
- `src/components/lab/PrintLabOrderModal.tsx` — Modal wrapper + window.print()
- `src/components/billing/PrintablePaymentReceipt.tsx` — POS 80mm phiếu thu component
- `src/components/billing/PrintPaymentReceiptModal.tsx` — Modal wrapper + window.print()
- `src/components/visit/PrintableMedicalSummary.tsx` — A4 bệnh án tóm tắt component

### Phần C — Test Files (5 files)
- `src/tests/visit/PrintableVisitSlip.test.tsx` — 11 tests
- `src/tests/lab/PrintableLabOrder.test.tsx` — 12 tests
- `src/tests/billing/PrintablePaymentReceipt.test.tsx` — 13 tests
- `src/tests/visit/PrintableMedicalSummary.test.tsx` — 16 tests
- `src/tests/lib/i18n-default-language.test.ts` — 8 tests (regression test by test agent)

**Tóm tắt:** 1 i18n + 7 typography + 8 print + 5 test = 21 files

---

**Phê duyệt**

| Vai trò | Họ tên | Ngày | Ghi chú |
|---------|--------|------|--------|
| Code Review | Code Review Agent | 2026-05-04 | APPROVED — no major issues, 4 MINOR gaps documented |
| Testing | Test Agent | 2026-05-04 | APPROVED — 838/838 tests pass, 0 new errors, all smoke checks pass |
| Documentation | Documentation Agent | 2026-05-04 | Completed |
