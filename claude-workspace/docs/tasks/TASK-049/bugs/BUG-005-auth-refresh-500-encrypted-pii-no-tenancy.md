---
id: BUG-005
title: /api/v1/auth/refresh trả 500 — đọc encrypted User PII trước khi TenancyMiddleware set ContextVar
severity: Critical
status: OPEN
discovered_in: TASK-049 Phase 1 — admin login (localhost)
url: http://localhost:8001/api/v1/auth/refresh
---

# BUG-005: /api/v1/auth/refresh 500 — encrypted PII read trước khi tenancy context set

## Symptom
Sau khi POST `/api/v1/auth/login` thành công (200), FE gọi tiếp `/api/v1/auth/refresh` → BE trả **500 Internal Server Error**. FE clear token + redirect về `/#/login`. **Toàn bộ login flow hiện đang broken end-to-end.**

Chuỗi network observed (login admin / Demo@1234):
```
POST /api/v1/auth/login   → 200 OK
POST /api/v1/auth/refresh → 500 Internal Server Error
```

FE App.tsx cũng có lỗi phụ: `TypeError: error?.error?.startsWith is not a function` (defensive code break trên non-string error payload).

## Root cause (verified từ BE log + code)

Stack trace từ `docker logs docker-api-1`:
```
File "/app/app/modules/auth/api/routes.py", line 188, in refresh
File "/app/app/modules/auth/services/auth_service.py", line 511, in refresh
    user = await db.get(User, user_id)
File "/app/app/core/crypto/types.py", line 73, in process_result_value
    raise RuntimeError(...)
RuntimeError: EncryptedString.process_result_value: current_clinic_id ContextVar
is not set. Ensure TenancyMiddleware has run before reading PII columns.
```

Chain:
1. `/api/v1/auth/refresh` ở whitelist trong `app/core/tenancy.py:55` → TenancyMiddleware **skip** việc set `current_clinic_id` ContextVar.
2. `auth_service.refresh()` line 511: `await db.get(User, user_id)` → load User entity → SQLAlchemy trigger `EncryptedString.process_result_value` cho các PII column (TASK-037 Phase 2: User.email, User.full_name, etc.).
3. `EncryptedString.process_result_value` đọc `current_clinic_id` ContextVar để pick DEK → **không có** → raise RuntimeError.

→ **Regression của TASK-037 Phase 2** (PII column encryption rollout). Refresh path không được coordinate với encryption flow.

## Impact (CRITICAL)
- **TOÀN BỘ login flow broken** trên localhost dev. Mỗi login attempt → FE auto-call refresh → 500 → kick user về login.
- Block 100% E2E test (TASK-049) — không có role nào login được, không thể proceed Phase 2+.
- Nếu prod-like env (encrypted PII bật), bug này ship sẽ hỏng auth refresh cho mọi user.

## Files involved
- BE: `clinic-cms-merge/app/modules/auth/services/auth_service.py:494-511` (refresh — đọc `active_clinic_id` từ JWT claim NHƯNG không set ContextVar TRƯỚC khi `db.get(User, ...)`)
- BE: `clinic-cms-merge/app/core/tenancy.py:55` (whitelist `/api/v1/auth/refresh`)
- BE: `clinic-cms-merge/app/core/crypto/types.py:73` (EncryptedString)
- FE: `clinic-cms-web/src/App.tsx:34` (defensive code crash trên non-string error)

## Suggested fix

**Option A — quickest** (BE only, scope = `auth_service.refresh`):
Set `current_clinic_id` ContextVar TRƯỚC khi load User. JWT refresh token đã chứa `active_clinic_id` claim (TASK-033) → service tự pick lên.

```python
# auth_service.py — refresh()
from app.core.tenancy import current_clinic_id

# After parsing claims, BEFORE db.get(User, ...)
if active_clinic_id:
    current_clinic_id.set(active_clinic_id)
# ... then:
user = await db.get(User, user_id)
```

**Option B — robust**: thêm helper `with_tenant_context(clinic_id)` (đã có cho Arq workers — TASK-037) và wrap toàn bộ refresh logic. An toàn cho cả case `active_clinic_id is None`.

**Option C — kiến trúc**: load User qua repository raw query bỏ qua EncryptedString (nhưng nhánh này phức tạp + dễ miss audit).

→ Khuyến nghị **Option B** (consistent với pattern Arq worker đã thiết lập trong TASK-037).

## Test gap
- Tests `clinic-cms-merge/tests/integration/test_auth_refresh*.py` được viết TRƯỚC TASK-037 Phase 2 → khả năng cao test fixture không trigger encrypt path. Cần re-run sau fix + thêm test case "refresh khi User có encrypted PII column".

## Related
- TASK-037 Phase 2: PII column encryption rollout (root regression source)
- TASK-033: JWT `active_clinic_id` claim (đã có sẵn để pick lên)
- BUG-003 (BUG-004): user without clinic — không liên quan trực tiếp nhưng cùng module auth
