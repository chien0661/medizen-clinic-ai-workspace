# TASK-019 Functional Design — FE Doctor Module

**Task**: TASK-019  
**Branch**: `feature/task-019-fe-doctor`  
**Status**: DONE  
**Completed**: 2026-04-27

---

## Module Overview

The Doctor module provides UI for the doctor's consultation workflow in Clinic CMS. It covers:

1. **My Queue** (`/doctor/queue`) — list of WAITING and IN_PROGRESS visits
2. **Consultation** (`/doctor/visits/:id`) — full consultation workspace
3. **Doctor Dashboard** (`/doctor/dashboard`) — daily statistics

---

## Pages

### 1. /doctor/queue — My Queue

**File**: `src/pages/doctor/QueuePage.tsx`

**Features**:
- Two tabs: "Của tôi" (visits assigned to current doctor or unassigned) / "Tất cả"
- Visit cards showing: visit_number, status badge, priority badge, chief_complaint preview, wait time
- Auto-refreshes every 10 seconds via TanStack Query `refetchInterval`
- "Gọi bệnh nhân tiếp theo" button → calls `POST /visits/call-next` → redirects to consultation
- Manual refresh button
- Countdown timer showing seconds to next auto-refresh
- Assigned-to-me visits highlighted with brand border

**Permissions**:
- `visit.read` — to see the queue (fallback: access denied message)
- `visit.write` — to see/use the "call next" button

**AC Coverage**:
- AC: "Click Gọi tiếp theo với có visit assigned cho mình → ưu tiên đó trước" ✅
  - Visits assigned to current user sorted first (aMine > bMine in sort), then by priority DESC, created_at ASC

### 2. /doctor/visits/:id — Consultation Page

**File**: `src/pages/doctor/ConsultationPage.tsx`

**Layout**:
- Breadcrumb back to queue
- Patient info header (name, code, age, gender, phone, visit_number, started_at, status)
- Tab panel (4 tabs) + action sidebar

**Tabs**:

#### a) Vitals Tab (`src/components/doctor/VitalsTab.tsx`)
- Shows existing vitals records in timeline with warning icons (⚠️) for out-of-threshold values
- Dynamic form rendered from `GET /vitals/definitions` (STUB)
- Fields grouped by `group_name`, rendered based on `data_type` (integer/number/text/boolean/select)
- Warning icons shown when value > warning_max or < warning_min
- Trend chart available when ≥ 2 records (SVG line chart, no external library)
- Chart selector for different vital keys
- STUB banner visible

#### b) Services Tab (`src/components/doctor/ServicesTab.tsx`)
- Displays current visit services in table with total calculation
- Service search (calls real TASK-010 API)
- Add service with quantity + optional discount (requires discount reason)
- Remove service button (requires `visit.write`)

#### c) Prescription Tab (`src/components/doctor/PrescriptionTab.tsx`)
- Medicine search with in_stock indicator (✓ with qty / ✗ Hết kho)
- Auto-suggests dispense_source: `in_house` if stock ≥ qty, else `external`
- Toggle source override per item
- Free-text item mode (medicine_id = null, always external)
- Stock warning when requested > available with one-click switch to external
- Mixed prescription badge when items have different sources
- Save draft → print preview (STUB)
- STUB banner visible

#### d) Notes & Diagnosis Tab (`src/components/doctor/NotesTab.tsx`)
- Chief complaint textarea
- Clinical notes textarea
- Diagnosis free-text (ICD-10 or description)
- Auto-save with 5s debounce → PATCH `/visits/:id`
- Save status indicator (saving/saved/error)
- Manual "Lưu" button

**Action Sidebar**:
- "Hoàn tất khám" → `POST /visits/:id/complete` → status AWAITING_PAYMENT → navigate to queue
- "Quay về hàng đợi" link
- Patient history placeholder

**AC Coverage**:
- AC: "Hoàn tất khám → status AWAITING_PAYMENT, navigate về my queue" ✅
- AC: "Vitals form cho clinic pediatric hiển thị head_circumference" ✅ (dynamic, depends on definitions from API)
- AC: "Nhập huyết áp 180/100 → icon ⚠️ tooltip Cao hơn ngưỡng" ✅ (checkVitalWarning returns "high" at 180 vs warning_max 140)
- AC: "Search Paracetamol → kết quả với stock indicator" ✅ (STUB data has Paracetamol 500mg ✓ 230 viên, Paracetamol siro ✗ Hết kho)
- AC: "Kê 50 viên Paracetamol (còn 230) → in_house OK" ✅ (suggestSource returns in_house when available ≥ qty)
- AC: "Kê 300 viên → cảnh báo + suggest external" ✅ (stockWarning shown when qty > available)
- AC: "Mixed prescription: 2 in_house + 1 external → dispense_type mixed" ✅ (createPrescription logic)
- AC: "Auto-save notes → reload → notes vẫn còn" ✅ (PATCH visit with debounce)

### 3. /doctor/dashboard — Doctor Dashboard

**File**: `src/pages/doctor/DoctorDashboardPage.tsx`

**Features**:
- 3 stat cards: Chờ khám, Đang khám, Đã khám xong
- Simple SVG bar chart for weekly trend (no external library)
- Auto-refresh every 30s
- Quick link to queue

---

## Routing

**File**: `src/router/index.tsx`

```
/doctor → redirect → /doctor/queue
/doctor/queue → QueuePage
/doctor/visits/:id → ConsultationPage
/doctor/dashboard → DoctorDashboardPage
```

All lazy-loaded with `Suspense` fallback.

---

## Sidebar

**File**: `src/components/shell/Sidebar.tsx`

"Bác sĩ" group (permission: `visit.read`) with sub-items:
- "Hàng đợi của tôi" → `/doctor/queue` (perm: `visit.read`)
- "Bảng điều khiển" → `/doctor/dashboard` (perm: `visit.read`)

---

## i18n

- `src/locales/vi/doctor.json` — full Vietnamese with diacritics
- `src/locales/en/doctor.json` — full English
- Namespace: `doctor`
- Registered in `src/lib/i18n.ts`

---

## Stub Map

| Endpoint | Status | Task | Reason |
|----------|--------|------|--------|
| `GET /vitals/definitions` | STUB | TASK-009 | Not on demo BE |
| `GET /visits/{id}/vitals` | STUB | TASK-009 | Not on demo BE |
| `POST /visits/{id}/vitals` | STUB | TASK-009 | Not on demo BE |
| `GET /medicines/search` | STUB | TASK-012 | Not on demo BE |
| `POST /visits/{id}/prescriptions` | STUB | TASK-011 | Not on demo BE |
| `GET /prescriptions/{id}/print` | STUB | TASK-011 | Not on demo BE |
| `GET /visits` (list) | REAL | TASK-007 | On demo BE |
| `GET /visits/{id}` | REAL | TASK-007 | On demo BE |
| `POST /visits/call-next` | REAL | TASK-007 | On demo BE |
| `POST /visits/{id}/complete` | REAL | TASK-007 | On demo BE |
| `PATCH /visits/{id}` | REAL | TASK-007 | On demo BE |
| `GET /patients/{id}` | REAL | TASK-005 | On demo BE |
| `GET /services` (search) | REAL | TASK-010 | On demo BE |
| `GET /visits/{id}/services` | REAL | TASK-010 | On demo BE |
| `POST /visits/{id}/services` | REAL | TASK-010 | On demo BE |

---

## Known Limitations (v1)

1. **Queue card shows patient_id UUID** — visit list API does not return patient name. Full enrichment requires N+1 GET /patients calls. Deferred to v2 (or when visit list API includes patient_name).
2. **Prescription submit** — fully stubbed; needs TASK-011 merge to demo BE.
3. **Print prescription** — uses stub HTML; needs TASK-011 + Tauri printer integration (TASK-016).
4. **Patient history panel** — placeholder only; needs additional visit history API.
5. **Weekly dashboard chart** — uses mock data; needs aggregate API endpoint.
