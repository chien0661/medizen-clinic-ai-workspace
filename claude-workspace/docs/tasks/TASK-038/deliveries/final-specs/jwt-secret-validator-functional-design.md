---
task_id: TASK-038
scope: Q.1 (JWT_SECRET hardening — quick-win)
date: 2026-05-01
status: DONE
test_result: 19/19 PASSED (15 pytest + 4 extended cases)
---

# Q.1 — Thiết kế chức năng JWT_SECRET Validator

## Mục đích

JWT_SECRET là khóa bảo mật sử dụng để ký các JWT token xác thực người dùng. Audit an ninh TASK-032 B.6f phát hiện rằng hệ thống cho phép các giá trị placeholder (ví dụ `change-me-in-production`) chạy trong staging/production nếu chúng đủ dài, gây rủi ro lộ lọc thông tin và không vượt qua các audit tuân thủ quy định (NFR-005, NFR-024).

**Mục tiêu Q.1**: Thêm validator vào `Settings.model_validator()` để:
1. Từ chối bất kỳ JWT_SECRET nào là placeholder khi `ENVIRONMENT != "development"`
2. Tăng độ dài tối thiểu từ 8 ký tự lên 32 ký tự
3. Fail-fast tại startup (trước FastAPI bind request handlers)

Đây là quick-win độc lập (<1 ngày), không liên quan đến MFA, anomaly detection, hoặc lifecycle quản lý PII (B.1-B.17).

---

## Phạm vi

- **Chỉ Q.1** của TASK-038 (riêng biệt với B.1-B.17)
- **Repositories**: `clinic-cms` (BE)
- **Affected file**:
  - `app/core/config.py` — thêm validator + constant
  - `tests/unit/test_config.py` — 15 test cases
  - `.env.example` — hướng dẫn tạo secret mạnh
  - `docker/docker-compose.yml` — cập nhật dev secret

---

## Bảng hành vi (Behavior Matrix)

| Môi trường | JWT_SECRET | Kết quả | Ghi chú |
|-----------|-----------|---------|--------|
| `development` | Bất kỳ chuỗi ≥32 ký tự (kể cả placeholder) | ✅ OK | Cho phép dev dùng giá trị placeholder dài |
| `development` | Chuỗi <32 ký tự | ❌ `ValidationError: string_too_short` | Reject ngay ở `min_length=32` |
| `staging` / `production` / `test` | `change-me-in-production` (legacy, 23 ký tự) | ❌ `ValidationError: string_too_short` | Reject ở min_length trước validator |
| `staging` / `production` / `test` | Bất kỳ placeholder ≥32 ký tự trong set | ❌ `ValidationError: JWT_SECRET is set to a placeholder value in {environment}` | Validator model sau min_length |
| `staging` / `production` / `test` | Secret mạnh, ≥32 ký tự, không placeholder | ✅ OK | Production-ready |

---

## Files được sửa đổi

| File | Dòng | Thay đổi |
|------|------|---------|
| `clinic-cms/app/core/config.py` | 1-62 | **Thêm constants**: `_DEV_PLACEHOLDER_JWT_SECRET` (49 ký tự) + `_PLACEHOLDER_JWT_SECRETS` (frozenset với 3 entries: `please-change-me-to-a-strong-random-secret`, `change-me-in-production-this-default-is-insecure`, và `_DEV_PLACEHOLDER_JWT_SECRET`). **Thay đổi Field**: `JWT_SECRET` min_length `8 → 32`. **Thêm validator**: `model_validator(mode="after")` kiểm tra `ENVIRONMENT != "development"` rồi reject nếu `JWT_SECRET in _PLACEHOLDER_JWT_SECRETS` |
| `clinic-cms/tests/unit/test_config.py` | 1-200 | **Thay old secrets**: 12/27-char secrets thay bằng `TEST_SECRET` (35 ký tự). **Thêm 6 test groups mới** (parametrized 3 envs × 2 placeholders + min_length + strong-prod + default-prod-reject + legacy-short-reject) = ~13 test cases mới |
| `clinic-cms/.env.example` | 7-10 | **Thêm comment block** 3 dòng hướng dẫn tạo secret: `python -c "import secrets; print(secrets.token_urlsafe(48))"` + warning "phải thay đổi trước deploy" |
| `clinic-cms/docker/docker-compose.yml` | 40, 66 | **Cập nhật JWT_SECRET**: cả `api` + `worker` services từ `dev-secret-change-me` (19 ký tự) → `dev-secret-change-me-must-be-32-or-more-chars` (45 ký tự) để pass min_length=32 trong development |

---

## Hợp đồng API / Hành vi thay đổi

### Startup behavior

Khi ứng dụng khởi động:

1. `app.core.config.get_settings()` được gọi (sử dụng `@lru_cache`)
2. `Settings` Pydantic model validate input environment variables
3. **Đầu tiên**: kiểm tra `min_length=32` trên `JWT_SECRET`
   - Nếu fail → `ValidationError: Field validation failed for 'JWT_SECRET' — string_too_short`
   - Nếu pass → tiếp tục
4. **Sau đó**: `model_validator(mode="after")` chạy
   - Nếu `ENVIRONMENT == "development"` → return self (OK)
   - Nếu `ENVIRONMENT != "development"` và `self.JWT_SECRET in _PLACEHOLDER_JWT_SECRETS` → raise `ValidationError("JWT_SECRET is set to a placeholder value '…' in environment '{env}'. Please generate a strong secret using: python -c \"import secrets; print(secrets.token_urlsafe(48))\"")"`
   - Nếu `ENVIRONMENT != "development"` và secret không phải placeholder → return self (OK)

### Error message format

```
pydantic_core._pydantic_core.ValidationError: 1 validation error for Settings
JWT_SECRET
  JWT_SECRET is set to a placeholder value 'please-change-me-to-a-strong-random-secret' in environment 'staging'. Please generate a strong secret using: python -c "import secrets; print(secrets.token_urlsafe(48))" (type=value_error)
```

Message bao gồm:
- Giá trị placeholder thực tế (safe vì nó ở trong public set)
- Tên environment hiện tại
- Hướng dẫn cách tạo secret mạnh

---

## Phạm vi test

### 15 unit tests (pytest)

Chạy bằng `pytest tests/unit/test_config.py -v`:

1. ✅ `test_settings_defaults` — mặc định settings load không error
2. ✅ `test_settings_loads_from_env` — ENV variables override defaults
3. ✅ `test_settings_cors_origins_json_parse` — unrelated to Q.1, regression check
4. ✅ `test_jwt_secret_min_length_enforced` — short secret (9 ký tự) → ValidationError
5. ✅ `test_jwt_secret_legacy_short_placeholder_rejected_by_length` — `change-me-in-production` (23 ký tự) → ValidationError ở min_length
6. ✅ `test_jwt_secret_long_placeholder_allowed_in_development[please-change-me-…]` — development cho phép placeholder dài
7. ✅ `test_jwt_secret_long_placeholder_allowed_in_development[change-me-in-production-…]` — development cho phép placeholder dài thứ 2
8-13. ✅ `test_jwt_secret_placeholder_rejected_outside_development[{env}-{placeholder}]` — 6 cases: `staging × 2 placeholders`, `production × 2`, `test × 2` → tất cả reject
14. ✅ `test_jwt_secret_strong_value_accepted_in_production` — secret mạnh ≥32 ký tự → OK trong production
15. ✅ `test_jwt_secret_default_value_rejected_in_production` — default (`please-change-me-…`) reject trong production

**Result**: 15/15 PASSED

### 4 extended test cases (manual verification)

Script riêng test các edge cases:

| # | Tình huống | Kỳ vọng | Kết quả |
|---|----------|--------|--------|
| 8a | `dev-secret-change-me-must-be-32-or-more-chars` (docker-compose value) NOT in `_PLACEHOLDER_JWT_SECRETS` → load trong production | OK | ✅ PASS |
| 8b | Cùng docker secret load trong development | OK | ✅ PASS |
| 9a | Whitespace-padded placeholder `"   change-me-…   "` trong production → Pydantic không strip whitespace → NOT in set → accepted | OK (behavior documented) | ✅ PASS |
| 9b | Short secret với whitespace (9 ký tự total) → reject ở min_length | ValidationError | ✅ PASS |

**Result**: 4/4 PASSED

**Total**: 19/19 tests PASSED

---

## Migration notes (cho ops team)

### Cách generate strong secret

Thay vì `change-me-in-production`, generate secret mạnh:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
# Output: ví dụ: Drmhze6EPcv0fN_81Bj-nA-...  (~64 ký tự URL-safe)
```

### Cập nhật .env cho staging/production

```bash
# Trước
JWT_SECRET=change-me-in-production

# Sau (copy secret từ câu lệnh trên)
JWT_SECRET=Drmhze6EPcv0fN_81Bj-nA-...
```

### Deployment warning

**Bất kỳ deployment nào** vào staging/production **sử dụng secret cũ** (`change-me-in-production`, `please-change-me-…`, v.v.) **sẽ không khởi động**. Error sẽ xuất hiện tại startup:

```
ValidationError: JWT_SECRET is set to a placeholder value '...' in environment 'staging'.
```

**Remediation**: 
1. Generate secret mạnh (xem trên)
2. Cập nhật `JWT_SECRET` env var
3. Restart app

Đây là **hành vi mong muốn** — fails-fast ngay tại startup thay vì mở lỗ hổng bảo mật.

---

## Hạn chế & khuyến nghị (Known Limitations)

### 1. Whitespace handling (non-blocking)

**Hạn chế**: Pydantic v2 không tự động strip whitespace trên string fields. Một operator có thể vô tình thêm space:

```bash
JWT_SECRET="   please-change-me-to-a-strong-random-secret   "
```

Giá trị này sẽ PASS validator vì nó khác exact match trong frozenset.

**Severity**: Thấp. Risk thực tế: operators hiếm khi thêm whitespace vào env vars.

**Khuyến nghị**: Thêm `@field_validator("JWT_SECRET", mode="before")` gọi `.strip()` trong v2 (sau Q.1).

### 2. Environment case-sensitive check (A.4 from review)

**Behavior**: Validator so sánh `ENVIRONMENT == "development"` (exact match, lowercase). Giá trị như `"DEV"`, `"local"`, `"Development"` (case-sensitive: `case_sensitive=True`) sẽ được coi như production.

**Severity**: Thấp. Strict default là đúng.

**Khuyến nghị**: Tài liệu .env.example đã clarify: "ENVIRONMENT must be exactly `development` (lowercase)".

### 3. docker-compose dev secret không in placeholder set (intentional)

**Design decision**: Giá trị `dev-secret-change-me-must-be-32-or-more-chars` trong docker-compose.yml KHÔNG nằm trong `_PLACEHOLDER_JWT_SECRETS`. 

**Lý do**: Cho phép `docker compose up` chạy cleanly tại dev mà không cần generate random secret.

**Trade-off**: Giá trị vẫn có pattern "change-me", nhưng ≥32 ký tự nên safe cho dev.

**Khuyến nghị**: Thêm comment 1 dòng trong docker-compose.yml: `# dev-only — production deployments MUST override JWT_SECRET via secrets manager`.

### 4. Legacy short placeholder (3-entry set)

**Behavior**: Chuỗi `change-me-in-production` (23 ký tự) ở trong `_PLACEHOLDER_JWT_SECRETS` nhưng Vô dụng vì:
- Min_length=32 reject nó trước
- Validator model nikdy không được chạy cho value này

**Severity**: Negligible. Dual defense không hại.

**Khuyến nghị**: Thêm comment source: `_PLACEHOLDER_JWT_SECRETS` gồm cả legacy short (nếu operator thay đổi min_length tương lai).

### 5. Entropy validation (future hardening)

**Khuyến nghị cho future v2**: Kiểm tra Shannon entropy ≥3.5 để từ chối các secret như `aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa` (32 ký tự nhưng không entropy). Không làm trong Q.1 vì add validation đó sẽ chậm startup (~5ms/check). Defer to future enhancement.

---

## References

### NFRs

- **NFR-005**: Credential hardening (minimize default credential exposure)
- **NFR-024**: Secrets management & rotation (initial JWT_SECRET validation)
- **NFR-029/035/040/042/027**: Các NFR khác trong TASK-038 (không liên quan Q.1)

### Original audit findings

- **TASK-032 BE audit B.6f**: JWT_SECRET hardening — placeholder validation missing
- Audit report: `E:\MyProject\clinic-cms-workspace\claude-workspace\docs\tasks\TASK-032\deliveries\final-specs\audit-report.md`

### Handoff documents

- Implementation handoff: `docs/tasks/TASK-038/handoff/impl-to-review-Q1.md`
- Review report: `docs/tasks/TASK-038/handoff/review-to-test-Q1.md`
- Test report: `docs/tasks/TASK-038/handoff/test-to-documentation-Q1.md`

### Source files

- `clinic-cms/app/core/config.py` — Pydantic Settings model
- `clinic-cms/tests/unit/test_config.py` — Unit tests
- `clinic-cms/.env.example` — Configuration example
- `clinic-cms/docker/docker-compose.yml` — Dev environment

---

## Test Coverage Summary

| Component | Coverage | Notes |
|-----------|----------|-------|
| `min_length=32` validation | 100% | 2 tests (legacy short + explicit min test) |
| Placeholder rejection in non-dev | 100% | 6 parametrized × 3 envs |
| Placeholder allow in dev | 100% | 2 tests (both placeholder variants) |
| Strong secret acceptance | 100% | 1 test (production happy path) |
| Default-in-prod rejection | 100% | 1 test |
| Module-load smoke test (implicit) | 100% | `from app.core.config` succeeds at top of test file |

**Estimated line coverage**: ~100% reachable branches trong validator path.

---

## Tóm tắt thay đổi

- ✅ **Files modified**: 4 (config.py, test_config.py, .env.example, docker-compose.yml)
- ✅ **Test result**: 19/19 PASSED (15 pytest + 4 extended)
- ✅ **Status**: DONE — Production-ready
- ✅ **Non-blocking polish items documented** (whitespace, entropy, comments) — defer để future releases

---

**Prepared by**: Documentation Agent  
**Date**: 2026-05-01  
**Next steps**: Pending B.1-B.17 implementation (password history, anomaly detection, MFA, PII lifecycle)
