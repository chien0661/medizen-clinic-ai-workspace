# TASK-029 — Stitch Cleanup & Screen Mapping

**Cập nhật**: 2026-05-01 (sau batch 1 EDIT — 8/8 succeed)
**Stitch project**: https://stitch.withgoogle.com/projects/5572301228665717471

---

## A. Cleanup list — 15 màn cần xoá thủ công khỏi Stitch UI

> MCP không có `delete_screen` tool → phải vào Stitch project xoá thủ công. Click vào mỗi screen → "..." → Delete.

### A.1 — Old versions replaced bởi EDIT batch 1 (8 màn)

| # | Old ID (xoá) | Tên cũ | New ID (canonical) |
|---|---|---|---|
| 1 | `e98de272bc7249f39f9a233c7adb17f2` | Màn Đăng nhập Cura (có field clinic_code) | `569434d14ff34d6a902e796b88d93394` |
| 2 | `7e32e3c8c27043dfae12c8409a1acc2a` | EMR Tab 4 — Kê đơn (không có stock chip) | `efa12301afcb49f48c0db6bee18d2247` |
| 3 | `5f5f1093c7114782aaf063043443395d` | Cấu hình Phòng khám (không có toggle BHYT) | `d50565d932674ccc94f6b0a15dcc8f83` |
| 4 | `b15b501502274b55999bc61ac70f5045` | Bảo mật & Mã hoá (chưa có PII inventory + anomaly + hash chain card) | `f47b869348944312a32616fd88a4d4c3` |
| 5 | `308fffe2883f4c1cad7e7441120158b9` | Multi-role Dashboard (chưa có ⌘K + clinic switcher topbar) | `245746efaff741ddaaf6ba533b3e674b` |
| 6 | `e1e5cfeb40ce4de49b9be9e922fc3ab2` | Dashboard Quản trị (chưa có ⌘K + clinic switcher) | `4e585cec433d4c4ca39cb782f427762b` |
| 7 | `ccc8e77578684bd98a03a7d4344f70ff` | Dashboard Bác sĩ (chưa có ⌘K + clinic switcher) | `d4617e39b6044dc9ac4b502249fb85bb` |
| 8 | `1d6fc53966d541c4abb1f3c6949fc20f` | Cấu hình Tích hợp (chưa có VSS disabled banner) | `95a0acfd6e214d84bcd2ac7d63891451` |

### A.2 — Duplicates từ TASK-027 (4 màn — chưa xoá từ trước)

| # | Old ID (xoá) | Tên cũ | Lý do |
|---|---|---|---|
| 9 | `283a28fda61c4785973ee139f668a00b` | Kho thuốc & Cấp phát (V2) | Bản retry cũ từ trước TASK-027 |
| 10 | `4da3b971f72b410a8a44f6ed76149b18` | Kho thuốc & Cấp phát (V3 incomplete) | Empty, no screenshot |
| 11 | `692bb83d5b254461ad1abdef1ae7b0f3` | Dashboard Đa vai trò (auto-retry) | Stitch tự retry khi MCP timeout TASK-027 batch 1 |
| 12 | `a83fc3556c1f438eb070d7708e017902` | Dashboard Đa vai trò v3 | Same |

### A.3 — Duplicates Reports từ TASK-027 batch 3 retry (3 màn — phát hiện mới)

| # | Old ID (xoá) | Tên cũ | Canonical giữ lại |
|---|---|---|---|
| 13 | `ebc4859b18f74a9bbea060b0d5467cbe` | Báo cáo Vận hành (retry) | `9431a116c63b4045a9798698d0826d41` |
| 14 | `8aa802b201974e019b4a4af3a74dcd6e` | Báo cáo Dược (retry) | `6b235c69f8e047c7a5798990e9665c81` |
| 15 | `1310a9581ba64853931e28dd680e815a` | Báo cáo BHYT (retry) | `12334fcf1bec408a80075ea361164ad4` |

→ **Tổng 15 màn cần xoá thủ công**. Sau cleanup: tổng còn lại = (45 hiện tại) − 15 = **30 canonical**, sau đó cộng 16 màn Phase D mới = **46 canonical** (sau batch 2/3 GENERATE complete).

---

## B. Canonical mapping sau batch 1 EDIT (31 màn)

### 🔐 Auth (1)
- Đăng nhập (mới) — `569434d14ff34d6a902e796b88d93394` ⬅ TASK-029 EDIT

### 🏠 Dashboards (6)
- Dashboard Lễ tân — `e8ec8790c76f4a04b42400c78f3e934a`
- Dashboard Điều dưỡng — `416445275b17462e87c4dd6f29d42106`
- Dashboard Bác sĩ (mới) — `d4617e39b6044dc9ac4b502249fb85bb` ⬅ TASK-029 EDIT (topbar)
- Dashboard Dược sĩ — `0d856e6c35484cd2bffc967b23ce8268`
- Dashboard Quản trị (mới) — `4e585cec433d4c4ca39cb782f427762b` ⬅ TASK-029 EDIT (topbar)
- Dashboard Multi-role BS+QT (mới) — `245746efaff741ddaaf6ba533b3e674b` ⬅ TASK-029 EDIT (topbar)

### 🏥 Clinical workflow (3)
- Tiếp nhận & Đăng ký BN — `8c84c7e3270d4b729d83d1c5d4f60992`
- Lịch hẹn (week view) — `2e1591c3fd534046932aaf2969fd571b`
- Kho thuốc & Cấp phát — `434d73b9387947328139f56dfad5309f`

### 🩺 EMR — 6 tab
- Tab 1 Sinh hiệu — `acef698641904014bf33326dcdd90813`
- Tab 2 Khám LS (S.O.A.P) — `c12bf23adc844cfc8b3d4f632111b501`
- Tab 3 Chẩn đoán — `fbb61911b4f0496392836546150d2cb9`
- Tab 4 Kê đơn (mới) — `efa12301afcb49f48c0db6bee18d2247` ⬅ TASK-029 EDIT (stock chip)
- Tab 5 CLS — `b8f84b4034da4ebda2040f1260a01a0a`
- Tab 6 Tóm tắt — `41e3a324001a4c469864e4538ad5539a`

### 💰 Billing (1)
- Thanh toán hoá đơn — `43971b42ba2b4043a89e8aa32261ec16`

### ⚙️ Cấu hình (8)
- Phòng khám (mới) — `d50565d932674ccc94f6b0a15dcc8f83` ⬅ TASK-029 EDIT (toggle BHYT)
- RBAC — `1cb79779d2f145efb13f3d1223f70fc0`
- Ca trực — `31b1b71d30bd4de88048648db5ab158f`
- Bảng giá DV — `7c43ae65ba4346fea4685212f222866b`
- BHYT — `7ff9fe5bc8d541ecb7844f8965ddbf2b`
- Tích hợp (mới) — `95a0acfd6e214d84bcd2ac7d63891451` ⬅ TASK-029 EDIT (VSS disabled)
- Audit log — `e7735b5a24944273b631b514409be668`
- Bảo mật (mới) — `f47b869348944312a32616fd88a4d4c3` ⬅ TASK-029 EDIT (PII/anomaly/hash chain)

### 📊 Báo cáo (6)
- Tổng quan — `d86ddd116f614b41b7f6536af01f86dc`
- Tài chính — `e471372c45ce42da827ce03c7f14559c`
- Lâm sàng — `eb2d066147e2472180010db35b66333e`
- Vận hành — `9431a116c63b4045a9798698d0826d41`
- Dược — `6b235c69f8e047c7a5798990e9665c81`
- BHYT — `12334fcf1bec408a80075ea361164ad4`

→ **31 canonical** sau batch 1.

---

## C. Phase D backlog — 11 màn còn cần GENERATE

### Batch 2 (8 high-priority) — đã fire, **5/8 confirmed**
- [x] **Chọn phòng khám** — `20a43e4f061642a6b72749438eb9d902` ✓
- [x] **Quên mật khẩu** — `135acdcc79184490bb3c3b9e871643df` ✓
- [x] **Danh sách BN** — `26c8ef9ff7cb425ea86d1d37697b3805` ✓
- [x] **Hồ sơ BN 8 tabs (Lê Hà Vy)** — `1518032028644744bbf952600da820ff` ✓
- [x] **Phòng chờ Queue Board** — `0974ed00c4ed4a639e44f11202edb7e4` ✓
- [ ] Profile multi-tab — **không persist** (Stitch agent timeout không lưu)
- [ ] Cmd+K Quick search palette — **không persist**
- [ ] Clinic switcher dropdown — **không persist** (mặc dù initial response confirmed)

### Batch 3 (8 medium-priority) — chưa fire
- [ ] Pharmacy — Danh mục thuốc
- [ ] Pharmacy — Nhập kho (PO)
- [ ] Pharmacy — Kiểm kê wizard
- [ ] Pharmacy — Xử lý hết hạn
- [ ] Billing — Lịch sử hoá đơn
- [ ] Billing — Công nợ AR aging
- [ ] Notifications full page
- [ ] (Optional) Tiếp nhận BN re-gen

### Retry batch (3 màn batch 2 missing) — re-fire trong batch 3
- [ ] Profile multi-tab
- [ ] Cmd+K Quick search palette
- [ ] Clinic switcher dropdown

→ Phase D còn cần GENERATE: **8 batch 3 + 3 retry = 11 màn**.

→ Sau Phase D complete: **31 (TASK-027) + 8 (EDIT) + 5 (batch 2) + 11 (còn lại) = 55** màn với 15 duplicates → cleanup → **40 canonical** (gộp 24 chưa thay đổi + 8 EDIT mới + 8 GENERATE batch 2/retry hoàn tất + 8 GENERATE batch 3).

---

## D. State sau batch 1+2 (TASK-029 progress 13/24 actions)

**Batch 1 EDIT: 8/8 ✓** (tất cả timed-out đều đã succeed server-side)
**Batch 2 GENERATE: 5/8** (3 missing chưa persist)

**Canonical count hiện tại**: 24 nguyên gốc + 8 EDIT + 5 GENERATE = **37 màn**
**Duplicates**: 15 cần xoá thủ công (8 OLD versions + 4 from TASK-027 + 3 Reports retries)
**Còn cần GENERATE**: 11 màn (batch 3 + retry)

---

## D. Manual cleanup checklist cho user

1. Mở Stitch project: https://stitch.withgoogle.com/projects/5572301228665717471
2. Cho mỗi ID trong §A (15 IDs), tìm screen → click "..." → Delete
3. Verify count: tổng còn lại sau cleanup = canonical IDs
4. Đổi tên Stitch project: "Cura Clinic — Modern (Role-Based EMR)" → "MediZen — Modern (Role-Based EMR)"
5. (Optional) Đổi tên design system asset `assets/12787757101558093729` "Cura Modern" → "MediZen Modern" qua MCP `update_design_system`

→ Sau cleanup + rebrand, project sạch sẽ và đồng bộ với docs.
