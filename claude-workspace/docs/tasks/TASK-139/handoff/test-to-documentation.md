# Handoff: TASK-139 → Documentation Agent

**From**: Test Agent
**To**: Documentation Agent
**Status**: DOCUMENTING

## Summary

All tests PASSED (round 2, after BUG-001 was found in round 1 and fixed). BE (`_feat139-be @ 37b258d`)
and FE (`_feat139-web @ d271e00`) are ready for documentation.

## Test Results

- **Round 1** (BE `37b258d`, FE `d59942f`): everything passed except one AC — "Không regression
  PayrollPage hiện có" — due to BUG-001 (footer `colSpan` misalignment). BE full unit suite (1156
  passed / 12 pre-existing baseline failures, 0 new), BE integration on a disposable stack (22/22,
  including mixed pay-type reconciliation, real two-clinic cross-tenant isolation, forged `X-Clinic-Id`,
  `doctor`-role RBAC, 9 malformed-`month` variants, formula-injection neutralisation), FE full vitest
  (1282/1282 vs baseline + 21/21 new tests), i18n vi/en parity clean.
- **Round 2** (FE `d271e00` only — BE unchanged, not re-run): verified BUG-001's fix directly in the
  diff (`colSpan` 14→13) and confirmed the new regression test in `PayrollPage.export.test.tsx` genuinely
  asserts the footer total lands under "Thực nhận" (ties to the header's actual position, not a
  hardcoded/tautological count). Full FE suite: 1283 passed / 3 pre-existing failures (QueuePage×2,
  ForgotPasswordPage×1), zero new failures.
- **Total**: 29 scenarios across both rounds (test-cases.md), all PASS.
- Test report: `docs/tasks/TASK-139/deliveries/test-reports/test-report.md`
- Test cases: `docs/tasks/TASK-139/deliveries/test-cases/test-cases.md`

## Notes for Documentation

- **Blended commission rate columns (m2/m3, from code review)** — user decision on record: **KEEP
  AS-IS**. The Excel export's `Tỷ lệ HH thủ thuật (%)` / `Tỷ lệ HH thuốc (%)` columns (and the matching
  rate on `PrintablePayslip`) are *derived* (`commission / revenue × 100`), so a staff member earning
  commission across multiple service types at different rates shows a revenue-weighted **blend**, not a
  literal configured rate. Likewise `Nguồn tỷ lệ` ("Riêng"/"Chung") reflects whether **at least one**
  contributing line used an override, not all. This should be **documented explicitly** wherever the
  export columns are described (final-specs, user-facing help text), since accounting could otherwise
  misread the percentage as "the configured rate." See `implementation-to-review.md`'s "Fix round 1"
  section for the full rationale.
- Route path is `GET /api/v1/payroll/export` (not nested under `/hr/payroll/...`) — intentional, matches
  the sibling export-endpoint convention (`/staff/export`, `/attendance/export`, etc.), confirmed
  correct by code review — not a typo, no need to flag as an inconsistency in docs.
- PDF generation is entirely client-side (browser print → Save as PDF), consistent with
  `PrintableInvoice`/`PrintablePrescription` — no new BE dependency.
- Known non-blocking follow-ups (not TASK-139 bugs, don't need fixing before docs): m5 (unknown
  `rate_source` blanks instead of falling back to raw value — cosmetic), n1 (a `per_shift`
  commission-only staff with `shift_rate=null` shows no count row on the printable payslip — edge case,
  arguably correct), and the TASK-140 follow-up on shared e2e DB fixture-leak/teardown (see test-report's
  "Fixture-leak / teardown observation" section — a repo-wide, pre-existing pattern, not specific to
  TASK-139).
