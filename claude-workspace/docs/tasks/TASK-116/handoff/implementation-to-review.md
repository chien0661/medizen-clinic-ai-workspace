# TASK-116 — Implementation → Review Handoff

**Bug (M-11, TASK-095 E2E):** print-template READ/WRITE gates were asymmetric.
READ required a single blanket `prescription.print` permission, so
cashier/receptionist got 403 fetching the **invoice** layout they need to
print invoices, and even a `settings.clinic` writer (incl. superadmin) got
403 reading back the template it had just POSTed 201 (relapse of
BUG-094-001's original fix, which only fixed the doctor/prescription case).

## RBAC scheme chosen

**READ is gated per `template_type`, not by one blanket permission — plus a
writer bypass:**

| template_type | READ permission required |
|---|---|
| `invoice`      | `invoice.read` |
| `prescription` | `prescription.print` |
| `exam_form`    | `visit.read` |

Any caller holding **`settings.clinic`** (the WRITE permission, incl.
superadmin) can always read **any** template type — this is what fixes the
"write 201 then read 403" asymmetry: a writer reads back everything, not just
what maps to their own printing role.

**WRITE is unchanged**: create/update/duplicate/delete remain gated on
`settings.clinic` only (admin/superadmin).

### Why this mapping (not a single broad "any authenticated clinic user" read gate)

Checked the actual permission catalog (`alembic/versions/0007...`,
`0018a_add_prescription_permissions.py`, `0019a_add_billing_permissions.py`,
`0034_seed_cashier_role.py`) rather than assume — turns out **every** system
role (admin, doctor, nurse, pharmacist, receptionist) plus `cashier` already
holds `invoice.read` (billing visibility was granted broadly on purpose in
0019a). So gating `invoice` templates on `invoice.read` is *already* about as
broad as "any staff role" in practice, while still being a real permission
check (a custom/reduced role without `invoice.read` correctly gets 403)
rather than an unconditional bypass. `prescription.print` and `visit.read`
are narrower and reproduce the intended split: pharmacist can read
`prescription` (has `prescription.print`) but not `exam_form` (no
`visit.read`); cashier/receptionist can read `invoice`+`exam_form` (both have
`visit.read`) but not `prescription`.

### Route-level implementation

`require_permission(...)` (a single static-code dependency) can't express
"gate depends on a field of the resource being fetched," so the two GET
routes in `app/modules/admin/api/routes.py` dropped their
`dependencies=[Depends(require_permission("prescription.print"))]` and
instead call a new async helper,
`print_template_service.assert_can_read(db, user_id, clinic_id,
template_type)`, after resolving `template_type` (from the query param for
list, or from the fetched row for GET-by-id):

- `GET /print-templates/{id}` — fetch the template first (so its real
  `template_type` is known), then `assert_can_read`; 403 if it fails.
- `GET /print-templates?template_type=X` — `assert_can_read(X)` before
  querying, same 403 semantics as before, just per-type now.
- `GET /print-templates` (no filter — used by the admin management UI) —
  no single check makes sense here since it spans all types. `settings.clinic`
  holders get the unfiltered list (admin manages everything); everyone else
  gets the list filtered down to only the types their permissions cover
  (`print_template_service.readable_types(effective_perms)`), rather than a
  blanket 403 for a route they're allowed to use for at least one type.

New code lives in `app/modules/admin/services/print_template_service.py`:
`READ_PERMISSION_BY_TYPE`, `assert_can_read()`, `readable_types()`.

## Files changed

- `app/modules/admin/api/routes.py` — print-template GET routes (list + by id).
- `app/modules/admin/services/print_template_service.py` — read-gate map + helpers.
- `tests/integration/admin/test_admin_e2e.py` — new
  `test_print_template_read_gated_by_document_type` (role × template_type
  matrix) + two small test-helper functions (`_create_role_user`,
  `_delete_role_user`) reused from the existing doctor-role test pattern.

## Commit / branch

- Branch `fix/TASK-116-print-template-rbac`, based on `origin/dev` @ `85f70cc`.
- Worktree `F:/MyProject/clinic-cms-workspace/_fix116-be` (left in place for review).
- Commit `5f66694` — `fix(admin): rebalance print-template read/write RBAC so
  printing roles can read + writers can read back (TASK-116)`.
- Pushed: `origin/fix/TASK-116-print-template-rbac`.

## Test results

Isolated Docker stack `fix116` (api 9957 / postgres 5457 / redis 6439),
migrated to head (0069), torn down after:

- New test `test_print_template_read_gated_by_document_type` — **1/1 passed**
  (asserts: writer reads back all 3 types it created; cashier reads
  `invoice` 200 / `prescription` 403, both filtered-list and unfiltered-list
  forms; pharmacist reads `prescription`+`invoice` 200 / `exam_form` 403;
  PATCH stays 403 for both non-writer roles).
- Targeted (`-k print_template`, includes the two pre-existing TASK-094
  tests): **3/3 passed**.
- Full `tests/integration/admin/`: **23/23 passed**.
- `ruff check` on the 3 touched files: 1 finding (`F401` unused `Clinic`
  import in the test file) — confirmed **pre-existing**, identical against
  `origin/dev` (diffed the file as-is from `origin/dev` inside the
  container). **0 new.**
- `mypy` on the 2 touched app files + the test file: **0 errors** in both.

## For the reviewer

- **Please confirm the RBAC scheme is the intended shape.** The task allowed
  either "gate READ per document type" or "gate READ on one broad
  permission"; I picked per-type + writer-bypass because it stays a real
  permission check (denies a hypothetical narrow custom role) while
  happening to be broad in practice for the 6 shipped system roles, and it
  extends the TASK-094 precedent (`prescription.print` for the doctor case)
  symmetrically to `invoice`/`exam_form` instead of replacing it with an
  unconditional gate.
- **`exam_form` → `visit.read`** is a judgment call — there's no
  `exam_form.print`/`visit.print` permission in the catalog, and `visit.read`
  is the closest existing "this role works with visit/exam records"
  permission, held by doctor/nurse/receptionist/cashier (matches
  `PrintExamFormModal.tsx`'s callers) but not pharmacist. Flag if you'd
  rather introduce a dedicated permission instead of reusing `visit.read`.
- No DB/migration changes — this is routing/permission logic only, so no new
  alembic revision.
