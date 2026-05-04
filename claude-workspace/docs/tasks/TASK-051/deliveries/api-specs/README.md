# API Specifications — TASK-051

**Task:** Cập nhật UI — Typography, i18n, In Phiếu  
**Status:** Complete  
**Date:** 2026-05-04

---

## Tóm tắt

**Không áp dụng** — Task TASK-051 là FE-only (UI/UX polish). Không có API mới, không có endpoint thay đổi, không có payload thay đổi.

### Lý do

1. **i18n default** — Local config change only (`detection.order` modified), không cần BE.
2. **Typography update** — Frontend CSS/className changes, không liên quan API.
3. **Print templates** — Use existing patient/visit/invoice APIs, không endpoint mới.

### Các API hiện tại được sử dụng (không thay đổi)

- Clinic settings API (fetch logo, clinic name for print header) — existing, unchanged
- Patient API (patient demographics) — existing, unchanged
- Visit API (visit info, QR code) — existing, unchanged
- Invoice/Payment API (payment records) — existing, unchanged

### Follow-up

- **TASK-041 BE merge** — When lab-orders endpoint available, PatientDetailPage will wire real lab data to `PrintableLabOrder` component.
- **Visits/Prescriptions/LabResults** — When shared page-level query created, `PrintableMedicalSummary` will receive real data instead of empty arrays.

Các follow-up này sẽ documentted trong task riêng sau khi BE ready.
