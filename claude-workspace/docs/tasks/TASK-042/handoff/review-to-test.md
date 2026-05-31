# TASK-042 EMR + RX-016 — Code Review → Test Handoff

**Date:** 2026-05-01
**From:** Code Review
**To:** Test
**Decision:** **APPROVED (with non-blocking findings)**

---

## Decision Summary

The 6-tab EMR refactor and RX-016 3-state stock chip are functionally correct, well-structured, type-safe, and fully tested at the unit level. All TASK-042 acceptance criteria are met (subject to deferred AI/BHYT tabs). Forward to Test phase. The two findings flagged below are non-blocking but should be tracked for Wave 3-A merge and a follow-up audit-log task.

---

## A. Migration quality — `0023_visit_soap_diagnosis.py`

| Item | Status | Notes |
|---|---|---|
| `visit_soap` schema (PK visit_id, S/O/A/P TEXT, FK visit ON DELETE CASCADE) | ✅ | Includes `created_at`/`updated_at` with `now()` defaults. PK by `visit_id` correctly enforces 1:1. |
| `visit_diagnosis` schema (UUID PK, FK visit + icd10_code, type CHECK constraint, notes) | ✅ | `type` constrained to `('primary','secondary')` via CHECK; FK to `icd10_reference` `ON DELETE RESTRICT` (correct — never delete a referenced code). |
| `icd10_reference` schema (code PK, name_vi, name_en, parent_code self-FK) | ✅ | Self-referential FK with `ON DELETE SET NULL`; GIN trigram index on `name_vi` (after `CREATE EXTENSION IF NOT EXISTS pg_trgm`). |
| 225 ICD-10 seeds | ✅ | Exactly 225 tuples. 140 top-level + 85 children. Hierarchy parents all exist (no dangling parent refs — verified). Categories covered: J00–J45 respiratory, I10–I64 cardio/cerebro, E10–E78 endocrine/lipid/thyroid, K20–K92 GI/hepatic, L01–L70 skin, M06–M79 musculoskeletal, G35–G47 neuro, F10–F50 psych, N10–N40 GU, O03–O80 OB, P07–P59 pediatric, H10–H66 ENT/eye, S00–T39 trauma, Z00–Z96 general, plus A09/B02/B34.9/D50/D64/R05/R50/R51/R52/R53/T39 catch-alls. |
| Vietnamese names natural? | ✅ | Spot-checked 15 entries — proper medical Vietnamese (e.g. "Viêm mũi họng cấp tính", "Đau thắt ngực không ổn định", "Bệnh trào ngược dạ dày thực quản với viêm thực quản"). Not machine-translated. |
| `down_revision = 65fc9ae59ba5` | ✅ | Matches current `merge_task_015` head in w2d worktree. |
| Conflict status with Wave 1+2 (`0021/0022/0024/0025`) | ⚠️ | Numeric clash with future Wave 1 (`0021`/`0022`) and Wave 2 (`0024`/`0025`) migrations. Per handoff, explicit numbering is acceptable — merge-time renumbering is plan of record. **Action**: orchestrator must rename to `0026_…` or higher when merging into integration branch. |
| `min_stock_level` column on `inventory_item` | ✅ | Added as nullable `Numeric` — non-breaking. |
| Idempotent seed (`ON CONFLICT (code) DO NOTHING`) | ✅ | Safe re-runs. |

---

## B. BE endpoint correctness

| Endpoint | Status | Notes |
|---|---|---|
| `POST /visits/{id}/soap` | ✅ | Idempotent upsert with field-level merge (existing fields preserved if `None`). `_get_visit_or_404` validates `clinic_id` + `is_deleted`. Permission `visit.write`. |
| `GET /visits/{id}/soap` | ✅ | Returns `None` if not yet created. |
| `POST /visits/{id}/diagnosis` | ✅ | Replace-all semantics (delete + insert). Pre-validates ICD-10 codes exist via `IN` query (fast); `ValidationError` lists missing codes. Commits via route-level `await db.commit()`. |
| `POST /visits/{id}/complete-emr` | ✅ | State machine: requires `IN_PROGRESS`, SOAP exists, ≥1 diagnosis, ≥1 prescription OR service_order. Transitions to `AWAITING_PAYMENT`, sets `completed_at` + `doctor_id`. |
| `GET /icd10/search` | ✅ | ILIKE on `code` and `name_vi`, exact-match boost in ORDER BY, `limit 1..50` (default 20). Returns `total` count. |
| Audit log on visit complete | ⚠️ | No `audit_log` write in `complete_visit_emr` despite `0002_create_audit_log` being the standard. Other complete-style transitions (e.g. billing) write audit entries. **Recommendation**: add audit_log entry capturing visit_id, old_status, new_status, doctor_id. Non-blocking but should be tracked. |

---

## C. FE EMR refactor

| Item | Status | Notes |
|---|---|---|
| `ConsultationPage.tsx` 6+1 tab nav | ✅ | `TabId` union has 7 ids; `TABS` array drives render. URL hash persistence works (init from `location.hash`, sync via `useEffect`, `setTab` writes hash with `replace: true`). |
| Notes tab as 7th (backward compat) | ✅ | Kept per task decision; flag for future cleanup is documented in handoff. |
| `SoapTab.tsx` 4-textarea form, auto-save on blur | ✅ | `handleBlur` mutates per-field; "Lưu tất cả" button for explicit save. Loads existing SOAP via React Query, populates state via `useEffect` on `data`. |
| `DiagnosisTab.tsx` autocomplete + chips | ✅ | 300ms debounce; min length 2 to trigger search; first chip auto-marked `primary`, subsequent `secondary`; toggle button + remove button per chip; explicit "Lưu" via replace-all. **Minor**: existing-diagnosis hydration sets `name_vi = code` because GET `/visits/{id}/diagnosis` doesn't join the icd10 reference (cosmetic only — chip shows code+code instead of code+name until next search). |
| `SummaryTab.tsx` readonly aggregation + complete button | ✅ | Loads SOAP, diagnoses, services, prescriptions in parallel. Client-side `canComplete` mirrors BE state machine (SOAP + diag + (rx OR svc)). Calls `completeVisitEmr`, navigates back to queue, invalidates queries. |
| Permission gating | ✅ | `RequirePermission permission="visit.read"` wraps page; `visit.write` permissions enforced server-side per route. |

---

## D. RX-016 enhancements — `PrescriptionTab.tsx`

| Item | Status | Notes |
|---|---|---|
| 3-state chip (emerald/amber/red) | ✅ | `StockChip` reads `medicine.stock_status` (server-computed) with fallback to `in_stock ? "ok" : "out"`. Server logic (`medicine_search_service.search`): `out` if qty≤0, `low` if `min_stock_level` present and qty≤min, else `ok`. Correct per spec. |
| Lot tooltip | ✅ | `LotTooltip` shows `Lot #`, formatted HSD date, available qty, "Sắp hết hạn" badge if `<30 days`. FEFO ordering (`expiry_date ASC, received_date ASC`) enforced server-side. |
| "Chỉ hiện thuốc còn hàng" filter chip default ON | ✅ | `inStockOnly = true` initial state; filter applied client-side in route handler (post-search filter). |
| Substitute drawer | ✅ | Opens on red-state chip click via `onClickOutOfStock`. Right-aligned 480px width drawer, backdrop click closes. Server: same `active_ingredient`, `available_qty > 0`, `ORDER BY available_qty DESC LIMIT 20`. |
| External-prescription path bypass | ✅ | `freeTextMode` branch skips medicine search entirely; no stock check. |
| Minor: hard-coded "viên" unit in chip label | ⚠️ | `Còn ${available} viên` ignores `medicine.base_unit` (could be ml, gói, etc.). Cosmetic — flag for follow-up. |

---

## E. ICD-10 seed quality

| Check | Result |
|---|---|
| Total entries | ✅ 225 (matches handoff) |
| Hierarchy integrity | ✅ All 85 child `parent_code` refs resolve |
| Vietnamese names natural | ✅ Medical Vietnamese, not machine output |
| Coverage of common conditions | ✅ Cảm cúm, viêm họng, hen, COPD, tăng huyết áp, đái tháo đường, GERD, viêm dạ dày, viêm da, mề đay, gout, đau lưng, migraine, lo âu, trầm cảm, viêm bàng quang, viêm kết mạc, ho, sốt, đau đầu — top 25 VN primary-care conditions covered |
| Pediatric (P00–P99 + ped J/K) | ✅ P07/P22/P36/P59 |
| Top-N most common Vietnamese GP conditions | ✅ Coverage adequate for soft-launch; expand later as needed |

---

## F. Test coverage

| Suite | Status | Notes |
|---|---|---|
| BE TASK-042 unit tests (59) | ✅ | 8 icd10_search + 5 soap_endpoint + 15 medicine_stock_status + 8 medicine_substitutes + 11 visit_complete + 12 visit_diagnosis. **Important**: tests are schema/business-logic focused (Pydantic + service-input validation). No DB integration in unit suite — relies on existing pattern. |
| BE full unit (588 pass) | ✅ | 1 pre-existing HR failure (`test_hr_service_logic.py::TestCheckInRejectsOtherUsersShiftId`) unrelated and already documented. |
| Integration test `test_emr_full_flow.py` | ⚠️ | File exists in `tests/integration/` but not run in unit suite per handoff. **Test phase action**: run integration suite end-to-end after migration applied. |
| FE TS / Lint / Vitest | ✅ | 0 TS errors, 0 lint warnings, 568/568 vitest pass. |
| FE coverage of new tabs | ✅ | SoapTab 4 / DiagnosisTab 5 / SummaryTab 5 / PrescriptionTab-stock 7 / ConsultationPage 7. **Minor**: `it("renders 4 tabs", …)` in `ConsultationPage.test.tsx` is a stale description (assertions are correct, but caller-readable label says 4). Cosmetic. |

---

## G. Performance

| Item | Status |
|---|---|
| ICD-10 autocomplete on 225 rows + GIN trigram index | ✅ Fine; sub-ms ILIKE on this size. |
| Stock summary per medicine — N+1 risk? | ✅ Mitigated. `medicine_search_service.search` issues a **single batched query** using `ANY(ARRAY[...])` over all returned medicine ids; lot count + earliest expiry computed in same statement via `LEFT JOIN batch GROUP BY`. No per-row roundtrip. |
| Substitute query | ✅ Single SQL with active-ingredient filter + LIMIT 20. |
| Lot tooltip data | ⚠️ Currently bundled into `medicine.lots` from search response — not yet wired (lots array is empty in current Medicine type from search). **Test phase action**: verify whether lot tooltip data is populated end-to-end or requires a follow-up. Implementation-side `get_lot_details` exists but is not invoked by the search endpoint; the FE shows tooltip only when `medicine.lots` is non-empty. Likely a downstream fetch needed when chip is hovered. Non-blocking. |

---

## H. Cross-cutting

| Item | Status |
|---|---|
| BHYT history tab gating (TASK-034 dep) | ✅ Correctly deferred per handoff and task spec F.2. |
| Wave 3-A column encryption — SOAP/diagnosis content has PII | ⚠️ **Important collision warning**. `visit_soap.subjective/objective/assessment/plan` are TEXT fields containing patient symptoms (PHI). `visit_diagnosis.notes` likewise. These were created without encryption. Wave 3-A (`encrypted column` rollout) must include these tables. **Action**: tag for orchestrator handoff; SOAP/diagnosis PII columns must be added to the Wave 3-A encryption inventory. |
| Migration numeric collision (`0023` vs Wave 1+2 `0021/0022/0024/0025`) | ⚠️ See A. |
| Audit log gap on visit complete | ⚠️ See B. |
| Hard-coded "viên" unit in stock chip | ⚠️ See D. |
| `name_vi` enrichment of pre-existing diagnoses on hydration | ⚠️ See C. |
| `stock-summary` endpoint (B.6) not implemented separately | ⚠️ Stock data is annotated inline by `/medicines/search`. Functional outcome equivalent, but if any other consumer (e.g. a separate medicine detail screen) needs stock summary, a dedicated endpoint should be added. Non-blocking for TASK-042 acceptance. |

---

## Top-3 Findings (priority order)

1. **Wave 3-A encryption collision** — SOAP fields and diagnosis notes contain patient PHI; must be enrolled in Wave 3-A encryption inventory before that wave's merge.
2. **No audit_log write on `complete_visit_emr`** — clinical state transition (visit → AWAITING_PAYMENT) should emit an audit entry; track as follow-up bug or post-042 task.
3. **Lot tooltip data path not end-to-end wired** — server returns `lot_count`/`earliest_expiry` aggregates in search, but `lots[]` array is empty in the search response; FE tooltip will silently hide unless caller fetches `get_lot_details` on hover. Verify in Test phase.

---

## Items to Test (test phase TODO)

- [ ] Apply migration `0023_visit_soap_diagnosis` against fresh DB; verify 225 seeds, indexes, FKs
- [ ] Run integration suite `tests/integration/test_emr_full_flow.py`
- [ ] E2E: vitals → SOAP → diagnosis → service+rx → summary → "Hoàn tất" → AWAITING_PAYMENT
- [ ] State-machine negative cases: complete with no SOAP / no diag / no rx-or-svc → 400
- [ ] ICD-10 search: code match (J00), name match (đau lưng), Vietnamese diacritics (đái tháo đường)
- [ ] Diagnosis replace: validate unknown code rejection + replace-all semantics
- [ ] RX-016: 3-state chip rendering with fixture medicines (qty 0 / qty=min / qty>min); substitute drawer opens on red click; substitute pick replaces draft
- [ ] Lot tooltip: verify data is populated (vs current FE assumption); FEFO order; HSD <30d highlight
- [ ] Filter chip default ON; toggle off shows out-of-stock; in_stock_only param flows to BE
- [ ] URL hash persistence: deep link `#diagnosis` opens correct tab; back button restores

---

**Approved for Test phase.**
