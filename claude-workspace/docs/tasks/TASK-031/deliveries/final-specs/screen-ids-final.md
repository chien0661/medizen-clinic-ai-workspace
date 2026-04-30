# TASK-031 — Final Screen IDs Mapping

**Date**: 2026-05-01
**Stitch Project**: `2542650746708884228` (MediZen Modern fresh project)
**Design system asset**: `assets/3512187121078190969`
**Status**: 45/47 canonical screens (~96%) + 2 blocked-stitch-api

## Result Summary

| Group | Count |
|---|:---:|
| Canonical screens | **45** |
| Bonus screen ("Quản lý lịch hẹn") | **1** |
| Duplicates pending manual cleanup | **12** |
| Blocked-stitch-api (need TASK-032 or manual UI fire) | **2** |
| **Total in project** | **57** |

## 13 màn mới sinh trong TASK-031 (15 target → 13 sinh thành công)

| # | Màn | Screen ID | Status |
|---|---|---|---|
| 1 | Quên mật khẩu | `e7d8a31dfb64457dbb1065168111ae01` | ✓ |
| 2 | Danh sách Bệnh nhân | `4e751f21216f4d57914c09e909ebeeef` | ✓ |
| 3 | Hồ sơ Bệnh nhân (Lê Hà Vy, 8 tabs) | `2d438ac0dfb04bdc83e41ec0b29bc7d9` | ✓ |
| 4 | Phòng chờ Kanban (5 cột) | `b29cce2159544b148ca95def7ffd36ac` | ✓ (đã có từ TASK-029) |
| 5 | Báo cáo Tab BHYT | `0b6214575af0401a8f8b96402e3c0d70` | ✓ |
| 6 | Profile cá nhân BS. An (5 tabs) | `18d1ec870224423c8b50717aeb957bd3` | ✓ |
| 7 | ⌘K Quick Search Palette | `3812ba7a5ff8430890011daceafd3343` | ✓ |
| 8 | Clinic Switcher Dropdown | `af58042597394694a83eebec6c3d5ff1` | ✓ |
| 9 | Pharmacy — Danh mục thuốc | `59d0a9320fd84fd2a281cff113657d95` | ✓ |
| 10 | Pharmacy — Tạo phiếu nhập kho | `3cb03ffce4ea4f739cbe1f82576b349b` | ✓ |
| 11 | Pharmacy — Kiểm kê thực tế | `8ed40f5e4cf54108adf4fe0d59b0048d` | ✓ |
| 12 | Pharmacy — Xử lý hết hạn | `9c07546bdc214e499f3af5db011b2249` | ✓ |
| 13 | Billing — Lịch sử hoá đơn | `e4089713951341d18ca200d33e2bbc66` | ✓ |
| 14 | Billing — Công nợ AR aging | — | ⚠️ **blocked-stitch-api** |
| 15 | Notifications full page | — | ⚠️ **blocked-stitch-api** |

## 12 Duplicates pending manual cleanup

| ID | Title | Canonical replacement |
|---|---|---|
| `63dea7d252cf415499f5a0568830b911` | Quên mật khẩu | `e7d8a31d` |
| `d642bdeebd2b4ac2a8c25e1b17178ec2` | Quên mật khẩu | `e7d8a31d` |
| `57e82178bb45450cae8e1b7d3be82182` | Danh sách BN | `4e751f21` |
| `05867e02ef464d6a993d9df526eb0060` | Danh sách BN | `4e751f21` |
| `905f2198c8fe4a61b7f48b10057f71d7` | Hồ sơ BN | `2d438ac0` |
| `938893912b9140a7aebad9c4803e3d60` | Hồ sơ BN | `2d438ac0` |
| `70fe170da19d4f26a82a5aa8e48df6ff` | Phòng chờ Queue Board | `b29cce21` (Kanban) |
| `eccd3ef35d544f0abf15694f8ea382cd` | Phòng chờ Queue Board | `b29cce21` (Kanban) |
| `f208b29370b54e749fc136ca2d5d049b` | Cấu hình BHYT v1 | `1a8f4df4` |
| `e59bef8bee744926ae5654f6b26ef25e` | Cấu hình Tích hợp v1 | `9b5d4a26` |
| `0a5d702b2f994c0a973978a8f7fd152c` | Báo cáo BHYT | `0b621457` |
| `6020a87a892a4ef59faa3722fa430a4a` | ⌘K Quick Search | `3812ba7a` |

## Strategy applied

- Sequential 1-prompt-per-call pattern → reliability ~93% (13/14 effective fires)
- Retry-once rule cho 2 màn fail → cả 2 retry vẫn fail (Stitch rate-limit cứng)
- Per spec, mark 2 màn còn thiếu là `blocked-stitch-api` thay vì spam retry

## Recommendation cho 2 màn blocked

1. **Cleanup 12 duplicates trước** → giảm project size về 45 → retry 2 màn còn lại có khả năng thành công cao
2. **Hoặc skip Stitch, code trực tiếp trong TASK-032** — prompt spec đã có chi tiết trong `task.md` §A.1 + §A.2 đủ để FE port React/Tailwind

## Stitch project URL

https://stitch.withgoogle.com/projects/2542650746708884228
