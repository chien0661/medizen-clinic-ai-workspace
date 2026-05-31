---
from: code-review
to: test
task: TASK-038
scope: B.5 + B.6 + B.7 (Anomaly Detection Cron — NFR-042)
decision: CHANGES_REQUESTED
date: 2026-05-01
branch: feature/task-038-b5-anomaly-cron
worktree: clinic-cms-w2b
reviewer: code-review-agent
---

# Review Report — TASK-038 B.5–B.7 (Anomaly Detection Cron)

## Decision: CHANGES_REQUESTED

The infrastructure is sound (alerting backends, cron registration, error isolation, test scaffolding all good), but **3 of 4 active SQL rules use action strings that DO NOT match the strings emitted by the codebase audit listener**. As written, those rules will silently produce zero violations in production despite the implementation appearing healthy. This is a CRITICAL correctness gap and must be fixed before testing.

---

## A. SQL Rule Correctness

### A.1 `failed_login_burst` ❌ ACTION STRING MISMATCH (BLOCKING)
- Rule SQL filters `action = 'auth.login.failed'`.
- Production code (`app/modules/auth/services/auth_service.py:130`) emits **`action="user.login_failed"`**.
- Lockout module (`app/modules/auth/services/lockout_service.py:102`) emits `action="user.locked"`.
- Time window (`NOW() - INTERVAL '5 minutes'`) ✅ correct.
- `ip_address IS NOT NULL` filter ✅ correct (column is nullable per `audit_log.ip_address: Mapped[str | None]`).
- `HAVING COUNT(*) > 5` boundary correct (matches threshold ">5", i.e. 6+ triggers).
- **Fix**: change SQL to `action = 'user.login_failed'` (or add an OR-list including `'user.locked'`).

### A.2 `mass_pii_reveal` ❌ ACTION STRING MISMATCH (BLOCKING)
- Rule SQL filters `action = 'patient.read'`.
- Production code (`app/modules/patients/services/patient_service.py:323` via `audit_read`) emits **`action="READ"`** with `entity_type="Patient"`.
- 1-min / >50 threshold may be aggressive: legitimate batch operations (clinic morning roster open, queue refresh) could fire false positives. Recommend documenting baseline observation period before flipping severity to `critical`.
- **Fix**: filter on `action = 'READ' AND entity_type = 'Patient'` (or change `audit_read` to emit `patient.read` — coordinate with audit module owners; the simpler fix is the rule SQL).

### A.3 `sudden_role_grant` ❌ ACTION STRING MISMATCH (BLOCKING)
- Rule SQL JOINs `auth.login.success` with `role.granted`.
- Production code emits **`action="user.login"`** for successful login (auth_service.py:158).
- **No occurrence of `role.granted`** anywhere in `app/` (only inside the rule SQL itself). Need to verify whether RBAC role-grant audit string exists at all — currently appears to be `INSERT`/`UPDATE` via the `__auditable__` SQLAlchemy listener on the role/permission model.
- JOIN logic + `BETWEEN al.login_at AND al.login_at + INTERVAL '5 minutes'` ✅ window math correct.
- Multi-session admin: query allows multiple admin login rows in last 1h; each grant matches every login row whose 5-min window contains it. If admin has 3 logins in 1h, a single grant emits up to 3 rows. ⚠️ Recommend `DISTINCT ON (rg.granting_user_id, rg.target_user_id, rg.grant_at)` to dedupe.
- **Fix**: action strings + dedupe.

### A.4 `mass_export` ❌ ACTION STRING MISMATCH (BLOCKING)
- Rule SQL filters `action LIKE 'export.%'`.
- No `export.*` action emitted anywhere in `app/`. Excel export endpoints (`/attendance/export`, etc.) do **not** call `write_audit` at all. Hence rule will never fire.
- Threshold `>3 in 5 min` is reasonable but only if events get logged.
- **Fix path**: either (a) add `write_audit(action="export.attendance")` style calls in export endpoints (out of scope here, but this rule is non-functional otherwise), or (b) document this as a known follow-up and gate the rule behind a feature flag, or (c) downgrade rule to "deferred" with same TODO treatment as `cross_clinic_access`.

---

## B. Alerting Safety ✅

| Item | Status | Notes |
|------|--------|-------|
| Slack 5s timeout | ✅ | `httpx.AsyncClient(timeout=5.0)` |
| PD 5s timeout | ✅ | Same client |
| Exception isolation | ✅ | `except Exception` in both backends + outer `send_alert`, alerting never crashes cron |
| Slack payload | ✅ | `{"text": ...}` — incoming-webhook-spec compatible |
| PD payload | ✅ | `routing_key`, `event_action: "trigger"`, severity mapped, `custom_details` populated |
| structlog fallback | ✅ | Fires when both env vars unset; uses ERROR level |
| Severity mapping | ✅ | `_PD_SEVERITY` 1:1 for critical/warning/info |

⚠️ Minor: `_send_slack` uses `str(settings.SLACK_WEBHOOK_URL)` — `SLACK_WEBHOOK_URL` is typed `str | None` (not `HttpUrl`) so `str(...)` is a no-op but harmless.

---

## C. Cron Registration ✅

- `WorkerSettings.cron_jobs` includes `cron(anomaly_detection_run, minute={0, 15, 30, 45})` ✅
- `WorkerSettings.functions` includes `anomaly_detection_run` ✅ (Arq requires both)
- Job is `async` and Arq-compatible ✅
- ⚠️ `anomaly_detection_run` creates its own engine via `create_async_engine(settings.DATABASE_URL)` and disposes in `finally`. Other cron jobs may share the global engine — verify against project pattern (`generate_recurring_shifts` etc.). Per-run engine is functionally safe but adds connection-establishment overhead every 15 min. Acceptable but consider switching to shared session factory in a follow-up.

---

## D. Deferred / Placeholder Rule Stubs ✅

- `rule_audit_tamper_detected` returns `[]`, TASK-037 TODO present ✅
- `rule_key_decrypt_anomaly` returns `[]`, TASK-037 Phase 2 TODO present ✅
- `rule_cross_clinic_access` returns `[]`, TASK-033 TODO present ✅
- Integration code samples included as comments — clear handoff for downstream tasks ✅

---

## E. Performance & Scaling ⚠️

- Existing `audit_log` indexes (mig 0002): `(clinic_id, created_at)`, `(entity_type, entity_id)`, `(user_id, created_at)`, `(clinic_id)`.
- **No index on `(action, created_at)`**. All 4 active rules filter on `action = ...` + `created_at >= NOW() - INTERVAL ...`. On a 1M-row audit_log, sequential scan over 5-min slice may still be tolerable due to the `created_at` filter, but a partial index `WHERE action IN (...)` would be ideal.
- 4 queries every 15 min = 16 queries/hour ✅ — negligible.
- **No LIMIT clause** on rule SQL. If a botnet hits with thousands of unique IPs, `failed_login_burst` could return thousands of rows → thousands of `send_alert` calls in a single cron run → Slack/PD rate-limit + log spam. Recommend `LIMIT 50` per rule with `ORDER BY ... DESC` (already present) so worst case is bounded.
- **Recommendation (non-blocking)**: add migration to create partial index `idx_audit_log_action_created_at ON audit_log (action, created_at) WHERE created_at > NOW() - INTERVAL '1 day'` (or simple composite), and add `LIMIT 50` to all 4 rule SQLs.

---

## F. Test Quality ⚠️

| Aspect | Status | Notes |
|--------|--------|-------|
| 16 unit + 2 integration | ✅ | All 18 PASS per handoff |
| Per-rule coverage | ✅ | Each active rule has violation + clean test |
| Boundary tests | ❌ | No test at exactly threshold (e.g. exactly 5 failed logins → must NOT trigger; exactly 6 → must trigger) |
| Mock send_alert verified per violation | ✅ | `test_send_alert_called_per_violation` |
| Integration test isolation | ✅ | UUID-derived unique IPs — clever workaround for append-only audit_log |
| **Action-string regression test** | ❌ | **No test verifies that the action strings emitted by `auth_service`, `audit_read`, etc. actually MATCH what rule SQL queries** — this is exactly the bug surface |
| Slack payload shape verified | ⚠️ | Integration test verifies POST URL but not payload schema; could add JSON shape assertion |

**Critical gap**: integration test inserts rows directly with `action='auth.login.failed'` instead of triggering a real failed-login flow. This means the test passed despite the production action string being `user.login_failed` — false confidence. Before testing, the test agent should add a regression test that calls the real auth flow (or `write_audit` with the actual production action name) and verifies the rule fires.

---

## G. Field Name + Audit Listener Integration ❌ (THE ROOT CAUSE)

Verified action strings emitted by codebase:

| Source | Action string | Rule expects | Match |
|--------|---------------|--------------|-------|
| `auth_service.py:130` (login fail) | `user.login_failed` | `auth.login.failed` | ❌ |
| `auth_service.py:158` (login OK) | `user.login` | `auth.login.success` | ❌ |
| `auth_service.py:255` (refresh) | `user.token_refreshed` | — | n/a |
| `auth_service.py:311` (logout) | `user.logout` | — | n/a |
| `auth_service.py:354` (pwd change) | `user.password_changed` | — | n/a |
| `lockout_service.py:102` | `user.locked` | — | n/a |
| `audit_read` (Patient read) | `READ` (entity_type=`Patient`) | `patient.read` | ❌ |
| RBAC role grant | not found — likely `INSERT`/`UPDATE` via `__auditable__` listener on role model | `role.granted` | ❌ |
| Export endpoints | NO write_audit calls found | `export.*` | ❌ |
| `__auditable__` listener | `INSERT` / `UPDATE` / `DELETE` | — | n/a |
| `merge_service.py` | `MERGE`, `MERGE_UNDO` | — | n/a |

**Conclusion**: The rules were written against an aspirational/spec-doc action-naming convention, not the codebase's actual emitted strings. Implementation must align rule SQL with reality (or alternatively, refactor audit emitters to canonical `{module}.{verb}` form — out of scope for B.5).

---

## H. Implementation Hygiene ✅

- No hardcoded secrets, no debug prints
- Imports are clean and ordered
- Type hints present on public functions (`-> list[dict]`, `-> dict`)
- `# noqa: ARG001` on placeholder `session: Any` parameters — appropriate
- Docstrings adequate; TODO references to TASK-033 / TASK-037 included
- `_RULE_SEVERITY` map has entries for all 7 rule names — even deferred ones — defensive
- `_ACTIVE_RULES` list correctly excludes `cross_clinic_access` while keeping placeholders 5-6 (which return `[]`); this means they execute on every run and contribute zero violations — fine

---

## Summary of Required Changes

**MUST fix before TEST phase**:
1. Update rule SQL action strings to match actual emissions:
   - `failed_login_burst`: `'user.login_failed'`
   - `mass_pii_reveal`: `action='READ' AND entity_type='Patient'`
   - `sudden_role_grant`: `'user.login'` (success); investigate / decide on the role-grant action — the cleanest path is to instrument the role grant service to emit `user.role_granted` (or similar) explicitly and update the rule, OR demote the rule to deferred placeholder until an audit-emission fix lands.
   - `mass_export`: instrument export endpoints to emit `export.attendance`/`export.invoice`/etc. via `write_audit`, OR demote to deferred placeholder.
2. Add regression unit test that asserts the action strings used in rule SQL match the constants emitted by `auth_service`, `audit_read`, etc. (e.g., import the strings from a shared module and reference both there).
3. Add boundary tests (exactly-at-threshold cases).

**SHOULD fix (non-blocking, can defer to follow-up)**:
4. Add `LIMIT 50` to each rule SQL to bound alert spam.
5. Add `DISTINCT ON` or equivalent to `sudden_role_grant` to avoid multi-login duplicate alerts.
6. Add partial composite index `(action, created_at)` on `audit_log` (requires migration — coordinate with concurrent stream merge).

**Migration conflict**: NONE in this stream — confirmed `git status` shows only `app/core/config.py`, `app/workers/scheduler.py`, and 4 new files. No alembic version added. Clean re: migration ordering.

---

## Files Reviewed

- `app/workers/jobs/anomaly_detection.py` — 325 lines
- `app/core/alerting.py` — 112 lines
- `app/core/config.py` — diff: +2 settings
- `app/workers/scheduler.py` — diff: +1 import, +1 function entry, +1 cron job
- `tests/unit/test_anomaly_detection.py` — 374 lines
- `tests/integration/test_anomaly_alerting.py` — 187 lines

Cross-checked against:
- `app/core/audit.py` — listener emits `INSERT`/`UPDATE`/`DELETE`/`READ`
- `app/modules/auth/services/auth_service.py` — emits `user.login*` actions
- `app/modules/auth/services/lockout_service.py`
- `app/modules/patients/services/patient_service.py`, `merge_service.py`
- `app/modules/audit/models/audit_log.py` — schema + nullability
- `alembic/versions/0002_create_audit_log.py` — indexes

---

**Next step**: route back to `code-implementation` for action-string fixes, then re-review.
