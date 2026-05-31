---
task: TASK-039b
title: "Functional Design — MediZen Component Restyle (Button + Input + Card + Modal + Toast + Badge + Tooltip + Popover + Tabs + Avatar)"
date: 2026-05-01
status: DONE
language: Vietnamese
---

# Thiết kế chức năng — MediZen Component Restyle

**Task**: TASK-039b  
**Ngày hoàn thành**: 2026-05-01  
**Trạng thái**: DONE (670/670 tests pass)  
**Chi nhánh**: `feature/task-039b-component-restyle`

---

## Mục đích

TASK-039 đã chuyển đổi design tokens (màu sắc, font chữ, độ bo tròn) sang MediZen. TASK-039 F.11 hoãn kiểm toán + restyle các component primitives (Button/Input/Card/Modal/Toast/Badge/Tooltip/Popover/Tabs/Avatar) thành task riêng — đây chính là task này.

Mục tiêu: restyle 9 component UI cơ sở với các variant MediZen, duy trì tương thích ngược (backward-compat) với 6+ trang admin hiện tại.

---

## Phạm vi

### Thành phần được restyle (11 file)

#### Cập nhật (2)

| Component | File | Thay đổi |
|-----------|------|---------|
| **Button** | `src/components/ui/button.tsx` | Thêm variant: `primary`, `secondary`, `danger`, `ghost`, `outline`. Thêm size: `sm` (h-8), `md` (h-10), `lg` (h-12). Hỗ trợ `iconLeading`/`iconTrailing`. Giữ variant cũ (`default`, `destructive`, `link`) để tương thích |
| **Input** | `src/components/ui/input.tsx` | Thêm size (`sm/md/lg`), state (`error/success/disabled`), `helperText`/`errorMessage` props. Thêm component `FormField` với label + dấu sao đỏ required. Wrapping có điều kiện: nếu không có `helperText`/`errorMessage`, trả về `<input>` bare |

#### Mới (9)

| Component | File | Mô tả |
|-----------|------|-------|
| **Select** | `src/components/ui/select.tsx` | Radix Select với size sm/md/lg, state error/success, dark mode parity |
| **Textarea** | `src/components/ui/textarea.tsx` | Tương tự Input: size + state + helper/error text |
| **Card** | `src/components/ui/card.tsx` | Card + CardHeader + CardTitle + CardDescription + CardContent + CardFooter. Hỗ trợ `hoverable` (hover:shadow-md) |
| **Dialog** | `src/components/ui/dialog.tsx` | Cập nhật: khôi phục `p-6` padding trên DialogContent (tương thích ngược). Thêm DialogBody slot. Header/Footer optional borders (opt-in) |
| **Toast** | `src/components/ui/toast.tsx` | 4 variant (success/info/warning/error). Hook `useToast` + Provider `Toaster`. Auto-dismiss 5000ms. Viewport bottom-right |
| **Badge** | `src/components/ui/badge.tsx` | 6 màu filled + 6 outlined, 3 size (xs/sm/md) |
| **Tooltip** | `src/components/ui/tooltip.tsx` | Radix Tooltip, bg-slate-900, mũi tên, z-50 |
| **Popover** | `src/components/ui/popover.tsx` | Lightweight controlled (không dùng Radix Popover vì không trong deps). Toggle mở/đóng, ESC + outside-click close. `role="region"` + `aria-label` |
| **Tabs** | `src/components/ui/tabs.tsx` | Controlled + uncontrolled modes. Indigo active border (border-b-2 border-indigo-500). Tab role + aria-selected |
| **Avatar** | `src/components/ui/avatar.tsx` | Radix Avatar, 4 size (xs/sm/md/lg), fallback initials, status dot (online/offline/busy) |

---

## Chi tiết theo component

### Button

**Variant**:
- `primary`: bg-indigo-500, text-white, hover:bg-indigo-600 (default)
- `secondary`: bg-slate-100, text-slate-900, hover:bg-slate-200
- `danger`: bg-red-500, text-white, hover:bg-red-600
- `ghost`: bg-transparent, text-slate-700, hover:bg-slate-100
- `outline`: border border-slate-300, text-slate-900, hover:bg-slate-50
- *Legacy*: `default` → primary; `destructive` → danger; `link` giữ nguyên

**Size**:
- `sm`: h-8, px-3, text-sm
- `md`: h-10, px-4, text-base (default)
- `lg`: h-12, px-6, text-lg
- `icon`: square, padding equal, cho icon-only buttons

**Props**:
- `iconLeading`, `iconTrailing`: React.ReactNode
- `asChild`: forwarded to Slot (guard để không duplicate icon khi asChild=true)
- Focus visible: ring-indigo-500, ring-offset-2

**Dark mode**:
- Primary: dark:bg-indigo-600 → dark:bg-indigo-700 on hover
- Secondary: dark:bg-slate-800, dark:text-slate-100
- Danger: dark:bg-red-600 → dark:bg-red-700 on hover
- Ghost: dark:text-slate-300, dark:hover:bg-slate-800
- Outline: dark:border-slate-600, dark:text-slate-100, dark:hover:bg-slate-900

---

### Input

**State**:
- `default`: border-slate-300, focus:border-indigo-500, focus:ring-indigo-500
- `error`: border-red-500, focus:border-red-500, focus:ring-red-200
- `success`: border-emerald-500, focus:border-emerald-500, focus:ring-emerald-200

**Size**:
- `sm`: h-8, px-3, text-sm
- `md`: h-10, px-3, text-base (default)
- `lg`: h-12, px-4, text-lg

**Props**:
- `inputSize?: "sm" | "md" | "lg"`
- `state?: "default" | "error" | "success" | "disabled"`
- `helperText?: string` — mẹo phía dưới input (slate-600)
- `errorMessage?: string` — lỗi phía dưới, màu đỏ; tự động set `state="error"`
- `disabled?: boolean`

**Wrapping logic** (CRITICAL FIX):
- Nếu **không** có `helperText` hay `errorMessage`: return bare `<input>` (tương thích 100%)
- Nếu **có**: wrap trong `<div class="flex flex-col gap-1">` với text bên dưới

**Component FormField**:
```tsx
<FormField required={true} label="Email" htmlFor="email-input" />
<Input id="email-input" type="email" />
```
- `label`: string
- `required?: boolean` → "*" đỏ
- `htmlFor`: id của input

**Dark mode**: dark:bg-slate-900, dark:border-slate-700, dark:text-white, dark:placeholder:text-slate-500

---

### Select

**Size**: sm/md/lg (tương tự Input)

**State**: error/success/disabled (border color + ring color khác nhau)

**Props**:
```tsx
<Select value={value} onValueChange={setValue} disabled={false} size="md" state="default">
  <SelectTrigger>Choose...</SelectTrigger>
  <SelectContent>
    <SelectItem value="a">Option A</SelectItem>
  </SelectContent>
</Select>
```

**Dark mode**: dark:bg-slate-900, dark:border-slate-700

---

### Textarea

**Tương tự Input**:
- `inputSize` (sm/md/lg)
- `state` (default/error/success)
- `helperText`, `errorMessage`
- `rows` (default: 4)

**Dark mode**: dark:bg-slate-900, dark:border-slate-700

---

### Card

**Props**:
```tsx
<Card hoverable>
  <CardHeader>
    <CardTitle>Tiêu đề</CardTitle>
    <CardDescription>Mô tả</CardDescription>
  </CardHeader>
  <CardContent>Nội dung</CardContent>
  <CardFooter>Footer</CardFooter>
</Card>
```

**Styling**:
- `Card`: bg-white, border border-slate-200, rounded-xl, shadow-sm
- `hoverable`: hover:shadow-md (transition smooth)
- `CardHeader`: border-b border-slate-200, px-6, py-4 (nếu có HeaderBorder)
- `CardTitle`: text-lg, font-semibold
- `CardDescription`: text-sm, text-slate-600
- `CardContent`: px-6, py-4
- `CardFooter`: border-t border-slate-200, px-6, py-4, flex justify-end gap-2

**Dark mode**: dark:bg-slate-900, dark:border-slate-700, dark:text-slate-100

---

### Dialog (Modal)

**Fix tương thích ngược (critical)**:
- `DialogContent`: **restored** `p-6` as default padding (nguyên ban đầu)
  - Các trang admin hiện tại (UsersPage, VitalsPage, v.v.) đặt `<form>` trực tiếp vào DialogContent → giữ padding cũ
  - Nếu muốn dùng structured slots (DialogHeader + DialogBody + DialogFooter), pass `className="p-0"` trên DialogContent để tránh double-padding
  
- `DialogHeader`: `mb-4` (margin-bottom, không border/padding) — giữ cũ
- `DialogBody`: **NEW** slot cho nội dung (optional, `p-6` nếu muốn structured layout)
- `DialogFooter`: `mt-6 flex justify-end gap-2` — giữ cũ, optional border-t/bg-slate-50

**New JSDoc**: tài liệu hai cách sử dụng:
1. Legacy: `<DialogContent p-6><form>...</form></DialogContent>`
2. Structured: `<DialogContent p-0><DialogHeader>...</DialogHeader><DialogBody>...</DialogBody><DialogFooter>...</DialogFooter></DialogContent>`

**a11y**:
- Close button: `aria-label="Close dialog"`
- Focus trap: Radix Dialog (built-in)
- Esc key: close (Radix)

**Dark mode**: dark:bg-slate-900, dark:border-slate-700

---

### Toast

**Component**:
```tsx
// Setup App root:
<ToastContextProvider>
  <YourApp />
  <Toaster />
</ToastContextProvider>

// Usage:
const { toast } = useToast();
toast({
  title: "Thành công",
  description: "Lưu thành công",
  variant: "success"
});
```

**Variant**:
- `success`: bg-emerald-50, border-emerald-300, text-emerald-900
- `info`: bg-blue-50, border-blue-300, text-blue-900
- `warning`: bg-yellow-50, border-yellow-300, text-yellow-900
- `error`: bg-red-50, border-red-300, text-red-900

**Props**:
- `title`: string
- `description?: string`
- `duration?: number` (default 5000ms)
- `variant?: "success" | "info" | "warning" | "error"` (default: "success")

**Viewport**: bottom-4 right-4, stack từ dưới lên

**a11y**: aria-live="polite" (Radix Toast built-in)

**Dark mode**: dark:bg-{color}-900/20, dark:border-{color}-800, dark:text-{color}-200

---

### Badge

**Variant** (filled + outlined):
- `primary`: bg-indigo-100, text-indigo-900
- `secondary`: bg-slate-100, text-slate-900
- `success`: bg-emerald-100, text-emerald-900
- `warning`: bg-yellow-100, text-yellow-900
- `danger`: bg-red-100, text-red-900
- `neutral`: bg-gray-100, text-gray-900

**Outlined**:
- `primary-outlined`: border border-indigo-500, text-indigo-700
- (+ tương tự cho secondary/success/warning/danger/neutral)

**Size**:
- `xs`: px-2, py-0.5, text-xs
- `sm`: px-2.5, py-1, text-sm (default)
- `md`: px-3, py-1.5, text-base

**Styling**: rounded-md (6px)

**Dark mode**: dark:bg-{color}-900/40, dark:text-{color}-200 (for filled); dark:border-{color}-600 (for outlined)

---

### Tooltip

**Component**:
```tsx
<Tooltip>
  <TooltipTrigger asChild>
    <button>Hover me</button>
  </TooltipTrigger>
  <TooltipContent>Tooltip text</TooltipContent>
</Tooltip>
```

**Styling**:
- Content: bg-slate-900, text-white, rounded-md, px-3 py-2, text-sm
- Arrow: 4px, slate-900
- z-index: z-50

**Props**:
- `delayDuration?: number` (default 200ms)
- `side?: "top" | "right" | "bottom" | "left"`

**Dark mode**: bg-slate-900 (intentionally same light + dark)

---

### Popover

**Component**:
```tsx
const [open, setOpen] = useState(false);
<Popover open={open} onOpenChange={setOpen}>
  <PopoverTrigger asChild>
    <button>Click</button>
  </PopoverTrigger>
  <PopoverContent>
    Popover content
  </PopoverContent>
</Popover>
```

**Impl**: lightweight controlled (không dùng Radix Popover vì không trong deps)

**Props**:
- `open?: boolean`
- `onOpenChange?: (open: boolean) => void`
- ESC key: close
- Outside click: close

**a11y**:
- Content div: `role="region"` + `aria-label="Popover"` (giữ tương thích region labelling)

**Note**: Nếu cần Radix Popover đầy đủ sau này, migration path ~10 dòng code.

---

### Tabs

**Component**:
```tsx
// Controlled:
const [value, setValue] = useState("tab1");
<Tabs value={value} onValueChange={setValue}>
  <TabsList>
    <TabsTrigger value="tab1">Tab 1</TabsTrigger>
    <TabsTrigger value="tab2">Tab 2</TabsTrigger>
  </TabsList>
  <TabsContent value="tab1">Content 1</TabsContent>
  <TabsContent value="tab2">Content 2</TabsContent>
</Tabs>

// Uncontrolled:
<Tabs defaultValue="tab1">
  ...
</Tabs>
```

**Styling**:
- `TabsList`: flex gap-1, bg-slate-100, rounded-lg, p-1
- `TabsTrigger`: px-3 py-2, text-slate-700, hover:bg-slate-200, active: border-b-2 border-indigo-500, text-indigo-700
- `TabsContent`: pt-4

**a11y**: role=tablist/tab/tabpanel, aria-selected, tabIndex management (Radix)

**Dark mode**: dark:bg-slate-800, dark:text-slate-300, dark:hover:bg-slate-700, dark:border-indigo-400

---

### Avatar

**Component**:
```tsx
<Avatar size="md" status="online">
  <AvatarImage src="..." alt="..." />
  <AvatarFallback>JD</AvatarFallback>
</Avatar>
```

**Size**:
- `xs`: w-6 h-6
- `sm`: w-8 h-8
- `md`: w-10 h-10 (default)
- `lg`: w-12 h-12

**Styling**:
- Image: rounded-full, object-cover
- Fallback: bg-indigo-100, text-indigo-900, flex items-center justify-center, font-semibold

**Status dot** (optional):
- Position: absolute bottom-0 right-0
- Size: w-3 h-3
- Color:
  - `online`: bg-emerald-500
  - `offline`: bg-slate-400
  - `busy`: bg-red-500
- Border: 2px white ring

**Props**:
- `size?: "xs" | "sm" | "md" | "lg"`
- `status?: "online" | "offline" | "busy"`

**a11y**: Status dot aria-label (e.g., "Status: online")

**Dark mode**: dark:bg-indigo-900/40, dark:text-indigo-300, dark:ring-slate-900

---

## Chiến lược tương thích ngược (Backward-compat)

### Button ✅
- Variant cũ (`default`, `destructive`, `link`) mapped sang indigo/red, giữ nguyên
- Tất cả callsite hiện tại compile & render y như cũ

### Input ✅ (with conditional wrapping fix)
- Bare khi không có helper/error (100% tương thích)
- Wrapped khi có (non-breaking vì wrapper là flex parent)
- Tất cả `className` forward đến inner `<input>`

### Dialog ⚠️ → ✅ (FIXED)
- DialogContent restored `p-6` (cũ)
- DialogHeader/Footer giữ margin-only style (cũ)
- 6 admin page không cần migrated

### Select, Textarea, Card, Toast, Badge, Tooltip, Popover, Tabs, Avatar
- Net-new files, zero existing imports
- Zero risk

---

## Kiểm chứng a11y

| Item | Status | Ghi chú |
|------|--------|---------|
| Modal close button aria-label | ✅ | "Close dialog" |
| Toast aria-live | ✅ | Radix built-in "polite" |
| Toast dismiss aria-label | ✅ | "Dismiss notification" |
| Toast viewport | ✅ | bottom-4 right-4 |
| Tabs role + aria-selected | ✅ | Radix managed |
| Avatar status dot aria-label | ✅ | "Status: online/offline/busy" |
| Button icon-only (size=icon) | ⚠️ | Caller must use aria-label (not enforced) |
| Popover role + aria-label | ✅ | role="region" + aria-label="Popover" (post-fix) |
| Button focus-visible | ✅ | ring-indigo-500, ring-offset-2 |

---

## Dark mode parity

✅ Tất cả component có `dark:*` counterpart:
- Color tokens: dark variant per color palette
- Background: dark:bg-slate-900, dark:bg-slate-800
- Border: dark:border-slate-700
- Text: dark:text-slate-100, dark:text-slate-300
- Focus ring: dark:ring-indigo-400

---

## Test coverage

| Metric | Value |
|--------|-------|
| Baseline (trước task) | 547 tests |
| New (task này) | 123 tests |
| **Total** | **670 tests** |
| **Status** | **✅ 670/670 PASS** |

### Per-component:
- `button-variants.test.tsx`: 20 tests (primary/secondary/danger/ghost/outline + sizes + disabled + icon)
- `input-states.test.tsx`: 24 tests (error/success/disabled + sizes + helper/error text + wrapping logic)
- `card.test.tsx`: 13 tests (hoverable + slots)
- `modal.test.tsx`: 9 tests (dialog padding p-6 default + DialogBody + focus trap)
- `toast.test.tsx`: 14 tests (variants + auto-dismiss + close)
- `badge.test.tsx`: 18 tests (6 filled + 6 outlined + sizes)
- `tabs.test.tsx`: 12 tests (controlled + uncontrolled + active state)
- `avatar.test.tsx`: 13 tests (sizes + initials + status dot)

---

## Quyết định hoãn lại (Deferred)

1. **Radix Popover full integration**: Hiện tại là lightweight controlled. Nếu cần Radix, migration path rõ ràng (~10 dòng).
2. **Storybook examples**: Storybook không configured → skip.
3. **Button aria-label enforcement**: Icon-only buttons giữ convention (caller's responsibility).

---

## Điểm liên kết chéo (Cross-task)

- **TASK-040 PatientDetail**: Sử dụng Card/Modal nặng → kiểm chứng backward-compat ✅
- **TASK-046 Bảo mật**: Sử dụng Toast/Modal → kiểm chứng backward-compat ✅
- **Trang admin hiện tại**: UsersPage, VitalsPage, ServicesPage, MedicinesPage, RolesPage → Dialog padding fix ✅

---

## Lịch sử hoàn thành

- **2026-05-01**: Implementation → Code Review (CHANGES_REQUESTED cho Dialog padding + Input wrapping)
- **2026-05-01**: Code Review → Fix applied (Dialog p-6 restored, Input conditional wrapping, Popover JSDoc/a11y)
- **2026-05-01**: Fix verified (670/670 tests, 0 TS/lint errors, build PASS)
- **2026-05-01**: Functional design finalized, task status → **DONE**

---

## Kết luận

TASK-039b restyle thành công 11 UI component (9 mới, 2 cập nhật) với MediZen variants. Tất cả 670 unit test pass. Tương thích ngược duy trì bằng cách:
1. Button: legacy variant preserved
2. Input: conditional wrapping (bare nếu không có helper/error)
3. Dialog: p-6 padding restored (additive DialogBody)
4. Tất cả component mới: zero existing imports

Dark mode parity kiểm chứng trên tất cả variant. a11y labels đầy đủ. Sẵn sàng tích hợp vào TASK-040/046 mà không lo regression.

**Status**: ✅ **DONE**
