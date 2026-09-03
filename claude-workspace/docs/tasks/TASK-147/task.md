---
id: TASK-147
type: bug
title: FE thiếu bước "bác sĩ gửi đơn" — cấp phát thuốc bị chặn hoàn toàn sau TASK-142
status: IN_PROGRESS
priority: High
assigned: claude-main
created: 2026-09-03
updated: 2026-09-03
branch: "dev"
jira_key: ""
tags: [prescription, pharmacy, dispense, regression, frontend]
affected-repos: [clinic-cms-web]
refs:
  detail_design: ""
  implementation_plan: ""
  figma: ""
  confluence: ""
  jira_ticket: ""
  other:
    - "TASK-142 (commit 5084356) — guard đã tạo ra regression này"
---

# TASK-147: FE thiếu bước "bác sĩ gửi đơn" — cấp phát thuốc bị chặn hoàn toàn sau TASK-142

## Description

Cấp phát thuốc trả về lỗi với mọi đơn thuốc kê qua UI:

```json
{
  "error": {
    "code": "BUSINESS_RULE_VIOLATION",
    "message": "Không thể cấp phát đơn thuốc ở trạng thái 'draft' (yêu cầu 'pending' — bác sĩ phải gửi đơn trước khi cấp phát).",
    "details": { "prescription_id": "f7b8a00b-f21f-4fbf-badc-1f5e55c8fa87", "status": "draft" }
  }
}
```

**Nguyên nhân gốc:** đường duy nhất chuyển `draft → pending` là
`POST /prescriptions/{id}/submit` (`prescription_service.submit`, dòng 764).
FE có khai báo wrapper `doctorApi.submitPrescription`
(`src/modules/doctor/api.ts:196`) và đủ chuỗi i18n (`prescription.submit`,
`submitting`, `submitSuccess` — cả `vi` và `en`) **từ TASK-012**, nhưng
**không có call site nào trong toàn bộ `src/`**. Nên mọi đơn thuốc nằm mãi ở
`draft`.

Điều này vô hại cho tới TASK-142 (commit `5084356`, 2026-08-18) siết cấp phát
về đúng nghiệp vụ. Guard của TASK-142 là **đúng và không nên gỡ** — thiếu là
phần FE tương ứng chưa bao giờ được làm.

**Phạm vi hỏng — 3 chỗ, không chỉ chỗ user gặp:**

| Chỗ | Cơ chế |
|---|---|
| Nút "Cấp phát thuốc" ở Khu làm việc bác sĩ | `ClinicalWorkspacePage.tsx:259` hiện nút với mọi status ≠ dispensed/cancelled → bấm là ra lỗi trên |
| Hàng đợi "Chờ cấp phát" của nhà thuốc | `pending_dispense_service.list_pending` lọc `Prescription.status == 'pending'` → **luôn rỗng** |
| Hoàn tất lượt khám | `visit_completion_service` chặn khi còn thuốc nội viện chưa cấp phát → lượt khám có thuốc **không bao giờ** COMPLETED được |

## Requirements

- [x] Thêm điểm vào UI cho `POST /prescriptions/{id}/submit` (draft → pending)
- [x] Nút "Cấp phát thuốc" ở Khu làm việc không được chết vì đơn còn draft
- [x] Không phá luồng bác sĩ sửa đơn giữa buổi khám
- [x] Unit test cho hành vi mới, có xác nhận test fail trên code chưa vá
- [ ] E2E toàn luồng khám bệnh (theo yêu cầu user)

## Acceptance Criteria

- [x] AC1 — Tab Kê đơn có nút "Gửi đơn thuốc", chỉ hiện khi đơn ở `draft` và
  bảng có thuốc; gated bởi permission `prescription.write` (khớp dependency
  của BE route).
- [x] AC2 — Nếu bảng đã sửa so với lần lưu cuối, submit phải chạy Save trước
  rồi gửi **id mới**. Vì `create_with_items` hủy + tạo lại đơn mỗi lần Save,
  gửi id cũ = gửi đơn đã hủy cho nhà thuốc, còn sửa đổi thật của bác sĩ nằm ở
  draft chưa gửi.
- [x] AC3 — Đơn `pending`/`dispensed` không hiện nút gửi (đã có banner riêng
  từ TASK-145 M-2).
- [x] AC4 — Nút "Cấp phát thuốc" ở Khu làm việc tự submit nếu đơn còn draft
  rồi mới dispense, giống bước `if (inv.status === "draft") submitInvoice(...)`
  mà `quickCollectMutation` đã làm với hóa đơn.
- [x] AC5 — Sau khi gửi, hàng đợi "Chờ cấp phát" của nhà thuốc thấy được đơn
  (invalidate query key `["pharmacy"]`).
- [ ] AC6 — E2E: kê đơn → gửi → nhà thuốc cấp phát → thu tiền → lượt khám
  COMPLETED, chạy được trọn vòng.

## Progress Checklist

- [x] Implementation
- [ ] Code Review
- [ ] Testing
- [ ] Documentation

## Related Files

- **Input Specs**: `docs/tasks/TASK-147/refs/`
- **Code**:
  - `clinic-cms-web/src/components/doctor/PrescriptionTab.tsx` — nút "Gửi đơn thuốc" + `submitMutation`
  - `clinic-cms-web/src/pages/doctor/ClinicalWorkspacePage.tsx` — dispense tự submit khi còn draft
  - `clinic-cms-web/src/tests/doctor/PrescriptionTab-submit.test.tsx` — mới, 5 test
- **Tests**: `docs/tasks/TASK-147/deliveries/test-cases/`
- **Handoffs**: `docs/tasks/TASK-147/handoff/`
- **Test Report**: `docs/tasks/TASK-147/deliveries/test-reports/test-report.md`
- **API Specs**: `docs/tasks/TASK-147/deliveries/api-specs/`
- **Final Specs**: `docs/tasks/TASK-147/deliveries/final-specs/`

## Timestamps

- **Created**: 2026-09-03
- **Implementation done**: 2026-09-03

## Notes

### Vì sao không gộp submit vào nút "Lưu"

`create_with_items` raise `ConflictError` khi lượt khám đã có đơn `pending`
("Đơn thuốc của lượt khám này đã gửi nhà thuốc — không thể tạo đơn mới"), mà
stepper của màn khám auto-save mỗi lần rời bước (`flushRef`). Gộp submit vào
Save sẽ lấy mất quyền sửa đơn của bác sĩ ngay giữa buổi khám. Gửi đơn phải là
hành động cố ý.

### Kết quả test (2026-09-03)

| Việc | Kết quả |
|---|---|
| `PrescriptionTab-submit.test.tsx` (mới) | 5/5 pass |
| 11 file test liên quan (`PrescriptionTab-*`, `ConsultationPage`, `PendingDispensePage`, `PrintPrescription*`) | pass, chạy từng file |
| Test mới chạy trên code chưa vá | **fail** — xác nhận bắt được lỗi |
| `eslint` 2 file sửa | sạch |

### Hạn chế môi trường khi test

- `tsc --noEmit` và `vitest run` full suite **OOM** trên máy dev
  (`Fatal process out of memory: Zone`, `Worker exited unexpectedly`) — máy
  đang chạy Oracle + Elasticsearch + Kafka. Phải chạy vitest từng file với
  `--pool=threads --poolOptions.threads.singleThread=true`. **Chưa typecheck
  được toàn bộ project.**
- Ép nhiều file test vào cùng 1 thread thì `PrescriptionTab-dosage-unit` fail
  do nhiễm state chéo giữa các file — đã đối chiếu bằng `git stash`, lỗi này
  **có sẵn trước** thay đổi của task này.
- `ClinicalWorkspacePage` chưa có file test nào trong repo; thay đổi ở đó
  (1 dòng submit-if-draft) hiện chỉ được kiểm bằng E2E, chưa có unit test.

## Blockers

None
