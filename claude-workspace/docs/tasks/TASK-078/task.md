---
id: TASK-078
title: "E2E Full System Test — Multi-role: Admin + Lễ tân + Bác sĩ + Dược + Thu ngân + Báo cáo"
status: DONE
priority: High
type: test
assigned: test-agent
started: 2026-06-10
completed: 2026-06-10
affected-repos:
  - clinic-cms
  - clinic-cms-web
---

## Mục tiêu

Kiểm thử E2E toàn bộ luồng nghiệp vụ chính của Clinic CMS theo từng vai trò:

1. **Admin** — Quản trị + thiết lập phòng khám
2. **Lễ tân (Receptionist)** — Tiếp nhận bệnh nhân
3. **Bác sĩ (Doctor)** — Khám bệnh + kê đơn + chỉ định dịch vụ
4. **Dược sĩ (Pharmacist)** — Phát thuốc
5. **Thu ngân (Cashier)** — Thanh toán hóa đơn
6. **Admin/Owner** — Xem thống kê, báo cáo phòng khám

## Môi trường

- FE: `http://localhost:1420`
- BE: `http://localhost:8002` (Docker `clinic_cms_w2e_api`)
- DB: PostgreSQL port 5434

## Tài khoản test

| Role | Username | Password |
|------|----------|----------|
| Administrator | admin | Demo@1234 |
| Doctor | dr_nguyen | Doctor@1234 |
| Nurse | nurse_lan | Nurse@1234 |
| Receptionist | recept_anh | Recept@1234 |
| Pharmacist | pharm_cuong | Pharm@1234 |
| Cashier | cashier_em | Cashier@1234 |

## Test Cases

Xem: `deliveries/test-cases/test-cases.md`

## Deliverables

- `deliveries/test-cases/test-cases.md` — Test cases chi tiết
- `deliveries/test-reports/test-report-TASK-078.md` — Kết quả test E2E
