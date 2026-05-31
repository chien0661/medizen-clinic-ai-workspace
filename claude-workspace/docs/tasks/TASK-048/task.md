---
id: TASK-048
type: debt
title: Rà soát + cleanup các tính năng FE đang gắn nhãn Beta
status: TODO
priority: Medium
assigned: Unassigned
created: 2026-05-04
updated: 2026-05-04
branch: ""
jira_key: ""
tags: [fe, audit, beta-cleanup]
affected-repos: [clinic-cms-web]
refs:
  detail_design: ""
  implementation_plan: ""
  figma: ""
  confluence: ""
  jira_ticket: ""
  other: []
---

# TASK-048: Rà soát + cleanup các tính năng FE đang gắn nhãn Beta

## Description

Trên FE (`clinic-cms-web`) hiện có nhiều chỗ gắn nhãn `Beta` (banner, badge, label) — di sản từ các đợt port TASK-018, TASK-039, TASK-040. Cần rà soát toàn bộ và quyết định cho từng chỗ:

- **Complete** → hoàn thiện chức năng + xóa nhãn Beta khỏi UI
- **Keep Beta** → giữ nguyên nhưng ghi rõ lộ trình hoàn thiện trong audit doc
- **Remove** → loại bỏ feature/UI khỏi codebase

Đây là task **debt/cleanup**, không phải feature mới. Có thể không cần qua Test phase đầy đủ (chỉ smoke test sau cleanup).

## Requirements

- [ ] Scan codebase: `grep -r "Beta" clinic-cms-web/src/` + check `BetaBanner`, `BetaBadge` components
- [ ] Lập danh sách: vị trí + module + feature + Beta artifact (banner/badge/label/comment)
- [ ] Với mỗi item, đánh giá:
  - Current implementation state (chưa làm / đang làm / xong nhưng chưa stable)
  - Missing pieces
  - Đề xuất action: complete / keep / remove
- [ ] Document toàn bộ → `docs/tasks/TASK-048/deliveries/final-specs/beta-audit.md`
- [ ] Implement quyết định cho các Beta items được vote "complete" (priority cao) hoặc "remove"
- [ ] Update UI: xóa Beta artifact tương ứng

## Acceptance Criteria

- [ ] `beta-audit.md` liệt kê đầy đủ tất cả Beta items với decision rõ ràng
- [ ] Beta items vote "complete" → đã implement xong + xóa nhãn Beta khỏi UI
- [ ] Beta items vote "remove" → đã xóa khỏi UI + xóa code orphan
- [ ] Beta items vote "keep" → có note rõ ràng (lý do giữ + ETA hoàn thiện) trong audit doc
- [ ] FE không còn Beta artifact nào không được giải trình trong audit doc

## Progress Checklist

- [ ] Investigation: scan + lập danh sách Beta items
- [ ] User review danh sách + chốt action mỗi item
- [ ] Implementation cleanup
- [ ] Smoke test FE (verify không bể UI)
- [ ] Documentation: finalize `beta-audit.md`

## Related Files

- **Input Specs**: `docs/tasks/TASK-048/refs/`
- **Code**: `clinic-cms-web/src/` (toàn bộ FE)
- **Final Specs**: `docs/tasks/TASK-048/deliveries/final-specs/beta-audit.md`

## Timestamps

- **Created**: 2026-05-04

## Notes

**Investigation hints**:
- Recent commit `e7bbfee fix(admin): remove all Beta banners + unused AlertCircle imports` — đã có 1 đợt remove Beta banners trên admin, có thể còn sót ở các module khác
- Modules cần kiểm: reception, EMR, billing, pharmacy, dashboard, settings, audit
- Tìm: `<BetaBanner>`, `<BetaBadge>`, `Beta` text labels, comment `// Beta:`, `// TODO: Beta`

**Workflow note**: Task này có 2 phases user-blocking:
1. Sau "Investigation" → user review danh sách + chốt action
2. Sau "Implementation cleanup" → user verify trước khi close

**Liên quan**: Tách ra từ task gốc TASK-047 (đã narrow scope chỉ còn print).

## Blockers

None
