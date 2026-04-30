# TASK-027 — Stitch Screen Mapping (Phase B + C)

**Stitch project**: https://stitch.withgoogle.com/projects/5572301228665717471
**Hoàn tất**: 2026-04-30
**Cách tạo**: Stitch MCP `generate_screen_from_text` với prompt theo spec `cura-modern/TAB_MATRIX.md` + `MULTI_ROLE_UX.md`.

## Tổng

| Trước TASK-027 | Sinh thêm | Sau TASK-027 |
|---|---|---|
| 14 màn unique | +18 màn (1 Phase B + 17 Phase C) | **32 màn unique** |

Cura design system v2 (`assets/12787757101558093729`) đã apply cho mọi màn — tokens Indigo `#6366F1` / Slate / Emerald / Amber / Red, Plus Jakarta Sans + Inter, 12/8/6 px roundness.

## Phase B — Multi-role Dashboard (1)

| Màn | Stitch ID |
|---|---|
| Dashboard Multi-role (BS + Quản trị) | `308fffe2883f4c1cad7e7441120158b9` |

## Phase C — EMR tab variants (5)

| Tab | Stitch ID |
|---|---|
| Tab 1 — Sinh hiệu | `acef698641904014bf33326dcdd90813` |
| Tab 2 — Khám LS (S.O.A.P) | `c12bf23adc844cfc8b3d4f632111b501` |
| Tab 4 — Kê đơn thuốc | `7e32e3c8c27043dfae12c8409a1acc2a` |
| Tab 5 — Cận lâm sàng (CLS) | `b8f84b4034da4ebda2040f1260a01a0a` |
| Tab 6 — Tóm tắt & Hoàn tất | `41e3a324001a4c469864e4538ad5539a` |

(Tab 3 — Chẩn đoán đã có từ trước: `fbb61911b4f0496392836546150d2cb9`)

## Phase C — Settings tab variants (7)

| Section | Stitch ID |
|---|---|
| Phòng khám & Chi nhánh | `5f5f1093c7114782aaf063043443395d` |
| Vai trò & Phân quyền (RBAC) | `1cb79779d2f145efb13f3d1223f70fc0` |
| Ca trực & Giờ làm | `31b1b71d30bd4de88048648db5ab158f` |
| BHYT (Mức hưởng + DM) | `7ff9fe5bc8d541ecb7844f8965ddbf2b` |
| Tích hợp (VSS/HL7/DICOM/SMS) | `1d6fc53966d541c4abb1f3c6949fc20f` |
| Audit log | `e7735b5a24944273b631b514409be668` |
| Bảo mật & Mã hoá | `b15b501502274b55999bc61ac70f5045` |

(Bảng giá DV đã có từ trước: `7c43ae65ba4346fea4685212f222866b`)

## Phase C — Reports tab variants (5)

| Tab | Stitch ID |
|---|---|
| Tài chính | `e471372c45ce42da827ce03c7f14559c` |
| Lâm sàng | `eb2d066147e2472180010db35b66333e` |
| Vận hành | `9431a116c63b4045a9798698d0826d41` |
| Dược | `6b235c69f8e047c7a5798990e9665c81` |
| BHYT | `12334fcf1bec408a80075ea361164ad4` |

(Tab Tổng quan đã có từ trước: `d86ddd116f614b41b7f6536af01f86dc`)

## Duplicate cần xoá thủ công (4 màn)

MCP `generate_screen_from_text` timeout phía client trong khi server vẫn xử lý → một số request được thử lại tự động bởi Stitch generator, sinh ra duplicate. Đã xác định 4 màn cần xoá thủ công khi mở project:

| Stitch ID | Tiêu đề | Lý do |
|---|---|---|
| `283a28fda61c4785973ee139f668a00b` | Kho thuốc V2 | Bản retry cũ (trước task) |
| `4da3b971f72b410a8a44f6ed76149b18` | Kho thuốc V3 | Empty, không có screenshot |
| `692bb83d5b254461ad1abdef1ae7b0f3` | Dashboard Đa vai trò | Auto-retry batch 1 |
| `a83fc3556c1f438eb070d7708e017902` | Dashboard Đa vai trò v3 | Auto-retry batch 1 |

→ Sau khi xoá, tổng còn lại đúng **32 unique canonical**.

## Patterns đã enforce trên 18 màn mới

1. **EMR (5 màn)**: cùng patient banner sticky · 3-col 280/720/380 · tab strip 6 dot indicators · footer "← back / draft / next →".
2. **Settings (7 màn)**: cùng sub-nav 240px (settings tree) · tab strip horizontal · footer "Hủy / Xuất / 💾 Lưu thay đổi".
3. **Reports (5 màn)**: cùng filter bar sticky (date · clinic · export) · KPI 4 cards · charts grid · tables footer · trend sparklines.
4. **Multi-role Dashboard (1 màn)**: merge sidebar 2 group label ("─── Bác sĩ ───" + "─── Quản trị ───") · KPI cards có chip role nguồn · 2 widget song song · quick action matrix trộn role.

## Đã update đồng thời

- `docs/design/cura-modern/README.md` — section "32 màn (đã đủ)" + flag duplicates
- `docs/design/cura-modern/SITEMAP.md` §6 — bảng mapping screen ID toàn bộ 32 màn + bảng duplicates riêng
- `docs/design/cura-modern/TAB_MATRIX.md` — đính `**Stitch screen**: <id>` ở đầu mỗi tab/section (20 mục)
- `docs/design/cura-modern/MULTI_ROLE_UX.md` §4 — đính screen ID Multi-role Dashboard

## Việc còn lại (ngoài scope task này)

- **TASK-028 (đề xuất)**: port các màn Stitch sang React/Tailwind trong `clinic-cms-web`, áp dụng tokens vào `tailwind.config.js`, dùng Stitch HTML làm reference component skeleton.
- **Manual cleanup**: vào Stitch project xoá 4 màn duplicate đã liệt kê.
