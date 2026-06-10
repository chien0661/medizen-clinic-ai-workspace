# TASK-078 — Test Cases Chi tiết

**Hệ thống:** Clinic CMS  
**Ngày tạo:** 2026-06-10  
**Phạm vi:** Toàn bộ luồng từ cấu hình → tiếp nhận → khám → kê đơn → dịch vụ → dược → thanh toán → báo cáo

---

## PHASE 1 — ADMIN: Thiết lập phòng khám

### TC-01: Đăng nhập Admin
| Trường | Nội dung |
|--------|---------|
| **Vai trò** | Administrator |
| **Tài khoản** | admin / Demo@1234 |
| **URL** | `http://localhost:1420` |
| **Input** | username=admin, password=Demo@1234 |
| **Mong muốn** | Đăng nhập thành công, redirect về dashboard Admin |
| **Tình huống** | Happy path |

### TC-02: Xem & cập nhật thông tin phòng khám
| Trường | Nội dung |
|--------|---------|
| **Vai trò** | Administrator |
| **URL** | `#/admin/settings` |
| **Input** | Cập nhật tên phòng khám, địa chỉ, điện thoại |
| **Mong muốn** | Settings lưu thành công, toast "Đã cập nhật" |
| **Tình huống** | Happy path |

### TC-03: Tạo dịch vụ mới
| Trường | Nội dung |
|--------|---------|
| **Vai trò** | Administrator |
| **URL** | `#/admin/services` |
| **Input** | Mã: TC78SVC1, Tên: "Khám tổng quát TC78", Danh mục: Khám, Giá: 200.000 |
| **Mong muốn** | Dịch vụ tạo thành công, xuất hiện trong danh sách |
| **Tình huống** | Happy path |

### TC-04: Tạo thuốc mới
| Trường | Nội dung |
|--------|---------|
| **Vai trò** | Administrator |
| **URL** | `#/admin/medicines` |
| **Input** | Mã: TC78MED1, Tên: "Paracetamol TC78", Dạng: Viên nén, Đơn vị: Viên, Giá: 2.000 |
| **Mong muốn** | Thuốc tạo thành công, xuất hiện trong danh sách |
| **Tình huống** | Happy path |

### TC-05: Phân quyền người dùng
| Trường | Nội dung |
|--------|---------|
| **Vai trò** | Administrator |
| **URL** | `#/admin/users` |
| **Input** | Tìm user "dr_nguyen", xem chi tiết vai trò |
| **Mong muốn** | Hiển thị đúng role Doctor, active=true |
| **Tình huống** | Happy path |

---

## PHASE 2 — RECEPTIONIST: Tiếp nhận bệnh nhân

### TC-06: Đăng nhập Lễ tân
| Trường | Nội dung |
|--------|---------|
| **Vai trò** | Receptionist |
| **Tài khoản** | recept_anh / Recept@1234 |
| **Mong muốn** | Đăng nhập thành công, thấy sidebar Reception |
| **Tình huống** | Happy path |

### TC-07: Tìm kiếm bệnh nhân hiện có
| Trường | Nội dung |
|--------|---------|
| **Vai trò** | Receptionist |
| **URL** | `#/patients` |
| **Input** | Tìm kiếm "TC78" |
| **Mong muốn** | Danh sách kết quả hoặc "Không tìm thấy" |
| **Tình huống** | Happy path |

### TC-08: Đăng ký bệnh nhân mới
| Trường | Nội dung |
|--------|---------|
| **Vai trò** | Receptionist |
| **URL** | `#/patients` → "Đăng ký mới" |
| **Input** | Họ tên: Trần Thị TC78, Ngày sinh: 15/03/1985, Giới tính: Nữ, SĐT: 0912345678, Địa chỉ: 123 Đường ABC |
| **Mong muốn** | Bệnh nhân tạo thành công với mã BNxxxx |
| **Tình huống** | Happy path |

### TC-09: Tạo lượt khám walk-in
| Trường | Nội dung |
|--------|---------|
| **Vai trò** | Receptionist |
| **Input** | Từ trang BN vừa tạo → "Khám ngay" (walk-in) |
| **Mong muốn** | Lượt khám tạo, trạng thái WAITING, xuất hiện trong hàng chờ |
| **Tình huống** | Happy path |

### TC-10: Xem hàng chờ
| Trường | Nội dung |
|--------|---------|
| **Vai trò** | Receptionist |
| **URL** | `#/queue` hoặc `#/reception` |
| **Mong muốn** | Hiển thị BN vừa đăng ký trong hàng chờ WAITING |
| **Tình huống** | Happy path |

---

## PHASE 3 — DOCTOR: Khám bệnh

### TC-11: Đăng nhập Bác sĩ
| Trường | Nội dung |
|--------|---------|
| **Vai trò** | Doctor |
| **Tài khoản** | dr_nguyen / Doctor@1234 |
| **Mong muốn** | Đăng nhập thành công, thấy sidebar Doctor (My Queue, Patients...) |
| **Tình huống** | Happy path |

### TC-12: Xem hàng chờ bác sĩ
| Trường | Nội dung |
|--------|---------|
| **Vai trò** | Doctor |
| **URL** | `#/doctor/queue` |
| **Mong muốn** | Hiển thị BN TC78 trong hàng chờ, trạng thái WAITING |
| **Tình huống** | Happy path |

### TC-13: Bắt đầu khám
| Trường | Nội dung |
|--------|---------|
| **Vai trò** | Doctor |
| **Input** | Click "Bắt đầu khám" trên BN TC78 |
| **Mong muốn** | Visit chuyển sang IN_PROGRESS, mở trang khám |
| **Tình huống** | Happy path |

### TC-14: Ghi SOAP + chẩn đoán
| Trường | Nội dung |
|--------|---------|
| **Vai trò** | Doctor |
| **Input** | S: "BN đau đầu, sốt 2 ngày", O: "T=38°C, họng đỏ", A: "Viêm họng cấp", P: "Kê đơn kháng sinh + hạ sốt", ICD-10: J02.9 |
| **Mong muốn** | SOAP lưu thành công, hiển thị lại đúng |
| **Tình huống** | Happy path |

### TC-15: Kê đơn thuốc
| Trường | Nội dung |
|--------|---------|
| **Vai trò** | Doctor |
| **URL** | Tab "Đơn thuốc" trong trang khám |
| **Input** | Thêm: Paracetamol TC78 — 1v × 3 lần/ngày × 5 ngày; Lưu đơn |
| **Mong muốn** | Đơn thuốc lưu thành công, 1 thuốc trong đơn |
| **Tình huống** | Happy path |

### TC-16: Chỉ định dịch vụ CLS
| Trường | Nội dung |
|--------|---------|
| **Vai trò** | Doctor |
| **URL** | Tab "Dịch vụ CLS" trong trang khám |
| **Input** | Thêm: Khám tổng quát TC78 |
| **Mong muốn** | Dịch vụ thêm thành công vào visit |
| **Tình huống** | Happy path |

### TC-17: Hoàn thành khám
| Trường | Nội dung |
|--------|---------|
| **Vai trò** | Doctor |
| **Input** | Click "Hoàn tất khám" |
| **Mong muốn** | Visit → AWAITING_PAYMENT, redirect về hàng chờ |
| **Tình huống** | Happy path |

---

## PHASE 4 — PHARMACIST: Phát thuốc

### TC-18: Đăng nhập Dược sĩ
| Trường | Nội dung |
|--------|---------|
| **Vai trò** | Pharmacist |
| **Tài khoản** | pharm_cuong / Pharm@1234 |
| **Mong muốn** | Đăng nhập thành công, thấy sidebar Pharmacy |
| **Tình huống** | Happy path |

### TC-19: Xem danh sách đơn thuốc chờ phát
| Trường | Nội dung |
|--------|---------|
| **Vai trò** | Pharmacist |
| **URL** | `#/pharmacy` |
| **Mong muốn** | Hiển thị đơn thuốc BN TC78 trạng thái PENDING |
| **Tình huống** | Happy path |

### TC-20: Phát thuốc
| Trường | Nội dung |
|--------|---------|
| **Vai trò** | Pharmacist |
| **Input** | Click vào đơn thuốc BN TC78 → "Phát thuốc" / "Xác nhận phát" |
| **Mong muốn** | Đơn thuốc chuyển sang DISPENSED |
| **Tình huống** | Happy path |

---

## PHASE 5 — CASHIER: Thanh toán

### TC-21: Đăng nhập Thu ngân
| Trường | Nội dung |
|--------|---------|
| **Vai trò** | Cashier |
| **Tài khoản** | cashier_em / Cashier@1234 |
| **Mong muốn** | Đăng nhập thành công, thấy sidebar Billing |
| **Tình huống** | Happy path |

### TC-22: Tạo hóa đơn cho visit
| Trường | Nội dung |
|--------|---------|
| **Vai trò** | Cashier |
| **URL** | `#/billing` → tìm visit BN TC78 → "Tạo hóa đơn" |
| **Input** | Visit BN TC78 (AWAITING_PAYMENT) |
| **Mong muốn** | Hóa đơn tạo thành công, trạng thái DRAFT, có dịch vụ + thuốc |
| **Tình huống** | Happy path |

### TC-23: Phát hành hóa đơn
| Trường | Nội dung |
|--------|---------|
| **Vai trò** | Cashier |
| **Input** | Click "Phát hành hóa đơn" |
| **Mong muốn** | Hóa đơn → ISSUED (Đã phát hành) |
| **Tình huống** | Happy path |

### TC-24: Thu tiền mặt
| Trường | Nội dung |
|--------|---------|
| **Vai trò** | Cashier |
| **Input** | Phương thức: Tiền mặt, Số tiền: đủ tổng hóa đơn |
| **Mong muốn** | Hóa đơn → PAID, hiển thị "Đã thanh toán" |
| **Tình huống** | Happy path |

### TC-25: In hóa đơn
| Trường | Nội dung |
|--------|---------|
| **Vai trò** | Cashier |
| **Input** | Click "In hóa đơn" |
| **Mong muốn** | Print preview mở, hiển thị đúng tên BN, số HĐ, tổng tiền |
| **Tình huống** | Happy path |

---

## PHASE 6 — ADMIN: Báo cáo & Thống kê

### TC-26: Đăng nhập lại Admin
| Trường | Nội dung |
|--------|---------|
| **Vai trò** | Administrator |
| **Tài khoản** | admin / Demo@1234 |
| **Mong muốn** | Đăng nhập thành công |

### TC-27: Xem báo cáo doanh thu
| Trường | Nội dung |
|--------|---------|
| **Vai trò** | Administrator |
| **URL** | `#/reports` |
| **Mong muốn** | Trang báo cáo load, hiển thị tab doanh thu / bệnh nhân |
| **Tình huống** | Happy path |

### TC-28: Xem dashboard Admin
| Trường | Nội dung |
|--------|---------|
| **Vai trò** | Administrator |
| **URL** | `#/admin/dashboard` hoặc `#/dashboard` |
| **Mong muốn** | Dashboard hiển thị số liệu (BN hôm nay, doanh thu...) |
| **Tình huống** | Happy path |

### TC-29: Xuất Excel danh sách bệnh nhân
| Trường | Nội dung |
|--------|---------|
| **Vai trò** | Administrator |
| **URL** | `#/patients` |
| **Input** | Click "Xuất Excel" |
| **Mong muốn** | File Excel tải về, có dữ liệu BN |
| **Tình huống** | Happy path |

### TC-30: Xem AR Aging (công nợ)
| Trường | Nội dung |
|--------|---------|
| **Vai trò** | Administrator |
| **URL** | `#/reports` → Tab AR Aging |
| **Mong muốn** | Báo cáo AR aging hiển thị, có thể lọc theo khoảng nợ |
| **Tình huống** | Happy path |

---

## Tình huống lỗi cần test

### TC-E1: Admin không thể tự thu tiền hóa đơn mình tạo (SOD)
| Trường | Nội dung |
|--------|---------|
| **Vai trò** | Administrator (tạo HĐ) → Administrator (thu tiền) |
| **Input** | Admin tạo HĐ rồi tự click "Xác nhận thu tiền" |
| **Mong muốn** | Lỗi rõ ràng: "Người tạo hóa đơn không được tự xác nhận thanh toán" |
| **Tình huống** | SOD rule |

### TC-E2: Lễ tân không thể vào trang Doctor Queue
| Trường | Nội dung |
|--------|---------|
| **Vai trò** | Receptionist |
| **Input** | Truy cập trực tiếp `#/doctor/queue` |
| **Mong muốn** | 403 hoặc redirect về trang không có quyền |
| **Tình huống** | RBAC guard |

### TC-E3: Đăng ký bệnh nhân với SĐT trùng
| Trường | Nội dung |
|--------|---------|
| **Vai trò** | Receptionist |
| **Input** | Tạo BN với SĐT đã tồn tại |
| **Mong muốn** | Cảnh báo duplicate, gợi ý BN trùng |
| **Tình huống** | Validation / duplicate check |
