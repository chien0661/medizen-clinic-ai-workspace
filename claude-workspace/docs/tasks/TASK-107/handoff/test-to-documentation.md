# Handoff: TASK-107 → Documentation Agent

**From**: Test Agent
**To**: Documentation Agent
**Status**: DOCUMENTING
**Date**: 2026-07-24

## Summary
All in-scope tests PASSED. The three acceptance invariants (H-5 deactivation, H-6 password
change/reset, H-7 role revoke) are all genuinely enforced against a real Postgres+Redis stack,
migrated cleanly to alembic head **0067**. No regressions introduced by this fix.

## Test Results
- **Acceptance: 3/3 PASS**
  - H-5: old access token → 401 (PASS)
  - H-6: old access → 401 AND old refresh → 401, new creds work (PASS)
  - H-7: old token → 403 AND fresh login → 403, pivot cleared in DB (PASS)
- **Regression sweep** (`tests/integration -k "auth or rbac or user"`, 196 tests): 183 passed,
  13 failed — **all 13 verified pre-existing** by reproducing the identical failing test IDs on
  a fresh `origin/dev` baseline stack with no TASK-107 code (see test report for the full
  comparison table). Zero new failures.
- Migration: reached **0067 (head)** on a completely fresh DB.
- Test report: `docs/tasks/TASK-107/deliveries/test-reports/test-report.md`

## Environment Notes for awareness
- Isolated Docker stack used: project `v107` (api 9974 / pg 5474 / redis 6456), fully torn down
  (`down -v`) after the run. A second throwaway baseline stack `v107base` (9975/5475/6457) was
  used only to diff-verify pre-existing failures and was also torn down.
- `docker/docker-start.sh` in this worktree checkout has CRLF line endings (local `core.autocrlf`
  artifact) — worked around via a mounted, normalized copy; no source file was modified
  (`git status` on the worktree stayed clean throughout).
- Main/dev/`w2e` stack (ports 9999/5434/5436/6380/6382) was verified untouched before and after.

## Ready for Documentation
Functional design / API spec / final docs can proceed — mechanism is `user.tokens_valid_after`
(DB source of truth) + Redis fast-path `sess:cutoff:{uid}` for access tokens; see
`docs/tasks/TASK-107/handoff/implementation-to-review.md` and `review-report.md` for full
mechanism detail and file list.
