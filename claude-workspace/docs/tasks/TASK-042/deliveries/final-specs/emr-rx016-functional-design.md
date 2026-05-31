# Thiết kế chức năng EMR 6-tab + RX-016 Stock

**Task:** TASK-042  
**Ngày hoàn thành:** 2026-05-01  
**Trạng thái:** DONE  
**Chi nhánh:** feature/task-042-emr-rx016 (BE), feature/task-042-emr-rx016-fe (FE)

---

## I. Mục đích

Triển khai giao diện EMR (Electronic Medical Record) 6 tab chính cho trang khám bệnh, kế thừa từ yêu cầu EMR 8-tab trong spec chung, đồng thời nâng cấp RX-016 (chức năng chip tồn kho 3 trạng thái với tooltip lô và đề xuất thuốc tương đương).

---

## II. Phạm vi

### Tabs Được Triển khai (6/8)

| Tab | Trạng thái | Mô tả |
|-----|-----------|-------|
| Vitals (Dấu hiệu sống) | Existing | Tái sử dụng từ phiên bản trước |
| SOAP | NEW | 4 field S/O/A/P; tự động lưu khi rời focus |
| Diagnosis (Chẩn đoán) | NEW | Autocomplete ICD-10 + chip; xóa/sửa; lưu toàn bộ (replace-all) |
| Services (Dịch vụ) | Existing | Tái sử dụng từ phiên bản trước |
| Prescription (Đơn thuốc) | Enhanced | RX-016: chip 3 trạng thái + tooltip lô (FEFO) + drawer đề xuất |
| Summary (Tóm tắt) | NEW | Readonly aggregation + button "Hoàn tất khám" |
| Notes (Ghi chú) | Kept | 7 tab; giữ lại để backward compatibility, sẽ cleanup sau |
| AI Suggestions | DEFERRED | Kế hoạch tương lai |
| BHYT History | DEFERRED | Phụ thuộc TASK-034 (merge BHYT) |

---

## III. Schema + Migration

### Bảng mới (`0023_visit_soap_diagnosis.py`)

**Down-revision:** `65fc9ae59ba5`

#### 1. visit_soap
```sql
CREATE TABLE visit_soap (
    visit_id UUID PRIMARY KEY REFERENCES visit(id) ON DELETE CASCADE,
    subjective TEXT,
    objective TEXT,
    assessment TEXT,
    plan TEXT,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
)
```
- **1:1 với visit** (idempotent upsert per visit)
- Chứa PHI (patient history, examination findings) → **Wave 3-A encryption scope**

#### 2. visit_diagnosis
```sql
CREATE TABLE visit_diagnosis (
    id UUID PRIMARY KEY,
    visit_id UUID NOT NULL REFERENCES visit(id) ON DELETE CASCADE,
    icd10_code VARCHAR NOT NULL REFERENCES icd10_reference(code) ON DELETE RESTRICT,
    type VARCHAR CHECK (type IN ('primary', 'secondary')),
    notes TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
)
```
- **N:M visit ↔ ICD-10** (replace-all semantics)
- `type` constraint đảm bảo 'primary' hoặc 'secondary'
- Chứa notes (PHI) → **Wave 3-A encryption scope**

#### 3. icd10_reference
```sql
CREATE TABLE icd10_reference (
    code VARCHAR PRIMARY KEY,
    name_vi VARCHAR NOT NULL,
    name_en VARCHAR,
    parent_code VARCHAR REFERENCES icd10_reference(code) ON DELETE SET NULL,
    created_at TIMESTAMP
)
CREATE INDEX ix_icd10_name_vi_trigram ON icd10_reference USING GIN (name_vi gin_trgm_ops)
```
- **225 seeds** (140 top-level + 85 child)
- Hierarchy: J (respiratory) + I (cardio/cerebro) + E (endocrine) + K (GI) + L (skin) + M (musculoskeletal) + G (neuro) + F (psych) + N (GU) + O (OB) + P (pediatric) + H (ENT/eye) + S (trauma) + Z (general) + catch-all
- GIN trigram index → tìm kiếm diacritics nhanh

#### 4. inventory_item — min_stock_level
```sql
ALTER TABLE inventory_item ADD COLUMN min_stock_level NUMERIC(10,2) NULL;
```
- Non-breaking (nullable)
- RX-016 sử dụng để xác định "sắp hết"

---

## IV. API Endpoints

### BE (TASK-042 scope)

#### SOAP Management
- **POST /visits/{id}/soap** — idempotent upsert; merge field-level
  - Request: `{ subjective?, objective?, assessment?, plan? }`
  - Response: `{ visit_id, subjective, objective, assessment, plan, ... }`
  - Permission: `visit.write`
  - Behavior: nếu field là `null` → không ghi đè

- **GET /visits/{id}/soap** — fetch SOAP (hoặc null nếu chưa tạo)
  - Response: VisitSoap | null

#### Diagnosis Management
- **POST /visits/{id}/diagnosis** — replace-all (xóa hết, insert lại)
  - Request: `{ diagnoses: [ { icd10_code, type, notes? } ] }`
  - Response: array diagnoses
  - Validation: code phải tồn tại trong icd10_reference; lỗi nếu code bị mất
  - Permission: `visit.write`

- **GET /visits/{id}/diagnosis** — fetch diagnoses
  - Response: `[ { id, icd10_code, type, notes } ]`
  - **Note:** không join icd10 name (cosmetic gap; FE hiển thị code lần 2)

#### Visit Complete (State Machine)
- **POST /visits/{id}/complete-emr** → transition IN_PROGRESS → AWAITING_PAYMENT
  - Preconditions: SOAP exists + ≥1 diagnosis + (≥1 rx OR ≥1 service)
  - Sets: `status=AWAITING_PAYMENT`, `completed_at=now()`, `doctor_id=current_user`
  - Response: updated Visit
  - **Finding F2 (non-blocking):** không emit audit_log entry → track as follow-up

#### ICD-10 Autocomplete
- **GET /icd10/search?q=...&limit=20** — ILIKE on code + name_vi
  - Features: exact-match boost, sort by name, limit 1–50 (default 20)
  - Response: `{ items: [ { code, name_vi, name_en, parent_code } ], total, query }`

#### Medicine Stock + Substitutes (RX-016)
- **GET /medicines/search?q=...&with_stock=true** — search + stock annotation
  - Returns: `{ items: [ Medicine ], ... }`
  - Each Medicine: `{ ..., stock_status, available, lot_count, earliest_expiry }`
  - **Data aggregation only** (NOT individual lots — see Finding F3)

- **GET /medicines/{id}/substitutes** — same active_ingredient + in stock
  - Response: `{ items: [ { id, name, code, dosage_form, strength, available } ], total }`
  - Order: DESC available_qty, LIMIT 20

---

## V. Per-Tab Implementation

### 1. Vitals Tab
- **Status:** Pre-existing (TASK-019)
- **Reuse:** `VitalsTab.tsx`

### 2. SOAP Tab
**New component:** `SoapTab.tsx`

- **4 Textarea fields:** Subjective / Objective / Assessment / Plan
- **Auto-save on blur:** `handleBlur` → mutate + POST to `/visits/{id}/soap`
- **"Lưu tất cả" button** để explicit save
- **Load on init:** fetch `/visits/{id}/soap` + populate state via useEffect

### 3. Diagnosis Tab
**New component:** `DiagnosisTab.tsx`

- **Autocomplete:** debounce 300ms; min length 2
- **Search:** GET `/icd10/search?q=...`
- **Chip display:** 
  - First added chip → mark `type='primary'`
  - Subsequent → `type='secondary'`
  - Toggle button per chip để switch primary ↔ secondary
  - Remove button per chip
- **Save:** "Lưu" button → POST `/visits/{id}/diagnosis` (replace-all)
- **Hydration:** existing diagnoses từ GET `/visits/{id}/diagnosis` (shows code + code; name_vi enrichment deferred)

### 4. Services Tab
- **Status:** Pre-existing (TASK-019)
- **Reuse:** `ServicesTab.tsx`

### 5. Prescription Tab
**Enhanced component:** `PrescriptionTab.tsx` (RX-016)

#### 5a. 3-State Stock Chip
```tsx
StockChip({ medicine, onClickOutOfStock })
```
- **Server-computed status:** `medicine.stock_status` from /medicines/search
  - "ok" (emerald) — `available > min_stock_level || min_stock_level not set`
  - "low" (amber) — `0 < available ≤ min_stock_level`
  - "out" (red) — `available ≤ 0`
- **Icons:** CheckCircle / AlertCircle / XCircle
- **Labels:**
  - "Còn {qty} viên" (ok)
  - "Sắp hết {qty} viên" (low)
  - "Hết hàng — đề xuất thay thế" (out, clickable)

#### 5b. Lot Tooltip (FEFO Order)
```tsx
LotTooltip({ lots: LotInfo[] })
```
- **Trigger:** hover chip (not out-of-stock)
- **Display:** Lot # + HSD date + SL + "Sắp hết hạn" badge nếu <30 days
- **Order:** FEFO (earliest expiry first)
- **Data structure:**
  ```ts
  interface LotInfo {
    batch_code: string;
    expiry_date: string;
    available_quantity: Decimal;
    unit_cost?: Decimal;
  }
  ```
- **Status:** ⚠️ **Not yet end-to-end wired** (see Finding F3)

#### 5c. Filter Chip — "Chỉ hiện thuốc còn hàng"
- **Default:** ON (`inStockOnly = true`)
- **Behavior:** client-side filter post-search; param `in_stock_only=true` to API
- **Toggle:** user can turn off to see out-of-stock

#### 5d. Substitute Drawer
```tsx
SubstituteDrawer({ medicine, onClose, onSelect })
```
- **Trigger:** click on red (out-of-stock) chip
- **Width:** 480px, right-aligned, backdrop dismiss
- **Query:** GET `/medicines/{id}/substitutes`
- **Content:** list {name, code, dosage_form, strength, available}
- **Action:** click → replace draft medicine with selected substitute

#### 5e. External Prescription (Free-text)
- **Bypass:** `freeTextMode` branch skips medicine search entirely
- **No stock check** for external

### 6. Summary Tab
**New component:** `SummaryTab.tsx`

- **Readonly aggregation:** loads SOAP + diagnoses + services + prescriptions in parallel
- **Display:**
  - SOAP: 4-line block
  - Diagnoses: chips (primary vs secondary colored)
  - Services: list
  - Prescriptions: table
- **State check:** client-side mirror of BE state machine (SOAP + diag + (rx OR svc))
- **Action:** "Hoàn tất khám" button
  - POST `/visits/{id}/complete-emr`
  - On success: navigate back to queue, invalidate queries
- **Permission:** `visit.write` (server enforced)

---

## VI. RX-016 Stock Chip — 3-State Logic

### BE Logic (medicine_search_service.py)

```python
if available_qty <= 0:
    status = "out"
elif min_stock_level and available_qty <= min_stock_level:
    status = "low"
else:
    status = "ok"
```

### FE Display

| Status | Color  | Icon          | Label                          |
|--------|--------|---------------|--------------------------------|
| ok     | emerald | CheckCircle   | "Còn {qty} viên"              |
| low    | amber   | AlertCircle   | "Sắp hết {qty} viên"          |
| out    | red     | XCircle       | "Hết hàng — đề xuất thay thế" |

### Test Coverage
- **15 tests** `test_medicine_stock_status.py` — fixture medicines with qty 0 / qty=min / qty>min
- **8 tests** `test_medicine_substitutes.py` — active_ingredient match, available_qty filter
- **7 tests** `PrescriptionTab-stock.test.tsx` — chip rendering, substitute drawer, filter toggle

---

## VII. Kiểm thử

### Backend (59 task-specific + 588 full suite)
- ✅ 8 tests ICD-10 search (code match, name match, diacritics)
- ✅ 5 tests SOAP endpoint (upsert, merge, not found)
- ✅ 15 tests medicine stock status (qty 0/low/ok → out/low/ok)
- ✅ 8 tests medicine substitutes (active ingredient match, qty>0)
- ✅ 11 tests visit complete (state machine, preconditions)
- ✅ 12 tests diagnosis (replace-all, code validation)
- ✅ Full suite: 588 passed (1 pre-existing HR failure unrelated)

### Frontend (54 test files, 568 tests)
- ✅ TypeScript: 0 errors
- ✅ ESLint: 0 warnings
- ✅ Vitest: 568/568 passed
- Coverage per-tab:
  - SoapTab: 4 tests
  - DiagnosisTab: 5 tests
  - SummaryTab: 5 tests
  - PrescriptionTab-stock: 7 tests
  - ConsultationPage: 7 tests

### Integration (Deferred to Test phase)
- [ ] Apply migration 0023 → fresh DB
- [ ] Run `tests/integration/test_emr_full_flow.py`
- [ ] E2E: vitals → SOAP → diagnosis → service+rx → summary → complete → AWAITING_PAYMENT

---

## VIII. Những Phát hiện Từ Code Review (Non-Blocking, Track as Follow-up)

### F1: Wave 3-A Encryption Collision
**Issue:** SOAP + diagnosis content chứa PHI (patient symptoms, medical notes)
- Được tạo WITHOUT encryption
- Wave 3-A phải include these tables in encryption scope
- **Action:** Tag for orchestrator; add to encryption inventory before Wave 3-A merge

### F2: Audit Log Gap
**Issue:** `complete_visit_emr` không emit audit_log entry
- Quy trình state transition (IN_PROGRESS → AWAITING_PAYMENT) không được log
- Các complete-style transitions khác (billing) có audit entries
- **Action:** Track as post-042 bug fix / audit task

### F3: Lot Tooltip Data Path Not End-to-End Wired
**Issue:** `medicine_search.search` returns aggregates only
- Returns: `lot_count`, `earliest_expiry` (summary stats)
- Does NOT return: `lots[]` array (individual batch details)
- BE has `get_lot_details` service function but **not exposed as endpoint**
- FE LotTooltip checks `hasLots = medicine.lots.length > 0`
- **Result:** Tooltip silently hides when lots array is empty
- **Recommendation:** Either:
  - A) Wire `get_lot_details` as endpoint + FE fetch on hover, or
  - B) Include lots array in search response (larger payload), or
  - C) Fetch as separate query post-search
- **Status:** Non-blocking for TASK-042 acceptance; flag for follow-up wire-up

---

## IX. Quyết định Deferred

| Item | Reason | Reference |
|------|--------|-----------|
| BHYT History tab | Blocked on TASK-034 BHYT merge completion | TASK-034 |
| AI Suggestions tab | Post-042 feature | Future task |
| Notes tab cleanup | Kept as 7th tab for backward compat; remove later | Future cleanup task |
| SOAP/diagnosis encryption | Wave 3-A scope expansion | Wave 3-A orchestration |

---

## X. Migration Conflict (Merge Note)

**0023_visit_soap_diagnosis** numeric ID collides with Wave 1+2 migrations:
- Current: `0023`
- Future: `0021`, `0022`, `0024`, `0025`

**Resolution:** Orchestrator must renumber to `0026_...` or higher at merge time into integration branch.

---

## XI. Chỉ số + Metrics

| Metric | Giá trị |
|--------|--------|
| Task-specific BE tests | 59 |
| Full BE suite | 588 |
| FE test files | 54 |
| FE tests | 568 |
| ICD-10 seed codes | 225 (140 top-level + 85 child) |
| ICD-10 categories | 14 (J, I, E, K, L, M, G, F, N, O, P, H, S, Z, etc.) |
| Tabs delivered | 6 (Vitals + SOAP + Diagnosis + Services + Prescription + Summary) |
| Tabs deferred | 2 (AI Suggestions + BHYT History) |
| Backward-compat tabs | 1 (Notes, as 7th) |
| Code review findings | 3 (all non-blocking) |

---

## XII. Cấu trúc Dự Án

**Backend:** `E:\MyProject\clinic-cms-workspace\clinic-cms-w2d` → `feature/task-042-emr-rx016`

**Frontend:** `E:\MyProject\clinic-cms-workspace\clinic-cms-web-w2d` → `feature/task-042-emr-rx016-fe`

**Workspace:** `E:\MyProject\clinic-cms-workspace\claude-workspace\docs\tasks\TASK-042\`

