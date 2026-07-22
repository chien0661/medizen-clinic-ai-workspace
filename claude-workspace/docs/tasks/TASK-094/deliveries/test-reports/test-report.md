# Test Report: TASK-094 - Fix prescription printing (default template + diagnosis) & add usage / dosage-unit fields

**Test Agent:** Test Agent (Sonnet)
**Date:** 2026-07-22 (iteration 1), re-tested 2026-07-22 (iteration 2, post-fix commit `79210c4`)
**Status:** ✅ ALL PASSED (iteration 2) — both bugs from iteration 1 verified fixed and re-tested live as the actual target actors (doctor / admin). One documented, explicitly out-of-scope limitation remains (see "Known Limitation" below) — not a failure.

## RE-TEST — Iteration 2 (2026-07-22, commit `79210c4`)

Re-tested after Code Implementation + Code Review fixed and re-approved BUG-094-001 and BUG-094-002 (branch `feature/TASK-094-rx-print-and-prescribing`, backend worktree `clinic-cms-merge`, commit `79210c4`).

**Confirmed the running API reflected the fix before drawing any conclusion:** restarted the live API container from the branch worktree (bind-mounted, no rebuild needed) and verified directly — `GET /print-templates` with a real `dr_nguyen` (doctor) JWT now returns **200** (was 403); a write attempt (`POST /print-templates`) with the same token still correctly returns 403 (admin-only writes preserved). Confirmed via `grep` inside the running container that `routes.py` now gates the two read routes on `prescription.print`.

**Mid-re-test environment incident:** Docker Desktop's backing WSL2 VM crashed into a read-only filesystem state (`docker restart` on Postgres failed with "read-only file system"; unrelated to any TASK-094 code — matches the documented "Docker Desktop unstable" environment pattern). Recovered per the standard procedure: killed Docker Desktop, `wsl --shutdown`, relaunched, restarted Postgres/Redis (data volume survived intact — verified `prescription_item` row count and `alembic_version=0062` unchanged), and recreated the two helper containers (test-runner + live API) from the same branch worktree. Re-confirmed the permission fix and the hidden-flag persistence both survived the crash/recovery before continuing.

### Scenario 1 — Per-field hide (re-test)
**PASS.** As `admin`, unchecked "Hiển thị trên bản in" on the "Chẩn đoán:" label of the default prescription template, saved. Confirmed via captured network traffic: PATCH response now includes `"hidden":true` for that element (previously absent). Confirmed via an independent fresh `GET` (not the PATCH echo) that it persisted (`dg-19 hidden=True`). Re-opened the print (VisitDetailPage path) and confirmed the "Chẩn đoán:" **label** no longer appears while the diagnosis **value** ("Viêm phế quản") still prints on its own line — exactly the expected per-field (not per-block) behavior. Toggled it back on, saved, and confirmed via a fresh GET it reverted to `hidden=False` and the label reappeared in a re-check. Screenshots: `08b-PASS-hidden-field-persisted-in-print.png`.

### Scenario 2 — Doctor default template + exam-form print (re-test)
**PASS.** As `dr_nguyen` (doctor role), opened the in-progress visit's consultation "Kê đơn" tab → "In đơn thuốc" (the actual `doctor/PrintPrescriptionModal.tsx` path, not the billing-shared one). Confirmed the rendered content is the **custom** "Đơn thuốc A4 (mẫu bệnh viện)" template (A4 paper size, "Mã BN:/Mã phiếu:/Tên đơn vị:" layout distinctive to that template) — not the built-in A5 fallback — with the correct diagnosis ("Chẩn đoán: Viêm họng cấp TASK-094 E2E") and resolved unit ("1 ống"). Screenshot: `06b-PASS-doctor-modal-honors-default-template.png`.

Also re-tested exam-form printing ("In phiếu khám" from the visit overview, doctor session): previously showed "Chưa có mẫu in phiếu khám mặc định." with the print button disabled; now correctly shows "Dùng mẫu 'Phiếu khám bệnh A5' — khổ A5." with the "In (A5)" print button **enabled**. Screenshot: `07b-PASS-examform-default-found-enabled.png`.

### Regression (re-test)
- **BE integration:** `tests/integration/prescriptions tests/integration/admin tests/unit/prescriptions tests/integration/inventory` → **87/87 passed** (48 admin+prescriptions incl. the 2 new BUG-094 regression tests `test_print_template_read_allowed_for_prescription_print_role` and `test_print_template_hidden_field_roundtrips`, + 39 unit/inventory), re-run twice (once before, once after the Docker recovery) on freshly recreated containers, both green.
- **ruff** (scoped to the 3 files touched in commit `79210c4`): 2 findings, both confirmed pre-existing via diff comparison (`print_template_schemas.py:20` — the pre-existing `RowColumn.children` forward-ref, untouched by this commit; `test_admin_e2e.py:38` — pre-existing unused `Clinic` import, identical before/after). **Zero new.**
- **mypy** (whole app): 51 total, unchanged from iteration 1's baseline; none land in the 3 touched files. **Zero new.**
- **A/D/E previously-passing scenarios:** diagnosis-source correctness, usage-instruction persistence, and dosage-form-unit resolution all re-confirmed still correct in this same re-test session (same fixtures reused; visible in the screenshots above — diagnosis, "1 ống" unit, and the underlying data were all intact through the Docker crash/recovery).

### Known Limitation (accepted, does NOT fail this task)
The `cashier` role has no `prescription.print` (and never had `settings.clinic`), so the billing/cashier prescription-print path still 403s on template read and falls back to the built-in layout for a real cashier session. This is an explicit, user-accepted out-of-scope limitation for this task (cashier-role template access was never part of TASK-094's AC) — documented here, not filed as a new bug.

**Re-test decision: ALL PASS. Status → DOCUMENTING.**

---

## ITERATION 1 (original run, 2026-07-22) — historical record below

## Environment

- Docker Desktop was unstable at session start; the pre-existing `clinic_cms_w2e_api` container's entrypoint script (`docker/docker-start.sh`) fails to run under this checkout due to CRLF line endings (Windows `core.autocrlf=true` artifact — pre-existing infra issue, unrelated to TASK-094 code). Worked around by starting a parallel container from the same `docker-api:latest` image via `docker compose run --entrypoint bash`, running `alembic`/`pytest`/`ruff`/`mypy` directly inside it, and a second container running `uvicorn` directly on port 9999 for live E2E (bypassing the broken shell script, not editing it).
- Postgres + Redis: real containers (`clinic_cms_w2e_postgres`, `clinic_cms_w2e_redis`), not mocked.
- FE dev server: `clinic-cms-web-task094` worktree, `npm run dev`, port 1420.
- **Local-only, uncommitted change:** `vite.config.ts`'s dev proxy target was hardcoded to a stale port (`8002`, occupied by another app on this machine) in this fresh worktree; the main worktree already had this locally patched to `9999` (per project memory) but this task worktree never got that patch. Repointed it to `127.0.0.1:9999` for this test session only — never committed, pure local dev plumbing, not a source-code fix to the feature.

## Test Statistics

| Test Type | Scenarios | Passed | Failed | Success Rate |
|-----------|-----------|--------|--------|--------------|
| BE unit + integration (real DB) | 66 | 66 | 0 | 100% |
| BE static (ruff, touched files) | 19 findings | 0 new / 19 pre-existing | 0 | 100% (no new) |
| BE static (mypy, touched files) | 3 findings | 0 new / 3 pre-existing | 0 | 100% (no new) |
| Migration integrity (down/up cycle) | 1 | 1 | 0 | 100% |
| FE type-check | 1 | 1 | 0 | 100% |
| FE lint | 18 findings | 0 new / 18 pre-existing | 0 | 100% (no new) |
| FE unit (vitest, full suite) | 1090 | 1087 | 3 (pre-existing/flaky, unrelated) | 99.7% (100% excl. known) |
| FE unit (scoped TASK-094 + regression files) | 61 | 61 | 0 | 100% |
| E2E (browser, live doctor/admin session) | 7 scenarios | 5 | 2 | 71% |
| **TOTAL (E2E-inclusive)** | — | — | **2 blocking bugs** | **FAIL** |

## Acceptance Criteria — Results

1. **Doctor "In đơn thuốc" honors default template** — ❌ **FAIL** (BUG-094-001). Code is wired correctly (verified: doctor modal calls `printTemplatesApi.list("prescription")`, `selectDefaultTemplate()` picks the right template when data is present), but `GET /print-templates` requires permission `settings.clinic`, which the `doctor` role does not have (confirmed via DB role_permission query and a direct API call returning 403 for a real `dr_nguyen` token). The doctor's own print modal therefore **always** falls back to the built-in layout in practice, never the configured default. Same root cause silently disables exam-form printing entirely for doctors (`PrintExamFormModal` shows "no default template", print button disabled) since it has no built-in fallback.
2. **Diagnosis prints correctly on all paths** — ✅ **PASS**. Verified `visit.diagnosis` (not notes/chief_complaint) renders correctly on: VisitDetailPage/billing-shared modal (both built-in and custom-template branches, as admin), doctor's own `PrescriptionTab` print modal (built-in fallback, as doctor — due to BUG-094-001 the custom branch could not be exercised as a real doctor, but the `visit.diagnosis` wiring itself is source-verified identical across both branches). Distinguishing test data used (`chief_complaint="Ho khan"` / `diagnosis="Viêm phế quản"`, and separately `diagnosis="Viêm họng cấp TASK-094 E2E"`) — printed diagnosis text matched the saved diagnosis exactly in every case, never the notes/complaint.
3. **Per-field hide/unhide on template builder** — ❌ **FAIL** (BUG-094-002). The FE toggle ("Hiển thị trên bản in") and `TemplateRenderer` filtering are correctly implemented, but the backend `LayoutElement` Pydantic schema has no `hidden` field, so Pydantic silently drops it from every PATCH. Confirmed via network capture: PATCH request body contains `"hidden":true`; the PATCH's own response (and a subsequent fresh `GET`) show the same element with **no** `hidden` key at all. The toggle only "works" transiently in the same unsaved browser tab; it never survives a save, so it can never affect a real printout.
4. **Structured "cách dùng" persists/reloads/prints** — ✅ **PASS**. Prescribed a medicine (Dexamethasone 4mg inj) with `usage_instruction="Uống sau ăn"`; confirmed in DB (`prescription_item.usage_instruction`), confirmed it re-populates the combobox after a full page reload (edit path), and confirmed it appears on the printed output (`"... 1 ống · Uống sau ăn"`).
5. **Dosage unit follows dosage form** — ✅ **PASS**. Same medicine (`dosage_form=injection`) auto-populated the unit field with `"ống"` (not the trivial tablet→viên case) with zero user input, persisted to DB, and appeared correctly on the printed output ("1 ống").
6. **BE new fields + migration + tests; unit follows dosage form** — ✅ **PASS**. See BE section below.
7. **No regression in named FE test files; ruff/mypy/tsc/eslint clean** — ✅ **PASS** (0 new findings in either linter; all 4 named regression test files green as part of the 61/61 scoped run).

## Backend

- **Migration-chain integrity:** verified `alembic downgrade 0060` → `alembic upgrade head` round-trip on the real (previously manually-patched) dev DB: `prescription_item.usage_instruction` and `dosage_form.unit` columns correctly dropped on downgrade and correctly recreated + reseeded on upgrade. Single linear head (`0062`), no ambiguity on this branch (the documented cross-branch `0061` collision with TASK-093 is an unmerged-branch/merge-gate concern only, confirmed out of scope per review).
- **Seed units verified:** `tablet/capsule→viên, syrup→ml, injection→ống, cream→tuýp, drops→lọ, inhaler→bình, other→NULL` — all match.
- **pytest:** `tests/integration/prescriptions tests/unit/prescriptions tests/integration/inventory` → **66/66 passed**, including `TestUsageInstruction` (create with/without, update persists) and `TestDosageFormUnitResolution` (system-code match, no-match→None, clinic-owned by-name match) — all present and green.
- **ruff** (`ruff check` scoped to the 10 files touched on this branch): 19 findings, all confirmed pre-existing (verified line-by-line against the branch diff — none fall on added/changed lines; line numbers merely shifted due to unrelated insertions earlier in the same files). Zero new.
- **mypy** (`mypy app`, whole app, 51 total errors matches reviewer's cited pre-existing baseline exactly): 3 hits land in touched files (`dosage_form.py:26` clinic_id-nullable-override pattern — identical pre-existing pattern also flagged in `exam_template.py:31`; `medicine_search_service.py:404` and `prescription_service.py:777` — both confirmed unchanged, pre-existing code via diff comparison). Zero new.

## Frontend

- `npm run type-check`: clean.
- `npm run lint`: 18 problems (17 err + 1 warn), all in files untouched by this branch (`VitalsPage.tsx`, `VssIntegrationConfigPage.tsx`, `VssSyncLogPage.tsx` rules-of-hooks; `TemplateRenderer.tsx:239` react-refresh warning on the pre-existing `childStyle` export, confirmed byte-identical to `main`). Zero new.
- `npm test --silent` (full suite): 1090 total, 1087 passed, 3 failed — `QueuePage.test.tsx` (x2) and `ForgotPasswordPage.test.tsx` (x1), matching exactly the reviewer's cited pre-existing/flaky failures. Zero new failures.
- Scoped TASK-094 + must-not-break regression run (`PrintPrescriptionModal`, `PrintablePrescription`, `PrescriptionTab-stock`, `PrescriptionTab-dosage-unit`, `PrescriptionTab-usage-instruction`, `ExamTab`, `SummaryTab`, `DosageFormsPage`, `TemplateRenderer`): **61/61 passed, 9/9 files**.

## E2E Browser Testing (Playwright, real backend on port 9999)

Screenshots: `docs/tasks/TASK-094/deliveries/test-reports/screenshots/`

| # | Scenario | Result | Evidence |
|---|----------|--------|----------|
| 1 | Diagnosis prints correctly (VisitDetailPage/billing path, built-in + custom template, admin) | ✅ PASS | `01-visit-detail-page.png`, `02-visitdetail-print-modal.png`, `03-visitdetail-print-diagnosis.png`, `04-visitdetail-default-template-diagnosis.png` |
| 2 | Doctor "In đơn thuốc" honors default template | ❌ **FAIL** — BUG-094-001 (403 on `settings.clinic`, always falls back to built-in) | `06-FAIL-doctor-modal-403-fallback-builtin.png` |
| 2b | Exam-form print honors default (side-effect of same bug) | ❌ **FAIL** — BUG-094-001 (print disabled entirely, "no default" shown despite one configured) | `07-FAIL-examform-no-default-disabled.png` |
| 3 | Per-field hide toggle (template builder) | ❌ **FAIL** — BUG-094-002 (toggle sent correctly, backend schema drops `hidden`, never persists) | `08-templatebuilder-hidden-toggle.png` + captured PATCH request/response bodies |
| 4 | Usage instruction: set, save, reload, print | ✅ PASS | `05-prescribe-usage-unit.png`, `06-FAIL-doctor-modal-403-fallback-builtin.png` (shows "· Uống sau ăn" in the actual printed text) |
| 5 | Dosage-form unit resolution (injection→ống), editable, prints | ✅ PASS | `05-prescribe-usage-unit.png`, printed text shows "1 ống" |

**7 total screenshots captured** (01–08, `07` includes both scenario 2b and its own file). 5/7 scenario-groups pass; 2 fail with root-caused, reproducible bugs (not flaky/environmental).

## Failures

### Failure 1: Doctor prescription print never honors default template (real doctor session)
**Type:** Business Logic / Authorization
**Severity:** High
**Bug Report:** `docs/tasks/TASK-094/bugs/BUG-094-001.md`

**Expected:** AC1 — doctor's "In đơn thuốc" uses the clinic's configured default prescription template.
**Actual:** `GET /print-templates` requires `settings.clinic` (admin-only); doctor role lacks it → 403 → silent fallback to built-in, always, for every real doctor.

### Failure 2: Per-field hide toggle does not persist
**Type:** Data Integrity / Backend schema gap
**Severity:** High
**Bug Report:** `docs/tasks/TASK-094/bugs/BUG-094-002.md`

**Expected:** AC3 — toggling a field hidden and saving keeps it hidden on the actual printed output.
**Actual:** Backend `LayoutElement` schema has no `hidden` field; Pydantic drops it on every save; a fresh fetch (used by every real print path) never reflects the hidden state.

## Next Steps (iteration 1 — superseded)

2 severe E2E failures found, both root-caused to specific backend fixes (see bug reports for exact file/line and suggested fix). Bug reports created in `docs/tasks/TASK-094/bugs/`.

~~Status set to IN_PROGRESS. Assigned to Code Implementation Agent.~~ — **Superseded: see "RE-TEST — Iteration 2" at the top of this report. Both bugs fixed (commit `79210c4`), re-verified live, all pass. Status → DOCUMENTING.**

---

**Test Execution Time (iteration 1):** ~90 minutes (including Docker recovery, migration verification, full BE/FE suites, and live browser E2E)
**Test Execution Time (iteration 2, re-test):** ~45 minutes (including a second Docker Desktop crash/recovery cycle)
**Total Scenarios:** 87 BE (iteration 2) + 1090 FE unit + 9 E2E scenario-groups across both iterations
**Environment:** dev (real Postgres 15 + Redis 7 + FastAPI + Vite dev server, no mocks)
**Bug status:** BUG-094-001 — RESOLVED, verified live as `dr_nguyen`. BUG-094-002 — RESOLVED, verified via PATCH→GET round-trip + live print re-check.
