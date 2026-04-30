# MediZen — Danh mục chức năng (Function List)

> **Mục đích**: liệt kê toàn bộ chức năng (function/feature) của hệ thống, nhóm theo domain. Dùng làm:
> - Checklist phát triển (track xong/chưa xong)
> - Đầu vào cho test plan, demo script, marketing collateral
> - Mapping với task implementation
> - Đầu vào cho AI thiết kế giao diện (mỗi function = ít nhất 1 UI affordance)
>
> **Cập nhật**: 2026-04-30
> **Format**: Code | Tên chức năng | Mô tả ngắn | Role | Phase | Task | Status
> **Phase**: v1 (MVP, Q2 2026) | v2 (Phase 2, Q3-Q4) | v3 (Phase 3, 2027+)
> **Status**: ✅ DONE | 🔄 IN_PROGRESS | ⬜ TODO | 💡 IDEA

---

## 0. Mục lục

1. [AUTH — Xác thực & Phiên](#1-auth--xác-thực--phiên)
2. [RBAC — Phân quyền](#2-rbac--phân-quyền)
3. [TENANT — Đăng ký & Onboarding phòng khám](#3-tenant--đăng-ký--onboarding-phòng-khám)
4. [SUB — Subscription & Billing](#4-sub--subscription--billing)
5. [PATIENT — Quản lý bệnh nhân](#5-patient--quản-lý-bệnh-nhân)
6. [VISIT — Quản lý visit/lượt khám](#6-visit--quản-lý-visit-lượt-khám)
7. [VITAL — Sinh hiệu](#7-vital--sinh-hiệu)
8. [DIAG — Chẩn đoán & Bệnh án](#8-diag--chẩn-đoán--bệnh-án)
9. [SVC — Dịch vụ y tế](#9-svc--dịch-vụ-y-tế)
10. [RX — Đơn thuốc](#10-rx--đơn-thuốc)
11. [MED — Thuốc & Tồn kho](#11-med--thuốc--tồn-kho)
12. [PHRM — Cấp phát dược](#12-phrm--cấp-phát-dược)
13. [APPT — Hẹn khám & Hàng đợi](#13-appt--hẹn-khám--hàng-đợi)
14. [BILL — Thanh toán & Hóa đơn](#14-bill--thanh-toán--hóa-đơn)
15. [HR — Nhân sự](#15-hr--nhân-sự)
16. [RPT — Báo cáo & Phân tích](#16-rpt--báo-cáo--phân-tích)
17. [NOTI — Thông báo](#17-noti--thông-báo)
18. [AUDIT — Audit log & Compliance](#18-audit--audit-log--compliance)
19. [CFG — Cấu hình phòng khám](#19-cfg--cấu-hình-phòng-khám)
20. [PLT — Platform Admin (Super Admin)](#20-plt--platform-admin-super-admin)
21. [JOB — Background Jobs](#21-job--background-jobs)
22. [DATA — Import/Export/Backup](#22-data--importexportbackup)
23. [INT — Integrations](#23-int--integrations)
24. [I18N — Localization & A11y](#24-i18n--localization--a11y)
25. [NAV — Navigation & Quick Search](#25-nav--navigation--quick-search)
26. [NFR — Non-functional requirements](#26-nfr--non-functional-requirements)

**Tổng kết**: §27 · **Cách dùng**: §28

---

## 1. AUTH — Xác thực & Phiên

| Code | Tên | Mô tả | Role | Phase | Task | Status |
|---|---|---|---|---|---|---|
| AUTH-001 | Đăng nhập email/password | Login bằng `email` (hoặc `username`) + `password` — KHÔNG cần `clinic_code`. Sau khi xác thực OK, hệ thống resolve default clinic của account → set context + trả JWT chứa `account_id` + `clinic_id` + `roles` + `perms` | Tất cả | v1 | TASK-003 | 🔄 (cần migrate khỏi clinic_code) |
| AUTH-002 | Refresh token | Refresh access token bằng refresh token (rolling) | Tất cả | v1 | TASK-003 | ✅ |
| AUTH-003 | Logout | Revoke refresh token, xoá local storage | Tất cả | v1 | TASK-003 | ✅ |
| AUTH-004 | Đổi mật khẩu | User tự đổi password | Tất cả | v1 | TASK-003 | ✅ |
| AUTH-005 | Forced change password | Bắt đổi password lần đầu / sau reset | Tất cả | v1 | TASK-003 | ✅ |
| AUTH-006 | Account lockout | Lock account sau N lần fail (default 5/15min) | System | v1 | TASK-003 | ✅ |
| AUTH-007 | Rate limit | Rate limit login attempts per IP | System | v1 | TASK-003 | ✅ |
| AUTH-008 | Reset password (admin gen) | Admin clinic generate password mới cho nhân viên | Clinic Admin | v1 | TASK-006 | ⬜ |
| AUTH-009 | Forgot password (self-service) | User tự reset qua email link | Tất cả | v2 | TASK-027 | ⬜ |
| AUTH-010 | MFA TOTP | 2FA bằng authenticator app | Tất cả | v2 | — | 💡 |
| AUTH-011 | MFA bắt buộc cho super admin | Platform admin login phải có MFA | Super Admin | v2 | TASK-026 | 💡 |
| AUTH-012 | Session timeout | Auto-logout sau N phút inactive (default 30p) | Tất cả | v1 | TASK-003 | ✅ |
| AUTH-013 | Show password toggle | UI Eye/EyeOff icon | Tất cả | v1 | TASK-017 | ✅ |
| AUTH-014 | Remember me | Lưu credentials cho lần login sau (Tauri secure storage) | Tất cả | v1 | TASK-017 | ✅ |
| AUTH-015 | Last login tracking | Hiển thị thời gian login lần cuối | Tất cả | v1 | TASK-003 | ✅ |
| AUTH-016 | IP whitelist (super admin) | Chỉ login admin từ IP whitelist | Super Admin | v2 | TASK-026 | 💡 |
| AUTH-017 | Re-authentication | Yêu cầu nhập password trước action nguy hiểm | Admin | v2 | — | 💡 |
| AUTH-018 | Account ↔ Multi-clinic mapping | 1 account (email unique global) → N phòng khám. Bảng pivot `account_clinic_role` (account_id, clinic_id, roles[], is_default, granted_at, granted_by). Owner clinic mời user đã tồn tại → chỉ thêm row pivot, KHÔNG tạo account mới. Account có thể bị revoke khỏi 1 clinic mà không xoá account. | Clinic Admin | v1 | TASK-006 | ⬜ |
| AUTH-019 | Default clinic per account | Mỗi account chọn 1 phòng khám mặc định (`is_default=true` trong pivot). Sau login auto-load context default. User tự đổi default trong Profile. | Tất cả | v1 | TASK-006 | ⬜ |
| AUTH-020 | Auto-resolve clinic post-login | Khi login OK, BE đọc `account_clinic_role`: chỉ 1 clinic → auto select; có default → load default; không default + nhiều clinic → trả list để FE hiện màn "Chọn phòng khám" trước khi vào dashboard. | System | v1 | TASK-006 | ⬜ |
| AUTH-021 | Switch-clinic flow + JWT reset | Khi user switch clinic (qua NAV-002), BE revoke JWT cũ, sinh JWT mới với `clinic_id` + `roles` + `perms` mới (RBAC khác giữa các clinic). Clear FE cache (zustand + react-query) tránh leak data clinic cũ. | System | v1 | TASK-003 | ⬜ |
| AUTH-022 | Last-active clinic remembered | Lưu clinic dùng cuối (Tauri local storage + Redis `user:last_clinic:{uid}`). Login sau auto chọn clinic này (override `default_clinic_id` nếu có). | System | v1 | TASK-003 | ⬜ |

---

## 2. RBAC — Phân quyền

| Code | Tên | Mô tả | Role | Phase | Task | Status |
|---|---|---|---|---|---|---|
| RBAC-001 | 5 system roles | Admin / Doctor / Nurse / Pharmacist / Receptionist | System | v1 | TASK-004 | ✅ |
| RBAC-002 | Permission catalog (38 perms) | Theo BA §13.5 | System | v1 | TASK-004 | ✅ |
| RBAC-003 | Multi-role per user | 1 user có nhiều role | Tất cả | v1 | TASK-004 | ✅ |
| RBAC-004 | Extra grant per user | Cấp thêm permission ngoài role | Clinic Admin | v1 | TASK-004 | ✅ |
| RBAC-005 | Extra deny per user | Chặn permission khỏi user dù role có | Clinic Admin | v1 | TASK-004 | ✅ |
| RBAC-006 | Permission cache | JWT 15p + Redis 5p | System | v1 | TASK-004 | ✅ |
| RBAC-007 | Cache invalidation | Khi role/perm đổi → clear cache user | System | v1 | TASK-004 | ✅ |
| RBAC-008 | Clone system role | Copy system role → clinic-specific để custom | Clinic Admin | v1 | TASK-004 | ✅ |
| RBAC-009 | System role immutable | Không cho sửa/xóa system role | System | v1 | TASK-004 | ✅ |
| RBAC-010 | Custom role CRUD | Clinic admin tạo custom role mới | Clinic Admin | v2 | TASK-023 | ⬜ |
| RBAC-011 | Permission group UI | Hiển thị perm theo nhóm (Patient/Visit/Pharmacy/...) | Clinic Admin | v1 | TASK-023 | ⬜ |
| RBAC-012 | Role description | Mỗi role có mô tả khi nào dùng | Clinic Admin | v1 | TASK-023 | ⬜ |
| RBAC-013 | Audit role changes | Mọi thay đổi role/perm ghi audit | System | v1 | TASK-002 | ✅ |
| RBAC-014 | Platform RBAC tách biệt | `platform_role` + `platform_permission` riêng | System | v1 | TASK-026 | ⬜ |
| RBAC-015 | Applied role trong audit | Mỗi action ghi audit log với field `applied_role` — role mà user đang dùng khi thực hiện action. VD user kiêm BS+QT sửa giá DV → ghi `applied_role=admin`; user đó kê đơn → `applied_role=doctor`. Truy vết khi sự cố. | System | v1 | TASK-002 | ⬜ |
| RBAC-016 | Separation of Duties (SoD) | Enforce trên audit-critical action. VD user kiêm BS+DS KHÔNG được tự duyệt đơn của chính mình; user tạo đề xuất giá KHÔNG được self-approve. UI disabled + tooltip giải thích, BE check 403. | System | v1 | TASK-004 | ⬜ |
| RBAC-017 | Merge sidebar cho multi-role | UI hiển thị UNION tất cả module mà user có quyền (qua mọi role) — KHÔNG có role-switcher. Sidebar group label phân tách "─── Bác sĩ ───" / "─── Quản trị ───". Xem `medizen-modern/MULTI_ROLE_UX.md`. | All | v1 | TASK-017 | ⬜ |
| RBAC-018 | Multi-role chip ở avatar | Hiển thị tất cả role hiện hành ở sidebar footer + topbar avatar badge ("+2"). Hover thấy full list + ngày được cấp. | All | v1 | TASK-017 | ⬜ |

---

## 3. TENANT — Đăng ký & Onboarding phòng khám

| Code | Tên | Mô tả | Role | Phase | Task | Status |
|---|---|---|---|---|---|---|
| TENT-001 | Self-signup form | Form công khai trên landing page | Visitor | v1 | TASK-006 | ⬜ |
| TENT-002 | Email verification | Send + click link xác thực email | Visitor | v1 | TASK-006 | ⬜ |
| TENT-003 | Tạo clinic + admin user | Atomic create cả 2 trong 1 transaction | System | v1 | TASK-006 | ⬜ |
| TENT-004 | Clone system roles cho clinic mới | 5 role cloned tự động | System | v1 | TASK-006 | ⬜ |
| TENT-005 | First-time login wizard | 4-step wizard sau lần login đầu | Clinic Admin | v1 | TASK-006 | ⬜ |
| TENT-006 | Chọn vital preset | General/Pediatric/Dental/OBGYN/TCM | Clinic Admin | v1 | TASK-006 | ⬜ |
| TENT-007 | Cấu hình prefix code | invoice/patient/visit number prefix | Clinic Admin | v1 | TASK-006 | ⬜ |
| TENT-008 | Lead form (Liên hệ tư vấn) | Form public → notify super admin | Visitor | v1 | TASK-026 | ⬜ |
| TENT-009 | Sales-led tạo clinic | Super admin tạo clinic + admin manual | Super Admin | v1 | TASK-026 | ⬜ |
| TENT-010 | Convert lead → clinic | One-click từ lead detail → tạo clinic pre-fill info | Super Admin | v1 | TASK-026 | ⬜ |
| TENT-011 | Suspend invite link | Link verify email TTL 24h, single-use | System | v1 | TASK-006 | ⬜ |
| TENT-012 | Invite resend | User nhấn "Gửi lại email" nếu hết hạn | System | v1 | TASK-006 | ⬜ |
| TENT-013 | Clinic code uniqueness | Validate code không trùng across all clinics | System | v1 | TASK-006 | ⬜ |
| TENT-014 | reCAPTCHA on signup | Chống bot spam | System | v1 | TASK-029 | ⬜ |

---

## 4. SUB — Subscription & Billing (provider side)

| Code | Tên | Mô tả | Role | Phase | Task | Status |
|---|---|---|---|---|---|---|
| SUB-001 | Subscription type | trial / paid | System | v1 | TASK-026 | ⬜ |
| SUB-002 | Billing cycle | monthly / yearly / perpetual | System | v1 | TASK-026 | ⬜ |
| SUB-003 | Trial 14 ngày default | Auto set khi self-signup | System | v1 | TASK-026 | ⬜ |
| SUB-004 | Grace period 7d/14d/0d | Theo cycle (monthly/yearly/trial) | System | v1 | TASK-026 | ⬜ |
| SUB-005 | Subscription state machine | pending → active → grace → expired → suspended → archived | System | v1 | TASK-026 | ⬜ |
| SUB-006 | SubscriptionGuard middleware | Check status mỗi request, gate API | System | v1 | TASK-026 | ⬜ |
| SUB-007 | Behavior matrix per status | Định nghĩa GET/POST allowed per status | System | v1 | TASK-026 | ⬜ |
| SUB-008 | Read-only mode khi expired | Cho GET, chặn POST/PATCH/DELETE | System | v1 | TASK-026 | ⬜ |
| SUB-009 | Banner cảnh báo trial/grace | UI top banner trong clinic app | Clinic Admin | v1 | TASK-006 | ⬜ |
| SUB-010 | Subscription event audit | clinic_subscription_event table log mọi thay đổi | System | v1 | TASK-026 | ⬜ |
| SUB-011 | Renewal manual (super admin) | Form gia hạn + lý do | Super Admin | v1 | TASK-026 | ⬜ |
| SUB-012 | Convert trial → paid | Sales-led, super admin click | Super Admin | v1 | TASK-026 | ⬜ |
| SUB-013 | Upgrade plan | Đổi cycle (monthly→yearly) | Super Admin | v1 | TASK-026 | ⬜ |
| SUB-014 | Suspend clinic | Manual với reason + visible toggle | Super Admin | v1 | TASK-026 | ⬜ |
| SUB-015 | Reactivate clinic | Từ suspended → active | Super Admin | v1 | TASK-026 | ⬜ |
| SUB-016 | Archive clinic | Đóng tài khoản, giữ data 90d | Super Admin | v1 | TASK-026 | ⬜ |
| SUB-017 | Auto export trước hard delete | Trigger export final + email link 30d trước xoá | System | v1 | TASK-028 | ⬜ |
| SUB-018 | Hard delete sau 90d | Cron xoá vĩnh viễn data archived | System | v1 | TASK-028 | ⬜ |
| SUB-019 | Reminder D-14/-7/-3/-1/0 | Cron gửi email + in-app banner | System | v1 | TASK-028 | ⬜ |
| SUB-020 | Daily reminder trong grace | Banner ngày càng đỏ | System | v1 | TASK-028 | ⬜ |
| SUB-021 | Subscription metrics dashboard | MRR, ARR, churn, conversion | Super Admin | v1 | TASK-030 | ⬜ |
| SUB-022 | Auto-renew payment integration | VNPay/MoMo webhook | Super Admin | v2 | — | 💡 |
| SUB-023 | E-invoice integration | Xuất hóa đơn điện tử cho clinic (VNPT/Viettel) | Super Admin | v2 | — | 💡 |
| SUB-024 | Subscription tiers (Basic/Pro/Enterprise) | Phase 2 — chia gói theo limit | Super Admin | v2 | — | 💡 |
| SUB-025 | Free tier vĩnh viễn (siêu hạn chế) | Phase 2 reconsider | Super Admin | v2 | — | 💡 |

---

## 5. PATIENT — Quản lý bệnh nhân

| Code | Tên | Mô tả | Role | Phase | Task | Status |
|---|---|---|---|---|---|---|
| PAT-001 | Tạo bệnh nhân mới | Form đăng ký đầy đủ | Receptionist+ | v1 | TASK-005 | ✅ |
| PAT-002 | Auto-gen patient_code | BN0001, BN0002... per clinic | System | v1 | TASK-005 | ✅ |
| PAT-003 | Xem hồ sơ chi tiết | Profile + lịch sử | Doctor+ | v1 | TASK-005 | ✅ |
| PAT-004 | Sửa thông tin BN | Edit basic info | Receptionist+ | v1 | TASK-005 | ✅ |
| PAT-005 | Soft-delete BN | Đánh dấu xoá, vẫn giữ data | Admin | v1 | TASK-005 | ✅ |
| PAT-006 | Search theo SĐT | Exact match | Receptionist+ | v1 | TASK-005 | ✅ |
| PAT-007 | Search theo tên (fuzzy) | Trigram + unaccent | Receptionist+ | v1 | TASK-005 | ✅ |
| PAT-008 | Search theo mã BN | Exact match patient_code | Receptionist+ | v1 | TASK-005 | ✅ |
| PAT-009 | Performance: 100k record <100ms | AC: phone search p95<100ms | System | v1 | TASK-005 | ✅ |
| PAT-010 | Guardian relationship | Thêm người giám hộ (cha/mẹ/...) | Receptionist+ | v1 | TASK-005 | ✅ |
| PAT-011 | Primary contact flag | 1 guardian là contact chính | Receptionist+ | v1 | TASK-005 | ✅ |
| PAT-012 | Merge duplicate BN | Gộp 2 hồ sơ trùng | Admin | v1 | TASK-005 | ✅ |
| PAT-013 | Undo merge (7 ngày) | Khôi phục merge | Admin | v1 | TASK-005 | ✅ |
| PAT-014 | BHYT info | Số thẻ + ngày hết hạn | Receptionist+ | v1 | TASK-005 | ✅ |
| PAT-015 | Allergies tracking | List dị ứng — cảnh báo khi kê thuốc | Doctor+ | v1 | TASK-005 | ✅ |
| PAT-016 | Chronic conditions | Tiền sử bệnh mãn tính | Doctor+ | v1 | TASK-005 | ✅ |
| PAT-017 | Blood type | Nhóm máu | Doctor+ | v1 | TASK-005 | ✅ |
| PAT-018 | DOB hoặc birth_year | Cho phép chỉ nhập năm sinh | Receptionist+ | v1 | TASK-005 | ✅ |
| PAT-019 | Đính kèm tài liệu | Upload CMND/BHYT/XQuang | Receptionist+ | v1 | TASK-005 | ⬜ (storage chưa wire) |
| PAT-020 | Audit patient.read | Mỗi lần đọc PHI ghi log | System | v1 | TASK-005 | ✅ |
| PAT-021 | Export hồ sơ BN | PDF tổng hợp | Doctor+ | v2 | — | 💡 |
| PAT-022 | Bulk import CSV | Import từ hệ thống cũ | Admin | v2 | — | 💡 |

---

## 6. VISIT — Quản lý visit/lượt khám

| Code | Tên | Mô tả | Role | Phase | Task | Status |
|---|---|---|---|---|---|---|
| VIS-001 | Tạo visit | Walk-in hoặc từ appointment | Receptionist+ | v1 | TASK-007 | ✅ |
| VIS-002 | Auto-gen visit_number | KB-2026-04-30-0001 per clinic per day | System | v1 | TASK-007 | ✅ |
| VIS-003 | Visit state machine | WAITING_VITAL → IN_CONSULTATION → COMPLETED | System | v1 | TASK-007 | ✅ |
| VIS-004 | NO_SHOW status | Đánh dấu BN không đến | Receptionist+ | v1 | TASK-007 | ✅ |
| VIS-005 | CANCELLED status | Hủy visit | Receptionist+ | v1 | TASK-007 | ✅ |
| VIS-006 | PAUSED status | Tạm dừng visit (đi xét nghiệm...) | Doctor | v1 | TASK-007 | ✅ |
| VIS-007 | Resume visit | Tiếp tục sau pause | Doctor | v1 | TASK-007 | ✅ |
| VIS-008 | Lịch sử visit của BN | Hiển thị trong patient detail | Doctor+ | v1 | TASK-005 | ✅ |
| VIS-009 | Visit doctor assignment | Chọn bác sĩ khám | Receptionist+ | v1 | TASK-007 | ✅ |
| VIS-010 | Reassign doctor | Đổi bác sĩ giữa visit | Admin | v1 | TASK-007 | ✅ |
| VIS-011 | Visit reason | Lý do khám (free text) | Receptionist+ | v1 | TASK-007 | ✅ |
| VIS-012 | Concurrent call-next safe | Multiple doctors call cùng lúc không bị race | System | v1 | TASK-007 | ✅ |
| VIS-013 | Visit completion auto-trigger | Auto-create draft invoice + route Rx | System | v1 | TASK-007 | ✅ |
| VIS-014 | Tài liệu đính kèm visit | Upload kết quả XN, XQuang | Doctor | v1 | TASK-007 | ⬜ (storage) |

---

## 7. VITAL — Sinh hiệu

| Code | Tên | Mô tả | Role | Phase | Task | Status |
|---|---|---|---|---|---|---|
| VTL-001 | 5 specialty preset | General/Pediatric/Dental/OBGYN/TCM | System | v1 | TASK-009 | ⬜ |
| VTL-002 | Dynamic field schema | JSON schema linh hoạt | System | v1 | TASK-009 | ⬜ |
| VTL-003 | Field types: number/text/select/bool | Validation theo type | System | v1 | TASK-009 | ⬜ |
| VTL-004 | Range bình thường | Trên/dưới range warning | System | v1 | TASK-009 | ⬜ |
| VTL-005 | Auto-calc fields | BMI từ weight+height | System | v1 | TASK-009 | ⬜ |
| VTL-006 | Vital trends chart | Biểu đồ huyết áp/cân nặng theo time | Doctor | v1 | TASK-009 | ⬜ |
| VTL-007 | Schema editor (admin) | Custom thêm/bớt field per clinic | Clinic Admin | v1 | TASK-009 | ⬜ |
| VTL-008 | Schema versioning | Đổi schema không phá visit cũ | System | v1 | TASK-009 | ⬜ |
| VTL-009 | Pediatric percentile chart | Chiều cao/cân nặng vs WHO | Doctor | v2 | — | 💡 |
| VTL-010 | OBGYN tuần thai tracker | Theo dõi qua nhiều visit | Doctor | v2 | — | 💡 |
| VTL-011 | TCM mạch/lưỡi (free text) | Y học cổ truyền | Doctor | v1 | TASK-009 | ⬜ |
| VTL-012 | Required field per preset | General require BP, Pediatric require head circumference | System | v1 | TASK-009 | ⬜ |
| VTL-013 | Vital input by nurse | Nurse fill trước, doctor verify | Nurse | v1 | TASK-009 | ⬜ |
| VTL-014 | Vital alert thresholds | Highlight đỏ nếu BP >140/90 | System | v1 | TASK-009 | ⬜ |

---

## 8. DIAG — Chẩn đoán & Bệnh án

| Code | Tên | Mô tả | Role | Phase | Task | Status |
|---|---|---|---|---|---|---|
| DIAG-001 | Chẩn đoán chính + phụ | Primary + multi secondary | Doctor | v1 | TASK-007 | ✅ |
| DIAG-002 | Khám lâm sàng (free text) | Rich text editor | Doctor | v1 | TASK-007 | ✅ |
| DIAG-003 | ICD-10 autocomplete | Search code/tên bệnh | Doctor | v1 | TASK-007 | ✅ |
| DIAG-004 | ICD-10 catalog (Vietnamese) | Master DB ICD-10 dịch VN | System | v1 | TASK-007 | ✅ |
| DIAG-005 | Diagnosis history | Lịch sử chẩn đoán BN | Doctor | v1 | TASK-005 | ✅ |
| DIAG-006 | Lời dặn cuối visit | Free text instructions | Doctor | v1 | TASK-007 | ✅ |
| DIAG-007 | Lịch tái khám | Suggest ngày tái khám | Doctor | v1 | TASK-007 | ✅ |
| DIAG-008 | Diagnosis templates | Save common diagnosis cho dùng lại | Doctor | v2 | — | 💡 |
| DIAG-009 | Voice-to-text input | Đọc khám lâm sàng | Doctor | v3 | — | 💡 |

---

## 9. SVC — Dịch vụ y tế

| Code | Tên | Mô tả | Role | Phase | Task | Status |
|---|---|---|---|---|---|---|
| SVC-001 | Service catalog CRUD | Tên, giá, phân loại, thời lượng | Clinic Admin | v1 | TASK-010 | ⬜ |
| SVC-002 | Service phân loại | Khám/XN/Thủ thuật/Siêu âm/X-quang | System | v1 | TASK-010 | ⬜ |
| SVC-003 | Multi-price (BHYT vs trực tiếp) | 2 mức giá per service | Clinic Admin | v1 | TASK-010 | ⬜ |
| SVC-004 | Service-doctor mapping | Service nào doctor nào thực hiện được | Clinic Admin | v1 | TASK-010 | ⬜ |
| SVC-005 | Service packages | Gói "Khám tổng quát" gồm nhiều service | Clinic Admin | v2 | — | 💡 |
| SVC-006 | Add service vào visit | Doctor chỉ định service trong visit | Doctor | v1 | TASK-010 | ⬜ |
| SVC-007 | VisitService tracking | Performed services per visit | System | v1 | TASK-010 | ⬜ |
| SVC-008 | Service revenue report | Doanh thu theo service | Admin | v1 | TASK-015 | ⬜ |
| SVC-009 | Service price history | Audit thay đổi giá | System | v1 | TASK-002 | ✅ |

---

## 10. RX — Đơn thuốc

| Code | Tên | Mô tả | Role | Phase | Task | Status |
|---|---|---|---|---|---|---|
| RX-001 | Tạo đơn thuốc | Multi-medicine với liều/cách dùng | Doctor | v1 | TASK-011 | ⬜ |
| RX-002 | Auto-gen Rx number | RX-2026-04-30-0001 | System | v1 | TASK-011 | ⬜ |
| RX-003 | Internal vs External | Internal = clinic bán, External = mua ngoài | Doctor | v1 | TASK-011 | ⬜ |
| RX-004 | Liều dùng (sáng/trưa/tối) | Segmented control + trước/sau ăn | Doctor | v1 | TASK-011 | ⬜ |
| RX-005 | Số ngày → auto qty | Tính số lượng từ liều × ngày | System | v1 | TASK-011 | ⬜ |
| RX-006 | Cảnh báo dị ứng | Match medicine với patient.allergies | System | v1 | TASK-011 | ⬜ |
| RX-007 | Drug interaction warning | Check tương tác giữa các thuốc trong đơn | System | v2 | — | 💡 |
| RX-008 | Drug-condition warning | Check chống chỉ định với chronic_conditions | System | v2 | — | 💡 |
| RX-009 | In đơn thuốc | A5 hoặc A4 với layout chuẩn | Doctor | v1 | TASK-011 | ⬜ |
| RX-010 | QR code in đơn | Verify đơn thuốc qua QR | System | v2 | — | 💡 |
| RX-011 | Edit đơn (trước dispense) | Doctor sửa lại đơn nếu cần | Doctor | v1 | TASK-011 | ⬜ |
| RX-012 | Cancel đơn | Doctor cancel đơn (trước dispense) | Doctor | v1 | TASK-011 | ⬜ |
| RX-013 | Lịch sử đơn của BN | Hiển thị trong patient detail | Doctor | v1 | TASK-005 | ⬜ |
| RX-014 | Đơn template | Save đơn common cho dùng lại | Doctor | v2 | — | 💡 |
| RX-015 | Reserve stock | Khi tạo đơn internal → reserve tồn kho | System | v1 | TASK-012 | ⬜ |
| RX-016 | Hiển thị stock thuốc khi kê đơn | Mỗi card thuốc trong form kê đơn hiển thị real-time tồn kho (số lượng còn + đơn vị). Chip emerald "✓ Còn 320 viên" / amber "⚠ Còn 12 viên" (dưới min) / red "✕ Hết hàng — đề xuất thay thế". Hover tooltip hiện breakdown theo lô (FEFO, HSD). Nếu kê quá tồn → cảnh báo "Vượt tồn kho — chỉ kê được 12 viên" + button "Đề xuất thuốc tương đương". Filter chip "Chỉ hiện thuốc còn hàng" default ON. Loại "External" (mua ngoài) không hiển thị stock. | Doctor | v1 | TASK-011 | ⬜ |

---

## 11. MED — Thuốc & Tồn kho

| Code | Tên | Mô tả | Role | Phase | Task | Status |
|---|---|---|---|---|---|---|
| MED-001 | Medicine catalog CRUD | Tên/hoạt chất/hàm lượng/dạng/đơn vị | Clinic Admin | v1 | TASK-011 | ⬜ |
| MED-002 | Phân loại thuốc | Kê đơn / OTC / kiểm soát đặc biệt | Clinic Admin | v1 | TASK-011 | ⬜ |
| MED-003 | Multi-unit conversion | 1 hộp = 10 vỉ × 10 viên | System | v1 | TASK-011 | ⬜ |
| MED-004 | Min/max stock alert | Cảnh báo dưới min, vượt max | System | v1 | TASK-012 | ⬜ |
| MED-005 | Lot/batch tracking | Mỗi lô có HSD + số lô | System | v1 | TASK-012 | ⬜ |
| MED-006 | Stock movement audit | In/out với lý do, audit trail | System | v1 | TASK-012 | ⬜ |
| MED-007 | Expiry tracking | Cảnh báo 30/60/90 ngày trước HSD | System | v1 | TASK-012 | ⬜ |
| MED-008 | FEFO suggestion | First-Expired-First-Out gợi ý lô | System | v1 | TASK-012 | ⬜ |
| MED-009 | Stock import (PO) | Phiếu nhập từ supplier | Pharmacist | v1 | TASK-012 | ⬜ |
| MED-010 | Stock adjustment | Điều chỉnh tồn kho khi kiểm kê | Pharmacist | v1 | TASK-012 | ⬜ |
| MED-011 | Adjustment approval | Admin duyệt phiếu điều chỉnh | Admin | v1 | TASK-012 | ⬜ |
| MED-012 | Reorder suggestion | Auto-suggest nhập theo tốc độ tiêu thụ | System | v2 | — | 💡 |
| MED-013 | Substitute medicine | Tương đương khi hết hàng | Pharmacist | v2 | — | 💡 |
| MED-014 | Supplier catalog | Quản lý nhà cung cấp | Clinic Admin | v1 | TASK-012 | ⬜ |
| MED-015 | Cost tracking | Giá vốn lịch sử + GW average | System | v1 | TASK-012 | ⬜ |
| MED-016 | Margin report | Báo cáo lợi nhuận thuốc | Admin | v1 | TASK-015 | ⬜ |
| MED-017 | Barcode scan | Scan barcode khi xuất/nhập (Phase 2) | Pharmacist | v2 | — | 💡 |
| MED-018 | Bulk import CSV catalog | Import từ Excel | Clinic Admin | v2 | — | 💡 |

---

## 12. PHRM — Cấp phát dược

| Code | Tên | Mô tả | Role | Phase | Task | Status |
|---|---|---|---|---|---|---|
| PHRM-001 | Pending dispense queue | List đơn chờ cấp | Pharmacist | v1 | TASK-012 | ⬜ |
| PHRM-002 | Dispense screen | Confirm + chọn lô | Pharmacist | v1 | TASK-012 | ⬜ |
| PHRM-003 | Lot selection | FEFO suggested, override được | Pharmacist | v1 | TASK-012 | ⬜ |
| PHRM-004 | Multi-lot dispense | Chia 1 row thành nhiều lô | Pharmacist | v1 | TASK-012 | ⬜ |
| PHRM-005 | Partial dispense | Cấp 1 phần đơn (out of stock) | Pharmacist | v1 | TASK-012 | ⬜ |
| PHRM-006 | Stock auto-decrement | Trừ tồn kho theo lô đã chọn | System | v1 | TASK-012 | ⬜ |
| PHRM-007 | Cảnh báo HSD lô | Show "còn N ngày HSD" khi chọn lô | System | v1 | TASK-012 | ⬜ |
| PHRM-008 | Cảnh báo thiếu hàng | "Chỉ còn X, cần Y" | System | v1 | TASK-012 | ⬜ |
| PHRM-009 | Dispense audit | Log ai cấp gì lô nào lúc nào | System | v1 | TASK-002 | ✅ |
| PHRM-010 | In nhãn thuốc | Label cho từng item (POS printer) | Pharmacist | v2 | — | 💡 |
| PHRM-011 | Auto add to invoice | Internal medicine vào draft invoice | System | v1 | TASK-013 | ⬜ |
| PHRM-012 | Reverse dispense | Hoàn tồn kho khi cancel đơn | Pharmacist | v1 | TASK-012 | ⬜ |
| PHRM-013 | Substitute confirm | Pharmacist đề xuất substitute, doctor approve | Pharmacist | v2 | — | 💡 |

---

## 13. APPT — Hẹn khám & Hàng đợi

| Code | Tên | Mô tả | Role | Phase | Task | Status |
|---|---|---|---|---|---|---|
| APPT-001 | Tạo hẹn | Form hẹn cho BN có/mới | Receptionist | v1 | TASK-008 | ⬜ |
| APPT-002 | Slot capacity per doctor | Max bao nhiêu BN/giờ | Clinic Admin | v1 | TASK-008 | ⬜ |
| APPT-003 | Calendar view | Week/month grid | Receptionist | v1 | TASK-008 | ⬜ |
| APPT-004 | Confirm appointment | Status SCHEDULED → CONFIRMED | Receptionist | v1 | TASK-008 | ⬜ |
| APPT-005 | Check-in appointment | Khi BN đến → tạo visit | Receptionist | v1 | TASK-008 | ⬜ |
| APPT-006 | Reschedule | Đổi giờ/bác sĩ | Receptionist | v1 | TASK-008 | ⬜ |
| APPT-007 | Cancel appointment | Huỷ + lý do | Receptionist | v1 | TASK-008 | ⬜ |
| APPT-008 | NO_SHOW tracking | Sau giờ hẹn 30p chưa check-in → NO_SHOW | System | v1 | TASK-008 | ⬜ |
| APPT-009 | Smart queue priority | Appointment đến giờ ưu tiên hơn walk-in | System | v1 | TASK-008 | ⬜ |
| APPT-010 | Walk-in registration | Tiếp nhận không hẹn | Receptionist | v1 | TASK-008 | ⬜ |
| APPT-011 | Queue board (TV mode) | Fullscreen hiển thị STT | System | v1 | TASK-018 | ⬜ |
| APPT-012 | Sound chime gọi STT | Beep khi gọi BN tiếp theo | System | v1 | TASK-018 | ⬜ |
| APPT-013 | Privacy mask name | "Nguyễn V.A." trên queue board | System | v1 | TASK-018 | ⬜ |
| APPT-014 | SMS reminder trước hẹn | 24h + 2h trước | System | v2 | — | 💡 |
| APPT-015 | Patient self-book | Portal tự đặt hẹn (Phase 3) | Patient | v3 | — | 💡 |
| APPT-016 | Block schedule | Doctor block giờ không nhận BN | Doctor | v1 | TASK-008 | ⬜ |
| APPT-017 | Conflict với HR shift | Validate không overlap leave/off | System | v1 | TASK-008 | ⬜ |

---

## 14. BILL — Thanh toán & Hóa đơn

| Code | Tên | Mô tả | Role | Phase | Task | Status |
|---|---|---|---|---|---|---|
| BILL-001 | Auto-gen invoice | Khi visit COMPLETED + medicine DISPENSED | System | v1 | TASK-013 | ⬜ |
| BILL-002 | Auto-gen invoice number | HD-2026-04-30-0001 prefix tuỳ chỉnh | System | v1 | TASK-013 | ⬜ |
| BILL-003 | Manual invoice | Tạo HĐ ngoài visit (vd: bán lẻ thuốc) | Receptionist | v1 | TASK-013 | ⬜ |
| BILL-004 | Add/remove line item | Sửa hóa đơn trước khi ISSUED | Receptionist | v1 | TASK-013 | ⬜ |
| BILL-005 | Multi-payment method | Cash + QR + Card cùng 1 HĐ | Receptionist | v1 | TASK-013 | ⬜ |
| BILL-006 | Cash payment | Nhập số tiền + auto-tính tiền thừa | Receptionist | v1 | TASK-013 | ⬜ |
| BILL-007 | Card payment | Manual entry số tham chiếu | Receptionist | v1 | TASK-013 | ⬜ |
| BILL-008 | QR payment | Hiện QR VietQR + verify | Receptionist | v1 | TASK-013 | ⬜ |
| BILL-009 | Bank transfer | Manual entry số tham chiếu | Receptionist | v1 | TASK-013 | ⬜ |
| BILL-010 | BHYT | Phần BHYT chi trả + phần BN trả | Receptionist | v1 | TASK-013 | ⬜ |
| BILL-011 | Discount % hoặc số tiền | Áp dụng discount | Receptionist+ | v1 | TASK-013 | ⬜ |
| BILL-012 | VAT | Tính VAT theo config | System | v1 | TASK-013 | ⬜ |
| BILL-013 | Partial payment | Ghi nhận thanh toán một phần | Receptionist | v1 | TASK-013 | ⬜ |
| BILL-014 | Outstanding balance | Theo dõi nợ chưa thanh toán | System | v1 | TASK-013 | ⬜ |
| BILL-015 | Void invoice | Huỷ HĐ với lý do (admin) | Admin | v1 | TASK-013 | ⬜ |
| BILL-016 | Void → reverse stock | Trả medicine về kho khi void | System | v1 | TASK-013 | ⬜ |
| BILL-017 | Refund | Hoàn tiền (full hoặc partial) | Admin | v1 | TASK-013 | ⬜ |
| BILL-018 | In hóa đơn POS | 58/80mm thermal printer | System | v1 | TASK-013 | ⬜ |
| BILL-019 | In hóa đơn A4 | Letterhead + watermark "Đã thanh toán" | System | v1 | TASK-013 | ⬜ |
| BILL-020 | Email hóa đơn | Gửi PDF qua email | System | v2 | — | 💡 |
| BILL-021 | Loyalty program | Tích điểm + giảm giá khách quen | System | v2 | — | 💡 |
| BILL-022 | Promotion code | Mã giảm giá | System | v2 | — | 💡 |
| BILL-023 | E-invoice (hóa đơn điện tử) | Tích hợp VNPT/Viettel | System | v2 | — | 💡 |

---

## 15. HR — Nhân sự

| Code | Tên | Mô tả | Role | Phase | Task | Status |
|---|---|---|---|---|---|---|
| HR-001 | User CRUD (clinic) | Admin tạo/sửa/xoá nhân viên | Clinic Admin | v1 | TASK-006 | ⬜ |
| HR-002 | Temp password gen | 12-char random, hiện 1 lần | System | v1 | TASK-006 | ⬜ |
| HR-003 | Magic link invite (Phase 2) | Email link đặt password | System | v2 | TASK-027 | ⬜ |
| HR-004 | Reset password (admin) | Admin reset cho user | Clinic Admin | v1 | TASK-006 | ⬜ |
| HR-005 | Disable/enable user | Toggle is_active | Clinic Admin | v1 | TASK-006 | ⬜ |
| HR-006 | License number | Chứng chỉ hành nghề (doctor/pharmacist) | Clinic Admin | v1 | TASK-006 | ⬜ |
| HR-007 | Specialty per doctor | Chuyên khoa phụ | Clinic Admin | v1 | TASK-006 | ⬜ |
| HR-008 | Shift CRUD | Tạo/sửa/xoá ca | Clinic Admin / Manager | v1 | TASK-014 | ✅ |
| HR-009 | Recurring schedule | Template tuần | Clinic Admin | v1 | TASK-014 | ✅ |
| HR-010 | Apply recurring → shifts | Generate shift từ template | System | v1 | TASK-014 | ✅ |
| HR-011 | Calendar view | Week grid lịch ca | All | v1 | TASK-022 | ⬜ |
| HR-012 | Drag to reschedule | Kéo-thả đổi ca | Manager | v2 | — | 💡 |
| HR-013 | Attendance check-in | Click button hoặc scan QR | All | v1 | TASK-014 | ✅ |
| HR-014 | Attendance check-out | End shift | All | v1 | TASK-014 | ✅ |
| HR-015 | OT calculation | Tự tính giờ OT | System | v1 | TASK-014 | ✅ |
| HR-016 | Late/early tracking | Tự đánh dấu đi muộn/về sớm | System | v1 | TASK-014 | ✅ |
| HR-017 | Leave request | Đơn nghỉ phép (annual/sick/...) | All | v1 | TASK-014 | ✅ |
| HR-018 | Leave approval | Manager duyệt | Manager | v1 | TASK-014 | ✅ |
| HR-019 | Leave balance | Theo dõi số ngày phép còn | System | v1 | TASK-014 | ✅ |
| HR-020 | Attendance report | Bảng chấm công cuối tháng | Admin | v1 | TASK-015 | ⬜ |
| HR-021 | Payroll integration | Export sang lương | System | v3 | — | 💡 |
| HR-022 | Multi-role user | 1 nhân viên kiêm 2 role | Clinic Admin | v1 | TASK-004 | ✅ |

---

## 16. RPT — Báo cáo & Phân tích

| Code | Tên | Mô tả | Role | Phase | Task | Status |
|---|---|---|---|---|---|---|
| RPT-001 | Doanh thu theo ngày/tuần/tháng | Line chart + KPI | Admin | v1 | TASK-015 | ⬜ |
| RPT-002 | Doanh thu theo bác sĩ | Breakdown per doctor | Admin | v1 | TASK-015 | ⬜ |
| RPT-003 | Doanh thu theo phương thức | Cash/Card/QR/BHYT | Admin | v1 | TASK-015 | ⬜ |
| RPT-004 | Số visit theo specialty | Phân theo chuyên khoa | Admin | v1 | TASK-015 | ⬜ |
| RPT-005 | Top thuốc dùng | Top N theo doanh thu/số lượng | Admin | v1 | TASK-015 | ⬜ |
| RPT-006 | Thuốc ít dùng | Ngược của top — gợi ý ngừng nhập | Admin | v1 | TASK-015 | ⬜ |
| RPT-007 | Tồn kho theo giá vốn | Tổng giá trị tồn kho | Admin | v1 | TASK-015 | ⬜ |
| RPT-008 | Thuốc sắp hết hạn | List 30/60/90 ngày | Pharmacist | v1 | TASK-012 | ⬜ |
| RPT-009 | No-show rate | Tỷ lệ vắng hẹn | Admin | v1 | TASK-015 | ⬜ |
| RPT-010 | Demographic BN | Phân theo tuổi/giới/tỉnh | Admin | v1 | TASK-015 | ⬜ |
| RPT-011 | Visit duration | Thời gian khám TB | Admin | v1 | TASK-015 | ⬜ |
| RPT-012 | Wait time | Thời gian chờ TB | Admin | v1 | TASK-015 | ⬜ |
| RPT-013 | Custom date range | Filter mọi report | All | v1 | TASK-015 | ⬜ |
| RPT-014 | Export CSV | Mọi report | Admin | v1 | TASK-015 | ⬜ |
| RPT-015 | Export PDF | Report đẹp có letterhead | Admin | v1 | TASK-015 | ⬜ |
| RPT-016 | Scheduled email reports | Gửi tự động hàng tuần/tháng | Admin | v2 | TASK-027 | ⬜ |
| RPT-017 | Patient retention | Tỷ lệ BN quay lại | Admin | v2 | — | 💡 |
| RPT-018 | Clinical KPIs | Outcome lâm sàng (Phase 3) | Admin | v3 | — | 💡 |

---

## 17. NOTI — Thông báo

| Code | Tên | Mô tả | Role | Phase | Task | Status |
|---|---|---|---|---|---|---|
| NOTI-001 | In-app notification | Bell icon + dropdown | All | v1 | TASK-015 | ⬜ |
| NOTI-002 | Mark as read | Click → đánh dấu đọc | All | v1 | TASK-015 | ⬜ |
| NOTI-003 | Mark all as read | Bulk action | All | v1 | TASK-015 | ⬜ |
| NOTI-004 | Notification categories | Info / Warning / Critical / Success | System | v1 | TASK-015 | ⬜ |
| NOTI-005 | Visit completion notify | Khi visit done → notify cashier | System | v1 | TASK-015 | ⬜ |
| NOTI-006 | Stock low alert | Notify pharmacist | System | v1 | TASK-015 | ⬜ |
| NOTI-007 | Subscription expiring | Notify clinic admin | System | v1 | TASK-028 | ⬜ |
| NOTI-008 | Email transactional | Verify, reset, reminder | System | v1 | TASK-027 | ⬜ |
| NOTI-009 | Email templates | Vi/En, brand-themed | System | v1 | TASK-027 | ⬜ |
| NOTI-010 | SMS notifications | Appointment reminder, OTP | System | v2 | TASK-027 | 💡 |
| NOTI-011 | Zalo OA push | Phase 3 | System | v3 | — | 💡 |
| NOTI-012 | Push notification (web) | Browser push API | System | v2 | — | 💡 |
| NOTI-013 | Tauri desktop notification | Native OS notification | System | v1 | TASK-016 | ✅ |
| NOTI-014 | User preference | Tắt theo loại notification | All | v2 | — | 💡 |
| NOTI-015 | Reminder schedule cron | Daily cron gửi reminder | System | v1 | TASK-028 | ⬜ |

---

## 18. AUDIT — Audit log & Compliance

| Code | Tên | Mô tả | Role | Phase | Task | Status |
|---|---|---|---|---|---|---|
| AUDIT-001 | Audit mọi INSERT/UPDATE/DELETE | Auto qua SQLAlchemy event | System | v1 | TASK-002 | ✅ |
| AUDIT-002 | PII redaction | Password/token redacted | System | v1 | TASK-002 | ✅ |
| AUDIT-003 | __auditable__ flag | Opt-in per model | System | v1 | TASK-002 | ✅ |
| AUDIT-004 | __audit_exclude__ | Exclude sensitive fields | System | v1 | TASK-002 | ✅ |
| AUDIT-005 | RLS row-level security | Per clinic_id auto-filter | System | v1 | TASK-002 | ✅ |
| AUDIT-006 | Tenancy middleware | Set app.current_clinic_id | System | v1 | TASK-002 | ✅ |
| AUDIT-007 | Audit patient.read | Đọc PHI ghi log riêng | System | v1 | TASK-005 | ✅ |
| AUDIT-008 | Audit log viewer (clinic) | Xem audit của clinic mình | Admin | v1 | TASK-023 | ⬜ |
| AUDIT-009 | Audit log viewer (super admin) | Cross-clinic forensic | Super Admin | v1 | TASK-030 | ⬜ |
| AUDIT-010 | Data export (PDPA) | Right to portability — export full BN data | Admin | v1 | TASK-015 | ⬜ |
| AUDIT-011 | ToS + Privacy versioning | Track version khách đồng ý | System | v1 | TASK-006 | ⬜ |
| AUDIT-012 | Consent tracking | Bệnh nhân đồng ý xử lý dữ liệu | System | v2 | — | 💡 |
| AUDIT-013 | Right to be forgotten | Xoá hoàn toàn data BN theo yêu cầu | Admin | v2 | — | 💡 |
| AUDIT-014 | DPA template | Data Processing Agreement | Legal | v1 | TASK-029 | ⬜ |
| AUDIT-015 | Cookie consent banner | GDPR-style trên landing | System | v1 | TASK-029 | ⬜ |

---

## 19. CFG — Cấu hình phòng khám

| Code | Tên | Mô tả | Role | Phase | Task | Status |
|---|---|---|---|---|---|---|
| CFG-001 | Clinic info | Tên/mã/địa chỉ/SĐT/email/MST | Clinic Admin | v1 | TASK-006 | ⬜ |
| CFG-002 | Logo upload | Hiện trên hóa đơn / app shell | Clinic Admin | v1 | TASK-006 | ⬜ |
| CFG-003 | Working hours | Lịch tuần điển hình | Clinic Admin | v1 | TASK-006 | ⬜ |
| CFG-004 | Holiday list | Auto-import VN public holidays | Clinic Admin | v1 | TASK-006 | ⬜ |
| CFG-005 | Lunch break | Default 12:00-13:30 | Clinic Admin | v1 | TASK-006 | ⬜ |
| CFG-006 | Invoice prefix | HD- prefix tuỳ chỉnh | Clinic Admin | v1 | TASK-006 | ⬜ |
| CFG-007 | Patient code prefix | BN- prefix tuỳ chỉnh | Clinic Admin | v1 | TASK-006 | ⬜ |
| CFG-008 | Visit number prefix | KB- prefix tuỳ chỉnh | Clinic Admin | v1 | TASK-006 | ⬜ |
| CFG-009 | VAT rate | Default 5%, tuỳ chỉnh | Clinic Admin | v1 | TASK-006 | ⬜ |
| CFG-010 | Currency | VND default | System | v1 | TASK-006 | ✅ |
| CFG-011 | Timezone | Asia/Ho_Chi_Minh default | System | v1 | TASK-006 | ✅ |
| CFG-012 | Default language | vi/en | Clinic Admin | v1 | TASK-006 | ✅ |
| CFG-013 | Vital schema editor | Tuỳ chỉnh fields per specialty | Clinic Admin | v1 | TASK-009 | ⬜ |
| CFG-014 | Service category management | CRUD phân loại service | Clinic Admin | v1 | TASK-010 | ⬜ |
| CFG-015 | Discount policy | Cấu hình policy giảm giá | Clinic Admin | v2 | — | 💡 |
| CFG-016 | Medicine warning rules | Custom dị ứng/tương tác per clinic | Clinic Admin | v2 | — | 💡 |
| CFG-017 | Toggle BHYT bật/tắt | Feature flag `clinic.bhyt_enabled` (default OFF). Khi OFF: ẩn module BHYT khỏi sidebar, ẩn cột BHYT trong bảng giá, ẩn ô BHYT khi tiếp nhận, bỏ split BHYT trong đơn thuốc/CLS/hoá đơn, ẩn tab Báo cáo BHYT. Khi ON: yêu cầu nhập Mã cơ sở KCB. Confirm modal khi đổi state. | Clinic Admin | v1 | TASK-006 | ⬜ |

---

## 20. PLT — Platform Admin (Super Admin)

| Code | Tên | Mô tả | Role | Phase | Task | Status |
|---|---|---|---|---|---|---|
| PLT-001 | Platform user CRUD | Quản lý team super admin | Super Admin | v1 | TASK-026 | ⬜ |
| PLT-002 | Platform role CRUD | support/sales/finance/devops roles | Super Admin | v1 | TASK-026 | ⬜ |
| PLT-003 | Clinic list + filter | List all clinics across platform | Super Admin | v1 | TASK-030 | ⬜ |
| PLT-004 | Clinic detail panel | Metadata + counts (no PHI) | Super Admin | v1 | TASK-030 | ⬜ |
| PLT-005 | Tạo clinic + admin (sales-led) | 3-step wizard | Super Admin | v1 | TASK-030 | ⬜ |
| PLT-006 | Convert trial → paid | Form upgrade subscription | Super Admin | v1 | TASK-030 | ⬜ |
| PLT-007 | Renew subscription | Manual renewal entry | Super Admin | v1 | TASK-030 | ⬜ |
| PLT-008 | Suspend clinic | Manual với reason | Super Admin | v1 | TASK-030 | ⬜ |
| PLT-009 | Reactivate clinic | Resume từ suspended | Super Admin | v1 | TASK-030 | ⬜ |
| PLT-010 | Archive clinic | Đóng tài khoản | Super Admin | v1 | TASK-030 | ⬜ |
| PLT-011 | Reset clinic admin password | Cho khách quên password | Super Admin | v1 | TASK-030 | ⬜ |
| PLT-012 | Lead management | List/filter lead từ landing | Super Admin | v1 | TASK-030 | ⬜ |
| PLT-013 | Convert lead → clinic | One-click pre-fill | Super Admin | v1 | TASK-030 | ⬜ |
| PLT-014 | Platform metrics dashboard | MRR/ARR/churn/conversion | Super Admin | v1 | TASK-030 | ⬜ |
| PLT-015 | Subscription expiring view | List sắp hết hạn | Super Admin | v1 | TASK-030 | ⬜ |
| PLT-016 | Cross-clinic audit log | Forensic search | Super Admin | v1 | TASK-030 | ⬜ |
| PLT-017 | System config | Rate limits / feature flags / JWT rotation | Super Admin | v1 | TASK-030 | ⬜ |
| PLT-018 | Feature flag UI | Bật/tắt feature per clinic hoặc global | Super Admin | v1 | TASK-030 | ⬜ |
| PLT-019 | PHI access prohibited | Vật lý không thể đọc patient/visit/Rx | System | v1 | TASK-026 | ⬜ |
| PLT-020 | Impersonate clinic (Phase 2) | Audit + clinic approve | Super Admin | v2 | — | 💡 |
| PLT-021 | Data export per clinic | Trigger export khi archive | Super Admin | v1 | TASK-030 | ⬜ |
| PLT-022 | Internal notes | Note nội bộ về clinic (private) | Super Admin | v1 | TASK-030 | ⬜ |
| PLT-023 | Activity feed platform-wide | Recent signups/converts/churns | Super Admin | v1 | TASK-030 | ⬜ |
| PLT-024 | Email super admin team | Notify all admins event quan trọng | System | v1 | TASK-027 | ⬜ |

---

## 21. JOB — Background Jobs (Arq)

| Code | Tên | Mô tả | Role | Phase | Task | Status |
|---|---|---|---|---|---|---|
| JOB-001 | Subscription expiration check | Cron mỗi giờ | System | v1 | TASK-028 | ⬜ |
| JOB-002 | Grace transition | active → grace khi quá hạn | System | v1 | TASK-028 | ⬜ |
| JOB-003 | Expired transition | grace → expired sau N ngày | System | v1 | TASK-028 | ⬜ |
| JOB-004 | Reminder dispatch | D-14/-7/-3/-1/0 + grace daily | System | v1 | TASK-028 | ⬜ |
| JOB-005 | Hard delete archived | Cron 90 ngày sau archive | System | v1 | TASK-028 | ⬜ |
| JOB-006 | Recurring shift generation | Generate shifts từ template | System | v1 | TASK-014 | ✅ |
| JOB-007 | Stock alert generation | Daily cron check min_stock | System | v1 | TASK-028 | ⬜ |
| JOB-008 | Expiry alert generation | Daily cron check 30/60/90 days | System | v1 | TASK-028 | ⬜ |
| JOB-009 | NO_SHOW marker | 30p sau giờ hẹn chưa check-in | System | v1 | TASK-028 | ⬜ |
| JOB-010 | Refresh permission cache | Trigger khi role/perm đổi | System | v1 | TASK-004 | ✅ |
| JOB-011 | Daily backup | DB dump → S3 | System | v1 | TASK-028 | ⬜ |
| JOB-012 | Weekly report email | Tự động gửi report cho admin | System | v2 | — | 💡 |
| JOB-013 | Patient birthday SMS | Chúc mừng sinh nhật | System | v3 | — | 💡 |
| JOB-014 | Audit log retention | Xoá audit log quá X ngày | System | v2 | — | 💡 |

---

## 22. DATA — Import/Export/Backup

| Code | Tên | Mô tả | Role | Phase | Task | Status |
|---|---|---|---|---|---|---|
| DATA-001 | Patient import CSV | Bulk import từ hệ thống cũ | Clinic Admin | v2 | — | 💡 |
| DATA-002 | Medicine catalog import CSV | Import hàng loạt thuốc | Clinic Admin | v2 | — | 💡 |
| DATA-003 | Service catalog import | Import dịch vụ | Clinic Admin | v2 | — | 💡 |
| DATA-004 | Patient export | Export full BN data | Admin | v1 | TASK-015 | ⬜ |
| DATA-005 | Visit export | Export lịch sử khám | Admin | v1 | TASK-015 | ⬜ |
| DATA-006 | Invoice export | Export hóa đơn theo dải ngày | Admin | v1 | TASK-013 | ⬜ |
| DATA-007 | Full clinic export | Tất cả data clinic (JSON+CSV zip) | Admin | v1 | TASK-015 | ⬜ |
| DATA-008 | Daily DB backup | Auto pg_dump → S3 | System | v1 | TASK-028 | ⬜ |
| DATA-009 | Point-in-time recovery | RDS PITR (Phase 2 khi up RDS) | System | v2 | — | 💡 |
| DATA-010 | Tauri offline SQLite mirror | Offline-first sync | System | v1 | TASK-016 | ✅ |
| DATA-011 | Sync conflict resolution | Last-write-wins hoặc manual | System | v1 | TASK-016 | ✅ |

---

## 23. INT — Integrations

| Code | Tên | Mô tả | Role | Phase | Task | Status |
|---|---|---|---|---|---|---|
| INT-001 | Email provider (SES/SendGrid) | Transactional email | System | v1 | TASK-027 | ⬜ |
| INT-002 | SMS provider (Stringee/Twilio VN) | OTP, reminder | System | v2 | TASK-027 | 💡 |
| INT-003 | VietQR generator | QR code thanh toán | System | v1 | TASK-013 | ⬜ |
| INT-004 | VNPay webhook (Phase 2) | Auto-renew subscription | System | v2 | — | 💡 |
| INT-005 | MoMo webhook (Phase 2) | Alternative payment | System | v2 | — | 💡 |
| INT-006 | E-invoice (VNPT/Viettel) | Hóa đơn điện tử | System | v2 | — | 💡 |
| INT-007 | reCAPTCHA | Chống bot signup | System | v1 | TASK-029 | ⬜ |
| INT-008 | Google Analytics (landing) | Track conversion | System | v1 | TASK-029 | ⬜ |
| INT-009 | Sentry error tracking | Error monitoring | System | v1 | TASK-029 | ⬜ |
| INT-010 | S3-compatible storage | Patient documents, exports | System | v1 | TASK-005 | ⬜ |
| INT-011 | Zalo OA Push | Phase 3 notification | System | v3 | — | 💡 |
| INT-012 | ICD-10 master data | Catalog VN-translated | System | v1 | TASK-007 | ✅ |
| INT-013 | VN address API | Tỉnh/quận/phường autocomplete | System | v1 | TASK-005 | ⬜ |
| INT-014 | Drug master data (Phase 2) | DrugBank-like cho VN | System | v2 | — | 💡 |
| INT-015 | Lab system integration | Phase 3 — kết quả XN auto | System | v3 | — | 💡 |
| INT-016 | Imaging system (PACS) | Phase 3 — XQuang/CT | System | v3 | — | 💡 |
| INT-017 | National Health Insurance API | BHYT verification | System | v3 | — | 💡 |
| INT-018 | POS printer driver | ESC/POS commands | System | v1 | TASK-013 | ⬜ |
| INT-019 | Barcode scanner (Tauri) | USB HID | System | v1 | TASK-016 | ✅ |
| INT-020 | Card reader (Tauri) | CMND/CCCD scan | System | v2 | — | 💡 |

---

## 24. I18N — Localization & A11y

| Code | Tên | Mô tả | Role | Phase | Task | Status |
|---|---|---|---|---|---|---|
| I18N-001 | Vietnamese (default) | UI vi | System | v1 | TASK-017 | ✅ |
| I18N-002 | English | UI en | System | v1 | TASK-017 | ✅ |
| I18N-003 | Date format VN/EN | DD/MM/YYYY vs MM/DD/YYYY | System | v1 | TASK-017 | ✅ |
| I18N-004 | Number format | 1.000.000 vs 1,000,000 | System | v1 | TASK-017 | ✅ |
| I18N-005 | Currency format | VND vs USD | System | v1 | TASK-017 | ✅ |
| I18N-006 | Time format | 24h VN vs 12h EN | System | v1 | TASK-017 | ✅ |
| I18N-007 | Language switcher | Per-user preference | All | v1 | TASK-017 | ✅ |
| A11Y-001 | ARIA labels | Mọi icon-only button | System | v1 | TASK-017 | ✅ |
| A11Y-002 | Keyboard navigation | Tab order + Esc + Enter | System | v1 | TASK-017 | ✅ |
| A11Y-003 | Focus rings | Visible ring-2 ring-brand | System | v1 | TASK-017 | ✅ |
| A11Y-004 | WCAG AA contrast | 4.5:1 cho text | System | v1 | TASK-017 | ✅ |
| A11Y-005 | Screen reader support | role="alert", role="status" | System | v1 | TASK-017 | ✅ |
| A11Y-006 | High contrast mode | Theme variant | System | v2 | — | 💡 |
| A11Y-007 | Font size adjuster | UI cho người cao tuổi | System | v2 | — | 💡 |
| THEME-001 | Light mode | Default | System | v1 | TASK-017 | ✅ |
| THEME-002 | Dark mode | Class-based toggle | System | v1 | TASK-017 | ✅ |
| THEME-003 | System theme detection | Auto theo OS | System | v1 | TASK-017 | ✅ |

---

## 25. NAV — Navigation & Quick Search

| Code | Tên | Mô tả | Role | Phase | Task | Status |
|---|---|---|---|---|---|---|
| NAV-001 | Global command palette (Ctrl+K / ⌘K) | Mở popup ở bất cứ màn nào, type-ahead search across: bệnh nhân (theo tên/mã/SĐT), thuốc (tên/hoạt chất/ATC), tính năng/màn (theo nhãn menu), hoá đơn (số INV-), đơn thuốc (RX-), lượt khám (LK-). Result group theo entity, mỗi item có icon + breadcrumb, click → navigate. Hỗ trợ ↑/↓/Enter để chọn không cần chuột. | All | v1 | TASK-017 | ⬜ |
| NAV-002 | Clinic switcher dropdown (topbar) | Avatar bên cạnh có dropdown 240px liệt kê tất cả phòng khám user có quyền + chỉ báo current (chip "Hiện tại"). Click row → trigger AUTH-021 switch flow. Search box trong dropdown nếu user có >5 clinic. Footer "→ Cấu hình clinic" và "Đăng xuất". | All | v1 | TASK-017 | ⬜ |
| NAV-003 | Quick search bệnh nhân | NAV-001 sub-mode "/bn " hoặc tab "Bệnh nhân" — tìm theo tên (fuzzy unaccent + trigram), mã BN, SĐT, CCCD, BHYT (nếu enabled). Hiện 5 result đầu với avatar + tuổi + giới + chip status visit gần nhất. | Receptionist+ | v1 | TASK-017 | ⬜ |
| NAV-004 | Quick search thuốc | NAV-001 sub-mode "/thuoc " — search theo tên thương mại, hoạt chất, mã ATC. Hiện stock badge + giá + chip "Trong DM BHYT" nếu enabled. Click → mở Medicine Detail hoặc add vào đơn nếu đang ở EMR Tab Kê đơn. | Doctor/Pharmacist | v1 | TASK-017 | ⬜ |
| NAV-005 | Quick search feature/màn | NAV-001 default mode (không prefix) — fuzzy search tên menu/route. VD gõ "ke don" → match "Khám bệnh → Kê đơn thuốc". Track recent + frequent để đẩy lên top. | All | v1 | TASK-017 | ⬜ |
| NAV-006 | Recent items pin | NAV-001 footer hiển thị 5 entity user mở gần nhất (BN, đơn, hoá đơn). Persisted per-user trong Tauri local storage. | All | v2 | — | 💡 |
| NAV-007 | Keyboard shortcuts cheatsheet | Press "?" hoặc Ctrl+/ → modal hiện full danh sách shortcuts (Ctrl+K search, Ctrl+N new, Ctrl+S save, Esc close, ...). Mỗi shortcut có scope (global / page-specific). | All | v1 | TASK-017 | ⬜ |
| NAV-008 | Breadcrumb navigation | Topbar luôn hiện breadcrumb "Trang chủ / Module / Resource". Click level cao → quay về. Resource có badge status (vd "Lê Hà Vy · Đang khám"). | All | v1 | TASK-017 | ✅ |

---

## 26. NFR — Non-functional requirements

> Phi chức năng — track như requirement có status để đo lường liên tục. Không dính role cụ thể (toàn hệ thống).

| Code | Tên | Mô tả / Ngưỡng | Phase | Task | Status |
|---|---|---|---|---|---|
| **NFR-001** | API response time | p50 <200ms · p95 <500ms · p99 <1s cho mọi endpoint trừ /reports/* (allow p95 <2s). Đo qua middleware structlog + Prometheus. | v1 | — | 🔄 |
| **NFR-002** | Page load time | First Contentful Paint <1.5s · Time to Interactive <2.5s trên mạng 4G + máy mid-range. Đo qua Lighthouse + Web Vitals. | v1 | TASK-017 | 🔄 |
| **NFR-003** | Concurrent users | ≥100 concurrent users / clinic mà không degrade response time >20%. Test load qua Locust trước v1 GA. | v1 | — | ⬜ |
| **NFR-004** | Uptime SLA | 99.5% uptime / tháng (≤3.6h downtime). Trừ scheduled maintenance window thông báo 7 ngày trước. | v1 | — | ⬜ |
| **NFR-005** | Encryption in-transit | TLS 1.3 bắt buộc, không cho TLS 1.2. HSTS preload. Cert auto-renew Let's Encrypt. | v1 | TASK-001 | ✅ |
| **NFR-006** | Encryption at-rest | Postgres TDE AES-256 cho data + WAL. Backup mã hoá AES-256 + key trong KMS. | v1 | TASK-002 | 🔄 |
| **NFR-007** | Multi-tenant isolation | Postgres RLS enforce ở session var `app.current_clinic_id`. Mọi query phải scoped bởi RLS — không có cross-tenant leak. Verify qua test e2e cho từng module mới. | v1 | TASK-002 | ✅ |
| **NFR-008** | OWASP Top 10 protection | Audit định kỳ: SQL injection (parameterized query) · XSS (React auto-escape + CSP) · CSRF (SameSite cookie + token) · auth/session (JWT + bcrypt) · misconfig (env review hằng quý). | v1 | — | 🔄 |
| **NFR-009** | Audit log immutable | Bảng audit_log append-only, không UPDATE/DELETE. Retention 7 năm (BYT compliance). Backup riêng + offsite. | v1 | TASK-002 | ✅ |
| **NFR-010** | Data retention BN | Lượt khám + bệnh án giữ 30 năm theo quy định BYT. Auto-archive sau 5 năm vào storage rẻ hơn. | v2 | — | ⬜ |
| **NFR-011** | Backup & DR | Daily incremental + weekly full backup. RTO 4h · RPO 24h. Test restore hằng quý. | v1 | — | ⬜ |
| **NFR-012** | Accessibility WCAG 2.1 AA | Mọi màn pass aXe-core scan (0 violations). Contrast ≥4.5:1 text · ≥3:1 graphics. Keyboard navigation 100% (không cần chuột). Screen reader (NVDA/JAWS) support. | v1 | TASK-017 | ✅ |
| **NFR-013** | Browser support | Chrome / Edge / Firefox last 2 versions. Safari 15+. Tauri shell ưu tiên (desktop). KHÔNG support IE11. | v1 | TASK-017 | ✅ |
| **NFR-014** | OS support (Tauri) | Windows 10+ (build 1903+) · macOS 11+ · Ubuntu 20.04+. Bundle size <80MB per platform. | v1 | TASK-016 | ✅ |
| **NFR-015** | Responsive (web fallback) | Vite web fallback cho admin lite trên tablet 1024×768+. Mobile responsive cho landing + sub-flow đăng ký BN. Phase 2 mới làm full mobile EMR. | v2 | — | ⬜ |
| **NFR-016** | Localization | Vi (mặc định) · En (đầy đủ). Tất cả string qua i18next, không hardcode. Date/number/currency theo locale. | v1 | TASK-017 | ✅ |
| **NFR-017** | Code coverage | New code ≥80% · Overall ≥70%. Enforce ở CI gate. Integration test phải hit DB thật + Redis (không mock). | v1 | — | 🔄 |
| **NFR-018** | Observability | Structured log JSON (structlog) · Metrics Prometheus · Trace OpenTelemetry. Mọi request có request_id + user_id + clinic_id. | v1 | TASK-001 | 🔄 |
| **NFR-019** | Search performance | Patient search 100k records p95 <100ms (trigram + unaccent + indexed). Medicine search 10k records p95 <50ms. Global search (NAV-001) <300ms. | v1 | TASK-005 | ✅ |
| **NFR-020** | Offline capability (Tauri) | Tauri SQLite mirror cho dữ liệu BN gần nhất + lượt khám đang dở. Sync khi online lại (eventual consistency, conflict resolution last-write-wins). | v1 | TASK-016 | 🔄 |
| **NFR-021** | Compliance HIPAA + Nghị định 13/2023 | Checklist 14 mục (xem `medizen-modern/TAB_MATRIX.md` Section "Bảo mật → Compliance"). Quarterly review. | v1 | — | 🔄 |
| **NFR-022** | Rate limiting | Login 10/min/IP. Sensitive write 60/min/user. Reports query 30/min/user. SlowAPI middleware. | v1 | TASK-003 | ✅ |

---

## 27. Tổng kết theo phase

### Phase 1 (MVP — Q2-Q3 2026)

**Tổng: ~270 functions**

| Group | Total | DONE | TODO |
|---|---|---|---|
| AUTH | 17 | 8 | 9 |
| RBAC | 15 | 9 | 6 |
| TENANT | 14 | 0 | 14 |
| SUB | 21 | 0 | 21 |
| PATIENT | 22 | 17 | 5 |
| VISIT | 14 | 13 | 1 |
| VITAL | 10 | 0 | 10 |
| DIAG | 7 | 7 | 0 |
| SVC | 8 | 0 | 8 |
| RX | 12 | 0 | 12 |
| MED | 16 | 0 | 16 |
| PHRM | 11 | 1 | 10 |
| APPT | 14 | 0 | 14 |
| BILL | 19 | 0 | 19 |
| HR | 16 | 13 | 3 |
| RPT | 15 | 0 | 15 |
| NOTI | 10 | 1 | 9 |
| AUDIT | 11 | 7 | 4 |
| CFG | 14 | 3 | 11 |
| PLT | 22 | 0 | 22 |
| JOB | 11 | 2 | 9 |
| DATA | 7 | 2 | 5 |
| INT | 11 | 4 | 7 |
| I18N+A11Y+THEME | 17 | 14 | 3 |
| NAV | 7 | 1 | 6 |
| NFR | 20 | 9 | 11 |
| **TỔNG v1** | **361** | **111** | **250** |

→ Tiến độ MVP: **~31% DONE** (111/361)

### Phase 2 (Q4 2026 - Q1 2027)

~50 functions: drug interaction, e-invoice, payment auto-renew, SMS, magic link invite, custom role, tiers, advanced analytics...

### Phase 3 (2027+)

~30 functions: lab integration, PACS, BHYT API, multi-clinic per user, patient portal, voice input, AI clinical decision support...

---

## 28. Cách sử dụng tài liệu này

### Cho Project Manager
- Track tiến độ MVP — count DONE/TODO mỗi tuần
- Identify blocker — function nào chưa làm chặn function nào khác
- Plan sprint — pick 10-15 functions per sprint

### Cho Developer
- Mỗi feature implement → tick status
- Code references function code (`// FN: BILL-005 multi-payment method`)
- Test naming: `test_bill_005_multi_payment_method`

### Cho QA / Tester
- Mỗi function = ít nhất 1 test case
- Trace requirement → test case → bug

### Cho UI/UX Designer (AI)
- Mỗi function = ít nhất 1 UI affordance (button/menu/screen)
- Cross-reference với `clinic_management_ux_specification.md` cho screen layout

### Cho Marketing
- Phân loại Phase để planning launch
- Feature comparison sheet sales/landing page

---

**Ngày**: 2026-04-30 (v1.2 — multi-clinic per account · global search · multi-role UX · NFR tracking)
**Phiên bản**: 1.2
**Tổng**: 361 v1 + 53 v2 + 30 v3 = ~444 functions
**Đồng bộ với**: `clinic_management_business_analysis.md`, `clinic_management_saas_platform_model.md`, `clinic_management_ux_specification.md`, `claude-workspace/docs/design/medizen-modern/`
