# Test Case Catalog — NAV · Điều hướng & Quick Search

**Nguồn:** function_list_data.py (group NAV, dòng 1757-1790) + clinic_management_function_list.md (mục 25) + system_design/SaaS.
**Phạm vi:** 8 functions.  **Tổng test case:** 27.  **Ngày:** 2026-05-30.

> **Ghi chú truy cập & Coverage:** Repo mã nguồn `E:/MyProject/clinic-cms-merge/app` và `E:/MyProject/clinic-cms-merge/tests` **KHÔNG tồn tại / không truy cập được** (thư mục thực tế là `E:/MyProject/clinic-cms`, không có `app/` ở đó từ môi trường này). Do đó Coverage được **suy ra từ cột status nguồn** trong `function_list_data.py`:
> - NAV-001..005, NAV-007: status **TODO** (⬜) → **MISSING**, kèm ghi chú "cần xác minh test file".
> - NAV-006: status **IDEA** (💡, Phase v2, chưa lên kế hoạch) → **MISSING** (chưa triển khai).
> - NAV-008: status **DONE** (✅) → đánh dấu **PARTIAL** vì không truy cập được test file để xác minh; cần xác minh test file khi repo khả dụng.
>
> Phần lớn NAV là tầng UI (SPA + Tauri shell). Các function chạm **dữ liệu domain qua API backend** và do đó cần case phân quyền + cô lập clinic (RLS): **NAV-001** (global search đa entity), **NAV-003** (search bệnh nhân, perm `patient.read`), **NAV-004** (search thuốc, perm `medicine.read`). **NAV-002** (clinic switcher) liên quan trực tiếp luồng AUTH-021 (reset JWT + set RLS `app.current_clinic_id`) nên có case bảo mật chuyển clinic.

---

## 1. Ma trận truy vết (Function → Test Cases → Coverage)

| Function | Tên chức năng | Status (nguồn) | Test Case IDs | Coverage |
|---|---|---|---|---|
| NAV-001 | Global command palette (Ctrl+K / ⌘K) | TODO | TC-NAV-001, TC-NAV-002, TC-NAV-003, TC-NAV-004 | MISSING |
| NAV-002 | Clinic switcher dropdown (topbar) | TODO | TC-NAV-005, TC-NAV-006, TC-NAV-007, TC-NAV-008 | MISSING |
| NAV-003 | Quick search bệnh nhân (/bn) | TODO | TC-NAV-009, TC-NAV-010, TC-NAV-011, TC-NAV-012 | MISSING |
| NAV-004 | Quick search thuốc (/thuoc) | TODO | TC-NAV-013, TC-NAV-014, TC-NAV-015, TC-NAV-016 | MISSING |
| NAV-005 | Quick search feature/màn (default mode) | TODO | TC-NAV-017, TC-NAV-018, TC-NAV-019 | MISSING |
| NAV-006 | Recent items pin | IDEA (v2) | TC-NAV-020, TC-NAV-021, TC-NAV-022 | MISSING |
| NAV-007 | Keyboard shortcuts cheatsheet | TODO | TC-NAV-023, TC-NAV-024 | MISSING |
| NAV-008 | Breadcrumb navigation (topbar) | DONE | TC-NAV-025, TC-NAV-026, TC-NAV-027 | PARTIAL |

---

## 2. Chi tiết Test Cases

### TC-NAV-001 — Mở command palette bằng Ctrl+K ở mọi màn & search đa entity
- **Function:** NAV-001
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** E2E (httpx) + Manual/UI
- **Tiền điều kiện:** User đăng nhập vào clinic có dữ liệu mẫu: bệnh nhân, thuốc, hoá đơn (INV-), đơn thuốc (RX-), lượt khám (LK-).
- **Bước thực hiện:** 1) Ở màn bất kỳ nhấn Ctrl+K (⌘K trên macOS) → popup mở. 2) Gõ từ khóa khớp nhiều loại entity. 3) Quan sát kết quả group theo entity. 4) Dùng ↑/↓ chọn rồi Enter.
- **Dữ liệu test:** Từ khóa "an" khớp bệnh nhân + thuốc; số "INV-" / "RX-" / "LK-".
- **Kết quả mong đợi:** Popup mở ở mọi route; kết quả group theo entity (Bệnh nhân/Thuốc/Hoá đơn/Đơn thuốc/Lượt khám/Tính năng), mỗi item có icon + breadcrumb; ↑/↓/Enter điều hướng đúng không cần chuột; p95 < 300ms (theo NFR-019).
- **Coverage hiện tại:** MISSING (function TODO — cần xác minh test file API/E2E khi repo khả dụng).

### TC-NAV-002 — Global search cô lập dữ liệu theo clinic (RLS)
- **Function:** NAV-001
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** 2 clinic A và B; mỗi clinic có bệnh nhân/thuốc trùng tên (vd. cùng "Minh").
- **Bước thực hiện:** 1) Đăng nhập user clinic A (JWT có clinic_id=A, RLS `app.current_clinic_id`=A). 2) Gọi global search "Minh". 3) Lặp với user clinic B.
- **Dữ liệu test:** entity_A (clinic A), entity_B (clinic B) cùng từ khóa.
- **Kết quả mong đợi:** User A chỉ thấy entity của clinic A; user B chỉ thấy của clinic B; không rò rỉ chéo clinic (RLS chặn ở tầng DB, không chỉ filter app).
- **Coverage hiện tại:** MISSING (function TODO — cần xác minh test file RLS).

### TC-NAV-003 — Global search yêu cầu xác thực (401)
- **Function:** NAV-001
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Endpoint global search yêu cầu auth.
- **Bước thực hiện:** 1) Gọi API search không kèm token. 2) Gọi lại với token hết hạn/không hợp lệ.
- **Dữ liệu test:** Request thiếu header Authorization; token rác.
- **Kết quả mong đợi:** Trả 401 cho cả hai; không trả bất kỳ kết quả dữ liệu nào.
- **Coverage hiện tại:** MISSING (function TODO — cần xác minh test file).

### TC-NAV-004 — Esc đóng palette & query không khớp trả trạng thái rỗng
- **Function:** NAV-001
- **Loại:** Negative / Edge
- **Ưu tiên:** P2
- **Layer:** Manual/UI + E2E
- **Tiền điều kiện:** Palette đang mở.
- **Bước thực hiện:** 1) Gõ từ khóa vô nghĩa "zzzqqq". 2) Quan sát. 3) Nhấn Esc.
- **Dữ liệu test:** Chuỗi không khớp; chuỗi rỗng/khoảng trắng.
- **Kết quả mong đợi:** Hiển thị "Không tìm thấy kết quả" (không 500); query rỗng không quét toàn bảng; Esc đóng popup, focus trả về màn nền.
- **Coverage hiện tại:** MISSING (function TODO — cần xác minh test file).

### TC-NAV-005 — Clinic switcher liệt kê đúng các phòng khám user có quyền
- **Function:** NAV-002
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB) + Manual/UI
- **Tiền điều kiện:** User có pivot `account_clinic_role` với 3 clinic; 1 trong số đó là current.
- **Bước thực hiện:** 1) Đăng nhập. 2) Click avatar topbar mở dropdown 240px. 3) Quan sát danh sách + chỉ báo current.
- **Dữ liệu test:** Account gắn 3 clinic; clinic hiện tại = clinic #1.
- **Kết quả mong đợi:** Dropdown liệt kê đúng 3 clinic user có quyền; clinic hiện tại có chip "Hiện tại" (indigo); footer có 2 link "→ Cấu hình clinic" và "Đăng xuất".
- **Coverage hiện tại:** MISSING (function TODO — cần xác minh test file).

### TC-NAV-006 — Switch clinic reset JWT + RLS context (AUTH-021)
- **Function:** NAV-002
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB) + E2E (httpx)
- **Tiền điều kiện:** User có quyền clinic A (current) và clinic B với role/perm khác nhau.
- **Bước thực hiện:** 1) Đang ở clinic A. 2) Click row clinic B trong switcher → POST /auth/switch-clinic. 3) Dùng JWT cũ gọi API. 4) Dùng JWT mới gọi API dữ liệu clinic B.
- **Dữ liệu test:** clinic A perms ≠ clinic B perms.
- **Kết quả mong đợi:** JWT cũ bị revoke (blacklist Redis) → trả 401; JWT mới có clinic_id=B + roles/perms của B; RLS `app.current_clinic_id`=B; FE clear cache; audit event 'clinic.switch' được ghi; không thấy dữ liệu clinic A.
- **Coverage hiện tại:** MISSING (function TODO — cần xác minh test file, phụ thuộc AUTH-021).

### TC-NAV-007 — Không thể switch sang clinic ngoài quyền (403)
- **Function:** NAV-002
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** E2E (httpx)
- **Tiền điều kiện:** Tồn tại clinic C mà user KHÔNG có pivot row.
- **Bước thực hiện:** 1) Gọi POST /auth/switch-clinic với clinic_id=C (bypass UI). 2) Quan sát.
- **Dữ liệu test:** clinic_id của clinic không thuộc user.
- **Kết quả mong đợi:** Trả 403; JWT hiện tại không đổi; không sinh token cho clinic C.
- **Coverage hiện tại:** MISSING (function TODO — cần xác minh test file).

### TC-NAV-008 — User chỉ có 1 clinic ẩn dropdown
- **Function:** NAV-002
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Manual/UI
- **Tiền điều kiện:** User chỉ gắn 1 clinic.
- **Bước thực hiện:** 1) Đăng nhập. 2) Quan sát topbar avatar.
- **Dữ liệu test:** Account gắn duy nhất 1 clinic.
- **Kết quả mong đợi:** Không hiện dropdown switcher; chỉ hiện text-only tên clinic; (search box trong dropdown chỉ xuất hiện khi user có >5 clinic).
- **Coverage hiện tại:** MISSING (function TODO — cần xác minh test file).

### TC-NAV-009 — Quick search bệnh nhân /bn trả kết quả fuzzy đa tiêu chí
- **Function:** NAV-003
- **Loại:** Happy path
- **Ưu tiên:** P0
- **Layer:** Integration (real DB) + E2E (httpx)
- **Tiền điều kiện:** Clinic có bệnh nhân với tên dấu, mã BN, SĐT, CCCD; user có perm `patient.read`.
- **Bước thực hiện:** 1) Mở palette gõ "/bn nguyen van a" (không dấu). 2) Thử search theo mã BN, SĐT, CCCD. 3) Quan sát 5 result đầu.
- **Dữ liệu test:** BN "Nguyễn Văn A", mã BN, SĐT 09xx, CCCD.
- **Kết quả mong đợi:** Khớp fuzzy unaccent + trigram theo tên; khớp chính xác theo mã/SĐT/CCCD/BHYT (nếu enabled); hiện ≤5 card mini (avatar + tuổi/giới + mã BN + chip status visit gần nhất); click → /patients/{id}.
- **Coverage hiện tại:** MISSING (function TODO — cần xác minh test file).

### TC-NAV-010 — Search bệnh nhân yêu cầu permission patient.read (403/ẩn)
- **Function:** NAV-003
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB) + E2E (httpx)
- **Tiền điều kiện:** User role KHÔNG có `patient.read`.
- **Bước thực hiện:** 1) Đăng nhập user thiếu quyền. 2) Gõ "/bn" + từ khóa khớp BN. 3) Gọi trực tiếp API search BN.
- **Dữ liệu test:** Role thiếu `patient.read`; BN tồn tại.
- **Kết quả mong đợi:** Không hiện kết quả BN (tab/kết quả ẩn); gọi API trực tiếp trả 403; không rò rỉ thông tin BN.
- **Coverage hiện tại:** MISSING (function TODO — cần xác minh test file).

### TC-NAV-011 — Search bệnh nhân cô lập theo clinic (RLS)
- **Function:** NAV-003
- **Loại:** Security
- **Ưu tiên:** P0
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** 2 clinic, mỗi clinic có BN trùng tên.
- **Bước thực hiện:** 1) User clinic A search "/bn Trần B". 2) User clinic B search cùng từ khóa.
- **Dữ liệu test:** patient_A (clinic A), patient_B (clinic B) cùng tên.
- **Kết quả mong đợi:** User A chỉ thấy patient_A; user B chỉ thấy patient_B; RLS chặn chéo clinic.
- **Coverage hiện tại:** MISSING (function TODO — cần xác minh test file RLS).

### TC-NAV-012 — Search bệnh nhân với dấu tiếng Việt & query rỗng
- **Function:** NAV-003
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** BN có tên dấu "Lê Hà Vy".
- **Bước thực hiện:** 1) Gõ "le ha vy" (không dấu). 2) Gõ "LÊ HÀ VY" (in hoa có dấu). 3) Gõ chuỗi rỗng / 1 ký tự.
- **Dữ liệu test:** Biến thể dấu/hoa-thường; query rỗng/ngắn.
- **Kết quả mong đợi:** Cả hai biến thể đều khớp "Lê Hà Vy" (unaccent); query rỗng/quá ngắn không trigger quét toàn bảng, trả rỗng có kiểm soát.
- **Coverage hiện tại:** MISSING (function TODO — cần xác minh test file).

### TC-NAV-013 — Quick search thuốc /thuoc hiển thị stock badge + giá
- **Function:** NAV-004
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Integration (real DB) + E2E (httpx)
- **Tiền điều kiện:** Clinic có thuốc đủ trạng thái tồn kho; user có perm `medicine.read`.
- **Bước thực hiện:** 1) Mở palette gõ "/thuoc amox". 2) Search theo hoạt chất và mã ATC. 3) Quan sát badge + giá + chip BHYT.
- **Dữ liệu test:** Thuốc "Amoxicillin" (còn 320v), 1 thuốc "Sắp hết", 1 thuốc "Hết hàng".
- **Kết quả mong đợi:** Khớp theo tên thương mại/hoạt chất/ATC; mỗi result hiện stock badge (emerald "Còn 320v" / amber "Sắp hết" / red "Hết hàng") + giá + chip "Trong DM BHYT" nếu bhyt_enabled; click → mở Medicine Detail.
- **Coverage hiện tại:** MISSING (function TODO — cần xác minh test file).

### TC-NAV-014 — Search thuốc trong EMR Tab Kê đơn add thẳng vào đơn
- **Function:** NAV-004
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Manual/UI + Integration
- **Tiền điều kiện:** Đang ở EMR Tab Kê đơn của một lượt khám; user role Doctor.
- **Bước thực hiện:** 1) Trong tab Kê đơn mở quick search "/thuoc". 2) Chọn 1 thuốc.
- **Dữ liệu test:** Thuốc còn hàng.
- **Kết quả mong đợi:** Thuốc được add thẳng vào đơn đang soạn (không điều hướng rời màn); số lượng mặc định cho phép chỉnh.
- **Coverage hiện tại:** MISSING (function TODO — cần xác minh test file).

### TC-NAV-015 — Search thuốc yêu cầu permission medicine.read (403/ẩn)
- **Function:** NAV-004
- **Loại:** Security
- **Ưu tiên:** P1
- **Layer:** Integration (real DB) + E2E
- **Tiền điều kiện:** User role không có `medicine.read` (vd. Receptionist).
- **Bước thực hiện:** 1) Đăng nhập user thiếu quyền. 2) Search "/thuoc". 3) Gọi API search thuốc trực tiếp.
- **Dữ liệu test:** Role thiếu `medicine.read`.
- **Kết quả mong đợi:** Kết quả thuốc không hiện; API trực tiếp trả 403.
- **Coverage hiện tại:** MISSING (function TODO — cần xác minh test file).

### TC-NAV-016 — Search thuốc cô lập theo clinic (RLS)
- **Function:** NAV-004
- **Loại:** Security
- **Ưu tiên:** P1
- **Layer:** Integration (real DB)
- **Tiền điều kiện:** 2 clinic có danh mục thuốc riêng (tồn kho khác nhau cùng tên thuốc).
- **Bước thực hiện:** 1) User clinic A search thuốc X. 2) User clinic B search thuốc X.
- **Dữ liệu test:** Thuốc X tồn ở cả 2 clinic với stock khác nhau.
- **Kết quả mong đợi:** Mỗi user thấy tồn kho/giá của clinic mình; không lẫn dữ liệu kho clinic khác (RLS).
- **Coverage hiện tại:** MISSING (function TODO — cần xác minh test file).

### TC-NAV-017 — Search feature/màn fuzzy match nhãn menu/route
- **Function:** NAV-005
- **Loại:** Happy path
- **Ưu tiên:** P2
- **Layer:** Manual/UI
- **Tiền điều kiện:** User đăng nhập (default mode, không prefix).
- **Bước thực hiện:** 1) Mở palette gõ "ke don". 2) Gõ "cau hinh". 3) Chọn 1 kết quả.
- **Dữ liệu test:** "ke don" → "Khám bệnh → Kê đơn thuốc"; "cau hinh" → "Cấu hình hệ thống → Phòng khám".
- **Kết quả mong đợi:** Fuzzy match đúng route; chọn → điều hướng tới màn tương ứng.
- **Coverage hiện tại:** MISSING (function TODO — cần xác minh test file).

### TC-NAV-018 — Empty state hiển thị top 5 frequent & track recent/frequent
- **Function:** NAV-005
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Manual/UI
- **Tiền điều kiện:** User đã sử dụng vài route nhiều lần (lưu Tauri local storage).
- **Bước thực hiện:** 1) Truy cập route X nhiều lần. 2) Mở palette không gõ gì. 3) Quan sát empty state.
- **Dữ liệu test:** Lịch sử dùng route per-user.
- **Kết quả mong đợi:** Empty state hiện top 5 mục frequent; mục hay dùng đẩy lên top theo recent + frequent.
- **Coverage hiện tại:** MISSING (function TODO — cần xác minh test file).

### TC-NAV-019 — Feature search chỉ hiện route trong quyền user
- **Function:** NAV-005
- **Loại:** Security
- **Ưu tiên:** P1
- **Layer:** Manual/UI + E2E
- **Tiền điều kiện:** User role hạn chế (vd. Receptionist).
- **Bước thực hiện:** 1) Search nhãn của module ngoài quyền (vd. "cau hinh he thong"). 2) Thử deep-link route đó.
- **Dữ liệu test:** Role Receptionist.
- **Kết quả mong đợi:** Route ngoài quyền không xuất hiện trong kết quả; deep-link bị chặn (403/redirect).
- **Coverage hiện tại:** MISSING (function TODO — cần xác minh test file).

### TC-NAV-020 — Recent items hiển thị 5 entity mở gần nhất ở footer popup
- **Function:** NAV-006
- **Loại:** Happy path
- **Ưu tiên:** P2
- **Layer:** Manual/UI + Integration
- **Tiền điều kiện:** User mở lần lượt nhiều entity khác loại (BN, đơn, hoá đơn, lượt khám). (Lưu ý: NAV-006 là IDEA/Phase v2 — chưa triển khai.)
- **Bước thực hiện:** 1) Mở 6 entity cross-type. 2) Mở palette xem footer recent.
- **Dữ liệu test:** BN, RX-, INV-, LK- gần nhất.
- **Kết quả mong đợi:** Footer hiển thị 5 entity mở gần nhất (mới nhất trước, cross-type); click chip → navigate; persisted per-user (Tauri local storage / Redis `user:recent:{uid}`).
- **Coverage hiện tại:** MISSING (function IDEA Phase v2 — chưa triển khai; cần xác minh test file khi build).

### TC-NAV-021 — Recent items cô lập per-user / per-clinic
- **Function:** NAV-006
- **Loại:** Security
- **Ưu tiên:** P2
- **Layer:** Integration (real DB) / Manual
- **Tiền điều kiện:** 2 user khác nhau; user A mở vài entity của clinic A.
- **Bước thực hiện:** 1) User A mở entity. 2) User B mở palette xem recent.
- **Dữ liệu test:** Entity clinic A.
- **Kết quả mong đợi:** User B không thấy recent của user A / clinic A; recent cô lập theo `user:recent:{uid}` và clinic.
- **Coverage hiện tại:** MISSING (function IDEA Phase v2 — chưa triển khai).

### TC-NAV-022 — Recent items giới hạn 5 mục & loại trùng
- **Function:** NAV-006
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Integration / Manual
- **Tiền điều kiện:** User mở > 5 entity.
- **Bước thực hiện:** 1) Mở > 5 entity khác nhau. 2) Mở lại 1 entity đã có. 3) Xem footer recent.
- **Dữ liệu test:** > 5 entity; 1 entity lặp.
- **Kết quả mong đợi:** Giữ tối đa 5 mục, mục cũ nhất bị đẩy ra; entity mở lại không tạo bản trùng mà nhảy lên đầu.
- **Coverage hiện tại:** MISSING (function IDEA Phase v2 — chưa triển khai).

### TC-NAV-023 — Mở cheatsheet bằng "?" / Ctrl+/ và hiển thị shortcuts theo scope
- **Function:** NAV-007
- **Loại:** Happy path
- **Ưu tiên:** P2
- **Layer:** Manual/UI
- **Tiền điều kiện:** User đăng nhập; không đang focus trong input.
- **Bước thực hiện:** 1) Nhấn "?" (hoặc Ctrl+/). 2) Quan sát modal full-screen. 3) Kiểm nhóm scope.
- **Dữ liệu test:** Bộ shortcut: Global (Ctrl+K, Ctrl+N, Ctrl+/, Esc), EMR (Tab, Ctrl+S), Pharmacy (Ctrl+D).
- **Kết quả mong đợi:** Modal hiện tất cả shortcuts nhóm theo scope (Global / EMR / Pharmacy); mỗi shortcut hiển thị cả Win/Mac (⌘K); Esc đóng modal.
- **Coverage hiện tại:** MISSING (function TODO — cần xác minh test file).

### TC-NAV-024 — "?" không kích hoạt khi đang gõ trong input
- **Function:** NAV-007
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Manual/UI
- **Tiền điều kiện:** Một ô input/textarea đang focus.
- **Bước thực hiện:** 1) Focus ô tìm kiếm/ghi chú. 2) Gõ ký tự "?".
- **Dữ liệu test:** Ký tự "?" trong input.
- **Kết quả mong đợi:** Ký tự "?" nhập bình thường vào ô; modal cheatsheet KHÔNG mở (tránh side-effect khi nhập liệu).
- **Coverage hiện tại:** MISSING (function TODO — cần xác minh test file).

### TC-NAV-025 — Breadcrumb phản ánh hierarchy & auto-update khi navigate
- **Function:** NAV-008
- **Loại:** Happy path
- **Ưu tiên:** P1
- **Layer:** Manual/UI + E2E
- **Tiền điều kiện:** User đăng nhập; có một lượt khám của BN.
- **Bước thực hiện:** 1) Điều hướng tới màn Khám bệnh của BN "Lê Hà Vy". 2) Quan sát breadcrumb. 3) Điều hướng sang module khác.
- **Dữ liệu test:** Lượt khám LK-20260430-0042 của "Lê Hà Vy".
- **Kết quả mong đợi:** Topbar hiện "Trang chủ / Khám bệnh / Lê Hà Vy (LK-20260430-0042)"; resource cuối có badge status ("Đang khám" indigo / "Đã hoàn tất" emerald); breadcrumb auto-update khi đổi màn.
- **Coverage hiện tại:** PARTIAL (status nguồn DONE nhưng không truy cập được test file để xác minh — cần xác minh test file khi repo khả dụng).

### TC-NAV-026 — Click level cao trên breadcrumb quay về đúng trang cha
- **Function:** NAV-008
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Manual/UI
- **Tiền điều kiện:** Đang ở màn resource cuối (≥3 cấp).
- **Bước thực hiện:** 1) Ở màn chi tiết. 2) Click level "Khám bệnh" trên breadcrumb.
- **Dữ liệu test:** Cây điều hướng nhiều cấp.
- **Kết quả mong đợi:** Điều hướng về đúng màn cấp cha; breadcrumb cập nhật lại; không lỗi 404; cấp cuối (current) không click được.
- **Coverage hiện tại:** PARTIAL (status nguồn DONE — cần xác minh test file).

### TC-NAV-027 — Breadcrumb badge status cập nhật theo trạng thái resource
- **Function:** NAV-008
- **Loại:** Edge
- **Ưu tiên:** P2
- **Layer:** Manual/UI + Integration
- **Tiền điều kiện:** Lượt khám đang ở trạng thái "Đang khám".
- **Bước thực hiện:** 1) Mở lượt khám đang khám → quan sát badge. 2) Hoàn tất lượt khám. 3) Quan sát lại badge breadcrumb.
- **Dữ liệu test:** Lượt khám chuyển "Đang khám" → "Đã hoàn tất".
- **Kết quả mong đợi:** Badge breadcrumb đổi từ "Đang khám" (indigo) sang "Đã hoàn tất" (emerald) phản ánh đúng trạng thái thực tế của resource.
- **Coverage hiện tại:** PARTIAL (status nguồn DONE — cần xác minh test file).
