# API Specification: GET /api/v1/sync/changes

**Document Title:** Sync Changes Endpoint Specification
**API Version:** 1.0
**Last Updated:** 2026-04-27
**Status:** Implemented (Stub)
**Task:** TASK-016 — Tauri Foundation

---

## Overview

The `GET /api/v1/sync/changes` endpoint provides a stream of entity changes (create, update, delete) to desktop clients for offline-first synchronization. Clients call this endpoint to pull changes from the server since their last sync timestamp, then apply them to their local SQLite cache.

---

## Endpoint Details

### Path & Method

```
GET /api/v1/sync/changes
```

### Description

Retrieves a paginated list of changes (create/update/delete operations) from the server database that occurred after a given timestamp. Supports optional filtering by entity type.

Used by Tauri desktop clients running in offline-first mode:
1. Client maintains local SQLite cache of 7 entities (patient, visit, vitals, appointment, visit_service, prescription, time_log)
2. Client tracks `lastPullAt` — the server_time from the last successful sync pull
3. Client periodically calls `GET /api/v1/sync/changes?since={lastPullAt}` to fetch new changes
4. Client applies changes to local cache (INSERT for creates, UPDATE for updates, SET is_deleted=1 for deletes)
5. On success, client updates `lastPullAt = server_time` from response

### Authentication

**Required:** Yes
**Type:** JWT Bearer Token

Header format:
```
Authorization: Bearer {JWT_TOKEN}
```

The token must be valid and not expired. User must have clinic tenant context (set via FastAPI ContextVar during request).

---

## Request

### Query Parameters

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `since` | String (ISO8601) | Yes | Timestamp (UTC) representing the last successful pull. Server returns changes that occurred **after** this timestamp. Format: `YYYY-MM-DDTHH:MM:SSZ` or `YYYY-MM-DDTHH:MM:SS.sssZ`. | `2026-04-27T10:30:00Z` |
| `entity` | String (enum) | No | Filter results to a single entity type. If omitted, all entity types are included. Valid values: `patient`, `visit`, `vitals`, `appointment`, `visit_service`, `prescription`, `time_log`. | `prescription` |
| `limit` | Integer | No | Maximum number of changes to return (pagination). Default: 1000. Max: 5000. | `500` |
| `offset` | Integer | No | Offset for pagination (used with limit). Default: 0. | `100` |

### Request Headers

| Header | Value | Required |
|--------|-------|----------|
| `Authorization` | `Bearer {JWT_TOKEN}` | Yes |
| `Content-Type` | `application/json` (implied, GET request) | No |

### Example Requests

**Pull all changes since last sync:**
```http
GET /api/v1/sync/changes?since=2026-04-27T10:30:00Z HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Pull only prescription changes with pagination:**
```http
GET /api/v1/sync/changes?since=2026-04-27T10:30:00Z&entity=prescription&limit=100&offset=0 HTTP/1.1
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## Response

### Success (HTTP 200 OK)

```json
{
  "changes": [
    {
      "entity": "patient",
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "op": "create",
      "data": {
        "name": "Nguyễn Văn A",
        "phone": "0912345678",
        "date_of_birth": "1990-01-15",
        "gender": "male",
        "address": "123 Đường Lê Lợi, TP.HCM",
        "id_card": "123456789",
        "is_deleted": 0,
        "created_at": "2026-04-27T10:20:00Z",
        "updated_at": "2026-04-27T10:20:00Z"
      },
      "server_version": 1,
      "server_updated_at": "2026-04-27T10:20:00Z"
    },
    {
      "entity": "prescription",
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "op": "update",
      "data": {
        "status": "dispensed",
        "dispensed_at": "2026-04-27T10:25:00Z"
      },
      "server_version": 2,
      "server_updated_at": "2026-04-27T10:25:00Z"
    },
    {
      "entity": "vitals",
      "id": "770e8400-e29b-41d4-a716-446655440002",
      "op": "delete",
      "data": null,
      "server_version": 1,
      "server_updated_at": "2026-04-27T10:28:00Z"
    }
  ],
  "server_time": "2026-04-27T10:35:00Z",
  "has_more": false,
  "total_count": 3
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `changes` | Array | List of change objects (see below). Empty if no changes since the given timestamp. |
| `changes[].entity` | String | Entity type: `patient`, `visit`, `vitals`, `appointment`, `visit_service`, `prescription`, `time_log`. |
| `changes[].id` | String (UUID) | Unique identifier of the entity. |
| `changes[].op` | String | Operation type: `create` (new entity), `update` (entity modified), `delete` (soft-delete, is_deleted=1). |
| `changes[].data` | Object or null | Entity payload. For `create`/`update`: full or partial entity data. For `delete`: null. Includes entity-specific columns (e.g. patient name, visit date) but EXCLUDES sync metadata columns (`sync_status`, `sync_error`, `sync_attempted_at`). |
| `changes[].server_version` | Integer | Monotonically increasing version number for optimistic locking. Client should store this locally and send it back during PATCH/POST to detect conflicts (409 Conflict response). |
| `changes[].server_updated_at` | String (ISO8601) | Timestamp of last modification on the server (UTC). Used for conflict resolution — compare with client's local `updated_at` to determine last-write-wins behavior. |
| `server_time` | String (ISO8601) | Current server timestamp (UTC) when this response was generated. Client must store this as `lastPullAt` for the next sync call to avoid re-fetching the same changes. |
| `has_more` | Boolean | If true, there are more changes beyond the current `limit`. Client should make another request with `offset` incremented. |
| `total_count` | Integer | Total number of changes matched by the `since` and optional `entity` filter (before pagination). |

---

## Error Responses

### 400 Bad Request

Missing or malformed required parameter.

```json
{
  "code": "INVALID_REQUEST",
  "message": "Missing required parameter: since"
}
```

| Case | Message |
|------|---------|
| Missing `since` param | "Missing required parameter: since" |
| Empty string `since` | "Parameter 'since' cannot be empty" |
| Invalid JSON in body (if POST) | "Invalid request body" |

### 401 Unauthorized

JWT token is invalid, expired, or missing.

```json
{
  "code": "UNAUTHORIZED",
  "message": "Invalid or expired token"
}
```

**Mitigation:** Client should redirect to login screen when receiving 401. Clear cached JWT token.

### 422 Unprocessable Entity

Parameter value is invalid (wrong format, out of enum range, etc).

```json
{
  "code": "VALIDATION_ERROR",
  "message": "Parameter 'since' must be a valid ISO8601 timestamp"
}
```

| Case | Message |
|------|---------|
| `since` not ISO8601 | "Parameter 'since' must be a valid ISO8601 timestamp" |
| `entity` not in enum | "Parameter 'entity' must be one of: patient, visit, vitals, appointment, visit_service, prescription, time_log" |
| `limit` out of range | "Parameter 'limit' must be between 1 and 5000" |

### 500 Internal Server Error

Server-side error (database, network, etc). Retry with exponential backoff.

```json
{
  "code": "INTERNAL_ERROR",
  "message": "Server error. Please retry later."
}
```

---

## Implementation Status (v1 / TASK-016)

**Current Status:** Stub implementation.

The endpoint validates the `since` query parameter, checks JWT authentication, and returns a hardcoded empty response:
```json
{
  "changes": [],
  "server_time": "2026-04-27T10:35:00Z",
  "has_more": false,
  "total_count": 0
}
```

**Full Implementation:** Deferred to TASK-015. Will:
1. Query the ORM (SQLAlchemy) to fetch actual changes from all 7 entity tables
2. Filter by `since` timestamp (WHERE updated_at > :since)
3. Apply tenant isolation (clinic context from ContextVar)
4. Construct proper `changes` array with correct `server_version` and `server_updated_at` values
5. Support entity type filtering and pagination

**Test Coverage:**
- `tests/unit/test_sync_endpoint.py` (6 tests) — auth requirement, parameter validation, schema validation, empty stub response
- Must run with Python 3.11+ (requires `datetime.UTC`; host has 3.10)

---

## Conflict Handling

When a client receives a 200 response and tries to apply a change that conflicts with its local state, the client uses the following logic:

### Non-Critical Entities (Vitals, TimeLog, Appointment, VisitService)

**Last-Write-Wins (LWW):**
- Compare `local.updated_at` vs `server.updated_at` (from change.server_updated_at)
- If `local.updated_at > server.updated_at`: local is newer → apply local (push via POST/PATCH)
- If `server.updated_at >= local.updated_at`: server is newer → discard local, apply server (INSERT/UPDATE)

### Critical Entities (Prescription)

**Manual Resolution via Modal:**
- If a PATCH to /api/v1/prescriptions/{id} returns 409 Conflict (because server has version > local.server_version)
- Client fetches server record from conflict response
- Show `ConflictResolutionModal` with 3 options: **keep_local** (force-push), **take_server** (discard local), **merge** (user edit manually)

---

## Rate Limiting

**Not implemented in v1.** May be added in v2.

---

## Pagination

Use `limit` and `offset` for pagination:

**Example: Fetch next 100 changes**
```http
GET /api/v1/sync/changes?since=2026-04-27T10:30:00Z&limit=100&offset=0 HTTP/1.1
```

Then:
```http
GET /api/v1/sync/changes?since=2026-04-27T10:30:00Z&limit=100&offset=100 HTTP/1.1
```

Client checks `has_more` field — if true, increment `offset` and fetch again.

---

## Performance Considerations

- **Indexed columns:** `updated_at`, `entity_type`, `is_deleted` should be indexed for fast filtering
- **Large result sets:** Use `limit` to avoid timeout (default 1000, max 5000)
- **Frequent calls:** Client should cache `lastPullAt` and only call when:
  - Periodic timer (~30 seconds) if online
  - Immediately after reconnect (online event)
  - User manually trigger sync
- **Server response time:** Stub returns immediately. Full impl (TASK-015) should complete <1s for typical clinic (500-5000 entities per clinic, <100 changes per sync cycle)

---

## Example Workflow

**Scenario: Desktop client syncs prescription changes**

1. **Client state:**
   - `lastPullAt = 2026-04-27T10:30:00Z` (from previous sync)
   - Local SQLite has 50 prescriptions with `sync_status='synced'`

2. **Client makes request:**
   ```http
   GET /api/v1/sync/changes?since=2026-04-27T10:30:00Z&entity=prescription HTTP/1.1
   Authorization: Bearer eyJ...
   ```

3. **Server processes:**
   - Validate JWT → OK
   - Parse `since=2026-04-27T10:30:00Z` → OK (ISO8601)
   - Query: SELECT * FROM prescription WHERE updated_at > '2026-04-27T10:30:00Z' AND clinic_id = :clinic_id
   - Result: 3 changes (1 create, 1 update, 1 delete)

4. **Server responds (200 OK):**
   ```json
   {
     "changes": [
       {"entity": "prescription", "id": "uuid1", "op": "create", "data": {...}, "server_version": 1, "server_updated_at": "2026-04-27T10:31:00Z"},
       {"entity": "prescription", "id": "uuid2", "op": "update", "data": {"status": "dispensed"}, "server_version": 3, "server_updated_at": "2026-04-27T10:33:00Z"},
       {"entity": "prescription", "id": "uuid3", "op": "delete", "data": null, "server_version": 2, "server_updated_at": "2026-04-27T10:34:00Z"}
     ],
     "server_time": "2026-04-27T10:35:00Z",
     "has_more": false,
     "total_count": 3
   }
   ```

5. **Client applies:**
   - For change 1 (create): INSERT into local prescription table with all data
   - For change 2 (update): UPDATE local prescription where id=uuid2, set status='dispensed'
   - For change 3 (delete): UPDATE local prescription where id=uuid3, set is_deleted=1
   - Update `lastPullAt = 2026-04-27T10:35:00Z`

6. **Next sync:** Client waits 30s or until reconnect, then calls:
   ```http
   GET /api/v1/sync/changes?since=2026-04-27T10:35:00Z&entity=prescription HTTP/1.1
   ```

---

## Related Endpoints (Per-Entity REST)

For PUSH operations, client uses standard REST endpoints (not part of this spec, but mentioned for context):

| Method | Path | Purpose |
|--------|------|---------|
| POST | `/api/v1/patients` | Create new patient (client-side UUIDv7 id) |
| PATCH | `/api/v1/patients/{id}` | Update patient |
| DELETE | `/api/v1/patients/{id}` | Soft-delete patient |
| POST | `/api/v1/prescriptions` | Create new prescription |
| PATCH | `/api/v1/prescriptions/{id}` | Update prescription |
| DELETE | `/api/v1/prescriptions/{id}` | Soft-delete prescription |
| ... | ... | (Similar for visit, vitals, appointment, visit_service, time_log) |

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-04-27 | Initial spec — stub implementation (TASK-016). Full impl deferred to TASK-015. |
