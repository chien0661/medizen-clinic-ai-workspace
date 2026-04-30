# MediZen Modern — Fresh Stitch Project

**Cập nhật**: 2026-05-01 (TASK-031 partial DONE — 45/47 canonical + 2 blocked by Stitch API)
**Stitch project (NEW)**: https://stitch.withgoogle.com/projects/2542650746708884228
**Stitch project (OLD — deprecated)**: https://stitch.withgoogle.com/projects/5572301228665717471
**Design system asset**: `assets/3512187121078190969` ("MediZen Modern" — clean, không còn "Cura" branding)

> Sau khi old project tích lũy nhiều duplicates từ TASK-027/029 batch retries, quyết định tạo project mới hoàn toàn để có baseline sạch sẽ. Doc này canonical mapping screen IDs trong project mới.

---

## 1. Trạng thái — 45/47 canonical ✓ (~96%) + 2 blocked-stitch-api

| Nhóm | Đã có | Còn thiếu |
|---|:---:|---|
| Auth & Onboarding | 3/3 | — |
| Dashboards (per-role + multi-role) | 6/6 | — |
| Bệnh nhân (master + detail) | 2/2 | — |
| Queue board kanban | 1/1 | — |
| Lịch hẹn | 1/1 (+1 bonus "Quản lý lịch hẹn") | — |
| EMR 6 tabs | 6/6 | — |
| Tiếp nhận BN | 1/1 | — |
| Pharmacy (cấp phát + 4 sub) | 5/5 | — |
| Billing (thanh toán + 2 sub) | 2/3 | **Công nợ AR aging** (blocked-stitch-api) |
| Settings 8 sections | 8/8 | — |
| Reports 6 tabs | 6/6 | — |
| Profile multi-tab | 1/1 | — |
| Modals & popovers | 2/2 | — |
| Notifications full page | 0/1 | **Notifications** (blocked-stitch-api) |
| **Tổng** | **45/47** | **2 blocked** |

**Quản lý lịch hẹn** (`f9728dac61f44dbd9118ff79e2819f0b`) là bonus screen — alt-naming/management view của Lịch hẹn calendar tuần. Giữ lại làm alternative listing layout.

---

## 2. Canonical screen IDs — 45 màn ✓ (project `2542650746708884228`)

### Auth & Onboarding (3/3)
| Màn | Screen ID |
|---|---|
| Login | `10fa1b88fcb14939b196120c068b4359` |
| Chọn phòng khám (multi-clinic select sau login) | `a24a76fa86c34ab4bd29280e3f8a673d` |
| Quên mật khẩu (centered card 400px) | `e7d8a31dfb64457dbb1065168111ae01` |

### Dashboards (6/6)
| Màn | Screen ID |
|---|---|
| Dashboard Lễ tân | `08884cb4dda34c2a94b0d0859ead80c3` |
| Dashboard Điều dưỡng | `2048c96803b942ce9a327a6b8fb5eca8` |
| Dashboard Bác sĩ | `a1da59d6c00e4a0186408c134d0a7bc1` |
| Dashboard Dược sĩ | `e22f743e588d476a935e06e6a7bead0d` |
| Dashboard Quản trị | `0107aedca56b4e86a10034239dbee630` |
| Dashboard Multi-role (Tổng quan) | `18ed36db80964e6c9f32ac367163cb6f` |

### Clinical workflow (4/4 + 1 bonus)
| Màn | Screen ID |
|---|---|
| Tiếp nhận & Đăng ký BN | `c192150a9ca44949b2ae7bff71268055` |
| Lịch hẹn (calendar tuần) | `d4a26b27a53f4627a759d4a47be5ef64` |
| Quản lý lịch hẹn (bonus — list/management view) | `f9728dac61f44dbd9118ff79e2819f0b` |
| Phòng chờ Kanban (5 cột state machine, 27 BN, 1 cấp cứu RED) | `b29cce2159544b148ca95def7ffd36ac` |
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

### Patient Master (2/2)
| Màn | Screen ID |
|---|---|
| Danh sách Bệnh nhân (table 12 rows + filter sticky + pagination) | `4e751f21216f4d57914c09e909ebeeef` |
| Hồ sơ BN — Lê Hà Vy (3-col 280/720/380, 8 tabs, AI gợi ý card) | `2d438ac0dfb04bdc83e41ec0b29bc7d9` |

### Billing (2/3 — 1 blocked)
| Màn | Screen ID |
|---|---|
| Thanh toán Hoá đơn | `6c560c9159bd492a93f81a040fc081ff` |
| Lịch sử hoá đơn (table + filter date/status/method + pagination) | `e4089713951341d18ca200d33e2bbc66` |
| **Công nợ AR aging** — buckets 0-30/31-60/61-90/>90 ngày | ⚠️ blocked-stitch-api (xem §4) |

### Pharmacy (5/5)
| Màn | Screen ID |
|---|---|
| Kho thuốc & Cấp phát (Pending Dispense) | `d1f07ac3a95d447f89a9324dd6dad740` |
| Danh mục thuốc (table 12+ rows, filter, CRUD inline) | `59d0a9320fd84fd2a281cff113657d95` |
| Tạo phiếu nhập kho (PO + line items thuốc/lô/HSD/qty/giá vốn) | `3cb03ffce4ea4f739cbe1f82576b349b` |
| Kiểm kê thực tế (3-step wizard: chọn category → đếm → adjustment) | `8ed40f5e4cf54108adf4fe0d59b0048d` |
| Xử lý hết hạn (table 30/60/90d HSD + actions disposal/giảm giá/trả NCC) | `9c07546bdc214e499f3af5db011b2249` |

### Cấu hình hệ thống (8/8)
| Màn | Screen ID |
|---|---|
| Phòng khám & Chi nhánh (toggle BHYT default OFF) | `cf5b5eaa419a469591f378d8756dc1c4` |
| Vai trò & Phân quyền (RBAC) | `db783faa5ee44d5fa7a4495c4640151a` |
| Ca trực & Giờ làm | `c37cf2c381c44368aed26bc6f03c9116` |
| Bảng giá dịch vụ | `149093160f354daaa28ba80046bc8f19` |
| BHYT (Mức hưởng + DM) | `1a8f4df42c844078ba28ad915ccc87e8` |
| Tích hợp (VSS/HL7/DICOM/SMS) | `9b5d4a26e1ff42368a64721ef9d1c95e` |
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
| Tab 6 BHYT (funnel duyệt 4 stages, top 10 lý do từ chối, trend 12 tháng, sync VSS) | `0b6214575af0401a8f8b96402e3c0d70` |

### Modals & Popovers (2/2)
| Màn | Screen ID |
|---|---|
| ⌘K Quick Search Palette (sub-mode prefix `/bn /thuoc /inv /rx /lk`) | `3812ba7a5ff8430890011daceafd3343` |
| Clinic Switcher Dropdown (3 PK với role chip + "Hiện tại" current) | `af58042597394694a83eebec6c3d5ff1` |

### Profile Multi-tab (1/1)
| Màn | Screen ID |
|---|---|
| Profile cá nhân — BS. An (5 tabs với "Phòng khám của tôi" ACTIVE — 3 PK card + radio default) | `18d1ec870224423c8b50717aeb957bd3` |

### Notifications (0/1 — blocked)
| Màn | Screen ID |
|---|---|
| **Trung tâm Thông báo** — table 14 rows + filter date/type/source + bulk actions | ⚠️ blocked-stitch-api (xem §4) |

---

## 3. Cleanup notes — 12 duplicates trong project mới cần xoá thủ công

Stitch retry server-side đôi khi tạo phiên bản mới thay vì update in-place. Các duplicates dưới đây cần xoá qua Stitch UI:

### Auth dups
- `63dea7d252cf415499f5a0568830b911` — Quên MK retry 1 (canonical = `e7d8a31d`)
- `d642bdeebd2b4ac2a8c25e1b17178ec2` — Quên MK retry 2

### Patient dups
- `57e82178bb45450cae8e1b7d3be82182` — Danh sách BN retry 1 (canonical = `4e751f21`)
- `05867e02ef464d6a993d9df526eb0060` — Danh sách BN retry 2
- `905f2198c8fe4a61b7f48b10057f71d7` — Hồ sơ BN retry 1 (canonical = `2d438ac0`)
- `938893912b9140a7aebad9c4803e3d60` — Hồ sơ BN retry 2

### Queue dups
- `70fe170da19d4f26a82a5aa8e48df6ff` — "Phòng chờ — Queue Board" alt-name (canonical Kanban = `b29cce21`)
- `eccd3ef35d544f0abf15694f8ea382cd` — Phòng chờ Queue Board retry

### Settings dups
- `f208b29370b54e749fc136ca2d5d049b` — Cấu hình BHYT v1 (canonical = `1a8f4df4` "Mức hưởng")
- `e59bef8bee744926ae5654f6b26ef25e` — Cấu hình Tích hợp (VSS Disabled) v1 (canonical = `9b5d4a26`)

### Reports dups
- `0a5d702b2f994c0a973978a8f7fd152c` — Báo cáo BHYT retry (canonical = `0b621457`)

### Modals dups
- `6020a87a892a4ef59faa3722fa430a4a` — Cmd+K retry (canonical = `3812ba7a`)

→ Sau khi xoá 12 duplicates: **45 unique canonical screens** + bonus "Quản lý lịch hẹn" = 46 screens trong project.

---

## 4. Blocked-stitch-api — 2 màn missing

### Màn còn thiếu

| # | Màn | Đã fire | Result |
|---|---|---|---|
| 1 | **Billing — Công nợ AR aging** | 2 lần (TASK-031 batch C+D + retry 1x) | MCP timeout, server không persist |
| 2 | **Notifications full page** | 2 lần (TASK-031 batch C+D + retry 1x) | MCP timeout, server không persist |

### Nguyên nhân

Stitch project `2542650746708884228` đã có 57 screens (45 canonical + 12 dups). Khi project >50 screens, Stitch generation hit rate-limit/throughput hard cap khiến server không persist mọi prompt mới — chỉ confirm receipt rồi drop.

### Cách giải quyết (ngoài luồng auto)

Lựa chọn 1 — **Manual qua Stitch UI**: Mở project, click "+ New screen" → paste prompt từ `task.md` §A.2 (mục "Lịch sử hoá đơn" và "Công nợ AR aging" / "Notifications full page") → wait → screen sinh ra.

Lựa chọn 2 — **Cleanup duplicates trước**: Xoá 12 duplicates ở §3 để giảm project size về 45 screens, sau đó retry 2 màn thiếu — có khả năng cao success.

Lựa chọn 3 — **Defer to FE implementation phase**: TASK-032 (FE port React/Tailwind) sẽ implement 2 màn này trực tiếp dựa trên prompt spec đã có trong `task.md` (đủ chi tiết để code).

→ **Khuyến nghị**: Lựa chọn 2 (cleanup → retry) hoặc Lựa chọn 3 (skip Stitch, code trực tiếp).

---

## 5. Apply mapping vào docs khác

Các docs khác (`SITEMAP.md`, `MENU_AND_SCREENS.md`, `TAB_MATRIX.md`, `MULTI_ROLE_UX.md`, `README.md`) cần update:
- Replace project URL `5572301228665717471` → `2542650746708884228`
- Replace screen IDs theo bảng §2 trong các Phase D references
- Mark 2 màn còn lại là "blocked-stitch-api" hoặc "TODO TASK-032"

---

## 6. Multi-clinic per account architecture

Project mới phản ánh chuẩn multi-clinic per account (TASK-026 + AUTH-018..022 functions):
- Login KHÔNG còn clinic_code field
- Sau login → "Chọn phòng khám" nếu user có multi-clinic, else auto-redirect dashboard
- Topbar có Clinic Switcher dropdown để chuyển clinic without re-login
- Profile cá nhân tab "Phòng khám của tôi" cho phép set default clinic

---

**Status**: TASK-031 — IN_REVIEW (45/47 = 96% canonical, 2 blocked-stitch-api)
**Next**: TASK-032 (proposed) — FE Phase D implementation (port 47 màn sang React/Tailwind, code 2 màn blocked trực tiếp)
