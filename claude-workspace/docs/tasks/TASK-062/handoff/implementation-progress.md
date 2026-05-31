# TASK-062 — Implementation progress (increment 1)

**Date**: 2026-05-30 · **Branch**: `fix/TASK-052-test-encryption-fixtures` (user chose to code on current branch) · **Target**: `../clinic-cms-merge`

## Increment 1 — Email infrastructure + visit-completion notify (DONE, tested)

### Done & tested
| Code | Item | Status | Where |
|---|---|---|---|
| INT-001 | Email provider abstraction | ✅ DONE | `app/integrations/email/{__init__,client}.py` — `email_client` singleton, adapters: `console` (dev, logs), `noop` (tests/CI), `smtp` (config-validated; network send stubbed v1, mirrors VSS mock pattern) |
| NOTI-009 | Email templates vi/en | ✅ DONE | `app/integrations/email/templates.py` — registry: `email_verify`, `password_reset`, `staff_invite`, `subscription_reminder`, `generic`; vi default + en, HTML-escaped, vi fallback for unknown lang |
| NOTI-008 | Transactional email send | ✅ DONE | `app/modules/notifications/services/email_service.py` — `send_templated_email()` + `send_bulk()`; never raises on transport failure (returns `EmailSendResult`) |
| NOTI-005 | Visit-completion notify | ✅ DONE | `app/modules/visits/services/visit_service.py::transition_to_complete` — emits `visit.queue_alert` broadcast to clinic when visit → AWAITING_PAYMENT; best-effort (failure can't roll back the clinical transition) |

Config: `app/core/config.py` — added `EMAIL_PROVIDER` (default `console`), `EMAIL_FROM`, `EMAIL_FROM_NAME`, `SMTP_HOST/PORT/USER/PASSWORD/USE_TLS`.

### Tests (all pass in `clinic_cms_w2e_api`)
- `tests/unit/integrations/test_email.py` — 16 tests: adapters (console/noop/smtp config-error/smtp-stub), templates (both langs, vi fallback, escape, unknown key), service (success/render-fail/missing-ctx/bulk).
- `tests/unit/visits/test_visit_complete_notification.py` — 2 tests: completion emits `visit.queue_alert` with correct entity; completion survives a notification failure.
- Regression: `tests/unit/visits` (61) + `tests/unit/notifications` + `tests/unit/integrations/test_email.py` all green; `ruff` clean; `app.main` imports OK. Fixed a pre-existing mock inaccuracy (`db.add` is sync) in `test_visit_service.py`.

## Increment 2 — Event-driven low-stock alert (DONE, tested)

| Code | Item | Status | Where |
|---|---|---|---|
| NOTI-006 | Stock-low event-driven | ✅ DONE (DRIFT→MAPPED) | `app/modules/inventory/services/stock_alert_service.py` — `notify_if_low_stock()` (single-item version of the cron query; same `inventory.low_stock` shape + 24h dedup) + `notify_if_low_stock_safe()` best-effort fan-out. Wired into `pharmacy/services/dispense_service.py` (collects affected items, notifies after decrement) and `inventory/services/adjustment_service.py`. Hourly cron retained as safety net. |

### Tests (increment 2)
- `tests/unit/inventory/test_stock_alert_service.py` — 5 tests: below-min creates, not-below no-op, dedup no-op, safe swallows errors, safe counts.
- **Real-DB regression**: `tests/integration/pharmacy` + `tests/integration/inventory` (23 tests) all pass — confirms the inline low-stock SQL is valid against the live schema and dispense/adjustment flows are unbroken. `ruff` clean; removed a pre-existing unused `Decimal` import in `adjustment_service.py`.

## Remaining
| Code | Item | Status | Note |
|---|---|---|---|
| PLT-024 | Email super admin team | ⚠️ PARTIAL | Send mechanism done (`send_bulk`). Recipient resolution (platform-admin emails) deferred — platform accounts are encrypted `User` rows in a hidden infra clinic (WIP superadmin module); wire once that lands. |
| NOTI-007 | Subscription expiring notify | ❌ BLOCKED | Depends on subscription module (TASK-055) which does not exist. Template `subscription_reminder` is ready; trigger deferred to TASK-055. |

## Status summary
5 of 7 items MAPPED (INT-001, NOTI-005, NOTI-006, NOTI-008, NOTI-009). PLT-024 partial (mechanism ready). NOTI-007 blocked by TASK-055. Event-driven + email infra core of TASK-062 is complete and tested (23 unit tests + 23 real-DB integration regress).

## Notes
- No DB migration in this increment (kept the change migration-free given the dirty worktree + uncommitted `0036_super_admin.py`). An `email_log` audit table (mirroring `VssSyncLog`) is a candidate follow-up for send auditability.
- Real-DB e2e for NOTI-005 (assert notification row after a real visit completion) is a follow-up for the notifications e2e suite; covered at unit level now.
- Parent mapping `api-mapping.md` will be flipped GAP/DRIFT→MAPPED for INT-001/NOTI-005/008/009 when TASK-062 fully completes (avoid partial summary drift).
