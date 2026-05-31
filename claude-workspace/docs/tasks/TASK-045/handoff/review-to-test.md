# TASK-045 — VSS BHYT Integration: Review → Test Handoff

**Status**: APPROVED with non-blocking notes
**Decision**: APPROVED
**Date**: 2026-05-01
**Agent**: Code Review
**Inputs**: `impl-to-review.md`, `task.md`, BE @ `clinic-cms-w5v` (feature/task-045-vss-integration), FE @ `clinic-cms-web-w5v` (feature/task-045-vss-integration-fe)

---

## Decision summary

**APPROVED** — pass to Test agent. No blocking defects. Several improvement notes (mostly post-merge wiring + 1 latent React hooks ordering bug that surfaces only after FE feature flag is wired). All 4 stubs are clearly tagged and reasonable for v1.

---

## A. Migration `0029_vss_sync_log` — Pass

| Item | Verdict | Notes |
|---|---|---|
| Table schema (clinic_id FK, sync_type, JSONB payloads, status, error_message, synced_at, synced_by) | ✅ | Matches spec |
| `sync_type` ENUM (CHECK constraint: check_eligibility/submit_claim/pull_status) | ✅ | Text + CHECK (Postgres-friendly, easier to extend than native ENUM) |
| `status` ENUM (CHECK: pending/success/failed/timeout) | ✅ | |
| Composite index `(clinic_id, synced_at DESC)` | ✅ | Matches list-query order — good |
| RLS enabled + FORCE + isolation policy on `current_setting('app.current_clinic_id')` | ✅ | Consistent with project RLS pattern |
| `down_revision="65fc9ae59ba5"` | ✅ | Matches current head |
| Migration ran in Docker | ✅ | Confirmed in handoff |
| 0028 conflict risk vs TASK-038 B.15-B.17 | ⚠️ | No 0028 currently exists in tree; if TASK-038 lands first with a different head, this will need re-stamping. Coordinate at merge. |
| Permission seeding for `vss:read` / `vss:sync` in this migration | ❌ | Comment in routes.py says permissions "will be seeded in migration 0029" but the migration does NOT seed them. Documented stub. Acceptable for v1 (post-TASK-034 follow-up) but **note: prod deployment will 403 every endpoint** until seed happens. |

---

## B. VssClient mock adapter — Pass

| Item | Verdict | Notes |
|---|---|---|
| Result classes (Eligibility/Claim/Status) with `.to_dict()` | ✅ | Clean shape |
| Mock returns realistic v1 data (eligible=True, coverage 80%, CLM-XXXXXXXXXX) | ✅ | |
| TODO v2 comments per method (URL + auth header) | ✅ | Easy to wire later |
| Reads `settings.VSS_API_URL` / `VSS_API_KEY` (config wiring) | ✅ | |
| Error handling (timeout, network failure, malformed) | ⚠️ | Mock cannot fail → no path tested for `VssSyncStatus.TIMEOUT` / `FAILED`. Service has try/except + `_update_log(FAILED)`, so the wiring exists, but no negative test injects an exception from the client. **Test agent: please add a unit test that monkeypatches `vss_client.check_eligibility` to raise, asserts log row goes to `failed`.** |
| Singleton at module level | ⚠️ | Acceptable for v1 mock; for v2 real httpx, prefer a dependency-injected client (so tests can swap easily and the lifecycle is tied to the FastAPI app). Not blocking. |

---

## C. Endpoints — Pass

| Endpoint | Verdict | Notes |
|---|---|---|
| `POST /eligibility-check` (`vss:read`) | ✅ | Validates card length 10–20, dob ISO; writes log; commits |
| `POST /submit-claim` (`vss:sync`) | ⚠️ | **Not idempotent** — same `visit_id` submitted twice creates 2 log rows + 2 random claim IDs. v1 acceptable (mock), but TODO for v2 should call out idempotency-key or unique constraint on `(clinic_id, visit_id, sync_type='submit_claim', status='success')`. Note for Test: deliberately submit twice and document behaviour as "expected v1, v2 must dedup". |
| `GET /sync-log` (filter + pagination) | ✅ | Filters: from/to/sync_type/status, page 1+, page_size 1–100. RLS + explicit `where clinic_id=` is belt-and-braces. |
| `GET /status` | ✅ | Catches all exceptions, returns `connected=false`. Always 200 — good for FE polling. |
| Permission decorators (`vss:read`/`vss:sync`) | ✅ | Correct mapping per endpoint |
| Feature-flag stub on every endpoint | ✅ | Clearly tagged TODO POST-TASK-034 |
| `get_sync_log` filter param `status` aliased to avoid shadowing FastAPI status | ✅ | Good |
| `get_sync_log` `to_dt` boundary inclusive (`<=`) | ⚠️ | If `to_dt` = `2026-12-31T23:59:59`, microsecond ts > that are excluded. Minor edge. Document for Test as "use end-of-day-plus-1 to be safe". |

---

## D. Stub strategy — Pass

All 4 stubs are clearly documented:

1. ✅ `require_feature_stub("bhyt")` — explicit dependency, easy grep, clear TODO comment
2. ✅ `vss:read`/`vss:sync` permissions not seeded — documented in routes.py header + handoff §"Known limitations"
3. ✅ Real VSS HTTP — every method has `TODO v2: <method+URL>` comment, settings wired but unused
4. ✅ FE `useFeatureFlag('bhyt')` stub — both pages have identical `const bhytEnabled = true` with TODO + `NotEnabledFallback` component already coded
5. ✅ FE `PATCH /admin/integrations/vss/config` placeholder — handler swallows errors, surfaces success-toast (acceptable for v1 demo)

**Strategy assessment**: Disciplined. Each stub has (a) a clear inline TODO, (b) the production interface already coded behind the stub, (c) corresponding follow-up in the handoff. No "magic" hardcodes hidden in business logic.

---

## E. FE pages — Pass with 1 latent bug

### `VssIntegrationConfigPage`
| Item | Verdict | Notes |
|---|---|---|
| Connection status panel + recheck button | ✅ | |
| Form fields (API URL, API Key masked, Facility code) | ✅ | API key uses `type=password` with eye-toggle |
| Save + Test connection buttons | ✅ | |
| Indigo MediZen tokens (`indigo-50/100/600/700`, `emerald-500`, `red-500`) | ✅ | |
| Vietnamese-first labels via `t()` namespace `vss` | ✅ | |
| **Hooks order** | ❌ | `if (!bhytEnabled) return <NotEnabledFallback />` is placed BEFORE the `useState` calls. Currently harmless because `bhytEnabled` is a constant `true`. **After TASK-034 merge**, when `useFeatureFlag('bhyt')` returns a value that can flip across renders, this violates Rules of Hooks (different hook count between renders → React crash). **Fix at merge time**: move all `useState` ABOVE the early return. Same issue in `VssSyncLogPage`. Flag this as a follow-up in the post-TASK-034 wiring task, not blocking v1. |

### `VssSyncLogPage`
| Item | Verdict | Notes |
|---|---|---|
| Filter bar (from/to/type/status), page reset on filter change | ✅ | |
| Table with synced_at / type / status / patient ref / detail btn | ✅ | |
| Status badges (emerald/red/amber/orange) per spec | ✅ | |
| Detail modal with collapsible JSON viewers (request/response) | ✅ | |
| Pagination (only when total > page_size) | ✅ | |
| `data-testid` coverage | ✅ | Excellent — Test agent will have an easy time |
| Date formatting `toLocaleString('vi-VN')` | ✅ | |
| Same hooks-order issue as Config page | ❌ | See above |

---

## F. Permission gating — Pass

- `vss:read` / `vss:sync` strings used consistently in BE routes + FE Sidebar nav-items. ✅
- Sidebar entries are inside the `key:"admin"` group → matches expected `ROLE_NAV_SECTIONS` admin grouping. ✅
- Permission-not-seeded TODO clearly flagged. ⚠️ post-merge.

---

## G. i18n — Pass

| Item | Verdict | Notes |
|---|---|---|
| `vss` namespace registered in `i18n.ts` (vi+en, ns array) | ✅ | |
| vi/en parity (key counts match) | ✅ | Tests assert this explicitly |
| `nav` / `config` / `syncLog` / `syncType` / `status` sections | ✅ | |
| Vietnamese-first content quality | ✅ | "Kiểm tra lại", "Lịch sử đồng bộ", "Hết thời gian" — natural |

---

## H. Test quality — Pass with gaps to fill in test phase

| Layer | Coverage | Notes |
|---|---|---|
| BE unit (12 client + 9 sync log = 21) | ✅ | Enums, model columns, log helpers, service happy paths |
| BE integration (13) | ✅ | 422 negatives on all 3 POST/GET endpoints, 200 happy paths via service mock, query param validation |
| FE Vitest (581 across 52 files; 2 new files) | ✅ | i18n parity asserts, render asserts, form behaviour, modal open/close, pagination conditional |
| Negative path: VSS client raises → log = failed | ❌ | **Missing.** Test agent: add this. |
| Negative path: invalid `from`/`to` ISO format → 500 vs 422 | ⚠️ | `datetime.fromisoformat()` raises ValueError → unhandled → 500. **Fix recommendation (non-blocking):** wrap in try/except → 422. Test agent: confirm current behaviour, file as low-severity bug if confirmed 500. |
| RLS verified (other clinics not visible) | ⚠️ | Integration tests bypass RLS (single test clinic, no second-tenant scenario). **Test agent: add a scenario where 2 different `X-Clinic-Id` values are used and verify list-sync-log returns disjoint results.** |
| Idempotency on submit-claim | ❌ | See §C. Document as "expected v1 behaviour" if confirmed. |

---

## I. Security — Notes for Test + future task

| Item | Verdict | Notes |
|---|---|---|
| `VSS_API_KEY` placeholder is "CHANGE-ME-VSS-API-KEY" | ✅ | Not committed real secret |
| API key masked in FE (type=password, eye-toggle) | ✅ | |
| API key NOT echoed in any log | ✅ | Reviewed routes/services — only request_payload (card_no/full_name/dob/visit_id) goes to log |
| **JSONB `request_payload` contains PII** (BHYT card_no, full_name, dob) | ⚠️ | **TASK-037 P2 follow-up**: encrypt-at-rest these JSONB columns OR mask before storing OR retain TTL purge. For v1, acceptable; flag for security review. |
| **JSONB `response_payload` contains PII** (full_name, dob, insurer code, coverage dates) | ⚠️ | Same as above. |
| RLS prevents cross-tenant log read | ✅ | Policy in migration |
| Permission gate prevents unauthorised log read | ✅ | `vss:read` required |

---

## J. Cross-task coordination

| Coord | Action |
|---|---|
| **TASK-034** (BHYT feature flag) merge | (1) Replace `require_feature_stub("bhyt")` → `require_feature("bhyt")` in routes.py. (2) Replace `const bhytEnabled = true` → `useFeatureFlag('bhyt')` in 2 FE pages **AND** move `useState` ABOVE the early return (see §E). (3) Seed `vss:read`/`vss:sync` permissions in TASK-034 migration. |
| **TASK-037 P2** (PII encryption) | Add `vss_sync_log.request_payload` + `response_payload` to encryption scope, OR add a redaction step in the service before write. |
| **TASK-035** (Sidebar role-based nav) | VSS nav items already in `key:"admin"` group with `permission:"vss:read"` — should "just work" with `ROLE_NAV_SECTIONS`. Re-verify after TASK-035 lands. |
| **TASK-038 B.15-B.17** (parallel migration) | If TASK-038 produces 0028 with a different `down_revision`, restamp 0029 → 0030 at merge. Both branches currently target `65fc9ae59ba5`. Trivial relabel + re-run alembic in CI. |

---

## Items for Test agent (must-do)

1. **Negative path**: monkeypatch `vss_client.check_eligibility` to raise → assert log row finalised with `status='failed'` and `error_message` populated.
2. **Idempotency**: POST `/submit-claim` with same `visit_id` twice → document v1 produces 2 distinct log rows + 2 distinct claim IDs (expected v1; v2 must dedup).
3. **RLS isolation**: 2 different `X-Clinic-Id` headers across requests, list `/sync-log` for each, verify disjoint rows.
4. **Boundary**: invalid `from`/`to` ISO string in `/sync-log` → record actual status code (probably 500). If 500, file as low-severity bug.
5. **i18n smoke**: switch `i18n.changeLanguage('en')` and verify all 4 syncType + 4 status badges render English labels.

## Items for Test agent (nice-to-have)

6. e2e screenshot: VssSyncLogPage with detail modal open showing JSON viewer expanded.
7. Verify Sidebar nav items appear only when user has `vss:read` permission.

---

**Verdict**: APPROVED. Forwarding to Test agent. No code changes required for v1; all caveats are post-merge or covered by Test additions above.
