# Test Case Catalog — DATA · Nhập/Xuất/Backup Dữ liệu

**Nguồn:** function_list_data.py (group DATA, 11 function) + clinic_management_function_list.md §22 + system_design/saas_platform_model.
**Phạm vi:** 11 functions (DATA-001 … DATA-011).  **Tổng test case:** 42.  **Ngày:** 2026-05-30.

> **Ghi chú nguồn & coverage.** 11 function lấy trực tiếp từ `scripts/function_list_data.py` (block `# 22. DATA`). Trong workspace hiện tại KHÔNG mount được repo code `clinic-cms-merge/` (đường dẫn không tồn tại) và `clinic-cms/tests` cũng không truy cập được, nên không thể đối chiếu test thực tế file-by-file. Coverage do đó gán theo **cột Status nguồn**:
> - DATA-010, DATA-011 = ✅ DONE (TASK-016 — offline sync) → ưu tiên xem lại test thực tế của TASK-016 để xác nhận (tạm gán **PARTIAL** vì là chức năng Tauri/sync engine, phần lớn test ở FE/Rust chứ chưa chắc có pytest BE đầy đủ).
> - DATA-004..DATA-008 = ⬜ TODO (v1, gắn TASK-013/015/028) → **MISSING**.
> - DATA-001, DATA-002, DATA-003, DATA-009 = 💡 IDEA (v2/Phase 2) → **MISSING** (chưa triển khai, test chỉ là spec cho tương lai).
>
> Kiến trúc bám: FastAPI `/api/v1`, PostgreSQL RLS theo `clinic_id`, Redis + Arq cho job nền, JWT + RBAC, `audit_log`, Tauri offline SQLite mirror + sync engine (LWW). Endpoint export tham chiếu spec trong nguồn: `/reports/visits/export`, `/reports/invoices/export`, `/clinic/export`.

---

## 1. Ma trận truy vết (Function → Test Cases → Coverage)

| Function | Tên chức năng | Status (nguồn) | Test Case IDs | Coverage |
|---|---|---|---|---|
| DATA-001 | Patient import CSV (bulk, Phase 2 = PAT-022) | 💡 IDEA (v2) | TC-DATA-001, TC-DATA-002, TC-DATA-003 | MISSING |
| DATA-002 | Medicine catalog import CSV (Phase 2 = MED-018) | 💡 IDEA (v2) | TC-DATA-004, TC-DATA-005 | MISSING |
| DATA-003 | Service catalog import (Phase 2) | 💡 IDEA (v2) | TC-DATA-006, TC-DATA-007 | MISSING |
| DATA-004 | Patient export (full BN data, AUDIT-010 PDPA) | ⬜ TODO (v1, TASK-015) | TC-DATA-008, TC-DATA-009, TC-DATA-010, TC-DATA-011, TC-DATA-012 | MISSING |
| DATA-005 | Visit export (/reports/visits/export CSV, date range) | ⬜ TODO (v1, TASK-015) | TC-DATA-013, TC-DATA-014, TC-DATA-015, TC-DATA-016 | MISSING |
| DATA-006 | Invoice export (/reports/invoices/export, kế toán) | ⬜ TODO (v1, TASK-013) | TC-DATA-017, TC-DATA-018, TC-DATA-019, TC-DATA-020 | MISSING |
| DATA-007 | Full clinic export (/clinic/export zip JSON+CSV) | ⬜ TODO (v1, TASK-015) | TC-DATA-021, TC-DATA-022, TC-DATA-023, TC-DATA-024, TC-DATA-025 | MISSING |
| DATA-008 | Daily DB backup (auto pg_dump → S3, JOB-011) | ⬜ TODO (v1, TASK-028) | TC-DATA-026, TC-DATA-027, TC-DATA-028, TC-DATA-029 | MISSING |
| DATA-009 | Point-in-time recovery (RDS PITR) | 💡 IDEA (v2) | TC-DATA-030, TC-DATA-031 | MISSING |
| DATA-010 | Tauri offline SQLite mirror (offline-first sync) | ✅ DONE (v1, TASK-016) | TC-DATA-032, TC-DATA-033, TC-DATA-034, TC-DATA-035, TC-DATA-036 | PARTIAL |
| DATA-011 | Sync conflict resolution (LWW / manual) | ✅ DONE (v1, TASK-016) | TC-DATA-037, TC-DATA-038, TC-DATA-039, TC-DATA-040, TC-DATA-041, TC-DATA-042 | PARTIAL |

**Tổng:** 11 functions · 42 test cases. Coverage: COVERED 0 · PARTIAL 2 · MISSING 9.

---

## 2. Chi tiết Test Cases

### DATA-001 — Patient import CSV (bulk import từ hệ thống cũ)

#### TC-DATA-001 — Import danh sách bệnh nhân từ CSV hợp lệ (Phase 2)
- **Function:** DATA-001
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** User role Clinic Admin, có permission `patient:create` / `data:import`, clinic A.
- **Bước thực hiện:** 1) POST `/api/v1/patients/import` (multipart) với CSV `code,full_name,dob,gender,phone`. 2) BE validate + insert kèm `clinic_id=A` trong transaction, auto-gen patient_code nếu thiếu (PAT-002). 3) Đọc báo cáo.
- **Dữ liệu test:** CSV 50 dòng hợp lệ.
- **Kết quả mong đợi:** HTTP 200/201 `{inserted:50, failed:0}`; `patient` clinic A tăng 50; audit `data.import.patient`.
- **Coverage hiện tại:** MISSING (Phase 2 — 💡 IDEA, chưa ship).

#### TC-DATA-002 — Báo cáo dòng lỗi (dob sai, thiếu họ tên) không chặn dòng hợp lệ
- **Function:** DATA-001
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Như TC-DATA-001.
- **Bước thực hiện:** 1) Import CSV 10 dòng, 4 dòng lỗi (2 thiếu full_name, 2 dob sai). 2) BE partial-import + trả error theo số dòng.
- **Dữ liệu test:** CSV 10 dòng (4 lỗi).
- **Kết quả mong đợi:** HTTP 200 `{inserted:6, failed:4, errors:[{row, field, message}]}`.
- **Coverage hiện tại:** MISSING

#### TC-DATA-003 — Import thiếu quyền / chưa auth
- **Function:** DATA-001
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** (a) không JWT; (b) JWT role Receptionist thiếu `data:import`.
- **Bước thực hiện:** 1) POST import không JWT → 401. 2) POST import JWT thiếu quyền → 403.
- **Dữ liệu test:** CSV bất kỳ.
- **Kết quả mong đợi:** Lần lượt HTTP 401 và 403; không ghi DB.
- **Coverage hiện tại:** MISSING

---

### DATA-002 — Medicine catalog import CSV (import hàng loạt thuốc)

#### TC-DATA-004 — Import danh mục thuốc từ CSV (Phase 2 = MED-018)
- **Function:** DATA-002
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Clinic Admin clinic A, quyền `medicine:create`/`data:import`.
- **Bước thực hiện:** 1) POST `/api/v1/medicines/import` CSV `name,active_ingredient,strength,form,unit`. 2) BE insert vào `medicine` kèm clinic_id, dedupe theo (clinic_id, name+strength).
- **Dữ liệu test:** CSV 30 thuốc.
- **Kết quả mong đợi:** HTTP 200 `{inserted:30, skipped:0}`; cô lập clinic A.
- **Coverage hiện tại:** MISSING (Phase 2 — 💡).

#### TC-DATA-005 — Dedupe thuốc trùng + cô lập clinic (RLS)
- **Function:** DATA-002
- **Loại:** Edge / Security
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Clinic A đã có "Paracetamol 500mg"; clinic B cũng có thuốc cùng tên.
- **Bước thực hiện:** 1) User A import CSV chứa "Paracetamol 500mg" + 5 thuốc mới. 2) Kiểm tra dedupe chỉ trong phạm vi clinic A, không đụng catalog clinic B.
- **Dữ liệu test:** CSV 6 dòng, 1 trùng.
- **Kết quả mong đợi:** HTTP 200 `{inserted:5, skipped:1}`; catalog clinic B không đổi.
- **Coverage hiện tại:** MISSING

---

### DATA-003 — Service catalog import (import dịch vụ)

#### TC-DATA-006 — Import danh mục dịch vụ từ CSV
- **Function:** DATA-003
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Clinic Admin, quyền `service:create`/`data:import`.
- **Bước thực hiện:** 1) POST `/api/v1/services/import` CSV `name,category,price_direct,price_bhyt,duration`. 2) BE insert vào `service` kèm clinic_id.
- **Dữ liệu test:** CSV 20 dịch vụ với 2 mức giá (SVC-003).
- **Kết quả mong đợi:** HTTP 200 `{inserted:20}`; multi-price map đúng.
- **Coverage hiện tại:** MISSING (Phase 2 — 💡).

#### TC-DATA-007 — Giá âm / category không hợp lệ bị từ chối
- **Function:** DATA-003
- **Loại:** Negative
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Như TC-DATA-006.
- **Bước thực hiện:** 1) Import CSV có dòng `price_direct=-100` và category ngoài enum (Khám/XN/Thủ thuật/Siêu âm/X-quang).
- **Dữ liệu test:** CSV 5 dòng, 2 lỗi.
- **Kết quả mong đợi:** HTTP 200 `{inserted:3, failed:2, errors:[...]}` (hoặc 422 nếu fail-fast); không insert dòng giá âm.
- **Coverage hiện tại:** MISSING

---

### DATA-004 — Patient export (export full BN data — PDPA / AUDIT-010)

#### TC-DATA-008 — Export toàn bộ bệnh nhân clinic ra CSV
- **Function:** DATA-004
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** User Admin clinic A, quyền `data:export`/`audit:export`; clinic A có 120 BN.
- **Bước thực hiện:** 1) GET `/api/v1/patients/export?format=csv` (hoặc `/clinic/export?entity=patients`). 2) BE stream CSV chỉ chứa BN clinic A.
- **Dữ liệu test:** 120 BN clinic A.
- **Kết quả mong đợi:** HTTP 200 `text/csv`, 120 dòng + header; ghi `audit_log` action=`patient.export` (AUDIT-010 — quyền data portability).
- **Coverage hiện tại:** MISSING

#### TC-DATA-009 — Export cô lập theo clinic (RLS) — không lẫn BN clinic khác
- **Function:** DATA-004
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Clinic A và clinic B mỗi clinic 50 BN; user thuộc A.
- **Bước thực hiện:** 1) User A export patients. 2) Kiểm tra mọi dòng `clinic_id=A`.
- **Dữ liệu test:** 2 clinic × 50 BN.
- **Kết quả mong đợi:** HTTP 200; tuyệt đối 0 bản ghi clinic B trong file.
- **Coverage hiện tại:** MISSING

#### TC-DATA-010 — Export ghi audit đọc PHI (mass PII reveal)
- **Function:** DATA-004
- **Loại:** Security / Edge
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Admin clinic A; anomaly rule `mass_pii_reveal`/`mass_export` (NFR-042) đang bật.
- **Bước thực hiện:** 1) Export full BN. 2) Kiểm tra audit_log ghi 1 sự kiện export tổng (không spam per-row) và trigger anomaly detection được tính.
- **Dữ liệu test:** 120 BN.
- **Kết quả mong đợi:** Audit có entry `data.export` với count; rule mass_export ghi nhận để PD/Slack alert.
- **Coverage hiện tại:** MISSING

#### TC-DATA-011 — Chưa auth không export được
- **Function:** DATA-004
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Không gửi JWT.
- **Bước thực hiện:** 1) GET export không Authorization.
- **Dữ liệu test:** —
- **Kết quả mong đợi:** HTTP 401.
- **Coverage hiện tại:** MISSING

#### TC-DATA-012 — Role không có `data:export` → 403
- **Function:** DATA-004
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** JWT role Receptionist (không có `data:export`).
- **Bước thực hiện:** 1) GET export với JWT thiếu quyền.
- **Dữ liệu test:** —
- **Kết quả mong đợi:** HTTP 403 problem+json `forbidden`; không trả file.
- **Coverage hiện tại:** MISSING

---

### DATA-005 — Visit export (/reports/visits/export — CSV theo date range)

#### TC-DATA-013 — Export lịch sử khám theo khoảng ngày
- **Function:** DATA-005
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Admin clinic A, quyền `data:export`; có visit nhiều tháng.
- **Bước thực hiện:** 1) GET `/api/v1/reports/visits/export?from=2026-01-01&to=2026-01-31&format=csv`. 2) BE filter date range + clinic_id.
- **Dữ liệu test:** Visits tháng 1/2026 = 80, ngoài range = 200.
- **Kết quả mong đợi:** HTTP 200 CSV chỉ 80 visit trong range; cột visit_number, BN, doctor, status, ngày.
- **Coverage hiện tại:** MISSING

#### TC-DATA-014 — Range rỗng / from > to
- **Function:** DATA-005
- **Loại:** Edge / Negative
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Admin clinic A.
- **Bước thực hiện:** 1) GET với `from=2026-03-01&to=2026-02-01` (đảo ngược). 2) GET range không có visit.
- **Dữ liệu test:** Range đảo ngược + range trống.
- **Kết quả mong đợi:** Đảo ngược → HTTP 422 `invalid-date-range`; range trống → 200 CSV chỉ header (0 dòng).
- **Coverage hiện tại:** MISSING

#### TC-DATA-015 — RLS cô lập clinic khi export visit
- **Function:** DATA-005
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Clinic A và B đều có visit cùng khoảng ngày.
- **Bước thực hiện:** 1) User A export visits. 2) Kiểm tra không có visit clinic B.
- **Dữ liệu test:** 2 clinic.
- **Kết quả mong đợi:** HTTP 200; 0 dòng của clinic B.
- **Coverage hiện tại:** MISSING

#### TC-DATA-016 — Chưa auth / thiếu quyền export visit
- **Function:** DATA-005
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** (a) không JWT; (b) thiếu `data:export`.
- **Bước thực hiện:** 1) GET không JWT → 401. 2) GET thiếu quyền → 403.
- **Dữ liệu test:** —
- **Kết quả mong đợi:** HTTP 401 rồi 403.
- **Coverage hiện tại:** MISSING

---

### DATA-006 — Invoice export (/reports/invoices/export — kế toán)

#### TC-DATA-017 — Export hóa đơn theo dải ngày ra CSV/Excel
- **Function:** DATA-006
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Admin clinic A, quyền `billing:export`/`data:export`.
- **Bước thực hiện:** 1) GET `/api/v1/reports/invoices/export?from=...&to=...&format=xlsx`. 2) BE trả cột invoice_number, BN, total, payment_method, status.
- **Dữ liệu test:** 60 hóa đơn trong range.
- **Kết quả mong đợi:** HTTP 200; xlsx hợp lệ đủ cột kế toán; số tiền khớp DB.
- **Coverage hiện tại:** MISSING

#### TC-DATA-018 — Tổng tiền export khớp tổng DB (đối soát số tiền)
- **Function:** DATA-006
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Có hóa đơn nhiều trạng thái (ISSUED/PAID/VOID).
- **Bước thực hiện:** 1) Export range. 2) Cộng cột total trong file. 3) So với SUM(total) query DB cùng filter.
- **Dữ liệu test:** Hóa đơn gồm cả VOID.
- **Kết quả mong đợi:** Tổng file == tổng DB; VOID đánh dấu rõ status, không sai lệch tiền.
- **Coverage hiện tại:** MISSING

#### TC-DATA-019 — RLS cô lập clinic khi export hóa đơn
- **Function:** DATA-006
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Clinic A và B cùng có hóa đơn.
- **Bước thực hiện:** 1) User A export invoices. 2) Kiểm tra 0 hóa đơn clinic B.
- **Dữ liệu test:** 2 clinic.
- **Kết quả mong đợi:** HTTP 200; không lẫn hóa đơn clinic B.
- **Coverage hiện tại:** MISSING

#### TC-DATA-020 — Chưa auth / thiếu quyền export hóa đơn
- **Function:** DATA-006
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** (a) không JWT; (b) role thiếu `billing:export`.
- **Bước thực hiện:** 1) GET không JWT → 401. 2) GET thiếu quyền → 403.
- **Dữ liệu test:** —
- **Kết quả mong đợi:** HTTP 401 rồi 403.
- **Coverage hiện tại:** MISSING

---

### DATA-007 — Full clinic export (/clinic/export — zip JSON+CSV)

#### TC-DATA-021 — Export toàn bộ data clinic dạng zip
- **Function:** DATA-007
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Admin clinic A, quyền `data:export`/`clinic:export`.
- **Bước thực hiện:** 1) POST `/api/v1/clinic/export`. 2) BE tạo zip: profile, patients (CSV), visits, prescriptions, invoices, documents (binary). 3) Trả file/job_id.
- **Dữ liệu test:** Clinic A có đủ data các entity.
- **Kết quả mong đợi:** HTTP 200/202; zip chứa đủ folders đúng cấu trúc; audit `clinic.export`.
- **Coverage hiện tại:** MISSING

#### TC-DATA-022 — Full export khả dụng khi clinic ở trạng thái `expired` (PDPA portability)
- **Function:** DATA-007
- **Loại:** Edge
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Clinic A `status=expired` (chỉ GET, chặn ghi — saas_platform §8.3 exception cho `/clinic/export`).
- **Bước thực hiện:** 1) Admin clinic expired gọi `/clinic/export`. 2) Kiểm tra không bị SubscriptionGuard chặn (402).
- **Dữ liệu test:** Clinic expired.
- **Kết quả mong đợi:** HTTP 200/202 — export VẪN cho phép (data portability), trong khi POST nghiệp vụ khác bị 402.
- **Coverage hiện tại:** MISSING

#### TC-DATA-023 — RLS: zip chỉ chứa data của clinic gọi
- **Function:** DATA-007
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Clinic A và B cùng tồn tại data.
- **Bước thực hiện:** 1) User A full-export. 2) Giải nén kiểm tra mọi record `clinic_id=A`.
- **Dữ liệu test:** 2 clinic.
- **Kết quả mong đợi:** 0 record clinic B trong bất kỳ file nào của zip.
- **Coverage hiện tại:** MISSING

#### TC-DATA-024 — Super Admin KHÔNG thể đọc PHI qua full export
- **Function:** DATA-007
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Platform JWT (aud=platform). saas_platform §5.2 cấm tuyệt đối super admin đọc PHI.
- **Bước thực hiện:** 1) Platform user gọi `/api/v1/clinic/export` (clinic-scope endpoint).
- **Dữ liệu test:** Platform JWT.
- **Kết quả mong đợi:** HTTP 401 (audience mismatch) / 403; super admin không lấy được PHI clinic.
- **Coverage hiện tại:** MISSING

#### TC-DATA-025 — Chưa auth / thiếu quyền full export
- **Function:** DATA-007
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** (a) không JWT; (b) role non-admin thiếu `data:export`.
- **Bước thực hiện:** 1) POST không JWT → 401. 2) POST thiếu quyền → 403.
- **Dữ liệu test:** —
- **Kết quả mong đợi:** HTTP 401 rồi 403.
- **Coverage hiện tại:** MISSING

---

### DATA-008 — Daily DB backup (auto pg_dump → S3 — JOB-011)

#### TC-DATA-026 — Cron job tạo backup pg_dump và upload S3
- **Function:** DATA-008
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Arq scheduler cấu hình job daily backup (JOB-011); S3 (hoặc mock S3/minio) khả dụng.
- **Bước thực hiện:** 1) Trigger task `daily_db_backup`. 2) Job chạy pg_dump → upload object lên bucket với key theo ngày.
- **Dữ liệu test:** DB có data.
- **Kết quả mong đợi:** Job SUCCEEDED; object tồn tại trên S3 key `backups/YYYY-MM-DD.sql.gz`; ghi log/audit `system.backup`.
- **Coverage hiện tại:** MISSING

#### TC-DATA-027 — Backup là dump toàn DB (không lọc RLS — system scope)
- **Function:** DATA-008
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Job chạy bằng role có BYPASSRLS (system), không context clinic.
- **Bước thực hiện:** 1) Chạy backup. 2) Kiểm tra dump chứa data của TẤT CẢ clinic (đây là backup hạ tầng, khác export per-clinic).
- **Dữ liệu test:** 2+ clinic.
- **Kết quả mong đợi:** Dump đầy đủ mọi clinic; phân biệt rõ với DATA-004/007 (per-clinic, có RLS).
- **Coverage hiện tại:** MISSING

#### TC-DATA-028 — Job thất bại khi S3 không reachable → retry + alert
- **Function:** DATA-008
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** S3 endpoint lỗi (mô phỏng down).
- **Bước thực hiện:** 1) Trigger backup khi S3 down. 2) Quan sát Arq retry policy + alert.
- **Dữ liệu test:** S3 unreachable.
- **Kết quả mong đợi:** Job FAILED sau retry; ghi alert (NOTI/Slack); không để dump lỗi treo trên đĩa.
- **Coverage hiện tại:** MISSING

#### TC-DATA-029 — Endpoint trigger backup chỉ cho System/Super Admin
- **Function:** DATA-008
- **Loại:** Security
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Nếu có endpoint thủ công trigger backup (`/api/v1/platform/backup/run`).
- **Bước thực hiện:** 1) Clinic user gọi → expect chặn. 2) Platform admin có `platform.system.config` gọi → cho phép.
- **Dữ liệu test:** Clinic JWT vs Platform JWT.
- **Kết quả mong đợi:** Clinic JWT → 401/403; platform admin → 202.
- **Coverage hiện tại:** MISSING

---

### DATA-009 — Point-in-time recovery (RDS PITR — Phase 2)

#### TC-DATA-030 — Restore DB tới timestamp trong window (Phase 2)
- **Function:** DATA-009
- **Loại:** Happy path
- **Ưu tiên:** P2
- **Layer:** Manual/UI (runbook) + Integration
- **Tiền điều kiện:** RDS managed có automated backup + PITR 7-30 ngày (chỉ khi lên RDS).
- **Bước thực hiện:** 1) Chọn timestamp T trong window. 2) Trigger restore tới instance mới. 3) Verify data đúng tại T.
- **Dữ liệu test:** Snapshot có thay đổi đã biết trước/sau T.
- **Kết quả mong đợi:** Instance restore khớp trạng thái DB tại T; không mất data trong window.
- **Coverage hiện tại:** MISSING (Phase 2 — 💡, phụ thuộc hạ tầng RDS).

#### TC-DATA-031 — Restore ngoài window bị từ chối
- **Function:** DATA-009
- **Loại:** Negative
- **Ưu tiên:** P2
- **Layer:** Manual/UI (runbook)
- **Tiền điều kiện:** PITR window 7 ngày.
- **Bước thực hiện:** 1) Yêu cầu restore tới timestamp 30 ngày trước.
- **Dữ liệu test:** Timestamp ngoài retention.
- **Kết quả mong đợi:** Bị từ chối với thông báo "out of retention window".
- **Coverage hiện tại:** MISSING

---

### DATA-010 — Tauri offline SQLite mirror (offline-first sync — TASK-016, DONE)

#### TC-DATA-032 — App vận hành đọc dữ liệu khi offline từ SQLite mirror
- **Function:** DATA-010
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Manual/UI (vitest) + Tauri
- **Tiền điều kiện:** Tauri app đã sync data clinic A; ngắt mạng.
- **Bước thực hiện:** 1) Sync online lần đầu (mirror đầy đủ). 2) Ngắt mạng. 3) Mở danh sách BN / hàng đợi.
- **Dữ liệu test:** Mirror gồm patients, visits, queue.
- **Kết quả mong đợi:** UI render từ SQLite local, không lỗi mạng; có chỉ báo "offline".
- **Coverage hiện tại:** PARTIAL (TASK-016 DONE; cần xác nhận test thực tế ở repo TASK-016 — không truy cập được trong workspace).

#### TC-DATA-033 — Ghi offline được queue và đẩy lên khi online
- **Function:** DATA-010
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Manual/UI (vitest) + Tauri
- **Tiền điều kiện:** Offline; mirror sẵn.
- **Bước thực hiện:** 1) Offline tạo visit mới. 2) Lưu vào local SQLite + outbox. 3) Bật mạng → sync engine push.
- **Dữ liệu test:** 1 visit tạo offline.
- **Kết quả mong đợi:** Visit lưu local; khi online được đồng bộ lên BE, server nhận đúng `clinic_id`.
- **Coverage hiện tại:** PARTIAL

#### TC-DATA-034 — Mirror chỉ chứa data clinic hiện tại (cô lập, không leak clinic khác)
- **Function:** DATA-010
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Manual/UI (vitest) + Tauri
- **Tiền điều kiện:** User từng đăng nhập 2 clinic (switch).
- **Bước thực hiện:** 1) Sync clinic A. 2) Switch sang clinic B (AUTH-021 clear cache). 3) Kiểm tra mirror không lẫn data A khi đang ở B.
- **Dữ liệu test:** Data 2 clinic.
- **Kết quả mong đợi:** Sau switch, mirror/cache không lộ data clinic cũ (tránh cross-clinic leak).
- **Coverage hiện tại:** PARTIAL

#### TC-DATA-035 — Mất kết nối giữa chừng khi đang sync → không hỏng mirror
- **Function:** DATA-010
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Manual/UI (vitest) + Tauri
- **Tiền điều kiện:** Đang sync batch lớn.
- **Bước thực hiện:** 1) Sync, ngắt mạng giữa chừng. 2) Bật lại mạng. 3) Sync resume.
- **Dữ liệu test:** Batch sync gián đoạn.
- **Kết quả mong đợi:** Mirror không corrupt; sync resume idempotent, không nhân đôi record.
- **Coverage hiện tại:** PARTIAL

#### TC-DATA-036 — Sync chỉ chạy khi có JWT hợp lệ (token hết hạn → re-auth)
- **Function:** DATA-010
- **Loại:** Security
- **Ưu tiên:** P1
- **Layer:** Manual/UI (vitest) + Tauri
- **Tiền điều kiện:** JWT access hết hạn.
- **Bước thực hiện:** 1) Online sync với token hết hạn. 2) Sync engine refresh (AUTH-002) hoặc buộc re-login.
- **Dữ liệu test:** Token expired.
- **Kết quả mong đợi:** Sync không gửi data với token invalid; refresh thành công thì tiếp tục, fail thì dừng + báo đăng nhập lại.
- **Coverage hiện tại:** PARTIAL

---

### DATA-011 — Sync conflict resolution (LWW / manual — TASK-016, DONE)

#### TC-DATA-037 — Conflict cùng row sửa 2 nơi → last-write-wins
- **Function:** DATA-011
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration + Manual/UI
- **Tiền điều kiện:** Cùng 1 record (vd patient note) sửa ở offline-device và ở server.
- **Bước thực hiện:** 1) Offline sửa note = X (lúc t1). 2) Server sửa note = Y (lúc t2 > t1). 3) Online sync.
- **Dữ liệu test:** 2 phiên bản cùng row, timestamp khác.
- **Kết quả mong đợi:** LWW: bản có timestamp mới hơn (Y) thắng; bản cũ ghi nhận trong conflict log.
- **Coverage hiện tại:** PARTIAL

#### TC-DATA-038 — Conflict trên entity quan trọng (visit/invoice) → manual resolution
- **Function:** DATA-011
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Manual/UI (vitest)
- **Tiền điều kiện:** Conflict trên invoice (entity quan trọng — nguồn chỉ định manual UI).
- **Bước thực hiện:** 1) Tạo conflict trên invoice. 2) Sync phát hiện. 3) UI hiện màn chọn bản giữ.
- **Dữ liệu test:** 2 phiên bản invoice.
- **Kết quả mong đợi:** KHÔNG auto-LWW cho invoice/visit; hiện UI cho người dùng chọn; lựa chọn được ghi audit.
- **Coverage hiện tại:** PARTIAL

#### TC-DATA-039 — Timestamp bằng nhau (tie-break)
- **Function:** DATA-011
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Integration
- **Tiền điều kiện:** 2 bản ghi cùng updated_at chính xác.
- **Bước thực hiện:** 1) Tạo conflict cùng timestamp. 2) Sync.
- **Dữ liệu test:** updated_at bằng nhau.
- **Kết quả mong đợi:** Có quy tắc tie-break xác định (vd server-wins hoặc theo device_id) — không random, không mất data.
- **Coverage hiện tại:** PARTIAL

#### TC-DATA-040 — Conflict KHÔNG vượt biên giới clinic (RLS)
- **Function:** DATA-011
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration
- **Tiền điều kiện:** Sync engine xử lý nhiều clinic.
- **Bước thực hiện:** 1) Gửi bản ghi offline có clinic_id A trong khi context server là B. 2) Sync.
- **Dữ liệu test:** Payload chéo clinic.
- **Kết quả mong đợi:** Server từ chối/RLS chặn ghi chéo clinic; conflict resolution chỉ trong cùng clinic.
- **Coverage hiện tại:** PARTIAL

#### TC-DATA-041 — Resolution ghi audit + giữ bản thua để truy vết
- **Function:** DATA-011
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Integration
- **Tiền điều kiện:** Conflict đã resolve (LWW hoặc manual).
- **Bước thực hiện:** 1) Resolve conflict. 2) Kiểm tra audit_log + conflict history.
- **Dữ liệu test:** 1 conflict.
- **Kết quả mong đợi:** Audit ghi action `sync.conflict_resolved` với bản thắng/thua; bản thua không bị xoá vĩnh viễn (có thể khôi phục).
- **Coverage hiện tại:** PARTIAL

#### TC-DATA-042 — Sync idempotent — gửi lại cùng payload không nhân đôi
- **Function:** DATA-011
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Integration
- **Tiền điều kiện:** Mạng chập chờn khiến client gửi lại batch.
- **Bước thực hiện:** 1) Sync batch. 2) Gửi lại y nguyên (duplicate). 3) Kiểm tra DB.
- **Dữ liệu test:** Batch gửi 2 lần.
- **Kết quả mong đợi:** Không tạo bản ghi trùng; sync dùng client-id/version để dedupe idempotent.
- **Coverage hiện tại:** PARTIAL

---

## 3. Khuyến nghị độ ưu tiên triển khai test

1. **P0 trước (v1 đang/đã ship):** DATA-004 (TC-008/009/011/012), DATA-005 (TC-013/015/016), DATA-006 (TC-017/019/020), DATA-007 (TC-021/022/023/024), DATA-008 (TC-026), DATA-010 (TC-032/033/034), DATA-011 (TC-037/038/040). Đây là nhóm rủi ro cao nhất: **rò rỉ dữ liệu chéo clinic qua export** và **mất/nhân đôi data qua sync**.
2. **RLS là rủi ro số 1** của cả group: mọi TC export (004/005/006/007) và sync (010/011) đều phải có case cô lập `clinic_id`. Đặc biệt TC-DATA-024 (super admin không đọc PHI) và TC-DATA-022 (export khi expired — PDPA) là ràng buộc nghiệp vụ cứng từ saas_platform_model §5.2 và §8.3.
3. **DATA-008 backup là system-scope** (BYPASSRLS, dump toàn DB) — khác bản chất với export per-clinic; test phải làm rõ ranh giới để không nhầm thành lỗ hổng đa tenant.
4. **DATA-001/002/003/009 là Phase 2 (💡 IDEA)** — viết test ở mức spec/skeleton, không kỳ vọng pass tới khi implement.
5. **DATA-010/011 (TASK-016 DONE)**: cần truy ngược test thực tế của TASK-016 (FE vitest + có thể Rust/Tauri) để nâng PARTIAL → COVERED; hiện không mount được repo nên giữ PARTIAL.

> Khi mount lại được `clinic-cms-merge` (và repo TASK-016), cập nhật cột Coverage: đối chiếu `tests/integration` cho export endpoints (DATA-004..007), `tests/` cho Arq backup job (DATA-008), và test suite TASK-016 cho sync (DATA-010/011).
