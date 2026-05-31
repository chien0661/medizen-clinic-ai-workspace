# TASK-052 — GAP/DRIFT Backlog → Sub-tasks

> Tách từ `api-mapping.md` (2026-05-30). 85 GAP + 24 DRIFT (109 mục) → 10 sub-task (TASK-054..063).
> Mỗi function code được gán đúng một sub-task. Scope guard TASK-052 giữ nguyên: việc *build* nằm ở các sub-task này.

| Sub-task | Tên | Ưu tiên | #GAP | #DRIFT | Phụ thuộc |
|---|---|---|---:|---:|---|
| [TASK-054](../../TASK-054/task.md) | Billing correctness | High | 5 | 4 | Coordinate BILL-016 (void→reverse stock) với TASK-058 (pharmacy reversal) |
| [TASK-055](../../TASK-055/task.md) | Subscription & clinic lifecycle (provider billing) | High | 27 | 6 | Task lớn (epic) — nên chia phase nội bộ: (1) model+state machine, (2) SubscriptionGuard middleware + read-only mode, (3) admin actions (suspend/reactivate/archive/renew/convert/upgrade) thay cho is_active toggle hiện tại, (4) Arq jobs + reminders, (5) metrics MRR/ARR/churn |
| [TASK-056](../../TASK-056/task.md) | Reports dimensions + exports | Medium | 17 | 1 | batch |
| [TASK-057](../../TASK-057/task.md) | Self-signup & lead funnel | High | 10 | 3 | Phụ thuộc TASK-062 (email infra) cho email verification + invite resend |
| [TASK-058](../../TASK-058/task.md) | Clinical safety & inventory integrity | High | 5 | 1 | Coordinate với TASK-054 BILL-016 (void→reverse stock dùng chung reverse-dispense path) |
| [TASK-059](../../TASK-059/task.md) | Appointments completeness + HR shift integration | Medium | 4 | 2 | Gỡ stub HR shift (slot_service |
| [TASK-060](../../TASK-060/task.md) | Document storage (S3) & attachments | Medium | 4 | 0 | INT-010 S3 là tiền đề chặn PAT-019 / VIS-014 / CFG-002 |
| [TASK-061](../../TASK-061/task.md) | Auth & RBAC gaps | High | 3 | 2 | AUTH-009 forgot-password phụ thuộc TASK-062 (email infra) |
| [TASK-062](../../TASK-062/task.md) | Email infra & event-driven notifications | Medium | 6 | 1 | Nền tảng cho TASK-057 (signup verify), TASK-061 (forgot pw), TASK-055 (subscription reminders) |
| [TASK-063](../../TASK-063/task.md) | Clinic config & platform-admin completeness | Low | 11 | 3 | Nhiều mục nhỏ, độ rủi ro thấp |

## Thứ tự đề xuất

1. **TASK-062** (email infra) — nền tảng, mở khoá 057/061/055
2. **TASK-054** (billing correctness) — rủi ro tiền/kho cao, self-contained
3. **TASK-058** (clinical safety) — an toàn bệnh nhân (dị ứng, hoàn kho)
4. **TASK-061** (auth/RBAC) — bảo mật
5. TASK-057 → 055 → 056 → 059 → 060 → 063
