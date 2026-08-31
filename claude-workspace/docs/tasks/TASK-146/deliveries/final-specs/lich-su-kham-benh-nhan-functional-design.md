# Thiết Kế Chi Tiết: Lịch sử khám hiển thị đầy đủ

**Task:** TASK-146  
**Phiên bản:** 1.0  
**Ngày:** 2026-09-01  
**Trạng thái:** Đã duyệt  
**Tài liệu liên quan:** TASK-145 (hủy/hoàn hóa đơn + hủy đơn), TASK-142 (chặn cấp phát đơn chưa duyệt)

---

## Mục lục

1. [Tổng quan](#1-tổng-quan)
2. [Các tab trong hồ sơ bệnh nhân](#2-các-tab-trong-hồ-sơ-bệnh-nhân)
3. [Danh sách API](#3-danh-sách-api)
4. [Chi tiết từng API](#4-chi-tiết-từng-api)
5. [Quy tắc hiển thị dữ liệu](#5-quy-tắc-hiển-thị-dữ-liệu)
6. [Xử lý lỗi](#6-xử-lỗi)
7. [Ghi chú kiểm thử](#7-ghi-chú-kiểm-thử)

---

## 1. Tổng quan

### 1.1 Mục đích

Sau khi cho phép hủy đơn thuốc (TASK-145) và hoàn/hủy hóa đơn (TASK-145), lịch sử khám bệnh của bệnh nhân phải kể lại được toàn bộ câu chuyện:

- Bác sĩ kê đơn gì
- Đơn thuốc nào đã bị hủy, lý do hủy, thời điểm hủy
- Hóa đơn nào đã bị hủy/hoàn tiền, lý do, thời điểm
- Đơn/hóa đơn thay thế là gì

Từ trước, tab **Đơn thuốc** trong hồ sơ bệnh nhân không hiển thị bất kỳ đơn nào đã hủy, và tab **Hóa đơn** thiếu thông tin về lý do hủy/hoàn tiền. Tính năng này sửa lỗi này và cho phép bác sĩ/nhân viên tiếp nhận truy vết được lịch sử đầy đủ.

### 1.2 Phạm vi

**Bao gồm:**
- Tab Lượt khám (VisitsTab): hiển thị tất cả lượt khám, hỗ trợ phân trang khi bệnh nhân khám lâu năm
- Tab Đơn thuốc (PrescriptionsTab): hiển thị tất cả đơn (kể cả đã hủy), sắp theo thời gian, kèm lý do hủy/thời điểm
- Tab Hóa đơn (InvoicesTab): hiển thị tất cả hóa đơn (kể cả đã hủy/hoàn tiền), kèm lý do hủy/hoàn tiền
- Phân biệt trực quan giữa bản ghi đã hủy vs còn hiệu lực
- Phân trang "Xem thêm" với kích thước 50 bản ghi mỗi trang, không bị cắt im lặng

**Không bao gồm:**
- Tab Sinh hiệu (VitalsTab): giữ nguyên (là biểu đồ trend 5 lượt gần nhất, không phải lịch sử đầy đủ)
- Hiển thị tên người hủy đơn/hóa đơn (dành cho task follow-up — dữ liệu actor đã có, nhưng hiển thị tên cần quyền `user.manage`)
- Hủy lượt khám ở mức tổng thể (chỉ đơn thuốc/hóa đơn trong lượt được hủy)

### 1.3 Các bên liên quan

| Vai trò | Mô tả |
|---------|-------|
| **Bác sĩ / Nhân viên tiếp nhận** | Sử dụng để truy vét lịch sử bệnh nhân khi điều tra sai sót |
| **Nhà thuốc** | Xem lịch sử đơn hủy của bệnh nhân |
| **Quản lý** | Kiểm tra lịch sử khám và điều chỉnh |

---

## 2. Các tab trong hồ sơ bệnh nhân

### 2.1 Tab Lượt khám (VisitsTab)

#### Các cột hiển thị

| Cột | Nội dung | Ghi chú |
|-----|---------|--------|
| **Số thứ tự** | Thứ tự từ trên xuống (lượt gần nhất ở trên) | — |
| **Ngày khám** | Ngày-Tháng-Năm | Định dạng: `DD/MM/YYYY` |
| **Bác sĩ** | Tên bác sĩ khám | Nếu không có, hiển thị "—" |
| **Trạng thái** | Trạng thái lượt khám | Có thể là "Hoàn thành", "Đã huỷ", v.v. |

#### Phân trang

- **Kích thước trang:** 50 lượt khám mỗi trang
- **Nút "Xem thêm":** Xuất hiện khi còn dữ liệu chưa hiển thị, ẩn khi đã hiển thị hết
- **Cách hoạt động:** 
  - Nhấn "Xem thêm" sẽ tải 50 lượt khám tiếp theo
  - Các lượt khám đã tải vẫn ở trên màn hình (không xóa)
  - Tiếp tục nhấn cho đến khi không còn nút "Xem thêm"

#### Liên kết

Mỗi hàng lượt khám có thể nhấn vào để xem chi tiết lượt khám (hoặc hiển thị các đơn thuốc/hóa đơn của lượt đó).

---

### 2.2 Tab Đơn thuốc (PrescriptionsTab)

#### Các cột hiển thị

| Cột | Nội dung | Ghi chú |
|-----|---------|--------|
| **Lượt khám** | Ngày khám | Link sang lượt khám |
| **Số đơn** | Mã đơn thuốc | —  |
| **Ngày kê** | Ngày-Giờ kê đơn | Định dạng: `DD/MM/YYYY HH:MM` |
| **Loại thuốc** | Số lượng loại thuốc trong đơn | Ví dụ: 3 loại thuốc |
| **Trạng thái** | Trạng thái đơn | `Chưa gửi`, `Đang chờ`, `Đã huỷ` |
| **In** | Nút in đơn | Chỉ hiển thị khi đơn **không** bị hủy |

#### Hiển thị đơn đã hủy

Khi một lượt khám có nhiều đơn (ví dụ: 1 đơn gốc + 1 đơn hủy + 1 đơn thay thế):

1. **Tất cả đơn đều hiển thị**, sắp theo thời gian kê (từ cũ đến mới)
2. **Đơn hủy:**
   - Cột **Số đơn / Ngày kê / Loại thuốc**: hiển thị bị gạch ngang + mờ nhạt (opacity ~50%)
   - Cột **Trạng thái**: **KHÔNG** gạch ngang, hiển thị đầy đủ `Đã huỷ`
   - Dòng mới ngay dưới **Trạng thái**: ghi lý do hủy + thời điểm hủy
     - Ví dụ: `"Huỷ lúc 2026-09-01 10:30 — Kê sai loại thuốc"`
     - Màu chữ: **đỏ**, **KHÔNG** gạch ngang, đọc rõ ràng
   - Nút In: ẩn (không hiển thị)
3. **Đơn còn hiệu lực**: hiển thị bình thường, đầy đủ màu sắc

#### Phân trang

- **Kích thước:** 50 lượt khám mỗi trang (không phải 50 đơn — vì đơn là con của lượt)
- **Nút "Xem thêm":** Hiển thị khi còn lượt khám chưa tải
- **Trường hợp đặc biệt:** Nếu 50 lượt gần nhất **không có đơn nào** (ví dụ bệnh nhân khám nhưng không kê đơn), nút "Xem thêm" vẫn hiển thị để có thể xem các lượt khám cũ hơn

#### Liên kết

Mỗi đơn thuốc có thể nhấn để xem chi tiết đơn (hoặc in nếu không bị hủy).

---

### 2.3 Tab Hóa đơn (InvoicesTab)

#### Các cột hiển thị

| Cột | Nội dung | Ghi chú |
|-----|---------|--------|
| **Số hóa đơn** | Mã hóa đơn | Link sang trang chi tiết hóa đơn |
| **Ngày tạo** | Ngày-Giờ tạo hóa đơn | Định dạng: `DD/MM/YYYY HH:MM` |
| **Tổng tiền** | Số tiền cần thanh toán | Định dạng tiền tệ (VND) |
| **Trạng thái** | Trạng thái hóa đơn | `Nháp`, `Đã thanh toán`, `Đã huỷ`, `Đã hoàn tiền` |
| **In** | Nút in hóa đơn | Chỉ hiển thị khi hóa đơn **không** bị hủy |

#### Hiển thị hóa đơn đã hủy/hoàn tiền

Khi hóa đơn bị hủy hoặc hoàn tiền:

1. **Số hóa đơn / Ngày tạo / Tổng tiền**: hiển thị bị gạch ngang + mờ nhạt (opacity ~50%)
2. **Trạng thái**: **KHÔNG** gạch ngang, hiển thị đầy đủ `Đã huỷ` hoặc `Đã hoàn tiền`
3. **Dòng lý do hủy/hoàn tiền** ngay dưới trạng thái:
   - Ví dụ: `"Huỷ lúc 2026-09-01 14:15 — Khách hủy đơn"`
   - Hoặc: `"Hoàn tiền lúc 2026-09-01 15:00 — Trả lại vì lỗi tính tiền"`
   - Màu chữ: **đỏ**, **KHÔNG** gạch ngang, đọc rõ ràng (tương tự tab Đơn thuốc)
4. **Nút In**: ẩn (không hiển thị)

#### Phân trang

- **Kích thước:** 50 hóa đơn mỗi trang
- **Nút "Xem thêm":** Hiển thị khi còn hóa đơn chưa tải
- **Ngưỡng:** Tính toán dựa trên tổng số hóa đơn của bệnh nhân này, không phải toàn clinic

#### Liên kết

Nhấn vào số hóa đơn để mở trang chi tiết hóa đơn (xem nội dung, từng dòng hàng, lý do hủy, v.v.).

---

## 3. Danh sách API

Tất cả API yêu cầu xác thực qua header `Authorization: Bearer <jwt_token>` và thuộc phạm vi tenant (tự động lọc theo `clinic_id` từ token).

| Endpoint | Phương thức | Mục đích |
|----------|-----------|---------|
| `GET /api/v1/visits` | GET | Danh sách lượt khám của bệnh nhân |
| `GET /api/v1/visits/{visit_id}/prescriptions` | GET | Danh sách đơn thuốc của một lượt khám (bao gồm cả đã hủy) |
| `GET /api/v1/invoices` | GET | Danh sách hóa đơn của bệnh nhân |

---

## 4. Chi tiết từng API

### 4.1 `GET /api/v1/visits`

#### Mục đích

Lấy danh sách lượt khám của bệnh nhân, hỗ trợ phân trang.

#### Tham số truy vấn

| Tham số | Kiểu | Bắt buộc | Mô tả | Ví dụ |
|---------|------|---------|-------|-------|
| `patient_id` | UUID | Có | ID bệnh nhân | `550e8400-e29b-41d4-a716-446655440000` |
| `limit` | Integer | Không | Số bản ghi mỗi trang (mặc định 50, tối đa 500) | `50` |
| `skip` | Integer | Không | Số bản ghi bỏ qua từ đầu (mặc định 0) | `0`, `50`, `100` |

#### Cách gọi

```
GET /api/v1/visits?patient_id=550e8400-e29b-41d4-a716-446655440000&limit=50&skip=0
Authorization: Bearer <jwt_token>
```

#### Response (HTTP 200)

```json
{
  "items": [
    {
      "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "visit_number": "20260901-001",
      "visit_date": "2026-09-01",
      "status": "completed",
      "doctor_id": "f1f2f3f4-f5f6-f7f8-f9fa-fbfcfdfe0001",
      "assigned_doctor_id": "f1f2f3f4-f5f6-f7f8-f9fa-fbfcfdfe0002",
      "patient_id": "550e8400-e29b-41d4-a716-446655440000",
      "created_at": "2026-09-01T08:00:00Z"
    },
    {
      "id": "b2c3d4e5-f6f7-8901-bcde-f12345678901",
      "visit_number": "20260901-002",
      "visit_date": "2026-09-01",
      "status": "completed",
      "doctor_id": null,
      "assigned_doctor_id": "f1f2f3f4-f5f6-f7f8-f9fa-fbfcfdfe0001",
      "patient_id": "550e8400-e29b-41d4-a716-446655440000",
      "created_at": "2026-09-01T09:30:00Z"
    }
  ],
  "total": 25,
  "limit": 50,
  "skip": 0
}
```

#### Mô tả các trường response

| Trường | Kiểu | Mô tả |
|--------|------|-------|
| `items` | Array | Danh sách lượt khám |
| `items[].id` | UUID | Mã lượt khám |
| `items[].visit_number` | String | Số hiệu lượt khám (định dạng: `YYYYMMDD-NNN`) |
| `items[].visit_date` | Date | Ngày khám (định dạng: `YYYY-MM-DD`) |
| `items[].status` | String | Trạng thái lượt khám |
| `items[].doctor_id` | UUID \| null | ID bác sĩ khám (nếu có) |
| `items[].assigned_doctor_id` | UUID \| null | ID bác sĩ được giao (nếu không có doctor_id) |
| `total` | Integer | Tổng số lượt khám của bệnh nhân |
| `limit` | Integer | Kích thước trang được yêu cầu |
| `skip` | Integer | Số bản ghi bỏ qua |

#### Xử lý phân trang

- **Trang 1:** `skip=0, limit=50` → nhận items [0-49], `total=100`
- **Trang 2:** `skip=50, limit=50` → nhận items [50-99], `total=100` (giữ nguyên)
- **Trang 3:** `skip=100, limit=50` → nhận items [100-150], nhưng chỉ 50 item được trả về, `total=100` (kết thúc)

**Quy tắc kết thúc:** Khi `skip + items.length >= total`, nút "Xem thêm" ẩn.

---

### 4.2 `GET /api/v1/visits/{visit_id}/prescriptions`

#### Mục đích

Lấy **tất cả** đơn thuốc của một lượt khám, bao gồm cả những đơn đã hủy. Dùng để hiển thị lịch sử.

**Lưu ý:** Có một hàm tương tự `getVisitPrescription` (singular, trả về 1 đơn duy nhất) được dùng bởi màn khám bác sĩ. Hai hàm này **phục vụ mục đích khác nhau** và không được nhầm lẫn.

#### Tham số đường dẫn

| Tham số | Kiểu | Mô tả |
|---------|------|-------|
| `visit_id` | UUID | ID lượt khám |

#### Cách gọi

```
GET /api/v1/visits/a1b2c3d4-e5f6-7890-abcd-ef1234567890/prescriptions
Authorization: Bearer <jwt_token>
```

#### Response (HTTP 200)

```json
{
  "items": [
    {
      "id": "rx-001",
      "visit_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "status": "cancelled",
      "cancelled_at": "2026-09-01T10:15:00Z",
      "cancel_reason": "Kê sai loại thuốc",
      "prescribed_at": "2026-09-01T10:00:00Z",
      "line_items": [
        {
          "id": "rxl-001",
          "medicine_name": "Paracetamol 500mg",
          "quantity": 10,
          "dosage": "1 viên x 3 lần/ngày"
        }
      ]
    },
    {
      "id": "rx-002",
      "visit_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "status": "pending",
      "cancelled_at": null,
      "cancel_reason": null,
      "prescribed_at": "2026-09-01T10:20:00Z",
      "line_items": [
        {
          "id": "rxl-002",
          "medicine_name": "Ibuprofen 200mg",
          "quantity": 20,
          "dosage": "1 viên x 2 lần/ngày"
        }
      ]
    }
  ],
  "total": 2,
  "visit_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

#### Mô tả các trường

| Trường | Mô tả |
|--------|-------|
| `items[].id` | Mã đơn thuốc |
| `items[].status` | Trạng thái: `draft`, `pending`, `cancelled` |
| `items[].cancelled_at` | Thời điểm hủy (null nếu chưa hủy) |
| `items[].cancel_reason` | Lý do hủy (null nếu chưa hủy) |
| `items[].prescribed_at` | Thời điểm kê đơn |
| `items[].line_items` | Danh sách thuốc trong đơn |
| `total` | Tổng số đơn của lượt khám (không phân trang) |

#### Xử lý trên UI

- **Frontend lọc bỏ `draft`:** Đơn có status `draft` **KHÔNG** hiển thị trong tab "Lịch sử Đơn thuốc" (D-1 quyết định)
  - Lý do: `draft` là đơn chưa được kê cho bệnh nhân, chỉ là bản nháp; nó không là một sự kiện lâm sàng cần truy vết
- **Hiển thị `cancelled`:** Tất cả đơn có status `cancelled` **ĐỀU** hiển thị, kèm `cancelled_at` và `cancel_reason`

---

### 4.3 `GET /api/v1/invoices`

#### Mục đích

Lấy danh sách hóa đơn của bệnh nhân, bao gồm cả những hóa đơn đã hủy/hoàn tiền.

#### Tham số truy vấn

| Tham số | Kiểu | Bắt buộc | Mô tả | Ví dụ |
|---------|------|---------|-------|-------|
| `patient_id` | UUID | Có | ID bệnh nhân | `550e8400-e29b-41d4-a716-446655440000` |
| `limit` | Integer | Không | Số bản ghi mỗi trang (mặc định 50, tối đa 200) | `50` |
| `offset` | Integer | Không | Số bản ghi bỏ qua từ đầu (mặc định 0) | `0`, `50` |

**Lưu ý:** Từ trước, `patient_id` được gửi nhưng bị bỏ qua ở backend, nên tab này hiển thị hóa đơn của **toàn clinic** thay vì chỉ bệnh nhân. **Đã sửa** (FIX-2).

#### Cách gọi

```
GET /api/v1/invoices?patient_id=550e8400-e29b-41d4-a716-446655440000&limit=50&offset=0
Authorization: Bearer <jwt_token>
```

#### Response (HTTP 200)

```json
{
  "items": [
    {
      "id": "inv-001",
      "invoice_number": "INV-20260901-001",
      "visit_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "patient_id": "550e8400-e29b-41d4-a716-446655440000",
      "grand_total": 500000,
      "paid_total": 500000,
      "status": "paid",
      "voided_at": null,
      "void_reason": null,
      "refunded_at": null,
      "refund_reason": null,
      "created_at": "2026-09-01T10:00:00Z"
    },
    {
      "id": "inv-002",
      "invoice_number": "INV-20260901-002",
      "visit_id": "b2c3d4e5-f6f7-8901-bcde-f12345678901",
      "patient_id": "550e8400-e29b-41d4-a716-446655440000",
      "grand_total": 750000,
      "paid_total": 0,
      "status": "voided",
      "voided_at": "2026-09-01T11:00:00Z",
      "void_reason": "Phát hành nhầm — sẽ phát hành lại",
      "refunded_at": null,
      "refund_reason": null,
      "created_at": "2026-09-01T10:30:00Z"
    },
    {
      "id": "inv-003",
      "invoice_number": "INV-20260901-003",
      "visit_id": "b2c3d4e5-f6f7-8901-bcde-f12345678901",
      "patient_id": "550e8400-e29b-41d4-a716-446655440000",
      "grand_total": 750000,
      "paid_total": 750000,
      "status": "refunded",
      "voided_at": null,
      "void_reason": null,
      "refunded_at": "2026-09-01T12:00:00Z",
      "refund_reason": "Khách yêu cầu trả lại",
      "created_at": "2026-09-01T10:45:00Z"
    }
  ],
  "total": 3,
  "limit": 50,
  "offset": 0
}
```

#### Mô tả các trường bổ sung

| Trường | Kiểu | Mô tả |
|--------|------|-------|
| `voided_at` | DateTime \| null | Thời điểm hủy hóa đơn |
| `void_reason` | String \| null | Lý do hủy |
| `refunded_at` | DateTime \| null | Thời điểm hoàn tiền |
| `refund_reason` | String \| null | Lý do hoàn tiền |

#### Status hóa đơn

| Status | Ý nghĩa |
|--------|---------|
| `draft` | Nháp, chưa phát hành |
| `issued` | Đã phát hành, chờ thanh toán |
| `paid` | Đã thanh toán |
| `voided` | Đã hủy (hóa đơn không hợp lệ) |
| `refunded` | Đã hoàn tiền (khách đổi ý hoặc trả lại) |

---

## 5. Quy tắc hiển thị dữ liệu

### 5.1 Phân biệt thị giác: Bản ghi đã hủy vs còn hiệu lực

Cả tab **Đơn thuốc** và **Hóa đơn** dùng **cùng một ngôn ngữ thị giác** (D-2 quyết định):

**Đơn/Hóa đơn bị hủy/hoàn tiền:**

| Phần tử | Kiểu dáng |
|--------|---------|
| Số đơn / Số hoá đơn | Gạch ngang (`line-through`) + mờ (`opacity: 0.5`) |
| Ngày kê / Ngày tạo | Gạch ngang (`line-through`) + mờ (`opacity: 0.5`) |
| Tổng tiền / Số lượng thuốc | Gạch ngang (`line-through`) + mờ (`opacity: 0.5`) |
| **Trạng thái** | **KHÔNG** gạch ngang, đầy đủ opaque, màu đỏ |
| **Lý do hủy/hoàn tiền** | **KHÔNG** gạch ngang, đầy đủ opaque, **màu đỏ** (`text-red-600`), **bold** (`font-medium`) |

**Độ tương phản (WCAG AA):**
- Light theme: `text-red-600` (`#dc2626`) trên `bg-white` = **4.83:1** ✓
- Dark theme: `dark:text-red-400` (`#f87171`) trên `dark:bg-gray-800` (`#1f2937`) = **5.29:1** ✓

### 5.2 Quy tắc `draft` vs `cancelled`

**Quyết định D-1:**

| Status | Hiển thị trong tab lịch sử? | Lý do |
|--------|---------------------------|-------|
| `draft` | **KHÔNG** | Đơn `draft` chưa bao giờ gửi cho nhà thuốc / bệnh nhân, chỉ là bản nháp. Nó không phản ánh sự kiện lâm sàng thực sự xảy ra. Hiển thị sẽ gây nhiễu. |
| `cancelled` | **CÓ** | Đơn `cancelled` ghi lại một sự kiện có thật (đã kê → phát hiện lỗi → hủy). Thông tin này quan trọng cho truy vết lâm sàng. |
| `pending` / `dispensed` | **CÓ** | Các đơn này là bản ghi có hiệu lực, cần hiển thị đầy đủ |

### 5.3 Loại thuốc "In"

**Bản ghi bị hủy:**
- Nút "In" ẩn (không hiển thị), không thể in được đơn/hóa đơn đã hủy
- Lý do: một tài liệu đã hủy không nên được phát hành

**Bản ghi còn hiệu lực:**
- Nút "In" hiển thị, có thể in bình thường

---

## 6. Xử lý lỗi

### 6.1 Lỗi phổ biến

| HTTP Code | Lỗi | Nguyên nhân | Xử lý |
|-----------|-----|-----------|--------|
| 400 | `INVALID_PATIENT_ID` | ID bệnh nhân không phải UUID hợp lệ | Hiển thị thông báo lỗi, yêu cầu nhập lại |
| 404 | `PATIENT_NOT_FOUND` | ID bệnh nhân không tồn tại | Hiển thị "Bệnh nhân không tìm thấy" |
| 422 | `INVALID_UUID` | ID không hợp lệ hoặc loại không khớp | Kiểm tra dữ liệu gửi đi |
| 403 | `PERMISSION_DENIED` | Người dùng không có quyền xem bệnh nhân này | Hiển thị "Không có quyền truy cập" |
| 500 | `INTERNAL_SERVER_ERROR` | Lỗi server | Ghi log, thông báo người dùng "Đã xảy ra lỗi. Vui lòng thử lại" |

### 6.2 Xử lý khi gọi API bị lỗi

**Trên Frontend:**

1. **Lỗi kết nối (ECONNREFUSED, ENOTFOUND):** Hiển thị "Mất kết nối với server. Vui lòng kiểm tra kết nối mạng và thử lại."
2. **Timeout:** Hiển thị "Yêu cầu quá lâu. Vui lòng thử lại."
3. **Lỗi 4xx / 5xx:** Hiển thị pesan lỗi từ response hoặc thông báo mặc định

**Tab nào không tải được:**

- Hiển thị trạng thái lỗi cho tab đó, không ảnh hưởng đến các tab khác
- Có nút "Thử lại" để tải lại dữ liệu

---

## 7. Ghi chú kiểm thử

### 7.1 Kịch bản kiểm thử chính

1. **Bệnh nhân có 1 đơn hủy + 1 đơn thay thế:**
   - Mở tab Đơn thuốc → Phải thấy cả 2 đơn
   - Đơn hủy phải gạch ngang, hiển thị lý do + thời điểm hủy
   - Đơn mới phải đầy đủ màu sắc

2. **Bệnh nhân có hóa đơn hủy + hóa đơn phát hành lại:**
   - Mở tab Hóa đơn → Phải thấy cả 2 hóa đơn
   - Hóa đơn hủy phải gạch ngang, hiển thị lý do + thời điểm hủy
   - Hóa đơn mới phải đầy đủ màu sắc

3. **Bệnh nhân khám 55+ lần:**
   - Tab Lượt khám / Đơn thuốc / Hóa đơn: tất cả đều phải hiển thị hết (không bị cắt)
   - Nút "Xem thêm" phải xuất hiện và khi nhấn phải tải thêm dữ liệu

### 7.2 Đặc biệt chú ý

- **Màn khám của bác sĩ (PrescriptionTab) KHÔNG ĐỔI:** Vẫn chỉ hiển thị đơn đang hiệu lực cho bác sĩ chỉnh sửa. Không dùng API này cho màn khám bác sĩ.
- **Hai hàm API khác nhau:** 
  - `getVisitPrescription` (singular): cho màn khám bác sĩ, trả 1 đơn
  - `getVisitPrescriptions` (plural): cho lịch sử, trả tất cả đơn
- **`patient_id` trên tab Hóa đơn:** Từ trước bị bỏ qua ở backend → tab hiển thị hóa đơn của toàn clinic. Đã sửa (FIX).
- **VitalsTab (tab Sinh hiệu):** Giữ nguyên `limit=5` (trend chart, không phải lịch sử đầy đủ).

### 7.3 Bệnh nhân test dùng demo creds

| Bệnh nhân | Cách tạo |
|-----------|---------|
| Bệnh nhân mới, có 1-2 lượt khám | Dùng UI tiếp nhận (Intake screen) |
| Bệnh nhân khám 55+ lần | Tạo qua SQL seeding hoặc API batch |

**Demo creds:** Xem `clinic-cms-local-ports` trong persistent memory.

### 7.4 Các lỗi pre-existing không cần sửa trong TASK-146

- **BUG-146-01**: `fn_next_visit_number` lpad truncation (khi clinic tạo >999 visit/ngày) — ghi lại cho follow-up
- **BUG-146-04**: Không có UI submit prescription từ draft → pending — ghi lại cho follow-up
- **BUG-146-05**: `_pull_lines_from_visit` nuốt lỗi, trả 500 — ghi lại cho follow-up

---

## Liên kết

- **Handoff từ Test Agent:** `docs/tasks/TASK-146/handoff/test-to-documentation.md`
- **Task definition:** `docs/tasks/TASK-146/task.md`
- **Audit report:** `docs/tasks/TASK-146/handoff/audit-report.md`
- **Review report:** `docs/tasks/TASK-146/handoff/review-report.md` (ROUND 2 APPROVED)
- **Test report:** `docs/tasks/TASK-146/deliveries/test-reports/test-report.md`
- **Test cases:** `docs/tasks/TASK-146/deliveries/test-cases/visit-correction-full-flow-test-cases.md`

