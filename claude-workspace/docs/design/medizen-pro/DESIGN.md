# MediZen Pro — Design System (Teal Medical Premium)

A modern, professional, role-aware EMR/clinic-management UI for Vietnamese clinics
(brand "MediZen"). Desktop-first (≥1440px). Calm, clinical, spacious, high-legibility.
All copy is Vietnamese. This document is the single source of truth for the design system.

---

## 1. Brand & mood

- **Tone:** clinical premium — calm, trustworthy, modern, uncluttered. Generous whitespace,
  large legible type, soft shadows, rounded surfaces. NOT dense/cramped, NOT flashy.
- **Primary brand color:** Teal (medical, fresh, professional).
- **Surfaces:** light slate background with white cards; subtle borders and soft shadows.

## 2. Color tokens

### Primary — Teal
| Token | Hex | Use |
|---|---|---|
| primary-50 | #F0FDFA | tinted section header bg, hover wash |
| primary-100 | #CCFBF1 | chips, light fills |
| primary-500 | #14B8A6 | accents, icons |
| **primary-600** | **#0D9488** | **primary action / buttons / active nav / focus ring** |
| primary-700 | #0F766E | button hover/active, links |
| primary-900 | #134E4A | deep accents |

### Neutral — Slate
| Token | Hex | Use |
|---|---|---|
| bg | #F8FAFC | page background (slate-50) |
| surface | #FFFFFF | cards, inputs |
| border | #E2E8F0 | card/input borders (slate-200) |
| text | #1E293B | body text (slate-800) |
| heading | #0F172A | headings (slate-900) |
| muted | #64748B | secondary text, hints (slate-500) |
| disabled | #94A3B8 | disabled text (slate-400) |

### Semantic
| Token | Hex | Use |
|---|---|---|
| success | #10B981 | OK, paid, in-stock (emerald) |
| warning | #F59E0B | low-stock, pending (amber) |
| danger | #E11D48 | errors, delete, emergency (rose) |
| info | #0EA5E9 | info banners (sky) |

### Dark mode (optional)
bg #0F172A · surface #1E293B · border #334155 · text #F1F5F9 · muted #94A3B8 ·
brand accent #2DD4BF (teal-400 for contrast).

## 3. Typography

- **Heading font:** "Sora" (700 bold, 600 semibold). Geometric, modern, professional.
- **Body font:** "Inter" (400 regular, 500 medium). High legibility for Vietnamese diacritics.
- **Numbers / clinical data / money:** use tabular-nums.

| Role | Size / Line | Weight | Font |
|---|---|---|---|
| Display / Page H1 | 30px / 38px | 700 | Sora |
| Section H2 | 24px / 32px | 700 | Sora |
| Card title H3 | 19px / 28px | 600 | Sora |
| **Body (base)** | **15px / 24px** | 400 | Inter |
| Body strong | 15px / 24px | 500 | Inter |
| Small / hint | 13px / 20px | 400 | Inter |
| Field label | 14px / 20px | 500 | Inter |
| Section label (eyebrow) | 12px / 16px | 600, uppercase, letter-spacing 0.06em | Inter |

Base font size is **15px** (larger than typical 14px for a more spacious, readable feel).

## 4. Spacing, radius, elevation

- **Spacing scale (4px base):** 4, 8, 12, 16, 20, 24, 32, 40, 48.
- **Field vertical gap:** 20px. **Section gap:** 32px. **Page gutter:** 32px.
- **Radius:** cards 16px · inputs/buttons 10px · chips/badges 8px · pills/full for toggles.
- **Shadow:** cards use `shadow-sm` + `ring-1 ring-slate-900/5`. Modals/popovers `shadow-lg`.
- **Card padding:** 24–28px.

## 5. Components

### Inputs (text, number, date, select, textarea)
- Height **44px** (textarea min 88px). Horizontal padding 14px. Font 15px.
- Border 1px slate-200, radius 10px, white bg.
- Focus: 2px ring primary-600 (`ring-2 ring-teal-600`), border transparent.
- Disabled: slate-50 bg, slate-400 text.
- Error state: border + 2px ring danger (rose), error message 13px rose below field.
- Placeholder: slate-400.

### Field
Label (14px/500, with red `*` if required) → control → optional hint (13px muted) /
error (13px rose). Vertical stack, gap 6px.

### Buttons (height 44px default, 36px small, 52px large; radius 10px; font 15px/500)
- **Primary:** bg primary-600, white text, hover primary-700.
- **Secondary:** white bg, slate-200 border, slate-800 text, hover slate-50.
- **Ghost:** transparent, hover slate-100.
- **Destructive:** bg danger (rose), white text.
- Icon + label allowed; icon-only is 44×44 square.

### Cards / Form sections
White card, radius 16px, border slate-200, shadow-sm, padding 24–28px.
Header row: small primary-tinted icon chip (teal-50 bg + teal-600 icon) + H3 title +
optional eyebrow/section label. Body below with field grid.

### Segmented control (e.g., gender)
Pill group, slate-100 track, active segment = white pill + shadow-sm + primary-700 text.
Used for small mutually-exclusive choices instead of a dropdown.

### Switch / toggle
Pill switch, off = slate-300, on = primary-600. Used for feature toggles (e.g., BHYT).

### Chips / badges
Radius 8px, 13px. Status colors: in-stock = emerald, low = amber, out = rose,
neutral = slate. e.g. "Còn 240 viên" (emerald), "Sắp hết" (amber), "Hết hàng" (rose).

### Sticky form actions
Bottom action bar sticky to viewport: white bg, top border slate-200, right-aligned
[Huỷ] secondary + [Lưu] primary. Stays visible while form scrolls.

## 6. Form layout (desktop)

- Forms are **wide**: content max-width ~1100–1200px (NOT a narrow single column).
- 12-column grid. Group related fields 2-up or 3-up:
  - Họ tên: full width.
  - Giới tính (segmented) + Ngày sinh / Năm sinh: same row.
  - Số điện thoại + Email: same row.
  - Địa chỉ: full width; Tỉnh / Quận-Huyện / Phường-Xã: 3-up row.
- Split the form into clear cards: e.g. "Thông tin bắt buộc" and "Thông tin bổ sung".
- Long forms: optional left sticky section nav + sticky bottom action bar.

## 7. Iconography & misc

- Icon set: Lucide (outline, 1.75px stroke), 20px default, in teal-600 for section icons.
- Avatars: rounded-full, slate-100 bg, initials in slate-600.
- Empty states: centered icon + muted text + primary action.
- Tables: sticky header, row hover slate-50, zebra optional, tabular-nums for numeric cols.

## 8. Vietnamese clinic specifics

- BHYT (bảo hiểm y tế) fields appear only when the BHYT feature toggle is ON.
- Money in VND with thousands separators and tabular-nums (e.g. 1.250.000 ₫).
- Emergency (cấp cứu) uses danger/rose emphasis (red queue badge, fast-track).
