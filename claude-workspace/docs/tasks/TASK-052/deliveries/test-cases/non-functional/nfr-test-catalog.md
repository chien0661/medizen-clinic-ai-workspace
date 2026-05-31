# Test Case Catalog — NFR · Yêu cầu Phi chức năng (Performance / Security / Reliability / Compliance)

**Nguồn:** function_list_data.py (group NFR, dòng 1795–1981) + clinic_management_function_list.md (§26, NFR-001..046) + system_design / SaaS platform model + SECURITY.md (§NFR-023..046).
**Phạm vi:** 46 functions (NFR-001 → NFR-046).  **Tổng test case:** 78.  **Ngày:** 2026-05-30.

> **Ghi chú Coverage:** Thư mục `clinic-cms-merge/app` và `clinic-cms-merge/tests` KHÔNG tồn tại trong môi trường hiện tại. Tuy nhiên test backend thực tế nằm tại `E:\MyProject\clinic-cms-workspace\claude-workspace\tests` (61 file unit + integration, hit DB thật + Redis theo Quality Gate). Coverage dưới đây được đối chiếu trực tiếp với các file test này; nơi không có test tương ứng thì ghi MISSING và suy ra từ cột status nguồn (✅ DONE / 🔄 IN_PROGRESS / ⬜ TODO).
>
> **Lưu ý loại NFR:** Nhiều NFR là yêu cầu hạ tầng/vận hành/quy trình (TLS, WAF, DDoS, KMS, mTLS, pen test, breach notification, code signing, backup ACL, CI gate) — kiểm bằng **kiểm thử cấu hình / drill / audit thủ công**, không phải unit/integration thuần; đã ghi Layer = Manual/Config/Infra/Ops/CI.
> NFR-044 (forensic hash chain) tham chiếu **TASK-037** (audit-hash-chain-functional-design.md) — chưa thấy test hash-chain trong tests hiện tại → MISSING/PARTIAL.

---

## 1. Ma trận truy vết (Function → Test Cases → Coverage)

| Function | Tên chức năng | Status (nguồn) | Test Case IDs | Coverage |
|---|---|---|---|---|
| NFR-001 | API response time (p95 <500ms) | 🔄 IN_PROGRESS | TC-NFR-001, TC-NFR-002 | MISSING (chưa có test perf API chung) |
| NFR-002 | Page load time (FCP/TTI) | 🔄 IN_PROGRESS | TC-NFR-003 | MISSING (Lighthouse, ngoài backend tests) |
| NFR-003 | Concurrent users (≥100/clinic) | ⬜ TODO | TC-NFR-004, TC-NFR-005 | MISSING (cần load test Locust) |
| NFR-004 | Uptime SLA 99.5% | ⬜ TODO | TC-NFR-006 | MISSING (vận hành/monitoring) |
| NFR-005 | Encryption in-transit (TLS 1.3) | ✅ DONE | TC-NFR-007, TC-NFR-008 | MISSING (TLS ở tầng infra, chưa có config test) |
| NFR-006 | Encryption at-rest (TDE AES-256) | 🔄 IN_PROGRESS | TC-NFR-009, TC-NFR-010 | MISSING (TDE infra) |
| NFR-007 | Multi-tenant isolation (RLS) | ✅ DONE | TC-NFR-011, TC-NFR-012, TC-NFR-013 | COVERED (test_rls_isolation, test_tenant_isolation_full, test_rls_admin_bypass, patients/test_rls_isolation_cms_app_role) |
| NFR-008 | OWASP Top 10 protection | 🔄 IN_PROGRESS | TC-NFR-014, TC-NFR-015, TC-NFR-016 | PARTIAL (test_jwt_signature; injection/CSP chưa có test riêng) |
| NFR-009 | Audit log immutable (append-only) | ✅ DONE | TC-NFR-017, TC-NFR-018 | COVERED (test_audit_immutable, test_audit_lifecycle) |
| NFR-010 | Data retention BN (30 năm) | ⬜ TODO | TC-NFR-019 | MISSING (archive job chưa có) |
| NFR-011 | Backup & DR (RTO 4h / RPO 24h) | ⬜ TODO | TC-NFR-020, TC-NFR-021 | MISSING (quy trình restore) |
| NFR-012 | Accessibility WCAG 2.1 AA | ✅ DONE | TC-NFR-022 | MISSING (aXe-core ở FE, ngoài backend tests) |
| NFR-013 | Browser support | ✅ DONE | TC-NFR-023 | MISSING (manual matrix) |
| NFR-014 | OS support (Tauri) | ✅ DONE | TC-NFR-024 | MISSING (manual matrix) |
| NFR-015 | Responsive (web fallback) | ⬜ TODO | TC-NFR-025 | MISSING (manual UI) |
| NFR-016 | Localization vi/en | ✅ DONE | TC-NFR-026, TC-NFR-027 | MISSING (i18n ở FE) |
| NFR-017 | Code coverage (new ≥80%) | 🔄 IN_PROGRESS | TC-NFR-028 | PARTIAL (CI gate; cần xác minh cấu hình pipeline) |
| NFR-018 | Observability (log/metrics/trace) | 🔄 IN_PROGRESS | TC-NFR-029, TC-NFR-030 | PARTIAL (test_request_id, test_request_id_e2e; metrics/trace chưa có test) |
| NFR-019 | Search performance (100k p95<100ms) | ✅ DONE | TC-NFR-031, TC-NFR-032 | COVERED (patients/test_patients_perf.py) |
| NFR-020 | Offline capability (Tauri sync) | 🔄 IN_PROGRESS | TC-NFR-033, TC-NFR-034, TC-NFR-035 | MISSING (sync Tauri ở client, chưa có test) |
| NFR-021 | Compliance HIPAA + Nghị định 13 | 🔄 IN_PROGRESS | TC-NFR-036 | MISSING (checklist review thủ công) |
| NFR-022 | Rate limiting (SlowAPI) | ✅ DONE | TC-NFR-037, TC-NFR-038 | COVERED login (test_auth_rate_limit.py); PARTIAL write/reports |
| NFR-023 | Data classification 4-tier | ⬜ TODO | TC-NFR-039 | MISSING (inventory review) |
| NFR-024 | Column-level encryption T3 | ⬜ TODO | TC-NFR-040, TC-NFR-041 | MISSING (chưa triển khai) |
| NFR-025 | Per-tenant encryption keys | ⬜ TODO | TC-NFR-042, TC-NFR-043 | MISSING (KMS chưa triển khai) |
| NFR-026 | Key rotation policy | 🔄 IN_PROGRESS | TC-NFR-044 | MISSING (rotation job chưa có) |
| NFR-027 | Bcrypt cost ≥12 | 🔄 IN_PROGRESS | TC-NFR-045, TC-NFR-046 | PARTIAL (test_security.py hash/verify; cần xác minh cost + history) |
| NFR-028 | JWT RS256 + key rotation | ⬜ TODO | TC-NFR-047 | MISSING (v2; hiện HS256 — test_jwt_signature) |
| NFR-029 | Session fingerprinting | ⬜ TODO | TC-NFR-048 | MISSING (v2) |
| NFR-030 | PII redaction trong log | 🔄 IN_PROGRESS | TC-NFR-049, TC-NFR-050 | COVERED (test_audit_pii_redaction.py) |
| NFR-031 | Data minimization | ⬜ TODO | TC-NFR-051 | MISSING |
| NFR-032 | Right to Erasure (Nghị định 13) | ⬜ TODO | TC-NFR-052, TC-NFR-053 | MISSING (v2) |
| NFR-033 | Data portability | ⬜ TODO | TC-NFR-054 | MISSING (v2) |
| NFR-034 | WAF | ⬜ TODO | TC-NFR-055 | MISSING (infra v2) |
| NFR-035 | DDoS protection | ⬜ TODO | TC-NFR-056 | MISSING (infra v2) |
| NFR-036 | mTLS internal service-to-service | ⬜ TODO | TC-NFR-057 | MISSING (infra v2) |
| NFR-037 | SAST static analysis | 🔄 IN_PROGRESS | TC-NFR-058 | PARTIAL (CI: ruff/Bandit/Semgrep; cần xác minh pipeline) |
| NFR-038 | DAST dynamic analysis | ⬜ TODO | TC-NFR-059 | MISSING (OWASP ZAP v2) |
| NFR-039 | Dependency scanning | 🔄 IN_PROGRESS | TC-NFR-060 | PARTIAL (CI: Safety/npm audit/Trivy) |
| NFR-040 | Secret management | 🔄 IN_PROGRESS | TC-NFR-061, TC-NFR-062 | PARTIAL (git-secrets/scan; cần xác minh) |
| NFR-041 | Backup encryption + ACL | ⬜ TODO | TC-NFR-063 | MISSING (ops) |
| NFR-042 | Anomaly detection audit log | ⬜ TODO | TC-NFR-064, TC-NFR-065 | MISSING (job chưa có) |
| NFR-043 | Breach notification ≤72h | ⬜ TODO | TC-NFR-066 | MISSING (quy trình/drill) |
| NFR-044 | Forensic logging + hash chain | ⬜ TODO | TC-NFR-067, TC-NFR-068, TC-NFR-069 | MISSING (TASK-037; chưa thấy test hash-chain) |
| NFR-045 | Tauri code signing + secure storage | 🔄 IN_PROGRESS | TC-NFR-070, TC-NFR-071 | MISSING (build/manual) |
| NFR-046 | Pen test annual | ⬜ TODO | TC-NFR-072 | MISSING (3rd-party) |

> **Bao phủ 100% group NFR:** 46/46 function đều có ≥ 1 test case. Bổ sung 6 test case cross-cutting TC-NFR-073..078 kiểm tra thuộc tính NFR ghép (RLS + perf, cache tenant, 401/403, rate-limit + audit, restore + RLS + hash chain).
>
> **Test file backend hiện có (đường dẫn tuyệt đối, làm chứng cứ Coverage):**
> - RLS: `E:\MyProject\clinic-cms-workspace\claude-workspace\tests\integration\test_rls_isolation.py`, `test_tenant_isolation_full.py`, `test_rls_admin_bypass.py`, `patients\test_rls_isolation_cms_app_role.py`
> - Audit immutable: `tests\integration\test_audit_immutable.py`, `test_audit_lifecycle.py`
> - PII redaction: `tests\integration\test_audit_pii_redaction.py`
> - Search perf: `tests\integration\patients\test_patients_perf.py`
> - Rate limit: `tests\integration\test_auth_rate_limit.py`
> - JWT/observability: `tests\integration\test_jwt_signature.py`, `test_request_id.py`, `test_request_id_e2e.py`
> - Bcrypt/security: `tests\unit\test_security.py`

---

## 2. Chi tiết Test Cases

### TC-NFR-001 — API đọc đạt p95 < 500ms (happy path)
- **Function:** NFR-001
- **Loại:** Happy path (performance)
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Seed 1 clinic ≥ 1.000 BN, ≥ 5.000 visit; structlog middleware + Prometheus bật.
- **Bước thực hiện:** 1) Gửi 200 request tuần tự tới các endpoint đọc trọng yếu (GET /patients, /visits, /appointments). 2) Đo latency từng request. 3) Tính p50/p95/p99.
- **Dữ liệu test:** Bộ seed chuẩn 1 clinic.
- **Kết quả mong đợi:** p50 < 200ms · p95 < 500ms · p99 < 1s (đúng ngưỡng NFR-001). Không lỗi 5xx.
- **Coverage hiện tại:** MISSING (chưa có test perf API chung; chỉ patient search có perf test — xem NFR-019)

### TC-NFR-002 — Endpoint /reports/* được nới ngưỡng p95 < 2s (edge)
- **Function:** NFR-001
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Dữ liệu báo cáo lớn.
- **Bước thực hiện:** 1) Gọi các endpoint /reports/* với khoảng thời gian rộng. 2) Đo p95.
- **Dữ liệu test:** Dataset báo cáo ≥ 12 tháng.
- **Kết quả mong đợi:** /reports/* p95 < 2s (ngoại lệ cho phép); endpoint khác vẫn < 500ms.
- **Coverage hiện tại:** MISSING

### TC-NFR-003 — FCP < 1.5s & TTI < 2.5s trên 4G (happy path)
- **Function:** NFR-002
- **Loại:** Happy path (performance UI)
- **Ưu tiên:** P2
- **Layer:** Manual/UI (Lighthouse + Web Vitals)
- **Tiền điều kiện:** Build production FE, throttle 4G, máy mid-range (Snapdragon 700-series).
- **Bước thực hiện:** 1) Chạy Lighthouse CI trên các màn chính (login, dashboard, patient list). 2) Ghi FCP, TTI.
- **Dữ liệu test:** Cấu hình throttle 4G chuẩn Lighthouse.
- **Kết quả mong đợi:** FCP < 1.5s; TTI < 2.5s.
- **Coverage hiện tại:** MISSING (Lighthouse ở FE/TASK-017, ngoài backend tests)

### TC-NFR-004 — 100 concurrent users không degrade > 20% (happy path)
- **Function:** NFR-003
- **Loại:** Happy path (load)
- **Ưu tiên:** P1
- **Layer:** E2E (Locust)
- **Tiền điều kiện:** Staging tương đương production; pool connection 20 + Redis pool 10.
- **Bước thực hiện:** 1) Đo baseline latency 1 user. 2) Locust 100 concurrent users/clinic, scenario 70% browse + 20% write + 10% report, 5 phút. 3) So sánh latency.
- **Dữ liệu test:** 100 user mô phỏng.
- **Kết quả mong đợi:** Response time tăng ≤ 20% so baseline; tỉ lệ lỗi < 1%.
- **Coverage hiện tại:** MISSING (cần load test Locust trước v1 GA)

### TC-NFR-005 — Cạn kiệt connection pool có kiểm soát (negative)
- **Function:** NFR-003
- **Loại:** Negative
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Pool DB cấu hình giới hạn nhỏ để test.
- **Bước thực hiện:** 1) Tạo số kết nối đồng thời vượt pool (N+5). 2) Quan sát.
- **Dữ liệu test:** N+5 request đồng thời.
- **Kết quả mong đợi:** Request thừa xếp hàng/timeout có kiểm soát (503 rõ ràng), không treo vô hạn; pool phục hồi khi tải giảm.
- **Coverage hiện tại:** MISSING

### TC-NFR-006 — Uptime SLA 99.5% & maintenance window (happy path)
- **Function:** NFR-004
- **Loại:** Happy path (vận hành)
- **Ưu tiên:** P2
- **Layer:** Infra/Ops (monitoring)
- **Tiền điều kiện:** Có uptime monitoring (Pingdom/UptimeRobot).
- **Bước thực hiện:** 1) Lấy số liệu uptime tháng. 2) Đối chiếu downtime vs ngưỡng 3.6h/tháng (trừ maintenance đã thông báo 7 ngày trước, max 4h ngoài giờ).
- **Dữ liệu test:** Log uptime 30 ngày.
- **Kết quả mong đợi:** Uptime ≥ 99.5%; mọi maintenance window thông báo trước 7 ngày.
- **Coverage hiện tại:** MISSING (vận hành/monitoring)

### TC-NFR-007 — TLS 1.3 bắt buộc, từ chối TLS 1.2 (security / happy path)
- **Function:** NFR-005
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Config (kiểm tra TLS)
- **Tiền điều kiện:** Endpoint production/staging có TLS.
- **Bước thực hiện:** 1) Bắt tay TLS 1.3 (`openssl s_client -tls1_3`). 2) Thử ép TLS 1.2 (`-tls1_2`). 3) Kiểm HSTS header (max-age 1 năm + preload).
- **Dữ liệu test:** không.
- **Kết quả mong đợi:** TLS 1.3 thành công; TLS 1.2 bị từ chối; header `Strict-Transport-Security` preload.
- **Coverage hiện tại:** MISSING (status DONE TASK-001 nhưng TLS ở tầng infra/reverse-proxy, chưa có config test trong repo)

### TC-NFR-008 — Cert auto-renew Let's Encrypt còn hạn (edge)
- **Function:** NFR-005
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Infra/Ops
- **Tiền điều kiện:** Cert Let's Encrypt cấu hình certbot auto-renew.
- **Bước thực hiện:** 1) Kiểm ngày hết hạn cert. 2) Kiểm job renew.
- **Dữ liệu test:** không.
- **Kết quả mong đợi:** Cert hợp lệ, còn > 30 ngày hoặc renew tự động hoạt động.
- **Coverage hiện tại:** MISSING

### TC-NFR-009 — Dữ liệu at-rest mã hóa AES-256 (security / happy path)
- **Function:** NFR-006
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Config / Infra
- **Tiền điều kiện:** Postgres TDE AES-256 bật cho data + WAL.
- **Bước thực hiện:** 1) Kiểm cấu hình TDE/encryption tablespace. 2) Kiểm WAL mã hóa. 3) Backup mã hóa AES-256, key trong KMS.
- **Dữ liệu test:** không.
- **Kết quả mong đợi:** Data + WAL + backup AES-256; key qua KMS; rotation 90 ngày.
- **Coverage hiện tại:** MISSING (status IN_PROGRESS TASK-002; TDE ở tầng infra)

### TC-NFR-010 — File data thô không đọc được ở mức OS (security / negative)
- **Function:** NFR-006
- **Loại:** Security / Negative
- **Ưu tiên:** P1
- **Layer:** Infra/Ops
- **Tiền điều kiện:** TDE bật.
- **Bước thực hiện:** 1) Truy cập file data/WAL trực tiếp ở mức OS.
- **Dữ liệu test:** không.
- **Kết quả mong đợi:** Nội dung ở dạng ciphertext, không đọc được plaintext PHI.
- **Coverage hiện tại:** MISSING

### TC-NFR-011 — RLS cô lập dữ liệu giữa clinic (security / happy path)
- **Function:** NFR-007
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Clinic A và B có dữ liệu riêng; RLS bật, session var `app.current_clinic_id`.
- **Bước thực hiện:** 1) Set context = Clinic A. 2) Query bảng patient KHÔNG filter clinic_id thủ công.
- **Dữ liệu test:** P_A thuộc A, P_B thuộc B.
- **Kết quả mong đợi:** Chỉ trả dữ liệu Clinic A; P_B không xuất hiện. RLS chặn ở tầng DB.
- **Coverage hiện tại:** COVERED (test_rls_isolation.py, test_tenant_isolation_full.py, patients/test_rls_isolation_cms_app_role.py)

### TC-NFR-012 — Thiếu session var → deny by default (security / negative)
- **Function:** NFR-007
- **Loại:** Security / Negative
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** RLS bật, không set `app.current_clinic_id`.
- **Bước thực hiện:** 1) Kết nối role app không set tenant. 2) Query bảng có RLS.
- **Dữ liệu test:** dữ liệu nhiều clinic.
- **Kết quả mong đợi:** Trả rỗng (deny by default) hoặc lỗi — KHÔNG trả toàn bộ dữ liệu mọi clinic.
- **Coverage hiện tại:** COVERED (test_rls_isolation.py + test_rls_admin_bypass.py kiểm hành vi không-context/admin bypass)

### TC-NFR-013 — Ghi cross-tenant bị chặn (security / negative)
- **Function:** NFR-007
- **Loại:** Security / Negative
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Context = Clinic A.
- **Bước thực hiện:** 1) Thử INSERT/UPDATE bản ghi với clinic_id = B.
- **Dữ liệu test:** payload clinic_id = B.
- **Kết quả mong đợi:** RLS WITH CHECK từ chối; dữ liệu B không đổi.
- **Coverage hiện tại:** PARTIAL (test_tenant_isolation_full.py; cần xác minh case WITH CHECK ghi cross-tenant cụ thể)

### TC-NFR-014 — Chống SQL Injection (security)
- **Function:** NFR-008
- **Loại:** Security / Negative
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Endpoint nhận tham số tìm kiếm.
- **Bước thực hiện:** 1) Gửi payload injection (`' OR '1'='1`, `; DROP TABLE`) qua query/body (vd /patients/search).
- **Dữ liệu test:** chuỗi injection.
- **Kết quả mong đợi:** Parameterized query xử lý an toàn; không lộ dữ liệu, không lỗi DB; trả kết quả rỗng/hợp lệ.
- **Coverage hiện tại:** PARTIAL (patients/test_patients_negative.py có case input bất thường; chưa có test injection chuyên biệt)

### TC-NFR-015 — CSRF & SameSite cookie (security)
- **Function:** NFR-008
- **Loại:** Security / Negative
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Phiên đăng nhập hợp lệ.
- **Bước thực hiện:** 1) Gửi request ghi giả lập cross-site không kèm CSRF token.
- **Dữ liệu test:** request không token.
- **Kết quả mong đợi:** Bị từ chối (403); cookie có SameSite + CSRF token bắt buộc.
- **Coverage hiện tại:** MISSING

### TC-NFR-016 — Signed JWT integrity + security headers (security)
- **Function:** NFR-008
- **Loại:** Security
- **Ưu tiên:** P1
- **Layer:** Integration / E2E
- **Tiền điều kiện:** App chạy.
- **Bước thực hiện:** 1) Sửa payload JWT rồi gọi endpoint (A08 Data Integrity). 2) Kiểm header CSP/X-Frame-Options.
- **Dữ liệu test:** JWT giả mạo.
- **Kết quả mong đợi:** JWT giả mạo bị từ chối; CSP có mặt; XSS chặn bởi React auto-escape + CSP.
- **Coverage hiện tại:** PARTIAL (test_jwt_signature.py kiểm chữ ký JWT; security headers/CSP chưa có test)

### TC-NFR-017 — audit_log append-only, không UPDATE/DELETE (security / happy path)
- **Function:** NFR-009
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Bảng audit_log revoke UPDATE/DELETE khỏi role app.
- **Bước thực hiện:** 1) INSERT 1 audit row (qua action nghiệp vụ). 2) Thử UPDATE và DELETE trực tiếp row đó.
- **Dữ liệu test:** 1 audit row.
- **Kết quả mong đợi:** INSERT thành công; UPDATE/DELETE bị từ chối.
- **Coverage hiện tại:** COVERED (test_audit_immutable.py)

### TC-NFR-018 — Vòng đời audit + retention (edge)
- **Function:** NFR-009
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Integration + Infra/Ops
- **Tiền điều kiện:** Chính sách retention cấu hình.
- **Bước thực hiện:** 1) Kiểm vòng đời ghi audit (test_audit_lifecycle). 2) Kiểm job retention 7 năm + backup riêng offsite.
- **Dữ liệu test:** chuỗi audit event.
- **Kết quả mong đợi:** Audit ghi đúng vòng đời; retention ≥ 7 năm (BYT); backup tách riêng + offsite.
- **Coverage hiện tại:** PARTIAL (test_audit_lifecycle.py phủ vòng đời; retention/offsite là vận hành — MISSING)

### TC-NFR-019 — Lượt khám/bệnh án giữ 30 năm + auto-archive 5 năm (happy path)
- **Function:** NFR-010
- **Loại:** Happy path (vận hành)
- **Ưu tiên:** P2
- **Layer:** Integration / Ops
- **Tiền điều kiện:** Có cơ chế archive (S3 Glacier/cold storage).
- **Bước thực hiện:** 1) Tạo visit > 5 năm. 2) Chạy archive job. 3) Kiểm dữ liệu chuyển storage rẻ hơn, vẫn khôi phục on-demand < 24h.
- **Dữ liệu test:** visit cũ > 5 năm.
- **Kết quả mong đợi:** Dữ liệu > 5 năm auto-archive; giữ tới 30 năm; truy xuất được.
- **Coverage hiện tại:** MISSING (status TODO v2)

### TC-NFR-020 — Backup daily/weekly tạo artifact hợp lệ (happy path)
- **Function:** NFR-011
- **Loại:** Happy path (vận hành)
- **Ưu tiên:** P1
- **Layer:** Infra/Ops
- **Tiền điều kiện:** Cơ chế backup cấu hình (7 daily + 4 weekly + 12 monthly).
- **Bước thực hiện:** 1) Kích hoạt full backup. 2) Kiểm artifact (size > 0, checksum). 3) Liệt kê bảng trong dump.
- **Dữ liệu test:** DB nhiều clinic.
- **Kết quả mong đợi:** Backup hoàn tất, có checksum, đủ schema + data.
- **Coverage hiện tại:** MISSING

### TC-NFR-021 — Test restore đạt RTO 4h / RPO 24h (edge)
- **Function:** NFR-011
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Infra/Ops
- **Tiền điều kiện:** Có backup hợp lệ; DB đích sạch.
- **Bước thực hiện:** 1) Restore backup. 2) Đo thời gian restore (RTO). 3) So khớp số bản ghi & checksum; xác định mất tối đa 24h dữ liệu (RPO).
- **Dữ liệu test:** backup từ TC-NFR-020.
- **Kết quả mong đợi:** Restore < 4h (RTO); mất dữ liệu ≤ 24h (RPO); RLS + ràng buộc còn nguyên; app chạy được trên DB restore.
- **Coverage hiện tại:** MISSING

### TC-NFR-022 — Mọi màn pass aXe-core 0 violations (happy path)
- **Function:** NFR-012
- **Loại:** Happy path (accessibility)
- **Ưu tiên:** P1
- **Layer:** Manual/UI (aXe-core)
- **Tiền điều kiện:** FE build.
- **Bước thực hiện:** 1) Chạy aXe-core scan các màn chính. 2) Kiểm contrast ≥ 4.5:1 text. 3) Điều hướng 100% bằng bàn phím.
- **Dữ liệu test:** không.
- **Kết quả mong đợi:** 0 violations AA; keyboard navigation đầy đủ; screen reader (NVDA/JAWS) đọc được.
- **Coverage hiện tại:** MISSING (aXe-core ở FE/TASK-017, ngoài backend tests)

### TC-NFR-023 — Hỗ trợ trình duyệt mục tiêu (happy path)
- **Function:** NFR-013
- **Loại:** Happy path
- **Ưu tiên:** P2
- **Layer:** Manual/UI (BrowserStack matrix)
- **Tiền điều kiện:** Môi trường test đa trình duyệt.
- **Bước thực hiện:** 1) Mở app trên Chrome/Edge/Firefox (2 bản mới nhất), Safari 15+.
- **Dữ liệu test:** không.
- **Kết quả mong đợi:** App hoạt động đầy đủ; IE11 không hỗ trợ.
- **Coverage hiện tại:** MISSING (manual matrix)

### TC-NFR-024 — Tauri chạy đúng OS + bundle < 80MB (happy path)
- **Function:** NFR-014
- **Loại:** Happy path
- **Ưu tiên:** P2
- **Layer:** Manual/Build
- **Tiền điều kiện:** Bundle Tauri 3 nền tảng.
- **Bước thực hiện:** 1) Cài & chạy trên Windows 10+ (1903+), macOS 11+, Ubuntu 20.04+. 2) Kiểm bundle size.
- **Dữ liệu test:** không.
- **Kết quả mong đợi:** Chạy ổn 3 OS; mỗi bundle < 80MB.
- **Coverage hiện tại:** MISSING (manual/TASK-016)

### TC-NFR-025 — Web fallback responsive tablet 1024×768 (happy path)
- **Function:** NFR-015
- **Loại:** Happy path
- **Ưu tiên:** P2
- **Layer:** Manual/UI
- **Tiền điều kiện:** Web fallback build.
- **Bước thực hiện:** 1) Mở admin lite trên viewport 1024×768. 2) Kiểm layout & landing/đăng ký BN responsive.
- **Dữ liệu test:** không.
- **Kết quả mong đợi:** Layout không vỡ; chức năng admin lite dùng được.
- **Coverage hiện tại:** MISSING (status TODO v2)

### TC-NFR-026 — Chuyển ngôn ngữ vi/en đầy đủ (happy path)
- **Function:** NFR-016
- **Loại:** Happy path
- **Ưu tiên:** P2
- **Layer:** Manual/UI + Unit (i18n)
- **Tiền điều kiện:** i18next cấu hình.
- **Bước thực hiện:** 1) Đổi locale vi ↔ en. 2) Duyệt các màn chính. 3) Kiểm date/number/currency theo locale (Intl).
- **Dữ liệu test:** không.
- **Kết quả mong đợi:** Vi mặc định; mọi string qua i18next; format theo locale.
- **Coverage hiện tại:** MISSING (i18n ở FE/TASK-017)

### TC-NFR-027 — Không còn string hardcode + pseudo-localization (negative)
- **Function:** NFR-016
- **Loại:** Negative
- **Ưu tiên:** P2
- **Layer:** Unit / Lint (FE)
- **Tiền điều kiện:** Codebase FE.
- **Bước thực hiện:** 1) Bật pseudo-localization (zz-locale) để bắt missing translation. 2) Quét chuỗi UI hardcode.
- **Dữ liệu test:** không.
- **Kết quả mong đợi:** Không chuỗi UI hardcode; mọi key có cả vi & en; zz-locale không lộ chuỗi gốc.
- **Coverage hiện tại:** MISSING

### TC-NFR-028 — CI gate enforce coverage (happy path)
- **Function:** NFR-017
- **Loại:** Happy path (process)
- **Ưu tiên:** P1
- **Layer:** CI / Config
- **Tiền điều kiện:** Pipeline CI cấu hình coverage gate; integration test hit DB thật + Redis (không mock).
- **Bước thực hiện:** 1) Mở PR với code mới coverage < 80%. 2) Quan sát gate.
- **Dữ liệu test:** PR coverage thấp.
- **Kết quả mong đợi:** CI fail khi new code < 80% hoặc overall < 70%; reviewer reject mock-only integration test.
- **Coverage hiện tại:** PARTIAL (bộ test integration đã hit DB thật + Redis đúng quy tắc; cần xác minh CI gate config)

### TC-NFR-029 — Log JSON có request_id/user_id/clinic_id/applied_role (happy path)
- **Function:** NFR-018
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration
- **Tiền điều kiện:** structlog JSON cấu hình.
- **Bước thực hiện:** 1) Gọi 1 request. 2) Kiểm dòng log + response header X-Request-ID.
- **Dữ liệu test:** 1 request bất kỳ.
- **Kết quả mong đợi:** Log JSON chứa request_id + user_id + clinic_id + applied_role + latency + status; parse được.
- **Coverage hiện tại:** PARTIAL (test_request_id.py, test_request_id_e2e.py phủ request_id; cần xác minh đủ user_id/clinic_id/applied_role)

### TC-NFR-030 — Metrics Prometheus + trace OpenTelemetry (happy path)
- **Function:** NFR-018
- **Loại:** Happy path
- **Ưu tiên:** P2
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Endpoint /metrics + tracing bật.
- **Bước thực hiện:** 1) Sinh vài request. 2) Đọc /metrics. 3) Kiểm trace span propagate trace_id qua header.
- **Dữ liệu test:** vài request.
- **Kết quả mong đợi:** Counter & latency histogram tăng; trace span gắn trace_id.
- **Coverage hiện tại:** MISSING (chưa có test metrics/trace)

### TC-NFR-031 — Patient search 100k records p95 < 100ms (happy path)
- **Function:** NFR-019
- **Loại:** Happy path (performance)
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Clinic seed 100k bệnh nhân; GIN index trigram + unaccent + partial index.
- **Bước thực hiện:** 1) Chạy phone search + name fuzzy search nhiều lần. 2) Tính p95.
- **Dữ liệu test:** 100k patient.
- **Kết quả mong đợi:** Phone search p95 < 100ms (PAT-009: ≈ 46.9ms PASS); medicine search 10k p95 < 50ms.
- **Coverage hiện tại:** COVERED (patients/test_patients_perf.py)

### TC-NFR-032 — Global search (NAV-001) < 300ms (edge)
- **Function:** NFR-019
- **Loại:** Edge (performance)
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Dữ liệu đa entity + materialized view cho frequent queries.
- **Bước thực hiện:** 1) Gọi global search nhiều từ khóa. 2) Đo p95.
- **Dữ liệu test:** keyword đa loại.
- **Kết quả mong đợi:** Global search p95 < 300ms.
- **Coverage hiện tại:** PARTIAL (perf framework có ở test_patients_perf; global search chưa có test riêng)

### TC-NFR-033 — Offline tạo/sửa → sync khi online (happy path)
- **Function:** NFR-020
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** E2E (Tauri) / Integration
- **Tiền điều kiện:** Client Tauri SQLite mirror (50 BN cuối), đang offline < 30 phút.
- **Bước thực hiện:** 1) Tạo/sửa BN khi offline. 2) Kết nối lại. 3) Kích hoạt sync.
- **Dữ liệu test:** 1 BN mới offline.
- **Kết quả mong đợi:** Thay đổi đẩy lên server đúng clinic; local "synced"; không trùng lặp; banner "Đang offline" hiển thị khi ngắt mạng.
- **Coverage hiện tại:** MISSING (sync Tauri ở client/TASK-016, chưa có test)

### TC-NFR-034 — Xung đột sửa đồng thời → last-write-wins (edge)
- **Function:** NFR-020
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Integration
- **Tiền điều kiện:** Cùng bản ghi sửa offline + trên server.
- **Bước thực hiện:** 1) Sửa bản ghi X offline. 2) X cũng bị sửa trên server. 3) Sync.
- **Dữ liệu test:** bản ghi X hai phiên bản.
- **Kết quả mong đợi:** Áp dụng last-write-wins (timestamp/version) như NFR-020; không mất dữ liệu âm thầm.
- **Coverage hiện tại:** MISSING

### TC-NFR-035 — Sync không vượt biên clinic (security / RLS)
- **Function:** NFR-020
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration
- **Tiền điều kiện:** Client thuộc Clinic A.
- **Bước thực hiện:** 1) Client A cố sync bản ghi gắn clinic_id = B (giả mạo payload).
- **Dữ liệu test:** payload clinic_id = B.
- **Kết quả mong đợi:** Server từ chối (403 hoặc RLS WITH CHECK chặn); dữ liệu B không đổi.
- **Coverage hiện tại:** MISSING (luồng sync chưa có; RLS nền tảng đã COVERED — xem NFR-007)

### TC-NFR-036 — Checklist compliance 14 mục đạt (happy path)
- **Function:** NFR-021
- **Loại:** Happy path (process)
- **Ưu tiên:** P1
- **Layer:** Manual (audit checklist)
- **Tiền điều kiện:** Checklist 14 mục (TAB_MATRIX.md → Bảo mật → Compliance).
- **Bước thực hiện:** 1) Đối chiếu từng mục với hệ thống thực tế (HIPAA Privacy/Security Rule + Nghị định 13/2023).
- **Dữ liệu test:** không.
- **Kết quả mong đợi:** 14/14 mục đạt hoặc có kế hoạch; quarterly review (GĐ PK + legal) ghi nhận.
- **Coverage hiện tại:** MISSING (review thủ công)

### TC-NFR-037 — Rate limit login 10/min/IP (security / negative)
- **Function:** NFR-022
- **Loại:** Security / Negative
- **Ưu tiên:** P0
- **Layer:** Integration (real Redis)
- **Tiền điều kiện:** SlowAPI cấu hình.
- **Bước thực hiện:** 1) Gửi > 10 request login/phút từ 1 IP.
- **Dữ liệu test:** 11+ request login.
- **Kết quả mong đợi:** Sau ngưỡng trả **429** + header Retry-After; whitelist IP nội bộ không bị giới hạn.
- **Coverage hiện tại:** COVERED (test_auth_rate_limit.py)

### TC-NFR-038 — Rate limit write 60/min/user & reports 30/min/user (edge)
- **Function:** NFR-022
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Integration
- **Tiền điều kiện:** SlowAPI cấu hình per-endpoint.
- **Bước thực hiện:** 1) Gửi > 60 sensitive write/phút/user; > 30 reports query/phút/user.
- **Dữ liệu test:** request vượt ngưỡng.
- **Kết quả mong đợi:** 429 đúng ngưỡng từng nhóm endpoint.
- **Coverage hiện tại:** PARTIAL (test_auth_rate_limit phủ login; write/reports limit chưa có test riêng)

### TC-NFR-039 — Mọi cột T2/T3 được gán tier (happy path)
- **Function:** NFR-023
- **Loại:** Happy path (process)
- **Ưu tiên:** P2
- **Layer:** Manual (inventory review)
- **Tiền điều kiện:** PII inventory ~30 cột (SECURITY.md §1.1).
- **Bước thực hiện:** 1) Đối chiếu schema với phân loại T0–T3; kiểm PR template có checklist tier.
- **Dữ liệu test:** không.
- **Kết quả mong đợi:** Mọi field gán đúng 1 tier; ~30 cột PII ở T2/T3 liệt kê đầy đủ.
- **Coverage hiện tại:** MISSING (status TODO)

### TC-NFR-040 — Field T3 mã hóa column-level (security / happy path)
- **Function:** NFR-024
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Field T3 (CCCD, BHYT card, MFA secret, audit diff) cấu hình AES-256 column-level (envelope DEK/master).
- **Bước thực hiện:** 1) Lưu bản ghi T3 qua API. 2) Đọc cột thô trong DB. 3) Đọc lại qua API.
- **Dữ liệu test:** CCCD mẫu.
- **Kết quả mong đợi:** Cột thô là ciphertext (DBA thấy ciphertext); API trả plaintext đúng; master key không rời KMS.
- **Coverage hiện tại:** MISSING (status TODO; chưa triển khai)

### TC-NFR-041 — Không decrypt T3 nếu thiếu quyền/khóa (security / negative)
- **Function:** NFR-024
- **Loại:** Security / Negative
- **Ưu tiên:** P0
- **Layer:** Integration
- **Tiền điều kiện:** Field T3 mã hóa.
- **Bước thực hiện:** 1) Truy cập field T3 với context không có quyền decrypt.
- **Dữ liệu test:** request thiếu quyền.
- **Kết quả mong đợi:** Không trả plaintext; trả masked hoặc 403; KMS log per-decrypt; không log plaintext.
- **Coverage hiện tại:** MISSING

### TC-NFR-042 — Mỗi clinic có master key riêng (security / happy path)
- **Function:** NFR-025
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration / KMS
- **Tiền điều kiện:** Per-tenant key `clinic:{id}:pii` trong KMS/Vault.
- **Bước thực hiện:** 1) Mã hóa dữ liệu Clinic A & B. 2) Kiểm key dùng khác nhau.
- **Dữ liệu test:** dữ liệu hai clinic.
- **Kết quả mong đợi:** Mỗi clinic 1 key; key A không giải mã được dữ liệu B (no cross-tenant).
- **Coverage hiện tại:** MISSING (status TODO; KMS chưa triển khai)

### TC-NFR-043 — Crypto-shred revoke key xóa dữ liệu 1 clinic (security / edge)
- **Function:** NFR-025
- **Loại:** Edge / Security
- **Ưu tiên:** P1
- **Layer:** Integration / KMS
- **Tiền điều kiện:** Clinic A có dữ liệu mã hóa.
- **Bước thực hiện:** 1) Revoke master key clinic A trong KMS. 2) Thử đọc dữ liệu A.
- **Dữ liệu test:** dữ liệu A.
- **Kết quả mong đợi:** Dữ liệu A không thể giải mã (instant destruction); clinic khác không ảnh hưởng.
- **Coverage hiện tại:** MISSING

### TC-NFR-044 — Key rotation zero-downtime (happy path)
- **Function:** NFR-026
- **Loại:** Happy path / Edge
- **Ưu tiên:** P1
- **Layer:** Integration / KMS
- **Tiền điều kiện:** Chính sách rotation (master 1y, tenant 1y/on-demand, JWT 30d grace 7d, backup 90d, TLS 90d).
- **Bước thực hiện:** 1) Trigger rotate key. 2) Trong lúc rotate, đọc/ghi dữ liệu (re-encrypt background job).
- **Dữ liệu test:** dữ liệu mã hóa với key cũ.
- **Kết quả mong đợi:** Dữ liệu cũ vẫn giải mã được (grace overlap); ghi mới dùng key mới; không downtime.
- **Coverage hiện tại:** MISSING (status IN_PROGRESS; rotation job chưa có test)

### TC-NFR-045 — Password hash bcrypt cost ≥ 12 (security / happy path)
- **Function:** NFR-027
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Unit / Integration
- **Tiền điều kiện:** Đăng ký/đổi mật khẩu.
- **Bước thực hiện:** 1) Tạo user / đổi password. 2) Đọc password_hash. 3) Parse cost factor từ bcrypt hash (`$2b$12$...`).
- **Dữ liệu test:** password mẫu.
- **Kết quả mong đợi:** Cost factor ≥ 12; min length 12 + complexity.
- **Coverage hiện tại:** PARTIAL (test_security.py có hash/verify password; cần xác minh assert cost ≥ 12)

### TC-NFR-046 — Không tái sử dụng 5 password gần nhất + rotation 90 ngày (negative)
- **Function:** NFR-027
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** Integration
- **Tiền điều kiện:** User đã đổi password vài lần.
- **Bước thực hiện:** 1) Đổi password về 1 trong 5 password cũ.
- **Dữ liệu test:** password cũ.
- **Kết quả mong đợi:** Bị từ chối với thông báo không dùng lại password gần đây; rotation 90 ngày.
- **Coverage hiện tại:** PARTIAL (test_change_password.py có luồng đổi password; cần xác minh history 5)

### TC-NFR-047 — JWT RS256 + JWKS endpoint (security / happy path)
- **Function:** NFR-028
- **Loại:** Security
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** JWT chuyển sang RS256 (v2; Phase 1 vẫn HS256).
- **Bước thực hiện:** 1) Login lấy JWT. 2) Kiểm header alg=RS256. 3) Lấy public key /.well-known/jwks.json, verify.
- **Dữ liệu test:** JWT mẫu.
- **Kết quả mong đợi:** alg=RS256; verify bằng public key OK; rotation 30 ngày grace 7d.
- **Coverage hiện tại:** MISSING (status TODO v2; hiện HS256 — test_jwt_signature.py phủ HS256)

### TC-NFR-048 — Session fingerprint phát hiện device lạ (security / negative)
- **Function:** NFR-029
- **Loại:** Security / Negative
- **Ưu tiên:** P1
- **Layer:** Integration
- **Tiền điều kiện:** JWT đính fingerprint + IP + UA + geo (v2).
- **Bước thực hiện:** 1) Dùng JWT từ device/IP khác đột ngột.
- **Dữ liệu test:** JWT + UA/IP khác.
- **Kết quả mong đợi:** Force MFA/re-login + alert email "Phiên đăng nhập từ thiết bị mới [địa điểm, giờ]".
- **Coverage hiện tại:** MISSING (status TODO v2)

### TC-NFR-049 — PII bị redact trong structlog (security / happy path)
- **Function:** NFR-030
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration
- **Tiền điều kiện:** Global redact list ở app/core/audit.py.
- **Bước thực hiện:** 1) Action có PII (email, phone, CCCD). 2) Quét log/audit.
- **Dữ liệu test:** email `bs.an@hd.vn`, phone, CCCD.
- **Kết quả mong đợi:** Email → `b***@h***.vn`, phone `***1234`, CCCD `***7890`; không log full PII.
- **Coverage hiện tại:** COVERED (test_audit_pii_redaction.py)

### TC-NFR-050 — Field `__audit_exclude__` không bị log (negative)
- **Function:** NFR-030
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** Unit / Integration
- **Tiền điều kiện:** Model có `__audit_exclude__: ClassVar[frozenset[str]]`.
- **Bước thực hiện:** 1) Ghi audit cho model có field excluded.
- **Dữ liệu test:** model có field nhạy cảm excluded.
- **Kết quả mong đợi:** Field excluded không xuất hiện trong audit diff/log.
- **Coverage hiện tại:** PARTIAL (test_audit_pii_redaction.py + test_audit_writer.py; cần xác minh case __audit_exclude__ cụ thể)

### TC-NFR-051 — Quick mode chỉ thu thập field tối thiểu, PII không trong URL (happy path)
- **Function:** NFR-031
- **Loại:** Happy path
- **Ưu tiên:** P2
- **Layer:** Integration / UI
- **Tiền điều kiện:** Form đăng ký BN 2 mode (Quick/Full).
- **Bước thực hiện:** 1) Đăng ký BN Quick mode (tên+SĐT+DOB+giới). 2) Kiểm PII không nằm trong URL query string.
- **Dữ liệu test:** BN quick.
- **Kết quả mong đợi:** Lưu thành công với field tối thiểu; PII chỉ qua POST body, không vào access log.
- **Coverage hiện tại:** MISSING (status TODO)

### TC-NFR-052 — Right to Erasure: crypto-shred + soft delete (security / happy path)
- **Function:** NFR-032
- **Loại:** Security
- **Ưu tiên:** P1
- **Layer:** Integration
- **Tiền điều kiện:** Quy trình xóa theo Nghị định 13 (v2).
- **Bước thực hiện:** 1) BN yêu cầu xóa. 2) Confirm 2 bước. 3) Kiểm soft delete + crypto-shred key + audit event 'crypto.shred.executed'.
- **Dữ liệu test:** 1 hồ sơ BN.
- **Kết quả mong đợi:** Data on disk không đọc được (key shred); audit event ghi; process ≤ 30 ngày.
- **Coverage hiện tại:** MISSING (status TODO v2)

### TC-NFR-053 — Erasure irreversible cần confirm 2 bước (negative)
- **Function:** NFR-032
- **Loại:** Negative
- **Ưu tiên:** P2
- **Layer:** Integration
- **Tiền điều kiện:** Quy trình erasure 2 bước.
- **Bước thực hiện:** 1) Bỏ qua bước xác nhận thứ 2.
- **Dữ liệu test:** request thiếu confirm.
- **Kết quả mong đợi:** Không thực hiện xóa; yêu cầu đủ 2 bước.
- **Coverage hiện tại:** MISSING

### TC-NFR-054 — BN tự download data (JSON + PDF) mã hóa (happy path)
- **Function:** NFR-033
- **Loại:** Happy path
- **Ưu tiên:** P2
- **Layer:** Integration
- **Tiền điều kiện:** Self-service portal (v2).
- **Bước thực hiện:** 1) BN yêu cầu export. 2) Nhận JSON + PDF mã hóa AES-256 password user; TTL storage 24h.
- **Dữ liệu test:** 1 BN.
- **Kết quả mong đợi:** Export đúng data của chính BN (BN info, lịch sử khám, chẩn đoán, đơn thuốc, hóa đơn, CLS); file mã hóa; chỉ data BN đó (RLS).
- **Coverage hiện tại:** MISSING (status TODO v2)

### TC-NFR-055 — WAF chặn OWASP Top 10 payload (security)
- **Function:** NFR-034
- **Loại:** Security
- **Ưu tiên:** P2
- **Layer:** Infra/Config (Cloudflare/AWS WAF, v2)
- **Tiền điều kiện:** WAF cấu hình ruleset OWASP.
- **Bước thực hiện:** 1) Gửi payload chứa SQL keyword/bot signature; thử IP nước ngoài (geo-block).
- **Dữ liệu test:** payload tấn công.
- **Kết quả mong đợi:** WAF block trước khi tới app; geo-block per clinic config hoạt động.
- **Coverage hiện tại:** MISSING (status TODO v2)

### TC-NFR-056 — DDoS protection & circuit breaker (security / edge)
- **Function:** NFR-035
- **Loại:** Edge / Security
- **Ưu tiên:** P2
- **Layer:** Infra/Ops (v2)
- **Tiền điều kiện:** Cloudflare Pro + circuit breaker (slowapi + tenacity) + HPA.
- **Bước thực hiện:** 1) Mô phỏng burst lưu lượng cao.
- **Dữ liệu test:** flood request.
- **Kết quả mong đợi:** Circuit breaker mở; Always Online serve cache; auto-scale HPA + read replica; không sập toàn cục.
- **Coverage hiện tại:** MISSING (status TODO v2)

### TC-NFR-057 — mTLS giữa các service nội bộ (security)
- **Function:** NFR-036
- **Loại:** Security
- **Ưu tiên:** P2
- **Layer:** Infra/Config (v2)
- **Tiền điều kiện:** Cert internal CA (Vault); cert pinning.
- **Bước thực hiện:** 1) Kết nối API↔DB↔Redis↔Worker↔S3 với mTLS. 2) Thử kết nối không cert hợp lệ.
- **Dữ liệu test:** cert hợp lệ / không hợp lệ.
- **Kết quả mong đợi:** Yêu cầu mTLS; cert không hợp lệ bị từ chối; rotate 30 ngày; không password auth cho DB/Redis ở prod.
- **Coverage hiện tại:** MISSING (status TODO v2)

### TC-NFR-058 — SAST chặn PR high severity (security / process)
- **Function:** NFR-037
- **Loại:** Security / Negative
- **Ưu tiên:** P1
- **Layer:** CI
- **Tiền điều kiện:** ruff + Bandit + Semgrep + ESLint security pre-commit + CI.
- **Bước thực hiện:** 1) Mở PR có lỗ hổng high severity.
- **Dữ liệu test:** code có finding high.
- **Kết quả mong đợi:** CI block merge; báo cáo finding.
- **Coverage hiện tại:** PARTIAL (status IN_PROGRESS; cần xác minh CI config)

### TC-NFR-059 — DAST OWASP ZAP pre-prod (security / process)
- **Function:** NFR-038
- **Loại:** Security
- **Ưu tiên:** P2
- **Layer:** CI / Ops (v2)
- **Tiền điều kiện:** ZAP scan cấu hình pre-prod.
- **Bước thực hiện:** 1) Chạy ZAP full crawl + active scan + auth replay trước major release.
- **Dữ liệu test:** không.
- **Kết quả mong đợi:** Block release nếu high severity finding.
- **Coverage hiện tại:** MISSING (status TODO v2)

### TC-NFR-060 — Dependency scan chặn critical CVE (security / process)
- **Function:** NFR-039
- **Loại:** Security / Negative
- **Ưu tiên:** P1
- **Layer:** CI
- **Tiền điều kiện:** Safety + npm audit + Trivy chạy CI + nightly.
- **Bước thực hiện:** 1) Thêm dependency có critical CVE.
- **Dữ liệu test:** package có CVE.
- **Kết quả mong đợi:** Block deploy nếu CVE critical chưa patch ≤ 7 ngày; Dependabot/Renovate auto-PR.
- **Coverage hiện tại:** PARTIAL (status IN_PROGRESS)

### TC-NFR-061 — Không hardcode secret (security / negative)
- **Function:** NFR-040
- **Loại:** Security / Negative
- **Ưu tiên:** P0
- **Layer:** CI / Lint
- **Tiền điều kiện:** git-secrets pre-commit + GitHub secret scanning.
- **Bước thực hiện:** 1) Commit có API key/secret.
- **Dữ liệu test:** chuỗi secret giả.
- **Kết quả mong đợi:** Pre-commit/scan chặn; secret không vào repo.
- **Coverage hiện tại:** PARTIAL (status IN_PROGRESS)

### TC-NFR-062 — Secret lấy từ Vault/Secrets Manager ở prod (happy path)
- **Function:** NFR-040
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Config / Ops
- **Tiền điều kiện:** Prod dùng Vault/AWS Secrets Manager.
- **Bước thực hiện:** 1) Kiểm app đọc secret runtime từ Vault, không từ file .env trong prod; FE chỉ nhận VITE_ public config.
- **Dữ liệu test:** không.
- **Kết quả mong đợi:** Secret nạp từ secret manager; dev dùng .env.local (gitignore); Tauri không bundle secret.
- **Coverage hiện tại:** PARTIAL (test_config.py phủ config loading; cần xác minh nguồn secret prod)

### TC-NFR-063 — Backup mã hóa AES-256 + ACL MFA-required (security)
- **Function:** NFR-041
- **Loại:** Security
- **Ưu tiên:** P1
- **Layer:** Infra/Ops
- **Tiền điều kiện:** Backup gpg encrypt + S3 SSE-KMS; IAM giới hạn Ops+DBA.
- **Bước thực hiện:** 1) Kiểm backup gpg encrypt + checksum SHA-256 + sign GPG. 2) Thử restore không MFA.
- **Dữ liệu test:** backup artifact.
- **Kết quả mong đợi:** Backup double-encrypted + signed; restore yêu cầu MFA; cross-region replication HCM→SG.
- **Coverage hiện tại:** MISSING (status TODO; ops)

### TC-NFR-064 — Anomaly job phát hiện cross_clinic_access (security / happy path)
- **Function:** NFR-042
- **Loại:** Security
- **Ưu tiên:** P1
- **Layer:** Integration (Arq background job)
- **Tiền điều kiện:** Job 15 phút quét audit với 7 rules.
- **Bước thực hiện:** 1) Tạo mẫu vi phạm (failed_login_burst, mass_pii_reveal, cross_clinic_access, mass_export...). 2) Chạy job.
- **Dữ liệu test:** audit log có pattern bất thường.
- **Kết quả mong đợi:** Job phát hiện đúng rule → alert PD/Slack; có action tương ứng (block IP/tạm khóa quyền/403).
- **Coverage hiện tại:** MISSING (status TODO TASK-002; job chưa có test)

### TC-NFR-065 — Phát hiện audit_tamper_detected (security / negative)
- **Function:** NFR-042
- **Loại:** Security / Negative
- **Ưu tiên:** P0
- **Layer:** Integration
- **Tiền điều kiện:** Hash chain audit (NFR-044) bật.
- **Bước thực hiện:** 1) Sửa thủ công 1 audit row. 2) Chạy anomaly job.
- **Dữ liệu test:** audit row bị sửa.
- **Kết quả mong đợi:** Rule audit_tamper_detected kích hoạt → lockdown clinic + page on-call.
- **Coverage hiện tại:** MISSING

### TC-NFR-066 — Quy trình breach notification ≤ 72h (process)
- **Function:** NFR-043
- **Loại:** Happy path (process)
- **Ưu tiên:** P2
- **Layer:** Manual (drill)
- **Tiền điều kiện:** Process + template email + DPO contact (default VISSoft).
- **Bước thực hiện:** 1) Chạy drill breach. 2) Đo thời gian thông báo.
- **Dữ liệu test:** kịch bản breach giả.
- **Kết quả mong đợi:** Notify Bộ TTTT + affected users trong ≤ 72h; drill annually.
- **Coverage hiện tại:** MISSING (status TODO)

### TC-NFR-067 — Hash chain audit hợp lệ end-to-end (security / happy path)
- **Function:** NFR-044
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Unit / Integration (real DB)
- **Tiền điều kiện:** audit_log dùng `hash = SHA256(prev_hash || row_data)` (TASK-037).
- **Bước thực hiện:** 1) Ghi N audit row. 2) Chạy daily cron verifier toàn chuỗi.
- **Dữ liệu test:** chuỗi N row.
- **Kết quả mong đợi:** Verifier báo chuỗi hợp lệ; mỗi curr_hash khớp công thức.
- **Coverage hiện tại:** MISSING (TASK-037; chưa thấy test hash-chain trong tests hiện tại)

### TC-NFR-068 — Hash chain phát hiện sửa đổi (security / negative)
- **Function:** NFR-044
- **Loại:** Security / Negative
- **Ưu tiên:** P0
- **Layer:** Unit / Integration
- **Tiền điều kiện:** Chuỗi hash đã ghi.
- **Bước thực hiện:** 1) Sửa thủ công 1 row giữa chuỗi. 2) Chạy verifier.
- **Dữ liệu test:** chuỗi 5 row, sửa row 3.
- **Kết quả mong đợi:** Verifier báo chuỗi không hợp lệ tại đúng vị trí bị sửa → break chain detect.
- **Coverage hiện tại:** MISSING

### TC-NFR-069 — Forensic logs preserve 30 ngày + chain of custody (edge)
- **Function:** NFR-044
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Infra/Ops
- **Tiền điều kiện:** Nghi ngờ breach.
- **Bước thực hiện:** 1) Kích hoạt preserve: snapshot DB, lock affected accounts (không xóa), document timeline.
- **Dữ liệu test:** không.
- **Kết quả mong đợi:** Raw logs giữ 30 ngày + chain of custody ghi nhận; account bị lock không bị xóa.
- **Coverage hiện tại:** MISSING

### TC-NFR-070 — Tauri bundle code-sign + notarize (security / happy path)
- **Function:** NFR-045
- **Loại:** Security
- **Ưu tiên:** P1
- **Layer:** Build / Manual
- **Tiền điều kiện:** Pipeline build Tauri ký số (Win EV cert + Mac notarization).
- **Bước thực hiện:** 1) Build bundle Win + Mac. 2) Verify signature + macOS notarization + updater signature.
- **Dữ liệu test:** không.
- **Kết quả mong đợi:** Bundle ký hợp lệ; updater verify signature trước install.
- **Coverage hiện tại:** MISSING (status IN_PROGRESS TASK-016; build/manual)

### TC-NFR-071 — Tauri secure storage mã hóa local (security)
- **Function:** NFR-045
- **Loại:** Security
- **Ưu tiên:** P1
- **Layer:** Integration (Tauri)
- **Tiền điều kiện:** Tauri Store API encrypted (master password derive từ login session).
- **Bước thực hiện:** 1) Lưu token vào secure storage. 2) Đọc file storage thô ở OS.
- **Dữ liệu test:** token.
- **Kết quả mong đợi:** File local ở dạng mã hóa; token không lộ plaintext.
- **Coverage hiện tại:** MISSING

### TC-NFR-072 — Pen test annual + track findings theo SLA (process)
- **Function:** NFR-046
- **Loại:** Security (process)
- **Ưu tiên:** P2
- **Layer:** Manual (3rd-party)
- **Tiền điều kiện:** Hợp đồng pen test hàng năm.
- **Bước thực hiện:** 1) Pen test web + API + Tauri + infra (network, KMS). 2) Track findings + re-test.
- **Dữ liệu test:** không.
- **Kết quả mong đợi:** Findings fix theo SLA: critical ≤ 7d, high ≤ 30d, medium ≤ 90d; report PDF lưu compliance archive.
- **Coverage hiện tại:** MISSING (status TODO v2)

### TC-NFR-073 — RLS giữ vững dưới tải đồng thời đa clinic (cross-cutting / security)
- **Function:** NFR-007 × NFR-003
- **Loại:** Security / Edge
- **Ưu tiên:** P0
- **Layer:** E2E (Locust)
- **Tiền điều kiện:** Nhiều clinic chạy đồng thời.
- **Bước thực hiện:** 1) 10 clinic × 10 user gọi đồng thời. 2) Kiểm không có response lẫn dữ liệu cross-tenant.
- **Dữ liệu test:** 10 clinic.
- **Kết quả mong đợi:** Mỗi user chỉ thấy dữ liệu clinic mình kể cả dưới tải; không leak.
- **Coverage hiện tại:** PARTIAL (RLS đơn-luồng đã COVERED; chưa có test RLS dưới tải concurrent)

### TC-NFR-074 — Cache permission không lẫn tenant (cross-cutting / security)
- **Function:** NFR-007 × RBAC perm cache
- **Loại:** Security / Negative
- **Ưu tiên:** P0
- **Layer:** Integration (real Redis)
- **Tiền điều kiện:** Redis perm cache `user:perms:{uid}:{clinic_id}`.
- **Bước thực hiện:** 1) Cache perm user ở Clinic A. 2) Switch sang Clinic B. 3) Kiểm perm dùng đúng key clinic B.
- **Dữ liệu test:** user multi-clinic.
- **Kết quả mong đợi:** Cache key gắn clinic_id; không dùng nhầm perm clinic A cho B.
- **Coverage hiện tại:** PARTIAL (test_jwt_includes_perms.py + test_require_permission.py phủ perm; cần xác minh key per-clinic khi switch)

### TC-NFR-075 — Truy cập không token bị 401 (cross-cutting / security)
- **Function:** NFR-008 × auth gate
- **Loại:** Security / Negative
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Endpoint protected.
- **Bước thực hiện:** 1) Gọi endpoint không / sai / hết-hạn token.
- **Dữ liệu test:** token rỗng/sai/hết hạn.
- **Kết quả mong đợi:** 401 Unauthorized cho mọi trường hợp; không lộ dữ liệu.
- **Coverage hiện tại:** PARTIAL (test_jwt_signature.py + test_auth_login.py; cần gom case 401 đầy đủ trên endpoint NFR-protected)

### TC-NFR-076 — Sai role bị 403 trên action nhạy cảm (cross-cutting / security)
- **Function:** NFR-008 × RBAC deny precedence
- **Loại:** Security / Negative
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** User role thấp (Receptionist).
- **Bước thực hiện:** 1) Gọi endpoint chỉ Admin (user.manage, config.write).
- **Dữ liệu test:** token role thấp.
- **Kết quả mong đợi:** 403 Forbidden; thao tác không thực hiện; audit ghi nhận.
- **Coverage hiện tại:** COVERED (test_require_permission.py, test_rbac_e2e_real_db.py, test_rbac_extra_perm.py)

### TC-NFR-077 — Rate-limit event sinh log + redact (cross-cutting)
- **Function:** NFR-022 × NFR-030
- **Loại:** Security / Edge
- **Ưu tiên:** P1
- **Layer:** Integration
- **Tiền điều kiện:** Rate limit + structlog bật.
- **Bước thực hiện:** 1) Trigger rate limit login (lockout/burst). 2) Kiểm log warning có IP + UA nhưng KHÔNG full PII.
- **Dữ liệu test:** burst login.
- **Kết quả mong đợi:** Log đủ ngữ cảnh điều tra brute-force; PII bị redact.
- **Coverage hiện tại:** PARTIAL (test_auth_rate_limit + test_auth_lockout_real_db + test_audit_pii_redaction phủ từng phần; chưa có test ghép)

### TC-NFR-078 — Restore từ backup giữ nguyên RLS + hash chain (cross-cutting / reliability)
- **Function:** NFR-011 × NFR-007 × NFR-044
- **Loại:** Edge / Security
- **Ưu tiên:** P1
- **Layer:** Infra/Ops + Integration
- **Tiền điều kiện:** Backup hợp lệ.
- **Bước thực hiện:** 1) Restore backup. 2) Kiểm RLS policy còn bật. 3) Chạy verifier hash chain audit trên DB restore.
- **Dữ liệu test:** backup đầy đủ.
- **Kết quả mong đợi:** RLS hoạt động sau restore; hash chain audit verify hợp lệ (không gãy).
- **Coverage hiện tại:** MISSING

---

## 3. Ghi chú & việc cần làm tiếp (follow-up)

1. **Đã đối chiếu test thật** trong `claude-workspace\tests`: COVERED rõ ràng cho RLS (NFR-007), audit immutable (NFR-009), search perf (NFR-019), rate limit login (NFR-022), PII redaction (NFR-030), 403 RBAC (NFR-076). Khi mở từng file, bổ sung `test_file::test_name` chính xác vào cột Coverage.
2. **NFR-044 (hash chain) thuộc TASK-037** nhưng CHƯA thấy test hash-chain trong tests hiện tại → ưu tiên viết test verifier (TC-067, TC-068) + rule audit_tamper_detected (TC-065).
3. **NFR hạ tầng/vận hành** (TLS NFR-005, TDE NFR-006, backup NFR-011/041, WAF/DDoS/mTLS NFR-034/035/036, KMS NFR-024/025/026, code signing NFR-045, pen test NFR-046, breach NFR-043): kiểm bằng config test / drill / audit thủ công — phối hợp Ops, không phải unit test.
4. **NFR phase v2** (NFR-010, 015, 028, 029, 032, 033, 034, 035, 036, 038, 046): test case hiện là đặc tả kỳ vọng, kích hoạt khi function vào v2.
5. **Bổ sung test còn thiếu ở P0/P1 quan trọng:** API perf chung (NFR-001), bcrypt cost ≥12 assert (NFR-027/TC-045), write/reports rate limit (NFR-022/TC-038), SQL injection chuyên biệt (NFR-008/TC-014), metrics/trace (NFR-018/TC-030).
6. **Ngưỡng SLA chính thức** đã nhúng từ nguồn: p50<200/p95<500/p99<1s (NFR-001), 100k p95<100ms (NFR-019), login 10/min/IP + write 60 + reports 30 (NFR-022), RTO 4h/RPO 24h (NFR-011), bcrypt cost ≥12 (NFR-027), uptime 99.5% (NFR-004).
