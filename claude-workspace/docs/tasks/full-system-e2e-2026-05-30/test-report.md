# Full-System E2E Test Report — Clinic CMS (MediZen)

- **Date**: 2026-05-30
- **Method**: Playwright MCP (interactive browser-driven)
- **Frontend**: http://localhost:1420 (Vite dev, HashRouter)
- **Backend**: http://localhost:8001 (clinic-cms-merge docker stack, seeded DEMO data)
- **Scope**: All screens / routes across all roles; load + core functions + console/network error checks

## Seeded credentials (DEMO clinic)
| Role | Username | Password |
|---|---|---|
| Admin | admin | Demo@1234 |
| Doctor | dr_nguyen | Doctor@1234 |
| Nurse | nurse_lan | Nurse@1234 |
| Receptionist | recept_anh | Recept@1234 |
| Pharmacist | pharm_cuong | Pharm@1234 |
| Cashier | cashier_em | Cashier@1234 |

## Legend
✅ PASS · ⚠️ PASS with warnings · ❌ FAIL · ⏭️ skipped/blocked

---

## Results

### Global / environmental note
⚠️ On **every** page a repeating console error fires: `[useSync] Sync error: Failed to load Tauri SQL plugin. Ensure app is running in Tauri context.` (`src/sync/database.ts:96`). This is **expected** when running the app in a plain browser via Vite dev instead of the Tauri desktop shell — the offline SQLite mirror is unavailable. Not a screen defect; would not occur in the packaged Tauri app. All "console errors" counts below are inflated by this.

### Auth & Dashboard
| # | Screen / Function | Result | Notes |
|---|---|---|---|
| A1 | `/login` — render, i18n (vi) | ✅ | Form, remember-me, forgot-password link, show-password all present |
| A2 | `/login` — login as admin | ✅ | Redirect → `/dashboard`; JWT issued (verified via API too) |
| A3 | `/dashboard` — admin | ✅ | KPI cards, 7-day revenue + visits-by-hour charts, quick actions, attendance widget all render |

### Admin / Catalog
| # | Screen / Function | Result | Notes |
|---|---|---|---|
| AD1 | `/admin/users` | ✅ | 14 users; search, role/status filters, add, row actions (edit/reset-pw/lock/roles/extra-perms) |
| AD2 | `/admin/roles` | ⚠️ | Role list + permission matrix load OK. **BUG (FE)**: React "unique key prop" warning at `RolesPage.tsx:152` — caused by duplicate role codes. **Data**: duplicate roles seeded (system roles + lowercase non-system dupes nurse/receptionist/pharmacist/cashier/admin/doctor) |
| AD3 | `/admin/settings` | ✅ | 7 tabs (general/hours/booking/queue/inventory/prescription/billing) + editable form |
| AD4 | `/admin/vitals` | ⚠️ | 7 vitals, version history, reset-by-specialty, add. **i18n leak**: data-type column shows raw key `vitals.dataTypes.integer` |
| AD5 | `/admin/services` | ⚠️ | ~34 services, CSV import, search, add. **Data**: junk/dup services seeded (e.g. "AA AA AA", `KHAMTQ` vs `KHAM-TQ`) |
| AD6 | `/admin/medicines` | ⚠️ | 87 medicines, search. **i18n leak**: form column shows raw key `medicines.form.dosageForm...` |
| AD7 | `/admin/audit` | ✅ | Hash-chain audit log (TASK-037), object/action/date filters, detail drill-down |

### Reception / Patients
| # | Screen / Function | Result | Notes |
|---|---|---|---|
| R1 | `/patients` — list | ✅ | 47 patients, search, register, per-row "Khám ngay" walk-in. Lots of leftover E2E test data |
| R2 | `/patients/new` — **register patient (function)** | ✅ | Filled name/phone/year → submitted → created **BN0048**, redirected to detail. End-to-end OK |
| R3 | `/patients/:id` — detail | ✅ | 8 tabs (overview/info/guardian/visit-history/prescriptions/invoices/vitals/BHYT), print order + print record buttons |
| R4 | `/appointments` | ✅ | Week/Day calendar, week navigation, slot grid |
| R5 | `/queue` | ✅ | Kanban: Đăng ký 0 / Chờ khám 57 / Đang khám 14 / Chờ TT 0 / Hoàn tất 0; auto-refresh, fullscreen |

### Doctor
| # | Screen / Function | Result | Notes |
|---|---|---|---|
| D1 | `/doctor/queue` | ✅ | Renders (call-next, my/all tabs, 10s auto-reload). Empty for admin (not a doctor). Deep consultation test pending as doctor role |
| D2 | `/doctor/dashboard` | ✅ | Today stats, weekly-trend chart, quick access |

### Pharmacy
| # | Screen / Function | Result | Notes |
|---|---|---|---|
| P1 | `/pharmacy/pending` | ⚠️ | 15 overdue prescriptions, auto-refresh. Dispense modal opens. **UX**: "Số đơn" column shows raw UUID. **Data/?**: opened dispense modal shows Patient/Doctor "—" and empty medicine list (likely orphaned E2E prescriptions) — re-verify in golden-path |
| P2 | `/pharmacy/inventory` | ✅ | ~78 stock items (on-hand/reserved/available/expiry/status), status filter tabs, search |
| P3 | `/pharmacy/adjustments` | ❌ | Form + history render, BUT **BUG**: item `<select>` shows all ~77 options as empty `()` — medicine name/code not rendered, item unselectable |
| P4 | `/pharmacy/purchase-in` | ⚠️ | Batch rows (lot/expiry/qty), preview totals OK. **Same `()` empty-option BUG** in item select. Supplier select only "Không có NCC" (none seeded) |
| P5 | `/pharmacy/substitute` | ✅ | Reserved-items table; medicine names render correctly here; pick-replacement-batch action |
| P6 | `/pharmacy/stocktake` | ✅ | 3-step wizard (prepare/count/reconcile), 77 items, start-count |
| P7 | `/pharmacy/expiry` | ✅ | 30/60/90-day windows, empty state (stock expires 2027) |

### Billing
| # | Screen / Function | Result | Notes |
|---|---|---|---|
| B1 | `/billing/invoices` | ✅ | Status filter, patient search, table. All rows are leftover empty `Nháp` (draft) 0₫ invoices from prior E2E |
| B2 | `/billing/invoices/:id` | ✅ | Draft detail: add-line, issue (correctly disabled when no lines), print, totals, payment history |
| B3 | `/billing/invoice/new` (no visit) | ✅ | Correct guard "Thiếu mã lượt khám" — invoice creation requires a visit context |

### Reports
| # | Screen / Function | Result | Notes |
|---|---|---|---|
| RP1 | `/reports/revenue` | ✅ | Date presets/range, day/week/month grouping, KPI cards, detail table; CSV export disabled when empty. 0₫ (no paid invoices) |
| RP2 | `/reports/inventory` | ✅ | KPIs (low-stock 1, expiring 0, 17 categories), low-stock + expiring-lot lists |
| RP3 | `/reports/doctor-performance` | ✅ | Date filters, comparison chart, detail table, CSV export |
| RP4 | `/reports/visit-volume` | ✅ | Chart + daily table (total/completed/waiting/cancelled/no-show); has data (3/3/60/5 visits) |
| RP5 | `/reports/prescriptions` | ✅ | KPIs (26 total, 18 internal/8 external, 19.2% cancel), in/out pie + top-10 medicines |
| RP6 | `/reports/ar-aging` | ✅ | Aging buckets (0-30/31-60/61-90/>90), total 30.1M₫, distribution chart, per-patient detail |
| RP7 | `/reports/bhyt` | ✅ | Navigated, loaded with 0 errors (snapshot interrupted by MCP disconnect but page rendered) |

### Infra note — Playwright MCP instability
The headed-browser Playwright MCP repeatedly closed the browser between calls and twice disconnected the MCP server entirely, each time requiring a manual `/mcp` reconnect and re-login. Switched `.mcp.json` to `--headless --isolated` for stability before continuing.

### NOT YET TESTED (pending continuation)
- **HR** (7): `/hr/schedule`, `/hr/me/timelog`, `/hr/leave/new`, `/hr/leave/approve`, `/hr/recurring`, `/hr/shift-templates`, `/hr/attendance/export`
- **Notifications** `/notifications`
- **Settings** `/settings`, **Profile** `/profile`
- **Role-based golden path** (deep functional): walk-in → doctor consultation+prescribe (`/doctor/queue`, `/doctor/visits/:id`) → pharmacy dispense (real, fresh Rx) → cashier invoice+payment
- **RBAC**: login as dr_nguyen / pharm_cuong / cashier_em / recept_anh and confirm forbidden routes are gated (403/redirect)
- Multi-clinic switcher, quick-search (Ctrl+K), notifications bell, language toggle (VI/EN), dark mode
