---
id: TASK-065
type: bug
title: Fix BUG-003 (GET /visits/{id}/prescriptions → 405) + BE VSS config endpoint
status: DONE
priority: High
assigned: Documentation Agent
created: 2026-05-31
updated: 2026-05-31
branch: ""
jira_key: ""
tags: [backend, frontend, bugfix, emr, vss, prescriptions]
affected-repos: [clinic-cms-merge, clinic-cms-web]
refs:
  detail_design: ""
  implementation_plan: ""
  figma: ""
  confluence: ""
  jira_ticket: ""
  other:
    - "docs/tasks/TASK-053/deliveries/final-specs/functional-audit.md  # §3.5, §3.6"
    - "clinic-cms-web/src/modules/doctor/api.ts:1-14,157-164  # BUG-003 comment + fallback code"
    - "clinic-cms-web/src/pages/admin/VssIntegrationConfigPage.tsx:91,114  # VSS config call"
    - "clinic-cms-merge/app/modules/prescriptions/  # BE prescriptions module"
    - "clinic-cms-merge/app/modules/integrations/  # BE VSS module"
    - "PROJECT.md"
---

# TASK-065: Fix BUG-003 (GET /visits/{id}/prescriptions 405) + BE VSS config endpoint

## Description

2 gap backend đã xác nhận từ TASK-053:

**BUG-003**: `GET /api/v1/visits/{id}/prescriptions` trả **405 Method Not Allowed**. BE có path `/visits/{visit_id}/prescriptions` nhưng chỉ accept `POST` (tạo đơn), không có `GET`. FE `doctor/api.ts` đã ghi nhận lỗi và có workaround:
```
// BUG-003: GET /api/v1/visits/{id}/prescriptions returns 405.
// Fallback: GET /api/v1/prescriptions?visit_id={id}.
// Returns null on any error (empty state).
```
Nhưng `GET /api/v1/prescriptions?visit_id=` cũng không tồn tại trên BE (chỉ có `/prescriptions/{id}`) → tab Kê đơn EMR thường hiện empty state dù đơn đã có.

**VSS config endpoint**: FE `VssIntegrationConfigPage.tsx:114` gọi `GET/PUT /api/v1/admin/integrations/vss/config` để đọc/lưu cấu hình VSS. BE expose `/integrations/vss/status` + `/sync-log` + eligibility/submit-claim nhưng **không có `/config`** và prefix là `/integrations/...` không `/admin/integrations/...`.

## Requirements

### BUG-003 — BE
- [ ] Thêm `GET /api/v1/visits/{visit_id}/prescriptions` → trả prescription(s) của visit
- [ ] Hoặc thêm `GET /api/v1/prescriptions?visit_id={id}` (collection query) — chọn 1 cách nhất quán với schema
- [ ] Phải có permission gate (`visit.read`), RLS, integration test

### BUG-003 — FE
- [ ] Xoá/đơn giản hoá fallback workaround trong `doctor/api.ts:157-164` sau khi BE fix
- [ ] Verify tab Kê đơn (EMR `/doctor/visits/{id}#prescription`) hiển thị đúng đơn thuốc

### VSS config — BE
- [ ] Thêm `GET /api/v1/integrations/vss/config` — đọc cấu hình VSS của clinic hiện tại
- [ ] Thêm `PUT /api/v1/integrations/vss/config` — lưu cấu hình VSS
- [ ] Hoặc đổi prefix FE thành `/integrations/vss/config` (không `/admin/...`) cho thống nhất

### VSS config — FE
- [ ] Chuẩn hoá path call trong `VssIntegrationConfigPage.tsx:114` khớp BE

## Acceptance Criteria

- [ ] `GET /visits/{id}/prescriptions` (hoặc `/prescriptions?visit_id=`) trả đơn thuốc đúng visit
- [ ] Tab Kê đơn trong EMR hiển thị đơn đã tạo (hết empty state sai)
- [ ] `GET/PUT /integrations/vss/config` hoạt động; VssIntegrationConfigPage save/load config thành công
- [ ] Integration tests pass; `ruff check` + `mypy` pass

## Progress Checklist

- [x] Implementation
- [x] Code Review
- [x] Testing
- [ ] Documentation

## Related Files

- **FE EMR**: `clinic-cms-web/src/modules/doctor/api.ts`
- **FE VSS**: `clinic-cms-web/src/pages/admin/VssIntegrationConfigPage.tsx`
- **BE prescriptions**: `clinic-cms-merge/app/modules/prescriptions/`
- **BE integrations**: `clinic-cms-merge/app/modules/integrations/`

## Timestamps

- **Created**: 2026-05-31

## Notes

- BUG-003 đã được FE ghi nhận từ TASK-019/011. Fix BE là giải pháp dứt điểm.
- VSS config path: kiểm tra xem có nên dùng `/admin/integrations/vss/config` (qua admin router) hay `/integrations/vss/config` (qua integration router) — phải nhất quán với permission gate.

## Timestamps

- **Started**: 2026-05-31
- **Implementation Completed**: 2026-05-31
- **Review Completed**: 2026-05-31 (APPROVED → IN_TESTING)
- **Testing Failed**: 2026-05-31 (IN_TESTING → IN_PROGRESS — BUG-001: FE test uses api.patch, impl uses api.put)
- **Testing Completed**: 2026-05-31 (Round 2 — 970/970 tests PASSED → DOCUMENTING)

## Blockers

None
