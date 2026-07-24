# TASK-106: Fix doctor-performance Cartesian product — khôi phục visits_count/revenue chính xác

**Mức độ:** High (H-4)  
**Ngày hoàn thành:** 2026-07-24  
**Trạng thái:** DONE (51/51 tests passed)

---

## Vấn đề

API `doctor-performance` report nhân bản dữ liệu qua phép join Cartesian.

**Kỳ vọng:**
- `visits_count` = số visit distinct
- `gross_revenue` = sum(grand_total) per invoice (một lần/invoice)

**Thực tế — SQL gốc:**
```sql
SELECT v.doctor_id,
       COUNT(v.id) AS visits_count,           -- ← bị nhân
       SUM(i.grand_total) AS gross_revenue   -- ← bị nhân
FROM visit v
LEFT JOIN invoice i ON i.visit_id = v.id
LEFT JOIN prescription p ON p.visit_id = v.id
GROUP BY v.doctor_id
```

Khi visit có 1 invoice + 3 prescriptions → join tạo 3 rows (1 visit × 3 prescriptions):
- `COUNT(v.id)` = 3 (thay vì 1) ✗
- `SUM(i.grand_total)` = 3× grand_total (thay vì 1×) ✗
- `COUNT(DISTINCT p.id)` = 3 ✓ (protected bởi DISTINCT)

**Bằng chứng:** Thêm prescription thứ 2 (không tạo visit mới) → visits_count 7→8 (sai, should stay 7).

---

## Giải pháp: CTEs để pre-aggregate (1 row/visit)

**File:** `app/modules/reports/services/doctor_performance_service.py`  
**Hàm:** `get_doctor_performance()`

```sql
WITH invoice_agg AS (
    -- Pre-aggregate invoices: 1 row per visit_id
    SELECT visit_id,
           SUM(grand_total) FILTER (WHERE status IN ('paid', 'partially_paid')) AS revenue
    FROM invoice
    WHERE is_deleted = FALSE
    GROUP BY visit_id
),
prescription_agg AS (
    -- Pre-aggregate prescriptions: 1 row per visit_id
    SELECT visit_id,
           COUNT(*) AS prescription_count
    FROM prescription
    WHERE is_deleted = FALSE
    GROUP BY visit_id
)
SELECT
    v.doctor_id,
    u.username,
    COUNT(DISTINCT v.id) AS visits_count,                    -- ← now 1:1 join, COUNT DISTINCT defense-in-depth
    COUNT(DISTINCT v.id) FILTER (WHERE v.status = 'COMPLETED') AS completed_count,
    AVG(...) FILTER (...) AS avg_consultation_minutes,
    COALESCE(SUM(ia.revenue), 0) AS gross_revenue,
    COALESCE(SUM(pa.prescription_count), 0) AS prescription_count
FROM visit v
LEFT JOIN "user" u ON u.id = v.doctor_id
LEFT JOIN invoice_agg ia ON ia.visit_id = v.id      -- ← 1:1 join, no fan-out
LEFT JOIN prescription_agg pa ON pa.visit_id = v.id -- ← 1:1 join, no fan-out
WHERE ...
GROUP BY v.doctor_id, u.username
```

**Lợi ích:**
1. CTEs pre-aggregate → join visit sau đó là **1:1** (không fan-out).
2. `COUNT(DISTINCT v.id)` thêm defense-in-depth.
3. **Cũng fix** case multiple invoices/visit (latent bug với join trực tiếp).

**Kho thay đổi:**
- `doctor_performance_service.py` (+45/-17 lines, SQL rewritten, no API schema change)
- `test_reports_e2e.py` (+104 lines: `_seed_prescription()` helper, `visit_id` param on `_seed_invoice()`, 1 test mới)

---

## Kết quả

**Tests — Reproduction + Regression:**
- `test_doctor_performance_no_cartesian_overcount` (new): 2 visits, visit A (1 invoice 100k + 3 prescriptions) + visit B (1 invoice 50k) → visits_count=2 (✓ not 8), gross_revenue=150k (✓ not 350k)
- Pre-existing tests still pass → no regression on simple/no-invoice cases
- **Regression-proof:** Reverted SQL, test **failed** (confirmed bug real, not tautology)
- Reports suite: 13/13 integration + 6/6 unit = 19/19 (part of 51/51 full reports+unit suite)

**Isolated stack: `w106` (api 9977, postgres 5477, redis 6459)**

---

## Bằng chứng Fix

| Trường hợp | Trước fix | Sau fix | Status |
|------------|-----------|---------|--------|
| 1 visit, 1 invoice, 1 prescription | 1 | 1 | ✓ |
| 1 visit, 1 invoice, 3 prescriptions | 3 | 1 | ✓ Fix |
| 1 visit, 2 invoices | 2 | 1 | ✓ Fix (latent) |
| 2 visits, mixed invoices/prescriptions | overcounted | correct distinct | ✓ Fix |

**Ground truth:** `/api/v1/visits?doctor_id=X` count visits distinct → khớp post-fix `doctor-performance` visits_count.

---

## Ghi chú

- **Response schema không thay đổi** — chỉ data correctness inside aggregation query.
- **CTEs aggregate all invoices/prescriptions in DB**, sau đó LEFT JOIN visit set đã filter → không double-count (correct).
- **Optional follow-up:** Index on `invoice(visit_id WHERE is_deleted=FALSE)` + `prescription(visit_id WHERE is_deleted=FALSE)` để query planning nếu tables rất lớn (correctness OK, performance tuning).

---

## Xác minh

| Tiêu chí | Kết quả |
|----------|---------|
| Unit + Integration tests | 51/51 passed ✓ |
| Cartesian fix | visits_count/revenue correct distinct ✓ |
| No regression | pre-existing tests pass ✓ |
| Multiple invoices | latent bug fixed ✓ |
| Static analysis | 0 new findings ✓ |
| Isolated stack | w106 (api 9977, postgres 5477, redis 6459) ✓ |
| API response | unchanged (internal fix only) ✓ |
