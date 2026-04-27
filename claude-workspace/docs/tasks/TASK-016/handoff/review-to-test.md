# Handoff: TASK-016 → Test Agent

**From**: Code Review Agent (iteration 2)
**To**: Test Agent
**Status**: IN_TESTING
**Date**: 2026-04-27
**Decision**: APPROVED — proceed with testing

---

## Summary for Test Agent

The Tauri foundation has been APPROVED after a 2-iteration review cycle. All CRITICAL and MAJOR issues from iteration 1 have been verified as fixed in iteration 2 (commits `c02cffd`, `a579677`, `ab335bd`, `eb61c1a`, `ab7dc44` on `feature/TASK-016-tauri-foundation`, plus `3dfbd0e`, `fcb1138` on `feature/TASK-016-sync-endpoint`).

TypeScript-side quality gates already pass:
- Vitest: **41/41** tests pass
- TypeScript: `tsc --noEmit` clean (0 errors)
- Cross-repo BE branch: clean (only 2 TASK-016 commits, no RBAC contamination)

---

## What's Already Verified (Don't Repeat)

| Verification | Status |
|---|---|
| TS unit tests (uuid, syncEngine, OnlineStatusIndicator, barcode, database) | PASS — 41/41 |
| TypeScript type-check | PASS — 0 errors |
| `applyServerRecord` SQL whitelist + duplicate-col fix | Tested by 5 new Vitest tests (`database.test.ts`) |
| Printer allowlist regex (Rust source review only — cargo not on host) | Source code verified; 4 unit tests defined |
| Tauri capabilities + icons present | All files exist with correct content |
| `useSync` listener leak fix | Verified by code review — handlers hoisted |
| BE branch hygiene | Verified `git log main..feature/TASK-016-sync-endpoint` shows only 2 commits |

---

## Test Agent Focus Areas (Deferred from Review)

These items require infrastructure not available on the review host. Please prioritise:

### 1. Rust unit tests (BLOCKING for full APPROVE → DONE confidence)

```bash
cd E:\MyProject\clinic-cms-workspace\clinic-cms-web\src-tauri
cargo test
```

Expected: **11 tests** pass:
- `db.rs`: 5 tests (schema creation, sync_status valid/invalid CHECK constraint, idempotent migration, sync_state seeding)
- `plugins/printer.rs`: 4 ESC/POS payload tests + 4 NEW `validate_printer_name` tests (8 total)
- `plugins/scanner.rs`: 2 barcode event serialization tests

**Required Rust toolchain**: stable + Tauri 2.x build deps (WebView2 on Windows).

### 2. Tauri build smoke (per AC: Windows .msi / macOS .dmg / Linux .AppImage)

```bash
cd E:\MyProject\clinic-cms-workspace\clinic-cms-web
npm install
npx tauri build
```

Verify:
- Exit code 0 on at least Windows (host platform)
- Bundled artifact present in `src-tauri/target/release/bundle/`
- App icon renders correctly (placeholder blue PNG)
- macOS / Linux deferred to CI matrix.

### 3. Tauri dev mode (per AC: `pnpm tauri dev` start app + connect to API)

```bash
npm run tauri:dev
```

Verify:
- App window opens (1280x800)
- Health-check button on HomePage successfully invokes `health_check` Tauri command (validates capabilities/default.json IPC allowlist works end-to-end)
- No "permission denied" errors in console — proves `core:ipc:allow-invoke` allowlist is correct
- Login form renders (auth store wiring intact)

### 4. BE sync endpoint integration test

```bash
cd E:\MyProject\clinic-cms-workspace\clinic-cms
git checkout feature/TASK-016-sync-endpoint
# Start FastAPI app (requires DB infrastructure per PROJECT.md)
pytest tests/unit/test_sync_endpoint.py -v
```

Expected: **6 tests** pass (auth required, missing/invalid `since` param, schema validation, empty stub response, router registration).

### 5. End-to-end sync demo (per AC: "tạo dummy entity offline → online → sync push thành công")

With both repos running:
1. Start BE: `cd clinic-cms && uvicorn app.main:app`
2. Start FE: `cd clinic-cms-web && npm run tauri:dev`
3. Create a dummy patient record offline (use HomePage or temporary test button)
4. Trigger sync via `useSync` hook
5. Verify pending count → 0
6. Verify BE log shows POST received

### 6. Conflict 409 modal (per AC)

Mock a 409 response from BE for a `prescription` record → verify `ConflictResolutionModal` opens with 3 buttons (`keep_local`, `take_server`, `merge`).

### 7. ESC/POS printer test (per AC: print "HELLO CLINIC")

Either:
- Hardware test with real ESC/POS printer
- Emulator: invoke `print_receipt({ content: "HELLO CLINIC", printer_name: null })` and verify temp file `clinic_cms_print.bin` contains valid ESC/POS bytes (INIT + "HELLO CLINIC\n" + FEED_CUT)

Also verify allowlist rejection:
- `print_receipt({ content: "x", printer_name: "LPT1 & del C:\\file" })` → returns Err

### 8. Barcode scanner test (per AC: HID input → callback)

Mock keystroke events at 50ms intervals → verify `useBarcode` hook emits `barcode-scanned` Tauri event with the buffered string.

---

## Iteration 2 Commits (For Test Agent Reference)

### `clinic-cms-web` branch `feature/TASK-016-tauri-foundation`

| Hash | Description |
|------|-------------|
| `30f3319` | feat(tauri): scaffold Tauri 2.x shell with React 18 frontend (TASK-016) |
| `c02cffd` | fix(printer): validate printer_name against allowlist regex (TASK-016) |
| `a579677` | feat(tauri): add capabilities/default.json and icon placeholders (TASK-016) |
| `ab335bd` | fix(sync): whitelist columns in applyServerRecord (TASK-016) |
| `eb61c1a` | fix(hooks,tauri): minor review fixes (TASK-016) |
| `ab7dc44` | chore: commit package-lock.json (TASK-016) |

### `clinic-cms` branch `feature/TASK-016-sync-endpoint`

| Hash | Description |
|------|-------------|
| `3dfbd0e` | feat(sync): add GET /api/v1/sync/changes endpoint stub (TASK-016) |
| `fcb1138` | fix(sync): remove unused imports and db parameter from sync routes (TASK-016) |

---

## Acceptance Criteria Status (Reviewer's Read)

| AC | Status | Notes |
|---|---|---|
| Tauri dev mode starts | UNBLOCKED — capabilities now present, Test Agent to confirm |
| 7-entity SQLite mirror schema | MET (db.rs reviewed; 5 Rust tests defined) |
| Sync engine push/pull/conflict | MET in TS (engine.ts, 15 tests pass; 5 new database tests pass) |
| Conflict 409 modal | MET (ConflictResolutionModal + 3 buttons; tested in syncEngine.test.ts) |
| ESC/POS printer test | UNBLOCKED — RCE fixed, Test Agent to verify hardware/emulator |
| Barcode scanner HID | MET (useBarcode hook + Rust event emit; 4 unit tests pass) |
| Build Win/macOS/Linux in CI | UNBLOCKED — icons + capabilities present, Test Agent to confirm `tauri build` |
| Foundation primitives for TASK-017..024 | MET (stores, hooks, types exported; 41 TS tests pass) |

---

## Known Limitations (Documented, Not Blocking)

1. **Non-ASCII printer names rejected**: `validate_printer_name` allowlist excludes Vietnamese characters. Acceptable for v1; Win32 OpenPrinter API migration tracked as a post-v1 TODO in `printer.rs` doc-comment.
2. **Console logging in production**: `console.error`/`console.warn` calls remain in `engine.ts`, `useSync.ts`, `useBarcode.ts`. Acceptable for v1; should funnel through Tauri `log` plugin in a follow-up.
3. **Icon placeholders**: All 5 icons are minimal blue PNGs. Replace with real brand icons before first production release.
4. **`pnpm`**: AC mentions `pnpm tauri dev`, but `pnpm` is not installed locally; `npm run tauri:dev` is equivalent. Pnpm migration deferred.

---

## If Test Agent Finds Issues

Use the standard rejection flow: IN_TESTING → IN_PROGRESS, write findings to `docs/tasks/TASK-016/bugs/<bug-name>.md`, and notify the Implementation Agent via `docs/tasks/TASK-016/handoff/test-to-implementation.md`.

If all tests pass: IN_TESTING → DOCUMENTING, write `docs/tasks/TASK-016/handoff/test-to-documentation.md`.
