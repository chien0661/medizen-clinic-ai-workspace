# MediZen Modern — Fresh Stitch Project

**Cập nhật**: 2026-05-01
**Stitch project (NEW)**: https://stitch.withgoogle.com/projects/2542650746708884228
**Stitch project (OLD — deprecate)**: https://stitch.withgoogle.com/projects/5572301228665717471
**Design system asset**: `assets/3512187121078190969` ("MediZen Modern" — clean, không còn "Cura" branding)

> Sau khi old project tích lũy nhiều duplicates từ TASK-027/029 batch retries, quyết định tạo project mới hoàn toàn để có baseline sạch sẽ. Doc này canonical mapping screen IDs trong project mới.

---

## 1. Trạng thái — 32/47 màn ✓ (~68%)

| Nhóm | Đã có | Còn thiếu |
|---|:---:|:---:|
| Auth & Onboarding | 2/3 | Quên mật khẩu |
| Dashboards (per-role + multi-role) | 6/6 | — |
| Bệnh nhân (master + detail) | 0/2 | Danh sách BN, Hồ sơ BN 8 tab |
| Queue board kanban | 0/1 | Phòng chờ kanban |
| Lịch hẹn | 1/1 | — |
| EMR 6 tabs | 6/6 | — |
| Tiếp nhận BN | 1/1 | — |
| Pharmacy (cấp phát + 4 sub) | 1/5 | Catalog, PO Nhập kho, Kiểm kê, Xử lý hết hạn |
| Billing (thanh toán + 2 sub) | 1/3 | Lịch sử hoá đơn, Công nợ AR |
| Settings 8 sections | 8/8 | — |
| Reports 6 tabs | 6/6 | — |
| Profile multi-tab | 0/1 | Profile cá nhân (5 tab) |
| Modals & popovers | 0/2 | Cmd+K palette, Clinic switcher dropdown |
| Notifications full page | 0/1 | Notifications |
| **Tổng** | **32/47** | **15** |

---

## 2. Canonical screen IDs — 32 màn ✓ (project mới `2542650746708884228`)

### Auth (2/3)
| Màn | Screen ID |
|---|---|
| Login | `10fa1b88fcb14939b196120c068b4359` |
| Chọn phòng khám | `a24a76fa86c34ab4bd29280e3f8a673d` |

### Dashboards (6/6)
| Màn | Screen ID |
|---|---|
| Dashboard Lễ tân | `08884cb4dda34c2a94b0d0859ead80c3` |
| Dashboard Điều dưỡng | `2048c96803b942ce9a327a6b8fb5eca8` |
| Dashboard Bác sĩ | `a1da59d6c00e4a0186408c134d0a7bc1` |
| Dashboard Dược sĩ | `e22f743e588d476a935e06e6a7bead0d` |
| Dashboard Quản trị | `0107aedca56b4e86a10034239dbee630` |
| Dashboard Multi-role (Tổng quan) | `18ed36db80964e6c9f32ac367163cb6f` |

### Clinical workflow (3/3)
| Màn | Screen ID |
|---|---|
| Tiếp nhận & Đăng ký BN | `c192150a9ca44949b2ae7bff71268055` |
| Lịch hẹn (calendar tuần) | `d4a26b27a53f4627a759d4a47be5ef64` |
| Kho thuốc & Cấp phát | `d1f07ac3a95d447f89a9324dd6dad740` |

### EMR — 6 tabs (6/6)
| Màn | Screen ID |
|---|---|
| Tab 1 Sinh hiệu | `7099e99ae3f54df7a109f9c1b1e2de3c` |
| Tab 2 Khám LS (S.O.A.P) | `b65f72edaff34c588183ec43bcfa4020` |
| Tab 3 Chẩn đoán | `f7a8a34921584dc8a40fb8d690b975b4` |
| Tab 4 Kê đơn thuốc (stock chip RX-016) | `e09e91adb049450ebb842dfe3a84339b` |
| Tab 5 Cận lâm sàng (CLS) | `1c8dc9a45b4646ca93b743e76cb7fd5c` |
| Tab 6 Tóm tắt & Hoàn tất | `1ffdbfe6457a4b0bbc1319f338b16656` |

### Billing (1/3)
| Màn | Screen ID |
|---|---|
| Thanh toán Hoá đơn | `6c560c9159bd492a93f81a040fc081ff` |

### Cấu hình (8/8)
| Màn | Screen ID |
|---|---|
| Phòng khám & Chi nhánh (toggle BHYT default OFF) | `cf5b5eaa419a469591f378d8756dc1c4` |
| Vai trò & Phân quyền (RBAC) | `db783faa5ee44d5fa7a4495c4640151a` |
| Ca trực & Giờ làm | `c37cf2c381c44368aed26bc6f03c9116` |
| Bảng giá dịch vụ | `149093160f354daaa28ba80046bc8f19` |
| BHYT (Mức hưởng + DM) | `1a8f4df42c844078ba28ad915ccc87e8` |
| Tích hợp (VSS Disabled banner) | `9b5d4a26e1ff42368a64721ef9d1c95e` |
| Audit Log | `c13abb5084b946e7ae1ba3ae56c32df2` |
| Bảo mật & Mã hoá (PII inventory + Anomaly + Hash chain) | `c8547b82621c4c0ca4abb8a4e3a2f149` |

### Reports — 6 tabs (6/6)
| Màn | Screen ID |
|---|---|
| Tab 1 Tổng quan | `0edb38245675437a9b9eeca7b5cdf91c` |
| Tab 2 Tài chính | `af50d7704ee34c6d9589438b51ac1e0e` |
| Tab 3 Lâm sàng | `7673357fad4b4c468b4eefa51d100f98` |
| Tab 4 Vận hành | `e3fdaab8c9514a0291c2e1ee0c7945bd` |
| Tab 5 Dược | `b98d3d7a78c643d69f7474d71f2d926b` |
| Tab 6 BHYT | (chưa có — cần fire lại trong TASK-030) |

---

## 3. 15 màn còn thiếu — TASK-030 backlog

| # | Nhóm | Màn | Priority |
|---|---|---|:---:|
| 1 | Auth | Quên mật khẩu | High |
| 2 | BN | Danh sách Bệnh nhân (master list) | High |
| 3 | BN | Hồ sơ BN chi tiết (8 tabs) | High |
| 4 | Queue | Phòng chờ kanban (5 cột) | High |
| 5 | Reports | Tab 6 BHYT | High |
| 6 | Pharmacy | Danh mục thuốc | Medium |
| 7 | Pharmacy | Nhập kho (PO) | Medium |
| 8 | Pharmacy | Kiểm kê wizard | Medium |
| 9 | Pharmacy | Xử lý hết hạn | Medium |
| 10 | Billing | Lịch sử hoá đơn | Medium |
| 11 | Billing | Công nợ AR aging | Medium |
| 12 | Profile | Profile cá nhân (5 tabs với "Phòng khám của tôi") | High |
| 13 | Modals | Cmd+K Quick search palette | High |
| 14 | Popover | Clinic switcher dropdown | High |
| 15 | Notifications | Notifications full page | Medium |

→ Sau khi xong: **47 unique canonical screens**.

---

## 4. Cleanup notes (project mới — sạch hơn nhiều)

Trong project mới `2542650746708884228` có **2 duplicates** cần xoá thủ công:
- `f208b29370b54e749fc136ca2d5d049b` "Cấu hình BHYT — MediZen" — bản cũ trước retry
- `e59bef8bee744926ae5654f6b26ef25e` "Cấu hình Tích hợp (VSS Disabled)" — bản trước, replaced by `9b5d4a26`

Project cũ `5572301228665717471` (Cura) có ~50 màn lộn xộn — **deprecate hoàn toàn**, không cần cleanup vì không reference trong docs nữa.

---

## 5. Tại sao 15 màn missing

**Nguyên nhân**:
1. Stitch generation reliability giảm sau 5-6 batches concurrent fire (từ ~85% batch 1-3 xuống ~25% batch 5-6)
2. MCP timeout vẫn trả "succeeded server-side" nhưng nhiều lần Stitch không persist
3. Không có cơ chế retry-confirm tốt qua MCP
4. Phase D màn (BN list, Profile multi-tab, Cmd+K, Clinic switcher) là màn complex, dễ timeout hơn

**Workaround cho TASK-030**:
- Fire 1 màn / call (không batch parallel) — chậm hơn nhưng reliable hơn
- Hoặc fire 3-4 màn / batch (sweet spot)
- Verify từng màn trước khi fire màn tiếp theo
- Total ước tính: 15 màn × 3-5 phút = ~60-90 phút wall-clock

---

## 6. Apply mapping vào docs khác

Các docs cũ (`SITEMAP.md`, `MENU_AND_SCREENS.md`, `TAB_MATRIX.md`, `MULTI_ROLE_UX.md`) đang reference screen IDs từ project cũ. Cần update:
- Replace project URL `5572301228665717471` → `2542650746708884228`
- Replace 32 screen IDs theo bảng §2
- Mark 15 màn còn lại là "TODO TASK-030"

Xem [`MENU_AND_SCREENS.md`](MENU_AND_SCREENS.md) §G Phase D backlog — sẽ cần update sau khi TASK-030 done.

---

**Status**: TASK-029 — IN_REVIEW (partial 32/47 = 68% done)
**Next**: TASK-030 — Generate 15 remaining màn cho fresh project
