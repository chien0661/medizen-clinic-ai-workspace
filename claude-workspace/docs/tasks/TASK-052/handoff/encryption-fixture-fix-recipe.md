# TASK-052 — Encryption Fixture Fix Recipe (Category A)

**Goal**: make integration test fixtures work after TASK-037 column encryption.
**Validated on**: `tests/integration/visits/test_visits_api.py` (24/24 pass — use as reference).
**Scope**: edit ONLY files under `tests/`. NEVER touch `app/` source or the uncommitted
super-admin WIP. Fix ONLY the encryption-fixture problem; do not fix logic/permission
failures (those are Category B / super-admin WIP — just report them).

---

## Why tests error

TASK-037 made these columns `EncryptedString` (stored BYTEA, encrypted with a
per-tenant DEK resolved from the `current_clinic_id` ContextVar):

- **User**: `email`, `phone`, `full_name`, `license_number`
- **Patient**: `full_name`, `phone`, `email`, `id_number`, `address_line`, `ward`, `district`, `province`
- **Clinic**: `address`, `phone`, `email`, `tax_code`, `bhyt_facility_code`

Fixtures insert these rows directly (bypassing TenancyMiddleware), so encryption fails with:
- `RuntimeError: current_clinic_id ContextVar is not set` (ORM insert, context missing), or
- `LookupError: No DEK found for tenant ...` (no DEK minted), or
- `DataError: a bytes-like object is required, not 'str'` (raw SQL writing plaintext into BYTEA).

## The 4 rules

### 1. Imports (add what you use)
```python
from app.core.crypto import mint_dek_for_tenant
from app.core.tenancy import with_tenant_context
from app.modules.patients.models.patient import Patient   # if seeding patients
from app.modules.users.models.user import User            # usually already imported
from app.modules.users.models.clinic import Clinic        # usually already imported
```

### 2. Mint a DEK per clinic, and COMMIT it before any encrypted flush
The DEK is read by a **separate sync engine** inside the envelope resolver → it only
sees committed rows. So mint + commit BEFORE inserting encrypted rows.
```python
async with factory() as session:
    session.add(Clinic(id=clinic_id, code=..., name=..., specialty=..., is_active=True))
    await session.flush()                       # clinic encrypted cols are None → safe
    await mint_dek_for_tenant(clinic_id, session)
    # ...mint for EVERY clinic the fixture creates (clinic_b, etc.)...
    await session.commit()
```
`mint_dek_for_tenant(tenant_id, db)` is async, idempotent (ON CONFLICT DO NOTHING).

### 3. Insert encrypted ORM rows INSIDE `with_tenant_context`, and flush INSIDE it
Encryption fires at **flush/commit**, not at `session.add()`. The context active at
flush time decides the DEK. Each row must be encrypted under ITS OWN clinic's context.
```python
with with_tenant_context(clinic_id):
    session.add(User(id=..., clinic_id=clinic_id, full_name="...", ...))
    await session.flush()                        # <-- flush inside the context
with with_tenant_context(clinic_b_id):           # different clinic → its own block
    session.add(User(id=..., clinic_id=clinic_b_id, full_name="...", ...))
    await session.flush()
await session.commit()
```

### 4. Convert raw-SQL inserts of encrypted tables to ORM
Raw `text("INSERT INTO patient/user/clinic ...")` that sets an encrypted column writes
plaintext into a BYTEA column → fails. Convert to an ORM insert under tenant context:
```python
# BEFORE: await session.execute(text("INSERT INTO patient (... full_name ...) VALUES (...)"))
with with_tenant_context(clinic_id):
    session.add(Patient(id=pid, clinic_id=clinic_id, patient_code="...",
                        full_name="...", gender="male", birth_year=1990))
    await session.flush()
await session.commit()
```
Tables WITHOUT encrypted columns (`user_role`, `account_clinic_role`, `role`, `visit`,
`invoice`, etc.) can STAY raw SQL — no change needed.

> Note: a `Clinic(...)` that sets only `code/name/specialty/is_active` (no
> address/phone/email/tax_code/bhyt_facility_code) needs NO context — those encrypted
> cols are None. Only wrap clinic inserts that actually set an encrypted clinic column.

## Per-file procedure
1. Find every encrypted insert in the file: `User(`, `Patient(`, encrypted-`Clinic(`,
   and raw `INSERT INTO user|patient|clinic`. Check BOTH fixtures AND inside test methods.
2. Apply rules 1–4. Mint DEK once per clinic per fixture/setup block.
3. Run: `docker exec clinic_cms_w2e_api pytest <file> -q --tb=short -p no:cacheprovider`
4. Iterate until **0 errors**. Remaining FAILED (not ERROR) that trace to RLS/auth/
   superadmin/lockout/permissions are **Category B** — leave them, note them in your report.

## Reference
Read `tests/integration/visits/test_visits_api.py` (already fixed) for a worked example
of all 4 rules, including a multi-clinic fixture and inline-in-test inserts.
