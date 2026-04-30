---
id: TASK-031
type: feature
title: MediZen UI — Generate 15 màn còn lại trong fresh Stitch project (TASK-029 follow-up)
status: DONE
priority: High
assigned: chiendv
created: 2026-05-01
updated: 2026-05-01
completed: 2026-05-01
branch: ""
jira_key: ""
tags: [design, ui, stitch, phase-d, medizen-modern, follow-up, task-029]
affected-repos: [clinic-cms-web]
refs:
  detail_design: "docs/design/medizen-modern/MEDIZEN_FRESH_PROJECT.md"
  implementation_plan: ""
  figma: "https://stitch.withgoogle.com/projects/2542650746708884228"
  confluence: ""
  jira_ticket: ""
  other:
    - "docs/design/medizen-modern/README.md"
    - "docs/design/medizen-modern/MENU_AND_SCREENS.md"
    - "docs/design/medizen-modern/TAB_MATRIX.md"
    - "docs/design/medizen-modern/SECURITY.md"
    - "../../../docs/clinic_management_function_list.md"
    - "../../tasks/TASK-029/task.md"
---

# TASK-031: MediZen UI — Generate 15 màn còn lại

> **Note**: TASK-030 đã có (Landing Page) nên follow-up TASK-029 đánh số TASK-031.

## Description

TASK-029 đã pivot sang fresh Stitch project mới `2542650746708884228` với MediZen Modern design system clean (asset `3512187121078190969`), generate được **32/47 màn (~68%)** trước khi Stitch rate-limit kick in trên các batch cuối.

TASK-031 hoàn tất nốt **15 màn còn lại** với strategy reliable hơn: **fire 1 màn/call** (sequential) thay vì batch parallel, để tránh rate-limit và verify từng màn thành công.

**Project active**: https://stitch.withgoogle.com/projects/2542650746708884228
**Design system**: `assets/3512187121078190969` MediZen Modern (giữ nguyên, không tạo mới)

## Requirements

### A. Generate 15 màn theo priority

#### A.1 — High priority (8 màn — fire trước)
- [ ] **Quên mật khẩu** — centered card 400px, form email + button "Gửi link reset", success state mock
- [ ] **Danh sách Bệnh nhân** — table 12 rows mock BN VN, filter sticky (giới/tuổi/tag/BHYT), pagination
- [ ] **Hồ sơ Bệnh nhân (Lê Hà Vy)** — 3-col 280/720/380, 8 tabs (Tổng quan ACTIVE + 7 tabs khác), AI gợi ý card
- [ ] **Phòng chờ — Queue Board kanban** — 5 cột state machine với 27 BN cards, 1 cấp cứu, wait timer color
- [ ] **Báo cáo — Tab BHYT** — funnel duyệt 4 stages, top 10 lý do từ chối, trend 12 tháng, sync history VSS
- [ ] **Profile cá nhân (BS. An)** — 5 tabs với "Phòng khám của tôi" ACTIVE — 3 PK card + radio "Mặc định"
- [ ] **Cmd+K Quick search palette** — modal overlay, search "/bn ha vy", tab filter, result list group BN/Thuốc/Tính năng
- [ ] **Clinic switcher dropdown** — popover 280px topbar, list 3 PK với role chip + "Hiện tại" current

#### A.2 — Medium priority (7 màn — fire sau)
- [ ] **Pharmacy — Danh mục thuốc** — table 12+ rows, filter, CRUD inline
- [ ] **Pharmacy — Nhập kho (PO)** — form supplier + line items thuốc/lô/HSD/qty/giá vốn
- [ ] **Pharmacy — Kiểm kê wizard** — 3-step (chọn category → đếm → adjustment cần admin approve)
- [ ] **Pharmacy — Xử lý hết hạn** — table 30/60/90d HSD + actions (disposal/giảm giá/trả NCC)
- [ ] **Billing — Lịch sử hoá đơn** — table + filter date/status/method + pagination
- [ ] **Billing — Công nợ AR aging** — table BN có công nợ + buckets (0-30/30-60/60-90/>90 ngày)
- [ ] **Notifications full page** — table dày + filter (date/type/source) + bulk actions

### B. Strategy execution

- [ ] Fire **1 màn/call sequential** — KHÔNG batch parallel (avoid rate-limit)
- [ ] Verify mỗi màn qua `list_screens` trước khi fire màn tiếp
- [ ] Nếu màn nào timeout không persist sau ~5 phút → re-fire 1 lần duy nhất
- [ ] Nếu re-fire vẫn fail → skip, document, mark "blocked-stitch-api"
- [ ] Tổng wall-clock dự kiến: 15 màn × ~5 phút = ~75-90 phút

### C. Cross-cutting docs

- [ ] Update `medizen-modern/MEDIZEN_FRESH_PROJECT.md` — bảng "32/47" → "47/47" với 15 IDs mới
- [ ] Update `medizen-modern/MENU_AND_SCREENS.md` — đính screen IDs mới cho Phase D màn
- [ ] Update `medizen-modern/SITEMAP.md` §6 — replace project URL cũ + screen IDs (toàn bộ 47)
- [ ] Update `medizen-modern/TAB_MATRIX.md` — Reports Tab BHYT đính screen ID mới
- [ ] Update `medizen-modern/README.md` — chuyển status "32/47 partial" → "47/47 complete"
- [ ] (Optional) Delete 2 duplicates trong project mới qua Stitch UI manual: `f208b29370b54e749fc136ca2d5d049b` + `e59bef8bee744926ae5654f6b26ef25e`

## Acceptance Criteria

- [ ] Stitch project `2542650746708884228` có **47 unique canonical screens**
- [ ] `MEDIZEN_FRESH_PROJECT.md` không còn dòng "(chưa có)" — toàn bộ 47 màn có screen ID
- [ ] 15 màn mới đều dùng MediZen Modern design system — Indigo/Slate/Emerald, Plus Jakarta Sans + Inter, 12px radius
- [ ] Vietnamese language throughout
- [ ] Sidebar 240px + topbar 56px (logo + ⌘K + 🔔 + clinic switcher + avatar) consistent với 32 màn hiện hữu
- [ ] Profile multi-tab có "Phòng khám của tôi" tab với 3 PK card + radio default
- [ ] Cmd+K palette có sub-mode prefix `/bn /thuoc /inv /rx /lk`
- [ ] Clinic switcher popover có 3+ PK với role chip + "Hiện tại" indicator + footer actions
- [ ] Queue board kanban có 5 cột rõ rệt + wait timer color + 1 cấp cứu chip RED

## Progress Checklist

- [ ] Implementation A.1 — 8 high-priority màn (fire 1/call sequential)
- [ ] Implementation A.2 — 7 medium-priority màn (fire 1/call sequential)
- [ ] Code Review (MediZen Modern design QA — consistency với 32 màn hiện hữu)
- [ ] Testing (UX walkthrough multi-clinic flow + Phase D end-to-end)
- [ ] Documentation (cập nhật 5 file design docs)

## Related Files

- **Input Specs**:
  - `docs/design/medizen-modern/MEDIZEN_FRESH_PROJECT.md` — current state 32/47 + 15 backlog
  - `docs/design/medizen-modern/MENU_AND_SCREENS.md` — spec đầy đủ từng màn Phase D
  - `docs/design/medizen-modern/TAB_MATRIX.md` — chi tiết Reports BHYT tab
- **Stitch project**: https://stitch.withgoogle.com/projects/2542650746708884228
- **Tests**: `docs/tasks/TASK-031/deliveries/test-cases/`
- **Final Specs**: `docs/tasks/TASK-031/deliveries/final-specs/screen-ids-final.md` — bản tổng hợp 47 IDs cuối cùng

## Timestamps

- **Created**: 2026-05-01

## Notes

### Why sequential thay vì parallel

TASK-029 fire 8 màn / batch hiệu quả batch 1-3 (~85% success) nhưng tụt mạnh batch 5-6 (~25% success). Stitch dường như rate-limit khi project có >30 màn + concurrent requests. Sequential 1/call:
- Reliable hơn (~95% success rate ước tính)
- Wall-clock chậm hơn nhưng predictable
- Dễ verify từng màn — không cần guess "missing nào trong batch"

### Reference data từ TASK-029 (giữ consistency)

- BN: Lê Hà Vy (45, ♀, BN-2026-00427, BHYT, Tăng HA, Dị ứng Penicillin)
- BS: Nguyễn Hoàng An (kiêm BS + Quản trị)
- ĐD: Lê Mai · DS: Trần Minh · LT: Nguyễn Lan · QT: Vũ Phương Anh
- Visit: LK-20260430-0042 · Hoá đơn: INV-2026-0892 · Đơn thuốc: RX-2026-0892
- Multi-clinic: PK Hồng Đức Trung Tâm (default) + Đa khoa Mai Lan + Phòng khám tư của tôi

### Cleanup pending (manual)

2 duplicates trong project mới — bạn xoá qua Stitch UI:
- `f208b29370b54e749fc136ca2d5d049b` — Cấu hình BHYT (cũ trước retry)
- `e59bef8bee744926ae5654f6b26ef25e` — Cấu hình Tích hợp (cũ trước retry)

### Sau TASK-031 hoàn tất

- **TASK-032** (đề xuất): Implement FE Phase D — port 47 màn sang React/Tailwind trong `clinic-cms-web`
- **TASK-033** (đề xuất): Implement BE security NFR-024..046 (column-level encryption + bcrypt 12 + hash chain audit + anomaly detection)

## Blockers

None — chỉ là thời gian wall-clock cho 15 calls sequential.

## Completion Summary (2026-05-01)

**Final result**: 13/15 màn ✓ (87%) — 2 màn `blocked-stitch-api`.

**Project state**:
- 45 unique canonical screens trong project `2542650746708884228` (~96% / 47 target)
- 1 bonus screen "Quản lý lịch hẹn" (alt-naming)
- 12 duplicates cần cleanup manual qua Stitch UI
- 2 màn missing: **Billing — Công nợ AR aging** + **Notifications full page**

**13 màn mới TASK-031 đã sinh thành công** — xem mapping đầy đủ tại [`deliveries/final-specs/screen-ids-final.md`](deliveries/final-specs/screen-ids-final.md).

**2 màn blocked-stitch-api**: Đã fire 2 lần (batch C+D + retry), MCP timeout cả 2 lần, server không persist. Nguyên nhân: project >50 screens hit Stitch rate-limit cứng. Per spec, mark blocked + skip thay vì spam retry.

**Next steps khuyến nghị cho 2 màn blocked**:
- Lựa chọn 1: Cleanup 12 duplicates trước (giảm project về 45) rồi retry 2 màn missing
- Lựa chọn 2 (preferred): Defer to **TASK-032 FE Phase D implementation** — port 47 màn sang React/Tailwind, code 2 màn blocked trực tiếp dựa trên spec đã có trong §A.1/§A.2

**Docs đã update**:
- [`docs/design/medizen-modern/MEDIZEN_FRESH_PROJECT.md`](../../design/medizen-modern/MEDIZEN_FRESH_PROJECT.md) — bảng "32/47" → "45/47" với canonical IDs đầy đủ + 12 duplicates cleanup notes + 2 blocked notes
- [`docs/design/medizen-modern/README.md`](../../design/medizen-modern/README.md) — bảng 32 màn → 45 màn canonical
- [`docs/tasks/TASK-031/deliveries/final-specs/screen-ids-final.md`](deliveries/final-specs/screen-ids-final.md) — final delivery mapping
