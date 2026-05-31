---
id: BUG-014
title: Pharmacy "Dispense" button không trigger gì — onClick handler missing/broken
severity: Critical
status: OPEN
discovered_in: TASK-049 Phase 5 — pharmacist click Dispense trên đơn pending
url: http://localhost:1420/#/pharmacy/pending
---

# BUG-014: Pending Dispense — Dispense button broken

## Symptom
Login pharmacist (`pharm_cuong` / `Pharm@1234`), navigate to `Pharmacy → Pending Dispense`. Đơn vừa kê (`Rx 378b8aaa-...`) hiện trong queue. Click button "Dispense" → **không có gì xảy ra**:
- Không network call (chỉ polling GET `/pharmacy/pending-dispense`)
- Không URL change
- Không modal/dialog
- Không toast
- Không console error mới

Click qua DOM JS trực tiếp (`btn.click()`) cũng không trigger. Button có class hover state đẹp + `hasOnClick` truthy nhưng handler không thực sự gọi API.

## Repro
1. Doctor kê đơn cho 1 visit + Save
2. Login `pharm_cuong` / `Pharm@1234`
3. Navigate `/#/pharmacy/pending`
4. Click "Dispense" trên 1 đơn
5. → Không response

## Impact (CRITICAL)
- 100% block luồng Pharmacy Phase 5
- Đơn không thể dispense → tồn kho không cập nhật → hóa đơn không gen → BLOCK toàn workflow KCB end-to-end
- Real clinic không dùng được pharmacy module

## Files involved (estimated)
- `clinic-cms-web/src/pages/pharmacy/PendingDispensePage.tsx` (or similar)
- Mutation hook `useDispensePrescription` hoặc `useStartDispense`

## Hypothesis
1. Handler attach bị lỗi (button không có onClick prop wired đúng)
2. Mutation fail silently (catch swallow error, no toast)
3. Permission/state guard return early without UI feedback
4. FE chưa implement — placeholder Dispense button (dạng Beta) chưa wire route đến detail page

## Suggested investigation
- Inspect `<button>` element trong DevTools React — coi prop `onClick` thực sự là function nào
- Set breakpoint trước fetch dispense
- Check FE code: tìm `onClick={...}` trên Dispense button trong pharmacy pages

## Related
- TASK-020 FE Pharmacy (Pending Dispense + Substitute Batch + Inventory + Stock Adjustment) — Pending Dispense module gốc
- TASK-040 Phase D screens port — pharmacy stocktake/expiry — không phải dispense
- TASK-048 Beta cleanup — có thể button "Dispense" là Beta placeholder chưa hoàn thiện

## Workaround (temporary cho test E2E)
Có thể test BE dispense API trực tiếp:
```bash
curl -X POST http://localhost:8001/api/v1/prescriptions/{id}/dispense \
  -H "Authorization: Bearer ..." \
  -H "X-Clinic-Id: ..."
```
Nếu BE OK thì confirm pure FE bug.
