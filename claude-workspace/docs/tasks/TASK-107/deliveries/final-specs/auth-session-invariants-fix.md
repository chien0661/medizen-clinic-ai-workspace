# Thông số kỹ thuật cuối cùng: Cấp độ bất biến của phiên/RBAC (H-5/H-6/H-7)

**Tác tử tài liệu:** Documentation Agent  
**Ngày hoàn thành:** 2026-07-24  
**Trạng thái:** COMPLETED  
**Nhánh:** `fix/TASK-107-auth-session-invariants`

---

## Tóm tắt vấn đề

Clinic CMS đã phát hiện ba lỗi bảo mật quan trọng trong quản lý phiên làm việc và RBAC thông qua E2E testing (TASK-095):

- **H-5**: Vô hiệu hóa tài khoản (`is_active = false`) không thu hồi các access token đang tồn tại — token cũ vẫn trả về dữ liệu (200) tới hết hạn (~ 15 phút)
- **H-6**: Đổi mật khẩu không chấm dứt phiên trước — cả access token cũ và refresh token cũ vẫn hợp lệ tới 7 ngày
- **H-7**: Thu hồi role không loại bỏ quyền có hiệu lực — `revoke_role` chỉ xóa bảng `user_role` cũ, không đồng bộ pivot `account_clinic_role.role_codes`; token cũ và login mới vẫn có quyền

Ba lỗi này nằm trong cùng một vùng (auth middleware, auth service, RBAC service) nên được gộp thành một task duy nhất.

---

## Cơ chế khắc phục

### Chiến lược chung: Version-check via `user.tokens_valid_after`

Thay vì duy trì một blacklist JTI đơn lẻ cho mỗi token, chúng ta sử dụng **một dấu thời gian cutoff duy nhất trên mỗi người dùng** — `user.tokens_valid_after` — và **từ chối mọi JWT có `iat < cutoff`**.

**Ưu điểm:**
- Đơn giản, không yêu cầu theo dõi từng JTI riêng lẻ
- Dễ mở rộng: có thể sử dụng cho bất kỳ hành động nào cần invalidate token (vô hiệu hóa tài khoản, đổi mật khẩu, v.v.)
- Giảm áp lực lưu trữ (một dòng/người dùng thay vì một hàng/token)

**Hạn chế đã biết:**
- JWT `iat` có độ phân giải 1 giây: nếu một token được phát hành và một hành động invalidate cùng xảy ra trong cùng một giây, token đó có thể vẫn sử dụng được (race condition < 1 giây). Đây là hạn chế tiêu chuẩn của các sơ đồ iat-based và được chấp nhận trong thiết kế này.

### Lớp lưu trữ và caching

1. **Nguồn sự thật (DB):** Cột `user.tokens_valid_after` (DateTime with timezone, nullable)
   - Migration 0067 (head) thêm cột này; giá trị NULL = không có cutoff (hành vi không thay đổi cho những tài khoản không được sửa đổi)
   - Additive, fully downgrade-able

2. **Fast-path (Redis):** Khóa `sess:cutoff:{user_id}` 
   - TTL = access token lifetime + 60 giây (mặc định: 15 phút + 60s)
   - Cho phép TenancyMiddleware từ chối access token trong O(1) mà không cần truy vấn DB mỗi yêu cầu
   - **Fail-open on Redis error**: Nếu Redis không có sẵn/lỗi, middleware không từ chối request. Refresh token vẫn được kiểm tra DB-authoritative bất kể Redis. Điều này phù hợp với chiến lược resilience hiện tại (permission cache cũng fail-open).

### Quy tắc enforcement ở ba điểm

#### 1. **TenancyMiddleware** (access token)
```python
# Sau khi xác minh chữ ký/expiry cơ bản
iat = int(payload.get('iat'))
user_id = payload.get('sub')

cutoff_ts = get_session_cutoff(user_id)  # O(1) Redis GET, fail-open
if cutoff_ts is not None and iat < cutoff_ts:
    raise 401 Unauthorized
```
- Chạy trên **mỗi** route được xác thực (global middleware, whitelist chỉ chứa pre-auth endpoints)
- Từ chối ngay lập tức khi access token cũ được phát hiện

#### 2. **auth_service.refresh()** (refresh token)
```python
# Ngoài xác minh chữ ký/expiry cơ bản
iat = int(payload.get('iat'))
user = db.get(User, payload.get('sub'))

if user.tokens_valid_after is not None:
    cutoff_epoch = int(user.tokens_valid_after.timestamp())
    if iat < cutoff_epoch:
        raise 401 Unauthorized
```
- Kiểm tra DB-authoritative vì refresh token có tuổi đến 7 ngày (vượt quá TTL Redis)
- Không phụ thuộc vào Redis; luôn có trong dòng code

#### 3. **require_permission()** (RBAC re-evaluation)
- Mỗi yêu cầu được xác thực gọi `get_user_effective_permissions(user_id)`, hợp nhất:
  - `user_role` (bảng cũ, clinic-scoped) → `Role.permissions`
  - `account_clinic_role.role_codes` (pivot, mới) → các `Role.code` được merge thành `Role.permissions`
- Thu hồi role loại bỏ nó khỏi **cả hai** bảng, vì vậy `get_user_effective_permissions` sẽ không trả về quyền đó
- Với fail-secure default (deny if not found), token cũ ngay lập tức bị từ chối cho bất kỳ endpoint nào yêu cầu quyền bị thu hồi

---

## Chi tiết khắc phục từng lỗi

### **H-5: Vô hiệu hóa tài khoản → token cũ bị từ chối (401)**

**File thay đổi:** `app/modules/users/services/user_service.py`, `app/core/token_blacklist.py`, `app/core/tenancy.py`

**Luồng:**
1. `user_service.update_user()` phát hiện chuyển đổi `is_active: true → false`
2. Gọi `set_session_cutoff(user_id, now)` để cập nhật Redis + stamping `user.tokens_valid_after = now`
3. Bất kỳ yêu cầu sắp tới với access token cũ được TenancyMiddleware từ chối
4. Token đó vẫn không thể được refresh (nếu cũng cũ) vì `refresh()` kiểm tra DB

**Kế hoạch khôi phục:** Tái kích hoạt tài khoản (`is_active: true`) không xóa cutoff. Điều này là chính xác: token từ trước lần vô hiệu hóa vẫn vô giá trị; login mới (iat > cutoff) sẽ hoạt động.

---

### **H-6: Đổi mật khẩu → access cũ (401) + refresh cũ (401)**

**File thay đổi:** `app/modules/auth/services/auth_service.py`

**Luồng:**
1. `change_password` và `password_reset` gọi `_apply_new_password(user_id, hashed_pw, new_salt)`
2. `_apply_new_password` cập nhật bảng `user`, stamp `tokens_valid_after = now`, và gọi `set_session_cutoff()`
3. **Old access token** (trong 15 phút tiếp theo): TenancyMiddleware từ chối ngay (iat < cutoff)
4. **Old refresh token** (7 ngày): nếu được gọi `refresh()`, bị từ chối trong `refresh()` (iat < tokens_valid_after)
5. **New credentials**: Tạo login mới, phát hành token mới với iat > cutoff → hoạt động bình thường

**Cụ thể về migration 0067:**
- Thêm cột `tokens_valid_after DateTime(timezone=True)` vào `user` (nullable)
- Không có dữ liệu hiện tại cần cập nhật (NULL = không có cutoff)
- Downgrade sạch sẽ (xóa cột)

---

### **H-7: Thu hồi role → pivot được đồng bộ + cả token cũ/login mới bị 403**

**File thay đổi:** `app/modules/users/services/rbac_service.py`, `app/modules/users/models/account_clinic_role.py`

**Thiết kế:** Clinic CMS hỗ trợ hai cách gán role:
- **Legacy:** `user_role` (bảng cũ, clinic-scoped)
- **Pivot:** `account_clinic_role.role_codes` (ARRAY, mới, clinic-scoped với một hàng mỗi clinic)

Cả `get_user_effective_permissions(user_id, clinic_id)` đều hợp nhất từ cả hai bảng.

**Lỗi cũ:** `revoke_role()` chỉ xóa từ `user_role`, để pivot nguyên vẹn → quyền vẫn áp dụng.

**Khắc phục:** `revoke_role()` hiện:
1. Xóa hàng `user_role` nếu tồn tại
2. **Mới:** Loại bỏ `role.code` từ `account_clinic_role.role_codes` trong:
   - Clinic role (`clinic_id = {clinic_id}`): hàng riêng cho clinic đó
   - System role (`clinic_id IS NULL`): tất cả các hàng của người dùng (vì system role áp dụng ở mọi nơi)
3. Gọi `invalidate_user_cache(user_id, clinic_id=None)` → xóa permission cache trên **tất cả** clinic (không clinic = mọi clinic)
4. Tăng `assignment_not_found` chỉ khi người dùng không từng giữ role qua bất kỳ cách nào

**Kết quả:**
- **Old access token:** Mỗi yêu cầu (sau khi gọi `revoke_role()`) chạy `require_permission()` → `get_user_effective_permissions()` không tìm thấy quyền bị thu hồi → 403
- **Fresh login:** Mật khẩu vẫn hợp lệ, nhưng quyền không có → các endpoint yêu cầu quyền đó → 403

---

## Acceptance Criteria (kết quả xác thực)

Tất cả ba tiêu chí được **xác nhận với DB Postgres thực + Redis** (xem [test-report.md](../test-reports/test-report.md)):

- ✅ **H-5:** Tài khoản vô hiệu hóa → access token cũ → **401** ngay lập tức
- ✅ **H-6:** Đổi mật khẩu → access cũ **401** AND refresh cũ **401** (new creds work)
- ✅ **H-7:** Pivot role revoke → old token **403** AND fresh login **403** (pivot DB cleared)

**Thống kê kiểm tra:**
- 3/3 acceptance pass
- 13 pre-existing failures (không liên quan đến TASK-107) xác nhận giống hệt trên baseline `origin/dev`
- **Zero regressions mới**

---

## Danh sách file thay đổi

### Migration
- `alembic/versions/0067_user_tokens_valid_after.py` (NEW)
  - Thêm `user.tokens_valid_after DateTime(timezone=True)` nullable
  - Single head (chỉ 0067 revises 0066; không có branch conflicts)

### Backend
- `app/modules/users/models/user.py`
  - Thêm cột SQLAlchemy `tokens_valid_after`

- `app/core/token_blacklist.py`
  - Hàm mới `set_session_cutoff(user_id, cutoff_datetime)` — set Redis key + floor to seconds
  - Hàm mới `get_session_cutoff(user_id)` — get Redis key, fail-open if error

- `app/core/tenancy.py`
  - TenancyMiddleware: thêm kiểm tra `iat < cutoff` (lines ~222-230)

- `app/modules/auth/services/auth_service.py`
  - `_apply_new_password()` (lines ~767-787): stamp cutoff + `set_session_cutoff()`
  - `refresh()` (lines ~594-601): DB-authoritative `iat < tokens_valid_after` check

- `app/modules/users/services/user_service.py`
  - `update_user()`: phát hiện `is_active true → false`, stamp `tokens_valid_after`, `set_session_cutoff()`

- `app/modules/users/services/rbac_service.py`
  - `revoke_role()` (lines ~443-495): sync pivot + invalidate cache across clinics
  - Pivot update: `role.code` removed từ `account_clinic_role.role_codes` (ARRAY reassignment)

### Tests
- `tests/integration/test_auth_session_invariants_real_db.py` (NEW)
  - Acceptance: H-5, H-6, H-7 (real Postgres + Redis)

- `tests/integration/test_auth_service_coverage.py`
  - Fixture `_make_user` patch: `tokens_valid_after = None` (mocking support)

---

## Ghi chú thiết kế (đã được review chốt)

### Fail-open on Redis error
**Định dạng:** Access tokens được kiểm tra Redis fast-path; nếu Redis lỗi, middleware cho phép request.  
**Lý do:** Phù hợp với chiến lược resilience hiện tại (permission cache cũng fail-open). Refresh token vẫn được kiểm tra DB-authoritative bất kỳ lúc nào.  
**Rủi ro còn lại:** Access token có thể được sử dụng tối đa 15 phút (lifetime) trong một Redis outage.

### Race condition cùng-giây
**Định dạng:** Nếu một token được phát hành và cutoff được stamp trong cùng một giây (same wall-clock second), token đó có thể vẫn được chấp nhận.  
**Tuy sao:**  Một token thường được phát hành vài giây trước khi một hành động invalidate xảy ra, nên token sẽ luôn ở một giây trước và bị từ chối. Lời gọi cutoff flooring rõ ràng (`.replace(microsecond=0)`).  
**Quy trình kiểm tra:** Các acceptance tests `sleep(1.1)` sau khi invalidate trước khi kiểm tra token bị từ chối.

### System-role revocation scope
**Định dạng:** Revoke một system role (`clinic_id IS NULL`) loại bỏ nó khỏi tất cả các clinic của người dùng.  
**Lý do:** System role áp dụng ở mọi nơi (`require_permission` kiểm tra `clinic_id = {clinic_id} OR clinic_id IS NULL`), nên gỡ bỏ ở khắp nơi là chính xác.

---

## Ghi chú bảo mật

### Recommendation: Đổi mật khẩu mặc định `cms_app`
Migration `0004_create_app_role.py` hardcodes mật khẩu Postgres role `cms_app = 'cms_app_change_in_production'`. Đây là một rủi ro bảo mật nếu không được thay đổi trước khi triển khai sản xuất. **Khuyến nghị:** Hãy đổi mật khẩu này thành một giá trị bảo mật cao trước khi triển khai (liên quan TASK-102 — auth infrastructure).

### Không hardcode secrets
- Không có secret hardcoded trong fix này
- Redis và DB credentials được đọc từ biến môi trường (existing setup)
- Logs chỉ sử dụng `user_id` (không phân lộ token/mật khẩu)

### SQL injection prevention
- Tất cả DB queries sử dụng ORM (SQLAlchemy) hoặc parametrized queries
- Không có user input trực tiếp trong SQL
- Giá trị cutoff được tính toán trong Python, không được gọi từ yêu cầu

### Per-request performance
- Access token check: O(1) Redis GET (không DB query)
- Refresh check: O(1) DB column read (từ model người dùng đã được tải)
- Cache invalidation: O(n) where n = số clinic của người dùng (thường là 1-3)

---

## Hướng dẫn triển khai

### Yêu cầu
- Alembic migration 0067 đã chạy (thêm `user.tokens_valid_after`)
- Redis có sẵn (fail-open but faster with Redis)
- Không có thay đổi cấu trúc bảng hiện tại; cột mới nullable và không ảnh hưởng đến hành vi hiện tại

### Bước
1. Deploy migration `0067`
2. Deploy mã thay đổi (auth service, middleware, RBAC service)
3. Không cần khôi động lại: cutoff được áp dụng cho các token mới phát hành ngay lập tức

### Rollback
- Nếu cần khôi phục: migrate down `0067` (xóa cột)
- Mã backend: remove cutoff checks từ middleware/refresh/revoke (reverts to H-5/H-6/H-7 behavior)
- Không có vấn đề data (cột nullable, không có constraint dữ liệu)

---

## Tài liệu tham khảo

- **Implementation handoff:** `docs/tasks/TASK-107/handoff/implementation-to-review.md`
- **Review report:** `docs/tasks/TASK-107/handoff/review-report.md`
- **Test report:** `docs/tasks/TASK-107/deliveries/test-reports/test-report.md`
- **Task tracking:** `docs/tasks/TASK-107/task.md`
- **E2E findings:** `docs/tasks/TASK-095/deliveries/test-reports/full-system-e2e-report.md` (H-5/H-6/H-7)

---

## Kết luận

TASK-107 hoàn tất ba bất biến bảo mật quan trọng:
1. **Vô hiệu hóa tài khoản** chấm dứt ngay các token đang tồn tại
2. **Đổi mật khẩu/reset** chấm dứt tất cả phiên trước
3. **Thu hồi role** loại bỏ quyền tức thời cho cả token cũ và login mới

Cơ chế (version-check via `user.tokens_valid_after` + Redis fast-path) là đơn giản, an toàn, và có thể mở rộng. Tất cả ba acceptance criteria được xác nhận, không có regressions, và quá trình triển khai là sạch sẽ.
