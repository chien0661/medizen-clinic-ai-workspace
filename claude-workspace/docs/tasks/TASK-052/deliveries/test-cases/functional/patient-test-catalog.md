# Test Case Catalog — PATIENT · Quản lý Bệnh nhân

**Nguồn:** function_list_data.py (group PATIENT, banner "5. PATIENT — Quản lý bệnh nhân (DONE TASK-005)") + clinic_management_function_list.md (mục 5) + system_design/BA + **đối chiếu code thực tế** `clinic-cms-merge/app/modules/patients/` và **test thật** `clinic-cms-merge/tests/{integration,unit}/patients/`.
**Phạm vi:** 22 functions (PAT-001 … PAT-022).  **Tổng test case:** 64.  **Ngày:** 2026-05-30.

> **Trạng thái nguồn (chuẩn 100%):** 20/22 function thuộc TASK-005: **19 ✅ DONE** + **1 ⬜ TODO** (PAT-019 "Đính kèm tài liệu" — storage S3 chưa wire). 2 function còn lại **💡 IDEA / v2**: PAT-021 (Export PDF), PAT-022 (Bulk import CSV).
>
> **API & permission thực tế** (đã xác minh từ `app/modules/patients/api/routes.py`):
> - GET `/patients` (list, `patient.read`), GET `/patients/search?q=&type=phone|name|code|all` (`patient.read`), GET `/patients/{id}` (`patient.read`)
> - POST `/patients` (201, `patient.write`), PATCH `/patients/{id}` (`patient.write`), DELETE `/patients/{id}` (204, `patient.delete`)
> - POST `/patients/{id}/guardians` (`patient.write`), GET `/patients/{id}/guardians` (`patient.read`), DELETE `/patients/guardians/{relation_id}` (`patient.write`)
> - POST `/patients/merge` (`patient.merge`), POST `/patients/merge/{merge_id}/undo` (`patient.merge`)
> - Erasure (GDPR/NĐ13): POST + DELETE under `api/erasure_routes.py` (`patient.erase`)
>
> **LƯU Ý quan trọng:** permission thật là `patient.read` / `patient.write` / `patient.delete` / `patient.merge` / `patient.erase` — KHÔNG có `patient.create` / `patient.update` / `patient.dob.edit` (các tên này trong BA chỉ là gợi ý, code gộp create+update vào `patient.write`).
>
> **Bộ test thật đã đối chiếu** (theo tên hàm thực tế):
> - `tests/integration/patients/test_patients_api.py` (E2E CRUD/search/guardian/merge/undo/audit/tenant)
> - `tests/integration/patients/test_patients_negative.py` (negative: validate, merge edge, undo 404/409/410, cross-clinic)
> - `tests/integration/patients/test_patients_audit.py` (audit read 1:1, multi-read, entity_id, PII redaction)
> - `tests/integration/patients/test_patients_merge_advanced.py` (concurrent merge, deadline boundary, undo-again)
> - `tests/integration/patients/test_patients_perf.py` (perf p95 100k, fuzzy name perf)
> - `tests/integration/patients/test_rls_isolation_cms_app_role.py` (RLS get/list/search/merge/audit cross-clinic ở cả service + HTTP + DB level)
> - `tests/integration/test_patient_search_endpoint.py` (search 401, unaccent, phone, invalid type 422, limit)
> - `tests/unit/patients/test_patient_service.py`, `test_guardian_service.py`, `test_merge_service.py`, `test_patient_schemas.py`

---

## 1. Ma trận truy vết (Function → Test Cases → Coverage)

| Function | Tên chức năng | Status (nguồn) | Test Case IDs | Coverage |
|---|---|---|---|---|
| PAT-001 | Tạo bệnh nhân mới | ✅ DONE | TC-PAT-001, TC-PAT-002, TC-PAT-003, TC-PAT-004, TC-PAT-005 | COVERED |
| PAT-002 | Auto-gen patient_code | ✅ DONE | TC-PAT-006, TC-PAT-007, TC-PAT-008 | COVERED |
| PAT-003 | Xem hồ sơ chi tiết | ✅ DONE | TC-PAT-009, TC-PAT-010, TC-PAT-011 | COVERED |
| PAT-004 | Sửa thông tin BN | ✅ DONE | TC-PAT-012, TC-PAT-013, TC-PAT-014, TC-PAT-015 | PARTIAL |
| PAT-005 | Soft-delete BN | ✅ DONE | TC-PAT-016, TC-PAT-017, TC-PAT-018 | PARTIAL |
| PAT-006 | Search theo SĐT | ✅ DONE | TC-PAT-019, TC-PAT-020 | COVERED |
| PAT-007 | Search theo tên (fuzzy) | ✅ DONE | TC-PAT-021, TC-PAT-022 | COVERED |
| PAT-008 | Search theo mã BN | ✅ DONE | TC-PAT-023, TC-PAT-024 | COVERED |
| PAT-009 | Performance: 100k record <100ms | ✅ DONE | TC-PAT-025 | COVERED |
| PAT-010 | Guardian relationship | ✅ DONE | TC-PAT-026, TC-PAT-027 | COVERED |
| PAT-011 | Primary contact flag | ✅ DONE | TC-PAT-028, TC-PAT-029 | PARTIAL |
| PAT-012 | Merge duplicate BN | ✅ DONE | TC-PAT-030, TC-PAT-031, TC-PAT-032, TC-PAT-033 | COVERED |
| PAT-013 | Undo merge (7 ngày) | ✅ DONE | TC-PAT-034, TC-PAT-035, TC-PAT-036 | COVERED |
| PAT-014 | BHYT info | ✅ DONE | TC-PAT-037, TC-PAT-038, TC-PAT-039 | PARTIAL |
| PAT-015 | Allergies tracking | ✅ DONE | TC-PAT-040, TC-PAT-041 | PARTIAL |
| PAT-016 | Chronic conditions | ✅ DONE | TC-PAT-042 | PARTIAL |
| PAT-017 | Blood type | ✅ DONE | TC-PAT-043, TC-PAT-044 | PARTIAL |
| PAT-018 | DOB hoặc birth_year | ✅ DONE | TC-PAT-045, TC-PAT-046, TC-PAT-047 | COVERED |
| PAT-019 | Đính kèm tài liệu | ⬜ TODO | TC-PAT-048, TC-PAT-049, TC-PAT-050 | MISSING |
| PAT-020 | Audit patient.read | ✅ DONE | TC-PAT-051, TC-PAT-052, TC-PAT-053 | COVERED |
| PAT-021 | Export hồ sơ BN | 💡 IDEA (v2) | TC-PAT-054, TC-PAT-055, TC-PAT-056 | MISSING |
| PAT-022 | Bulk import CSV | 💡 IDEA (v2) | TC-PAT-057, TC-PAT-058, TC-PAT-059, TC-PAT-060, TC-PAT-061, TC-PAT-062, TC-PAT-063, TC-PAT-064 | MISSING |

**Tổng kết coverage theo function:** COVERED = 13 · PARTIAL = 6 · MISSING = 3.
*(Status nguồn: 19 DONE, 1 TODO, 2 IDEA. PARTIAL = có test cho function nhưng thiếu nhánh field-cụ-thể/negative/security; MISSING = function chưa ship.)*

---

## 2. Chi tiết Test Cases

### TC-PAT-001 — Tạo bệnh nhân mới trả 201 + patient_code (happy path)
- **Function:** PAT-001
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Đăng nhập role có perm `patient.write`; clinic_id trong JWT.
- **Bước thực hiện:** 1) POST `/patients` body tối thiểu (full_name, gender, phone, dob/birth_year).
- **Dữ liệu test:** `{full_name:"Nguyễn Văn A", gender:"male", phone:"0901234567", dob:"1990-01-15"}`
- **Kết quả mong đợi:** HTTP 201; response có `id`, `patient_code` auto-gen (BN0001), `clinic_id` lấy auto từ JWT.
- **Coverage hiện tại:** COVERED (`test_patients_api.py::test_create_patient_returns_201_with_code`; permission seed: `::test_patient_permissions_seeded`).

### TC-PAT-002 — Tạo BN thiếu trường bắt buộc (negative 4xx)
- **Function:** PAT-001
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Đã auth `patient.write`.
- **Bước thực hiện:** 1) POST thiếu trường bắt buộc.
- **Dữ liệu test:** body thiếu full_name.
- **Kết quả mong đợi:** HTTP 4xx (422); không tạo record.
- **Coverage hiện tại:** COVERED (`test_patients_negative.py::test_create_missing_required_fields_returns_4xx`).

### TC-PAT-003 — Validate input bất thường: gender sai, tên quá dài, dob tương lai (negative)
- **Function:** PAT-001
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Đã auth `patient.write`.
- **Bước thực hiện:** 1) POST gender ngoài enum. 2) full_name quá dài. 3) dob ở tương lai. 4) birth_year=0.
- **Dữ liệu test:** lần lượt 4 biến thể.
- **Kết quả mong đợi:** Tất cả HTTP 4xx (422); không tạo record.
- **Coverage hiện tại:** COVERED (`test_patients_negative.py::test_create_invalid_gender_returns_4xx`, `::test_create_full_name_too_long_returns_4xx`, `::test_create_future_dob_returns_4xx`, `::test_create_birth_year_zero_returns_4xx`).

### TC-PAT-004 — Tạo/đọc BN: 401 chưa auth & 403 thiếu quyền (security)
- **Function:** PAT-001
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** (a) không token; (b) token role không có quyền.
- **Bước thực hiện:** 1) Gọi endpoint patient không token → 401. 2) Gọi với token thiếu quyền → 403.
- **Dữ liệu test:** body hợp lệ.
- **Kết quả mong đợi:** (a) 401; (b) 403.
- **Coverage hiện tại:** COVERED (`test_patients_api.py::test_list_patients_without_token_returns_401_or_403`; search 401 `test_patient_search_endpoint.py::test_unauthenticated_returns_401`). *(Bổ sung gợi ý: thêm 403 riêng cho POST `patient.write`.)*

### TC-PAT-005 — Cô lập clinic khi tạo/đọc BN (security RLS)
- **Function:** PAT-001
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB, RLS)
- **Tiền điều kiện:** Clinic A và B; token A.
- **Bước thực hiện:** 1) Tạo BN bằng token A. 2) Token B GET/list BN đó.
- **Dữ liệu test:** BN dưới clinic A.
- **Kết quả mong đợi:** Record gắn clinic_id=A; clinic B trả 404 / 0 row.
- **Coverage hiện tại:** COVERED (`test_patients_api.py::test_tenant_isolation_via_http`; `test_rls_isolation_cms_app_role.py::test_rls_get_patient_cross_clinic_returns_zero_rows`, `::test_rls_via_http_get_patient_cross_tenant_returns_404`, `::test_rls_list_patients_cross_clinic_returns_only_own`).

### TC-PAT-006 — Auto-gen patient_code BN0001 & tăng dần (happy path)
- **Function:** PAT-002
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Unit + Integration
- **Tiền điều kiện:** Clinic chưa có BN.
- **Bước thực hiện:** 1) Sinh code BN đầu tiên. 2) Sinh code BN thứ N.
- **Dữ liệu test:** chuỗi tạo BN.
- **Kết quả mong đợi:** BN đầu = BN0001; tiếp theo tăng tuần tự; duy nhất trong clinic.
- **Coverage hiện tại:** COVERED (`tests/unit/patients/test_patient_service.py::test_first_patient_returns_bn0001`, `::test_nth_patient_increments`; E2E `test_patients_api.py::test_create_patient_returns_201_with_code`).

### TC-PAT-007 — patient_code không tái dùng sau merge+undo (edge)
- **Function:** PAT-002
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Có BN bị merge (soft-delete) rồi undo.
- **Bước thực hiện:** 1) Tạo BN mới sau merge. 2) Kiểm tra code không trùng/không tái dùng số đã cấp.
- **Dữ liệu test:** kịch bản merge→undo→create.
- **Kết quả mong đợi:** Code mới không tái dùng số của BN đã xoá mềm (MAX tính cả soft-deleted).
- **Coverage hiện tại:** COVERED (`test_patients_api.py::test_patient_code_not_reused_after_merge_and_undo_succeeds`).

### TC-PAT-008 — Sequence độc lập theo clinic (RLS/edge)
- **Function:** PAT-002
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Clinic A, B.
- **Bước thực hiện:** 1) Tạo BN A. 2) Tạo BN B. 3) So sánh.
- **Dữ liệu test:** mỗi clinic 1 BN.
- **Kết quả mong đợi:** Mỗi clinic có dải mã riêng (đều BN0001); không counter toàn cục.
- **Coverage hiện tại:** PARTIAL (auto-code đã test trong 1 clinic; cần case 2-clinic riêng để chốt độc lập sequence).

### TC-PAT-009 — Xem hồ sơ chi tiết (happy path)
- **Function:** PAT-003
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Đã auth `patient.read`; BN tồn tại.
- **Bước thực hiện:** 1) GET `/patients/{id}`.
- **Dữ liệu test:** id hợp lệ.
- **Kết quả mong đợi:** HTTP 200; payload đủ info + y tế; ghi audit `patient.read` async (xem PAT-020).
- **Coverage hiện tại:** COVERED (`test_patients_api.py::test_get_patient_writes_audit_read_row`; unit `test_patient_service.py::test_returns_patient_when_found`).

### TC-PAT-010 — Xem BN không tồn tại / đã xoá (negative 404)
- **Function:** PAT-003
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** Unit + Integration
- **Tiền điều kiện:** Đã auth.
- **Bước thực hiện:** 1) GET id không tồn tại. 2) GET id đã soft-delete.
- **Dữ liệu test:** UUID rác + id đã xoá.
- **Kết quả mong đợi:** HTTP 404 (NotFound).
- **Coverage hiện tại:** COVERED (`tests/unit/patients/test_patient_service.py::test_raises_not_found_when_none`, `::test_raises_not_found_when_deleted`).

### TC-PAT-011 — Xem BN clinic khác (security RLS 404)
- **Function:** PAT-003
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB, RLS)
- **Tiền điều kiện:** BN clinic A; token B.
- **Bước thực hiện:** 1) GET `/patients/{id-A}` bằng token B (HTTP + DB level).
- **Dữ liệu test:** id BN clinic A.
- **Kết quả mong đợi:** HTTP 404 (RLS che giấu); ở DB level 0 row.
- **Coverage hiện tại:** COVERED (`test_rls_isolation_cms_app_role.py::test_rls_get_patient_cross_clinic_returns_zero_rows`, `::test_rls_via_http_get_patient_cross_tenant_returns_404`).

### TC-PAT-012 — Sửa thông tin BN (happy path)
- **Function:** PAT-004
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Unit + Integration
- **Tiền điều kiện:** Đã auth `patient.write`; BN tồn tại.
- **Bước thực hiện:** 1) PATCH `/patients/{id}` đổi full_name/phone.
- **Dữ liệu test:** `{full_name:"Tên mới", phone:"0987654321"}`
- **Kết quả mong đợi:** HTTP 200; field cập nhật; diff tracking ghi audit (xem PAT-020).
- **Coverage hiện tại:** COVERED (`tests/unit/patients/test_patient_service.py::test_updates_full_name`; schema update `test_patient_schemas.py::test_valid_phone_update`, `::test_all_fields_optional`).

### TC-PAT-013 — Sửa BN không tồn tại (negative 404)
- **Function:** PAT-004
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** Unit
- **Tiền điều kiện:** Đã auth.
- **Bước thực hiện:** 1) PATCH id không tồn tại.
- **Dữ liệu test:** UUID rác.
- **Kết quả mong đợi:** HTTP 404.
- **Coverage hiện tại:** COVERED (`tests/unit/patients/test_patient_service.py` lớp Update `::test_raises_not_found`).

### TC-PAT-014 — Sửa BN: SĐT sai format khi update (negative 422)
- **Function:** PAT-004
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** Unit
- **Tiền điều kiện:** —
- **Bước thực hiện:** 1) Validate PatientUpdate với phone sai format.
- **Dữ liệu test:** phone không 10 số VN.
- **Kết quả mong đợi:** ValidationError / 422; không cập nhật.
- **Coverage hiện tại:** COVERED (`tests/unit/patients/test_patient_schemas.py::test_invalid_phone_update_raises`).

### TC-PAT-015 — Sửa BN: 401/403 thiếu patient.write (security)
- **Function:** PAT-004
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** (a) không token; (b) token thiếu `patient.write`.
- **Bước thực hiện:** 1) PATCH `/patients/{id}` theo (a)(b).
- **Dữ liệu test:** body hợp lệ.
- **Kết quả mong đợi:** (a) 401; (b) 403; record không đổi.
- **Coverage hiện tại:** PARTIAL (pattern 401/403 đã có cho list/merge; cần case 403 riêng cho PATCH `patient.write` — đề xuất bổ sung).

### TC-PAT-016 — Soft-delete set is_deleted, ẩn khỏi list (happy path)
- **Function:** PAT-005
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Unit + Integration
- **Tiền điều kiện:** Đã auth `patient.delete`; BN tồn tại.
- **Bước thực hiện:** 1) DELETE `/patients/{id}`. 2) GET list mặc định.
- **Dữ liệu test:** id BN.
- **Kết quả mong đợi:** HTTP 204; set `is_deleted/deleted_at/deleted_by`; ẩn khỏi list (trừ `include_deleted=true`); references giữ; audit delete.
- **Coverage hiện tại:** COVERED (`tests/unit/patients/test_patient_service.py` lớp SoftDelete `::test_sets_is_deleted`; list `::test_returns_list_and_total` có tham số include_deleted).

### TC-PAT-017 — Soft-delete BN không tồn tại (negative 404)
- **Function:** PAT-005
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** Unit
- **Tiền điều kiện:** Đã auth.
- **Bước thực hiện:** 1) DELETE id không tồn tại.
- **Dữ liệu test:** UUID rác.
- **Kết quả mong đợi:** HTTP 404.
- **Coverage hiện tại:** COVERED (`tests/unit/patients/test_patient_service.py` lớp SoftDelete `::test_raises_not_found`).

### TC-PAT-018 — Soft-delete: 401/403 thiếu patient.delete + restore 30 ngày (security/edge)
- **Function:** PAT-005
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx) + Integration
- **Tiền điều kiện:** (a) token thiếu `patient.delete`; (b) BN đã soft-delete < 30 ngày (admin restore).
- **Bước thực hiện:** 1) DELETE thiếu quyền → 403. 2) Truy cập trash + restore (nếu endpoint admin tồn tại).
- **Dữ liệu test:** id BN.
- **Kết quả mong đợi:** (a) 403 (và 401 khi không token); (b) restore set is_deleted=false, quay lại list.
- **Coverage hiện tại:** PARTIAL (DELETE có gate `patient.delete` trong code; chưa thấy test 403 riêng cho DELETE, và chưa thấy test trash/restore 30 ngày — đề xuất bổ sung).

### TC-PAT-019 — Search theo SĐT (happy path)
- **Function:** PAT-006
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Unit + Integration
- **Tiền điều kiện:** Đã auth `patient.read`; có BN với SĐT đã biết.
- **Bước thực hiện:** 1) GET `/patients/search?q=0901234567&type=phone`.
- **Dữ liệu test:** SĐT trùng ≥1 BN.
- **Kết quả mong đợi:** HTTP 200; trả list match (SĐT không unique); chỉ trong clinic; dùng index phone.
- **Coverage hiện tại:** COVERED (`test_patients_api.py::test_search_by_phone_returns_patient`; `test_patient_search_endpoint.py::test_phone_search_now_functional`; unit `test_patient_service.py::test_search_by_phone`).

### TC-PAT-020 — Search SĐT cô lập clinic (security RLS)
- **Function:** PAT-006
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB, RLS)
- **Tiền điều kiện:** Cùng SĐT ở clinic A và B; token A.
- **Bước thực hiện:** 1) Search SĐT bằng token A (service + HTTP).
- **Dữ liệu test:** SĐT trùng 2 clinic.
- **Kết quả mong đợi:** Chỉ trả BN clinic A; 0 row của clinic B.
- **Coverage hiện tại:** COVERED (`test_rls_isolation_cms_app_role.py::test_rls_search_by_phone_cross_clinic_returns_zero`, `::test_rls_via_http_search_phone_cross_clinic_empty`).

### TC-PAT-021 — Search tên fuzzy có/không dấu (happy path)
- **Function:** PAT-007
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Unit + Integration
- **Tiền điều kiện:** Đã auth; có BN "Nguyễn Văn An".
- **Bước thực hiện:** 1) GET `/patients/search?q=nguyen van an&type=name` (không dấu).
- **Dữ liệu test:** keyword không dấu.
- **Kết quả mong đợi:** HTTP 200; match nhờ ts_vector + pg_trgm + unaccent.
- **Coverage hiện tại:** COVERED (`test_patients_api.py::test_search_by_name_fuzzy_matches_accented`; `test_patient_search_endpoint.py::test_name_search_vietnamese_unaccent`; unit `test_patient_service.py::test_search_by_name_combines_ts_and_trgm`, `::test_search_by_name_deduplicates`).

### TC-PAT-022 — Search tên input bất thường không 500 (edge/negative)
- **Function:** PAT-007
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Đã auth.
- **Bước thực hiện:** 1) Search với apostrophe, 1 ký tự, chuỗi rất dài, unicode, null-byte, q rỗng.
- **Dữ liệu test:** các payload bất thường.
- **Kết quả mong đợi:** Không 500; q rỗng/thiếu trả 4xx (422); phần còn lại 200 an toàn (chống SQLi).
- **Coverage hiện tại:** COVERED (`test_patients_negative.py::test_search_single_char_q_does_not_500`, `::test_search_very_long_q_does_not_500`, `::test_search_unicode_q_does_not_500`, `::test_search_null_byte_q_does_not_500`, `::test_search_empty_q_returns_4xx`, `::test_search_missing_q_parameter_returns_4xx`; `test_patients_api.py::test_search_by_name_apostrophe_does_not_500`).

### TC-PAT-023 — Search theo mã BN exact (happy path)
- **Function:** PAT-008
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Unit + Integration
- **Tiền điều kiện:** Đã auth; biết patient_code.
- **Bước thực hiện:** 1) GET `/patients/search?q=BN0023&type=code`.
- **Dữ liệu test:** mã hợp lệ.
- **Kết quả mong đợi:** HTTP 200; trả đúng BN0023 (exact, case-insensitive); index uq_patient_clinic_code.
- **Coverage hiện tại:** COVERED (`test_patients_api.py::test_search_by_code_exact_match`; unit `test_patient_service.py::test_search_by_code`).

### TC-PAT-024 — Search type không hợp lệ (negative 422)
- **Function:** PAT-008
- **Loại:** Negative
- **Ưu tiên:** P2
- **Layer:** Integration + Unit
- **Tiền điều kiện:** Đã auth.
- **Bước thực hiện:** 1) GET search với `type` ngoài {phone,name,code,all}.
- **Dữ liệu test:** `type=xyz`.
- **Kết quả mong đợi:** HTTP 422.
- **Coverage hiện tại:** COVERED (`test_patient_search_endpoint.py::test_invalid_type_returns_422`; schema `test_patient_schemas.py::test_invalid_type_raises`).

### TC-PAT-025 — Hiệu năng phone search p95 < 100ms / 100k (performance)
- **Function:** PAT-009
- **Loại:** Edge / Performance
- **Ưu tiên:** P1
- **Layer:** Integration (real DB) + benchmark
- **Tiền điều kiện:** Seed 100.000 BN; index partial + RLS clinic_id.
- **Bước thực hiện:** 1) Đo phone search nhiều lần lấy p95. 2) Đo fuzzy name search ghi nhận số liệu.
- **Dữ liệu test:** 100k BN.
- **Kết quả mong đợi:** phone p95 < 100ms (nguồn ghi 46.9ms PASS); fuzzy name ghi nhận số liệu.
- **Coverage hiện tại:** COVERED (`test_patients_perf.py::test_perf_phone_search_p95_under_100ms_at_100k`, `::test_perf_fuzzy_name_search_records_numbers_at_100k`).

### TC-PAT-026 — Thêm/list/xoá guardian relationship (happy path)
- **Function:** PAT-010
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Unit + Integration
- **Tiền điều kiện:** Đã auth `patient.write`; BN + 1 BN khác làm guardian (cùng clinic).
- **Bước thực hiện:** 1) POST `/patients/{id}/guardians`. 2) GET list. 3) DELETE `/patients/guardians/{relation_id}`.
- **Dữ liệu test:** type ∈ {parent/child/spouse/sibling/guardian}.
- **Kết quả mong đợi:** 201 add → list trả quan hệ → 204 soft-delete quan hệ.
- **Coverage hiện tại:** COVERED (`test_patients_api.py::test_guardian_add_list_remove`; unit `test_guardian_service.py::test_happy_path_creates_relation`, `::test_returns_relations`, `::test_soft_deletes_relation`).

### TC-PAT-027 — Guardian không tồn tại / BN đã xoá (negative + RLS cùng clinic)
- **Function:** PAT-010
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** Unit
- **Tiền điều kiện:** Đã auth.
- **Bước thực hiện:** 1) Add guardian khi patient không tồn tại / guardian không tồn tại / patient đã xoá. 2) Xoá relation không tồn tại / đã xoá.
- **Dữ liệu test:** các id không hợp lệ.
- **Kết quả mong đợi:** HTTP 404 (NotFound) cho mọi nhánh; không tạo quan hệ chéo.
- **Coverage hiện tại:** COVERED (`test_guardian_service.py::test_raises_not_found_for_patient`, `::test_raises_not_found_for_guardian`, `::test_raises_not_found_for_deleted_patient`, `::test_raises_not_found_when_none`, `::test_raises_not_found_when_already_deleted`).

### TC-PAT-028 — Đặt primary contact flag (happy path)
- **Function:** PAT-011
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** BN có ≥1 guardian.
- **Bước thực hiện:** 1) Set `is_primary_contact=true` cho 1 quan hệ.
- **Dữ liệu test:** guardian.
- **Kết quả mong đợi:** HTTP 200/201; quan hệ được đánh primary; dùng mặc định SMS reminder.
- **Coverage hiện tại:** PARTIAL (guardian CRUD đã COVERED; chưa thấy test riêng cho cờ `is_primary_contact` happy-path — đề xuất bổ sung assertion cụ thể).

### TC-PAT-029 — Chỉ 1 primary contact/BN — partial unique constraint (edge)
- **Function:** PAT-011
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** 1 guardian đang primary.
- **Bước thực hiện:** 1) Set guardian thứ 2 là primary.
- **Dữ liệu test:** chuyển primary.
- **Kết quả mong đợi:** Guardian cũ tự bỏ primary (mutual exclusive theo partial unique); chỉ 1 `is_primary_contact=true`.
- **Coverage hiện tại:** PARTIAL (constraint khai báo ở model; chưa thấy test mutual-exclusive cụ thể — đề xuất bổ sung).

### TC-PAT-030 — Merge 2 BN reassign + manifest (happy path)
- **Function:** PAT-012
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Unit + Integration
- **Tiền điều kiện:** Đã auth `patient.merge`; 2 BN cùng clinic, có visit/quan hệ riêng.
- **Bước thực hiện:** 1) POST `/patients/merge {keep_id, drop_id}`. 2) Kiểm tra reassign + merge_log manifest + audit.
- **Dữ liệu test:** keep_id, drop_id.
- **Kết quả mong đợi:** HTTP 200; rows của drop → keep; drop soft-delete; INSERT `patient_merge_log` manifest đủ cột; audit ghi.
- **Coverage hiện tại:** COVERED (`test_patients_api.py::test_merge_happy_path`; unit `test_merge_service.py::test_happy_path`, `::test_captures_all_columns`, `::test_audit_log_is_written`).

### TC-PAT-031 — Merge input bất thường: cùng id / drop đã xoá / id rác (negative)
- **Function:** PAT-012
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** Unit + Integration
- **Tiền điều kiện:** Đã auth `patient.merge`.
- **Bước thực hiện:** 1) keep_id==drop_id. 2) drop đã soft-delete. 3) keep/drop không tồn tại. 4) UUID sai format.
- **Dữ liệu test:** 4 biến thể.
- **Kết quả mong đợi:** HTTP 4xx (422/400/404); không merge.
- **Coverage hiện tại:** COVERED (`test_patients_negative.py::test_merge_same_id_returns_4xx`, `::test_merge_already_deleted_drop_returns_4xx`, `::test_merge_nonexistent_uuid_returns_4xx`, `::test_merge_invalid_uuid_format_returns_422`; unit `test_merge_service.py::test_keep_not_found_raises`, `::test_drop_not_found_raises`, `::test_drop_already_deleted_raises`).

### TC-PAT-032 — Merge xuyên clinic bị chặn (security RLS)
- **Function:** PAT-012
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Unit + Integration
- **Tiền điều kiện:** keep clinic A, drop clinic B.
- **Bước thực hiện:** 1) POST merge 2 id khác clinic (service + HTTP).
- **Dữ liệu test:** id chéo clinic.
- **Kết quả mong đợi:** Bị chặn (403/404); không merge xuyên clinic, kể cả ở DB level (cms_app role).
- **Coverage hiện tại:** COVERED (`test_patients_api.py::test_merge_cross_tenant_forbidden`; `test_rls_isolation_cms_app_role.py::test_rls_merge_cross_tenant_blocked_at_service_layer`; unit `test_merge_service.py::test_cross_tenant_raises`).

### TC-PAT-033 — Merge: 403 thiếu patient.merge (security)
- **Function:** PAT-012
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Token không có `patient.merge`.
- **Bước thực hiện:** 1) POST `/patients/merge`.
- **Dữ liệu test:** 2 id hợp lệ.
- **Kết quả mong đợi:** HTTP 403; không thay đổi. (401 khi không token theo pattern chung.)
- **Coverage hiện tại:** COVERED (`test_patients_api.py::test_merge_without_permission_returns_403`).

### TC-PAT-034 — Undo merge trong hạn (happy path)
- **Function:** PAT-013
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Unit + Integration
- **Tiền điều kiện:** Vừa merge < 7 ngày; có merge_log.
- **Bước thực hiện:** 1) POST `/patients/merge/{merge_id}/undo`. 2) Kiểm tra restore + reassign ngược.
- **Dữ liệu test:** merge_id còn hạn.
- **Kết quả mong đợi:** HTTP 200; restore drop; reassign ngược theo manifest; KHÔNG đụng quan hệ vốn của keep.
- **Coverage hiện tại:** COVERED (`test_patients_api.py::test_merge_then_undo_within_window`, `::test_undo_does_not_reassign_keep_patient_own_relations`; unit `test_merge_service.py::test_happy_path_within_deadline`, `::test_undo_only_moves_manifested_rows`; advanced `test_undo_with_long_manifest`, `test_undo_at_exact_deadline_boundary_future_succeeds`).

### TC-PAT-035 — Undo quá hạn 410 / đã undo 409 / log không tồn tại 404 (negative/state machine)
- **Function:** PAT-013
- **Loại:** Negative
- **Ưu tiên:** P0
- **Layer:** Unit + Integration
- **Tiền điều kiện:** merge_log ở các trạng thái: quá 7 ngày / đã undo / không tồn tại.
- **Bước thực hiện:** 1) Undo quá hạn. 2) Undo lần 2. 3) Undo merge_id không tồn tại. 4) Boundary đúng deadline (quá khứ).
- **Dữ liệu test:** merge_log đa trạng thái.
- **Kết quả mong đợi:** 410 (quá hạn), 409 (đã undo), 404 (không tồn tại); boundary quá khứ → 410.
- **Coverage hiện tại:** COVERED (`test_patients_api.py::test_merge_undo_after_expired_deadline_returns_410`; `test_patients_negative.py::test_undo_already_undone_merge_returns_409`, `::test_undo_nonexistent_merge_log_returns_404`; advanced `::test_undo_at_exact_deadline_boundary_past_returns_410`, `::test_undo_already_undone_returns_409`; unit `test_merge_service.py::test_expired_deadline_raises_410`, `::test_already_undone_raises_409`, `::test_merge_log_not_found_raises`).

### TC-PAT-036 — Undo merge verify clinic ownership (security RLS — BUG-004)
- **Function:** PAT-013
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB, RLS)
- **Tiền điều kiện:** merge_id thuộc clinic A; token clinic B.
- **Bước thực hiện:** 1) POST undo merge_id-A bằng token B.
- **Dữ liệu test:** merge_id clinic A.
- **Kết quả mong đợi:** HTTP 404/403; không undo xuyên clinic (regression BUG-004).
- **Coverage hiện tại:** COVERED (`test_patients_negative.py::test_undo_merge_from_different_clinic_returns_404_or_403`).

### TC-PAT-037 — Lưu BHYT info (happy path)
- **Function:** PAT-014
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Đã auth `patient.write`; BN tồn tại.
- **Bước thực hiện:** 1) PATCH `{bhyt_number, bhyt_expires_at}`. 2) GET profile.
- **Dữ liệu test:** bhyt_number 15 ký tự.
- **Kết quả mong đợi:** HTTP 200; lưu đúng; cảnh báo vàng nếu hết hạn < 30 ngày.
- **Coverage hiện tại:** PARTIAL (update field generic đã test; chưa thấy test riêng cho bhyt + cảnh báo hết hạn — đề xuất bổ sung).

### TC-PAT-038 — Validate format BHYT VN (negative)
- **Function:** PAT-014
- **Loại:** Negative
- **Ưu tiên:** P2
- **Layer:** Unit
- **Tiền điều kiện:** —
- **Bước thực hiện:** 1) Validate schema bhyt_number sai độ dài/ký tự.
- **Dữ liệu test:** "123".
- **Kết quả mong đợi:** ValidationError / 422.
- **Coverage hiện tại:** PARTIAL (schema test tồn tại cho phone/gender/dob; chưa thấy test bhyt_number cụ thể — đề xuất bổ sung).

### TC-PAT-039 — BHYT auto-fill khi tạo hóa đơn (cross-module)
- **Function:** PAT-014
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** BN có BHYT còn hạn; tạo invoice.
- **Bước thực hiện:** 1) Tạo invoice cho BN có BHYT.
- **Dữ liệu test:** BN có thẻ.
- **Kết quả mong đợi:** BHYT auto-fill (phần BHYT chi trả vs BN trả) — verify ở module billing.
- **Coverage hiện tại:** MISSING (cross-module; test khi billing hoàn thiện).

### TC-PAT-040 — Thêm dị ứng allergies (happy path)
- **Function:** PAT-015
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Đã auth `patient.write`; BN tồn tại.
- **Bước thực hiện:** 1) PATCH `allergies` (TEXT[]). 2) GET roundtrip.
- **Dữ liệu test:** `["penicillin","hải sản"]`
- **Kết quả mong đợi:** HTTP 200; lưu array; roundtrip đúng.
- **Coverage hiện tại:** PARTIAL (update field generic đã test qua `test_updates_full_name`/schema optional; chưa thấy test array allergies roundtrip cụ thể — đề xuất bổ sung).

### TC-PAT-041 — Allergy kích hoạt cảnh báo khi kê đơn (cross-module)
- **Function:** PAT-015
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** BN dị ứng penicillin; kê thuốc chứa penicillin.
- **Bước thực hiện:** 1) Kê đơn.
- **Dữ liệu test:** active_ingredient = penicillin.
- **Kết quả mong đợi:** Cảnh báo đỏ + override kèm lý do — verify module prescription (RX-006, chưa ship).
- **Coverage hiện tại:** MISSING (cross-module; thuộc RX-006).

### TC-PAT-042 — Ghi nhận chronic_conditions (happy path)
- **Function:** PAT-016
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Đã auth `patient.write`; BN tồn tại.
- **Bước thực hiện:** 1) PATCH `chronic_conditions` (TEXT[]). 2) GET roundtrip.
- **Dữ liệu test:** `["tiểu đường type 2"]`
- **Kết quả mong đợi:** HTTP 200; lưu array; hiển thị sidebar.
- **Coverage hiện tại:** PARTIAL (cơ chế update field/array dùng chung đã test; chưa thấy test chronic_conditions cụ thể — đề xuất bổ sung).

### TC-PAT-043 — Cập nhật blood_type (happy path)
- **Function:** PAT-017
- **Loại:** Happy path
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Đã auth `patient.write`; BN tồn tại.
- **Bước thực hiện:** 1) PATCH `{blood_type:"O+"}`. 2) GET.
- **Dữ liệu test:** O+.
- **Kết quả mong đợi:** HTTP 200; lưu enum đúng.
- **Coverage hiện tại:** PARTIAL (update field generic đã test; chưa thấy test blood_type happy-path cụ thể — đề xuất bổ sung).

### TC-PAT-044 — blood_type ngoài enum (negative)
- **Function:** PAT-017
- **Loại:** Negative
- **Ưu tiên:** P2
- **Layer:** Unit
- **Tiền điều kiện:** —
- **Bước thực hiện:** 1) Validate schema với blood_type không hợp lệ.
- **Dữ liệu test:** "Z".
- **Kết quả mong đợi:** ValidationError / 422.
- **Coverage hiện tại:** PARTIAL (pattern enum-reject có ở schema test gender; chưa thấy test blood_type enum cụ thể — đề xuất bổ sung tương tự `test_invalid_gender_raises`).

### TC-PAT-045 — Tạo BN với dob đầy đủ (happy path)
- **Function:** PAT-018
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Unit + Integration
- **Tiền điều kiện:** Đã auth.
- **Bước thực hiện:** 1) Tạo BN với dob hợp lệ.
- **Dữ liệu test:** `{dob:"1985-03-20"}`
- **Kết quả mong đợi:** HTTP 201; lưu dob; tuổi tính từ dob.
- **Coverage hiện tại:** COVERED (schema `test_patient_schemas.py::test_valid_dob_only`; E2E create `test_patients_api.py::test_create_patient_returns_201_with_code`).

### TC-PAT-046 — Tạo BN chỉ có birth_year (happy path/edge)
- **Function:** PAT-018
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Unit
- **Tiền điều kiện:** Đã auth; BN không nhớ ngày sinh.
- **Bước thực hiện:** 1) Tạo BN với birth_year, không dob.
- **Dữ liệu test:** `{birth_year:1960}`
- **Kết quả mong đợi:** Hợp lệ; tuổi fallback theo birth_year.
- **Coverage hiện tại:** COVERED (`test_patient_schemas.py::test_valid_birth_year_only`; unit service `test_no_dob_no_warning`).

### TC-PAT-047 — Ràng buộc dob/birth_year (negative — constraint)
- **Function:** PAT-018
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** Unit + Integration
- **Tiền điều kiện:** Đã auth.
- **Bước thực hiện:** 1) Thiếu cả dob+birth_year. 2) Có cả 2 nhưng year(dob)≠birth_year.
- **Dữ liệu test:** (a) thiếu cả hai; (b) `{dob:"1985-03-20", birth_year:1990}`.
- **Kết quả mong đợi:** HTTP 4xx (422) cho cả hai (constraint: ≥1; nếu cả 2 thì year khớp).
- **Coverage hiện tại:** COVERED (`test_patient_schemas.py::test_neither_dob_nor_birth_year_raises`, `::test_mismatch_year_raises`, `::test_valid_both_matching`; E2E `test_patients_negative.py::test_create_mismatched_dob_and_birth_year_returns_4xx`).

### TC-PAT-048 — Đính kèm tài liệu BN (happy path) — TODO
- **Function:** PAT-019
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB + storage)
- **Tiền điều kiện:** Đã auth; BN tồn tại; storage S3 wired.
- **Bước thực hiện:** 1) Presigned URL → upload. 2) POST metadata `patient_document`. 3) GET `/patients/:id/documents`.
- **Dữ liệu test:** PDF lab_result.
- **Kết quả mong đợi:** HTTP 201; metadata gắn patient_id+clinic_id; type ∈ {id_card,health_card,xray,lab_result,prescription,other}.
- **Coverage hiện tại:** MISSING (status TODO — storage S3 chưa wire).

### TC-PAT-049 — Upload sai type/size (negative) — TODO
- **Function:** PAT-019
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Storage wired.
- **Bước thực hiện:** 1) Upload .exe / file quá lớn / mime sai.
- **Dữ liệu test:** .exe, 100MB.
- **Kết quả mong đợi:** HTTP 413/422; từ chối.
- **Coverage hiện tại:** MISSING.

### TC-PAT-050 — Tài liệu cô lập clinic + 401/403 (security RLS) — TODO
- **Function:** PAT-019
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB, RLS)
- **Tiền điều kiện:** Tài liệu BN clinic A; (a) token B; (b) không token; (c) thiếu quyền.
- **Bước thực hiện:** 1) GET/tải document clinic A theo (a)(b)(c).
- **Dữ liệu test:** document_id clinic A.
- **Kết quả mong đợi:** (a) 404; (b) 401; (c) 403.
- **Coverage hiện tại:** MISSING.

### TC-PAT-051 — Mỗi lần đọc PHI ghi đúng 1 audit row (happy path/security)
- **Function:** PAT-020
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Đã auth; BN tồn tại; audit_log hoạt động.
- **Bước thực hiện:** 1) GET `/patients/{id}` 1 lần. 2) Query audit_log.
- **Dữ liệu test:** 1 lần đọc.
- **Kết quả mong đợi:** Đúng 1 audit `patient.read` với entity_id + action đúng; ghi async (poll, không sleep).
- **Coverage hiện tại:** COVERED (`test_patients_audit.py::test_single_read_produces_exactly_one_audit_row`, `::test_audit_read_has_correct_entity_id_and_action`, `::test_audit_uses_polling_not_sleep_demonstrates_promptness`; `test_patients_api.py::test_get_patient_writes_audit_read_row`; unit `test_patient_service.py::test_calls_write_audit`).

### TC-PAT-052 — Nhiều lần đọc → nhiều audit + PII redaction (edge/security)
- **Function:** PAT-020
- **Loại:** Security
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Đã auth.
- **Bước thực hiện:** 1) Đọc nhiều lần. 2) Tạo BN có id_number → kiểm tra snapshot audit.
- **Dữ liệu test:** nhiều lượt đọc + BN có id_number.
- **Kết quả mong đợi:** Mỗi lần đọc sinh 1 audit; snapshot create KHÔNG chứa `id_number` (PII redaction).
- **Coverage hiện tại:** COVERED (`test_patients_audit.py::test_multiple_reads_produce_multiple_audit_rows`, `::test_audit_exclude_id_number_absent_from_create_snapshot`).

### TC-PAT-053 — Audit read cô lập clinic (security RLS)
- **Function:** PAT-020
- **Loại:** Security
- **Ưu tiên:** P1
- **Layer:** Integration (real DB, RLS)
- **Tiền điều kiện:** 2 clinic.
- **Bước thực hiện:** 1) Đọc BN clinic A. 2) Vai trò cms_app/clinic B truy vấn audit_log.
- **Dữ liệu test:** audit của clinic A.
- **Kết quả mong đợi:** Audit gắn clinic_id A; clinic B không xem được audit của clinic A (DB-level block).
- **Coverage hiện tại:** COVERED (`test_rls_isolation_cms_app_role.py::test_rls_db_level_cms_app_blocks_cross_clinic_audit_log`).

### TC-PAT-054 — Export hồ sơ BN ra PDF (happy path) — IDEA/v2
- **Function:** PAT-021
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Đã auth; BN có visit/Rx; tính năng v2 đã làm.
- **Bước thực hiện:** 1) GET export PDF. 2) Kiểm tra file.
- **Dữ liệu test:** BN có lịch sử.
- **Kết quả mong đợi:** HTTP 200; PDF letterhead + info + lịch sử + watermark "Confidential" + timestamp; audit `export_patient_pdf`.
- **Coverage hiện tại:** MISSING (IDEA/v2 chưa làm).

### TC-PAT-055 — Export: 401/403 thiếu quyền (security) — IDEA/v2
- **Function:** PAT-021
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** (a) không token; (b) thiếu quyền export.
- **Bước thực hiện:** 1) GET export theo (a)(b).
- **Dữ liệu test:** id BN.
- **Kết quả mong đợi:** (a) 401; (b) 403.
- **Coverage hiện tại:** MISSING.

### TC-PAT-056 — Export BN clinic khác (security RLS) — IDEA/v2
- **Function:** PAT-021
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB, RLS)
- **Tiền điều kiện:** BN clinic A; token B.
- **Bước thực hiện:** 1) GET export BN clinic A bằng token B.
- **Dữ liệu test:** id BN clinic A.
- **Kết quả mong đợi:** HTTP 404; không export xuyên clinic.
- **Coverage hiện tại:** MISSING.

### TC-PAT-057 — Bulk import CSV hợp lệ (happy path) — IDEA/v2
- **Function:** PAT-022
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Admin; CSV đúng schema; v2 đã làm.
- **Bước thực hiện:** 1) Upload CSV 50 dòng + mapping. 2) Confirm. 3) Kiểm tra report.
- **Dữ liệu test:** CSV 50 BN hợp lệ.
- **Kết quả mong đợi:** HTTP 200; tạo 50 BN gắn clinic; patient_code tuần tự; report success=50; audit import.
- **Coverage hiện tại:** MISSING (IDEA/v2). *(Lưu ý: `tests/unit/admin/test_csv_parser.py` là cho onboarding admin, KHÔNG phải patient import.)*

### TC-PAT-058 — Preview 10 dòng đầu (edge) — IDEA/v2
- **Function:** PAT-022
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Admin; CSV upload.
- **Bước thực hiện:** 1) Upload CSV → bước preview.
- **Dữ liệu test:** CSV 100 dòng.
- **Kết quả mong đợi:** Trả 10 dòng đầu đã map; chưa INSERT.
- **Coverage hiện tại:** MISSING.

### TC-PAT-059 — Import dòng lỗi → skip + report (negative/partial) — IDEA/v2
- **Function:** PAT-022
- **Loại:** Negative
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Admin có quyền.
- **Bước thực hiện:** 1) Import CSV 10 dòng (3 lỗi).
- **Dữ liệu test:** 7 hợp lệ + 3 lỗi.
- **Kết quả mong đợi:** Tạo 7, skip 3; report chi tiết dòng lỗi.
- **Coverage hiện tại:** MISSING.

### TC-PAT-060 — Import phát hiện trùng (edge) — IDEA/v2
- **Function:** PAT-022
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Một số BN trong CSV đã tồn tại.
- **Bước thực hiện:** 1) Import CSV chứa BN trùng.
- **Dữ liệu test:** 2 dòng trùng.
- **Kết quả mong đợi:** Đánh dấu duplicate; không tạo bản ghi đôi.
- **Coverage hiện tại:** MISSING.

### TC-PAT-061 — Import file sai format/schema (negative) — IDEA/v2
- **Function:** PAT-022
- **Loại:** Negative
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Admin.
- **Bước thực hiện:** 1) Upload .txt / CSV sai header.
- **Dữ liệu test:** file sai.
- **Kết quả mong đợi:** HTTP 422; báo lỗi schema; không import.
- **Coverage hiện tại:** MISSING.

### TC-PAT-062 — Import: 401/403 thiếu quyền Admin (security) — IDEA/v2
- **Function:** PAT-022
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** (a) không token; (b) token không Admin / thiếu quyền.
- **Bước thực hiện:** 1) POST import theo (a)(b).
- **Dữ liệu test:** CSV hợp lệ.
- **Kết quả mong đợi:** (a) 401; (b) 403.
- **Coverage hiện tại:** MISSING.

### TC-PAT-063 — Import gán đúng clinic (security RLS) — IDEA/v2
- **Function:** PAT-022
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB, RLS)
- **Tiền điều kiện:** Token Admin clinic A.
- **Bước thực hiện:** 1) Import CSV bằng token A. 2) Token B kiểm tra.
- **Dữ liệu test:** CSV 10 BN.
- **Kết quả mong đợi:** Toàn bộ gán clinic_id=A; clinic B không thấy.
- **Coverage hiện tại:** MISSING.

### TC-PAT-064 — Import lớn: progress + code tuần tự (edge) — IDEA/v2
- **Function:** PAT-022
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** Admin; CSV 5.000 dòng.
- **Bước thực hiện:** 1) Import batch lớn. 2) Theo dõi progress + kiểm tra code.
- **Dữ liệu test:** CSV 5.000 BN.
- **Kết quả mong đợi:** Batch INSERT có progress; patient_code tuần tự không race; report đầy đủ.
- **Coverage hiện tại:** MISSING.

---

## 3. Khuyến nghị cho Tester

1. **Đã xác minh trực tiếp code + test** tại `clinic-cms-workspace/clinic-cms-merge`. Permission thật: `patient.read`, `patient.write` (create/update/guardian), `patient.delete`, `patient.merge`, `patient.erase`. Search hỗ trợ `type=phone|name|code|all` với `q` min_length=1 max_length=100.
2. **Tính năng "ngoài BA gốc" đã ship:** xoá vĩnh viễn (erasure, `patient.erase` — GDPR/NĐ13) ở `api/erasure_routes.py`; PII redaction trong audit snapshot (id_number bị loại); RLS test ở 3 tầng (service / HTTP / DB cms_app role). Đề xuất nhóm chức năng PLT/COMPLIANCE catalog hóa riêng các function erasure này nếu chúng có code function-list tương ứng.
3. **Gap test cần bổ sung (PARTIAL — function DONE nhưng thiếu nhánh):**
   - 403 riêng cho PATCH (`patient.write`) và DELETE (`patient.delete`) — hiện chỉ có 401/403 cho list & merge (TC-PAT-015, TC-PAT-018).
   - Test trash/restore 30 ngày (TC-PAT-018) — chưa thấy endpoint/test admin trash.
   - Primary contact happy + mutual-exclusive (TC-PAT-028/029).
   - Field-cụ-thể: BHYT (037/038), allergies roundtrip (040), chronic (042), blood_type enum (043/044) — hiện chỉ test qua update generic + schema phone/gender/dob; nên thêm test theo từng field y tế.
   - 2-clinic auto-code độc lập (TC-PAT-008).
   - Cross-module: BHYT auto-fill invoice (039), allergy warning kê đơn (041) — test khi billing/prescription hoàn thiện.
4. **Backlog (function chưa ship):** PAT-019 (TODO — storage S3), PAT-021 + PAT-022 (IDEA/v2). Viết test khi triển khai.
5. **Quy ước đã áp dụng:** mọi function có quyền có case 401+403; mọi thao tác domain có case RLS cô lập clinic; CRUD/state-machine (merge/undo, soft-delete) có Negative + Edge; regression BUG-004 (undo merge verify ownership) đã COVERED ở TC-PAT-036.
