# Thiết Kế Chi Tiết Tính Năng: In Đơn Thuốc & Cấu Hình Mẫu In

**Dự án:** Clinic CMS  
**Task:** TASK-094  
**Phiên bản:** 1.0  
**Ngày:** 2026-07-22  
**Người thực hiện:** Implementation + Test Agent  
**Trạng thái:** Đã duyệt & Kiểm thử xong  
**Tài liệu liên quan:** Implementation-plan: `docs/tasks/TASK-094/refs/implementation-plan.md`, Test Report: `docs/tasks/TASK-094/deliveries/test-reports/test-report.md`

---

## Lịch sử thay đổi

| Phiên bản | Ngày | Nội dung thay đổi |
|-----------|------|-------------------|
| 1.0 | 2026-07-22 | Phiên bản hoàn tất sau kiểm thử và fix bug |

---

## Mục lục

- [1. Tổng quan tính năng](#1-tổng-quan-tính-năng)
- [2. Luồng xử lý tổng thể](#2-luồng-xử-lý-tổng-thể)
- [3. Các tính năng chi tiết](#3-các-tính-năng-chi-tiết)
- [4. Danh sách API](#4-danh-sách-api)
- [5. Cấu trúc cơ sở dữ liệu](#5-cấu-trúc-cơ-sở-dữ-liệu)
- [6. Quy tắc nghiệp vụ](#6-quy-tắc-nghiệp-vụ)
- [7. Xử lý lỗi](#7-xử-lý-lỗi)
- [8. Ghi chú và lưu ý khi kiểm thử](#8-ghi-chú-và-lưu-ý-khi-kiểm-thử)

---

## 1. Tổng quan tính năng

### 1.1 Mục đích

Sửa chữa và cải thiện hệ thống in đơn thuốc, in phiếu khám với:
- In chẩn đoán chính xác từ dữ liệu được lưu (`visit.diagnosis`), không phải ghi chú
- Sử dụng mẫu in mặc định của phòng khám trong toàn bộ luồng in (doctor, billing, exam)
- Cho phép bác sĩ định cấu hình hiển thị/ẩn từng trường trên mẫu in
- Thêm trường "cách dùng" (usage instruction) có gợi ý nhưng vẫn cho nhập tự do
- Thống nhất đơn vị liều theo dạng thuốc (dosage form) thay vì toàn bộ tự do

### 1.2 Phạm vi

**Bao gồm 5 tính năng/sửa lỗi:**
1. **A. In chẩn đoán chính xác:** đọc từ `visit.diagnosis` trên 4 luồng in (doctor, billing, exam, visit-detail)
2. **B. Mẫu in mặc định cho doctor print:** doctor consultation "In đơn thuốc" dùng mẫu mặc định của phòng khám giống billing path
3. **C. Ẩn/hiện từng trường trên mẫu in:** flag `hidden` trên `LayoutElement`
4. **D. Cách dùng (usage instruction):** trường string với dropdown gợi ý (trước ăn/sau ăn/…) nhưng cho nhập tự do
5. **E. Đơn vị liều theo dạng thuốc:** cột `DosageForm.unit` mới, resolve medicine → dosage_form → unit

**Không bao gồm:**
- Sửa endpoint legacy `/api/v1/prescriptions/{id}/print` (stale/unused)
- Template read access cho `cashier` role (deliberate scope decision — xem Phần 8.2)

### 1.3 Các bên liên quan

| Vai trò | Mô tả |
|---------|-------|
| **Bác sĩ (doctor)** | Kê đơn thuốc, in đơn, in phiếu khám từ bệnh nhân đang khám |
| **Admin** | Thiết kế mẫu in, cấu hình mẫu mặc định, quản lý mẫu |
| **Dược sĩ (pharmacist)** | Xem đơn thuốc được in |
| **Lễ tân (cashier)** | In đơn thuốc khi thanh toán (hạn chế — xem Phần 8.2) |

---

## 2. Luồng xử lý tổng thể

### 2.1 Sơ đồ luồng in đơn thuốc

```
┌─────────────────────────┐
│  Bác sĩ khám bệnh       │
│  → Kê đơn thuốc         │
│  → Nhấn "In đơn thuốc"  │
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│ GET /print-templates?type=prescription  │
│ (quyền: prescription.print)             │
│ Tìm mẫu mặc định (is_default && !is_system → is_default → NULL)
└────────────┬────────────────────────────┘
             │
        ┌────┴────┐
        │          │
        ▼          ▼
  (Có mẫu)    (Không có)
    │           │
    │           └─► Dùng PrintablePrescription (built-in)
    │
    └─► Dùng TemplateRenderer (custom mẫu)
        │
        └─► Lọc trường hidden (hidden === true)
            │
            └─► In ra
```

### 2.2 Mô tả các bước chính (5 tính năng)

#### Tính năng A: Chẩn đoán in đúng

| Bước | Tên bước | Mô tả chi tiết |
|------|---------|----------------|
| 1 | Bác sĩ nhập chẩn đoán | Trên tab "Khám" → "Chẩn đoán" → nhập/chọn → lưu → `visit.diagnosis` |
| 2 | Mở phiếu in | Doctor: "In đơn thuốc" / "In phiếu khám"; Billing/VisitDetail: "In" |
| 3 | Modal in đọc `visit.diagnosis` | **Sửa lỗi:** đọc từ `visit.diagnosis` (không phải `visit.notes` hay `visit.chief_complaint`) |
| 4 | Render chẩn đoán | Trên custom template: field `visit.diagnosis`; trên built-in: fixed position |
| 5 | In ra | Giấy in hiển thị chẩn đoán chính xác |

#### Tính năng B: Mẫu in mặc định cho doctor print

| Bước | Tên bước | Mô tả chi tiết |
|------|---------|----------------|
| 1 | Admin cấu hình | `/admin/print-templates` → thiết kế template → chọn "Mặc định" → `is_default=true, is_system=false` |
| 2 | Bác sĩ in đơn | "Kê đơn" tab → "In đơn thuốc" |
| 3 | FE gọi API | `GET /print-templates?template_type=prescription` (quyền: `prescription.print`) |
| 4 | FE chọn template | `selectDefaultTemplate(templates, 'prescription')` → tìm `is_default && !is_system` → `is_default` → `null` |
| 5 | Render | Nếu tìm được: `TemplateRenderer` (custom); không: `PrintablePrescription` (built-in) |
| 6 | In ra | Dùng đúng mẫu |

#### Tính năng C: Ẩn/hiện từng trường

| Bước | Tên bước | Mô tả chi tiết |
|------|---------|----------------|
| 1 | Admin mở template builder | `/admin/print-templates` → chọn template → "Edit" |
| 2 | Chọn trường trên canvas | Kéo thả trường (e.g. "Chẩn đoán:") onto canvas |
| 3 | Toggle ẩn/hiện | Trên properties panel: checkbox "Hiển thị trên bản in" |
| 4 | Lưu | PATCH `/api/v1/print-templates/{id}` với `{"layout":[...{"id":"dg-19","hidden":true},...]}` |
| 5 | Render | `TemplateRenderer` lọc: `elements.filter(el => !el.hidden)` |
| 6 | In ra | Trường ẩn không xuất hiện; trường hiện bình thường |

#### Tính năng D: Cách dùng (Usage Instruction)

| Bước | Tên bước | Mô tả chi tiết |
|------|---------|----------------|
| 1 | Bác sĩ chọn/nhập cách dùng | "Kê đơn" tab → chọn medicine → dropdown suggestions (uống trước ăn/sau ăn/…) hoặc nhập tự do |
| 2 | Lưu | POST/PATCH `/api/v1/prescriptions/{id}/items` → `usage_instruction: "Uống sau ăn"` |
| 3 | Tải lại | Sửa đơn → field `usage_instruction` refill |
| 4 | In ra | Template field `prescription.usage_instruction` → in trên giấy |

#### Tính năng E: Đơn vị liều theo dạng thuốc

| Bước | Tên bước | Mô tả chi tiết |
|------|---------|----------------|
| 1 | Admin cấu hình dạng thuốc | `/admin/dosage-forms` → chọn form (e.g. Injection) → nhập "Đơn vị" (e.g. "ống") → lưu → `dosage_form.unit = "ống"` |
| 2 | Bác sĩ chọn thuốc | Medicine search → chọn injection (e.g. Dexamethasone inj) |
| 3 | FE resolve unit | `dosage_form_unit = medicine.dosage_form.unit` (fallback: `medicine.base_unit`) → pre-fill field |
| 4 | Bác sĩ có thể sửa | Field vẫn editable |
| 5 | Lưu đơn | `prescription_item.unit = "ống"` (user-set hoặc resolved) |
| 6 | In ra | "1 ống" (unit + quantity) |

---

## 3. Các tính năng chi tiết

### 3.1 Tính năng A: In chẩn đoán chính xác

**Mục đích:** Đảm bảo mỗi lần in (doctor, billing, exam, visit-detail) đều in **chẩn đoán chính xác** từ `visit.diagnosis`, không lỗi source.

**Quy tắc:**
- Luôn đọc từ `visit.diagnosis` khi khác `null/undefined`
- Fallback: `visit.chief_complaint` (chỉ nếu diagnosis trống)
- Không bao giờ dùng `visit.notes` (ghi chú tự do, không phải chẩn đoán chính thức)

**Danh sách 4 luồng:**

| Luồng | Tệp FE | Dòng cũ | Dòng mới | Quyền |
|-------|--------|--------|---------|-------|
| 1. Billing/Visit-Detail modal | `src/components/billing/PrintPrescriptionModal.tsx` | `visit?.notes` | `visit?.diagnosis \|\| visit?.chief_complaint \|\| ""` | `settings.clinic` (read) |
| 2. Exam form modal | `src/components/doctor/PrintExamFormModal.tsx` | `visit.notes` | `visit.diagnosis ?? ""` | `settings.clinic` (read) |
| 3. Doctor prescription print | `src/components/doctor/PrescriptionTab.tsx` | (omitted) | `diagnosis: visit.diagnosis` → pass to `VisitInfo` | `prescription.print` (read) |
| 4. Visit detail page | `src/pages/visits/VisitDetailPage.tsx` | (omitted) | `diagnosis: visit.diagnosis` → pass through | `settings.clinic` (read) |

**Test result:** ✅ Verified live — tất cả 4 luồng in diagnosis chính xác (test data: chẩn đoán được kê = chẩn đoán in ra).

---

### 3.2 Tính năng B: Mẫu in mặc định cho doctor print

**Mục đích:** Doctor consultation "In đơn thuốc" cũng dùng mẫu mặc định của phòng khám (parity với billing path), không bị buộc dùng built-in fallback.

**Quy tắc chọn template:**
```
selectDefaultTemplate(templates: PrintTemplate[], type: TemplateType) {
  // 1. Ưu tiên: is_default=true && is_system=false (custom default)
  let found = templates.find(t => t.is_default && !t.is_system);
  if (found) return found;
  
  // 2. Fallback: is_default=true (system default)
  found = templates.find(t => t.is_default);
  if (found) return found;
  
  // 3. Không có → null (caller sẽ dùng built-in)
  return null;
}
```

**Danh sách 2 modals cùng dùng logic này:**

| Modal | Tệp FE | Hành động nếu không có template |
|-------|--------|------------------------------|
| Doctor prescription | `src/components/doctor/PrintPrescriptionModal.tsx` | Fallback `PrintablePrescription` (built-in) |
| Billing/Visit-detail | `src/components/billing/PrintPrescriptionModal.tsx` | Fallback `PrintablePrescription` (built-in) |

**Exam form modal:** Nếu không có default → hiển thị "Chưa có mẫu mặc định" + disable print button (không có fallback).

**API permission change:**
- Read: `GET /print-templates` + `GET /print-templates/{id}` → quyền **`prescription.print`** (là `doctor`, `nurse`, `pharmacist`, `admin`)
- Write: `POST`, `PATCH`, `DELETE`, `duplicate` → quyền **`settings.clinic`** (chỉ `admin`)
- Trước: cả đọc/ghi dùng `settings.clinic` (doctor không thể đọc)

**Test result:** ✅ Verified live as `dr_nguyen` — "In đơn thuốc" giờ render custom default template (A4 khổ giấy, "Mã BN:/Mã phiếu:…" layout), không fallback built-in.

---

### 3.3 Tính năng C: Ẩn/hiện từng trường

**Mục đích:** Admin có thể toggle ẩn/hiện từng trường cụ thể (e.g. "Chẩn đoán:" label) mà không xóa nó, để reuse template mà không cần chỉnh sửa lại.

**Quy tắc:**
- Mỗi `LayoutElement` (field, label, block, row) có thêm trường optional: `hidden?: boolean | null`
- Default: `undefined` / `null` (hiển thị bình thường, parity với các element cũ)
- Khi `hidden === true` → renderer bỏ qua element này (không render)
- Bật lại: toggle `hidden` từ `true` → `false` / `null` → phục hồi hiển thị

**Scope ẩn:**
- `TemplateRenderer` lọc ở 3 vị trí:
  1. Top-level auto-flow elements
  2. Trong row columns
  3. Bên trong blocks (e.g. inside rx_list block)
- **Label vs Value độc lập:** e.g. "Chẩn đoán:" (label) ẩn, nhưng "Viêm phế quản" (value) vẫn hiện = **không phải** block ẩn mà từng field ẩn

**Backend schema:**
- `clinic-cms/app/modules/admin/schemas/print_template_schemas.py::LayoutElement`
  ```python
  class LayoutElement(BaseModel):
      id: str
      kind: Literal["field", "label", "block", "row"]
      field_key: str | None = None
      text: str | None = None
      ...
      hidden: bool | None = None  # ← NEW (nullable, no migration)
  ```
- Layout lưu trữ: JSONB (PostgreSQL) → không cần migration

**FE UI:**
- `src/pages/admin/PrintTemplatesPage.tsx` → field properties panel → checkbox "Hiển thị trên bản in"
- Tương tự checkbox "Hiển thị nhãn" `show_label` hiện có

**Test result:** ✅ Verified live — toggle "Chẩn đoán:" ẩn → PATCH → GET → print không hiển thị label, giá trị "Viêm phế quản" vẫn in (phía dưới); toggle hiện lại → restore.

---

### 3.4 Tính năng D: Cách dùng (Usage Instruction)

**Mục đích:** Bác sĩ kê đơn có thể chọn/nhập cách dùng thuốc một cách có cấu trúc (uống trước ăn, sau ăn, …) thay vì ghi trong free-text `dosage` field.

**Tên trường:** `usage_instruction` (VARCHAR(200), nullable, backend)

**Giá trị gợi ý (FE datalist):**
- Uống trước ăn
- Uống sau ăn
- Uống trong khi ăn
- Trước khi ngủ
- … (các giá trị khác)

**Quy tắc:**
- Dropdown gợi ý nhưng cho **nhập tự do** (không enum cứng)
- Bác sĩ có thể chọn từ dropdown hoặc gõ text mới
- Lưu: `POST/PATCH /api/v1/prescriptions/{id}/items` → `usage_instruction: "Uống sau ăn"`
- Tải lại (edit): FE refill field từ `prescription_item.usage_instruction`
- In ra: template field `prescription.usage_instruction` → text in trên giấy

**Backend schema:**
- `clinic-cms/app/modules/prescriptions/models/prescription_item.py`
  ```python
  class PrescriptionItem(Base):
      ...
      usage_instruction: Mapped[str | None] = mapped_column(String(200), nullable=True)
  ```
- Migration: `alembic/versions/0061_prescription_item_usage_instruction.py`
  ```sql
  ALTER TABLE prescription_item ADD COLUMN usage_instruction VARCHAR(200);
  ```

- `clinic-cms/app/modules/prescriptions/schemas/prescription_schemas.py`
  ```python
  class PrescriptionItemCreate(BaseModel):
      ...
      usage_instruction: str | None = None
  
  class PrescriptionItemUpdate(BaseModel):
      ...
      usage_instruction: str | None = None
  
  class PrescriptionItemResponse(BaseModel):
      ...
      usage_instruction: str | None = None
  ```

**FE types:**
- `clinic-cms-web/src/modules/doctor/types.ts::PrescriptionItem` + `PrescriptionItemCreate`
  ```typescript
  export interface PrescriptionItem {
      ...
      usage_instruction?: string;
  }
  ```

**FE UI:**
- `src/components/doctor/PrescriptionTab.tsx` → medicine list item properties → select/input field "Cách dùng" (với datalist gợi ý)
- Include trường trong POST/PATCH payload
- Tải lại (edit mode): `it.usage_instruction ?? ""`

**Print field:**
- `src/lib/printTemplates.ts::FIELD_CATALOG.prescription`
  ```javascript
  {
      key: 'usage_instruction',
      label: 'Cách dùng',
      type: 'string'
  }
  ```
- `src/components/doctor/PrintablePrescription.tsx` (built-in layout) + `TemplateRenderer.tsx` (custom layout) → render field

**Test result:** ✅ Verified live — bác sĩ chọn "Uống sau ăn" → lưu → edit lại → field refill → in ra hiển thị "Uống sau ăn".

---

### 3.5 Tính năng E: Đơn vị liều theo dạng thuốc

**Mục đích:** Thay vì cho bác sĩ tự gõ unit (dễ sai: "viên" vs "viênnn" vs "v"), hệ thống **tự resolve** unit từ dạng thuốc (e.g. injection → ống, tablet → viên).

**Quy tắc resolution:**
```
resolve_dosage_form_unit(medicine, clinic_id) {
  // 1. Nếu medicine.dosage_form_id có (từ TASK-093) → join DosageForm.unit
  if (medicine.dosage_form_id) {
      form = DosageForm.get(id=medicine.dosage_form_id, clinic=clinic_id)
      if (form && form.unit) return form.unit
  }
  
  // 2. Interim: match free-text medicine.dosage_form vs DosageForm.code (system rows)
  if (medicine.dosage_form) {
      form = DosageForm.search(
          code or name = medicine.dosage_form (case-insensitive),
          is_system=true, is_deleted=false
      )
      if (form && form.unit) return form.unit
  }
  
  // 3. Fallback: medicine.base_unit
  return medicine.base_unit
}
```

**Seed units cho system dosage forms (0062 migration):**

| DosageForm code | name | unit | example |
|-----------------|------|------|---------|
| tablet | Viên | viên | Paracetamol 500mg tablet → 2 viên |
| capsule | Viên | viên | Amoxicillin capsule → 1 viên |
| syrup | Siro | ml | Cough syrup → 10 ml |
| injection | Tiêm | ống | Dexamethasone inj → 1 ống |
| cream | Mỡ | tuýp | Antibiotic cream → 1 tuýp |
| drops | Giọt | lọ | Eye drops → 1 lọ |
| inhaler | Xịt | bình | Asthma inhaler → 1 bình |
| other | Khác | *(null)* | Unknown → null → fallback base_unit |

**Backend schema:**
- `clinic-cms/app/modules/inventory/models/dosage_form.py`
  ```python
  class DosageForm(Base):
      ...
      unit: Mapped[str | None] = mapped_column(String(50), nullable=True)
  ```
- Migration: `alembic/versions/0062_dosage_form_unit.py`
  ```sql
  ALTER TABLE dosage_form ADD COLUMN unit VARCHAR(50);
  -- Seed system rows
  UPDATE dosage_form SET unit = 'viên' WHERE code = 'tablet' AND is_system=true;
  UPDATE dosage_form SET unit = 'viên' WHERE code = 'capsule' AND is_system=true;
  UPDATE dosage_form SET unit = 'ml' WHERE code = 'syrup' AND is_system=true;
  ...
  ```

**Medicine search DTO (prescribing):**
- Include `dosage_form_unit` in the response (resolved từ logic ở trên)
- FE sẽ dùng field này để prefill khi chọn medicine

**FE types:**
- `src/modules/doctor/types.ts::Medicine` + admin `types.ts::DosageForm`
  ```typescript
  export interface Medicine {
      ...
      dosage_form_unit?: string;
  }
  
  export interface DosageForm {
      ...
      unit?: string;
  }
  ```

**FE UI:**
- `src/pages/admin/DosageFormsPage.tsx` → create/edit form → thêm field "Đơn vị" (input text)
- `src/components/doctor/PrescriptionTab.tsx::addMedicine()` → khi chọn medicine, prefill unit:
  ```javascript
  unit: med.dosage_form_unit || med.base_unit
  ```
- Unit field vẫn editable (bác sĩ có thể override)

**Print field:**
- Unit đã lưu trong `prescription_item.unit` → in như thường (không thay đổi logic in)

**Test result:** ✅ Verified live — bác sĩ chọn Dexamethasone injection → unit auto-fill "ống" (không phải "viên" default cũ) → in ra "1 ống".

---

## 4. Danh sách API

Tất cả API yêu cầu xác thực JWT (`Authorization: Bearer <token>`) trong header.

### 4.1 Print template — Read (quyền thay đổi → `prescription.print`)

#### GET /api/v1/print-templates

**Phương thức:** GET  
**Quyền:** `prescription.print` (doctor, nurse, pharmacist, admin)  
**Mục đích:** Lấy danh sách mẫu in theo loại

**Tham số query:**
| Tham số | Kiểu | Bắt buộc | Mô tả | Ví dụ |
|---------|------|----------|-------|-------|
| `template_type` | string | Không | Loại mẫu (prescription / exam_form / visit_detail) | `prescription` |
| `is_system` | boolean | Không | Lọc mẫu system (true) hay user (false) | `false` |
| `is_default` | boolean | Không | Lọc mẫu mặc định | `true` |

**Response 200 OK:**
```json
{
  "data": [
    {
      "id": "tmpl-001",
      "clinic_id": "clinic-123",
      "name": "Đơn thuốc A4 (mẫu bệnh viện)",
      "template_type": "prescription",
      "is_system": false,
      "is_default": true,
      "paper_size": "A4",
      "layout": [
        {
          "id": "dg-19",
          "kind": "field",
          "field_key": "visit.diagnosis",
          "align": "left",
          "hidden": false
        },
        ...
      ],
      "created_at": "2026-07-15T10:00:00Z",
      "updated_at": "2026-07-22T15:30:00Z"
    }
  ],
  "total": 1,
  "page": 1
}
```

**Response 403 Forbidden:**
```json
{
  "error": {
    "code": "FORBIDDEN",
    "message": "Permission 'prescription.print' is required for this action."
  }
}
```

---

#### GET /api/v1/print-templates/{id}

**Phương thức:** GET  
**Quyền:** `prescription.print` (doctor, nurse, pharmacist, admin)  
**Mục đích:** Lấy chi tiết một mẫu in (dùng khi render TemplateRenderer)

**Tham số URL:**
| Tham số | Kiểu | Mô tả |
|---------|------|-------|
| `id` | string (UUID) | ID của mẫu in |

**Response 200 OK:**
```json
{
  "data": {
    "id": "tmpl-001",
    "clinic_id": "clinic-123",
    "name": "Đơn thuốc A4 (mẫu bệnh viện)",
    "template_type": "prescription",
    "is_system": false,
    "is_default": true,
    "paper_size": "A4",
    "layout": [
      {
        "id": "dg-19",
        "kind": "field",
        "field_key": "visit.diagnosis",
        "label": "Chẩn đoán:",
        "align": "left",
        "hidden": false
      },
      {
        "id": "rx-list-1",
        "kind": "block",
        "block_key": "rx_list",
        "hidden": null
      }
    ]
  }
}
```

**Response 404 Not Found:**
```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Print template not found."
  }
}
```

---

### 4.2 Print template — Write (quyền không đổi → `settings.clinic`)

#### PATCH /api/v1/print-templates/{id}

**Phương thức:** PATCH  
**Quyền:** `settings.clinic` (admin only)  
**Mục đích:** Cập nhật mẫu in (gồm cả `hidden` flag trên layout elements)

**Request body:**
```json
{
  "name": "Đơn thuốc A4 (mẫu bệnh viện) - updated",
  "is_default": true,
  "layout": [
    {
      "id": "dg-19",
      "kind": "field",
      "field_key": "visit.diagnosis",
      "label": "Chẩn đoán:",
      "align": "left",
      "hidden": true
    }
  ]
}
```

**Response 200 OK:**
```json
{
  "data": {
    "id": "tmpl-001",
    ...
    "layout": [
      {
        "id": "dg-19",
        "kind": "field",
        "field_key": "visit.diagnosis",
        "label": "Chẩn đoán:",
        "align": "left",
        "hidden": true
      }
    ]
  }
}
```

---

### 4.3 Prescription — Tạo/cập nhật item (thêm `usage_instruction`)

#### POST /api/v1/prescriptions

**Phương thức:** POST  
**Quyền:** `prescription.create` (doctor, nurse)  
**Mục đích:** Tạo đơn thuốc mới

**Request body:**
```json
{
  "visit_id": "visit-456",
  "items": [
    {
      "medicine_id": "med-789",
      "quantity": 1,
      "unit": "ống",
      "usage_instruction": "Uống sau ăn",
      "note": "Dùng hết liều"
    }
  ]
}
```

**Response 201 Created:**
```json
{
  "data": {
    "id": "rx-001",
    "visit_id": "visit-456",
    "items": [
      {
        "id": "rx-item-1",
        "medicine_id": "med-789",
        "quantity": 1,
        "unit": "ống",
        "usage_instruction": "Uống sau ăn",
        "note": "Dùng hết liều"
      }
    ],
    "created_at": "2026-07-22T16:00:00Z"
  }
}
```

---

#### PATCH /api/v1/prescriptions/{id}/items/{item_id}

**Phương thức:** PATCH  
**Quyền:** `prescription.update` (doctor)  
**Mục đích:** Cập nhật item đơn thuốc (gồm `usage_instruction`)

**Request body:**
```json
{
  "quantity": 2,
  "unit": "ống",
  "usage_instruction": "Uống trước ăn"
}
```

**Response 200 OK:**
```json
{
  "data": {
    "id": "rx-item-1",
    "medicine_id": "med-789",
    "quantity": 2,
    "unit": "ống",
    "usage_instruction": "Uống trước ăn",
    "updated_at": "2026-07-22T16:05:00Z"
  }
}
```

---

### 4.4 DosageForm — Admin (thêm `unit`)

#### POST /api/v1/dosage-forms

**Phương thức:** POST  
**Quyền:** `inventory.manage` (admin)  
**Mục đích:** Tạo dạng thuốc mới

**Request body:**
```json
{
  "name": "Viên nang",
  "code": "capsule",
  "unit": "viên",
  "is_system": false
}
```

**Response 201 Created:**
```json
{
  "data": {
    "id": "df-005",
    "name": "Viên nang",
    "code": "capsule",
    "unit": "viên",
    "is_system": false,
    "created_at": "2026-07-22T16:10:00Z"
  }
}
```

---

#### PATCH /api/v1/dosage-forms/{id}

**Phương thức:** PATCH  
**Quyền:** `inventory.manage` (admin)  
**Mục đích:** Cập nhật dạng thuốc (gồm `unit`)

**Request body:**
```json
{
  "unit": "ml"
}
```

**Response 200 OK:**
```json
{
  "data": {
    "id": "df-001",
    "name": "Siro",
    "code": "syrup",
    "unit": "ml",
    "updated_at": "2026-07-22T16:15:00Z"
  }
}
```

---

#### GET /api/v1/dosage-forms

**Phương thức:** GET  
**Quyền:** Không giới hạn (public read, system rows)  
**Mục đích:** Lấy danh sách dạng thuốc (dùng cho dropdown/admin page)

**Response 200 OK:**
```json
{
  "data": [
    {
      "id": "df-001",
      "name": "Viên",
      "code": "tablet",
      "unit": "viên",
      "is_system": true,
      "created_at": "2026-07-10T00:00:00Z"
    },
    {
      "id": "df-002",
      "name": "Tiêm",
      "code": "injection",
      "unit": "ống",
      "is_system": true
    }
  ],
  "total": 7
}
```

---

## 5. Cấu trúc cơ sở dữ liệu

### 5.1 Bảng `prescription_item` (tính năng D)

**Cột mới:**

| Tên cột | Kiểu | Nullable | Default | Mô tả | Migration |
|---------|------|----------|---------|-------|-----------|
| `usage_instruction` | VARCHAR(200) | YES | NULL | Cách sử dụng thuốc (e.g. "Uống sau ăn") | 0061 |

**DDL:**
```sql
ALTER TABLE prescription_item 
ADD COLUMN usage_instruction VARCHAR(200) NULL;
```

**Downgrade:**
```sql
ALTER TABLE prescription_item 
DROP COLUMN usage_instruction;
```

---

### 5.2 Bảng `dosage_form` (tính năng E)

**Cột mới:**

| Tên cột | Kiểu | Nullable | Default | Mô tả | Migration |
|---------|------|----------|---------|-------|-----------|
| `unit` | VARCHAR(50) | YES | NULL | Đơn vị liều (e.g. "viên", "ống", "ml") | 0062 |

**DDL:**
```sql
ALTER TABLE dosage_form 
ADD COLUMN unit VARCHAR(50) NULL;

-- Seed system dosage forms with units
UPDATE dosage_form SET unit = 'viên' 
WHERE is_system = true AND (code = 'tablet' OR code = 'capsule') AND clinic_id IS NULL;

UPDATE dosage_form SET unit = 'ml' 
WHERE is_system = true AND code = 'syrup' AND clinic_id IS NULL;

UPDATE dosage_form SET unit = 'ống' 
WHERE is_system = true AND code = 'injection' AND clinic_id IS NULL;

UPDATE dosage_form SET unit = 'tuýp' 
WHERE is_system = true AND code = 'cream' AND clinic_id IS NULL;

UPDATE dosage_form SET unit = 'lọ' 
WHERE is_system = true AND code = 'drops' AND clinic_id IS NULL;

UPDATE dosage_form SET unit = 'bình' 
WHERE is_system = true AND code = 'inhaler' AND clinic_id IS NULL;

-- 'other' left NULL by design
```

**Downgrade:**
```sql
ALTER TABLE dosage_form 
DROP COLUMN unit;
```

---

### 5.3 Bảng `print_template` — JSONB layout (tính năng C)

**Cột hiện tại:** `layout` (JSONB)

**Thay đổi:** Thêm `hidden: bool | null` vào mỗi `LayoutElement` object trong JSONB.

**Ví dụ trước:**
```json
{
  "layout": [
    {
      "id": "dg-19",
      "kind": "field",
      "field_key": "visit.diagnosis",
      "label": "Chẩn đoán:",
      "align": "left"
    }
  ]
}
```

**Ví dụ sau:**
```json
{
  "layout": [
    {
      "id": "dg-19",
      "kind": "field",
      "field_key": "visit.diagnosis",
      "label": "Chẩn đoán:",
      "align": "left",
      "hidden": false
    }
  ]
}
```

**Lưu ý:** Không cần migration vì JSONB schema-less. Toàn bộ existing elements tự động có `hidden: null` / absent khi đọc (equals hidden = false).

---

### 5.4 Alembic migrations

**Liên quan 2 tệp:**

1. **`alembic/versions/0061_prescription_item_usage_instruction.py`**
   - Ngày: 2026-07-22
   - Revision: `0061`, Down: `0060`
   - Thêm column `prescription_item.usage_instruction`

2. **`alembic/versions/0062_dosage_form_unit.py`**
   - Ngày: 2026-07-22
   - Revision: `0062`, Down: `0061`
   - Thêm column `dosage_form.unit` + seed units

**Lưu ý merge-gate (Phần 8.2):** 2 migration này collision với TASK-093 trên revision `0061`.

---

## 6. Quy tắc nghiệp vụ

### BR-1: Chọn mẫu in mặc định

| Mục | Chi tiết |
|-----|----------|
| **Quy tắc** | Khi FE gọi `GET /print-templates?template_type=prescription`, BE trả về toàn bộ danh sách. FE gọi `selectDefaultTemplate()` để tìm mẫu mặc định theo thứ tự: `is_default && !is_system` → `is_default` → `null` |
| **Khi nào áp dụng** | Mỗi khi mở print modal (doctor, billing, exam form) |
| **Xử lý lỗi** | Nếu `null` → fallback built-in (`PrintablePrescription`) |
| **Test case** | AC1: Doctor print honors default template; 06b-PASS screenshot |

### BR-2: Đọc chẩn đoán chính xác

| Mục | Chi tiết |
|-----|----------|
| **Quy tắc** | Mỗi modal in phải đọc từ `visit.diagnosis`; nếu rỗng fallback `visit.chief_complaint` (KHÔNG bao giờ `visit.notes`) |
| **Khi nào áp dụng** | Doctor PrintPrescriptionModal, billing PrintPrescriptionModal, PrintExamFormModal, VisitDetailPage |
| **Xử lý lỗi** | Rỗng → hiển thị "(Chưa có chẩn đoán)" |
| **Test case** | AC2: Diagnosis prints correctly on all paths; 03-PASS, 04-PASS screenshots |

### BR-3: Ẩn/hiện trường trên mẫu in

| Mục | Chi tiết |
|-----|----------|
| **Quy tắc** | `TemplateRenderer` lọc: `elements.filter(el => !el.hidden)`. Element có `hidden === true` không render |
| **Khi nào áp dụng** | Mỗi khi render custom template (không ảnh hưởng built-in `PrintablePrescription`) |
| **Xử lý lỗi** | Nếu element vừa là label vừa là field: xử lý độc lập (e.g. label ẩn, field hiện) |
| **Test case** | AC3: Per-field hide/unhide; 08b-PASS screenshot |

### BR-4: Cách dùng — lưu và tái sử dụng

| Mục | Chi tiết |
|-----|----------|
| **Quy tắc** | `prescription_item.usage_instruction` là string tùy ý, có gợi ý từ datalist nhưng cho nhập tự do. POST/PATCH lưu giá trị đó; GET/PATCH-for-edit refill field |
| **Khi nào áp dụng** | Bác sĩ kê đơn (PrescriptionTab) |
| **Xử lý lỗi** | Rỗng / `null` → field trống (không hiển thị "undefined") |
| **Test case** | AC4: Usage instruction persists/reloads/prints; 05-PASS screenshot |

### BR-5: Đơn vị liều từ dạng thuốc

| Mục | Chi tiết |
|-----|----------|
| **Quy tắc** | Khi bác sĩ chọn medicine, FE resolve unit: `medicine.dosage_form_unit` (từ `DosageForm.unit` via resolution logic) → fallback `medicine.base_unit`. Pre-fill field `prescription_item.unit` nhưng vẫn editable |
| **Khi nào áp dụng** | Kê đơn (PrescriptionTab.addMedicine) |
| **Xử lý lỗi** | Không match → `null` → fallback base_unit → fallback "viên" (default cũ) |
| **Test case** | AC5: Dosage unit follows dosage form; 05-PASS screenshot (injection → ống) |

### BR-6: Permission gating (quyền mới)

| Mục | Chi tiết |
|-----|----------|
| **Quy tắc** | `GET /print-templates` + `GET /print-templates/{id}` → quyền `prescription.print` (rộng: doctor, nurse, pharmacist, admin). Write (`POST`, `PATCH`, `DELETE`, `duplicate`) → `settings.clinic` (chỉ admin) |
| **Khi nào áp dụng** | Mỗi request print template API |
| **Xử lý lỗi** | Nếu role thiếu `prescription.print` → 403 + fallback built-in |
| **Test case** | BUG-094-001 fixed: dr_nguyen now 200 on GET /print-templates; 06b-PASS screenshot |

---

## 7. Xử lý lỗi

### E-1: Chẩn đoán rỗng

**Lỗi:** Bệnh nhân không có chẩn đoán nhập
**Nguyên nhân:** Bác sĩ chưa lưu chẩn đoán trên tab "Khám"
**Xử lý:** Hiển thị dòng rỗng hoặc "(Chưa có chẩn đoán)" trên in
**Code:** Toàn bộ 4 modal đều handle: `visit?.diagnosis || visit?.chief_complaint || ""`

### E-2: Không có mẫu in mặc định

**Lỗi:** Phòng khám chưa cấu hình mẫu in mặc định
**Nguyên nhân:** Admin chưa vào `/admin/print-templates` để thiết kế
**Xử lý:** 
- Prescription: fallback built-in `PrintablePrescription` (tự động)
- Exam form: hiển thị "Chưa có mẫu in phiếu khám mặc định" + disable print button
**Code:** Kiểm tra `selectDefaultTemplate()` return `null` → render fallback

### E-3: Permission 403 khi bác sĩ in

**Lỗi:** `GET /print-templates` trả 403 (Forbidden)
**Nguyên nhân:** Role thiếu `prescription.print` (thường là role cũ chưa cập nhật quyền)
**Xử lý:** FE bắt exception → fallback built-in layout (graceful degrade)
**Code:** PrescriptionTab / PrintPrescriptionModal catch `api.list()` error → `rxTemplates = undefined` → fallback

### E-4: `usage_instruction` quá dài

**Lỗi:** Bác sĩ nhập >200 ký tự
**Nguyên nhân:** Datalist gợi ý dài, bác sĩ thêm thông tin dài
**Xử lý:** Backend validation: reject nếu `len > 200`; FE show toast lỗi "Cách dùng quá dài (tối đa 200 ký tự)"
**Code:** Pydantic `String(200)` + FE validation input `maxLength=200`

### E-5: Dosage form không match catalog

**Lỗi:** Bác sĩ chọn medicine với `dosage_form="siro Pháp"` (typo/kỳ lạ), không match "syrup"
**Nguyên nhân:** Dữ liệu không chuẩn hoặc catalog chưa đầy đủ
**Xử lý:** Resolution logic fallback → `medicine.base_unit` (e.g. "ml")
**Code:** `_resolve_dosage_form_units()` → `if not match: return None` → FE: `dosage_form_unit || base_unit`

### E-6: Template element lỗi render

**Lỗi:** TemplateRenderer gặp field không hợp lệ (e.g. `field_key="visit.unknown_field"`)
**Nguyên nhân:** Admin edit template field không cẩn thận
**Xử lý:** Fallback hiển thị dòng trống; log warning
**Code:** TemplateRenderer `try-catch` khi mapping values → field

---

## 8. Ghi chú và lưu ý khi kiểm thử

### 8.1 Kiểm thử chi tiết từng tính năng

#### Tính năng A: Chẩn đoán

- [ ] **Test A-1:** Bác sĩ nhập chẩn đoán "Viêm phế quản" → tab "Khám" → "Chẩn đoán" → lưu → kiểm tra DB `visit.diagnosis`
- [ ] **Test A-2:** Mở bệnh nhân này → "Kê đơn" → "In đơn thuốc" → check in ra "Chẩn đoán: Viêm phế quản" (không phải ghi chú)
- [ ] **Test A-3:** Admin → visit-detail → "In" → billing modal → check chẩn đoán in chính xác
- [ ] **Test A-4:** Exam form → "In phiếu khám" → check chẩn đoán in chính xác
- [ ] **Regressions:** không in `visit.notes` hay `visit.chief_complaint` (kiểm tra ngữ cảnh cũ)

**Pass criteria:** ✅ Đã test live — tất cả 4 luồng in diagnosis chính xác (test report Iteration 2, Scenario 1 đã pass)

#### Tính năng B: Mẫu in mặc định

- [ ] **Setup:** Admin cấu hình mẫu `"Đơn thuốc A4 (bệnh viện)"` → "Mặc định" → lưu
- [ ] **Test B-1:** Bác sĩ `dr_nguyen` → in đơn thuốc → check layout là **A4 custom** (không A5 built-in)
- [ ] **Test B-2:** Check permission: `GET /print-templates` as doctor → **200** (trước đây 403)
- [ ] **Test B-3:** Xóa "Mặc định" flag → in lại → fallback built-in A5 (parity vớI cũ)
- [ ] **Test B-4:** Exam form: "In phiếu khám" → nên hiển thị "Dùng mẫu: Phiếu khám bệnh A5" (không "Chưa có mẫu")

**Pass criteria:** ✅ Đã test live — doctor modal render custom A4 template, exam form finds default (test report Iteration 2, Scenario 2 đã pass)

#### Tính năng C: Ẩn/hiện trường

- [ ] **Setup:** Admin → template → chọn `"Chẩn đoán:"` label element → uncheck "Hiển thị trên bản in" → lưu
- [ ] **Test C-1:** Kiểm tra PATCH request body có `"hidden":true`
- [ ] **Test C-2:** Kiểm tra PATCH response + fresh GET đều có `"hidden":true` (persisted)
- [ ] **Test C-3:** In đơn → "Chẩn đoán:" label **không xuất hiện**; giá trị `"Viêm phế quản"` vẫn in
- [ ] **Test C-4:** Toggle lại "Hiển thị" → label **reappear** trên in
- [ ] **Regression:** Toàn bộ field hiện (default) vẫn in bình thường

**Pass criteria:** ✅ Đã test live — toggle persist, hidden field không in, restore hoạt động (test report Iteration 2, Scenario 1 đã pass, screenshot 08b-PASS)

#### Tính năng D: Cách dùng

- [ ] **Test D-1:** Bác sĩ kê đơn Dexamethasone → chọn "Uống sau ăn" từ dropdown → lưu
- [ ] **Test D-2:** Kiểm tra DB: `prescription_item.usage_instruction = "Uống sau ăn"`
- [ ] **Test D-3:** Edit đơn → field "Cách dùng" refill "Uống sau ăn" (không rỗng)
- [ ] **Test D-4:** In đơn → in ra "Uống sau ăn" sau item
- [ ] **Test D-5:** Bác sĩ nhập tự do "Uống sau ăn lúc 1 tiếng" → lưu → refill → in chính xác

**Pass criteria:** ✅ Đã test live — usage_instruction persist, refill, in chính xác (test report Iteration 2, Scenario 4 đã pass, screenshot 05-PASS)

#### Tính năng E: Đơn vị theo dạng thuốc

- [ ] **Setup:** Admin → DosageForm → Injection (code=`injection`) → nhập "ống" → lưu → DB `dosage_form.unit = "ống"`
- [ ] **Test E-1:** Bác sĩ kê đơn chọn Dexamethasone (injection) → field "Đơn vị" auto-fill "ống" (không "viên")
- [ ] **Test E-2:** Kiểm tra DB: `prescription_item.unit = "ống"`
- [ ] **Test E-3:** Edit đơn → field "Đơn vị" vẫn "ống" (không reset)
- [ ] **Test E-4:** Bác sĩ có thể override: chỉnh "ống" → "2 ống" (vẫn editable)
- [ ] **Test E-5:** In đơn → in ra "1 ống" (resolved unit, không default "viên")
- [ ] **Regression:** Tablet/syrup/cream (viên/ml/tuýp) vẫn resolve chính xác từ seed units

**Pass criteria:** ✅ Đã test live — injection → "ống", persist, editable, in chính xác (test report Iteration 2, Scenario 5 đã pass, screenshot 05-PASS)

### 8.2 Ghi chú & hạn chế đã biết (KHÔNG phải lỗi)

#### Known Limitation 1: Cashier role vẫn không thể in (deliberate scope)

**Trạng thái:** ✅ Accepted (KHÔNG file bug)  
**Tình huống:** `cashier` role kê đơn ở billing flow → click "In" → 403 on `GET /print-templates` → fallback built-in layout

**Nguyên nhân:** `cashier` role chưa được grant `prescription.print` quyền (task này không gồm cashier scope — được user decide)

**Scope decision:** TASK-094 AC không yêu cầu cashier in được (chỉ doctor/billing/exam form). Cashier access là follow-up candidate, không phải lỗi task này.

**Trong code:** Xem comment ở review report, Issue 1 & BUG-094-001 (now resolved for doctor role; cashier deliberately out-of-scope)

**Test action:** Nếu kiểm thử gặp cashier 403 → ✅ EXPECTED, không fail test case

#### Known Limitation 2: Alembic migration revision collision (merge-gate concern)

**Trạng thái:** 📝 Documented (để xử lý tại merge)  
**Tình huống:** TASK-094's `0061_prescription_item_usage_instruction.py` có revision `0061`. TASK-093 (unmerged) cũng dùng `0061` cho migration khác.

**Khi nào phát hiện:** Khi cả 2 branch merge vào `main`, Alembic sẽ báo duplicate revision + multiple heads.

**Fix tại merge (cho ai merge sau):**
- **Nếu TASK-093 merge trước:** TASK-094 renumber migrations `0061→0063`, `0062→0064` + repoint down_revision
- **Nếu TASK-094 merge trước:** TASK-093 renumber thay

**Ngay bây giờ (single-branch context):** ✅ Chain clean: `0059→0060→0061→0062` (linear, không duplicate on THIS branch)

**Test action:** 
- Nếu test shared dev DB → check `alembic_version` vs actual schema trước/sau (migration apply chính xác)
- Nếu gặp "multiple heads" error trên shared DB → manual fix: `ALTER TABLE prescription_item ADD COLUMN usage_instruction VARCHAR(200);` (verbatim migration body)

### 8.3 Kiểm thử regression (phải vượt)

**FE unit tests (61 files):**
- [ ] `PrintPrescriptionModal.test.tsx` — diagnosis, template selection
- [ ] `PrintablePrescription.test.tsx` — built-in layout rendering
- [ ] `PrescriptionTab-stock.test.tsx` — basic prescribing flow
- [ ] `PrescriptionTab-usage-instruction.test.tsx` — NEW, cách dùng flow
- [ ] `PrescriptionTab-dosage-unit.test.tsx` — NEW, unit resolution
- [ ] `ExamTab.test.tsx`, `SummaryTab.test.tsx` — (must not break)
- [ ] `DosageFormsPage.test.tsx` — unit field add/edit
- [ ] `TemplateRenderer.test.tsx` — hidden field filter
- **Result:** ✅ 61/61 pass (reported in review + test report)

**BE integration tests (87 tests real DB):**
- [ ] `test_print_template_read_allowed_for_prescription_print_role` — doctor 200 on GET /templates (NEW)
- [ ] `test_print_template_hidden_field_roundtrips` — hidden persist PATCH→GET (NEW)
- [ ] `TestUsageInstruction` — create/update/patch usage field (NEW)
- [ ] `TestDosageFormUnitResolution` — resolve injection→ống, fallback base_unit (NEW)
- [ ] All 83 existing tests (prescriptions, admin, inventory) — must pass unchanged
- **Result:** ✅ 87/87 pass (reported in test report, Iteration 2)

**Static checks:**
- [ ] `npm run type-check` — ✅ CLEAN
- [ ] `npm run lint` — ✅ 0 new (18 pre-existing in unmodified files)
- [ ] `ruff check` (BE) — ✅ 0 new (19 pre-existing, confirmed via diff review)
- [ ] `mypy app` (BE) — ✅ 0 new (51 total, none in modified files)

**Result:** ✅ Toàn bộ 87 BE + 61 FE + static checks PASS (test report Iteration 2)

### 8.4 Performance & edge cases

- **Performance:** In đơn với custom template (TemplateRenderer) được kiểm thử live — không có performance regression (render hàng chục field, đơn vị thời gian tương tự built-in)
- **Edge case 1:** Medicine không match dosage form → fallback base_unit (syrup → `medicine.base_unit="ml"` → "10 ml" in chính xác)
- **Edge case 2:** Template có vừa hidden vừa non-hidden field → renderer skip hidden, hiển thị non-hidden (verified 08b screenshot)
- **Edge case 3:** Rỗng cách dùng → `null` → in ra không dòng "Cách dùng:" (không "undefined" text)

### 8.5 Quy trình E2E thực tế (browser live test)

**Scenario 1 — Doctor in đơn với mẫu mặc định:**
1. Đăng nhập `dr_nguyen` / `Doctor@1234` (role doctor)
2. Mở visit đang khám → "Kê đơn" tab
3. Chọn medicine (e.g. Dexamethasone injection) → unit auto-fill "ống", usage "Uống sau ăn" → lưu
4. "In đơn thuốc" → modal mở → **check nội dung là A4 custom template** (không A5 built-in)
5. Check in ra: chẩn đoán, usage ("Uống sau ăn"), unit ("1 ống")
6. **Expected:** ✅ All 5 features visible + correct

**Scenario 2 — Admin hide diagnosis label:**
1. Đăng nhập admin
2. `/admin/print-templates` → "Đơn thuốc A4" template → Edit
3. Chọn "Chẩn đoán:" label → uncheck "Hiển thị trên bản in" → Save
4. Back to visit → doctor in đơn → **label không thấy**, giá trị "Viêm phế quản" vẫn in
5. **Expected:** ✅ Feature C working

**Screenshots kỳ vọng:**
- `06b-PASS-doctor-modal-honors-default-template.png` — A4 template render
- `07b-PASS-examform-default-found-enabled.png` — exam form finds default
- `08b-PASS-hidden-field-persisted-in-print.png` — hidden field không in
- `05-prescribe-usage-unit.png` — usage + unit in chính xác

### 8.6 Quy trình rollback nếu cần

**Nếu feature có issue & cần rollback:**

1. **Database:** 2 migrations additive/nullable → safe rollback
   ```bash
   alembic downgrade 0060  # Drops 0061, 0062 columns (reversible)
   ```

2. **Code:** Không dùng feature mới = fallback built-in (graceful degrade)
   - Doctor in → 403 on `GET /print-templates` → fallback `PrintablePrescription` (built-in)
   - Nếu usage field trống → không in dòng cách dùng
   - Nếu dosage_form.unit `NULL` → fallback base_unit

3. **API:** Old API callers vẫn hoạt động (new fields optional)

---

## Tài liệu tham khảo

- **Implementation Plan:** `docs/tasks/TASK-094/refs/implementation-plan.md`
- **Test Report (full, iteration 1+2):** `docs/tasks/TASK-094/deliveries/test-reports/test-report.md`
- **Bug reports (now resolved):** 
  - `docs/tasks/TASK-094/bugs/BUG-094-001.md` (permission fix)
  - `docs/tasks/TASK-094/bugs/BUG-094-002.md` (hidden field fix)
- **Code Review:** `docs/tasks/TASK-094/handoff/review-report.md`
- **Test-to-Doc Handoff:** `docs/tasks/TASK-094/handoff/test-to-documentation.md`
- **Screenshots:** `docs/tasks/TASK-094/deliveries/test-reports/screenshots/`
  - Passing: 06b, 07b, 08b, 05, 03, 04 (v.v.)

---

**Phiên bản này đã hoàn tất kiểm thử (Iteration 2, 2026-07-22) — Tất cả 5 tính năng + sửa lỗi đã PASS. Sẵn sàng để release.**

