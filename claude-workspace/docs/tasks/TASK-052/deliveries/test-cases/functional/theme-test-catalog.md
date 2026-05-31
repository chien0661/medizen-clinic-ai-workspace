# Test Case Catalog — THEME · Giao diện & Cá nhân hóa

**Nguồn:** function_list_data.py (group THEME) + clinic_management_function_list.md + system_design/SaaS.
**Phạm vi:** 3 functions.  **Tổng test case:** 16.  **Ngày:** 2026-05-30.

> **Bản chất nhóm THEME:** Đây là nhóm **giao diện client-side (frontend)**, không phải tính năng backend. Theo `function_list_data.py` (dòng 1744–1754) nhóm gồm đúng **3 function**, đều role = **System**, version **v1**, thuộc **TASK-017**, trạng thái nguồn = **DONE (✅)**:
> - **THEME-001 — Light mode (Default):** Tailwind default classes; background trắng, text đen.
> - **THEME-002 — Dark mode (Class-based toggle):** Tailwind `class="dark"` trên thẻ `<html>`; mọi component có biến thể `dark:`; toggle nằm trong topbar **+ lưu user preference**.
> - **THEME-003 — System theme detection (Auto theo OS):** Detect `prefers-color-scheme` media query lần đầu; user override sau đó; cập nhật khi OS đổi (nếu user **chưa** override).
>
> **Đối chiếu mã thực tế (đã thử):** Đây là tính năng frontend (Tailwind + Tauri offline UI). Quá trình đối chiếu cố gắng truy cập repo frontend `E:/MyProject/clinic-cms-web` và backend `E:/MyProject/clinic-cms-merge/app` qua công cụ nhưng **không truy cập/liệt kê được nội dung repo sibling** trong môi trường hiện tại. Vì không quét được file test cụ thể, Coverage được **suy ra từ cột status nguồn = DONE** và mọi tham chiếu test file đều ghi rõ **"cần xác minh test file"**. Đây là nhóm UI client-side nên không có endpoint API/RLS/DB; các test thiên về **Unit (logic toggle/detect) + Manual/UI + E2E (Playwright)** trên frontend. Không áp dụng test 401/403 (không có endpoint phân quyền) và không áp dụng cô lập clinic theo RLS (không đụng dữ liệu domain trong DB; preference lưu phía client / theo user). Các điểm này được nêu rõ trong từng test case tương ứng.

---

## 1. Ma trận truy vết (Function → Test Cases → Coverage)

| Function | Tên chức năng | Status (nguồn) | Test Case IDs | Coverage |
|---|---|---|---|---|
| THEME-001 | Light mode (Default) | DONE | TC-THEME-001, TC-THEME-002, TC-THEME-003 | PARTIAL (suy từ status DONE; cần xác minh test file) |
| THEME-002 | Dark mode (Class-based toggle) | DONE | TC-THEME-004, TC-THEME-005, TC-THEME-006, TC-THEME-007, TC-THEME-008, TC-THEME-009, TC-THEME-010 | PARTIAL (suy từ status DONE; cần xác minh test file) |
| THEME-003 | System theme detection (Auto theo OS) | DONE | TC-THEME-011, TC-THEME-012, TC-THEME-013, TC-THEME-014, TC-THEME-015, TC-THEME-016 | PARTIAL (suy từ status DONE; cần xác minh test file) |

*(MỘT dòng cho MỖI function — không bỏ sót. 3/3 function được phủ.)*

---

## 2. Chi tiết Test Cases

### TC-THEME-001 — Light mode là mặc định khi chưa có preference
- **Function:** THEME-001
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Unit (logic khởi tạo theme) + Manual/UI
- **Tiền điều kiện:** Người dùng mới, chưa có theme preference lưu (localStorage/user setting trống); OS đặt light hoặc không xác định.
- **Bước thực hiện:** 1) Mở app lần đầu. 2) Quan sát thẻ `<html>` và nền trang.
- **Dữ liệu test:** localStorage `theme` = null; `prefers-color-scheme: light`.
- **Kết quả mong đợi:** Thẻ `<html>` KHÔNG có class `dark`; background trắng, text đen (Tailwind default); render đúng light mode.
- **Coverage hiện tại:** PARTIAL — suy từ status nguồn DONE (TASK-017). Cần xác minh test file (đề xuất `clinic-cms-web` unit test `theme.spec.ts::default_is_light`).

### TC-THEME-002 — Mọi component hiển thị đúng ở light mode (không vỡ contrast)
- **Function:** THEME-001
- **Loại:** Edge / Visual
- **Ưu tiên:** P2
- **Layer:** Manual/UI (visual regression)
- **Tiền điều kiện:** App ở light mode.
- **Bước thực hiện:** 1) Duyệt các màn chính (dashboard, danh sách BN, form khám). 2) Kiểm tra màu chữ/nền, viền, trạng thái hover/disabled.
- **Dữ liệu test:** Các component dùng biến thể mặc định (không `dark:`).
- **Kết quả mong đợi:** Không có chữ trắng trên nền trắng; contrast đạt WCAG AA; không phần tử nào kế thừa nhầm style dark.
- **Coverage hiện tại:** PARTIAL — suy từ status DONE. Cần xác minh test file (đề xuất Playwright visual snapshot light).

### TC-THEME-003 — Light mode bền vững sau khi tải lại trang
- **Function:** THEME-001
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** E2E (Playwright)
- **Tiền điều kiện:** User đang ở light mode (đã set hoặc mặc định).
- **Bước thực hiện:** 1) Reload trang / khởi động lại app Tauri. 2) Quan sát theme khởi tạo.
- **Dữ liệu test:** localStorage `theme="light"`.
- **Kết quả mong đợi:** Sau reload vẫn light mode, không nhấp nháy (flash) sang dark rồi đổi lại.
- **Coverage hiện tại:** PARTIAL — suy từ status DONE. Cần xác minh test file (đề xuất e2e `theme_persist_light`).

### TC-THEME-004 — Bật dark mode từ topbar toggle
- **Function:** THEME-002
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** E2E (Playwright) + Unit
- **Tiền điều kiện:** App đang ở light mode; toggle theme hiển thị trên topbar.
- **Bước thực hiện:** 1) Click toggle theme. 2) Quan sát thẻ `<html>` và UI.
- **Dữ liệu test:** Trạng thái ban đầu light.
- **Kết quả mong đợi:** Thẻ `<html>` được thêm class `dark`; toàn bộ component chuyển sang biến thể `dark:` (nền tối, text sáng) đồng bộ.
- **Coverage hiện tại:** PARTIAL — suy từ status DONE (TASK-017). Cần xác minh test file (đề xuất `theme.spec.ts::toggle_to_dark`).

### TC-THEME-005 — Tắt dark mode (toggle về light)
- **Function:** THEME-002
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** E2E (Playwright)
- **Tiền điều kiện:** App đang ở dark mode.
- **Bước thực hiện:** 1) Click toggle theme lần nữa. 2) Quan sát.
- **Dữ liệu test:** Trạng thái ban đầu dark.
- **Kết quả mong đợi:** Class `dark` bị gỡ khỏi `<html>`; UI trở lại light mode đầy đủ.
- **Coverage hiện tại:** PARTIAL — suy từ status DONE. Cần xác minh test file (đề xuất `theme.spec.ts::toggle_back_to_light`).

### TC-THEME-006 — Lựa chọn dark được lưu vào user preference và bền vững qua phiên
- **Function:** THEME-002
- **Loại:** Edge (persistence)
- **Ưu tiên:** P0
- **Layer:** E2E (Playwright)
- **Tiền điều kiện:** User bật dark mode.
- **Bước thực hiện:** 1) Bật dark. 2) Reload / khởi động lại app / đăng nhập lại. 3) Quan sát theme khởi tạo.
- **Dữ liệu test:** preference lưu (localStorage/user setting) = `dark`.
- **Kết quả mong đợi:** Sau khi quay lại, app khởi tạo ở dark mode theo preference đã lưu; không revert về light/OS.
- **Coverage hiện tại:** PARTIAL — suy từ status DONE. Cần xác minh test file (đề xuất `theme_persist_dark`).

### TC-THEME-007 — Mọi component đều có biến thể dark (không sót)
- **Function:** THEME-002
- **Loại:** Edge / Visual
- **Ưu tiên:** P1
- **Layer:** Manual/UI (visual regression)
- **Tiền điều kiện:** App ở dark mode.
- **Bước thực hiện:** 1) Duyệt tất cả màn chính + modal, dropdown, toast, bảng, badge trạng thái.
- **Dữ liệu test:** Class `dark` active.
- **Kết quả mong đợi:** Không component nào còn nền trắng/chữ đen lạc lõng; contrast đạt WCAG AA ở dark; icon/đường viền nhìn rõ.
- **Coverage hiện tại:** PARTIAL — suy từ status DONE. Cần xác minh test file (đề xuất Playwright visual snapshot dark).

### TC-THEME-008 — Không có hiện tượng flash sai theme khi load (FOUC/FOIT)
- **Function:** THEME-002
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** E2E (Playwright)
- **Tiền điều kiện:** preference = dark đã lưu.
- **Bước thực hiện:** 1) Tải lại trang nhiều lần; quay video/track class `<html>` ngay khi load.
- **Dữ liệu test:** preference dark; mạng/CPU throttle.
- **Kết quả mong đợi:** App áp dark ngay từ frame đầu (script đọc preference trước paint); không thấy chớp sáng light.
- **Coverage hiện tại:** PARTIAL — suy từ status DONE. Cần xác minh test file (đề xuất `theme_no_flash`).

### TC-THEME-009 — Toggle hoạt động ở chế độ offline (Tauri)
- **Function:** THEME-002
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** E2E (Tauri) / Manual
- **Tiền điều kiện:** App Tauri chạy offline (không mạng).
- **Bước thực hiện:** 1) Ngắt mạng. 2) Toggle dark/light. 3) Khởi động lại app.
- **Dữ liệu test:** offline; preference lưu local.
- **Kết quả mong đợi:** Toggle vẫn hoạt động và preference lưu cục bộ, áp lại sau restart kể cả offline (không phụ thuộc API server).
- **Coverage hiện tại:** PARTIAL — suy từ status DONE. Cần xác minh test file (đề xuất Tauri e2e offline theme).

### TC-THEME-010 — Preference theme là theo từng người dùng (không lẫn giữa user)
- **Function:** THEME-002
- **Loại:** Edge (cô lập theo user)
- **Ưu tiên:** P1
- **Layer:** E2E (Playwright)
- **Tiền điều kiện:** Hai user U1, U2 trên cùng máy/khác phiên đăng nhập.
- **Bước thực hiện:** 1) U1 bật dark, đăng xuất. 2) U2 đăng nhập. 3) Quan sát theme của U2.
- **Dữ liệu test:** U1 preference=dark; U2 chưa set.
- **Kết quả mong đợi:** U2 không tự nhận dark của U1 (preference gắn theo user, không rò rỉ). *Ghi chú: đây là tính năng UI client-side — KHÔNG áp dụng cô lập clinic theo RLS DB; cô lập ở mức user preference.*
- **Coverage hiện tại:** PARTIAL — suy từ status DONE. Cần xác minh test file (đề xuất `theme_per_user`).

### TC-THEME-011 — Tự detect dark theo OS khi lần đầu (prefers-color-scheme: dark)
- **Function:** THEME-003
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Unit + E2E (Playwright emulate colorScheme)
- **Tiền điều kiện:** User chưa override theme (preference trống); OS đặt dark.
- **Bước thực hiện:** 1) Emulate `prefers-color-scheme: dark`. 2) Mở app lần đầu.
- **Dữ liệu test:** media query = dark; localStorage `theme`=null.
- **Kết quả mong đợi:** App tự áp dark mode theo OS ngay lần đầu (class `dark` trên `<html>`).
- **Coverage hiện tại:** PARTIAL — suy từ status DONE (TASK-017). Cần xác minh test file (đề xuất `theme.spec.ts::detect_os_dark`).

### TC-THEME-012 — Tự detect light theo OS khi lần đầu (prefers-color-scheme: light)
- **Function:** THEME-003
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** E2E (Playwright emulate colorScheme)
- **Tiền điều kiện:** Preference trống; OS đặt light.
- **Bước thực hiện:** 1) Emulate `prefers-color-scheme: light`. 2) Mở app.
- **Dữ liệu test:** media query = light; preference null.
- **Kết quả mong đợi:** App áp light mode theo OS.
- **Coverage hiện tại:** PARTIAL — suy từ status DONE. Cần xác minh test file (đề xuất `detect_os_light`).

### TC-THEME-013 — User override thắng OS detection
- **Function:** THEME-003
- **Loại:** Negative / Business rule
- **Ưu tiên:** P0
- **Layer:** E2E (Playwright)
- **Tiền điều kiện:** OS = dark; user đã chủ động chọn light (override).
- **Bước thực hiện:** 1) Set OS dark. 2) User toggle về light. 3) Reload app.
- **Dữ liệu test:** OS=dark; preference=light (override flag set).
- **Kết quả mong đợi:** App giữ light theo override của user, KHÔNG bị OS detection ghi đè.
- **Coverage hiện tại:** PARTIAL — suy từ status DONE. Cần xác minh test file (đề xuất `override_beats_os`).

### TC-THEME-014 — App cập nhật theo OS đổi theme khi user CHƯA override
- **Function:** THEME-003
- **Loại:** Edge
- **Ưu tiên:** P1
- **Layer:** E2E (Playwright media change event)
- **Tiền điều kiện:** Preference trống (chưa override); app đang mở.
- **Bước thực hiện:** 1) Đang ở light. 2) Đổi OS sang dark (bắn sự kiện change của media query). 3) Quan sát realtime.
- **Dữ liệu test:** prefers-color-scheme đổi light→dark; không override.
- **Kết quả mong đợi:** App tự chuyển sang dark realtime mà không cần reload (listener media query).
- **Coverage hiện tại:** PARTIAL — suy từ status DONE. Cần xác minh test file (đề xuất `os_change_live_update`).

### TC-THEME-015 — App KHÔNG đổi theo OS khi user đã override
- **Function:** THEME-003
- **Loại:** Edge / Negative
- **Ưu tiên:** P1
- **Layer:** E2E (Playwright media change event)
- **Tiền điều kiện:** User đã override (chọn dark thủ công); app đang mở.
- **Bước thực hiện:** 1) Đổi OS từ dark sang light. 2) Quan sát.
- **Dữ liệu test:** OS đổi dark→light; preference override=dark.
- **Kết quả mong đợi:** App giữ nguyên dark (đã override), bỏ qua thay đổi OS.
- **Coverage hiện tại:** PARTIAL — suy từ status DONE. Cần xác minh test file (đề xuất `os_change_ignored_when_override`).

### TC-THEME-016 — Browser/OS không hỗ trợ prefers-color-scheme → fallback an toàn
- **Function:** THEME-003
- **Loại:** Edge / Negative
- **Ưu tiên:** P2
- **Layer:** Unit
- **Tiền điều kiện:** Môi trường không hỗ trợ media query `prefers-color-scheme` (trả về no-preference).
- **Bước thực hiện:** 1) Mock matchMedia trả no-preference/undefined. 2) Khởi tạo theme.
- **Dữ liệu test:** matchMedia không hỗ trợ.
- **Kết quả mong đợi:** Fallback về light mode mặc định (THEME-001), không throw error, không crash.
- **Coverage hiện tại:** PARTIAL — suy từ status DONE. Cần xác minh test file (đề xuất `detect_fallback_default`).

---

## Tổng kết Coverage

| Coverage | Số test case |
|---|---|
| COVERED | 0 |
| PARTIAL | 16 |
| MISSING | 0 |

**Kết luận:** Nhóm THEME gồm **3 function** (THEME-001 Light mode, THEME-002 Dark mode, THEME-003 System theme detection), tất cả role **System**, thuộc **TASK-017**, trạng thái nguồn **DONE**. Đây là tính năng **giao diện client-side** (Tailwind class-based `dark:` + Tauri offline), nên test tập trung Unit (logic toggle/detect/override), E2E Playwright (emulate `colorScheme`, persistence, no-flash) và Manual/UI visual regression. **Không áp dụng** test 401/403 hay cô lập clinic theo RLS DB vì nhóm này không có endpoint API hay đụng dữ liệu domain; cô lập chỉ ở mức user preference (TC-THEME-010).

Vì cột status nguồn = DONE nhưng **không truy cập/liệt kê được repo frontend** trong môi trường hiện tại, toàn bộ 16 test case được gán **PARTIAL** (suy từ status DONE) kèm ghi chú **"cần xác minh test file"**. Bước tiếp theo: mở repo `clinic-cms-web` để định vị các spec test theme thực tế (đề xuất `theme.spec.ts` + Playwright e2e), nâng các case khớp lên **COVERED** và bổ sung các case còn thiếu.
