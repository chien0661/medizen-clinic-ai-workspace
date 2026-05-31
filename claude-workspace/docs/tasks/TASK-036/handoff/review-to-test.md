---
from: review
to: test
date: 2026-05-01
decision: CHANGES_REQUESTED
reviewer: code-review
task: TASK-036
scope: Cmd+K Quick Search (NAV-001..008)
---

# Code Review — TASK-036 Cmd+K Quick Search

**Decision: CHANGES_REQUESTED** (test phase blocked on a couple of high-priority items; most code is solid).

Branches reviewed:
- BE: `clinic-cms-w3c` on `feature/task-036-cmdk-search` (uncommitted working tree)
- FE: `clinic-cms-web-w3c` on `feature/task-036-cmdk-search-fe` (uncommitted working tree)

Note: the impl-handoff `impl-to-review.md` referenced in the brief was not produced; review is based on direct code inspection + task.md acceptance criteria.

---

## A. Search service correctness

| Item | Status | Note |
|------|--------|------|
| Patient name fuzzy match (`immutable_unaccent` + trigram >= 0.3) | OK | `_search_patients` uses `func.similarity(immutable_unaccent(lower(full_name)), immutable_unaccent(lower(q))) >= 0.3` |
| Phone trigram | OK | Conditional on digit-ish input (`q.replace(' ','').isdigit() or len(q)>=4`) — sensible gate |
| `patient_code` exact-prefix ILIKE | OK | Score 0.85 (constant) |
| `id_number` ILIKE | OK | Score 0.90 (constant) |
| Medicine search by name + active_ingredient | OK | `or_(name_similar, active_ingredient_similar, code ilike)` |
| Mode prefix routing (`bn|thuoc|inv|rx|lk|all`) | OK | Literal type validated by Pydantic; unknown mode → 422 |
| Permission filter (`current_clinic_id`, RBAC perm set) | OK | Uses `rbac_service.get_user_effective_permissions(user_id, clinic_id)` per request — clinic-scoped |
| Recency boost | PARTIAL (warn) | Within a single mode the SQL `ORDER BY` includes `updated_at DESC` as tiebreaker, but the **final cross-entity sort** is `score` only — no recency multiplier across types. Acceptable for v1; consider adding a small recency factor in a follow-up. |
| Deduplication | OK | `(type, id)` key, keep highest score |
| Empty/whitespace query short-circuit | OK | Returns `[]` without DB hit |
| `_search_prescriptions` defensive try/except | WARN | Catches **bare `Exception`** and silently returns `[]` — masks legitimate errors. Recommend at least logging the exception or scoping to `(ImportError, AttributeError)`. |
| `_search_features` scoring | OK | In-process, no DB; substring + char-overlap fallback |
| Feature catalog hardcoded | WARN | 18 routes in a Python list — duplicates the FE router config and will drift. Acceptable for v1 (low churn) but should be pulled from a shared source eventually. |

## B. Trigram conflict with TASK-037 Wave 3-A — CRITICAL

**Migration 0027** (TASK-036) and **Migration 0025** (TASK-037 Phase 2) **both have `down_revision = "0021_multi_clinic_account"`** → two heads after merge.

5 trigram GIN indexes are created on plaintext `patient.full_name`, `patient.phone`, `patient.id_number`, `medicine.name`, `medicine.active_ingredient`. After TASK-037 merges, the patient columns become `BYTEA` and TASK-037 explicitly drops 3 GIN indexes (see TASK-037 phase-2 handoff §"Wave 3-C"). Medicine columns remain plaintext — those 2 indexes survive.

**Conflict already documented** at the top of `0027_search_indexes.py` (lines 14-23) and inside `search_service.py` docstring (lines 23-26). Implementation acknowledges the issue but does not resolve it.

**Recommendation: Option (b) — searchable HMAC side columns** for `patient.full_name_hash`, `patient.phone_hash`, `patient.id_number_hash` (deterministic HMAC with a separate per-tenant key, indexable B-tree on hash). Rationale:

- (a) decrypt-then-filter: catastrophic at scale (10K patients × decrypt each row = unacceptable).
- (b) HMAC side columns: enables exact + prefix lookups (CCCD, phone) which are the most common patient lookups; loses fuzzy name matching but Vietnamese name fuzziness can be retained via a `full_name_search_normalized` plaintext column storing only `unaccent(lower(...))` (no PII risk that the raw name doesn't already carry, but deserves a dedicated security review).
- (c) drop on encrypted, keep on medicine: degrades patient UX significantly with no path back.

Either way the **chain conflict** must be resolved at merge time: rebase 0027 on top of 0025, change `down_revision` to `0025_column_encryption_envelope`, and adjust the 3 patient indexes per the chosen option.

## C. CommandPalette component

| Item | Status | Note |
|------|--------|------|
| Modal overlay z-50 | OK | `fixed inset-0 z-50` |
| Max-width 640px (`max-w-2xl`) | OK | Tailwind `max-w-2xl` = 42rem ≈ 672px — close enough; or change to `max-w-[640px]` |
| Top-aligned (`pt-[20vh]`) | OK | |
| Auto-focus on open | OK | `setTimeout(focus, 50)` after open |
| Sub-mode prefix parsing | OK | `parseModePrefix` matches both `"/bn"` exactly and `"/bn "` with trailing space; clean |
| Result groups + section headers | OK | `groups.{type}` i18n keys |
| Keyboard nav (↑↓ Enter Esc Tab) | OK | All implemented in `handleKeyDown` |
| Recent items (Tauri secureStore `RECENT_SEARCH_ITEMS`) | OK | `loadRecentItems` / `saveRecentItem`, capped at 10 |
| Empty state + loading state | OK | Both rendered |
| Custom impl vs cmdk lib | OK | Decision documented in component header; bundle-wise, a custom 391-line component is well under cmdk's 18KB |
| ARIA (`role=dialog`, `aria-modal`, `role=listbox`, `role=option`, `aria-selected`) | OK | Looks correct |
| Backdrop click closes | OK | `e.target === e.currentTarget` guard |

**Finding**: `useEffect` for `loadRecentItems()` on `open` triggers a state update **after** unmount in slow-async tests if the modal closes during the promise. Low impact, but consider an `if (!cancelled)` guard pattern.

## D. useGlobalShortcuts hook

| Item | Status | Note |
|------|--------|------|
| Cmd/Ctrl+K → palette | OK | `(metaKey || ctrlKey) && key === 'k'` |
| `?` → cheatsheet (skips inputs) | OK | `isInputElement(target)` correctly excludes `input/textarea/select/contenteditable` |
| `Esc` → close any | OK | Calls both `onClosePalette` + `onCloseCheatsheet`; intentional fall-through (no `stopPropagation`) |
| `active=false` disables | OK | Early return in `useEffect` |
| Cleanup on unmount | OK | `removeEventListener` in cleanup |
| Handlers in dep array | OK | All four destructured callbacks listed — bug claimed fixed during rescue is verified |

**Finding (minor)**: `Cmd+K` calls both `e.preventDefault()` AND `e.stopPropagation()`, but the `?` branch only calls `preventDefault()`. Inconsistent — recommend stopPropagation on `?` as well to avoid surprising third-party shortcuts.

## E. Breadcrumb (NAV-008)

| Item | Status | Note |
|------|--------|------|
| Auto-generates from `useLocation().pathname` | OK | |
| Hides on `/dashboard` and `/` | OK | `HIDE_ON_ROUTES` set |
| UUID segment collapse into prev crumb | OK | Regex `^[0-9a-f]{8}-...` + `^[a-f0-9]{24,}$` |
| Static `SEGMENT_META` table | OK | Acceptable v1 approach; documented |
| Last crumb `aria-current="page"` | OK | |
| 16 tests | OK | (counted) |

**Finding (minor)**: Breadcrumb uses raw `<a href>` instead of React Router `<Link>` — clicking causes a full page reload. Should be `<Link to={...}>`. Functional bug.

## F. ShortcutCheatsheet (NAV-007)

OK — modal w/ groups (Global, Palette, Doctor, Pharmacy), bilingual via `i18n.language === 'vi'` toggle. Esc handler local to the component. No tests file located for this component (Breadcrumb has tests, ShortcutCheatsheet does not). **Add basic render + Esc test.**

## G. AppShell + Topbar integration

- `useGlobalShortcuts` mounted at `AppShell.tsx` — correct level (above all routed pages, below auth).
- Topbar layout becomes: `ClinicSwitcher (flex-none) · ⌘K button · spacer (flex-1) · OnlineStatus · Notifications · Lang · Theme · User`. Visually sensible. **Confirmed no collision with TASK-033 ClinicSwitcher.**
- `Topbar.tsx` previously had ClinicSwitcher in `flex-1` (took remaining width). Changed to `flex-none` + new spacer — verify on mobile widths during test phase that the ⌘K button collapses gracefully (icon-only via `hidden sm:inline`).

## H. Performance

| Item | Status | Note |
|------|--------|------|
| p95 < 300ms on 10K patients fixture | NOT VERIFIED | No benchmark run; integration tests use 1 patient. **Test phase must run against the demo seed (`scripts/seed-demo.ts`) and capture EXPLAIN ANALYZE for the patient name query.** |
| Index hit rate | NOT VERIFIED | Same — needs EXPLAIN ANALYZE |
| Per-endpoint rate limit | MISSING | No `@limiter.limit(...)` on `/api/v1/search`. Inherits global rate limit only. Recommend adding `30/minute` per user — search is fired on every keystroke (debounced 300ms) and is a fan-out query across 4 tables. |

## I. Test quality

- BE: 15 unit + 7 integration tests counted in source. Unit tests fully mock `db.execute` — covers permission gating, mode routing, dedup, recency-via-score, empty query, Vietnamese unaccent (`"ngu"` → `"Nguyễn"`). **Integration tests do NOT exercise the actual unaccent + trigram path** because asserting trigram results requires real Postgres data; they only do structural checks (`isinstance(patient_results, list)`). Acceptable for unit coverage but **the unaccent claim is currently only verified at the mock layer**. Test phase should add at least one DB-backed assertion that `q="ngu"` returns the seeded "Nguyễn" patient.
- FE: 67 new tests (15 useGlobalShortcuts + 21 CommandPalette + 16 Breadcrumb + 15 search api). Boundary cases covered. Mock isolation OK.
- **Full FE suite verified: 635/635 pass; tsc clean; eslint clean** (executed during this review).
- BE tests not executed in this review env (Python 3.10 lacks `datetime.UTC` used elsewhere — pre-existing, not TASK-036).

## J. Cross-cutting collisions

| Concern | Status |
|---------|--------|
| Topbar layout coexistence (TASK-033 ClinicSwitcher + ⌘K button + notifications + avatar) | OK |
| AppShell shortcut listener vs other listeners | OK (document-level keydown, no propagation conflict) |
| TASK-033 multi-clinic perm scoping → search filter uses `current_clinic_id` from JWT | OK (verified in `search_service.py` + `routes.py`) |
| TASK-037 trigram conflict | UNRESOLVED — see §B |
| Migration revision chain conflict (0025 vs 0027 share parent 0021) | UNRESOLVED — both heads exist |

---

## Required changes before TEST → DONE

1. **(BLOCKING) Decide trigram strategy for encrypted patient columns** (option a/b/c — recommend **b**); document the decision in this report and add a follow-up task to implement it before TASK-037 merges.
2. **(BLOCKING) Resolve migration revision chain**: 0027 must rebase onto 0025 (or whichever lands first).
3. **(HIGH) Breadcrumb** — replace `<a>` with `<Link>` to avoid full page reloads.
4. **(MED) Add per-endpoint rate limit** on `/api/v1/search` (e.g. `30/minute`).
5. **(MED) DB-backed unaccent integration test** asserting `q="ngu"` returns seeded `"Nguyễn Văn Tìm"`.
6. **(MED) Run perf benchmark** against ≥10K patient fixture; capture p95 + EXPLAIN ANALYZE.
7. **(LOW) Replace bare `except Exception`** in `_search_prescriptions` with scoped exceptions + logging.
8. **(LOW) Add render test** for `ShortcutCheatsheet`.
9. **(LOW) `?` keypress** — add `e.stopPropagation()` for consistency.

Items 1-2 are **BLOCKING for merge**; items 3-6 are **REQUIRED before TEST phase APPROVES**; items 7-9 may be deferred.
