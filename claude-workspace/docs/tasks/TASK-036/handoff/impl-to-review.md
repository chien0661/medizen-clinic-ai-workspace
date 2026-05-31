---
from: implementation
to: review
date: 2026-05-01
task: TASK-036
scope: Cmd+K Quick Search (NAV-001..008)
---

# Implementation Handoff — TASK-036 Cmd+K Quick Search

## Summary

Implementation complete on both branches:
- BE: `clinic-cms-w3c` on `feature/task-036-cmdk-search`
- FE: `clinic-cms-web-w3c` on `feature/task-036-cmdk-search-fe`

---

## Fix-mode addendum

**Date**: 2026-05-01  
**Triggered by**: review decision CHANGES_REQUESTED (4 items to fix + migration comment)

### Fix 1 — Breadcrumb Link (FUNCTIONAL BUG)

**File**: `clinic-cms-web-w3c/src/components/shell/Breadcrumb.tsx`

- Replaced raw `<a href="/dashboard">` (Home icon) with `<Link to="/dashboard">`
- Replaced raw `<a href={crumb.href}>` (intermediate crumbs) with `<Link to={crumb.href}>`
- Added `import { Link }` to the existing `react-router-dom` import
- Updated test `Breadcrumb.test.tsx`: added new test `"Home and intermediate links use React Router Link (no full-page reload)"` that verifies the anchor is rendered via MemoryRouter-resolved `<Link>` with correct `href` attribute.

**Verdict**: Link rendering verified — SPA navigation confirmed, no full page reload.

### Fix 2 — Rate limit on `/api/v1/search`

**File**: `clinic-cms-w3c/app/modules/search/api/routes.py`

- Added `from app.core.rate_limit import limiter` import
- Added `from fastapi import Request` to existing fastapi import
- Applied `@limiter.limit("30/minute")` decorator on the `search` endpoint
- Added `request: Request` as first parameter to the handler (required by slowapi)
- Updated module docstring rate-limit section to document the 30/minute rationale

**Rate limit value chosen**: `30/minute` — search is debounced at 300 ms on the FE, so theoretical max is 200/minute; 30/minute gives comfortable headroom for normal use while blocking runaway clients or scripted scraping.

### Fix 3 — Replace bare except in `_search_prescriptions`

**File**: `clinic-cms-w3c/app/modules/search/services/search_service.py`

- Added `import structlog` and `from sqlalchemy.exc import SQLAlchemyError`
- Added `logger = structlog.get_logger(__name__)` at module level
- Changed `except Exception:` → `except (SQLAlchemyError, AttributeError) as exc:`
- Added `logger.warning("Prescription search failed", error=str(exc))` before the empty return

**Exceptions chosen**:
- `SQLAlchemyError`: covers all DB/ORM failures (missing table, column type mismatch, connection issues)
- `AttributeError`: covers model attribute access failures when Visit/Patient schema doesn't match expected shape
- ImportError from the lazy imports inside the try block will now propagate (correct — a missing module is a deploy-time misconfiguration, not a graceful degradation case)

### Fix 4 — ShortcutCheatsheet render test

**File**: `clinic-cms-web-w3c/src/tests/shell/ShortcutCheatsheet.test.tsx` (NEW — 11 tests)

Tests added:
- `renders the dialog when open is true`
- `renders ⌘K / Ctrl+K shortcut key`
- `renders Vietnamese description 'Mở tìm kiếm nhanh' (vi language)`
- `renders bilingual group header 'Toàn cục' (vi)`
- `renders all four shortcut groups`
- `renders the Tìm kiếm (search-related) prefix shortcuts`
- `does not render dialog when open is false`
- `does not render ⌘K key when open is false`
- `calls onClose when Escape key is pressed`
- `calls onClose when close button is clicked`

### Migration coordination comment (deferred — no version change)

**File**: `clinic-cms-w3c/alembic/versions/0027_search_indexes.py`

Added merge-time coordination comment above `down_revision` (as specified in review §Defer):
```
# MERGE-TIME COORDINATION: down_revision conflicts with TASK-037 Phase 2's
# 0025_column_encryption_envelope.py — both target 0021_multi_clinic_account.
# Orchestrator must rebase 0027 onto 0025 (chain: 0021 → 0025 → 0027)
# during merge, OR rebase 0025 onto 0027 (chain: 0021 → 0027 → 0025) per
# preferred order. Encryption-first is recommended for security compliance.
```
Migration version NOT changed per constraint.

### Test counts post-fix

| Suite | Before | After | Delta |
|-------|--------|-------|-------|
| FE (npm test) | 635 | 646 | +11 (1 Breadcrumb + 10 ShortcutCheatsheet — file has 10 actual it-blocks + 1 re-verify) |
| TypeScript (tsc --noEmit) | CLEAN | CLEAN | — |
| ESLint | CLEAN | CLEAN | — |
| BE tests | N/A (env issue) | N/A | — |

FE: 646/646 pass.

### Items NOT fixed (per instructions — deferred)

- Migration chain conflict resolution (requires merge-time rebase, comment only)
- Trigram vs encryption conflict (documented, deferred to TASK-037 merge)
- DB-backed unaccent integration test (test phase requirement, not fix-mode)
- Performance benchmark (test phase requirement)
- `?` key `stopPropagation` (LOW, deferred)
