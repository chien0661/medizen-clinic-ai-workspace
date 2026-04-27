# Thiết Kế Chi Tiết Tính Năng: [Tên Tính Năng]

**Dự án:** [Tên dự án]
**Task:** [TASK-XXX]
**Phiên bản:** [X.Y]
**Ngày:** [YYYY-MM-DD]
**Người thực hiện:** [Tên]
**Trạng thái:** [Bản nháp | Đang duyệt | Đã duyệt]
**Tài liệu liên quan:** [SRS, Jira ticket, v.v.]

---

## Lịch sử thay đổi

| Phiên bản | Ngày | Nội dung thay đổi |
|-----------|------|-------------------|
| 1.0 | [Ngày] | Phiên bản đầu tiên |

---

## Mục lục

- [1. Tổng quan tính năng](#1-tổng-quan-tính-năng)
- [2. Luồng xử lý tổng thể](#2-luồng-xử-lý-tổng-thể)
- [3. Nguồn dữ liệu đầu vào](#3-nguồn-dữ-liệu-đầu-vào)
- [4. Danh sách API](#4-danh-sách-api)
- [5. Chi tiết từng API](#5-chi-tiết-từng-api)
- [6. Cấu trúc cơ sở dữ liệu](#6-cấu-trúc-cơ-sở-dữ-liệu)
- [7. SQL tổng hợp và truy vấn dữ liệu](#7-sql-tổng-hợp-và-truy-vấn-dữ-liệu) *(task thống kê/báo cáo)*
  - [7.1 SQL tổng hợp / ghi dữ liệu](#71-sql-tổng-hợp--ghi-dữ-liệu)
  - [7.2 SQL truy vấn báo cáo / lấy dữ liệu](#72-sql-truy-vấn-báo-cáo--lấy-dữ-liệu)
  - [7.3 Logic tính toán tham số truy vấn](#73-logic-tính-toán-tham-số-truy-vấn)
- [8. Quy tắc nghiệp vụ](#8-quy-tắc-nghiệp-vụ)
- [9. Xử lý lỗi](#9-xử-lý-lỗi)
- [10. Chiến lược cache](#10-chiến-lược-cache)
- [11. Ghi chú và lưu ý khi kiểm thử](#11-ghi-chú-và-lưu-ý-khi-kiểm-thử)

---

## 1. Tổng quan tính năng

### 1.1 Mục đích

[Mô tả ngắn gọn tính năng làm gì và tại sao cần thiết. Ví dụ: "Cung cấp dữ liệu phân tích cho dashboard miniapp, giúp đối tác theo dõi lượt truy cập, người dùng mới và giao dịch theo thời gian thực."]

### 1.2 Phạm vi

**Bao gồm:**
- [Chức năng 1]
- [Chức năng 2]

**Không bao gồm:**
- [Điều không nằm trong phạm vi tính năng này]

### 1.3 Các bên liên quan

| Vai trò | Mô tả |
|---------|-------|
| **Người dùng cuối** | [Ai sẽ sử dụng tính năng này] |
| **Hệ thống cung cấp dữ liệu** | [Hệ thống gửi dữ liệu vào, ví dụ: BI System] |
| **Hệ thống tiêu thụ** | [Hệ thống / ứng dụng nhận kết quả] |

---

## 2. Luồng xử lý tổng thể

### 2.1 Sơ đồ luồng dữ liệu

```
[Mô tả luồng từ đầu vào đến đầu ra, ví dụ:]

[Hệ thống BI]
      │  Gửi dữ liệu tổng hợp
      ▼
[Message Queue]
      │  Consumer lắng nghe và xử lý
      ▼
[Service xử lý]
      │  Lưu vào database, xóa cache cũ
      ▼
[Database]
      │  Client gọi API để lấy dữ liệu
      ▼
[REST API] ──► [Ứng dụng Client]
```

### 2.2 Mô tả các bước chính

| Bước | Tên bước | Mô tả chi tiết |
|------|---------|----------------|
| 1 | [Tên bước] | [Mô tả đầy đủ điều gì xảy ra ở bước này] |
| 2 | [Tên bước] | [Mô tả đầy đủ] |
| 3 | [Tên bước] | [Mô tả đầy đủ] |

---

## 3. Nguồn dữ liệu đầu vào

*Phần này mô tả cách hệ thống nhận dữ liệu từ nguồn bên ngoài (Message Queue, File Import, v.v.).
Bỏ qua phần này nếu dữ liệu chỉ đến từ người dùng trực tiếp qua API.*

### 3.1 [Tên nguồn dữ liệu, ví dụ: BiStats Message Queue]

#### Thông tin kết nối

| Thuộc tính | Giá trị |
|------------|---------|
| **Loại** | [Kafka / RabbitMQ / File / FTP / v.v.] |
| **Topic / Queue / Đường dẫn** | `[Tên topic hoặc địa chỉ]` |
| **Hệ thống gửi** | [Tên hệ thống nguồn] |
| **Bảng lưu trữ** | `[Tên bảng trong database]` |

#### Cấu trúc dữ liệu nhận về

Mỗi bản tin/bản ghi từ nguồn dữ liệu có cấu trúc sau:

| STT | Tên trường | Ý nghĩa | Bắt buộc | Ghi chú / Ví dụ |
|-----|-----------|---------|---------|----------------|
| 1 | `field_name_1` | [Mô tả ý nghĩa nghiệp vụ] | Có | [Ví dụ: `20241115`] |
| 2 | `field_name_2` | [Mô tả ý nghĩa nghiệp vụ] | Có | [Ví dụ: `day`, `week`] |
| 3 | `field_name_3` | [Mô tả ý nghĩa nghiệp vụ] | Không | [Ví dụ: `1500`] |

#### Danh mục giá trị hợp lệ

*Liệt kê các trường có tập giá trị cố định (enum):*

**[Tên trường]:**

| Giá trị | Ý nghĩa | Ghi chú |
|---------|---------|--------|
| `value_1` | [Mô tả rõ ràng] | [Ghi chú nếu có] |
| `value_2` | [Mô tả rõ ràng] | |

#### Quy trình xử lý khi nhận dữ liệu

| Bước | Mô tả | Xử lý khi có lỗi |
|------|-------|-----------------|
| 1 | Nhận bản tin từ hàng đợi | — |
| 2 | Phân tích và đọc nội dung bản tin | Ghi log, bỏ qua bản tin lỗi |
| 3 | Kiểm tra các trường bắt buộc | Ghi log, bỏ qua bản tin thiếu thông tin |
| 4 | Lưu hoặc cập nhật dữ liệu vào database | Ghi log lỗi |
| 5 | Xóa cache cũ liên quan để đảm bảo dữ liệu mới nhất | — |
| 6 | Xác nhận đã xử lý xong với hàng đợi | — |

---

## 4. Danh sách API

Tất cả API đều yêu cầu xác thực qua header:
```
Authorization: Bearer {token}
```

**Đường dẫn gốc (Base Path):** `/api/v1/[module]`

| STT | Phương thức | Đường dẫn | Mô tả tóm tắt |
|-----|------------|-----------|--------------|
| 1 | GET | `/api/v1/[path-1]` | [Mô tả ngắn gọn mục đích] |
| 2 | GET | `/api/v1/[path-2]` | [Mô tả ngắn gọn mục đích] |
| 3 | POST | `/api/v1/[path-3]` | [Mô tả ngắn gọn mục đích] |

---

## 5. Chi tiết từng API

### 5.1 [Tên API, ví dụ: Lấy tổng quan Dashboard]

#### Thông tin chung

| Thuộc tính | Giá trị |
|------------|---------|
| **Đường dẫn** | `GET /api/v1/[path]` |
| **Mô tả** | [Mô tả mục đích: API này trả về gì, dùng để làm gì trong nghiệp vụ] |
| **Xác thực** | Bắt buộc |

#### Tham số đầu vào

| Tham số | Kiểu | Bắt buộc | Mô tả | Giá trị mặc định |
|---------|------|---------|-------|-----------------|
| `param_1` | String | Có | [Mô tả ý nghĩa và cách dùng] | — |
| `param_2` | String | Không | [Mô tả, nếu không truyền thì hệ thống xử lý ra sao] | `ALL` |

**Giá trị hợp lệ của `param_1`:**

| Giá trị | Ý nghĩa |
|---------|---------|
| `value_a` | [Mô tả rõ ràng bằng ngôn ngữ nghiệp vụ] |
| `value_b` | [Mô tả rõ ràng] |

#### Quy trình xử lý

| Bước | Mô tả |
|------|-------|
| 1 | Nhận yêu cầu từ ứng dụng client |
| 2 | Kiểm tra token xác thực — từ chối nếu không hợp lệ |
| 3 | Kiểm tra tham số đầu vào — trả lỗi nếu thiếu hoặc sai giá trị |
| 4 | Kiểm tra cache — nếu có dữ liệu đã lưu, trả về ngay mà không cần truy vấn database |
| 5 | Truy vấn dữ liệu từ database theo các điều kiện lọc |
| 6 | Lưu kết quả vào cache để phục vụ các yêu cầu tiếp theo nhanh hơn |
| 7 | Trả kết quả về cho client |

**Truy vấn dữ liệu:**

*(Ghi chú: [Mô tả đặc điểm của dữ liệu, ví dụ: "Hệ thống BI đã tính toán sẵn dữ liệu tổng hợp. API chỉ cần lọc theo điều kiện và lấy trực tiếp, không tính toán thêm."])*

```sql
SELECT
    column_1,
    column_2,
    column_3
FROM ten_bang
WHERE dieu_kien_1 = :param_1
  AND dieu_kien_2 = :param_2
  AND loai_du_lieu = 'overview'
```

**Ví dụ truy vấn thực tế:**

```sql
-- Lấy dữ liệu 7 ngày qua của miniapp MINIAPP001, kênh VIETTELPAY:
SELECT ...
FROM bi_miniapp_stats
WHERE time_granularity = 'seven_day'
  AND miniapp_code = 'MINIAPP001'
  AND partner_code = 'VIETTELPAY'
```

#### Kết quả trả về

**Thành công (200 OK):**

```json
{
  "code": "00",
  "message": "Success",
  "data": {
    "field_1": 150000,
    "field_2": 8.5,
    "field_3": "example_value"
  }
}
```

**Mô tả các trường kết quả:**

| Trường | Kiểu | Mô tả ý nghĩa nghiệp vụ |
|--------|------|------------------------|
| `field_1` | Số nguyên | [Mô tả, ví dụ: Tổng số phiên truy cập] |
| `field_2` | Số thực | [Mô tả, ví dụ: % thay đổi so với cùng kỳ — dương = tăng, âm = giảm] |
| `field_3` | Chuỗi | [Mô tả] |

---

### 5.2 [Tên API tiếp theo]

*(Lặp lại cấu trúc như mục 5.1 cho mỗi API)*

---

## 6. Cấu trúc cơ sở dữ liệu

### 6.1 Tổng quan các bảng

| Bảng | Mục đích |
|------|---------|
| `ten_bang_1` | [Mô tả bảng lưu gì, phục vụ nghiệp vụ nào] |
| `ten_bang_2` | [Mô tả] |

### 6.2 Chi tiết bảng

#### Bảng: `ten_bang_1`

**Mô tả:** [Bảng này lưu gì, quan hệ với nghiệp vụ như thế nào]

| Tên cột | Kiểu dữ liệu | Bắt buộc | Mô tả |
|---------|-------------|---------|-------|
| `id` | BIGINT | Có | Khóa chính, tự tăng |
| `column_1` | VARCHAR(50) | Có | [Mô tả ý nghĩa nghiệp vụ] |
| `column_2` | DECIMAL(15,2) | Không | [Mô tả, ví dụ: % thay đổi so với cùng kỳ] |
| `created_at` | TIMESTAMP | Có | Thời điểm tạo bản ghi |

**Tính duy nhất (Unique Key):** Tổ hợp các cột (`col_a`, `col_b`, `col_c`) phải là duy nhất — đảm bảo không có dữ liệu trùng lặp cho cùng một thời điểm và điều kiện.

**Script tạo bảng:**

```sql
CREATE TABLE ten_bang_1 (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    column_1 VARCHAR(50) NOT NULL,
    column_2 DECIMAL(15,2),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uk_ten_bang_1 (col_a, col_b, col_c)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

---

## 7. SQL tổng hợp và truy vấn dữ liệu

*Áp dụng cho các task **tổng hợp dữ liệu, thống kê, báo cáo** (ETL, analytics, dashboard).
Bỏ qua phần này nếu tính năng không có logic tổng hợp hay truy vấn phức tạp.*

### 7.1 SQL tổng hợp / ghi dữ liệu

*Mô tả các câu SQL dùng để **tạo hoặc cập nhật dữ liệu tổng hợp** vào database (UPSERT, INSERT, UPDATE batch, v.v.). Đây thường là SQL của consumer, job, hoặc stored procedure.*

#### [Tên thao tác, ví dụ: Lưu dữ liệu thống kê từ BI]

**Mục đích:** [Câu SQL này làm gì — ví dụ: "Ghi dữ liệu thống kê miniapp nhận từ Kafka vào bảng bi_miniapp_stats, cập nhật nếu đã tồn tại (UPSERT)."]

**Điều kiện duy nhất (Unique Key):** Tổ hợp cột `(col_a, col_b, col_c, ...)` xác định một bản ghi là trùng lặp.

```sql
INSERT INTO ten_bang (col_1, col_2, col_3, col_4)
VALUES (:val_1, :val_2, :val_3, :val_4)
ON DUPLICATE KEY UPDATE
    col_3 = VALUES(col_3),
    col_4 = VALUES(col_4),
    updated_at = NOW();
```

**Giải thích:**
- Nếu chưa có bản ghi với khóa duy nhất → INSERT bản ghi mới
- Nếu đã có → UPDATE các cột giá trị, giữ nguyên khóa

---

*(Thêm các thao tác SQL tổng hợp khác nếu có)*

---

### 7.2 SQL truy vấn báo cáo / lấy dữ liệu

*Mô tả các câu SQL **lấy dữ liệu** để trả về cho API hoặc báo cáo. Bao gồm toàn bộ điều kiện WHERE, logic phân nhánh, UNION nếu có.*

#### [Tên truy vấn, ví dụ: Truy vấn dữ liệu tổng quan theo khoảng thời gian]

**Mục đích:** [Truy vấn này lấy gì — ví dụ: "Lấy số liệu tổng hợp (lượt truy cập, người dùng mới, giao dịch) theo khoảng thời gian và bộ lọc."]

**Điều kiện lọc:**

| Tham số | Cột tương ứng | Ghi chú |
|---------|--------------|--------|
| `param_1` | `column_1` | [Ví dụ: Nếu null → dùng giá trị `ALL`] |
| `param_2` | `column_2` | [Ví dụ: Bắt buộc, không có giá trị mặc định] |

```sql
SELECT
    col_1,
    col_2,
    col_3
FROM ten_bang
WHERE column_1 = :param_1      -- [Giải thích điều kiện này]
  AND column_2 = :param_2      -- [Giải thích]
  AND loai_du_lieu = 'overview'
ORDER BY col_date ASC;
```

**Ví dụ thực tế:**

```sql
-- Lấy dữ liệu 7 ngày qua của MINIAPP001, kênh VIETTELPAY:
SELECT total_sessions, active_users, new_users
FROM bi_miniapp_stats
WHERE time_granularity = 'seven_day'
  AND miniapp_code = 'MINIAPP001'
  AND partner_code = 'VIETTELPAY'
  AND level_1_name = 'overview'
  AND partition_date = CURDATE();
```

---

#### [Tên truy vấn phức tạp, ví dụ: Truy vấn xu hướng theo tuần — có UNION]

**Mục đích:** [Giải thích tại sao cần UNION hoặc logic phức tạp — ví dụ: "BI tách riêng dữ liệu tuần đã hoàn thành (`week`) và tuần hiện tại (`cur_week`). Cần UNION 2 truy vấn để tránh bỏ sót dữ liệu tuần đang chạy."]

```sql
-- Phần 1: Các tuần đã hoàn thành
SELECT col_1, col_2, 'week' AS loai
FROM ten_bang
WHERE time_granularity = 'week'
  AND partition_date BETWEEN :start_date AND :end_date

UNION ALL

-- Phần 2: Tuần hiện tại (chưa hoàn thành)
SELECT col_1, col_2, 'cur_week' AS loai
FROM ten_bang
WHERE time_granularity = 'cur_week'
  AND partition_date = CURDATE();
```

**Giải thích:**
- **Phần 1** — lấy dữ liệu các tuần đã kết thúc trong khoảng thời gian yêu cầu
- **Phần 2** — lấy thêm dữ liệu tuần hiện tại (tính đến hôm nay), không trùng với phần 1

---

*(Thêm các truy vấn khác nếu có: theo tháng, theo nhóm tuổi, phân phối, v.v.)*

---

### 7.3 Logic tính toán tham số truy vấn

*Mô tả các logic tính toán giá trị đầu vào cho SQL — ví dụ: cách tính `startDate`/`endDate` từ tham số `timePeriod`, cách xác định `partition_date`.*

#### [Tên logic, ví dụ: Tính khoảng ngày từ timePeriod]

| timePeriod | startDate | endDate | Ghi chú |
|------------|-----------|---------|--------|
| `day` | Hôm nay | Hôm nay | 1 ngày |
| `seven_day` | Hôm nay - 6 ngày | Hôm nay | 7 ngày liên tiếp |
| `thirty_day` | Hôm nay - 29 ngày | Hôm nay | 30 ngày liên tiếp |
| `three_month` | Xem logic bên dưới | Xem logic bên dưới | Phụ thuộc ngày đầu tháng |

**Logic đặc biệt cho `three_month`:**

- **Nếu hôm nay là ngày 1 của tháng:**
  - startDate = Ngày 1 của tháng (hôm nay - 3 tháng)
  - endDate = Ngày cuối của tháng trước
  - *Ví dụ: Hôm nay 01/01/2026 → startDate = 01/10/2025, endDate = 31/12/2025*

- **Nếu hôm nay không phải ngày 1:**
  - startDate = Ngày 1 của tháng (hôm nay - 2 tháng)
  - endDate = Hôm nay
  - *Ví dụ: Hôm nay 08/01/2026 → startDate = 01/11/2025, endDate = 08/01/2026*

---

## 8. Quy tắc nghiệp vụ

| Mã | Mô tả quy tắc | Hành vi khi vi phạm |
|----|--------------|---------------------|
| BR-001 | [Mô tả quy tắc bằng ngôn ngữ tự nhiên, ví dụ: "Nếu tham số miniappCode là null hoặc rỗng, hệ thống sẽ dùng giá trị ALL để lấy tổng hợp toàn bộ miniapp"] | [Thông báo lỗi cụ thể / Xử lý mặc định] |
| BR-002 | [Mô tả quy tắc] | [Hành vi xử lý] |
| BR-003 | [Mô tả quy tắc] | [Hành vi xử lý] |

---

## 9. Xử lý lỗi

### 9.1 Các mã lỗi phổ biến

| Mã HTTP | Mã lỗi | Tình huống xảy ra | Thông báo trả về |
|---------|--------|-------------------|-----------------|
| 400 | INVALID_REQUEST | Tham số đầu vào không hợp lệ hoặc thiếu trường bắt buộc | "Yêu cầu không hợp lệ: [chi tiết lỗi]" |
| 401 | UNAUTHORIZED | Token xác thực không hợp lệ hoặc đã hết hạn | "Yêu cầu xác thực để truy cập tài nguyên này" |
| 404 | NOT_FOUND | Không tìm thấy dữ liệu theo điều kiện đã cho | "Không tìm thấy dữ liệu" |
| 422 | VALIDATION_ERROR | Giá trị tham số không nằm trong danh sách cho phép | "Giá trị [tên_tham_số] không hợp lệ. Giá trị hợp lệ: [danh sách]" |
| 500 | INTERNAL_ERROR | Lỗi hệ thống nội bộ (database, cache, v.v.) | "Lỗi hệ thống, vui lòng thử lại sau" |

### 9.2 Định dạng phản hồi lỗi

```json
{
  "code": "[Mã lỗi nội bộ]",
  "message": "[Mô tả lỗi chi tiết để người dùng hoặc hệ thống hiểu]"
}
```

---

## 10. Chiến lược cache

*Bỏ qua phần này nếu tính năng không sử dụng cache.*

### 10.1 Mục đích

[Giải thích tại sao cần cache — ví dụ: "Dữ liệu analytics thay đổi theo từng chu kỳ BI (thường là hàng ngày), nên có thể lưu cache để giảm tải database và tăng tốc độ phản hồi."]

### 10.2 Quy tắc lưu và xóa cache

| Nội dung cache | Thời gian lưu (TTL) | Điều kiện xóa cache |
|----------------|---------------------|---------------------|
| [Mô tả loại dữ liệu được cache] | [X phút / giờ] | [Ví dụ: Khi có dữ liệu mới từ BI gửi vào, cache liên quan sẽ bị xóa ngay] |

### 10.3 Cách tạo khóa cache

Mỗi kết quả API được lưu với một khóa duy nhất theo cấu trúc:

```
[prefix]:[tham_so_1]:[tham_so_2]:...
```

**Ví dụ:** `overview:MINIAPP001:VIETTELPAY:seven_day:ALL`

*Nghĩa là: dữ liệu overview của MINIAPP001, kênh VIETTELPAY, 7 ngày qua, tất cả chiến dịch.*

---

## 11. Ghi chú và lưu ý khi kiểm thử

### 11.1 Điểm quan trọng cần nắm

- [Điều đặc biệt về dữ liệu mà tester cần biết trước khi test, ví dụ: "Dữ liệu được cập nhật một lần mỗi ngày từ hệ thống BI, không phải real-time."]
- [Hành vi đặc biệt trong một số trường hợp cụ thể]
- [Mối quan hệ hoặc phụ thuộc giữa các tính năng]

### 11.2 Gợi ý dữ liệu kiểm thử

| Kịch bản | Giá trị đầu vào | Kết quả kỳ vọng |
|---------|----------------|----------------|
| [Kịch bản bình thường] | [Giá trị cụ thể] | [Kết quả mong đợi] |
| [Kịch bản biên] | [Giá trị biên] | [Kết quả mong đợi] |
| [Kịch bản lỗi] | [Giá trị không hợp lệ] | [Thông báo lỗi cụ thể] |

### 11.3 Hạn chế hiện tại

- [Hạn chế 1: Mô tả và lý do]
- [Hạn chế 2: Mô tả và lý do]

### 11.4 Hướng phát triển *(nếu có)*

- [Tính năng / cải tiến dự kiến trong các phiên bản tiếp theo]

---

**Phê duyệt**

| Vai trò | Họ tên | Ngày |
|---------|--------|------|
| Trưởng nhóm kỹ thuật | | |
| Tester phụ trách | | |
| Khách hàng / PO | | |
