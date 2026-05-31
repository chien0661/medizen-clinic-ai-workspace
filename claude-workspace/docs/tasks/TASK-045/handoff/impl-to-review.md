# TASK-045 — VSS BHYT Integration: Implementation → Review Handoff

**Status**: Implementation complete, ready for code review
**Date**: 2026-05-01
**Agent**: Code Implementation

---

## Migration

| Field | Value |
|-------|-------|
| Version | `0029` |
| Filename | `alembic/versions/0029_vss_sync_log.py` |
| Table | `vss_sync_log` |
| Depends on | `65fc9ae59ba5` (current head before this task) |

**Migration verified**: `alembic upgrade head` ran successfully in Docker — `Running upgrade 65fc9ae59ba5 -> 0029` confirmed in logs.

---

## BE Endpoints (`app/modules/integrations/vss/`)

| Method | Path | Permission |
|--------|------|-----------|
| POST | `/api/v1/integrations/vss/eligibility-check` | `vss:read` |
| POST | `/api/v1/integrations/vss/submit-claim` | `vss:sync` |
| GET  | `/api/v1/integrations/vss/sync-log` | `vss:read` |
| GET  | `/api/v1/integrations/vss/status` | `vss:read` |

---

## FE Pages (`clinic-cms-web-w5v`)

| Component | Route | File |
|-----------|-------|------|
| `VssIntegrationConfigPage` | `/admin/integrations/vss` | `src/pages/admin/VssIntegrationConfigPage.tsx` |
| `VssSyncLogPage` | `/admin/integrations/vss/log` | `src/pages/admin/VssSyncLogPage.tsx` |

---

## Stub TODOs (documented in code)

### BE Stubs

1. **`require_feature_stub`** in `app/modules/integrations/vss/api/routes.py`
   - Stub: dependency that always allows
   - TODO comment: `POST-TASK-034 MERGE: replace with require_feature("bhyt")`
   - Location: every endpoint `dependencies=` list

2. **Real VSS HTTP client** in `app/integrations/vss/client.py`
   - All methods mock/stub in v1
   - TODO comment: `TODO v2: replace _call_vss_api stubs with real httpx.AsyncClient calls`
   - v2 target: `VSS_API_URL/v1/eligibility`, `/v1/claims`, `/v1/health`

3. **`vss:read` / `vss:sync` permissions not seeded**
   - TODO comment in routes.py: `TODO POST-TASK-034 MERGE: seed these permissions`
   - Permissions exist as strings but not yet in DB role/permission tables

4. **Config endpoint** (`PATCH /admin/integrations/vss/config`)
   - Placeholder in FE; BE endpoint not yet implemented (returns silently)
   - TODO: implement when persistent config storage is designed

### FE Stubs

5. **`useFeatureFlag('bhyt')`** in both `VssIntegrationConfigPage.tsx` and `VssSyncLogPage.tsx`
   ```tsx
   // TODO POST-TASK-034 MERGE: replace with useFeatureFlag('bhyt')
   const bhytEnabled = true; // stub
   ```

---

## Test Results

### BE — unit (Docker, Python 3.11)
- `tests/unit/test_vss_client.py`: **12 passed**
- `tests/unit/test_vss_sync_log.py`: **9 passed**
- Total unit: **21 passed, 0 failed**

### BE — integration (Docker, real PostgreSQL)
- `tests/integration/test_vss_endpoints.py`: **13 passed, 0 failed**

### FE (Vitest)
- `src/tests/admin/VssIntegrationConfigPage.test.tsx`: new tests (part of 52 test files)
- `src/tests/admin/VssSyncLogPage.test.tsx`: new tests (part of 52 test files)
- Total FE: **581 passed, 0 failed** (52 test files)
- TypeScript: **0 errors**

---

## BE Files Created/Modified

**New files:**
- `alembic/versions/0029_vss_sync_log.py`
- `app/integrations/__init__.py`
- `app/integrations/vss/__init__.py`
- `app/integrations/vss/client.py` (VssClient mock adapter)
- `app/modules/integrations/__init__.py`
- `app/modules/integrations/vss/__init__.py`
- `app/modules/integrations/vss/models/__init__.py`
- `app/modules/integrations/vss/models/vss_sync_log.py`
- `app/modules/integrations/vss/schemas/__init__.py`
- `app/modules/integrations/vss/schemas/vss_schemas.py`
- `app/modules/integrations/vss/services/__init__.py`
- `app/modules/integrations/vss/services/vss_service.py`
- `app/modules/integrations/vss/api/__init__.py`
- `app/modules/integrations/vss/api/routes.py`
- `tests/unit/test_vss_client.py`
- `tests/unit/test_vss_sync_log.py`
- `tests/integration/test_vss_endpoints.py`
- `tests/unit/integrations/__init__.py`
- `tests/integration/integrations/__init__.py`

**Modified files:**
- `app/core/config.py` — added `VSS_API_URL`, `VSS_API_KEY` settings
- `app/main.py` — registered `vss_router`

## FE Files Created/Modified

**New files:**
- `src/pages/admin/VssIntegrationConfigPage.tsx`
- `src/pages/admin/VssSyncLogPage.tsx`
- `src/locales/vi/vss.json`
- `src/locales/en/vss.json`
- `src/tests/admin/VssIntegrationConfigPage.test.tsx`
- `src/tests/admin/VssSyncLogPage.test.tsx`

**Modified files:**
- `src/lib/i18n.ts` — registered `vss` namespace
- `src/router/index.tsx` — added 2 VSS routes
- `src/components/shell/Sidebar.tsx` — added 2 nav items under admin group (Link2, ScrollText icons)

---

## Known Limitations / Post-Merge Work

1. `vss:read` / `vss:sync` permissions need to be seeded in DB (via migration or seed script) for the permission check to pass in staging/production.
2. PATCH `/admin/integrations/vss/config` endpoint is a placeholder — FE silently ignores failures.
3. Real VSS HTTP calls are fully mocked in v1. v2 requires setting `VSS_API_URL` and `VSS_API_KEY` env vars and implementing real `httpx` calls in `client.py`.
4. After TASK-034 merges: replace `require_feature_stub("bhyt")` (BE) and `const bhytEnabled = true` (FE) with real feature flag gates.
