# Handoff: TASK-016 → Code Implementation Agent

**From**: Code Review Agent
**To**: Code Implementation Agent
**Status**: IN_PROGRESS
**Decision**: CHANGES_REQUESTED
**Iteration**: 1

---

## Summary

The Tauri foundation is well-structured (TS sync engine, Zustand stores, schema migration), but two CRITICAL issues block both security and the "app actually runs" acceptance criterion. Plus one branch-hygiene issue on the BE repo, and a few MAJOR/MINOR items. Full report in `docs/tasks/TASK-016/handoff/review-report.md`.

---

## Required Changes (must fix before re-review)

### CRITICAL — must fix

1. **Command injection in printer plugin** — `clinic-cms-web/src-tauri/src/plugins/printer.rs:102-110`
   - `printer_name` from frontend flows directly into `cmd /c copy ... <printer_name>`. A printer name like `LPT1 & del C:\file` executes via cmd.exe.
   - **Fix**: validate `printer_name` against `^[A-Za-z0-9 _\-:]+$` (reject anything else) before use, OR switch to Win32 `OpenPrinter`/`StartDocPrinter`/`WritePrinter` (no shell), OR restrict to a hard-coded allowlist (`LPT1`, `LPT2`, `default`) for v1 and document the limitation.

2. **Missing Tauri 2.x capabilities directory** — `clinic-cms-web/src-tauri/capabilities/` (does not exist)
   - Without `capabilities/default.json`, the IPC bridge denies every `invoke()` call → `health_check`, `db_execute`, `print_receipt`, plugin-sql, plugin-shell all blocked → app cannot run.
   - **Fix**: create `src-tauri/capabilities/default.json` with `windows: ["main"]` and the permissions for `core:default`, `sql:default` + `sql:allow-execute|allow-select|allow-load`, `shell:allow-open`, plus explicit allowlist for the project's custom commands (`health_check`, `get_app_config`, `print_receipt`, `start_barcode_listener`, `get_pending_changes_count`, `get_last_sync_time`, `set_last_sync_time`, `db_execute`, `db_query`). Verify the schema URL in the file.

### MAJOR — should fix

3. **Missing `icons/` directory** — `clinic-cms-web/src-tauri/tauri.conf.json:31-37` references icons that don't exist. `tauri build` will fail in CI.
   - **Fix**: run `tauri icon` to generate from a placeholder PNG (Tauri ships with a generator), or temporarily remove the icon references from `tauri.conf.json` and rely on Tauri defaults.

4. **SQL column injection in `applyServerRecord`** — `clinic-cms-web/src/sync/database.ts:118-138`
   - Server response `data` keys are interpolated into SQL via `Object.keys(data).join(", ")`. A hostile server response can inject SQL via column names; even a benign typo causes a runtime SQL error that's silently swallowed.
   - **Fix**: maintain a per-entity column whitelist (the seven schemas in `db.rs`) and filter `data` keys against the whitelist before constructing the INSERT. Reject (log + skip) records with unknown columns.

5. **Event-listener leak in `useSync`** — `clinic-cms-web/src/hooks/useSync.ts:95-101`
   - `addEventListener("online", () => setOnline(true))` followed by `removeEventListener("online", () => setOnline(true))` removes nothing — the two arrow functions are different references.
   - **Fix**: hoist `const onlineHandler = () => setOnline(true)` above the listeners, pass the same reference to add and remove.

6. **Cross-repo BE branch contains TASK-004 commits** — `clinic-cms` repo, branch `feature/TASK-016-sync-endpoint`
   - The branch was cut from `feature/task-004-rbac` instead of `main`. `git log main..feature/TASK-016-sync-endpoint --oneline` shows TASK-004's RBAC commit (`28aefad`) sits on top of the TASK-016 commit (`2618dc8`). Merging this branch to main as-is would silently land TASK-004's 28-file RBAC change.
   - **Fix**: `git checkout feature/TASK-016-sync-endpoint && git rebase --onto main 28aefad feature/TASK-016-sync-endpoint` (drop the RBAC commit so only `2618dc8` is on top of `main`). If TASK-004 is expected to land on `main` first, hold this branch and rebase after that merge.

### MINOR — fix while you're in there

7. **Duplicate-column risk in `applyServerRecord`** — `clinic-cms-web/src/sync/database.ts:118-126`
   - If `data` already contains `sync_status`, `server_version`, or `sync_error`, the INSERT will list them twice → SQL syntax error.
   - **Fix**: filter those keys out of `data` before computing `columns`/`values`, then re-add them once.

8. **Unused imports in BE sync routes** — `clinic-cms/app/modules/sync/api/routes.py:20-26`
   - `importlib`, `select`, `text`, and the `db: AsyncSession = Depends(get_db)` parameter are imported/wired but unused. Will fail strict ruff/flake8 lint in CI.
   - **Fix**: remove the unused imports and the `db` parameter (the stub doesn't query anything anyway).

9. **`emit_barcode_scan` not registered in `invoke_handler`** — `clinic-cms-web/src-tauri/src/lib.rs:30-40`
   - It's annotated `#[tauri::command]` but missing from `tauri::generate_handler![]`. Either register it or drop the annotation.

10. **`useBarcode` initial `lastKeystrokeRef = 0`** — `clinic-cms-web/src/hooks/useBarcode.ts:41,49-55`
    - First-keystroke `interval = Date.now() - 0` is a huge number. Currently safe because `bufferRef` is empty, but fragile.
    - **Fix**: initialize to `-Infinity` or `Number.MIN_SAFE_INTEGER`, or guard with `lastKeystrokeRef.current !== 0`.

11. **Commit `package-lock.json`** — currently untracked in `clinic-cms-web`. Either commit it or, since the spec mentions `pnpm tauri dev`, switch to pnpm and commit `pnpm-lock.yaml`.

---

## Out of Scope This Iteration

- Console.log usage in production code (engine.ts, useSync.ts, useBarcode.ts) — flagged as MINOR but acceptable for v1.
- Test coverage gaps for `applyServerRecord` and `pushRecord` last-write-wins branch — fold into TASK-018+ or a follow-up.

## After You Fix

1. Re-run `npm test` (must stay 36/36) — add new tests covering capability allowlist, column whitelist, and listener cleanup.
2. Re-run `npx tsc --noEmit` (must stay clean).
3. Update `docs/tasks/TASK-016/task.md` status back to IN_REVIEW.
4. Write `handoff/implementation-to-review-v2.md` summarizing what changed and reference the issue numbers above.
5. The Review Agent will be re-dispatched.

## Reference

- Full review report: `docs/tasks/TASK-016/handoff/review-report.md`
- Original handoff from implementation: `docs/tasks/TASK-016/handoff/implementation-to-review.md`
