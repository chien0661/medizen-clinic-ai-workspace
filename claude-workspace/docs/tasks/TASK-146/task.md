---
id: TASK-146
type: feature
title: "Lịch sử khám hiển thị đầy đủ (kể cả bản ghi đã hủy) + E2E luồng khám sai → hủy → cấp lại"
status: DONE
priority: High
assigned: Documentation Agent
created: 2026-08-31
updated: 2026-09-01
branch: "feature/TASK-146-visit-history-full"
jira_key: ""
tags: [patients, prescriptions, billing, e2e, ui]
affected-repos: [clinic-cms, clinic-cms-web]
refs:
  detail_design: ""
  implementation_plan: "docs/tasks/TASK-146/refs/implementation-plan.md"
  figma: ""
  confluence: ""
  jira_ticket: ""
  other:
    - "clinic-cms-web/src/pages/patients/PatientDetailPage.tsx (VisitsTab / PrescriptionsTab / InvoicesTab)"
    - "clinic-cms-web/src/modules/doctor/api.ts:165 getVisitPrescription (lọc mất đơn đã hủy)"
    - "TASK-145 — luồng hủy/điều chỉnh hóa đơn + đơn thuốc (đã DONE, đã lên main)"
    - "TASK-142 — chặn cấp phát đơn chưa duyệt (đã lên main)"
---

# TASK-146: Lịch sử khám hiển thị đầy đủ + E2E luồng khám sai → hủy → cấp lại

## Description

Hai phần liên quan chặt với nhau:

1. **Lịch sử khám của bệnh nhân đang giấu mất bản ghi đã hủy.** Sau khi TASK-145 cho phép bác sĩ hủy
   đơn thuốc và thu ngân hủy/hoàn hóa đơn, lịch sử phải kể lại được toàn bộ câu chuyện — kê sai cái gì,
   hủy lúc nào, lý do gì, đơn thay thế là đơn nào. Hiện tại không làm được.
2. **E2E một luồng khám hoàn chỉnh theo kịch bản "điền sai rồi sửa"** — chưa có spec nào chạy trọn vẹn
   một lượt khám từ tiếp nhận đến thanh toán, đi qua sai sót và khắc phục, rồi kiểm tra lại lịch sử.

### Hiện trạng đã khảo sát (grounding)

**Tab Đơn thuốc trong hồ sơ bệnh nhân — lỗi thật, đã xác minh**

`PatientDetailPage.tsx` → `PrescriptionsTab` lấy dữ liệu qua `doctorApi.getVisitPrescription(visitId)`
cho từng lượt khám. Hàm này (`src/modules/doctor/api.ts:165-181`) làm 2 việc khiến lịch sử không đầy đủ:

```ts
const active = result.items.filter((p) => p.status !== "cancelled");
return active[active.length - 1] ?? null;
```

- **Lọc bỏ hoàn toàn đơn `cancelled`** → đơn bị hủy không bao giờ xuất hiện trong lịch sử.
- **Chỉ trả về 1 đơn mới nhất cho mỗi lượt khám** → nếu một lượt khám có nhiều đơn (kê lại sau khi hủy),
  chỉ thấy đơn cuối.

Hệ quả trực tiếp: bảng nhãn trạng thái trong tab này có sẵn `cancelled: "Đã huỷ"`
(`PatientDetailPage.tsx`, PrescriptionsTab) nhưng **không bao giờ render được** — dead code.

Hàm `getVisitPrescription` được thiết kế cho **màn khám của bác sĩ** (chỉ cần đơn đang hiệu lực), dùng lại
cho **màn lịch sử** là sai mục đích — hai màn có nhu cầu ngược nhau.

**Tab Hóa đơn — có vẻ ổn, cần xác minh**

`InvoicesTab` gọi thẳng `/api/v1/invoices?patient_id={id}&limit=50`, **không lọc status**, và bảng nhãn có
`void: "Đã huỷ"`, `refunded: "Hoàn tiền"`. Nhiều khả năng hóa đơn đã hủy/hoàn tiền vẫn hiện — nhưng chưa
được kiểm chứng, và `limit=50` cứng có thể cắt mất lịch sử của bệnh nhân khám nhiều.

**Tab Lượt khám / Sinh hiệu** — đã có, chưa rà mức độ đầy đủ.

## Requirements

### A. Rà soát hiển thị lịch sử

- [x] A1. Liệt kê từng tab (Tổng quan / Lượt khám / Đơn thuốc / Hóa đơn / Sinh hiệu): đang hiển thị trường
      nào, thiếu trường nào so với dữ liệu BE đã trả về. → `handoff/audit-report.md`
- [x] A2. Xác minh hóa đơn `void`/`refunded` có thực sự hiện trong tab Hóa đơn không; nếu có thì lý do hủy
      / hoàn tiền có hiện không. → hiện status nhưng KHÔNG hiện lý do (F2, đã fix); phát hiện thêm:
      tab này trước đây hiện hóa đơn của TOÀN clinic chứ không lọc theo bệnh nhân (patient_id bị bỏ qua
      ở BE) — đã fix cùng đợt.
- [x] A3. Kiểm tra `limit=50` cứng ở InvoicesTab và các giới hạn tương tự — bệnh nhân khám lâu năm có bị
      mất lịch sử không. → xác nhận đúng ở VisitsTab + InvoicesTab (F3, đã fix); VitalsTab có `limit=5`
      riêng, đánh giá là trend chart không phải "lịch sử", để nguyên — xem audit-report.md.
- [x] A4. Xác định nguồn dữ liệu đúng cho lịch sử đơn thuốc (endpoint trả **tất cả** đơn của lượt khám,
      kể cả đã hủy) thay vì dùng lại `getVisitPrescription`. → `doctorApi.getVisitPrescriptions` (đã có
      sẵn từ TASK-145), không cần hàm mới như plan đề xuất.

### B. Sửa hiển thị

- [x] B1. Tab Đơn thuốc hiển thị **mọi** đơn của từng lượt khám, kể cả `cancelled`, sắp theo thời gian.
- [x] B2. Đơn đã hủy hiển thị rõ: trạng thái, **thời điểm hủy**, **lý do hủy**. Người hủy: KHÔNG hiện trên
      UI trong đợt này — nhưng **actor đã tồn tại** (`AuditedMixin.updated_by`, `base_model.py:79`, được
      set ở cả 3 luồng: `prescription_service.cancel` → `updated_by`, `invoice_service.void_invoice` →
      `updated_by`, `invoice_service.refund_invoice` → `updated_by`; cộng với `audit_log` từ TASK-145 bật
      `__auditable__` trên Prescription/Invoice/Payment). **Không cần migration.** Lý do hoãn hiển thị là
      hiển thị TÊN đọc được cần lookup `user_id → full_name`, mà màn hồ sơ bệnh nhân hiện không có quyền
      `user.manage` để gọi — xem F4, audit-report.md. Correction (review iteration 1, M-B2): bản audit ban
      đầu ghi sai lý do là "không có cột actor, cần migration" — đã sửa lại đúng ở đây và ở
      audit-report.md; đề xuất task follow-up cho việc resolve tên. Phân biệt trực quan (line-through +
      opacity-50, D-2) với đơn còn hiệu lực — review MAJOR-3: giới hạn phạm vi áp dụng ở từng ô dữ liệu
      (identity/ngày/số lượng), KHÔNG áp lên cả `<tr>`, để lý do hủy luôn đọc được rõ ràng.
- [x] B3. **Không đụng vào màn khám của bác sĩ** — `getVisitPrescription` giữ nguyên hành vi hiện tại cho
      màn đó (test AC4 khẳng định); tách nguồn dữ liệu riêng cho lịch sử (`getVisitPrescriptions`).
- [x] B4. Hóa đơn `void`/`refunded` hiện kèm lý do; bổ sung `voided_at`/`void_reason`/`refunded_at`/
      `refund_reason` vào `InvoiceSummaryResponse` + fix `patient_id` filter (phát hiện thêm khi làm B4).
- [x] B5. Xử lý giới hạn phân trang tìm thấy ở A3 — đọc `total`, nút "Xem thêm" thay vì cắt im lặng, ở cả
      VisitsTab, PrescriptionsTab, InvoicesTab.
- [x] B6. Mỗi lượt khám trong lịch sử liên kết được sang đơn thuốc / hóa đơn của chính nó — dòng đơn thuốc
      link sang `/visits/{id}`, dòng hóa đơn link sang `/billing/invoices/{id}`.

### C. E2E luồng khám sai → hủy → cấp lại

- [x] C1. Spec mới `e2e/regression/visit-correction-full-flow.spec.ts` — **một lượt khám duy nhất**, chạy
      liền mạch trên UI thật, không stub. → committed `b2e6301` on `_feat146-web`.
- [x] C2. Kịch bản: tiếp nhận bệnh nhân → tạo lượt khám → bác sĩ kê **sai** thuốc + chọn **sai** dịch vụ →
      phát hành hóa đơn → phát hiện sai → hủy hóa đơn → hủy đơn thuốc → kê lại đơn đúng → phát hành lại
      hóa đơn → thanh toán → **mở hồ sơ bệnh nhân kiểm tra lịch sử**. → PASS, observed clean multiple
      times; see `deliveries/test-reports/test-report.md` run history for the full honest account.
- [x] C3. Kiểm chứng cả UI lẫn dữ liệu: tồn kho về đúng, tiền về đúng, và lịch sử hiển thị **cả** bản ghi
      đã hủy lẫn bản ghi thay thế. → verified via UI + direct API reads (stock poll, paid_total/
      balance_due, void_reason/cancel_reason).
- [x] C4. Toàn bộ spec PASS; báo cáo tại `deliveries/test-reports/`. → 11/11 tests each observed passing
      cleanly across the session (not all 11 in one single final run — see report for why: session-volume
      side effect BUG-146-01 (visit_number `lpad` truncation past 999/day), not a defect in the feature
      under test).

## Acceptance Criteria

- [x] **AC1** — Lượt khám có 1 đơn đã hủy + 1 đơn thay thế: tab Đơn thuốc hiện **cả hai**, đúng thứ tự
      thời gian, đơn hủy ghi rõ lý do và thời điểm. Verified: unit test (component-level, mocked API);
      real-UI E2E verification is Test Agent's job (C2/AC5).
- [x] **AC2** — Lượt khám có hóa đơn đã hủy + hóa đơn phát hành lại: tab Hóa đơn hiện cả hai, kèm lý do hủy.
      Verified: unit test + integration test (patient_id filter); E2E pending Test Agent.
- [x] **AC3** — Không nhầm lẫn: đơn/hóa đơn đã hủy phân biệt rõ về mặt thị giác với bản còn hiệu lực.
      Verified: unit test asserts `line-through` + `opacity-50` classes present/absent as expected.
- [x] **AC4** — Màn khám của bác sĩ **không đổi hành vi**: vẫn chỉ nạp đơn đang hiệu lực để chỉnh sửa.
      Verified: `getVisitPrescription` untouched (diff has zero changes to it) + new regression test
      (`src/tests/doctor/api.test.ts`) proves it still filters cancelled entries and returns only the
      newest active one.
- [x] **AC5** — Luồng E2E C2 chạy trọn vẹn, mọi bước pass. Verified real-UI, real API, multiple runs.
- [x] **AC6** — Sau luồng C2: tồn kho thuốc về đúng số ban đầu (thuốc kê sai đã trả kho), tiền thu khớp
      đúng hóa đơn mới, không còn dư nợ treo. Verified via polled stock read + `paid_total`/
      `balance_due`/`grand_total` API checks.
- [x] **AC7** — Bệnh nhân có nhiều lượt khám: lịch sử hiện đủ, không bị cắt bởi giới hạn phân trang.
      Verified against 55 real visits (VisitsTab), the MAJOR-2 empty-first-page scenario
      (PrescriptionsTab), and the fixed-offset network check (InvoicesTab).
- [x] **AC8** — Không hồi quy: `cancel-adjust-flow.spec.ts` (TASK-145) và các spec regression hiện có
      vẫn PASS. 19/20 in `cancel-adjust-flow.spec.ts` (the 1 failure is pre-existing, TASK-146-unrelated
      copy drift — BUG-146-02); `billing.spec.ts`, `prescription.spec.ts`,
      `smoke/pharmacy-dispense.spec.ts`, `smoke/cashier-invoice.spec.ts` all clean.

## Progress Checklist

- [x] Rà soát (mục A) → `handoff/audit-report.md`
- [x] Implementation (mục B)
- [x] Code Review — iteration 1: CHANGES_REQUESTED (4 MAJOR, see handoff/review-report.md)
- [x] Fix round 1 — 4 MAJOR + M-B2 doc correction + A1 (VisitsTab) completed + MINOR 1/4/5/6/7 → see
      `handoff/implementation-to-review.md` FIX ROUND section. Re-submitted for review iteration 2.
- [x] Code Review — iteration 2: **APPROVED**. All 4 MAJOR closed (MAJOR-2/MAJOR-3 mutation-verified:
      the defect was reintroduced and the new tests went red, then restored). M-B2 + A1 doc
      corrections accepted; the implementer's correction on `assigned_doctor_id` is right and my
      round-1 claim was wrong. MINOR 1/4/5/6/7 fixed; MINOR 2/3 deferrals accepted; 5 new non-blocking
      observations (R2-1..R2-5) recorded for the Test Agent. See `handoff/review-report.md` (ROUND 2)
      and `handoff/review-to-test.md`.
- [x] Testing (mục C) — E2E C1–C4 + AC5–AC8, plus the 4 things unit tests cannot prove:
      cancelled-row rendering in both themes, print-button suppression in the real UI, offset
      pagination across real pages, and the `patient_id` fix end-to-end in the chart. All PASS.
      3 pre-existing (not TASK-146) bugs found and filed: BUG-146-01 (`fn_next_visit_number`'s `lpad`
      truncates past 999 visits/clinic/day, causing this session's own visit-creation 500s under heavy
      test volume), BUG-146-02 (stale banner-copy assertion in TASK-145's spec), BUG-146-04 (no UI
      submit action for draft prescriptions). See `deliveries/test-reports/test-report.md`.
- [x] Documentation — Complete:
      * Functional design: `docs/tasks/TASK-146/deliveries/final-specs/lich-su-kham-benh-nhan-functional-design.md`
      * API specs: `docs/tasks/TASK-146/deliveries/api-specs/visits-list.md`, `visit-prescriptions-list.md`, `invoices-list.md`
      * Architectural decisions: `docs/architecture/decisions/adr-patient-id-filter-discovery-pattern.md`, `adr-api-function-naming-singular-vs-plural.md`
      * Follow-ups filed: `docs/tasks/follow-ups/task146-followups-2026-09-01.md` (5 pre-existing bugs, 2 deferred enhancements, 1 spec maintainability issue)

## Related Files

- **Code (FE)**: `clinic-cms-web/src/pages/patients/PatientDetailPage.tsx`, `src/modules/doctor/api.ts`
- **Code (BE)**: `clinic-cms/app/modules/prescriptions/`, `app/modules/billing/` (nếu cần endpoint lịch sử)
- **Tests**: `clinic-cms-web/e2e/regression/visit-correction-full-flow.spec.ts`
- **Handoffs**: `docs/tasks/TASK-146/handoff/`
- **Test Report**: `docs/tasks/TASK-146/deliveries/test-reports/test-report.md`

## Timestamps

- **Created**: 2026-08-31
- **Implementation Completed**: 2026-08-31
- **Testing Completed**: 2026-09-01

## Notes

- Task này là hệ quả trực tiếp của TASK-145: đã cho phép hủy thì lịch sử phải kể lại được việc đã hủy.
- **Cạm bẫy chính**: `getVisitPrescription` phục vụ màn khám của bác sĩ. Sửa thẳng vào nó sẽ làm hỏng
  màn khám (bác sĩ sẽ thấy cả đơn đã hủy khi chỉnh sửa). Phải tách nguồn dữ liệu, xem B3/AC4.
- Worktree code mới nhất: `_dev-be` / `_dev-web` (branch `dev`, đã có TASK-145 + TASK-142).
- Docker Desktop trên máy này hay sập; **chỉ chạy một stack test tại một thời điểm**. Không đụng container
  `adn-*` của môi trường khác.
- E2E: API host port 9999; demo creds xem memory `clinic-cms-local-ports`.

## Quyết định đã chốt (2026-08-31, trước khi implement)

Hai điểm mở trong `refs/implementation-plan.md` đã được chốt để không chặn implement.
**Review agent cần thẩm định lại cả hai.**

- **D-1 — Đơn `draft` KHÔNG hiện trong lịch sử; đơn `cancelled` CÓ hiện.**
  Lý do: `draft` là đơn náp chưa từng có hiệu lực, chưa gửi nhà thuốc, không phản ánh việc gì đã xảy ra
  với bệnh nhân — hiện lên chỉ gây nhiễu. `cancelled` thì ngược lại: nó ghi lại một sự kiện có thật
  (đã kê rồi hủy), là thông tin lâm sàng cần truy vết.
  Lưu ý: `get_by_visit` trả cả `draft`, nên việc lọc `draft` phải làm ở tầng hiển thị lịch sử.

- **D-2 — Phân biệt thị giác theo mẫu sẵn của `InvoiceDetailPage`** (payment đã hủy:
  `line-through` + `opacity-50`), thay vì nghĩ ra cách mới — để toàn hệ thống nhất quán một ngôn ngữ
  thị giác cho "bản ghi đã hủy".

## Blockers

None
