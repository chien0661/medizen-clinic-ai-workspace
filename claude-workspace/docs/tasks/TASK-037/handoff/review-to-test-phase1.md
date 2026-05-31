# TASK-037 Phase 1 — Code Review Report (Review → Test handoff)

**Date**: 2026-05-01
**Reviewer**: Code Review Agent
**Branch**: `feature/task-037-hash-chain` (worktree `clinic-cms-w2a`)
**Implementation handoff**: `docs/tasks/TASK-037/handoff/impl-to-review-phase1.md`
**Decision**: **CHANGES_REQUESTED** (1 BLOCKER, 3 HIGH, 4 MEDIUM, 3 LOW)

---

## A. Trigger correctness

| Item | Status | Notes |
|---|---|---|
| Reads latest `row_hash` correctly | ⚠️ | `SELECT row_hash FROM audit_log ORDER BY chain_seq DESC LIMIT 1` — works, but **NO `FOR UPDATE`** lock, see HIGH-1 |
| Computes `row_hash = sha256(prev_hash \|\| canonical_json)` | ✅ | Matches Python verifier |
| Rejects INSERT on `prev_hash` mismatch | ⚠️ | The check fires only if caller-supplied `prev_hash IS NOT NULL`. Application code passes `NULL` (falls through to default sentinel `'0'*64`), so the anti-tamper guard is effectively **only against direct SQL writers**. Acceptable for the threat model but worth documenting. |
| Concurrency guarantee | ❌ | **HIGH-1 — race window**. Two concurrent INSERTs both run `SELECT … LIMIT 1` in their own snapshot, both see the same `latest_hash`, both compute valid hashes against it, both commit. Result: **chain branch** — verifier later reports a break for the second-committed row because its stored `prev_hash` won't equal the previous (by `chain_seq`) row's `row_hash`. PostgreSQL row-level locks do **not** auto-serialise here. Fix options: (a) `SELECT … FOR UPDATE` on the latest row, (b) `LOCK TABLE audit_log IN EXCLUSIVE MODE` (heavy), (c) acquire `pg_advisory_xact_lock(3700221)` inside the trigger. Option (c) is cheapest. |

## B. Canonical JSON

| Item | Status | Notes |
|---|---|---|
| Deterministic key ordering | ⚠️ | `jsonb_build_object()` → `jsonb` → `::text` produces deterministic output **for jsonb** (PG sorts keys when stringifying jsonb). However, the `old_data` / `new_data` columns are themselves `JSONB` and are nested into the outer object as values; their internal key order is whatever the storage layout chose. Round-trips are stable across PG versions but **MEDIUM-1** if a future PG upgrade changes jsonb output formatting. Recommend adding a regression test that pins the canonical output for a fixed input. |
| NULL handling | ✅ | `jsonb_build_object` represents NULLs as JSON null — consistent both sides |
| Float precision | ✅ (n/a) | No float columns hashed |
| Mismatch risk Python verifier vs PG fn | ⚠️ | Verifier delegates canonicalisation to `fn_audit_row_data_json()` (read same row) so mismatch is impossible **as long as the function is in lockstep with column list**. New columns added by other tasks (e.g. Wave 3-B `applied_role`) will silently NOT be hashed → see HIGH-2 |

## C. Backfill safety

| Item | Status | Notes |
|---|---|---|
| Genesis hash `'0'*64` | ✅ | Standard pattern |
| Advisory lock | ✅ | `pg_try_advisory_lock(3700221)` non-blocking, errors out cleanly |
| Deterministic ORDER BY | ✅ | `(created_at ASC, id ASC)` — UUID tiebreaker handles ms collisions |
| Backfill in same migration transaction | ⚠️ | **MEDIUM-2**. The `DO $$ … $$` block runs in the migration transaction. For a >100k-row audit_log this becomes a multi-minute single transaction holding `pg_advisory_lock` AND blocking schema migration commit. Recommend either (a) running backfill in a separate alembic data migration with autocommit batches of 10k, or (b) at minimum documenting the maintenance-window expectation. For a fresh DB (current test environment, 0 rows) it's a non-issue. |
| Rollback strategy | ❌ | **MEDIUM-3**. If backfill aborts mid-way (PG signal, OOM), the table is left with partial NULL `prev_hash`/`row_hash` values and the migration rolls back. The advisory lock is released by transaction end. Acceptable, but the path is not exercised by any test. Add a recovery doc note: "if backfill fails, downgrade and re-run upgrade". |

## D. Verifier service

| Item | Status | Notes |
|---|---|---|
| Streaming via `batch_size` | ✅ | LIMIT/OFFSET pagination, configurable |
| Memory-bounded | ✅ | Only one batch in memory at a time |
| Returns `chain_seq + expected/stored hashes` | ✅ | Schema matches `ChainBreak` Pydantic |
| `row_id` in break payload | ⚠️ | Implementation handoff promised `row_id` but the dict only has `chain_seq` (no UUID `id`). Useful for forensics — recommend adding `row_id` to the break dict so DBAs can locate the tampered row by PK without joining on chain_seq. **LOW-1**. |
| Performance — 1M rows | ⚠️ | `OFFSET` pagination becomes O(N²) on large tables (each batch re-scans skipped rows). Recommend keyset pagination: `WHERE chain_seq > :last_seq ORDER BY chain_seq LIMIT :batch_size`. **MEDIUM-4**. |
| Continuation logic on break | ✅ | After a break, verifier uses stored `prev_hash` to keep walking — good (avoids cascading false-positives). |

## E. Admin endpoint

| Item | Status | Notes |
|---|---|---|
| `audit:verify` permission required | ✅ | `Depends(require_permission(...))` |
| Permission seeded + granted to admin | ✅ | 0022a migration |
| Body parsing | ✅ | Uses `Body(default_factory=...)` — handoff flag was outdated; current code is correct |
| Async offload for large DBs | ⚠️ | Synchronous; documented in docstring as suitable for ≤1M rows. Defer Arq async variant to follow-up. **LOW-2**. |
| Rate limiting | ❌ | **MEDIUM-5**. Endpoint is expensive (full-table scan + per-row SHA256). No rate limit. Recommend adding `@limiter.limit("5/hour")` per admin user, or at minimum `@limiter.limit("1/minute")`. |

## F. Cron job

| Item | Status | Notes |
|---|---|---|
| Daily 03:00 UTC registered | ✅ | `cron(audit_chain_verify, hour=3, minute=0)` |
| Calls verifier | ✅ | Full scan, batch_size=1000 |
| Alerts on `verified=false` | ✅ | `send_alert(rule="audit_tamper_detected", payload={…})` |
| Stub interface compatible with Wave 2-B | ⚠️ | Stub signature is `async def send_alert(rule: str, payload: dict) -> None`. Acceptable contract, but Wave 2-B's real `alerting.py` may use richer typing (Pydantic models, severity levels). **Coordination flag** — at merge, delete the stub and verify Wave 2-B exposes the same name + signature. |
| Engine pooling | ⚠️ | Cron creates engine per run with `NullPool` — fine for daily-only job but disposes engine in `finally` — **LOW-3**. Consider reusing the worker context engine if Wave 2 adds one. |

## G. Migration conflict

| Item | Status | Notes |
|---|---|---|
| `0022` parent = `65fc9ae59ba5` (not `0021_multi_clinic_account`) | ✅ | Documented; Stream A (multi-clinic) lives on a different branch |
| `0022a` non-conflicting suffix | ✅ | Pattern matches existing `t008a`, `0017a`, `0018a` etc. |
| Wave 3-B (TASK-035) adds `applied_role` column to `audit_log` (migration `0026_audit_applied_role`) | ❌ | **HIGH-2 — Hash gap**. Verified in `clinic-cms-w3b`: TASK-035 adds `audit_log.applied_role`. The `fn_audit_row_data_json()` does not include it → after both branches merge, tampering with `applied_role` would go undetected. **Required follow-up**: when both branches merge, add a migration that recreates `fn_audit_row_data_json` to include `applied_role`, then re-backfill `row_hash` for existing rows (chain restart from a new genesis OR full re-hash with documented break record at the migration timestamp). |
| Merge migration recommendation | ✅ | Handoff already documents the need for a `0022_merge_w1a_w2a` revision when w1a (multi-clinic 0021) lands |

## H. docker-compose port changes

| Item | Status | Notes |
|---|---|---|
| Ports 5433/6380/8001 for worktree isolation | ⚠️ | Reasonable for local dev, but **WARNING — merge conflict surface**. Multiple worktrees (w1a/w2b/w3a/w3b/w3c) likely make similar edits with different port choices. **MEDIUM (already-flagged)**. Recommended: revert this file before merging into `main` and use a `docker-compose.override.yml` per-worktree (uncommitted) or env-var overrides instead. The shipped `docker-compose.yml` should keep canonical ports 5432/6379/8000. |
| `container_name` removed | ✅ | Necessary for parallel `docker compose up` runs across worktrees |

## I. Test quality

| Item | Status | Notes |
|---|---|---|
| 13 unit tests on verifier | ✅ | Empty / 1 row / 5 rows / pagination / tamper-row-hash / tamper-data / tamper-prev-hash / hash helper coverage. Solid. |
| 5 integration tests on endpoint | ✅ | 200 admin, 200 with breaks, 403 non-admin, 401 unauth, schema check |
| Negative DB-level test (trigger rejects bad `prev_hash`) | ❌ | **BLOCKER — missing live-DB test**. Task spec B.2 calls for a DB trigger that "rejects" bad `prev_hash`. No test covers this. The integration tests mock out `verify_chain`, never hitting the trigger. The unit tests don't touch PG. **Required**: add at least one integration test that runs the migration against a real PG, inserts a row, then attempts a manual SQL `INSERT` with a wrong `prev_hash` and asserts an `IntegrityError` with `audit_chain_tamper_detected` in the message. |
| Concurrency test | ❌ | No parallel-INSERT test exists → concurrency hole (HIGH-1) is invisible to CI. Add a test that fires N=10 concurrent `INSERT INTO audit_log` and asserts chain integrity afterwards. **HIGH-3 — required**. |
| Fresh-DB backfill test | ⚠️ | 0-row backfill exercised implicitly by migration; no test asserts ≥1-row backfill correctness end-to-end. Recommend: insert 5 rows (with chain trigger temporarily disabled → ALTER TABLE DISABLE TRIGGER), run backfill SQL, assert verifier returns `verified=true`. **LOW**. |

## J. Performance considerations

- Trigger overhead per INSERT: 1× `SELECT … LIMIT 1` + 1× `digest()` + 1× `jsonb_build_object`. Estimate ~200µs–500µs per insert on warm cache. For typical audit volume (10–100 inserts/sec) this is fine. For mass operations (e.g. seed import of 100k rows) → ~30s–50s overhead. Recommend adding a benchmark in `scripts/bench_audit_chain.py` and documenting baseline (e.g. "1000 sequential inserts in 0.6s").
- INSERT-heavy bulk operations (data import, migrations seeding visits) will bottleneck on the trigger. Consider exposing a documented "trigger-disable + manual rehash" maintenance procedure for bulk loads.
- Verifier on 1M rows with current OFFSET pagination: O(N²) → potentially 5+ minutes. With keyset pagination (MEDIUM-4 fix): O(N) → ~30–60s.

---

## Summary by severity

| Severity | Item | Required for next phase? |
|---|---|---|
| BLOCKER | I-3: Missing DB-level trigger-rejection integration test | **Yes** — add before testing phase signs off |
| HIGH-1 | A: Trigger race condition (no `FOR UPDATE` / advisory lock inside trigger) | **Yes** — add `pg_advisory_xact_lock(3700221)` at top of trigger function |
| HIGH-2 | G: Hash gap — `applied_role` (Wave 3-B) not included in canonical JSON | **Track as follow-up** — fix at merge time, not on this branch |
| HIGH-3 | I: No concurrency test | **Yes** — add parallel-INSERT integration test |
| MEDIUM-1 | B: Pin canonical-output regression test | Recommended |
| MEDIUM-2 | C: Backfill in single transaction risk | Recommended for >100k rows; document for now |
| MEDIUM-3 | C: Rollback recovery doc | Add note in migration docstring |
| MEDIUM-4 | D: OFFSET → keyset pagination | Recommended; required if production audit_log >500k |
| MEDIUM-5 | E: Rate limit on verify-chain endpoint | Recommended |
| LOW-1 | D: Add `row_id` to break payload | Nice-to-have |
| LOW-2 | E: Async offload variant | Defer to follow-up task |
| LOW-3 | F: Engine reuse in cron | Defer |
| WARNING | H: docker-compose port edit will conflict at merge | Document; revert before merge |

---

## Decision rationale

Implementation is **functionally correct for the single-writer case** with strong tamper-resistance via the trigger pattern, deterministic canonical JSON, and clean test coverage of the verifier logic. Blocking issues are:

1. **Concurrency race** (HIGH-1) — the trigger does not serialise concurrent INSERTs, which produces silent chain branches under load. This is a correctness bug for any system with parallel write paths (Arq workers + API handlers).
2. **Missing trigger-rejection test** (BLOCKER) — Task spec B.2 explicitly requires the DB trigger to reject mismatched `prev_hash`. The behavior exists in code but is not exercised by any test.
3. **Hash gap with Wave 3-B `applied_role`** (HIGH-2) — at merge time the chain will silently fail to cover the new column. This must be tracked as a Phase-1.5 follow-up.

Recommend fixing HIGH-1, HIGH-3 and BLOCKER on this branch before promoting to **IN_TESTING**. HIGH-2 can be tracked in TASK-037 task notes as a merge-time follow-up.

**Re-review trigger**: once the three required fixes land + tests added, mark **APPROVED** and hand off to test agent.
