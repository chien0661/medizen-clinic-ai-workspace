# MediZen v2.0 — Stitch Project Tracking

**Cập nhật**: 2026-05-31
**Stitch Project Part 1**: https://stitch.withgoogle.com/projects/18324036454103633899
**Project ID**: `18324036454103633899`
**Design System**: `assets/144349522488444424` — "MediZen v2.0 Indigo Premium"

## Design System
- **Primary**: Indigo #4F46E5
- **Secondary**: Violet #7C3AED
- **Accent**: Rose #EC4899
- **Background**: Lavender #F5F3FF
- **Fonts**: Plus Jakarta Sans (headline) + Inter (body)
- **Roundness**: ROUND_EIGHT (8px)

---

## Trạng thái: 6/25 canonical screens ✓

### Auth (3/3) ✓
| Screen | ID |
|--------|----|
| Login | `d396c03cc9504d458ecd9974055f16cf` |
| Chọn phòng khám | `8ff309983b7b471d87ec6f78916b9caf` |
| Quên mật khẩu | `4425a4cb27204912a9e69c2e7c98779f` |

### Dashboards (3/6) — còn 3
| Screen | ID | Status |
|--------|----|--------|
| Dashboard Lễ tân | `a776538f67bd4a8e8284a8001e06b7e4` | ✓ |
| Dashboard Điều dưỡng | `0c81716bfc27465db7c8b72e5d14aa08` | ✓ |
| Dashboard Bác sĩ | `3753d7e7b15949f5992fc2d0a4afee2a` | ✓ |
| Dashboard Dược sĩ | — | ⏳ TODO |
| Dashboard Quản trị | — | ⏳ TODO |
| Dashboard Multi-role | — | ⏳ TODO |

### Clinical Workflow (0/6) — còn 6
| Screen | Status |
|--------|--------|
| Danh sách bệnh nhân | ⏳ TODO |
| Hồ sơ bệnh nhân (Patient detail) | ⏳ TODO |
| Tiếp nhận & đăng ký BN mới | ⏳ TODO |
| Queue board / Phòng chờ (Kanban) | ⏳ TODO |
| Lịch hẹn (calendar tuần) | ⏳ TODO |
| EMR - Sinh hiệu | ⏳ TODO |

### EMR Tabs (0/5) — còn 5
| Screen | Status |
|--------|--------|
| EMR - Khám lâm sàng (SOAP) | ⏳ TODO |
| EMR - Chẩn đoán (ICD-10) | ⏳ TODO |
| EMR - Kê đơn thuốc | ⏳ TODO |
| EMR - Cận lâm sàng (CLS) | ⏳ TODO |
| EMR - Tóm tắt & hoàn tất | ⏳ TODO |

### Pharmacy & Billing (0/5) — còn 5
| Screen | Status |
|--------|--------|
| Cấp phát đơn thuốc | ⏳ TODO |
| Danh mục thuốc | ⏳ TODO |
| Nhập kho | ⏳ TODO |
| Thanh toán hoá đơn | ⏳ TODO |
| Lịch sử hoá đơn | ⏳ TODO |

---

## Duplicates cần xóa qua Stitch UI

| ID | Title |
|----|-------|
| `41981d7359af4d4aad21df990f5f5013` | Đăng nhập (dup Login) |
| `a86ad05d243844a985f523846186b8f2` | Chọn phòng khám (dup) |
| `d4b0df56a11a4f2f98f42e3db7447e1f` | Quên mật khẩu (dup) |
| `86af5f70e0ee469e8526af820099a452` | Dashboard Lễ tân (dup) |
| `57e68927eb124c26ac88b82226dcfe0d` | Dashboard Lễ tân Refined (dup) |
| `c9f832eebed6458e84be9c5cc8e1548f` | Dashboard Lễ tân (dup) |
| `f90c935ebb2e4f23a58b7084d8116d06` | Dashboard Điều dưỡng (dup) |
| `1dbefdf9b9894aa08e61898ba27f79c4` | Dashboard Bác sĩ (dup) |

---

## Hướng dẫn tiếp tục (session mới)

1. Xóa 8 duplicates trên Stitch UI
2. Chờ 10-15 phút (rate-limit reset)
3. Nhắn Claude: "tiếp tục generate v2.0, project 18324036454103633899, design system assets/144349522488444424, bắt đầu từ Dashboard Dược sĩ"

**Quy tắc generate:**
- Dùng GEMINI_3_FLASH cho TẤT CẢ screens phức tạp (dashboard, table, form)
- Sau TIMEOUT → check list_screens ngay, KHÔNG retry nếu screen đã xuất hiện
- Prompt dưới 15 dòng, súc tích
- Width: ghi "1920px" trong prompt (Stitch không có param width)
