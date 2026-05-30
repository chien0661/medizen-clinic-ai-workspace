---
id: TASK-068
type: feature
title: Theme Selection & Customization System
status: IN_REVIEW
priority: Medium
assigned: Unassigned
created: 2026-05-31
updated: 2026-05-31
last_tested: 2026-05-31
test_verdict: PASS
branch: "feature/TASK-068-theme-system"
jira_key: ""
tags: [ui, theme, customization, design-system]
affected-repos: [clinic-cms-web]
refs:
  detail_design: ""
  implementation_plan: ""
  figma: ""
  confluence: ""
  jira_ticket: ""
  other: []
---

# TASK-068: Theme Selection & Customization System

## Description

Thêm tính năng chọn và tùy chỉnh theme cho hệ thống Clinic CMS. Người dùng (admin/staff) có thể chọn từ nhiều preset theme hiện đại với màu sắc đẹp mắt, hoặc tùy chỉnh màu sắc theo ý muốn. Theme được lưu lại theo từng user và áp dụng trên toàn hệ thống.

## Requirements

### Theme Presets
- [ ] Cung cấp tối thiểu 6 built-in theme hiện đại:
  - **Medical Blue** (mặc định) — xanh navy chuyên nghiệp, hiện đại
  - **Emerald Health** — xanh lá tươi, cảm giác sức khỏe, tươi trẻ
  - **Soft Lavender** — tím nhạt thanh lịch, phù hợp phòng khám thẩm mỹ
  - **Warm Coral** — cam đào ấm áp, thân thiện
  - **Midnight Dark** — dark mode cao cấp, giảm mỏi mắt
  - **Slate Professional** — xám xanh trung tính, trang nghiêm
- [ ] Mỗi theme bao gồm: primary color, secondary color, accent color, background, surface, text colors

### UI/UX
- [ ] Thêm nút/icon chọn theme trên thanh header (góc phải)
- [ ] Hiển thị theme picker dạng popover/drawer với preview màu sắc trực quan
- [ ] Live preview — áp dụng theme ngay lập tức khi hover/click (không cần reload)
- [ ] Hiển thị tên theme + color swatches trong picker
- [ ] Support dark/light mode toggle riêng biệt (hoặc tích hợp vào theme)

### Customization
- [ ] Cho phép tùy chỉnh primary color tự do (color picker)
- [ ] Tùy chỉnh được lưu vào user profile/localStorage
- [ ] Reset về theme mặc định (Medical Blue)

### Persistence & Scope
- [ ] Lưu theme preference theo từng user (localStorage + user profile nếu có API)
- [ ] Áp dụng theme ngay khi load trang (không flash)
- [ ] Theme setting áp dụng toàn bộ giao diện: sidebar, header, tables, buttons, cards, badges, charts

### Technical
- [ ] Implement bằng CSS custom properties (CSS variables) để dễ override
- [ ] Tương thích với component library hiện tại (TailwindCSS / Ant Design / MUI)
- [ ] Không ảnh hưởng hiệu năng (lazy load theme definitions)

## Acceptance Criteria

- [ ] Người dùng có thể chọn theme từ ít nhất 6 preset — toàn bộ UI cập nhật ngay
- [ ] Theme preference được ghi nhớ sau khi reload trang
- [ ] Tất cả các trang/màn hình đều phản ánh đúng theme đã chọn
- [ ] Live preview hoạt động mượt, không lag/flicker
- [ ] Color picker tùy chỉnh lưu và áp dụng được
- [ ] Dark mode hoạt động đúng với tất cả theme
- [ ] Responsive — theme picker hiển thị đúng trên mobile/tablet
- [ ] Accessibility: contrast ratio đạt WCAG AA tối thiểu cho tất cả theme

## Progress Checklist

- [ ] Implementation
- [ ] Code Review
- [ ] Testing
- [ ] Documentation

## Related Files

- **Input Specs**: `docs/tasks/TASK-068/refs/` *(DetailDesign, SRS, implementation-plan)*
- **Code**: (feature branch)
- **Tests**: `docs/tasks/TASK-068/deliveries/test-cases/`
- **Handoffs**: `docs/tasks/TASK-068/handoff/`
- **Test Report**: `docs/tasks/TASK-068/deliveries/test-reports/test-report.md`
- **API Specs**: `docs/tasks/TASK-068/deliveries/api-specs/`
- **Final Specs**: `docs/tasks/TASK-068/deliveries/final-specs/`

## Timestamps

- **Created**: 2026-05-31

## Notes

- Ưu tiên UX: theme picker phải trực quan, đẹp, không rối
- Tham khảo design inspiration: Linear, Vercel Dashboard, Notion — các hệ thống có theme switching mượt
- Cần confirm stack FE (TailwindCSS / Ant Design / MUI) để chọn implementation approach phù hợp
- Nếu hệ thống dùng TailwindCSS: dùng `data-theme` attribute + CSS variables
- Nếu dùng Ant Design: dùng `ConfigProvider` + algorithm (darkAlgorithm, compactAlgorithm)

## Blockers

None
