---
id: TASK-050
type: feature
title: Seed data cho các danh mục (services, ICD, drugs, units, etc.)
status: BLOCKED
priority: High
assigned: Unassigned
created: 2026-05-04
updated: 2026-05-04
branch: "feature/TASK-050-seed-categories"
jira_key: ""
tags: [be, seed-data, categories]
affected-repos: [clinic-cms-merge]
refs:
  detail_design: ""
  implementation_plan: ""
  figma: ""
  confluence: ""
  jira_ticket: ""
  other: []
---

# TASK-050: Seed data cho các danh mục (services, ICD, drugs, units, etc.)

## Description

User báo: "**Các danh mục chưa có dữ liệu**". Cần seed data realistic cho các bảng danh mục để test luồng KCB end-to-end khả thi.

Phạm vi danh mục cần seed (xác định trong investigation):
- **Services / dịch vụ khám**: dịch vụ khám tổng quát, chuyên khoa, cận lâm sàng (siêu âm, X-quang, xét nghiệm máu, nước tiểu, điện tim, etc.)
- **Drugs / thuốc**: top ~50-100 thuốc thông dụng VN (Paracetamol, Amoxicillin, Cephalexin, etc.) + đơn vị + giá
- **ICD codes**: top diseases thông dụng (ICD-10 vi)
- **Units (đơn vị tính)**: viên, gói, ống, chai, lọ, ml, mg, etc.
- **Drug categories**: kháng sinh, giảm đau, hạ sốt, etc.
- **Lab tests**: CBC, sinh hóa máu, nước tiểu 10 thông số, etc.
- **Diagnosis templates**: nếu có
- **Tenant config**: clinic info default, working hours, etc. (chỉ verify, không touch nếu DEMO đã có)

## Approach

1. **Investigation**: scan `clinic-cms-merge/app/modules/*/models/` tìm các bảng danh mục đang empty trong DB
2. **Verify hiện trạng**: query DB qua psql hoặc API endpoint count → confirm bảng nào empty
3. **Create seed script**: tạo `clinic-cms-merge/scripts/seed_categories.py` (hoặc extend `seed_demo_data.py`) — idempotent, có thể re-run an toàn
4. **Run seed**: vào BE container/env, chạy seed script
5. **Verify**: query lại + screenshot count

## Technical decisions

- **NOT** touch FE — chỉ BE
- **NOT** modify model schemas — chỉ insert data
- **NOT** create Alembic migration cho seed — dùng script Python riêng (data seed không phải schema migration)
- **Idempotent**: dùng `INSERT ... ON CONFLICT DO NOTHING` hoặc check exist trước insert
- **Tenant scope**: tất cả data seed gắn vào DEMO clinic (`a0000000-0000-0000-0000-000000000001`)
- **Source data**: hard-code trong script (hoặc CSV trong `scripts/seed-data/`), Vietnamese labels, realistic giá VND

## Requirements

- [ ] Investigate: list bảng danh mục + count hiện tại
- [ ] Decide priority: bảng nào BLOCKING cho luồng KCB? (drugs + services + units = critical)
- [ ] Implement seed script
- [ ] Run + verify count tăng
- [ ] Test API: GET các endpoint danh mục → trả về data
- [ ] Document `seed-categories-spec.md` ghi rõ: bảng nào, bao nhiêu rows, source

## Acceptance Criteria

- [ ] Tất cả bảng danh mục critical có ≥10 rows realistic VN
- [ ] Drug list: ≥50 items (top common drugs) với đơn vị + giá
- [ ] Service list: ≥15 items dịch vụ thông dụng
- [ ] ICD codes: ≥30 items top diseases
- [ ] Seed script idempotent (re-run không tạo duplicate)
- [ ] FE call các endpoint danh mục → thấy data (verify gián tiếp qua TASK-049)

## Notes

**Liên quan**: Block một phần TASK-049 (luồng KCB) — không có drug list thì không kê đơn được. Cần seed drugs + services SỚM NHẤT.

**Source data Vietnam**:
- Danh mục dịch vụ: Bộ Y tế ban hành thông tư 39/2018/TT-BYT (giá dịch vụ KCB BHYT)
- Danh mục thuốc: TT 30/2018/TT-BYT (DM thuốc tân dược BHYT)
- ICD-10: phiên bản tiếng Việt
- Có thể search GitHub có sẵn dataset

## Blockers

**2026-05-04 INCIDENT**: Code Implementation Agent đầu tiên vi phạm scope nghiêm trọng:
- Đáng lẽ chỉ tạo `scripts/seed_categories.py`
- Thực tế đã modify 5 BE source files: `app/core/tenancy.py`, `app/modules/users/api/routes.py`, `app/modules/users/schemas/user_schemas.py`, `app/modules/search/services/search_service.py`, `docker/docker-compose.yml`
- BE running container 500 sau khi agent edit code (hot-reload picked up broken state)
- Stopped agent + reverted source files (giữ lại `scripts/seed_categories.py` agent đã tạo)
- BE container vẫn cần user restart manually

**Next time spawn agent**: Cần constraint chặt hơn (whitelist files được phép edit), hoặc dùng worktree isolation.

**Action items**:
- [ ] User restart BE container
- [ ] Review `scripts/seed_categories.py` xem agent tạo có đúng không
- [ ] Re-spawn task hoặc tự run script (sau khi review)
