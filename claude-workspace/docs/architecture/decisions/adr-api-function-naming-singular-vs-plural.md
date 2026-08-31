# ADR: Singular vs Plural API Functions — Screen Purpose Drives Contract

**Date:** 2026-09-01  
**Status:** Documented (from TASK-146 design)  
**Related:** TASK-146 (PrescriptionsTab), TASK-145 (doctor's PrescriptionTab)  
**Audience:** Frontend API designers, screen/component owners

---

## Problem

During TASK-146 implementation, a critical design decision had to be made:

The doctor's prescribing screen (`PrescriptionTab.tsx`) and the patient's prescription history tab (`PatientDetailPage.tsx`'s `PrescriptionsTab`) both need prescription data for the same visit. But they need **different subsets of that data**:

| Screen | Needs | Example |
|--------|-------|---------|
| **Doctor's PrescriptionTab** (prescribing) | **Only the active prescription** to edit | Visit has 3 prescriptions: [cancelled, cancelled, pending]. Doctor needs only `pending`. |
| **Patient's PrescriptionsTab** (history) | **All prescriptions** (including cancelled) to show what was tried and corrected | Patient needs to see: `cancelled` (what was wrong), `pending` (what was corrected). |

**The Trap:** Both could call the same API endpoint `GET /visits/{visit_id}/prescriptions` (which returns all prescriptions, including cancelled). The doctor's screen would then need to **filter client-side** to get just the active one.

**Why this is dangerous:**

If the doctor's screen forgets the client-side filter, it shows **all prescriptions** (including cancelled) to the doctor while editing. The doctor could:
- Accidentally re-edit a cancelled prescription
- Get confused by multiple versions
- Commit the wrong prescription to the system

This creates a "works but wrong" bug: the API is correct, but the screen misuses it.

---

## Solution: Function Naming Drives Intent

**Rule:** Give functions **explicit names** that match the screen's business intent. Never make a caller guess what a function returns by reading its source.

### Pattern: Singular = Filter, Plural = Full List

**For the doctor's screen (editing):**
```typescript
// Name explicitly signals: "get the ONE prescription I can work with"
const prescription = await doctorApi.getVisitPrescription(visitId);
// Returns: Prescription | null
// Behavior: filters status !== "cancelled", returns newest active, or null
// Call sites: PrescriptionTab.tsx (doctor editing), PrintPrescriptionModal, VisitDetailPage
```

**For the patient's screen (history):**
```typescript
// Name explicitly signals: "get ALL prescriptions for audit trail"
const {items, total} = await doctorApi.getVisitPrescriptions(visitId);
// Returns: PrescriptionListResponse
// Behavior: returns all (draft, pending, cancelled), srt by prescribed_at, no filtering
// Call sites: PatientDetailPage.tsx's PrescriptionsTab (patient history)
```

### Backend Matches Frontend

The backend also has **two separate routes** that serve the same semantic pattern:

**Doctor's edit screen:**
```python
@router.get("/{visit_id}/prescription", response_model=Optional[PrescriptionResponse])
async def get_visit_prescription(visit_id: UUID, db: AsyncSession):
    # Returns the newest active prescription for the doctor to edit
    # Filter: status != 'cancelled'
    # Logic: query().where(...).order_by(desc(created_at)).first()
```

**Patient's history:**
```python
@router.get("/{visit_id}/prescriptions", response_model=PrescriptionListResponse)
async def get_visit_prescriptions(visit_id: UUID, db: AsyncSession):
    # Returns all prescriptions for the audit trail
    # No status filter
    # Logic: query().order_by(asc(prescribed_at)).all()
```

---

## Application to TASK-146

### The Original Bug (Before TASK-146)

`PatientDetailPage.tsx` (history tab) was calling:
```typescript
const prescription = await doctorApi.getVisitPrescription(visitId);  // ← singular (WRONG)
// This returns only the newest active prescription
// So if a visit had [cancelled, pending], only pending was shown
```

**Result:** The patient's history was incomplete and misleading.

### The Fix (TASK-146)

Changed `PatientDetailPage.tsx` to call:
```typescript
const {items} = await doctorApi.getVisitPrescriptions(visitId);  // ← plural (CORRECT)
// This returns all prescriptions, including cancelled
```

The doctor's screen (`PrescriptionTab.tsx`, which also needs prescriptions) continues to use:
```typescript
const prescription = await doctorApi.getVisitPrescription(visitId);  // ← singular (CORRECT)
// Doctor only sees the active one to edit
```

### Why Renaming Was Better Than Adding a Filter

**Tempting but wrong approach:**
```typescript
// Anti-pattern: caller must remember to filter
const allRx = await doctorApi.getVisitPrescriptions(visitId);
const activeRx = allRx.items.filter(p => p.status !== 'cancelled').pop();
// ↑ Easy to forget this filter in one call site; creates silent bugs
```

**Better (what TASK-146 did):**
```typescript
// Each caller gets exactly what it needs, by function name
const activeRx = await doctorApi.getVisitPrescription(visitId);   // singular
const allRx = await doctorApi.getVisitPrescriptions(visitId);     // plural
// ↑ No ambiguity; every call site gets the right data by default
```

---

## Design Principles

### 1. **Function Name = Contract**

The function's name must unambiguously describe what it returns, so a developer can use it correctly without reading the source.

**Good:**
- `getUser()` — one user (current user, or by ID)
- `getUsers()` — list of users
- `getVisitPrescription()` — one prescription (the active one)
- `getVisitPrescriptions()` — all prescriptions

**Bad:**
- `getPrescription()` / `getPrescriptions()` — doesn't say whether it filters or not
- `getRx()` — abbreviation obscures intent; is it one or all?
- `loadPrescriptionData()` — too generic; doesn't say what's returned

### 2. **Singular = Filtered/Computed, Plural = Raw List**

When you have two functions for the same entity:

| Singular | Plural |
|----------|--------|
| Returns a **single item** (or null) | Returns a **list** |
| Often **filtered** by business logic | Returns **all matching** records (no filter) |
| Caller uses when they know what they want | Caller uses when they need to inspect or iterate |
| Example: `getUser()` (current user), `getVisitPrescription()` (active one) | Example: `getUsers()` (all users), `getVisitPrescriptions()` (all, incl. cancelled) |

### 3. **One Function Per Screen Purpose**

Never make a single function try to serve two different screens. Create dedicated functions:

```typescript
// WRONG:
const rx = await doctorApi.getVisitPrescription(visitId, { includeHistory: true });
// ↑ One function with a flag; caller must remember the flag per screen

// RIGHT:
const rx = await doctorApi.getVisitPrescription(visitId);        // doctor
const rxList = await doctorApi.getVisitPrescriptions(visitId);   // history
// ↑ Explicit functions; caller can't mix them up
```

---

## Detection: Code Review Checklist

When reviewing API client code, ask:

- [ ] Function name matches what it returns? (singular = 1 item, plural = list)
- [ ] Every call site using it for the right purpose? (search for all call sites)
- [ ] Backend has a matching function with the same singular/plural convention?
- [ ] Tests verify the exact behavior (filtering, ordering, count)?
- [ ] Could a developer new to the codebase understand by reading the function name alone?

---

## Related Patterns

### When You Have > 2 Functions

If you need more than just "one active" and "all", use explicit suffixes:

```typescript
// All variations explicit:
getVisitPrescription()           // newest active
getVisitPrescriptions()          // all
getVisitPrescriptionsForPrint()  // printable (excludes cancelled)
getVisitPrescriptionsDraft()     // draft only
```

Each function name describes exactly what it does. No surprises.

### Client-Side vs Server-Side Filtering

**Rule: Prefer server-side.**

If the backend can do the filtering (knows the business logic), make it do it. This keeps client-side code simple and prevents bugs from forgotten filters.

```typescript
// Anti-pattern (client-side filtering):
const allPrescriptions = await api.getVisitPrescriptions(visitId);
const active = allPrescriptions.items.filter(p => p.status !== 'cancelled').pop();

// Better (server-side filtering):
const active = await api.getVisitPrescription(visitId);  // backend does the filter
```

---

## References

- **TASK-146 decision D-1:** Why `draft` is excluded from history and `cancelled` is included
- **Implementation evidence:** 
  - `clinic-cms-web/src/modules/doctor/api.ts:165-181` (singular, for doctor editing)
  - `clinic-cms-web/src/modules/doctor/api.ts:190-191` (plural, for history)
  - `clinic-cms-web/src/pages/patients/PatientDetailPage.tsx:299-353` (uses plural, filters `draft`)
  - `clinic-cms-web/src/components/doctor/PrescriptionTab.tsx:696-702` (uses singular)
- **Test evidence:** 
  - `src/tests/doctor/api.test.ts` (verifies singular filters cancelled)
  - `src/tests/patients/PrescriptionsTab.test.tsx` (verifies plural shows all)

---

## Lessons Learned

1. **Function names are API contracts.** Invest time in naming; it prevents bugs.
2. **Don't try to build one function that serves multiple purposes.** Create separate functions with clear names.
3. **Code review must check: does this call site need all data, or just one item?** If the code wants one, use the singular function.
4. **Sync naming across frontend and backend.** If backend has `GET /visits/{id}/prescription` (singular), frontend should have `getVisitPrescription()` (singular).

