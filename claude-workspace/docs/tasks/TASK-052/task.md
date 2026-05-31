---
id: TASK-052
type: feature
title: Tài liệu API mapping theo function list (461 fn × 26 module) + audit gap test toàn bộ BE + fix bug
status: IN_PROGRESS
priority: High
assigned: chiendv
created: 2026-05-29
updated: 2026-05-30
branch: "fix/TASK-052-test-encryption-fixtures"
jira_key: ""
tags: [backend, api-docs, testing, audit, bugfix, qa]
affected-repos: [clinic-cms-merge]
refs:
  detail_design: ""
  implementation_plan: ""
  figma: ""
  confluence: ""
  jira_ticket: ""
  other:
    - "scripts/function_list_data.py  # NGUỒN function list — 461 function, 26 group (AUTH..THEME)"
    - "scripts/generate_function_list_xlsx.py  # generator xlsx từ function_list_data.py"
    - "docs/tasks/TASK-032/deliveries/final-specs/audit-report.md  # audit BE/FE trước đó — tham chiếu gap"
    - "docs/tasks/TASK-032/handoff/be-audit-report.md  # BE audit chi tiết"
    - "PROJECT.md  # build/test commands, module map (../clinic-cms-merge là main worktree)"
---

# TASK-052: Tài liệu API mapping theo function list + audit gap test toàn bộ BE + fix bug

## Description

Dựa vào **function list** (`scripts/function_list_data.py` — 461 function trên 26 module: AUTH, RBAC, TENANT, PATIENT, APPT, VISIT, VITAL, SVC, MED, RX, PHRM, BILL, HR, RPT, NOTI, JOB, AUDIT, CFG, DATA, DIAG, NAV, THEME, INT, SUB, PLT, NFR), thực hiện 3 việc:

1. **API Mapping Document** — Lập tài liệu ánh xạ **từng function code → endpoint API backend** tương ứng (method + path + permission gate + service/router file). Đánh dấu function nào CHƯA có API (gap), function nào có API nhưng lệch spec.
2. **Test toàn bộ BE (audit gap + viết test bổ sung)** — Chạy toàn bộ pytest hiện có, đối chiếu 461 function với coverage thực tế, **viết test bổ sung** cho các function chưa được cover (ưu tiên integration/e2e real-DB theo Testing Strategy của PROJECT.md).
3. **Fix bug** — Sửa các bug làm fail test (cũ + mới viết). Tuân thủ **Database Error Handling Protocol** trong CLAUDE.md (dừng & báo user trước khi sửa query/data nghi vấn).

> **Phạm vi test đã chốt với user (2026-05-29)**: *Audit gap + viết test thiếu* — không chỉ chạy suite cũ mà còn bổ sung test cho function chưa cover.
>
> **Target codebase**: `../clinic-cms-merge` (main-branch worktree — "what's actually shipped on main"), KHÔNG dùng `../clinic-cms` (stale feature branch). Xem PROJECT.md.

## Requirements

- [ ] Đọc & parse function list từ `scripts/function_list_data.py` (461 function, fields: group/code/name/brief/detail/role/phase/task/status)
- [ ] Lập **API mapping table** mỗi function → `{method, path, permission, router_file, service_file, status: MAPPED|GAP|DRIFT}` → lưu `deliveries/api-specs/api-mapping.md`
- [ ] Liệt kê **gap report**: function chưa có API endpoint + function có API nhưng lệch spec (DRIFT)
- [ ] Chạy toàn bộ pytest hiện có trên `clinic-cms-merge` (unit + integration + e2e), ghi nhận pass/fail baseline
- [ ] **Coverage audit**: đối chiếu 461 function ↔ test thực tế, xác định function chưa được cover
- [ ] **Viết test bổ sung** cho function chưa cover — integration/e2e real-DB (Postgres + Redis thật, KHÔNG mock — theo PROJECT.md override #4)
- [ ] Fix bug làm fail test; mọi sửa đổi liên quan data/query phải theo Database Error Handling Protocol
- [ ] Đảm bảo quality gates: test pass rate 100%, coverage new ≥80% / overall ≥70%, `ruff check` + `mypy` pass

## Acceptance Criteria

- [ ] `deliveries/api-specs/api-mapping.md` bao phủ đủ 461 function với trạng thái MAPPED/GAP/DRIFT rõ ràng
- [ ] Gap report được duyệt với user (function nào cần build API mới được tách thành sub-task / follow-up, KHÔNG tự ý implement ngoài phạm vi)
- [ ] Toàn bộ pytest pass 100% (0 failure) trên container `clinic_cms_api`
- [ ] Test bổ sung cho function chưa cover đã được viết & pass; coverage đạt gate
- [ ] Tất cả bug tìm thấy đã fix (hoặc ghi nhận thành bug report nếu out-of-scope) trong `bugs/`
- [ ] `ruff check app tests` + `mypy app` pass; build pass (`/auto-build check`)

## Progress Checklist

- [ ] Implementation (API mapping doc + viết test bổ sung + fix bug)
  - [x] **BE test sweep + bugfix** (2026-05-29 → 30): branch `fix/TASK-052-test-encryption-fixtures`
    - [x] Baseline: 20 failed / 1119 passed / **385 errors**
    - [x] Category A (encryption-fixture regression): **385 errors → 0** across 36 files (commit `54d760d`)
    - [x] Real bug fix: reports doctor-performance COALESCE on encrypted column + stale tests (commit `594d563`)
    - [x] Final: **1498 passed / 26 failed / 0 errors**; 26 parked → `handoff/follow-ups.md`
  - [x] **API mapping document** (461 function → endpoint) — DONE 2026-05-30 → `deliveries/api-specs/api-mapping.md`
    - Đối chiếu 461 fn ↔ **207 endpoint** thực tế trên `clinic-cms-merge` (20 router, gồm prescriptions/EMR/ICD-10/medicine-search ban đầu bị miss)
    - **v2 (source-verified)**: 8 cụm DRIFT/GAP/nghi-ngờ đã đọc source xác minh (file:line) qua 8 sub-agent. Kết quả: **200 MAPPED · 24 DRIFT · 85 GAP · 152 N/A** (v1 chưa verify là 227/20/63/151 — ~27 mục MAPPED lạc quan đã hạ xuống GAP/DRIFT)
    - Có Gap report (85) + Drift report (24) + phụ lục inventory 207 endpoint theo module
    - **Dead code phát hiện** (có hàm, chưa nối route): `clone_system_role` (RBAC-008/TENT-004), `smart_queue` (APPT-009), `make_sod_dep` (RBAC-016)
    - **DRIFT/GAP đáng chú ý**: void không hoàn kho (BILL-016), print không phân biệt POS/A4 (BILL-018/019), không check dị ứng khi kê đơn (RX-006), dispense all-or-nothing (PHRM-005), VAT hardcoded 0 (BILL-012), slot capacity stub=2 (APPT-002), reschedule không đổi được giờ (APPT-006)
    - Scope guard giữ nguyên: 85 GAP **không** tự build trong task này — backlog đề xuất tách sub-task
- [ ] Code Review
- [ ] Testing
- [ ] Documentation

## Related Files

- **Input — Function list**: `scripts/function_list_data.py` *(461 function nguồn)*
- **Code (target)**: `../clinic-cms-merge/app/modules/<feature>/` *(main worktree)*
- **Tests**: `../clinic-cms-merge/tests/{unit,integration}/` + `docs/tasks/TASK-052/deliveries/test-cases/`
- **API Mapping (deliverable chính)**: `docs/tasks/TASK-052/deliveries/api-specs/api-mapping.md`
- **Test Report**: `docs/tasks/TASK-052/deliveries/test-reports/test-report.md`
- **Bug reports**: `docs/tasks/TASK-052/bugs/`
- **Handoffs**: `docs/tasks/TASK-052/handoff/`
- **Final Specs**: `docs/tasks/TASK-052/deliveries/final-specs/`

## Timestamps

- **Created**: 2026-05-29

## Notes

- **Scope guard**: Nếu gap report cho thấy nhiều function chưa có API, KHÔNG tự ý build hàng loạt endpoint mới trong task này — đề xuất user tách sub-task. TASK-052 trọng tâm là **tài liệu hoá mapping + test + fix bug** cho những gì đã ship.
- **Module groups (số function)**: NFR(46), SUB(25), PLT(24), BILL(23), PATIENT(22), HR(22), AUTH(22), INT(20), RPT(18), RBAC(18), MED(18), CFG(17), APPT(17), RX(16), NOTI(15), AUDIT(15), VITAL(14), VISIT(14), TENANT(14), JOB(14), PHRM(13), DATA(11), SVC(9), DIAG(9), NAV(8), THEME(3).
- **Lưu ý NFR/PLT/SUB**: nhiều function nhóm này là non-functional / platform / subscription — có thể không map 1-1 với REST endpoint; ghi chú rõ trong mapping (vd: "infra-level", "cross-cutting middleware").
- Tham chiếu audit BE trước đó: `docs/tasks/TASK-032/handoff/be-audit-report.md` để tránh lặp lại phát hiện cũ.

## Blockers

None
