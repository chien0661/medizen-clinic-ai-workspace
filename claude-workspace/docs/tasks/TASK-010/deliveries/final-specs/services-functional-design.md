# Thiết kế chức năng: Danh mục dịch vụ và Dịch vụ trong lượt khám (TASK-010)

## 1. Tổng quan

Module Services cung cấp hai chức năng chính:

1. **Danh mục dịch vụ (Service Catalog)**: Quản lý danh sách dịch vụ của phòng khám (xét nghiệm, chẩn đoán hình ảnh, thủ thuật, v.v.)
2. **Dịch vụ trong lượt khám (Visit Services)**: Ghi nhận các dịch vụ đã thực hiện cho bệnh nhân trong một lượt khám

## 2. Mô hình dữ liệu

### 2.1 Bảng `service` — Danh mục dịch vụ

Mỗi phòng khám có danh mục dịch vụ riêng. Mỗi dịch vụ có:
- `code`: mã dịch vụ (chữ và số, 2-20 ký tự, duy nhất trong phòng khám với bản ghi active)
- `name`: tên dịch vụ
- `category`: nhóm dịch vụ (tự do, không ràng buộc ENUM)
- `default_price`: giá mặc định
- `default_duration_minutes`: thời gian thực hiện (phút)
- `is_active`: trạng thái hoạt động

### 2.2 Bảng `visit_service` — Dịch vụ trong lượt khám

Mỗi lượt khám có thể có nhiều dịch vụ. Mỗi bản ghi ghi nhận:
- `visit_id`: FK tới lượt khám
- `service_id`: FK tới danh mục dịch vụ
- `unit_price`: giá tại thời điểm thêm vào (**chụp ảnh** từ `default_price` — không thay đổi khi catalog thay đổi)
- `quantity`: số lượng
- `status`: trạng thái thực hiện
- `discount_amount / discount_reason`: giảm giá + lý do
- `performed_by_user_id`: nhân viên thực hiện
- `started_at / completed_at / cancelled_at`: thời điểm chuyển trạng thái

## 3. State Machine — Trạng thái dịch vụ trong lượt khám

```
ordered → in_progress → completed (trạng thái kết thúc)
ordered → cancelled (trạng thái kết thúc)
in_progress → cancelled (trạng thái kết thúc)
completed → KHÔNG THỂ hủy (AC #4)
```

### Mô tả các trạng thái:
- **ordered**: Bác sĩ/BS điều dưỡng đã chỉ định dịch vụ, chờ thực hiện
- **in_progress**: Đang thực hiện dịch vụ
- **completed**: Dịch vụ đã hoàn thành
- **cancelled**: Dịch vụ đã hủy (chỉ từ ordered hoặc in_progress)

## 4. Acceptance Criteria

### AC #1: Chụp ảnh giá (Price Snapshot)
Khi thêm dịch vụ vào lượt khám, hệ thống **chụp ảnh** `default_price` từ catalog vào trường `unit_price` của `visit_service`. Nếu sau đó catalog thay đổi giá, các bản ghi `visit_service` đã tồn tại **không bị ảnh hưởng**.

**Lý do**: Đảm bảo tính toàn vẹn của hóa đơn — giá trên hóa đơn phản ánh giá tại thời điểm thực hiện dịch vụ.

### AC #2: Thay đổi giá catalog không ảnh hưởng visit_service cũ
Xem AC #1. Được kiểm tra bằng test: tạo visit_service → cập nhật giá catalog → kiểm tra visit_service vẫn có giá cũ.

### AC #3: Ghi đè giá cần quyền `service.price_override`
Nếu có `unit_price_override` trong request và người dùng **không có** quyền `service.price_override` → HTTP 403.

**Các trường hợp có thể ghi đè giá**:
- Admin có toàn quyền
- Bác sĩ trưởng/quản lý được gán quyền `service.price_override` bổ sung

### AC #4: Không thể hủy dịch vụ đã completed
Nếu `visit_service.status == 'completed'` và gọi API cancel → HTTP 409 Conflict.

**Lý do**: Dịch vụ đã hoàn thành không thể hoàn tác mà không có quy trình hoàn tiền/điều chỉnh.

## 5. Phân quyền

| Quyền | Mô tả | Role mặc định |
|-------|-------|---------------|
| `service.read` | Xem danh mục + dịch vụ trong lượt khám | admin, doctor, nurse, receptionist |
| `service.write` | Thêm/cập nhật dịch vụ trong lượt khám | admin, doctor, nurse, receptionist |
| `service.manage` | Tạo/sửa/xóa danh mục dịch vụ | admin |
| `service.price_override` | Ghi đè đơn giá | admin (+ có thể gán thêm) |

## 6. Isolation giữa các phòng khám

Tất cả truy vấn đều được lọc theo `clinic_id`. RLS (Row Level Security) được kích hoạt trên cả hai bảng, đảm bảo phòng khám A không thể đọc/ghi dữ liệu của phòng khám B.

## 7. Ghi chú kỹ thuật

- **Partial unique index**: `uq_service_clinic_code_active` trên `(clinic_id, code) WHERE is_deleted=false` — cho phép tái sử dụng code sau khi soft-delete
- **Concurrent add**: Không có unique constraint trên `(visit_id, service_id)` — cho phép thêm cùng một dịch vụ nhiều lần trong một lượt khám (ví dụ: xét nghiệm máu x2)
- **Giảm giá**: `discount_amount > 0` bắt buộc phải có `discount_reason`
- **Audit log**: Tất cả thay đổi được ghi vào `audit_log` thông qua event listener của SQLAlchemy
