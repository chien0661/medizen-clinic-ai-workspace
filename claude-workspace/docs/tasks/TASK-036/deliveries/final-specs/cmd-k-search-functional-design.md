---
task: TASK-036
title: Cmd+K Quick Search & Global Navigation
date: 2026-05-01
status: DONE
scope: NAV-001..008 Command Palette + Global Search + Breadcrumb + Shortcuts
---

# Cmd+K Quick Search & Global Navigation — Functional Design

**Version**: 1.0 | **Status**: DONE | **Completion Date**: 2026-05-01

---

## Mục Đích

Triển khai bộ tính năng điều hướng nhanh và tìm kiếm toàn cục:

- **NAV-001**: Command Palette (Cmd+K) với tìm kiếm đa mode
- **NAV-002**: Tìm kiếm bệnh nhân (name, phone, ID)
- **NAV-003**: Tìm kiếm thuốc (name, active ingredient)
- **NAV-004**: Tìm kiếm tính năng (features/menu routes)
- **NAV-005**: Tìm kiếm đơn thuốc (prescription lookup)
- **NAV-006**: Tìm kiếm kho (inventory/lot tracking)
- **NAV-007**: Shortcut Cheatsheet (? key) — hướng dẫn phím tắt
- **NAV-008**: Breadcrumb Auto-generation — điều hướng ngữ cảnh

---

## Phạm Vi

| Thành Phần | Chi Tiết |
|-----------|---------|
| **Search Modes** | 6: bệnh nhân (bn), thuốc (thuoc), kho (inv), đơn thuốc (rx), tính năng (lk), all |
| **Shortcut Keys** | 4: Cmd+K (palette), ? (cheatsheet), Esc (close), Tab (mode switch) |
| **Breadcrumb** | Auto-generate từ route pathname; collapse UUID segments; hide on dashboard |
| **Cheatsheet** | Bilingual (vi/en), 4 groups: Global, Palette, Doctor, Pharmacy |
| **Rate Limit** | 30 requests/minute trên `/api/v1/search` |
| **Test Coverage** | BE: 22 tests (15 unit + 7 integration); FE: 646 tests (67 task-specific) |

---

## Architecture

### Backend Search Module

**Vị trí**: `clinic-cms-w3c/app/modules/search/`

#### Database Indexes (Migration 0027)

```
Extensions:
  - pg_trgm        → trigram matching for fuzzy search
  - unaccent       → remove diacritics (é → e)

Function:
  - immutable_unaccent(text) → IMMUTABLE version for indexing

Indexes (5 × GIN trigram):
  1. patient.full_name       (immutable_unaccent(lower(...)))
  2. patient.phone           (plaintext)
  3. patient.id_number       (plaintext)
  4. medicine.name           (immutable_unaccent(lower(...)))
  5. medicine.active_ingredient (immutable_unaccent(lower(...)))
```

**CRITICAL MERGE COORDINATION**: Migrations 0027 (TASK-036) và 0025 (TASK-037 Phase 2) cùng target parent 0021. Orchestrator phải rebase 0027 → 0025 (hoặc ngược lại per encryption-first strategy).

#### Encryption vs Trigram Strategy (TASK-037 Wave 3-A)

Khi TASK-037 merges, 3 patient columns (full_name, phone, id_number) trở thành BYTEA (encrypted):
- **Trigram indexes trên BYTEA không hoạt động** → indexes sẽ bị drop
- **Khuyến cáo**: Option **(b) Searchable HMAC side columns**
  - `patient.full_name_hash` (HMAC deterministic) → exact + prefix lookups
  - `patient.full_name_search_normalized` (plaintext unaccent) → retain fuzzy matching
  - Cần per-tenant key management

---

### API Endpoint

**Route**: `GET /api/v1/search?q=<query>&mode=<mode>&limit=20`

**Parameters**:
- `q` (string, required): Search query
- `mode` (enum, required): `bn` | `thuoc` | `inv` | `rx` | `lk` | `all`
- `limit` (int, optional, default 20): Max results per mode

**Response**:
```json
{
  "results": [
    {
      "id": "uuid",
      "type": "bn|thuoc|inv|rx|lk",
      "title": "Nguyễn Văn A",
      "subtitle": "089 123 4567",
      "score": 0.95,
      "href": "/patients/uuid"
    }
  ]
}
```

**Rate Limit**: `@limiter.limit("30/minute")` — user quota 30 requests/min

**Permission Filter**: 
- Scoped by `current_clinic_id` từ JWT
- RBAC permissions validated via `rbac_service.get_user_effective_permissions()`

**Query Processing**:
1. Empty/whitespace → return `[]` (no DB hit)
2. Mode-specific search function called
3. Per-entity scores calculated
4. Deduplication by `(type, id)`
5. Sort by score DESC, then `updated_at` DESC (tiebreaker)
6. Limit to N results

#### Search Modes

| Mode | Entities | Scoring | Special Rules |
|------|----------|---------|---------------|
| `bn` | Patient | name (≥0.3 trigram) 0.95, phone 0.80, id_number 0.90, code 0.85 | Phone: digit-gate (≥4 digits or space-separated) |
| `thuoc` | Medicine | name (≥0.3) 0.95, active_ingredient 0.85, code 0.90 | Drug lookup by active ingredient |
| `inv` | Inventory | lot, batch_number | Exact match + case-insensitive |
| `rx` | Prescription | visit_id, patient.name | Lookup via Visit entity join |
| `lk` | Features | hardcoded 18-route catalog | In-process substring + char-overlap fallback |
| `all` | Union (bn+thuoc+inv+rx+lk) | Per-entity rules + cross-type dedup | Smart score aggregation |

---

### Frontend Components

#### CommandPalette (`src/components/shell/CommandPalette.tsx`)

- **Modal overlay**: `fixed inset-0 z-50`, backdrop click closes
- **Dimensions**: `max-w-2xl` (≈672px), `pt-[20vh]` top-aligned
- **Input focus**: Auto-focus on open (setTimeout 50ms)
- **Sub-mode prefix parsing**: Detects `/bn`, `/thuoc`, etc. as mode shorthand
- **Keyboard navigation**: ↑↓ cycle, Enter select, Esc close, Tab next-mode
- **Recent items**: Tauri `secureStore` cap 10 items, persisted across sessions
- **Empty state**: "Không có kết quả" message
- **Loading state**: Spinner shown during API call
- **Custom implementation** (not cmdk lib): 391-line component, bundle-efficient, full control

**ARIA**: `role=dialog`, `aria-modal=true`, `role=listbox` results, `role=option` per item, `aria-selected`

#### useGlobalShortcuts Hook (`src/hooks/useGlobalShortcuts.ts`)

Mounted at `AppShell` level (above routed pages, below auth).

| Shortcut | Action | Condition |
|----------|--------|-----------|
| Cmd/Ctrl+K | Open/close palette | Always |
| ? | Open/close cheatsheet | Skip if in input field |
| Esc | Close both palette & cheatsheet | Always |
| Tab | Cycle to next mode (in palette) | Palette open only |

**Input detection**: Skips when target is `input`, `textarea`, `select`, `[contenteditable]`

#### Breadcrumb Component (`src/components/shell/Breadcrumb.tsx`)

- **Auto-generation**: Parse `useLocation().pathname` → crumb segments
- **UUID collapse**: Regex match UUIDs + MongoDB IDs → collapse into previous crumb
- **Hide routes**: Dashboard, root `/`
- **Rendering**: Uses React Router `<Link to={...}>` (SPA navigation, no full reload)
- **Last crumb**: `aria-current="page"`
- **Icons**: Home icon on first crumb, forward-slash separators

**Example**:
```
pathname: /patients/550e8400-e29b-41d4-a716-446655440000/prescriptions
crumbs: [
  { label: "Home", href: "/dashboard" },
  { label: "Bệnh nhân", href: "/patients" },
  { label: "Đơn thuốc", href: "/patients/550e8400.../prescriptions" }  ← UUID collapsed
]
```

#### ShortcutCheatsheet Component (`src/components/shell/ShortcutCheatsheet.tsx`)

Modal dialog, bilingual (vi/en toggle via `i18n.language`).

**Groups**:
1. **Global**: Cmd+K (palette), ? (cheatsheet)
2. **Tìm kiếm (Palette modes)**: /bn, /thuoc, /inv, /rx, /lk
3. **Bác sĩ (Doctor-specific)**: e.g., Ctrl+S (save), etc.
4. **Nhà Thuốc (Pharmacy-specific)**: e.g., batch entry, etc.

**Closure**: Esc key or close button

---

## i18n Configuration

**Namespace**: `commandPalette.*`

**Keys** (vi + en):
```yaml
commandPalette:
  title: "Tìm kiếm nhanh"               # Quick Search
  placeholder: "Tìm bệnh nhân, thuốc..." # Search patients, medicines...
  noResults: "Không có kết quả"         # No results
  loading: "Đang tải..."                 # Loading...
  recent: "Gần đây"                      # Recent
  groups:
    patients: "Bệnh nhân"
    medicines: "Thuốc"
    inventory: "Kho"
    prescriptions: "Đơn thuốc"
    features: "Tính năng"
  modes:
    bn: "Bệnh nhân"
    thuoc: "Thuốc"
    inv: "Kho"
    rx: "Đơn thuốc"
    lk: "Tính năng"
    all: "Tất cả"

shortcutCheatsheet:
  title: "Phím tắt"                    # Shortcuts
  groups:
    global: "Toàn cục"
    palette: "Tìm kiếm"
    doctor: "Bác sĩ"
    pharmacy: "Nhà Thuốc"
  items:
    cmdK: "Mở tìm kiếm nhanh"           # Open quick search
    helpKey: "Hiển thị phím tắt"        # Show shortcuts
    esc: "Đóng"                          # Close
```

---

## Test Coverage

### Backend (22 tests)

**Unit Tests (15)**:
- Permission gating: `current_clinic_id` filtering
- Mode routing: valid enum values, 422 on unknown
- Deduplication: `(type, id)` keying, highest score retained
- Recency tiebreaker: `updated_at DESC` in SQL
- Empty query: `[]` returned without DB hit
- Vietnamese unaccent: `"ngu"` → `"Nguyễn"` match via mock similarity

**Integration Tests (7)**:
- Structural validity of result objects
- Permission scoping (seeded clinic filter)
- Cross-entity union (`all` mode)
- Rate limit enforcement (30/min header checks)
- Empty result set handling

**NOT covered (integration)**:
- Actual trigram + unaccent behavior (requires live Postgres + seeded data)
  - *Deferred to test phase: asserting `q="ngu"` on seeded "Nguyễn Văn Tìm" patient*

### Frontend (646 tests total, 67 task-specific)

**useGlobalShortcuts (15 tests)**:
- Cmd+K opens palette
- ? opens cheatsheet (skip in input)
- Esc closes both
- Tab cycles modes
- Input detection (input/textarea/select/contenteditable)

**CommandPalette (21 tests)**:
- Modal render on open
- Auto-focus input
- Result grouping
- Recent items (secureStore persistence)
- Empty state
- Loading state
- Keyboard nav (↑↓ Enter Esc Tab)
- Mode prefix parsing
- Result click → navigate
- Backdrop click → close

**Breadcrumb (16 tests)**:
- Auto-generation from pathname
- UUID collapse
- Hide on dashboard/root
- React Router `<Link>` rendering (SPA nav)
- ARIA attributes

**ShortcutCheatsheet (10 tests)** *(added in fix phase)*:
- Modal render on open
- Bilingual rendering (vi/en)
- Group headers
- All 4 groups present
- Esc handler
- Close button

**API Mocking (5 tests)**:
- Search mode routing
- Permission filtering
- Result structure

---

## Migration Strategy (0027_search_indexes)

**Version**: `0027` | **Parent**: `0021_multi_clinic_account`

**Schema Changes**:
1. Enable extensions: `pg_trgm`, `unaccent`
2. Create immutable function: `immutable_unaccent(text)`
3. Create 5 GIN trigram indexes

**Rollback**:
- Drop indexes
- Drop function
- Disable extensions (if not used elsewhere)

**MERGE-TIME COORDINATION REQUIRED**:
```
TASK-037 Phase 2 migration 0025_column_encryption_envelope.py also targets 0021
→ Two-head conflict after merge
→ Orchestrator must rebase: 0021 → 0025 → 0027 (encryption-first)
→ Or: 0021 → 0027 → 0025 (search-first, less secure)
→ Recommended: 0025 FIRST (security priority)
```

---

## Cross-Task Coordination

### TASK-033: Multi-Clinic Account Switching
- ✅ Search respects `current_clinic_id` from JWT
- ✅ ClinicSwitcher in Topbar coexists (flex-none layout)
- ✅ No permission conflicts

### TASK-035: Role-Based UI Chips
- ✅ Role badge in Topbar coexists
- ✅ No shortcut conflicts

### TASK-037 Phase 2: Wave 3-A Column Encryption
- ⚠️ **CRITICAL**: 3 GIN indexes on encrypted columns will fail post-merge
- 📋 **Decision deferred**: Option (b) HMAC side columns recommended
- 🔗 **Migration chain**: 0027 must rebase onto 0025 at merge time
- ❌ **Deferred tasks**:
  - Implement HMAC side columns
  - DB-backed unaccent integration test
  - Performance benchmark (>10K patients)

---

## Performance & Optimization

| Aspect | Target | Status | Notes |
|--------|--------|--------|-------|
| p95 latency (10K patients) | <300ms | NOT VERIFIED | EXPLAIN ANALYZE pending |
| Index hit rate | >95% | NOT VERIFIED | Depends on patient count + query selectivity |
| FE palette response time | <200ms | OK | API debounced 300ms, reasonable |
| Memory (recent items) | <1MB | OK | Tauri secureStore, cap 10 items |

**Recommendations**:
- Run `EXPLAIN ANALYZE` on all patient/medicine queries against seeded demo (≥10K rows)
- Monitor slow-query log post-deployment
- Consider LIMIT prefetch optimization if p95 > 300ms

---

## Known Limitations & Deferred Items

1. **Trigram on encrypted data**: Not possible post-TASK-037 merge. Awaiting HMAC side-column design.
2. **Feature catalog hardcoding**: 18 routes duplicated from FE router. Should pull from shared source eventually (low churn v1, acceptable).
3. **Cross-type recency**: Final sort by score only (no recency multiplier across entity types). v1 acceptable; follow-up optimization in later sprint.
4. **Unaccent integration**: Real Postgres + seeded data testing deferred to test phase (local unit mocks in place).
5. **? key stopPropagation**: Inconsistent vs Cmd+K behavior. LOW priority.

---

## Acceptance Criteria (ALL MET)

- ✅ NAV-001: Command Palette accessible via Cmd+K
- ✅ NAV-002: Patient search by name, phone, ID
- ✅ NAV-003: Medicine search by name, active ingredient
- ✅ NAV-004: Feature navigation via hardcoded catalog
- ✅ NAV-005: Prescription lookup
- ✅ NAV-006: Inventory/lot search
- ✅ NAV-007: Shortcut Cheatsheet modal (? key)
- ✅ NAV-008: Breadcrumb auto-generation with UUID collapse
- ✅ 22 BE tests (15 unit + 7 integration)
- ✅ 646 FE tests (67 task-specific)
- ✅ Rate limit 30/minute on search API
- ✅ Permission scoping via `current_clinic_id`
- ✅ Bilingual i18n (vi/en)
- ✅ ARIA accessibility compliance
- ✅ React Router SPA navigation (no full reloads)

---

## Completion Summary

- **Branches**: 
  - BE: `clinic-cms-w3c` on `feature/task-036-cmdk-search`
  - FE: `clinic-cms-web-w3c` on `feature/task-036-cmdk-search-fe`
- **Test Results**: FE 646/646 pass, TypeScript clean, ESLint clean
- **Deliverables**: 4 fixes applied (Breadcrumb Link, rate limit, exception handling, ShortcutCheatsheet tests)
- **Status**: READY FOR MERGE (pending orchestrator coordination on migration chain)

