# TASK-116: Print-Template RBAC — Read/Write Asymmetry Fix

## Issue
Print template permissions were asymmetric and overly restrictive:

**READ asymmetry**:
- `prescription.print` gate locked out all non-prescribing roles (e.g., cashier, pharmacist couldn't read invoice/pharmacy templates)
- Superadmin couldn't read templates after creating them

**WRITE asymmetry**:
- Only `settings.clinic` could create, but the gate was also applied incorrectly

## Fix Applied
Rebalanced READ and WRITE gates by document type:

### READ (per-document-type):
- **invoice** → cashier, receptionist (invoice.read via existing document print flow)
- **prescription** → doctor, nurse (prescription.print)
- **exam_form** → doctor, nurse (visit.read for layout, non-PHI)
- **Writer bypass**: Any role with WRITE permission can READ back their own template

### WRITE (unchanged):
- Requires `settings.clinic` (admin/superadmin only)

### Files Changed
- `app/modules/admin/api/routes.py`
- `services/print_template_service.py`

## Verification
- **Integration Tests**: 23/23 passed on isolated stack `x116`, role × template_type matrix confirmed
- **Real per-role users** (not admin substitution):
  - Cashier: invoice 200 / prescription 403 ✓
  - Pharmacist: prescription+invoice 200 / exam_form 403 ✓
  - Doctor: prescription 200 ✓
  - Admin (writer): POST → PATCH → GET all 200 (reads back own write) ✓
  - Cashier/pharmacist PATCH: 403 (can't write) ✓

## Result
Printing roles can now read their required templates; writers can read back created templates. No privilege escalation; TASK-094 prescription flow intact.
