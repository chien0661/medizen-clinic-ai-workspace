# Thiết Kế Chi Tiết Tính Năng: Hệ Thống Lựa Chọn & Tùy Chỉnh Giao Diện Màu (Theme)

**Dự án:** Clinic CMS  
**Task:** TASK-068  
**Phiên bản:** 1.0  
**Ngày:** 2026-05-31  
**Người thực hiện:** Documentation Agent  
**Trạng thái:** Đã duyệt  
**Tài liệu liên quan:** Test Report (2026-05-31), Test-to-Documentation Handoff

---

## Lịch sử thay đổi

| Phiên bản | Ngày | Nội dung thay đổi |
|-----------|------|-------------------|
| 1.0 | 2026-05-31 | Phiên bản đầu tiên — tính năng hoàn tất round-2 testing, sẵn sàng triển khai |

---

## Mục lục

- [1. Tổng quan tính năng](#1-tổng-quan-tính-năng)
- [2. Luồng xử lý tổng thể](#2-luồng-xử-lý-tổng-thể)
- [3. Kiến trúc CSS biến tùy chỉnh](#3-kiến-trúc-css-biến-tùy-chỉnh)
- [4. Các preset theme](#4-các-preset-theme)
- [5. Quy tắc nghiệp vụ](#5-quy-tắc-nghiệp-vụ)
- [6. Xử lý lỗi](#6-xử-lý-lỗi)
- [7. SQL và cơ sở dữ liệu](#7-sql-và-cơ-sở-dữ-liệu)
- [8. Ghi chú và lưu ý khi kiểm thử](#8-ghi-chú-và-lưu-ý-khi-kiểm-thử)

---

## 1. Tổng quan tính năng

### 1.1 Mục đích

Hệ thống lựa chọn và tùy chỉnh giao diện màu (theme system) giúp người dùng (admin/nhân viên) cá nhân hóa giao diện của hệ thống Clinic CMS. Người dùng có thể chọn từ 6 preset theme được thiết kế sẵn, hoặc tùy chỉnh tự do màu sắc chính theo ý muốn. Sở thích về theme được lưu lại trên máy người dùng (localStorage) và tự động áp dụng khi họ đăng nhập lại, tạo trải nghiệm nhất quán và cá nhân hóa.

### 1.2 Phạm vi

**Bao gồm:**
- 6 preset theme được thiết kế sẵn: Medical Blue (mặc định), Emerald Health, Soft Lavender, Warm Coral, Midnight Dark, Slate Professional
- Thành phần ThemePicker để lựa chọn theme — hiển thị dạng popover trong header
- Kho Zustand (themeStore) để quản lý trạng thái theme hiện tại
- Hook useTheme để các component dễ dàng truy cập và sử dụng theme
- Hỗ trợ tùy chỉnh màu sắc chính (primary color) — người dùng có thể chọn màu tùy thích thông qua color picker
- Chức năng đặt lại mặc định — quay trở lại Medical Blue
- Lưu trữ preference trong localStorage với khóa `theme-preference` và `theme-custom-primary`
- Ngăn chặn FOUC (Flash of Unstyled Content) bằng inline script trong index.html

**Không bao gồm:**
- Lưu theme preference trong backend / user profile database
- Dark mode semantic (true dark mode colors) — Midnight Dark là color preset, không phải dark mode
- Keyboard navigation cho hover preview
- Theme presets ngoài 6 preset được định nghĩa

### 1.3 Các bên liên quan

| Vai trò | Mô tả |
|---------|-------|
| **Người dùng cuối (Admin/Nhân viên)** | Sử dụng ThemePicker để chọn theme, tùy chỉnh màu sắc, làm mới giao diện |
| **Hệ thống FE (clinic-cms-web)** | Cung cấp CSS custom properties, thành phần UI, kho trạng thái |
| **Browser localStorage** | Lưu trữ sở thích theme của người dùng |

---

## 2. Luồng xử lý tổng thể

### 2.1 Sơ đồ luồng dữ liệu

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. FOUC Prevention Inline Script (index.html)                   │
│    - Đọc localStorage["theme-preference"]                        │
│    - Đặt data-theme attribute trên <html>                       │
│    - CSS vars áp dụng TRƯỚC React hydrate                        │
└─────────────────────┬───────────────────────────────────────────┘
                      ▼
        ┌─────────────────────────────────┐
        │ React App Hydrates (ThemePicker │
        │ + themeStore initialized)       │
        └─────────┬───────────────────────┘
                  ▼
    ┌──────────────────────────────────────┐
    │ 2. User Clicks ThemePicker Button    │
    │    (Header kanan)                     │
    └─────────┬──────────────────────────┬─┘
              ▼                          ▼
      ┌──────────────────┐    ┌─────────────────────┐
      │ Popover mở       │    │ Hiển thị 6 preset + │
      │                  │    │ custom color input  │
      └──────────────────┘    └──────┬──────────────┘
                                     ▼
              ┌──────────────────────────────────────┐
              │ 3. User hovers over theme hoặc       │
              │    nhập custom color                 │
              └──────────┬─────────────────────┬─────┘
                         ▼                     ▼
        ┌───────────────────────┐  ┌─────────────────────┐
        │ setTheme() dipanggil  │  │ Custom color preview│
        │ - data-theme="..."    │  │ - Inline style áp   │
        │ - CSS vars update     │  │   dụng tạm          │
        │ - UI recolor instantly│  │                     │
        └───────────────────────┘  └─────────────────────┘
                         ▼                     ▼
              ┌──────────────────────────────────┐
              │ 4. User click theme hoặc submit  │
              │    custom color                  │
              └──────────┬───────────────────────┘
                         ▼
          ┌─────────────────────────────────┐
          │ Data persisted to localStorage:  │
          │ - localStorage["theme-preference"]│
          │ - localStorage["theme-custom-color"]
          └──────────┬──────────────────────┘
                     ▼
        ┌─────────────────────────────────┐
        │ ThemePicker closes              │
        │ Theme applied to entire UI      │
        └─────────────────────────────────┘
                     ▼
    ┌────────────────────────────────────────┐
    │ 5. User navigates / reloads (lần sau)  │
    │    - FOUC script áp dụng saved theme   │
    │    - No flicker, consistent experience │
    └────────────────────────────────────────┘
```

### 2.2 Mô tả các bước chính

| Bước | Tên bước | Mô tả chi tiết |
|------|---------|----------------|
| 1 | **FOUC Prevention** | Inline script trong `index.html` chạy ngay khi HTML parse xong (trước khi React load). Nó đọc `localStorage["theme-preference"]` và đặt `data-theme` attribute trên `<html>`. CSS vars trong `themes.css` kích hoạt theo attribute này. Kết quả: theme được áp dụng trước khi React hydrate, tránh flash của color không đúng. |
| 2 | **Người dùng mở ThemePicker** | Người dùng click nút "Chọn giao diện màu" ở góc phải header. ThemePicker component (popover) hiển thị danh sách 6 preset theme, custom color input, và nút reset. |
| 3 | **Live preview khi hover** | Khi người dùng hover chuột lên một theme preset hoặc nhập một custom color, hàm setTheme() được gọi để đặt `data-theme` attribute và CSS vars tạm thời. Giao diện cập nhật ngay lập tức để hiển thị preview. Không có flicker hay lag. |
| 4 | **Người dùng xác nhận lựa chọn** | Người dùng click vào theme muốn chọn, hoặc nhập xong custom color rồi click nút "Áp dụng" / submit. Lúc này themeStore gọi `setTheme()` và ghi vào localStorage cả `theme-preference` lẫn `theme-custom-primary` (nếu có). |
| 5 | **Đóng ThemePicker** | ThemePicker popover đóng lại. Theme đã được áp dụng và lưu trữ. Người dùng tiếp tục làm việc với giao diện mới. |
| 6 | **Persistence qua các lần truy cập** | Lần tiếp theo người dùng reload trang hoặc quay lại ứng dụng, FOUC script đọc localStorage, đặt data-theme đúng, CSS vars kích hoạt, theme hiển thị ngay không có flicker. Trải nghiệm nhất quán. |

---

## 3. Kiến trúc CSS biến tùy chỉnh

### 3.1 Tổ chức tệp

**Tệp chính:** `src/styles/themes.css`

Tệp này định nghĩa CSS custom properties cho mỗi theme dưới dạng `[data-theme="..."]` selector:

```css
[data-theme="medical-blue"] {
  --theme-primary: 26 55 99;           /* Navy blue */
  --theme-secondary: 59 130 246;       /* Blue-500 */
  --theme-accent: 6 182 212;           /* Cyan */
  --theme-sidebar: 249 250 251;        /* Gray-50 light bg */
  --theme-text: 15 23 42;              /* Slate-900 */
  --theme-success: 34 197 94;          /* Green-500 */
  /* ... other colors ... */
}

[data-theme="emerald-health"] {
  --theme-primary: 5 150 105;          /* Emerald-600 */
  --theme-secondary: 16 185 129;       /* Emerald-500 */
  --theme-accent: 34 197 94;           /* Green-500 */
  /* ... */
}

/* ... các theme khác ... */
```

### 3.2 CSS Variables được định nghĩa

Mỗi theme định nghĩa bộ CSS variables sau đây (tổng cộng ~15-20 variables):

| Tên Variable | Ý nghĩa | Kiểu giá trị |
|--------------|---------|------------|
| `--theme-primary` | Màu chính, dùng cho buttons, links, accents | RGB (3 giá trị được cách nhau bởi space) |
| `--theme-secondary` | Màu phụ, dùng cho hover states, secondary buttons | RGB |
| `--theme-accent` | Màu nhấn, dùng cho badges, highlights | RGB |
| `--theme-sidebar` | Màu nền sidebar | RGB hoặc hex |
| `--theme-text` | Màu text chính | RGB |
| `--theme-text-secondary` | Màu text phụ | RGB |
| `--theme-border` | Màu border | RGB |
| `--theme-success` | Màu cho success states | RGB |
| `--theme-warning` | Màu cho warning states | RGB |
| `--theme-error` | Màu cho error states | RGB |
| ... | ... | ... |

### 3.3 Cách dùng CSS vars trong Tailwind

Trong `tailwind.config.js`, các CSS variables được expose thành Tailwind classes:

```javascript
theme: {
  extend: {
    colors: {
      'theme-primary': 'rgb(var(--theme-primary) / <alpha-value>)',
      'theme-sidebar': 'rgb(var(--theme-sidebar) / <alpha-value>)',
      // ... etc ...
    }
  }
}
```

Ví dụ dùng trong JSX:

```jsx
<button className="bg-theme-primary text-white">
  Submit
</button>

<div className="bg-theme-sidebar p-4">
  Sidebar
</div>
```

### 3.4 Placement của CSS file

Trong `src/styles.css`, import CSS theme PHẢI ở dòng đầu tiên, **trước** `@tailwind` directives:

```css
/* src/styles.css */
@import "./styles/themes.css";  /* ← Bắt buộc ở dòng 1 */

@tailwind base;
@tailwind components;
@tailwind utilities;
```

**Lý do:** Đảm bảo CSS vars từ themes.css được định nghĩa trước khi Tailwind tạo các classes. Nếu import ở sau, CSS vars sẽ không resolve đúng.

---

## 4. Các preset theme

### 4.1 Danh sách theme

| Theme ID | Tên | Màu chính (RGB) | Mô tả |
|----------|------|------|--------|
| `medical-blue` | Medical Blue (Mặc định) | `26 55 99` (Navy) | Chuyên nghiệp, hiện đại, phù hợp ngành y tế. Lựa chọn mặc định. |
| `emerald-health` | Emerald Health | `5 150 105` (Emerald-600) | Xanh lá tươi mát, cảm giác sức khỏe, tươi trẻ, tích cực. |
| `soft-lavender` | Soft Lavender | `147 51 234` (Violet) | Tím nhạt thanh lịch, phù hợp cho phòng khám thẩm mỹ, spa. Hình ảnh cao cấp. |
| `warm-coral` | Warm Coral | `234 88 12` (Orange-600) | Cam đào ấm áp, thân thiện, dễ tiếp cận. Tạo cảm giác chào đón. |
| `midnight-dark` | Midnight Dark | `99 102 241` (Indigo) | Indigo, tone tối, giảm mỏi mắt khi làm việc khuya. Sang trọng. |
| `slate-professional` | Slate Professional | `51 65 85` (Slate-700) | Xám xanh trung tính, trang nghiêm, chuyên nghiệp. Không quá nổi bật. |

### 4.2 Ví dụ trực quan

Mỗi theme bao gồm:
- **Primary color**: Dùng cho buttons, links, active states
- **Secondary color**: Dùng cho hover, secondary actions
- **Accent color**: Badges, highlights
- **Background colors**: Sidebar, surfaces
- **Text colors**: Body text, labels
- **Semantic colors**: Success (xanh), Warning (vàng), Error (đỏ)

Ví dụ **Medical Blue** theme:

```
Primary:   Navy #1A3763 (26, 55, 99)
Secondary: Blue #3B82F6 (59, 130, 246)
Accent:    Cyan #06B6D4 (6, 182, 212)
Sidebar:   Light gray #F9FAFB (249, 250, 251)
Text:      Slate-900 #0F172A (15, 23, 42)
Success:   Green #22C55E (34, 197, 94)
```

---

## 5. Quy tắc nghiệp vụ

| Mã | Mô tả quy tắc | Hành vi khi vi phạm / Xử lý |
|----|--------------|---------------------|
| **BR-001** | Theme mặc định là `medical-blue`. Khi ứng dụng khởi động lần đầu (không có preference lưu), theme Medical Blue được áp dụng tự động. | Nếu localStorage không có `theme-preference`, hệ thống dùng `medical-blue`. |
| **BR-002** | Theme preference được lưu trong `localStorage["theme-preference"]` với giá trị là theme ID (ví dụ: `"emerald-health"`). Preference được lưu ngay khi người dùng click chọn theme hoặc submit custom color. | Nếu localStorage quota đầy, throw error được silent-catch — người dùng không mất theme hiện tại, nhưng preference sẽ không được lưu cho lần sau. Dùng fallback in-memory. |
| **BR-003** | Custom primary color được lưu trong `localStorage["theme-custom-primary"]` dạng hex string (ví dụ: `"#FF5733"`). Khi người dùng nhập màu, hex được validate trước khi áp dụng. Format phải là `#RRGGBB` (6 chữ số hex). | Nếu format không hợp lệ, custom color input không áp dụng, giữ nguyên theme hiện tại. Error message hiển thị: "Định dạng màu không hợp lệ. Vui lòng nhập hex color (#RRGGBB)." |
| **BR-004** | Live preview khi hover: Khi người dùng hover chuột lên một theme hoặc nhập custom color, theme được preview ngay (data-theme set, CSS vars update), nhưng KHÔNG được lưu vào localStorage. Khi người dùng di chuột ra (mouse leave) hoặc nhấn Escape, preview được hủy và quay lại theme đang hoạt động (committed theme). | Nếu người dùng hover rồi đóng popover mà không click, theme quay lại thế trạng cũ. Đây là designed behavior, không phải bug. |
| **BR-005** | Chức năng "Đặt lại mặc định" — click nút reset sẽ: (1) xóa `localStorage["theme-custom-primary"]`, (2) xóa `localStorage["theme-preference"]`, (3) áp dụng `medical-blue` theme. Nút reset là option riêng trong ThemePicker. | Sau khi click reset, nếu localStorage xóa không thành công (quota error), theme vẫn quay lại Medical Blue trong memory, nhưng next load sẽ dùng preference cũ nếu data không xóa được. Thực tế hiếm xảy ra. |
| **BR-006** | FOUC (Flash of Unstyled Content) Prevention — inline script trong `index.html` phải chạy TRƯỚC khi React hydrate và CSS được load. Script này: (1) đọc `localStorage["theme-preference"]`, (2) đặt `data-theme` attribute trên `<html>`, (3) CSS vars từ `themes.css` kích hoạt. Điều này đảm bảo không có flicker/flash khi page load. | Nếu inline script không chạy, hoặc localStorage undefined, default `data-theme="medical-blue"` được dùng. Không có fallback khác. |

---

## 6. Xử lý lỗi

### 6.1 Các tình huống lỗi phổ biến

| Tình huống | Lỗi | Xử lý | Trải nghiệm người dùng |
|-----------|------|------|----------------------|
| localStorage quota exceeded | QuotaExceededError | Try-catch silently ignore write, dùng in-memory state | Người dùng thấy theme apply ngay, nhưng next reload không nhớ (fallback mặc định). No error message shown. |
| Custom color hex format invalid | Invalid hex format | Reject input, không áp dụng CSS vars, giữ theme hiện tại | ThemePicker input shows validation error: "Định dạng không hợp lệ". Người dùng chỉnh sửa lại. |
| localStorage not accessible (private browsing) | Offline / restricted localStorage | Fallback to in-memory state, skip persistence | Theme hoạt động bình thường trong session, nhưng không persist qua reload. Không có error popup. |
| Inline FOUC script fails to run | Script error / timing | Theme áp dụng sau khi React load, có thể có flicker ngắn | Người dùng thấy default theme (Medical Blue) flash sau đó chuyển sang theme đúng. Lỗi hiếm. |
| Theme CSS file fails to load | Network / build error | Fallback CSS vars undefined, UI dùng default browser colors | Giao diện bị hỏng, không có theme colors. Dùng browser defaults (gray). Người dùng thấy warning console. |

### 6.2 Định dạng lỗi

Hầu hết các lỗi được silent-catch (không show popup) để tránh làm gián đoạn trải nghiệm. Ngoại lệ:

- **Custom color validation error** — hiển thị inline error trong ThemePicker: "Định dạng màu không hợp lệ"
- **Console errors** — ghi log để developer debug

---

## 7. SQL và cơ sở dữ liệu

**Không áp dụng.**

TASK-068 là tính năng thuần FE, không có backend API hay database changes. Toàn bộ logic lưu trữ theme preference nằm ở `localStorage` phía client:

- `localStorage["theme-preference"]` — lưu theme ID (ví dụ: `"emerald-health"`)
- `localStorage["theme-custom-primary"]` — lưu custom color hex (ví dụ: `"#FF5733"`)

Không có migration, không có bảng database, không có stored procedure. Nếu trong tương lai cần đồng bộ theme preference với backend (để người dùng có theme nhất quán trên nhiều device), phần này sẽ được thêm vào bằng TASK mới.

---

## 8. Ghi chú và lưu ý khi kiểm thử

### 8.1 Điểm quan trọng cần nắm

- **localStorage persistence**: Theme được lưu trong trình duyệt của từng người dùng trên từng máy. Không đồng bộ qua device khác. Đây là by-design, không phải bug.
- **FOUC prevention**: Inline script trong index.html PHẢI chạy trước React load. Nếu JavaScript disabled, FOUC sẽ xảy ra. Nhưng trong thực tế, Clinic CMS cần JavaScript để chạy, nên đây không phải issue thực tế.
- **Color format**: Custom color input chỉ chấp nhận hex format `#RRGGBB`. RGB, HSL, named colors không được support (để đơn giản). Validation xảy ra client-side.
- **Midnight Dark theme**: Không phải dark mode thực sự (semantic dark mode). Nó là color preset với tone tối dùng indigo. Các semantic colors (success, warning, error) vẫn sáng. Improvement đúng cho dark mode hoàn chỉnh được deferred.
- **Theme applied twice on init**: Do FOUC script + Zustand module load, theme có thể được set 2 lần. Điều này vô hại (idempotent), nhưng nếu nhận thấy console log ghi "theme applied" 2 lần, đây là normal behavior.

### 8.2 Gợi ý dữ liệu kiểm thử

| Kịch bản | Giá trị đầu vào | Kết quả kỳ vọng |
|---------|----------------|----------------|
| Lần đầu load ứng dụng | Không có localStorage | Theme `medical-blue` hiển thị, không flicker |
| Chọn theme Emerald Health | Click theme trong picker | UI recolor ngay, `data-theme="emerald-health"` set, localStorage lưu |
| Hover theme rồi mouse leave | Hover Warm Coral rồi di chuột ra | Preview Warm Coral hiển thị ngắn, revert về Emerald Health khi leave |
| Nhập custom color | Nhập `#FF5733` vào color input | Input được accept, CSS vars update ngay, preview color |
| Reset về mặc định | Click nút "Đặt lại mặc định" | Theme quay lại Medical Blue, localStorage cleared, custom color reset |
| Reload page sau khi lưu | Reload sau khi chọn Soft Lavender | Soft Lavender hiển thị ngay (từ FOUC script), không flash Medical Blue |
| Custom color invalid | Nhập `GGGGGG` hoặc `#FF57` | Input rejected, error message hiển thị, theme không thay đổi |
| Mở DevTools console | Xem network / storage tab | `theme-preference` và `theme-custom-primary` visible trong localStorage |

### 8.3 Hạn chế hiện tại

- **N1**: Midnight Dark là color preset, không phải dark mode semantic. Các color như background, text semantic colors không tự flip. Improvement cho dark mode hoàn chỉnh deferred (đợi TASK tiếp theo).
- **N2**: Theme preference lưu client-side (localStorage) chỉ, không sync qua device. Nếu người dùng dùng 2 device khác nhau, mỗi device có theme riêng. Feature "sync theme qua cloud" là future enhancement.
- **N3**: Theme được applied 2 lần trên init (FOUC script + Zustand module load) — harmless, design accepted (tradeoff giữa FOUC prevention vs code complexity).
- **N4**: Hover preview không có keyboard support. Người dùng keyboard-only không thể preview theme khi hover. Accessibility improvement deferred.
- **N5**: Custom color picker dùng HTML5 native `<input type="color">` — limited color space (RGB 8-bit). Advanced color model (LAB, HSL) không được support.

### 8.4 Hướng phát triển

- **Feature 1**: True dark mode — thêm semantic colors flip, support real dark mode standard (WCAG)
- **Feature 2**: Theme sync qua backend — lưu theme preference trong user profile, sync qua device
- **Feature 3**: Community themes — cho phép người dùng tạo và chia sẻ custom theme presets
- **Feature 4**: Schedule theme — tự động switch theme theo giờ (ví dụ: dark mode vào buổi tối)
- **Feature 5**: Keyboard navigation cho picker — accessibility improvement

---

## Phê duyệt

| Vai trò | Họ tên | Ngày |
|---------|--------|------|
| Test Agent | Test Agent | 2026-05-31 ✓ |
| Documentation Agent | Documentation Agent | 2026-05-31 |
| Người quản lý dự án | | |

---

**Ghi chú nội bộ**: Tính năng hoàn tất round-2 testing (914/914 unit tests + 7/7 E2E tests PASS). Branch: `feature/TASK-068-theme-system` (commit `e0f0d34`). Sẵn sàng merge vào main sau khi qua code review.
