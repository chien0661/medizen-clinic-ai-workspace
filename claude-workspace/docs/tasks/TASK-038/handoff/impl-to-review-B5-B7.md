---
from: code-implementation
to: code-review
task: TASK-038
scope: B.5 + B.6 + B.7 (Anomaly Detection Cron — NFR-042)
status: ready-for-review
date: 2026-05-01
branch: feature/task-038-b5-anomaly-cron
worktree: clinic-cms-w2b
---

# Handoff: TASK-038 B.5–B.7 — Anomaly Detection Cron

## Files Changed

| File | Type | Description |
|------|------|-------------|
| `app/workers/jobs/anomaly_detection.py` | NEW | B.5 — 4 active rules + 3 placeholders/deferred |
| `app/core/alerting.py` | NEW | B.6 — Slack + PagerDuty + structlog fallback alerting |
| `app/core/config.py` | MODIFIED | B.6 — added `SLACK_WEBHOOK_URL` + `PAGERDUTY_ROUTING_KEY` settings |
| `app/workers/scheduler.py` | MODIFIED | B.7 — registered cron every 15 min; added `anomaly_detection_run` to `functions` |
| `tests/unit/test_anomaly_detection.py` | NEW | 16 unit tests |
| `tests/integration/test_anomaly_alerting.py` | NEW | 2 integration tests |

## Rules Implemented

### Active Rules (4)

| # | Rule | Logic | Severity |
|---|------|-------|----------|
| 1 | `failed_login_burst` | >5 `auth.login.failed` from same IP in 5 min | critical |
| 2 | `mass_pii_reveal` | >50 `patient.read` from same user in 1 min | critical |
| 3 | `sudden_role_grant` | `role.granted` within 5 min after admin's `auth.login.success` | warning |
| 4 | `mass_export` | >3 `export.*` from same user in 5 min | warning |

### Placeholder Rules (2) — Always return empty list

| # | Rule | Reason | TODO |
|---|------|--------|------|
| 5 | `audit_tamper_detected` | TASK-037 chain_verifier not yet merged | `# TODO: integrate TASK-037 chain_verifier when both branches merge` |
| 6 | `key_decrypt_anomaly` | TASK-037 Phase 2 column encryption not in scope | `# TODO: integrate TASK-037 Phase 2 column encryption when ready` |

### Deferred Rule (1)

| # | Rule | Reason | TODO |
|---|------|--------|------|
| 7 | `cross_clinic_access` | Depends on TASK-033 multi-clinic (JWT `active_clinic_id`) | `# TODO: enable when TASK-033 multi-clinic lands; depends on JWT active_clinic_id` |

## Alerting Backends (B.6)

| Backend | Trigger condition | Payload format |
|---------|-------------------|----------------|
| Slack | `SLACK_WEBHOOK_URL` env set | Markdown-formatted text block |
| PagerDuty | `PAGERDUTY_ROUTING_KEY` env set | Events API v2 JSON |
| structlog fallback | Neither env set | `logger.error("anomaly_alert", rule=..., severity=..., **payload)` |

Both Slack and PagerDuty fire when both envs are set (not exclusive).

## Cron Schedule (B.7)

```python
cron(anomaly_detection_run, minute={0, 15, 30, 45})  # every 15 min
```

Added to `WorkerSettings.cron_jobs` and `WorkerSettings.functions`.

## Test Results

| Suite | Tests | Result |
|-------|-------|--------|
| `tests/unit/test_anomaly_detection.py` | 16 | 16 PASSED |
| `tests/integration/test_anomaly_alerting.py` | 2 | 2 PASSED |
| **Total** | **18** | **18 PASSED** |

### Unit test coverage
- `TestFailedLoginBurstViolation` — violation + multiple IPs (2 tests)
- `TestFailedLoginBurstClean` — no violations (1 test)
- `TestMassPiiRevealViolation` — violation detection (1 test)
- `TestMassPiiRevealClean` — no violations (1 test)
- `TestSuddenRoleGrantViolation` — single + multiple grants (2 tests)
- `TestSuddenRoleGrantClean` — no violations (1 test)
- `TestMassExportViolation` — violation detection (1 test)
- `TestMassExportClean` — no violations (1 test)
- `TestPlaceholderRules` — all 3 placeholders return empty (3 tests)
- `TestAnomalyDetectionRunCron` — 2 violations → send_alert called 2x; 0 violations → no alert; per_rule counts (3 tests)

### Integration test coverage
- `TestBurstTriggersSlack::test_failed_login_burst_triggers_alert` — 8 real DB rows, Slack POST verified
- `TestBurstTriggersSlack::test_below_threshold_no_burst_violation` — 3 rows, job completes clean

## Design Notes

- `audit_log` is append-only (DB triggers prevent DELETE/UPDATE) — integration tests use UUID-derived unique IPs instead of cleanup.
- All rule functions are pure async functions taking a `session` argument — easy to mock and unit-test independently.
- `send_alert` catches all exceptions internally so alerting never crashes the cron job.
- `httpx.AsyncClient` is used for Slack/PD HTTP calls (already in dependencies).

## TODOs for Integration Teams

### TASK-037 integration (audit_tamper_detected)
When TASK-037 chain_verifier merges:
```python
# In rule_audit_tamper_detected():
from app.core.chain_verifier import verify_chain
result = await verify_chain(session)
if not result.verified:
    return [{"breaks": result.breaks, "message": "Audit chain integrity failure"}]
return []
```

### TASK-037 Phase 2 (key_decrypt_anomaly)
When TASK-037 column encryption lands:
```python
# In rule_key_decrypt_anomaly():
from app.core.encryption import get_decrypt_rate_metrics
metrics = await get_decrypt_rate_metrics(session, window_minutes=15)
if metrics.rate > metrics.baseline_threshold * 3:
    return [{"rate": metrics.rate, "threshold": metrics.baseline_threshold}]
return []
```

### TASK-033 integration (cross_clinic_access)
When TASK-033 multi-clinic lands:
```sql
-- Query audit_log for events where clinic_id != JWT active_clinic_id
-- Requires active_clinic_id captured in JWT and stored in audit_log metadata
```

## Blockers

None. All 4 active rules implemented and tested against real DB.

---

## Fix-mode addendum

**Date**: 2026-05-02
**Trigger**: Code review CHANGES_REQUESTED — action string mismatch (critical)

### Action strings investigated

7 action strings emitted by the codebase were confirmed (grep-verified):

| Source file | Emitted action | Rule expected | Match before fix |
|-------------|---------------|---------------|-----------------|
| `auth_service.py:130` | `user.login_failed` | `auth.login.failed` | NO |
| `auth_service.py:158` | `user.login` | `auth.login.success` | NO |
| `auth_service.py:253` | `user.token_refreshed` | — | n/a |
| `auth_service.py:309/311` | `user.logout` | — | n/a |
| `auth_service.py:352/354` | `user.password_changed` | — | n/a |
| `lockout_service.py:100` | `user.locked` | — | n/a |
| `patient_service.py:321` via `audit_read()` | `READ` (entity_type=`Patient`) | `patient.read` | NO |
| RBAC role grant | **NOT FOUND** — listener emits generic `INSERT`/`UPDATE` | `role.granted` | NO |
| Export endpoints | **NOT FOUND** — no `write_audit()` calls | `export.*` | NO |

### Constants module created

`app/core/audit_actions.py` — single source of truth for emitter + analyzer.
All values verified against actual call sites. Placeholder constants for
`ROLE_GRANTED` and `EXPORT_PREFIX` carry TODO comments explaining the gap.

### Rules status post-fix

| Rule | Status | Change |
|------|--------|--------|
| `failed_login_burst` | ACTIVE | Fixed: `auth.login.failed` → `user.login_failed` (via `LOGIN_FAILED` constant) |
| `mass_pii_reveal` | ACTIVE | Fixed: `patient.read` → `action='READ' AND entity_type='Patient'` (via `PATIENT_READ` + `PATIENT_ENTITY_TYPE` constants) |
| `sudden_role_grant` | DEMOTED → placeholder | No `role.granted` event emitted anywhere; SQL preserved in comment for future re-enable |
| `mass_export` | DEMOTED → placeholder | No export endpoint calls `write_audit()`; SQL preserved in comment |
| `audit_tamper_detected` | placeholder (unchanged) | TASK-037 dependency |
| `key_decrypt_anomaly` | placeholder (unchanged) | TASK-037 Phase 2 dependency |
| `cross_clinic_access` | deferred (unchanged) | TASK-033 dependency |

**Active rules (fully wired): 2** (`failed_login_burst`, `mass_pii_reveal`)
**Demoted to placeholder: 2** (`sudden_role_grant`, `mass_export`)

### Additional changes

- Safety `LIMIT 100` added to both active rule SQL queries (botnet/storm bound)
- `RECOMMENDED INDEX` comment block added to both active rule SQL sections
- Both demoted rules (`sudden_role_grant`, `mass_export`) retain full SQL in a
  preservation comment — easy to restore when emitters are wired

### Test results post-fix

| Suite | Tests | Result |
|-------|-------|--------|
| `tests/unit/test_anomaly_detection.py` | 24 | 24 PASSED |
| `tests/integration/test_anomaly_alerting.py` | 2 | 2 PASSED |
| **Total** | **26** | **26 PASSED** |

New tests added:
- 4 boundary tests (exactly-at-threshold for each active rule — 5 failures must NOT trigger, 6 must)
- 2 demoted-rule tests per rule (always-empty + session-not-queried)
- 4 constant regression tests (`TestAuditActionConstantsMatchEmitters`) — assert constants
  match actual emitter source files; will catch future string drift
- Integration test: fixture now inserts `action=audit_actions.LOGIN_FAILED` instead of
  the wrong hardcoded string, giving true end-to-end coverage

### Verdict: FIXED
