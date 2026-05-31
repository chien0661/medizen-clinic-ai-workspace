---
id: BUG-008
title: TenancyMiddleware ignores JWT khi có X-Clinic-Id (dev override) nhưng không có X-User-Id → 401
severity: Critical
status: OPEN
discovered_in: TASK-049 Phase 2 — receptionist tạo BN, POST /patients 401
url: BE TenancyMiddleware (clinic-cms-merge/app/core/tenancy.py:156-211)
---

# BUG-008: TenancyMiddleware skips JWT user_id when X-Clinic-Id is present without X-User-Id

## Symptom
Mọi authenticated FE call trả 401 "Not authenticated". FE bị `BUG-006` refresh-loop (post-401 → /refresh 200 → retry 401 → loop). 100% authenticated FE flow hỏng.

Repro on `http://localhost:1420/`:
- Login `recept_anh` / `Recept@1234` → 200
- Direct `fetch('/api/v1/patients', { headers: { Authorization: 'Bearer ' + token, 'X-Clinic-Id': clinicId } })` → **401 "Not authenticated"**
- Direct `fetch('/api/v1/patients', { headers: { Authorization: 'Bearer ' + token } })` (no X-Clinic-Id) → **200 + data**
- Direct `fetch('/api/v1/patients', { headers: { Authorization: 'Bearer ' + token, 'X-Clinic-Id': clinicId, 'X-User-Id': sub } })` → **200**

## Root cause (verified)

`clinic-cms-merge/app/core/tenancy.py:156-211`:

```python
if x_clinic:                                  # ← dev override branch
    if not _IS_DEVELOPMENT: 401
    clinic_id = UUID(x_clinic)
    if x_user: user_id = UUID(x_user)
    # ← JWT IS NEVER INSPECTED
else:
    # JWT path: extract both clinic_id AND user_id from claims
    ...
```

→ Khi FE gửi đồng thời `X-Clinic-Id` (dev override) AND `Authorization: Bearer ...`, middleware đi nhánh `if x_clinic`, lấy clinic_id từ header, **không parse JWT**. `user_id` stays None.

→ Downstream `Depends(get_current_user_id)` (FastAPI OAuth2-style) trả 401 "Not authenticated" vì user context rỗng.

FE-side, `clinic-cms-web/src/lib/apiClient.ts:89-91` luôn append `X-Clinic-Id` từ store:

```typescript
if (state.activeClinicId) {
    headers.set("X-Clinic-Id", state.activeClinicId);
}
```

Header này từng cần thiết trước TASK-033 (multi-clinic JWT chưa có `active_clinic_id` claim). Sau TASK-033, JWT đã chứa `active_clinic_id` → `X-Clinic-Id` header dư thừa, và **conflict** với dev-mode logic của TenancyMiddleware.

## Impact (CRITICAL)
- 100% FE authenticated calls 401 (cho mọi role: admin, receptionist, doctor, …)
- Phase 2+ E2E test BLOCKED hoàn toàn (POST /patients fail → không tạo BN → không có flow tiếp)
- Refresh loop tăng tải BE + console noise (BUG-006 là hệ quả của bug này)
- UX: dashboard render "by accident" qua TanStack cache hits từ refresh chuỗi

## Suggested fix

**Option A — BE (preferred, robust)**: trong `tenancy.py:156`, đổi điều kiện để JWT path thắng khi cả Authorization Bearer và X-Clinic-Id cùng tồn tại:

```python
auth_header = request.headers.get("Authorization", "")
has_jwt = auth_header.startswith("Bearer ")

if x_clinic and not has_jwt:
    # dev-mode override path (curl/test only)
    ...
elif has_jwt:
    # JWT path — primary
    ...
else:
    return 401 "Missing or malformed Authorization header"
```

Khi đó: FE luôn gửi cả 2, BE ưu tiên JWT (chứa cả clinic_id + user_id). Dev curl/test không gửi JWT vẫn dùng dev override.

**Option B — FE (simpler, may miss other consumers)**: bỏ `headers.set("X-Clinic-Id", ...)` ở `apiClient.ts:89-91`. Sau TASK-033 active_clinic_id đã trong JWT.

Khuyến nghị **Option A**: đúng kiến trúc + bảo vệ chống regression nếu có FE/Tauri client nào còn dùng X-Clinic-Id legitimately.

## Test gap
- Không có test integration covering "JWT + X-Clinic-Id present together" (dev-mode + JWT mix). Cần thêm vào `clinic-cms-merge/tests/integration/test_dev_header_gating.py`.

## Related
- BUG-005 (FIXED): unrelated — auth refresh PII decryption
- BUG-006: là **hệ quả trực tiếp** của BUG-008 (FE refresh-loop bắt nguồn từ 401 trên mọi authenticated call). Fix BUG-008 sẽ tự đóng BUG-006.
- TASK-033: introduced `active_clinic_id` JWT claim → `X-Clinic-Id` header thành redundant
- TASK-035 F.6: X-Applied-Role header (separate, no overlap)
