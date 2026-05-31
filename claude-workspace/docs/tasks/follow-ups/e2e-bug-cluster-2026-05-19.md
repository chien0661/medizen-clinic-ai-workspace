# Follow-up Cluster — 2026-05-19 — E2E Bug Sweep

**Status**: READY TO DEPLOY — 6 fixes validated bằng Playwright E2E (129/129 pass, 19s).
**Trigger**: User chạy E2E test → phát hiện 5 fail + 2 flaky → đào ngược root cause → fix triệt để (kể cả bug backend ẩn).
**Repos**: `clinic-cms-merge` (backend, branch `main`), `clinic-cms-web` (frontend, branch `main`).

---

## Tóm tắt fixes

| # | Severity | Loại | Mô tả |
|---|---|---|---|
| 1 | High | Frontend infra | Vite proxy `/api` → backend chưa wire, FE relative call rơi vào Vite → 404 |
| 2 | Low | Outdated test | `auth.spec.ts` dùng `#clinic_code` đã bị xóa (TASK-033) |
| 3 | Low | Outdated test | `auth-debug.spec.ts` cùng issue |
| 4 | Medium | Backend config | Login rate-limit `10/minute` cứng → block test suite chạy |
| 5 | **Critical** | **Backend logic** | `_lock_user` đọc PII trên `User` ORM mà không có `current_clinic_id` ContextVar → 500 trong lockout flow (bị mask bởi rate-limit cũ) |
| 6 | Low | Flaky test | `auth-debug.spec.ts` timeout do `networkidle` + default `actionTimeout` |

**Fix #5 là bug production**: bất kỳ user nào sai mật khẩu đủ N lần (mặc định 5) đều trigger `_lock_user`, đụng PII decryption mà không có tenant context → 500. Trước đây không lộ vì test/người dùng thường bị rate-limit 429 trước khi đụng đến lockout path.

---

## Files touched

### Backend (`clinic-cms-merge`, branch `main`)

```
 app/core/rate_limit.py                       |  6 +++
 app/modules/auth/api/routes.py               |  6 +--
 app/modules/auth/services/auth_service.py    |  2 +-
 app/modules/auth/services/lockout_service.py | 57 +++++++++++++++++++---------
 4 files changed, 49 insertions(+), 22 deletions(-)
```

| File | Change |
|------|--------|
| `app/core/rate_limit.py` | Thêm `LOGIN_RATE_LIMIT = os.getenv("LOGIN_RATE_LIMIT", "10/minute")` |
| `app/modules/auth/api/routes.py` | `@limiter.limit("10/minute")` → `@limiter.limit(LOGIN_RATE_LIMIT)` (2 chỗ: `login` + `mfa_challenge`) |
| `app/modules/auth/services/auth_service.py` | Line 226: `record_failed_attempt(db, None, ...)` → `record_failed_attempt(db, user.clinic_id, ...)` |
| `app/modules/auth/services/lockout_service.py` | `_lock_user` set `current_clinic_id` ContextVar trước khi mở autonomous session; fallback raw-SQL lookup nếu caller pass `None` |

### Frontend (`clinic-cms-web`, branch `main`)

```
 e2e/auth-debug.spec.ts | 20 ++++++++++++--------
 e2e/auth.spec.ts       |  5 ++---
 vite.config.ts         |  8 ++++----
 3 files changed, 18 insertions(+), 15 deletions(-)
```

| File | Change |
|------|--------|
| `vite.config.ts` | Thêm `server.proxy["/api"]` → `process.env.VITE_API_PROXY_TARGET ?? "http://localhost:8001"` |
| `e2e/auth.spec.ts` | Xóa 2 dòng `#clinic_code` fill (TASK-033 cleanup) |
| `e2e/auth-debug.spec.ts` | Xóa `#clinic_code` fill; replace `waitForLoadState("networkidle")` bằng concrete locator; explicit `{ timeout: 1000 }` cho `getByRole("alert").textContent()`; defensive `.catch()` cho `page.content()` |

### Files NOT to commit (local dev only)

- `clinic-cms-merge/docker/docker-compose.override.yml` — alt ports + `LOGIN_RATE_LIMIT=200/minute`. Chỉ dùng khi máy dev đang có project khác chiếm port 5432/6379/8000. Production không cần.

---

## Deployment plan

### Pre-deployment

1. **Backup DB** (snapshot postgres trước khi deploy — fix #5 không phải migration nhưng safety first).
2. **Verify env staging**:
   - Backend container có biến `LOGIN_RATE_LIMIT` chưa? Mặc định `10/minute` nếu unset — production giữ mặc định, không cần set.
3. **Branch & PR**:
   - Backend: PR từ branch fix → `main`, message `fix(auth): bypass tenancy guard in lockout; configurable login rate-limit`.
   - Frontend: PR từ branch fix → `main`, message `fix(e2e): vite proxy /api + TASK-033 cleanup + auth-debug timeouts`.
   - Cả 2 PR phải pass CI trước khi merge.

### Deploy order

**Backend trước, frontend sau** — fix #1 (FE Vite proxy) chỉ ảnh hưởng dev/E2E (production FE gọi backend qua absolute URL, không qua Vite). Backend fix #5 là urgent.

#### Bước 1 — Deploy backend (`clinic-cms-merge`)

```bash
# 1. Merge PR vào main
# 2. Trên host production:
cd /path/to/clinic-cms
git pull origin main
cd docker
docker compose build api worker
docker compose up -d api worker
# 3. Verify:
docker exec clinic_cms_api alembic current  # Schema không đổi, vẫn 0035_audit_read_perm
curl http://localhost:8000/health             # 200
```

**KHÔNG cần chạy migration mới** — fix này thuần code.

#### Bước 2 — Smoke test backend post-deploy

```bash
# Login sai 6 lần một user thật (không phải admin) để verify fix #5
# Trước fix: lần thứ 5 sẽ trả 500
# Sau fix: lần thứ 5 trả 423 (locked_user)
for i in 1 2 3 4 5 6; do
  curl -s -o /dev/null -w "Attempt $i: %{http_code}\n" \
    -X POST https://api.your-domain/api/v1/auth/login \
    -H 'Content-Type: application/json' \
    -d '{"username": "<test_user>", "password": "WrongPassword!!"}'
done
# Expected sequence: 401, 401, 401, 401, 423, 423
# (giá trị chính xác phụ thuộc LOCKOUT_MAX_ATTEMPTS — mặc định 5)

# Sau test: unlock user
docker exec clinic_cms_postgres psql -U cms -d cms \
  -c "UPDATE \"user\" SET is_locked = false, failed_login_count = 0 WHERE username = '<test_user>';"
```

#### Bước 3 — Deploy frontend (`clinic-cms-web`)

Production FE build (Tauri / Vercel) **không bị ảnh hưởng** bởi fix #1 vì proxy chỉ trong dev. Vẫn nên deploy để code align main branch:

```bash
# Tauri desktop:
cd clinic-cms-web
git pull origin main
npm install --silent
npm run tauri:build  # ra bundle mới

# Landing/Web Vercel: trigger redeploy
```

### Verification (post-deploy)

| Kiểm tra | Expected |
|---|---|
| `POST /api/v1/auth/login` valid creds | 200 + access_token |
| `POST /api/v1/auth/login` wrong pass (×5 same user) | 401×4 → 423 (KHÔNG được 500) |
| `POST /api/v1/auth/login` ×11 cùng IP trong 1 phút | 200/401 đầu, 429 từ lần 11 (giữ nguyên policy `10/minute`) |
| API logs grep `EncryptedString` | 0 lần xuất hiện sau deploy |
| Audit log có `user.locked` action khi user bị lock | Có entry với `clinic_id` đúng |

### Rollback

Cả 2 PR đều thuần code, không migration. Rollback = revert PR + redeploy:

```bash
# Backend
cd /path/to/clinic-cms && git revert <commit-sha> && docker compose up -d --build api worker

# Frontend: rebuild từ commit cũ
```

---

## Test evidence

**Trước fix**: 122 passed / 5 failed / 2 flaky / 9 skipped (4.6 phút)
**Sau toàn bộ fix**: 129 passed / 0 failed / 0 flaky / 9 skipped (19 giây)

Run command: `npx playwright test --project=chromium --reporter=list` từ `clinic-cms-web/`.

9 skipped đều là `test.skip()` của tác giả test (không thuộc bug cluster).

---

## Risks & notes

- **Fix #5 thay đổi behavior lockout**: trước đây user trigger lockout đều bị 500, tức là lockout DB record không được tạo (transaction abort). Sau fix, lockout DB record sẽ được commit đúng. Nếu monitoring/alert có rule "spike 500 trên /auth/login" thì rule đó sẽ ngừng kêu — coi như benign.
- **Fix #4 (env var rate-limit)**: production KHÔNG set `LOGIN_RATE_LIMIT` env → giữ nguyên `10/minute`. Chỉ dev/staging có thể nâng cho test purposes. Đặt cao quá ở prod sẽ tăng surface brute-force.
- **Frontend proxy fix #1** chỉ active trong `npm run dev`. Tauri prod build không qua Vite dev server nên không bị ảnh hưởng.
- **Override compose file**: `clinic-cms-merge/docker/docker-compose.override.yml` được tạo trong session E2E. File này **không commit**, chỉ dùng khi máy dev có port conflict.

---

## Liên quan

- TASK-033 — loại bỏ `clinic_code` khỏi login form (tests vẫn còn dấu vết → fix #2, #3)
- TASK-037 P2 — PII encryption migration (fix #5 là follow-up issue của task này)
- BUG-001 — autonomous transaction cho `_lock_user` (fix #5 patch trên cùng function)
