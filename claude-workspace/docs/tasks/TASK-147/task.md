---
id: TASK-147
type: bug
title: FE thiếu bước "bác sĩ gửi đơn" — cấp phát thuốc bị chặn hoàn toàn sau TASK-142
status: IN_TESTING
priority: High
assigned: claude-main
created: 2026-09-03
updated: 2026-09-04
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
- [x] E2E toàn luồng khám bệnh (theo yêu cầu user)

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
- [x] AC6 — E2E: kê đơn → gửi → nhà thuốc cấp phát → thu tiền → lượt khám
  COMPLETED, chạy được trọn vòng. API 21/21 PASS; UI lái thật 3 nhánh (nút gửi
  ở tab Kê đơn, hàng đợi + cấp phát của nhà thuốc, nút Cấp phát ở Khu làm việc
  đúng kịch bản lỗi user báo). Xem
  `deliveries/test-reports/test-report.md`.

## Progress Checklist

- [x] Implementation
- [ ] Code Review
- [x] Testing (E2E API + UI — chạy sớm theo yêu cầu user, trước cổng review)
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
- **E2E tested**: 2026-09-04

## Notes

### Vì sao không gộp submit vào nút "Lưu"

`create_with_items` raise `ConflictError` khi lượt khám đã có đơn `pending`
("Đơn thuốc của lượt khám này đã gửi nhà thuốc — không thể tạo đơn mới"), mà
stepper của màn khám auto-save mỗi lần rời bước (`flushRef`). Gộp submit vào
Save sẽ lấy mất quyền sửa đơn của bác sĩ ngay giữa buổi khám. Gửi đơn phải là
hành động cố ý.

### Kết quả test

| Việc | Kết quả |
|---|---|
| E2E API toàn luồng (`deliveries/test-cases/e2e_clinical_flow.py`) | **21 PASS / 0 FAIL** |
| E2E UI — nút "Gửi đơn thuốc" (tab Kê đơn) | PASS |
| E2E UI — hàng đợi nhà thuốc + cấp phát | PASS (trước đó rỗng vĩnh viễn) |
| E2E UI — nút "Cấp phát thuốc" ở Khu làm việc (kịch bản lỗi user báo) | PASS, không còn `BUSINESS_RULE_VIOLATION` |
| `PrescriptionTab-submit.test.tsx` (mới, 5 test) | 5/5 pass |
| 11 file test liên quan, chạy từng file | pass hết |
| Test mới chạy trên code chưa vá | **fail** — xác nhận bắt được lỗi |
| `eslint` 2 file sửa | sạch |

Guard của TASK-142 (chặn cấp phát đơn `draft`, hàng đợi lọc `pending`) được kiểm
riêng ở bước 5 và 6 của E2E — vẫn nguyên hiệu lực sau khi vá.

Báo cáo đầy đủ: [deliveries/test-reports/test-report.md](deliveries/test-reports/test-report.md)

### Hạn chế môi trường khi test

- **Phải dùng `127.0.0.1`, không dùng `localhost`** khi lái stack E2E: máy này
  phân giải `localhost` ra IPv6 `::1` trước mà Docker chỉ nghe IPv4 → Python
  `urllib` treo 8s rồi timeout, trình duyệt `ERR_CONNECTION_RESET` (curl không
  bị vì tự fallback). Kéo theo phải build lại image UI với
  `--build-arg VITE_API_URL=http://127.0.0.1:8010` và thêm origin IPv4 vào
  `CORS_ORIGINS` qua `docker-compose.e2e.cors.yml`.
- **Không có endpoint nào expose `stock_movement`** (`/inventory/movements` →
  404). Kiểm tra tồn kho ở tầng DB qua `docker exec ... psql`.
- Nguyên nhân gốc của mọi OOM trong phiên (tsc, vitest, docker build): máy hết
  commit charge — `CommitLimit 49.1 GB / CommitFree 0.3 GB`, RAM vật lý vẫn còn
  7.7 GB trống. `docker build` báo đúng `errno=1455` = `ERROR_COMMITMENT_LIMIT`.
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
