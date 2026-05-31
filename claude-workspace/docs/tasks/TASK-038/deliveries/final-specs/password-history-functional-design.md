---
id: TASK-038-B1-B4-FD
type: functional-design
title: Chính sách lịch sử mật khẩu + xoay vòng 90 ngày (NFR-027)
scope: TASK-038 B.1-B.4 (Password history + rotation)
status: DONE
date: 2026-05-01
version: 1.0
---

# Thiết kế chức năng — Lịch sử mật khẩu + xoay vòng 90 ngày (NFR-027)

**Trạng thái**: ✅ DONE — B.1-B.4 hoàn thành 2026-05-01  
**Phạm vi**: TASK-038 sub-tasks B.1–B.4  
**Ngôn ngữ**: Vietnamese

---

## Mục đích

Triển khai NFR-027 (Chính sách xoay vòng mật khẩu) nhằm:
- **Ngăn chặn tái sử dụng mật khẩu cũ**: Người dùng không thể sử dụng lại 5 mật khẩu trước đó khi đổi mật khẩu
- **Bắt buộc đổi mật khẩu hết hạn**: Tự động đánh dấu `must_rotate=true` nếu chưa đổi mật khẩu trong 90 ngày
- **Hiển thị cảnh báo giao diện**: Banner trên `ChangePasswordPage` thông báo mật khẩu hết hạn

---

## Phạm vi

### ✅ Hoàn thành (B.1–B.4)

| B.1 | Migration: Bảng `password_history` + cột `user.must_rotate` |
| B.2 | `change_password` API từ chối nếu khớp với 5 hash gần nhất |
| B.3 | Cron job `password_rotation_check` hàng ngày 02:00 UTC; đánh dấu `must_rotate=true` cho > 90 ngày |
| B.4 | FE banner: `ChangePasswordPage` hiển thị "Mật khẩu đã hết hạn — vui lòng đổi mật khẩu" khi `must_rotate=true` |

### 📋 Hoãn lại (không thực hiện trong B.1–B.4)

| Cron audit log | Chưa viết audit entry khi cron đánh dấu `must_rotate` (flag: gap báo cáo bảo mật) |
| Admin override | Không có flag cho phép admin bỏ qua xoay vòng mật khẩu |
| Email thông báo | Không gửi email khi mật khẩu sắp hết hạn hoặc hết hạn |
| Tự động redirect | Nếu `must_rotate` trở thành `true` giữa phiên, không tự động redirect (yêu cầu người dùng đăng nhập lại) |

---

## Thay đổi Schema

### Bảng mới: `password_history`

```sql
CREATE TABLE password_history (
  user_id UUID NOT NULL,
  changed_at TIMESTAMPTZ NOT NULL,
  password_hash TEXT NOT NULL,
  PRIMARY KEY (user_id, changed_at),
  FOREIGN KEY (user_id) REFERENCES "user"(id) ON DELETE CASCADE
);

CREATE INDEX idx_password_history_user_id ON password_history(user_id);
```

**Mục đích**: Lưu trữ lịch sử hash mật khẩu của mỗi người dùng; khi đổi mật khẩu, hash cũ được lưu để kiểm tra tái sử dụng.

### Cột mới: `user.must_rotate`

```sql
ALTER TABLE "user" ADD COLUMN must_rotate BOOLEAN NOT NULL DEFAULT false;
```

**Mục đích**: Cờ nhị phân kích hoạt bởi cron khi `password_changed_at < now() - 90 days`.  
**Quy tắc cập nhật**: 
- Cron `password_rotation_check` (ngày hàng ngày) đặt `true` nếu hết hạn
- `change_password()` đặt `false` sau khi đổi mật khẩu thành công
- Không bao giờ cập nhật thủ công từ API khác

### Cột hiện hữu: `user.password_changed_at`

```sql
-- Không thêm; đã tồn tại từ migration 0005
-- Loại: TIMESTAMPTZ
-- Được cập nhật khi: change_password() hoặc khởi tạo user lần đầu
-- Giá trị mặc định: now()
```

**Ghi chú**: Các user cũ có thể có `password_changed_at = NULL` (trước migration 0005). Cron query không cờ NULL rows, an toàn.

---

## Migration: `0021_password_history_and_rotation`

**Vị trí**: `clinic-cms/alembic/versions/0021_password_history_and_rotation.py`  
**Revision ID**: `0021`  
**Down-revision**: `65fc9ae59ba5` (HEAD trước TASK-038)  
**Loại**: ADDITIVE (không xóa dữ liệu)

### Nội dung

```python
# Down-revision: 65fc9ae59ba5
# Revision: 0021

from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_table(
        'password_history',
        sa.Column('user_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('changed_at', sa.TIMESTAMPTZ(timezone=True), nullable=False),
        sa.Column('password_hash', sa.Text, nullable=False),
        sa.PrimaryKeyConstraint('user_id', 'changed_at'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
    )
    op.create_index('idx_password_history_user_id', 'password_history', ['user_id'])
    
    op.add_column('user', sa.Column('must_rotate', sa.Boolean, nullable=False, server_default='false'))

def downgrade():
    op.drop_column('user', 'must_rotate')
    op.drop_index('idx_password_history_user_id')
    op.drop_table('password_history')
```

### ⚠️ Xung đột Migration: `0021` x 3 stream

| Stream | Migration file | Nội dung |
|--------|----------------|---------|
| **B (hiện tại)** | `0021_password_history_and_rotation.py` | Lịch sử mật khẩu + xoay vòng |
| **A** | `0021_multi_clinic_account.py` | Đa clinic trên tài khoản (TASK-033) |
| **C** | `0021_add_mfa_columns_to_user.py` | Cột MFA trên user (TASK-038 B.8–B.14) |

**Vấn đề**: Cả ba stream đều yêu cầu `0021`. Khi merge, Alembic sẽ báo lỗi "multiple revisions with same id".

**Giải pháp (áp dụng tại merge, không phải dùng lúc này)**:
- Không thay đổi bất kỳ file nào hiện tại
- Tại thời điểm merge, manager sẽ đổi tên hai file thành `0021a_*` → `0022_*` và `0021b_*` → `0023_*`
- Hoặc sử dụng UUID revision tự động (Alembic `--autogenerate`)
- Đảm bảo thứ tự tuyến tính: `...0020 → 0021_password_history → 0022_multi_clinic → 0023_mfa`

---

## Hợp đồng API

### Endpoint: `POST /auth/login`

**Phản hồi** (thêm trường):

```json
{
  "access_token": "eyJhbGc...",
  "refresh_token": "...",
  "user": {
    "id": "uuid",
    "email": "user@clinic.local",
    "must_rotate": true
  }
}
```

**Trường mới**: `user.must_rotate: boolean` (mặc định `false`)  
**Ý nghĩa**: `true` → buộc đổi mật khẩu; `false` → mật khẩu còn hiệu lực

---

### Endpoint: `POST /auth/change-password`

**Request**:
```json
{
  "old_password": "...",
  "new_password": "..."
}
```

**Phản hồi thành công** (204 No Content)

**Phản hồi lỗi — mật khẩu khớp lịch sử** (400 Bad Request):

```json
{
  "detail": "Password matches one of your last 5 passwords"
}
```

**Logic kiểm tra**:
1. Xác thực `old_password` (như cũ)
2. Truy vấn `SELECT password_hash FROM password_history WHERE user_id = ? ORDER BY changed_at DESC LIMIT 5`
3. Kiểm tra từng hash cũ với `bcrypt.verify(new_password, old_hash)` → nếu khớp, trả 400
4. Cũng kiểm tra `user.password_hash` hiện tại (chưa lưu vào lịch sử)
5. Nếu không khớp, lưu hash hiện tại vào `password_history`, cập nhật `user.password_hash = new_hash`, đặt `must_rotate = false`

**Hiệu ứng phụ**: `must_rotate` được đặt `false` → tự động hủy bỏ flag hết hạn

---

## Cron Job: `password_rotation_check`

**Vị trí BE**: `clinic-cms/app/workers/jobs/password_rotation.py`  
**Lịch**: Hàng ngày 02:00 UTC  
**Chu kỳ**: 1 lần/ngày

### Logic

```python
async def password_rotation_check() -> dict:
    """
    Đánh dấu must_rotate=true cho user có password_changed_at < now() - 90 days
    """
    query = """
    UPDATE "user" 
    SET must_rotate = true 
    WHERE 
      is_deleted = false 
      AND must_rotate = false 
      AND password_changed_at IS NOT NULL 
      AND password_changed_at < now() - interval '90 days'
    RETURNING id
    """
    # Thực thi, log kết quả (số user đánh dấu, lỗi, v.v.)
    # Trả về dict với tóm tắt: {"users_flagged": 42, "errors": []}
```

### Đăng ký Cron

**Vị trí**: `clinic-cms/app/workers/scheduler.py`

```python
WorkerSettings.cron_jobs = [
    cron(password_rotation_check, hour=2, minute=0),  # Mỗi ngày lúc 02:00 UTC
    # ... cron jobs khác
]

WorkerSettings.functions = [
    password_rotation_check,  # Đăng ký callable
    # ... functions khác
]
```

### Các trường hợp cạnh tranh / an toàn

| Trường hợp | Xử lý | Kết quả |
|-----------|-------|--------|
| Concurrent cron runs | Cron không được chạy song song (worker lock) | ✅ An toàn |
| User tương tác lúc cron chạy | UPDATE thêm `WHERE must_rotate = false` → nếu user vừa đổi MK (cron set `true`, user set `false`), cron không ghi đè | ✅ An toàn |
| User có `password_changed_at = NULL` | SQL `NULL < timestamp` → `UNKNOWN` (không match) → không đánh dấu | ✅ An toàn (nhưng user cũ không bao giờ bị yêu cầu xoay) |
| Múlt user hết hạn cùng lúc | UPDATE ... WHERE ... RETURNING COUNT | ✅ Atomic |

### ⚠️ Khoảng trống: Không viết audit log

Khi cron đánh dấu `must_rotate=true`, **không có entry audit được tạo**. Lý tưởng là:
- Tạo entry `action="user.password_rotation_check"`, `user_id=<id>`, `metadata={"flagged": true}`
- Hoặc một entry tóm tắt: `action="password_rotation_check.batch"`, `metadata={"count": 42}`

Đây là **khoảng cách bảo mật** — nên bổ sung trong tương lai (không blocking cho B.1–B.4).

---

## Banner FE: `ChangePasswordPage`

**Vị trí**: `clinic-cms-web/src/pages/auth/ChangePasswordPage.tsx`

### Render

```tsx
import { AlertTriangle } from 'lucide-react';

export function ChangePasswordPage() {
  const { user } = useAuthStore();
  const mustRotate = Boolean(user?.must_rotate);
  
  return (
    <div className="container mx-auto py-8">
      {mustRotate && (
        <div 
          role="alert" 
          className="mb-4 flex items-start gap-3 rounded-lg bg-amber-50 border border-amber-200 px-4 py-3"
          data-testid="password-expiry-banner"
        >
          <AlertTriangle 
            className="text-amber-600 flex-shrink-0 mt-0.5" 
            size={20}
            aria-hidden="true"
          />
          <div>
            <h3 className="font-semibold text-amber-900">
              Mật khẩu đã hết hạn
            </h3>
            <p className="text-sm text-amber-800 mt-1">
              Vui lòng đổi mật khẩu để tiếp tục sử dụng ứng dụng
            </p>
          </div>
        </div>
      )}
      
      <div className="rounded-lg bg-white shadow p-6">
        {/* Form đổi mật khẩu */}
      </div>
    </div>
  );
}
```

### Xử lý lỗi

Khi `change_password` API trả lỗi 400 chứa `"last 5"`, banner xử lý:

```tsx
if (error.detail?.includes("last 5")) {
  // Hiển thị thông báo custom: "Mật khẩu này đã được sử dụng gần đây"
  setErrorMessage(t('auth:changePassword.errors.passwordInHistory'));
}
```

### Tương thích i18n

| Key | Tiếng Anh | Tiếng Việt |
|-----|----------|-----------|
| `auth:changePassword.errors.passwordInHistory` | "Password has been used recently" | "Mật khẩu này đã được sử dụng gần đây" |

---

## Quy tắc đặt tên trường: `must_rotate` (BE + FE thống nhất)

Sau khi manager sửa B.1–B.4:

| Thành phần | Trước | Sau | Ghi chú |
|-----------|-------|-----|---------|
| **BE API response** | `password_expired` (sai) | `must_rotate` | Khớp với tên cột DB |
| **FE `authStore.ts`** | `must_rotate?` | `must_rotate?` | Không thay đổi |
| **FE `ChangePasswordPage`** | `user.must_rotate` | `user.must_rotate` | Không thay đổi |
| **BE schema** | `password_expired` | `must_rotate` | Khớp response |

**Kết quả**: BE + FE đều sử dụng `must_rotate` → banner sẽ render đúng khi đăng nhập.

---

## Độ phủ kiểm thử

### BE Unit Tests: 16/16 ✅ PASS

| Test file | Test cases | Tất cả |
|-----------|-----------|--------|
| `test_password_history.py` | 10 | ✅ PASS |
| - `test_matches_last_5_returns_400` | — | ✅ |
| - `test_oldest_password_reusable_after_trim` | — | ✅ NEW |
| - `test_accepts_valid_new_password` | — | ✅ |
| - (+ 7 others) | — | ✅ |
| `test_password_rotation.py` | 6 | ✅ PASS |
| - `test_cron_flags_old_passwords` | — | ✅ |
| - `test_cron_skips_null_changed_at` | — | ✅ |
| - (+ 4 others) | — | ✅ |

### BE Integration Tests: 4/4 ✅ PASS (1 skipped)

| Test | Kết quả | Ghi chú |
|------|--------|--------|
| `test_change_password_no_auth_returns_401` | ✅ PASS | |
| `test_change_password_wrong_old_password_returns_401` | ✅ PASS | |
| `test_change_password_correct_old_password_returns_204` | ✅ PASS | |
| `test_password_matches_history_returns_400` | ✅ PASS | B.2 NFR-027 |
| `test_missing_new_password_returns_422` | ⏭️ SKIP | Env limitation: cần live Postgres (không blocking) |

### FE Unit Tests: 535/535 ✅ PASS

| Suite | Tests | Kết quả |
|-------|-------|--------|
| `ChangePasswordPage.test.tsx` | 6 | ✅ PASS |
| - Banner render khi `must_rotate=true` | — | ✅ |
| - Banner ẩn khi `must_rotate=false` | — | ✅ |
| - Accessible: `role="alert"` | — | ✅ |
| - (+ 3 others) | — | ✅ |
| **Toàn bộ FE suite** | 535 | ✅ PASS (50 test files) |

---

## Các quyết định thiết kế

1. **Kiểm tra lại ngay mật khẩu hiện tại**: `change_password()` kiểm tra cả `user.password_hash` hiện tại + 5 entries lịch sử → tổng cộng ngăn chặn tái sử dụng 6 mật khẩu gần nhất (hiện tại + 5 trước).

2. **`must_rotate` được xóa khi đổi thành công**: Sau `change_password()` thành công, `must_rotate = false` → người dùng không cần thực hiện lại, không bị redirect buộc.

3. **Cron idempotent**: Mệnh đề `WHERE must_rotate = false` ngăn các cập nhật dư thừa → an toàn cho cron chạy hàng ngày.

4. **Lịch sử được trim sau insert**: Sau khi thêm entry mới, xóa các entry cũ ngoài top-5 → bảng giới hạn kích thước, tối ưu query.

5. **Banner không tự động redirect**: Nếu `must_rotate` trở `true` giữa phiên (cron chạy), không có cơ chế redirect tự động từ `/dashboard` → yêu cầu người dùng đăng nhập lại để lấy flag trong JWT. Hợp lý cho B.1–B.4 (cron hàng ngày, không tức thời).

---

## Những vấn đề / Flags còn lại

### 🔴 CRITICAL: Xung đột migration `0021` (không phải sửa bây giờ)

Ba stream (A, B, C) cùng claim revision `0021`. **Cần renumbering tại merge**:
- **Không sửa lúc này** — để manager/CI quản lý tại thời điểm hợp nhất branches
- **Giải pháp**: `0021` (B) → `0022`, `0021` (A) → `0023`, hoặc tương tự

### 🟡 Flag: Không viết audit log cron

`password_rotation_check` không tạo audit entry. Khuyến cáo:
- Thêm entry batch: `action="password_rotation_check"`, `metadata={"users_flagged": N}`
- Hoặc per-user entries: `action="user.must_rotate_flagged"`
- **Follow-up**: Ghi lại tại PR sau (không blocking B.1–B.4)

### 🟡 Flag: FE forced-redirect trên login bị break

`LoginPage.tsx` line 173 đọc `user.password_expired` để redirect → `/change-password`. Sau rename BE, field hiện là `must_rotate` (tên khác), redirect sẽ không hoạt động.

**Tình trạng**: Banner `ChangePasswordPage` hoạt động (đọc `must_rotate` đúng), nhưng users không được force-redirect lúc login.

**Khuyến cáo**: Sửa `LoginPage.tsx`:
```tsx
if (user.must_rotate) {
  navigate('/change-password');
}
```

### 🟡 Flag: Tailwind classes chưa cập nhật (TASK-039 phối hợp)

Banner sử dụng `bg-amber-50`, `border-amber-200`, `text-amber-600` từ `main` branch. Sau TASK-039 merge (design system indigo), cần:
- Đổi → `bg-indigo-50`, `border-indigo-200`, `text-indigo-600`
- **Ghi chú**: Đã được phác thảo tại review; không cần chuyển bây giờ

---

## Tóm tắt

| Tiêu chí | Kết quả |
|----------|--------|
| **B.1 — Migration** | ✅ `0021_password_history_and_rotation.py` created |
| **B.2 — History rejection** | ✅ `change_password()` rejects matching last 5 hashes (400) |
| **B.3 — Rotation cron** | ✅ `password_rotation_check` daily 02:00 UTC; marks `must_rotate=true` |
| **B.4 — FE banner** | ✅ `ChangePasswordPage` shows "Mật khẩu đã hết hạn" when `must_rotate=true` |
| **Field naming** | ✅ BE + FE both use `must_rotate` (post-manager-rename) |
| **Test coverage** | ✅ 16 BE unit + 4 integration + 535 FE |
| **Audit log** | 🟡 Deferred — no cron audit entry (follow-up item) |
| **Migration conflict** | 🟡 Flagged — `0021` x 3 streams, requires renumbering at merge |
| **Forced redirect** | 🟡 Flagged — `LoginPage` still reads old field name (need fix) |

---

**Phiên bản**: 1.0  
**Hoàn thành**: 2026-05-01  
**Ký**: Documentation Agent (TASK-038 B.1–B.4)
