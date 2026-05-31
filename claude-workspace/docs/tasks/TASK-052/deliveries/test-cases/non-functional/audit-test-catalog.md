# Test Case Catalog — AUDIT · Nhật ký & Kiểm toán (audit, hash-chain, PII redaction)

**Nguồn:** function_list_data.py (group AUDIT, AUDIT-001..AUDIT-015) + clinic_management_function_list.md (mục 18) + system_design/SaaS + code & test thực tế trong `clinic-cms-merge`.
**Phạm vi:** 15 functions.  **Tổng test case:** 40.  **Ngày:** 2026-05-30.

> Ghi chú nguồn & phương pháp gán coverage:
> - Danh sách function + brief + detail + role + phase + task + status lấy nguyên văn từ `scripts/function_list_data.py` group "AUDIT" (dòng 1326–1385) và `docs/clinic_management_function_list.md` mục **18. AUDIT — Audit log & Compliance** (dòng 461–475). Dòng tổng kết (726): `AUDIT | 11 | 7 | 4`.
> - Quy ước status nguồn: DONE (✅), TODO (⬜ — có task chưa làm theo .md), IDEA (💡 — v2). LƯU Ý: bản code merge (`clinic-cms-merge`) đã triển khai VƯỢT cột status trong .md — nhiều function ⬜/💡 thực tế ĐÃ CÓ code + test (viewer AUDIT-008, patient.read AUDIT-007, erasure AUDIT-013, hash-chain immutability). Coverage dưới đây phản ánh **code/test thực tế đã đối chiếu**, không chỉ theo .md.
> - `clinic_management_system_design.md` / `clinic_management_business_analysis.md` tại thời điểm soạn là placeholder (44/60 bytes); rule lấy từ cột `detail` + docstring code.
> - **Code đã xác minh:** `app/core/audit.py` — `_ALWAYS_REDACT = {password_hash, password, token, secret, jwt_secret, refresh_token, refresh_token_hash, mfa_secret, access_token}` → thay `***`; listener SQLAlchemy `after_flush` ghi INSERT/UPDATE/DELETE đồng bộ trong cùng transaction (atomic, không dùng `asyncio.create_task`); context qua ContextVar `current_clinic_id`/`current_user_id`/`current_request_id`/`current_applied_role`; `_compute_diff` cho changed_fields; `_serialize_value` xử lý UUID/Decimal(→str giữ precision)/datetime; `_model_to_dict` áp dụng `__audit_exclude__`; `write_audit`/`audit_read` ghi trực tiếp; audit failure KHÔNG re-raise (không block business tx).
> - **Test đã đối chiếu (thực, có assertion):** unit `test_audit_writer.py` (10), `test_audit_event_listener.py` (4), `test_audit_coverage.py` (5), `test_audit_applied_role.py` (2), `test_tenancy_middleware.py` (4), `test_erasure_service.py` (3); integration `test_audit_lifecycle.py` (3), `test_audit_pii_redaction.py` (2), `test_audit_decimal.py` (2), `test_audit_immutable.py` (2 — UPDATE/DELETE bị trigger chặn), `test_audit_list_endpoint.py` (4 — AUDIT-008), `patients/test_patients_audit.py` (3 — AUDIT-007 patient.read), `test_erasure_endpoint.py` (4 — AUDIT-013), `test_audit_chain_endpoint.py` (3 — verify-chain), `test_audit_chain_trigger.py` (3 — prev_hash linkage), `test_audit_rls.py`/`test_rls_isolation.py`/`test_tenant_isolation_full.py`/`test_rls_admin_bypass.py` (RLS isolation, có assertion đầy đủ).

---

## 1. Ma trận truy vết (Function → Test Cases → Coverage)

| Function | Tên chức năng | Status (nguồn) | Test Case IDs | Coverage |
|---|---|---|---|---|
| AUDIT-001 | Audit mọi INSERT/UPDATE/DELETE (after_flush listener) | DONE (TASK-002) | TC-AUDIT-001, TC-AUDIT-002, TC-AUDIT-003 | COVERED |
| AUDIT-002 | PII redaction (_ALWAYS_REDACT → ***) | DONE (TASK-002) | TC-AUDIT-004, TC-AUDIT-005, TC-AUDIT-006 | COVERED |
| AUDIT-003 | `__auditable__` flag (opt-in per model) | DONE (TASK-002) | TC-AUDIT-007, TC-AUDIT-008 | COVERED |
| AUDIT-004 | `__audit_exclude__` (exclude sensitive fields) | DONE (TASK-002) | TC-AUDIT-009, TC-AUDIT-010 | COVERED |
| AUDIT-005 | RLS row-level security (per clinic_id auto-filter) | DONE (TASK-002) | TC-AUDIT-011, TC-AUDIT-012, TC-AUDIT-013 | COVERED |
| AUDIT-006 | Tenancy middleware (set app.current_clinic_id) | DONE (TASK-002) | TC-AUDIT-014, TC-AUDIT-015, TC-AUDIT-016 | COVERED |
| AUDIT-007 | Audit patient.read (đọc PHI ghi log riêng) | DONE (TASK-005) | TC-AUDIT-017, TC-AUDIT-018, TC-AUDIT-019 | COVERED |
| AUDIT-008 | Audit log viewer (clinic) | TODO (.md) / IMPLEMENTED (code) | TC-AUDIT-020, TC-AUDIT-021, TC-AUDIT-022, TC-AUDIT-023 | COVERED |
| AUDIT-009 | Audit log viewer (super admin) — cross-clinic forensic | TODO (TASK-030) | TC-AUDIT-024, TC-AUDIT-025, TC-AUDIT-026 | MISSING |
| AUDIT-010 | Data export PDPA (right to portability) | TODO (TASK-015) | TC-AUDIT-027, TC-AUDIT-028, TC-AUDIT-029 | MISSING |
| AUDIT-011 | ToS + Privacy versioning | TODO (TASK-006) | TC-AUDIT-030, TC-AUDIT-031 | MISSING |
| AUDIT-012 | Consent tracking (BN ký digital consent) | IDEA (v2) | TC-AUDIT-032, TC-AUDIT-033 | MISSING |
| AUDIT-013 | Right to be forgotten (PDPA Art 17) | IDEA (.md) / IMPLEMENTED (code) | TC-AUDIT-034, TC-AUDIT-035, TC-AUDIT-036 | COVERED |
| AUDIT-014 | DPA template (Data Processing Agreement) | TODO (TASK-029) | TC-AUDIT-037, TC-AUDIT-038 | MISSING |
| AUDIT-015 | Cookie consent banner (GDPR landing) | TODO (TASK-029) | TC-AUDIT-039, TC-AUDIT-040 | MISSING |

**Tổng kết coverage (15 function):** COVERED = 9 (AUDIT-001..008 + AUDIT-013), PARTIAL = 0, MISSING = 6 (AUDIT-009, 010, 011, 012, 014, 015 — chưa triển khai trong bản merge).

**Bonus (ngoài 15 function nguồn):** code merge còn có **hash-chain integrity** cho audit_log — trigger immutability (UPDATE/DELETE bị chặn: `test_audit_immutable.py`), prev_hash linkage (`test_audit_chain_trigger.py`), endpoint `GET /audit/verify-chain` phát hiện tamper (`test_audit_chain_endpoint.py`). Đây là phần nhãn group đề cập ("hash-chain") nhưng KHÔNG có function code riêng trong AUDIT-001..015; được kiểm thử như tăng cường cho AUDIT-001/005 — xem ghi chú ở TC-AUDIT-003.

---

## 2. Chi tiết Test Cases

### TC-AUDIT-001 — Ghi audit log tự động cho INSERT/UPDATE/DELETE (atomic trong tx)
- **Function:** AUDIT-001
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB) + Unit
- **Tiền điều kiện:** ContextVar clinic_id/user_id set; model `__auditable__=True`.
- **Bước thực hiện:** 1) INSERT 1 record. 2) UPDATE record. 3) DELETE record. 4) Truy vấn `audit_log`.
- **Dữ liệu test:** 1 record auditable mẫu.
- **Kết quả mong đợi:** 3 dòng audit (action INSERT/UPDATE/DELETE), clinic_id/user_id/request_id từ context, entity_type/entity_id, old_data/new_data JSONB, changed_fields; ghi đồng bộ trong cùng transaction (rollback business → rollback audit).
- **Coverage hiện tại:** COVERED — `tests/integration/test_audit_lifecycle.py::test_insert_creates_audit_row / test_update_creates_audit_row / test_delete_creates_audit_row`; unit `test_audit_event_listener.py::test_listener_captures_insert / test_listener_captures_update`.

### TC-AUDIT-002 — UPDATE chỉ ghi field thay đổi (_compute_diff / changed_fields)
- **Function:** AUDIT-001
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Unit
- **Tiền điều kiện:** Record tồn tại.
- **Bước thực hiện:** 1) Tính diff old/new. 2) Kiểm tra changed_fields.
- **Dữ liệu test:** old/new khác 1 field.
- **Kết quả mong đợi:** Chỉ field thực đổi xuất hiện; None→None bị strip; trùng giá trị không tính.
- **Coverage hiện tại:** COVERED — `test_audit_writer.py::test_compute_diff_detects_changes / test_compute_diff_no_changes`; `test_audit_coverage.py::test_compute_diff_added_removed_keys`.

### TC-AUDIT-003 — Audit log bất biến (immutability) + hash-chain prev_hash (chống tamper)
- **Function:** AUDIT-001
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Có audit row đã ghi.
- **Bước thực hiện:** 1) Thử UPDATE audit_log. 2) Thử DELETE audit_log. 3) Kiểm tra prev_hash linkage qua nhiều row. 4) Sửa lén 1 row → verify-chain.
- **Dữ liệu test:** Chuỗi audit row.
- **Kết quả mong đợi:** UPDATE/DELETE bị DB trigger chặn; row đầu prev_hash NULL; row sau link prev_hash; phát hiện chain break khi tamper.
- **Coverage hiện tại:** COVERED — `test_audit_immutable.py::test_audit_log_update_blocked / test_audit_log_delete_blocked`; `test_audit_chain_trigger.py::test_audit_chain_links_prev_hash / test_audit_chain_first_row_null_prev / test_audit_chain_detects_break`; endpoint `test_audit_chain_endpoint.py::test_verify_chain_detects_tampering`.

### TC-AUDIT-004 — PII redaction: field nhạy cảm → `***`
- **Function:** AUDIT-002
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Unit + Integration
- **Tiền điều kiện:** Dict chứa key trong `_ALWAYS_REDACT`.
- **Bước thực hiện:** 1) Redact dict có password_hash/mfa_secret/token/jwt_secret/refresh_token_hash/access_token... 2) Integration: tạo User có password_hash → đọc audit.
- **Dữ liệu test:** `{"password_hash":"x","mfa_secret":"y","name":"A"}`.
- **Kết quả mong đợi:** Mọi key always-redact thành `***`; key thường giữ nguyên; trong DB audit không lưu plaintext secret.
- **Coverage hiện tại:** COVERED — unit `test_audit_writer.py::test_redact_always_redact_fields`; integration `test_audit_pii_redaction.py::test_password_hash_redacted_in_audit / test_mfa_secret_redacted`.

### TC-AUDIT-005 — Redact nested + serialize JSON-safe (UUID/Decimal/datetime)
- **Function:** AUDIT-002
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Unit + Integration
- **Tiền điều kiện:** Dict lồng / giá trị non-JSON.
- **Bước thực hiện:** 1) Redact nested structure. 2) Serialize UUID/Decimal/datetime. 3) Integration: Decimal trong NUMERIC column → audit.
- **Dữ liệu test:** Decimal "150000.00", UUID, datetime, dict lồng.
- **Kết quả mong đợi:** Decimal→str giữ precision, UUID→str, datetime→isoformat; nested redact đúng; JSONB không lỗi serialize.
- **Coverage hiện tại:** COVERED — `test_audit_writer.py::test_serialize_value_uuid / test_serialize_value_decimal_preserves_precision / test_serialize_value_datetime`; `test_audit_coverage.py::test_redact_nested_structures / test_serialize_value_handles_list`; integration `test_audit_decimal.py::test_decimal_serialized_as_string / test_decimal_in_nested_dict`.

### TC-AUDIT-006 — Audit ghi đúng context (clinic/user/request/applied_role) & không block khi lỗi
- **Function:** AUDIT-002
- **Loại:** Happy path + Negative
- **Ưu tiên:** P1
- **Layer:** Unit
- **Tiền điều kiện:** ContextVar set / chưa set.
- **Bước thực hiện:** 1) `write_audit` khi context đầy đủ. 2) Khi context thiếu. 3) applied_role set/không set.
- **Dữ liệu test:** Các trạng thái context.
- **Kết quả mong đợi:** Khi đủ context → ghi đúng clinic/user/request/applied_role; thiếu context → vẫn ghi (None) không crash; applied_role NULL khi chưa set.
- **Coverage hiện tại:** COVERED — `test_audit_writer.py::test_write_audit_pulls_context_vars / test_write_audit_handles_missing_context`; `test_audit_applied_role.py::test_applied_role_captured_in_audit / test_applied_role_null_when_not_set`.

### TC-AUDIT-007 — Chỉ model `__auditable__=True` mới ghi audit
- **Function:** AUDIT-003
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Unit
- **Tiền điều kiện:** 1 model auditable, 1 model không.
- **Bước thực hiện:** 1) Thao tác cả hai model qua listener.
- **Dữ liệu test:** 2 model.
- **Kết quả mong đợi:** Chỉ model auditable sinh audit row; model còn lại bị skip.
- **Coverage hiện tại:** COVERED — `test_audit_event_listener.py::test_listener_skips_non_auditable` (và `::test_listener_captures_insert`).

### TC-AUDIT-008 — Redact áp dụng cả ở event listener (UPDATE giữ secret = ***)
- **Function:** AUDIT-003
- **Loại:** Security
- **Ưu tiên:** P1
- **Layer:** Unit
- **Tiền điều kiện:** Model auditable có field nhạy cảm.
- **Bước thực hiện:** 1) UPDATE field nhạy cảm → listener redact old & new.
- **Dữ liệu test:** Đổi password_hash.
- **Kết quả mong đợi:** old_data/new_data của field excluded đều `***`.
- **Coverage hiện tại:** COVERED — `test_audit_event_listener.py::test_listener_redacts_on_event`.

### TC-AUDIT-009 — `__audit_exclude__` loại field nhạy cảm khỏi audit (model-level)
- **Function:** AUDIT-004
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Unit
- **Tiền điều kiện:** Model khai báo `__audit_exclude__`.
- **Bước thực hiện:** 1) `_model_to_dict` snapshot model có exclude.
- **Dữ liệu test:** Model với field excluded + thường.
- **Kết quả mong đợi:** Field excluded → `***` (giữ cấu trúc, ẩn giá trị); field thường serialize bình thường.
- **Coverage hiện tại:** COVERED — `test_audit_writer.py::test_redact_model_exclude_fields / test_model_to_dict_redacts_excluded`.

### TC-AUDIT-010 — `_model_to_dict` xử lý model rỗng / không có exclude
- **Function:** AUDIT-004
- **Loại:** Negative
- **Ưu tiên:** P2
- **Layer:** Unit
- **Tiền điều kiện:** Model không khai báo `__audit_exclude__`.
- **Bước thực hiện:** 1) Snapshot model rỗng/không exclude.
- **Dữ liệu test:** Model tối thiểu.
- **Kết quả mong đợi:** Chỉ `_ALWAYS_REDACT` áp dụng; cột SKIP (created_at/updated_at/version/is_deleted...) bị loại; không lỗi.
- **Coverage hiện tại:** COVERED — `test_audit_coverage.py::test_model_to_dict_handles_empty`.

### TC-AUDIT-011 — RLS: clinic chỉ thấy audit/dữ liệu của mình (restricted role)
- **Function:** AUDIT-005
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB, role cms_app non-superuser)
- **Tiền điều kiện:** 2 clinic có audit row; SET LOCAL app.current_clinic_id.
- **Bước thực hiện:** 1) Set clinic A → SELECT. 2) Set clinic B → SELECT.
- **Dữ liệu test:** 1 row mỗi clinic.
- **Kết quả mong đợi:** Mỗi clinic chỉ thấy row của mình; row clinic khác bị ẩn (kiểm tqua role hạn chế vì cms là superuser BYPASSRLS).
- **Coverage hiện tại:** COVERED — `test_audit_rls.py::TestRLSIsolation::test_clinic_a_sees_only_own_rows / test_clinic_b_sees_only_own_rows`; `test_tenant_isolation_full.py::test_patient_isolation_between_clinics / test_visit_isolation_between_clinics / test_audit_isolation_between_clinics`.

### TC-AUDIT-012 — RLS NULL clinic_id (system event) hiển thị cho mọi clinic + admin bypass
- **Function:** AUDIT-005
- **Loại:** Edge + Security
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Row clinic_id NULL; role superuser vs restricted.
- **Bước thực hiện:** 1) Query row NULL clinic dưới context bất kỳ. 2) Kiểm tra superuser bypass RLS, restricted role enforce.
- **Dữ liệu test:** Row READ/System clinic_id NULL.
- **Kết quả mong đợi:** Row NULL clinic visible cho mọi clinic; superuser thấy tất cả; restricted role bị giới hạn.
- **Coverage hiện tại:** COVERED — `test_audit_rls.py::test_null_clinic_id_row_visible_to_all`; `test_rls_admin_bypass.py::test_superuser_bypasses_rls / test_restricted_role_enforces_rls`.

### TC-AUDIT-013 — RLS cô lập patient/visit cross-clinic (block cross-tenant)
- **Function:** AUDIT-005
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Patient/visit thuộc nhiều clinic.
- **Bước thực hiện:** 1) Set clinic A → query patient/visit. 2) Cố truy cập của clinic B.
- **Dữ liệu test:** Dữ liệu domain nhiều clinic.
- **Kết quả mong đợi:** Chỉ thấy dữ liệu clinic hiện tại; không rò rỉ chéo.
- **Coverage hiện tại:** COVERED — `test_rls_isolation.py`; `visits/test_visits_rls.py`; `patients/test_rls_isolation_cms_app_role.py`.

### TC-AUDIT-014 — Tenancy middleware set/clear clinic context theo request
- **Function:** AUDIT-006
- **Loại:** Happy path + Edge
- **Ưu tiên:** P0
- **Layer:** Unit / Integration
- **Tiền điều kiện:** Request authenticated có clinic_id.
- **Bước thực hiện:** 1) Request có token → middleware set context. 2) Sau request → context clear (không leak).
- **Dữ liệu test:** Token C1 rồi request kế tiếp.
- **Kết quả mong đợi:** Context set đúng clinic_id trong scope request; clear/reset sau request (không kế thừa qua pool).
- **Coverage hiện tại:** COVERED — `test_tenancy_middleware.py::test_middleware_sets_clinic_context / test_middleware_clears_context_after_request`.

### TC-AUDIT-015 — Request không token / token sai → không set context, 401
- **Function:** AUDIT-006
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Unit / E2E
- **Tiền điều kiện:** Endpoint yêu cầu auth.
- **Bước thực hiện:** 1) Không token. 2) Token sai.
- **Dữ liệu test:** Không token / token hỏng.
- **Kết quả mong đợi:** Không set context; token sai → 401.
- **Coverage hiện tại:** COVERED — `test_tenancy_middleware.py::test_middleware_no_token_no_context / test_middleware_invalid_token_401`.

### TC-AUDIT-016 — Context không leak qua connection pool (tái dùng connection)
- **Function:** AUDIT-006
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Integration
- **Tiền điều kiện:** Pool tái dùng connection.
- **Bước thực hiện:** 1) Request C1. 2) Request C2 dùng lại connection.
- **Dữ liệu test:** Hai request khác clinic liên tiếp.
- **Kết quả mong đợi:** C2 không kế thừa context C1 (đã clear cuối request).
- **Coverage hiện tại:** COVERED — đảm bảo bởi `test_middleware_clears_context_after_request` kết hợp RLS isolation tests (gián tiếp); khuyến nghị thêm 1 test connection-reuse tường minh.

### TC-AUDIT-017 — Đọc PHI bệnh nhân sinh audit READ riêng (patient.read)
- **Function:** AUDIT-007
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** User có quyền đọc PHI; BN tồn tại.
- **Bước thực hiện:** 1) GET `/patients/:id`. 2) Đọc audit_log.
- **Dữ liệu test:** 1 BN.
- **Kết quả mong đợi:** Sinh audit action READ với user context (who/when/patient_id); không chứa old/new_data.
- **Coverage hiện tại:** COVERED — `patients/test_patients_audit.py::test_get_patient_creates_read_audit / test_read_audit_includes_user_context`.

### TC-AUDIT-018 — LIST patients KHÔNG sinh read-audit hàng loạt (chỉ GET detail)
- **Function:** AUDIT-007
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Integration
- **Tiền điều kiện:** Nhiều BN.
- **Bước thực hiện:** 1) GET list patients. 2) Kiểm tra audit.
- **Dữ liệu test:** Danh sách BN.
- **Kết quả mong đợi:** Không tạo audit READ cho thao tác list (chỉ detail mới ghi).
- **Coverage hiện tại:** COVERED — `patients/test_patients_audit.py::test_list_patients_no_read_audit`.

### TC-AUDIT-019 — Đọc PHI thiếu quyền/khác clinic → 403/404, không lộ PHI
- **Function:** AUDIT-007
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** User thiếu quyền PHI; BN thuộc clinic khác.
- **Bước thực hiện:** 1) GET PHI thiếu quyền → 403. 2) GET BN clinic khác → 404 (RLS che).
- **Dữ liệu test:** Token thiếu quyền / patient_id clinic khác.
- **Kết quả mong đợi:** 403/404; không trả PHI; không audit read trái phép.
- **Coverage hiện tại:** PARTIAL → đánh COVERED ở mức function (RBAC `require_permission` được kiểm thử ở `test_require_permission.py`; RLS che ở các RLS tests). Khuyến nghị thêm 1 E2E ghép 403+404 cho patient detail (cần xác minh test file riêng).

### TC-AUDIT-020 — GET /audit trả audit của clinic hiện tại (viewer)
- **Function:** AUDIT-008
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** User authenticated clinic C1; có audit data.
- **Bước thực hiện:** 1) GET `/audit`.
- **Dữ liệu test:** Audit row của C1.
- **Kết quả mong đợi:** Trả danh sách audit của C1.
- **Coverage hiện tại:** COVERED — `test_audit_list_endpoint.py::test_list_audit_returns_clinic_rows`.

### TC-AUDIT-021 — GET /audit yêu cầu auth (401)
- **Function:** AUDIT-008
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Request không token.
- **Bước thực hiện:** 1) GET `/audit` không token.
- **Dữ liệu test:** Không token.
- **Kết quả mong đợi:** 401 Unauthorized.
- **Coverage hiện tại:** COVERED — `test_audit_list_endpoint.py::test_list_audit_requires_auth`.

### TC-AUDIT-022 — GET /audit filter theo action
- **Function:** AUDIT-008
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Audit nhiều action.
- **Bước thực hiện:** 1) GET `/audit?action=INSERT`.
- **Dữ liệu test:** Mix action.
- **Kết quả mong đợi:** Chỉ trả audit khớp action.
- **Coverage hiện tại:** COVERED — `test_audit_list_endpoint.py::test_list_audit_filters_by_action`.

### TC-AUDIT-023 — GET /audit phân trang
- **Function:** AUDIT-008
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Nhiều audit row.
- **Bước thực hiện:** 1) GET `/audit?page=...&page_size=...`.
- **Dữ liệu test:** > page_size rows.
- **Kết quả mong đợi:** Pagination đúng (limit/offset, total).
- **Coverage hiện tại:** COVERED — `test_audit_list_endpoint.py::test_list_audit_pagination`.

### TC-AUDIT-024 — Super admin xem audit cross-clinic (forensic)
- **Function:** AUDIT-009
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Super admin có `platform.audit.read`; audit nhiều clinic.
- **Bước thực hiện:** 1) GET `/admin/system/audit` search across clinics.
- **Dữ liệu test:** Audit C1/C2/C3.
- **Kết quả mong đợi:** Trả audit tất cả clinic kèm clinic_id; filter theo clinic.
- **Coverage hiện tại:** MISSING — status ⬜ TODO (TASK-030), không thấy endpoint super-admin viewer trong bản merge → cần xác minh test file.

### TC-AUDIT-025 — Chỉ super admin truy cập cross-clinic viewer (401/403)
- **Function:** AUDIT-009
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Clinic admin (không có `platform.audit.read`); không token.
- **Bước thực hiện:** 1) Không token → 401. 2) Clinic admin → 403.
- **Dữ liệu test:** Token clinic admin / không token.
- **Kết quả mong đợi:** 401/403; clinic admin không xem cross-clinic.
- **Coverage hiện tại:** MISSING — chưa triển khai.

### TC-AUDIT-026 — Forensic filter actor/clinic/khoảng thời gian
- **Function:** AUDIT-009
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Super admin; audit đa dạng.
- **Bước thực hiện:** 1) Filter clinic_id + actor + date range.
- **Dữ liệu test:** Audit nhiều clinic/actor.
- **Kết quả mong đợi:** Khớp tất cả điều kiện; pagination đúng.
- **Coverage hiện tại:** MISSING — chưa triển khai.

### TC-AUDIT-027 — Export toàn bộ dữ liệu BN (PDPA portability, ZIP)
- **Function:** AUDIT-010
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Admin C1; BN có hồ sơ/visits/Rx/invoices/documents.
- **Bước thực hiện:** 1) GET `/patients/:id/export`.
- **Dữ liệu test:** BN đầy đủ dữ liệu.
- **Kết quả mong đợi:** ZIP gồm JSON profile + CSV visits/Rx/invoices + folder documents; sinh audit `export`.
- **Coverage hiện tại:** MISSING — status ⬜ TODO (TASK-015), không thấy endpoint export ZIP trong merge → cần xác minh test file.

### TC-AUDIT-028 — Export yêu cầu quyền & ghi audit (401/403 + audit row)
- **Function:** AUDIT-010
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** User thường không quyền export; không token.
- **Bước thực hiện:** 1) Không token → 401. 2) User thường → 403. 3) Admin → audit `export`.
- **Dữ liệu test:** Token thường / không token / admin.
- **Kết quả mong đợi:** 401/403; export hợp lệ tạo audit row.
- **Coverage hiện tại:** MISSING — chưa triển khai.

### TC-AUDIT-029 — Export cô lập tenant (không export BN clinic khác)
- **Function:** AUDIT-010
- **Loại:** Security
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Admin C1; BN thuộc C2.
- **Bước thực hiện:** 1) Admin C1 export patient_id của C2.
- **Dữ liệu test:** patient_id C2.
- **Kết quả mong đợi:** 404/403; không export dữ liệu clinic khác.
- **Coverage hiện tại:** MISSING — chưa triển khai.

### TC-AUDIT-030 — Lưu phiên bản ToS/Privacy khách đồng ý
- **Function:** AUDIT-011
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration / E2E
- **Tiền điều kiện:** Có tos_version hiện hành.
- **Bước thực hiện:** 1) User đồng ý. 2) Đọc `user.accepted_tos_version`.
- **Dữ liệu test:** version="1.2".
- **Kết quả mong đợi:** Ghi version, user_id, timestamp.
- **Coverage hiện tại:** MISSING — status ⬜ TODO (TASK-006), chưa triển khai.

### TC-AUDIT-031 — Đổi ToS version → yêu cầu đồng ý lại
- **Function:** AUDIT-011
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** E2E
- **Tiền điều kiện:** Đã đồng ý v1.2; nâng v1.3.
- **Bước thực hiện:** 1) Đăng nhập sau khi version đổi.
- **Dữ liệu test:** version cũ vs mới.
- **Kết quả mong đợi:** Chặn tiếp tục, yêu cầu accept lại; lưu bản ghi mới.
- **Coverage hiện tại:** MISSING — chưa triển khai.

### TC-AUDIT-032 — Ghi nhận BN ký digital consent (signature + timestamp + IP)
- **Function:** AUDIT-012
- **Loại:** Happy path
- **Ưu tiên:** P2
- **Layer:** Integration
- **Tiền điều kiện:** BN đăng ký lần đầu.
- **Bước thực hiện:** 1) BN ký consent. 2) Đọc bản ghi.
- **Dữ liệu test:** signature image + IP.
- **Kết quả mong đợi:** Lưu signature, timestamp, IP, patient_id.
- **Coverage hiện tại:** MISSING — status 💡 IDEA (v2), chưa triển khai.

### TC-AUDIT-033 — Thu hồi consent (withdraw)
- **Function:** AUDIT-012
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Integration
- **Tiền điều kiện:** Có consent active.
- **Bước thực hiện:** 1) Thu hồi consent.
- **Dữ liệu test:** consent active.
- **Kết quả mong đợi:** Trạng thái revoked + revoked_at; dừng xử lý dữ liệu.
- **Coverage hiện tại:** MISSING — v2, chưa triển khai.

### TC-AUDIT-034 — Right to be forgotten: anonymize PII BN, GIỮ audit trail
- **Function:** AUDIT-013
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration / E2E + Unit
- **Tiền điều kiện:** Admin có quyền; BN có dữ liệu.
- **Bước thực hiện:** 1) POST `/patients/:id/erasure`. 2) Kiểm tra PII bị anonymize. 3) Kiểm tra audit_log vẫn còn (PDPA Art 17).
- **Dữ liệu test:** BN có PII + non-PII.
- **Kết quả mong đợi:** Field PII bị thay/anonymize; field non-PII giữ; **audit row của hành động xoá vẫn được giữ** (không tự xoá dấu vết).
- **Coverage hiện tại:** COVERED — integration `test_erasure_endpoint.py::test_erasure_anonymizes_patient / test_erasure_keeps_audit_trail`; unit `test_erasure_service.py::test_anonymize_fields_replaces_pii / test_anonymize_preserves_non_pii / test_erasure_keeps_audit_row`.

### TC-AUDIT-035 — Erasure yêu cầu auth + quyền (401/403)
- **Function:** AUDIT-013
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Không token; user thiếu quyền erasure.
- **Bước thực hiện:** 1) Không token → 401. 2) User thiếu quyền → 403.
- **Dữ liệu test:** Không token / token thiếu quyền.
- **Kết quả mong đợi:** 401 và 403 tương ứng.
- **Coverage hiện tại:** COVERED — `test_erasure_endpoint.py::test_erasure_requires_auth / test_erasure_requires_permission`.

### TC-AUDIT-036 — Erasure cô lập trong clinic (không xoá BN clinic khác)
- **Function:** AUDIT-013
- **Loại:** Security
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Admin C1; patient của C2.
- **Bước thực hiện:** 1) Admin C1 erasure patient C2.
- **Dữ liệu test:** patient_id C2.
- **Kết quả mong đợi:** 404/403 (RLS che); không xoá dữ liệu tenant khác.
- **Coverage hiện tại:** PARTIAL — erasure flow đã COVERED nhưng case cross-tenant cụ thể chưa thấy test riêng → cần xác minh/ bổ sung test file.

### TC-AUDIT-037 — Sinh DPA template với info clinic (PDF)
- **Function:** AUDIT-014
- **Loại:** Happy path
- **Ưu tiên:** P2
- **Layer:** Integration
- **Tiền điều kiện:** Clinic có thông tin pháp lý.
- **Bước thực hiện:** 1) Sinh DPA `/legal/dpa`.
- **Dữ liệu test:** Thông tin clinic mẫu.
- **Kết quả mong đợi:** PDF DPA điền đúng tên clinic, ngày, điều khoản PDPA+GDPR; tải về.
- **Coverage hiện tại:** MISSING — status ⬜ TODO (TASK-029), chưa triển khai.

### TC-AUDIT-038 — Truy cập DPA yêu cầu quyền (401/403)
- **Function:** AUDIT-014
- **Loại:** Security
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** User không quyền; không token.
- **Bước thực hiện:** 1) Không token → 401. 2) Thiếu quyền → 403.
- **Dữ liệu test:** Token thường / không token.
- **Kết quả mong đợi:** 401/403 tương ứng.
- **Coverage hiện tại:** MISSING — chưa triển khai.

### TC-AUDIT-039 — Hiển thị cookie consent banner trên landing (3 option)
- **Function:** AUDIT-015
- **Loại:** Happy path
- **Ưu tiên:** P2
- **Layer:** Manual/UI (E2E browser)
- **Tiền điều kiện:** Landing lần đầu (localStorage trống).
- **Bước thực hiện:** 1) Mở landing. 2) Xem banner All/Essential/Customize. 3) Bấm All.
- **Dữ liệu test:** Trình duyệt sạch localStorage.
- **Kết quả mong đợi:** Banner hiển thị; lưu choice localStorage; không hiện lại lần sau.
- **Coverage hiện tại:** MISSING — status ⬜ TODO (TASK-029), chưa triển khai.

### TC-AUDIT-040 — Chọn Essential → không set cookie không cần thiết
- **Function:** AUDIT-015
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Manual/UI (E2E browser)
- **Tiền điều kiện:** Banner đang hiển thị.
- **Bước thực hiện:** 1) Bấm "Essential".
- **Dữ liệu test:** Lựa chọn essential.
- **Kết quả mong đợi:** Chỉ set cookie cần thiết; không analytics/marketing (GDPR cho EU).
- **Coverage hiện tại:** MISSING — chưa triển khai.

---

## 3. Khuyến nghị bổ sung kiểm thử (gap chính)

1. **AUDIT-009 (super admin cross-clinic viewer):** chưa có endpoint/test trong bản merge — ưu tiên P0 case 401/403 + forensic filter khi TASK-030 triển khai (TC-AUDIT-024/025/026).
2. **AUDIT-010 (PDPA export ZIP):** chưa triển khai — cần test cô lập tenant + quyền + ghi audit `export` (TC-AUDIT-027/028/029).
3. **AUDIT-011/012 (ToS versioning, consent tracking):** test luồng accept lại khi đổi version + thu hồi consent.
4. **AUDIT-014/015 (DPA, cookie banner):** test UI Playwright + quyền truy cập.
5. **Bổ sung case còn thiếu của function đã COVERED:**
   - TC-AUDIT-016: thêm test connection-reuse tường minh để chứng minh context không leak qua pool.
   - TC-AUDIT-019: thêm E2E ghép 403 (thiếu quyền) + 404 (cross-clinic) cho GET patient detail.
   - TC-AUDIT-036: thêm test erasure cross-tenant (admin C1 cố erasure BN C2).
6. **Điểm mạnh đáng ghi nhận:** group AUDIT có độ phủ cao bất thường nhờ tính chất security-critical — bản merge đã có **hash-chain integrity** (immutability trigger + prev_hash linkage + verify-chain endpoint, vượt 15 function nguồn), audit viewer (AUDIT-008), patient.read (AUDIT-007), và erasure/right-to-be-forgotten (AUDIT-013) — tất cả đều có test thực với assertion. Status ⬜/💡 trong `clinic_management_function_list.md` đã lỗi thời so với code merge; nên cập nhật lại .md.
