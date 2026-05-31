# MediZen Pro (Teal) — Stitch project mapping

**Project**: `projects/11017295654666096971` — "MediZen Pro — Clinic CMS (Teal)"
**Design system asset**: `7fdf9855983c43ca8043740032641344` (Teal medical premium, từ DESIGN.md)
**Created**: 2026-05-29
**Stitch UI**: https://stitch.withgoogle.com/projects/11017295654666096971

> Project mới (Teal medical premium) làm source-of-truth thiết kế cho đợt nâng cấp FE.

## Trạng thái (2026-05-29 — DỪNG Stitch, tập trung FE)

| # | Màn | Screen ID | Status |
|---|---|---|---|
| — | DESIGN.md (design-system source) | `5781082264226487551` | ✅ |
| 1 | Tiếp nhận & Đăng ký bệnh nhân (canonical) | `e2983089ea0049cca136ac2fda88f57e` | ✅ landed |
| 1b | — bản trùng (xoá tay trong UI) | `139402d903a84493ae0cd9dc1caa90d2` | dup |
| 1c | — bản trùng (xoá tay trong UI) | `231912ccb0054e7c9d64016d4abc86f5` | dup |

**Kết luận generation**: MCP `generate_screen_from_text` CÓ persist nhưng cực chậm + rate-limit nặng — fire dồn dập bị **collapse/drop** (chỉ 3 lệnh đầu tiên lúc project trống sống được, 6 lệnh sau bị drop hết sau >10 phút). Đúng pattern trong memory `stitch_mcp_pitfalls`. → **Quyết định: dừng gen qua MCP**, tập trung implement FE. Nếu cần ảnh thiết kế: generate thủ công trong Stitch UI (design system "MediZen Pro" đã sẵn).

## ⚠️ blocked-stitch-api — generate timeout

`generate_screen_from_text` qua MCP **timeout liên tục** và server không persist screen
(đã thử 2 lần cho màn "Đăng ký BN", `list_screens` xác nhận chỉ còn instance DESIGN.md —
KHÔNG sinh duplicate). Đây là cùng triệu chứng đã gặp ở TASK-031 (MCP client timeout <
thời gian generate của Stitch). KHÔNG retry thêm (rủi ro duplicate).

**Cách xử lý:**
- **Đã làm**: theo plan, fallback = code trực tiếp ở FE (`clinic-cms-web`). Design system
  Teal + DESIGN.md là đủ spec để implement. Form đăng ký BN đã dựng lại bằng React/Tailwind.
- **Tùy chọn — generate thủ công trong Stitch UI**: mở project link ở trên → "+ New screen"
  → chọn design system "MediZen Pro" → paste prompt bên dưới → đợi.

## Prompts sẵn dùng (paste vào Stitch UI)

### 1. Tiếp nhận & Đăng ký bệnh nhân
```
Màn hình "Tiếp nhận & Đăng ký bệnh nhân" cho phần mềm quản lý phòng khám (desktop, tiếng Việt).
Bố cục FORM RỘNG ~1100px ở giữa, chia 2 thẻ card bo góc 16px viền slate-200 shadow nhẹ padding 28px.
Thẻ 1 "Thông tin bắt buộc" (icon teal trong ô vuông bo tròn nền teal nhạt): Họ tên (full width, dấu * đỏ);
hàng 2 cột Giới tính (segmented control 3 nút Nam/Nữ/Khác, nút active nền trắng chữ teal) và Số điện thoại;
hàng 2 cột Ngày sinh (date) và Năm sinh. Thẻ 2 "Thông tin bổ sung": hàng 2 cột Email và CCCD; Địa chỉ full
width; hàng 3 cột Tỉnh/Quận/Phường; hàng 2 cột Nhóm máu (select) và Nghề nghiệp; Dị ứng, Bệnh nền, Ghi chú
(textarea). Thanh hành động dính đáy nền trắng viền trên: nút Huỷ (trắng viền) và Lưu bệnh nhân (nền teal)
căn phải. Input cao 44px bo góc 10px, label 14px, chữ nhập 15px. Màu chính teal #0D9488, nền slate-50,
heading Sora, body Inter. Phong cách y tế cao cấp sạch thoáng.
```

(Các prompt màn 2–6 soạn tương tự khi cần — bám DESIGN.md.)
