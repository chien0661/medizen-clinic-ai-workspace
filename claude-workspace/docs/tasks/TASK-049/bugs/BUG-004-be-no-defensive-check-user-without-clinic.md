---
id: BUG-004
title: BE crash khi login với user thiếu clinic — không có defensive check, có thể là root cause container chết
severity: High
status: OPEN
discovered_in: TASK-049 Phase 1 — sau test login as test_e2e_dr
url: https://ff02-210-245-74-43.ngrok-free.app/api/v1/auth/login
---

# BUG-004: BE crash chain khi user thiếu clinic — Docker daemon dead by side-effect

## Symptom chain

1. Tạo `test_e2e_dr` qua Add User UI → user không có clinic (BUG-003)
2. Login as test_e2e_dr → BE detect "no clinic" → trả về error message friendly OK
3. Sau đó: login admin (đã work trước đó) → trả về 500 "An error occurred"
4. `/api/health` cũng 500
5. Cuối cùng: Docker Desktop service Stopped, WSL distro `docker-desktop` Stopped, pipe `\\.\pipe\dockerDesktopLinuxEngine` không tồn tại

→ Toàn bộ Docker Desktop CRASH.

## Suspected mechanism

- Có khả năng login service raise unhandled exception khi enumerate user.clinics rỗng
- Exception bubble up tới middleware → BE container crash loop
- Docker daemon under heavy crash-loop pressure → WSL2 backend kill
- → Toàn bộ Docker Desktop chết (cascade failure)

OR
- Hot-reload cycle với code agent edit (đã revert) gây deadlock trong async startup
- Combined với thread pool exhaustion từ retry loop

OR
- Coincidence — Docker Desktop có sẵn vấn đề, crash đúng lúc

## Reproduction (cần verify sau khi BE recover)

1. Bring BE up clean
2. Tạo user mới (sẽ rỗng clinic vì BUG-003)
3. Login với user đó nhiều lần liên tiếp (loop 10x)
4. Verify: BE còn sống không? Health check?
5. Verify: admin login còn được?

## Recovery steps đã làm

1. Stop TASK-050 BE seed agent (đang vi phạm scope)
2. Revert agent's BE source changes: `git checkout -- app/core/tenancy.py app/modules/users/api/routes.py app/modules/users/schemas/user_schemas.py app/modules/search/services/search_service.py docker/docker-compose.yml`
3. Kill zombie docker compose processes (PID 17152, 26088 — đã orphan sau khi daemon chết)
4. Launch Docker Desktop GUI để restart daemon
5. Đợi daemon ready, sau đó `docker compose up -d`

## Suggested BE fix

Login service phải have defensive guard:

```python
# In auth service / login endpoint
async def login(payload):
    user = await users.get_by_username(payload.username)
    if not user:
        raise HTTPException(401, "Invalid credentials")
    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(401, "Invalid credentials")
    
    # ✅ Defensive: handle user without clinic
    user_clinics = await user_clinic_repo.list_for_user(user.id)
    if not user_clinics:
        raise HTTPException(403, "Tài khoản chưa được gán phòng khám nào...")
    # ...
```

→ Nếu thiếu try/except hoặc check, một bad data row có thể bring down service.

## Related
- BUG-003: root cause — Add User không assign clinic
- TASK-050 incident: agent edit BE code khi bug này xảy ra → tăng confusion
