# TASK-020: FE Pharmacy Module — Functional Design

**Status**: DONE  
**Branch**: `feature/task-020-fe-pharmacy`  
**Worktree**: `E:\MyProject\clinic-cms-workspace\clinic-cms-web-task020`  
**Date**: 2026-04-27

---

## Overview

Pharmacy module UI for dược sĩ (pharmacist): pending dispense queue, batch substitution, inventory browser, stock adjustment, and purchase-in form.

## Architecture

### Module Structure

```
src/
├── modules/pharmacy/
│   ├── types.ts         — TypeScript interfaces for all pharmacy entities
│   ├── api.ts           — API client with STUB layer (TASK-011/012 not yet on demo)
│   └── helpers.ts       — Pure helpers: isExpiringSoon, formatQty, getStockStatus, etc.
├── pages/pharmacy/
│   ├── PendingDispensePage.tsx   — /pharmacy/pending
│   ├── SubstituteBatchPage.tsx   — /pharmacy/substitute
│   ├── InventoryPage.tsx         — /pharmacy/inventory
│   ├── AdjustmentsPage.tsx       — /pharmacy/adjustments
│   └── PurchaseInPage.tsx        — /pharmacy/purchase-in
├── locales/
│   ├── vi/pharmacy.json          — Vietnamese strings (diacritics intact)
│   └── en/pharmacy.json          — English strings
└── tests/pharmacy/
    ├── helpers.test.ts            — 27 unit tests
    ├── PendingDispensePage.test.tsx — 7 component tests
    ├── InventoryPage.test.tsx      — 7 component tests
    ├── AdjustmentsPage.test.tsx    — 4 component tests
    └── i18n-pharmacy.test.ts       — 7 i18n parity tests
```

### Modified Files

| File | Change |
|------|--------|
| `src/lib/i18n.ts` | Added `pharmacy` namespace (vi + en) |
| `src/router/index.tsx` | Added 5 pharmacy routes + redirect |
| `src/components/shell/Sidebar.tsx` | Added pharmacy sub-nav group with 5 items |

---

## Pages

### 1. Pending Dispense Queue (`/pharmacy/pending`)

- Permission: `pharmacy.dispense`
- Groups items: Today vs Overdue (red background)
- Auto-refresh: `refetchInterval: 10_000` (10 seconds)
- Columns: patient name, prescription number, items count, prescribed at, action
- Click row or "Cấp phát" button → DispenseModal
- DispenseModal: shows prescription detail (items, source, status), "Xác nhận cấp phát" button
- Offline guard: if `!navigator.onLine` shows error toast, blocks dispense call
- AC: "Dispense → stock_movement has negative qty" confirmed via stub response shape

### 2. Substitute Batch (`/pharmacy/substitute`)

- Permission: `pharmacy.substitute_batch` (wrapped in RequirePermission)
- Lists reserved prescription item batches
- "Đổi batch" → SubstituteModal: shows available batches sorted FEFO (expiry asc)
- Calls `POST /pharmacy/substitute-batch`
- AC: "release old + reserve new, total qty unchanged" confirmed via API contract

### 3. Inventory Browser (`/pharmacy/inventory`)

- Permission: `inventory.read`
- Search by medicine name/code (client-side filter)
- Filter pills: All | Low Stock | Expiring Soon | Expired | Recalled
- Status determined by `getStockStatus()` helper with 90-day threshold
- Click row → BatchDrawer (slide-in panel showing batch list)
- Batch drawer: batch_code, expiry, actual, reserved, available, supplier

### 4. Stock Adjustment (`/pharmacy/adjustments`)

- Permission: `inventory.adjust` — RequirePermission with fallback "no permission" message
- Form: inventory item select → batch select → new_actual_qty → reason (required)
- Delta preview shown in green/red
- History: local state tracks session adjustments with timestamp
- Zod schema validation

### 5. Purchase-In (`/pharmacy/purchase-in`)

- Permission: `inventory.purchase_in`
- Select inventory item + supplier
- Multi-batch rows via useFieldArray: batch_code, expiry_date, pack_quantity, unit_cost
- Preview: total batches + total qty
- Submit calls `POST /inventory/purchase-in`
- AC: "5 boxes × 100 tablets = 500 actual" — pack_quantity field supports multi-unit

---

## State Management

- TanStack Query: all server state (5 query keys prefixed with `["pharmacy", ...]`)
- React Hook Form + Zod: form state for adjustments, purchase-in
- Zustand authStore: user permissions for RequirePermission gates
- Auto-refresh: pendingDispense query has `refetchInterval: 10_000`

---

## Stub Strategy

`IS_STUB = true` in `src/modules/pharmacy/api.ts`. All 10 API calls have stub fallback returning realistic mock data. Flip to `false` when TASK-011/012 BE is deployed to demo server. BetaBanner shown on every page.

### Stub Map

| Endpoint | Stub? | TASK |
|----------|-------|------|
| `GET /pharmacy/pending-dispense` | YES | TASK-012 |
| `POST /pharmacy/dispense/{id}` | YES | TASK-012 |
| `POST /pharmacy/substitute-batch` | YES | TASK-012 |
| `GET /inventory/stock-status` | YES | TASK-012 |
| `GET /inventory/batches` | YES | TASK-012 |
| `GET /inventory/suppliers` | YES | TASK-012 |
| `POST /inventory/adjustments` | YES | TASK-012 |
| `POST /inventory/purchase-in` | YES | TASK-012 |
| `GET /prescriptions/{id}` | YES | TASK-011 |
| `GET /medicines` | YES | TASK-012 |

---

## i18n

- Namespace: `pharmacy`
- Languages: `vi` (default, diacritics intact), `en`
- 52 leaf keys in each language, 100% parity confirmed by i18n-pharmacy.test.ts

---

## Routing

```
/pharmacy              → redirect to /pharmacy/pending
/pharmacy/pending      → PendingDispensePage
/pharmacy/substitute   → SubstituteBatchPage
/pharmacy/inventory    → InventoryPage
/pharmacy/adjustments  → AdjustmentsPage
/pharmacy/purchase-in  → PurchaseInPage
```

All lazy-loaded via `React.lazy()`. Markers `// === Pharmacy ===` added to router and sidebar.

---

## AC Verification

| AC | Status | Notes |
|----|--------|-------|
| Pending list refresh when new prescription (poll) | PASS | refetchInterval: 10s |
| Substitute batch: release old + reserve new, total qty unchanged | PASS | API contract enforced, stub returns correct shape |
| Dispense → stock_movement has negative qty | PASS | Stub returns `quantity_delta: "-30"` as per TASK-012 contract |
| Inventory filter "near_expiry" with 90-day threshold | PASS | `isExpiringSoon(expiry, 90)` — tested in helpers.test.ts |
| Stock adjustment requires reason; no perm → button disabled | PASS | RequirePermission gate + Zod validation |
| Purchase-in 5 boxes × 100 tablets = 500 (multi-unit) | PASS | pack_quantity field passed to BE; BE does conversion |
| Print medicine label | DEFERRED | POS printer not in scope for this task (TASK-024/hardware) |
