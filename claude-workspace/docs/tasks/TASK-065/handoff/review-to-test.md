# Handoff: TASK-065 → Test Agent

**From**: Code Review Agent
**To**: Test Agent
**Status**: IN_TESTING
**Decision**: APPROVED

---

## Round 2 Re-Review (2026-05-31) — BUG-001 FIXED — APPROVED

Round 1 (testing) raised **BUG-001**: the `VssIntegrationConfigPage` test still
mocked/asserted `api.patch` after production was changed to `api.put` for the VSS
config save endpoint.

**Fix verified** — single commit `0a63315`, only the test file changed (no production code):
- `clinic-cms-web/src/tests/admin/VssIntegrationConfigPage.test.tsx` (+8 / −4)
  1. Added `put: vi.fn()` to the `apiClient` mock
  2. Added `(api.put ...).mockResolvedValue({ ok: true })` in `beforeEach`
  3. Renamed test → `calls api.put on save` and asserts
     `expect(api.put).toHaveBeenCalledWith("/api/v1/integrations/vss/config", ...)`

Cross-checked against production: `src/pages/admin/VssIntegrationConfigPage.tsx:113`
calls `await api.put("/api/v1/integrations/vss/config", config)` — endpoint + payload
shape match the test assertion.

**FE test run (`npm test`):** 88 files passed, **909 tests passed, 0 failures** (~18s).

BUG-001 resolved, full FE suite green, production code unchanged this round.
Original Round-1 focus areas below still apply for functional/E2E testing.

> Repo note: source repos are under `E:\MyProject\clinic-cms-workspace\`
> (clinic-cms-web, clinic-cms-merge), not `E:\MyProject\`.

---


## Summary

BUG-003 (`GET /visits/{id}/prescriptions` → 405) is fixed by a new clinic-isolated GET endpoint, and
GET/PUT `/integrations/vss/config` were added (JSONB storage, no migration). FE removed the BUG-003
fallback and the silent save-error swallow. All 31 BE integration tests pass; new code is lint/type clean;
cross-tenant isolation verified at the query level.

## Key Findings (for awareness)

- MINOR: VSS `api_key` is returned in plaintext on GET `/integrations/vss/config` (permission-gated by
  `vss:read`). Hardening candidate (mask on GET), not a blocker.
- MINOR: FE `VssConfig` form has no `enabled` toggle though the BE supports it (pre-existing FE gap).
- MINOR: Pre-existing ruff/mypy debt in the prescriptions module (`to_response` forward-ref, import order) —
  outside this task's diff.

## Environment Notes

- BE container `clinic_cms_w2e_api` mounts `clinic-cms-merge`, currently on
  `feature/TASK-065-prescriptions-vss-config`.
- FE working tree was on `feature/TASK-068-theme-system`; the TASK-065 FE changes live on
  `feature/TASK-065-prescriptions-vss-fix`. Check out that branch before FE/E2E testing.

## Focus Areas for Testing

1. **Prescription tab in EMR** — create a prescription on a visit, then load
   `/doctor/visits/{id}#prescription` and confirm the saved prescription shows (no false empty state).
2. **Multiple prescriptions per visit** — verify ordering (prescribed_at ASC) and `total` count; FE only
   uses `items[0]`, so confirm that's the intended/earliest one.
3. **Cross-tenant isolation (live DB)** — confirm clinic A cannot read clinic B's prescriptions via a
   foreign `visit_id` (expect empty list, 200).
4. **VSS config round-trip** — PUT then GET, confirm persisted under `clinic_settings.settings[vss]`;
   test partial update (only `enabled`) preserves other fields via deep-merge.
5. **Permission gates** — `prescription.read` for GET prescriptions; `vss:read` for GET config,
   `vss:sync` for PUT config (403 otherwise).
6. **Feature flag** — confirm `bhyt`-disabled clinic gets the gate behavior expected (FE fallback page;
   BE 403/feature-disabled on the config endpoints) and that the enable flow is not locked out.
7. **FE save error path** — force a PUT failure and confirm the `config.saveError` toast/message appears
   (no longer silently swallowed).
