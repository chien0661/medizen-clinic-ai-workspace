"""
E2E — toàn bộ luồng khám bệnh, tập trung vào mắt xích bị đứt ở TASK-147.

Chạy trên stack E2E isolated (docker-compose.e2e.yml, build từ _dev-be/_dev-web):
    python -X utf8 docs/tasks/TASK-147/deliveries/test-cases/e2e_clinical_flow.py

Luồng, mỗi bước bằng đúng role thật:
    recept_anh  tạo bệnh nhân + lượt khám
    dr_nguyen   bắt đầu khám → sinh hiệu → kê đơn thuốc NỘI VIỆN
    (guard)     cấp phát khi đơn còn 'draft' phải bị chặn 400
    (guard)     hàng đợi Chờ cấp phát KHÔNG được chứa đơn 'draft'
    dr_nguyen   GỬI ĐƠN (draft → pending)  ← mắt xích TASK-147 vá
    (guard)     hàng đợi Chờ cấp phát BÂY GIỜ phải chứa đơn
    pharm_cuong cấp phát → tồn kho giảm + có stock_movement
    dr_nguyen   hoàn tất khám (complete-emr)
    cashier_em  phát hành hóa đơn + thu tiền
    (gate)      lượt khám đóng được (COMPLETED)

Exit code 0 = toàn bộ PASS.
"""
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request

# 127.0.0.1, not localhost: on this Windows box Python resolves "localhost" to
# IPv6 ::1 first and hangs there (8s timeout) while the Docker port mapping only
# listens on IPv4 — curl falls back, urllib does not.
BASE = "http://127.0.0.1:8010/api/v1"
TIMEOUT = 20

CREDS = {
    "recept_anh": "Recept@1234",
    "dr_nguyen": "Doctor@1234",
    "pharm_cuong": "Pharm@1234",
    "cashier_em": "Cashier@1234",
    "admin": "Demo@1234",
}

# Pin a proxy-less opener so a machine-wide HTTP_PROXY cannot intercept these
# loopback calls.
_opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

_tokens: dict[str, str] = {}
_users: dict[str, dict] = {}
_results: list[tuple[str, str, str]] = []  # (status, step, msg)


def rec(status: str, step: str, msg: str) -> None:
    icon = {"PASS": "[PASS]", "FAIL": "[FAIL]", "INFO": "[ ** ]"}[status]
    _results.append((status, step, msg))
    print(f"  {icon} {step}: {msg}", flush=True)


def fail(step: str, msg: str) -> None:
    rec("FAIL", step, msg)


def req(method: str, path: str, user: str | None = None, body=None, expect=None):
    """Return (status_code, parsed_body). Never raises on HTTP error status."""
    url = BASE + path
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(url, data=data, method=method)
    r.add_header("Content-Type", "application/json")
    if user:
        r.add_header("Authorization", f"Bearer {_tokens[user]}")
    try:
        with _opener.open(r, timeout=TIMEOUT) as resp:
            code, raw = resp.status, resp.read()
    except urllib.error.HTTPError as e:
        code, raw = e.code, e.read()
    except Exception as e:  # network/stack down
        return 0, {"error": str(e)}
    try:
        parsed = json.loads(raw) if raw else {}
    except Exception:
        parsed = {"raw": raw[:400].decode(errors="replace")}
    if expect is not None and code not in expect:
        print(f"       ! {method} {path} → {code} (mong {expect}): {json.dumps(parsed)[:300]}")
    return code, parsed


def d(body):
    """Unwrap the {"data": ...} envelope."""
    if isinstance(body, dict) and "data" in body:
        return body["data"]
    return body


def login(user: str) -> bool:
    code, body = req("POST", "/auth/login", body={"username": user, "password": CREDS[user]})
    if code != 200:
        fail("login", f"{user} → {code} {json.dumps(body)[:200]}")
        return False
    payload = d(body)
    _tokens[user] = payload["access_token"]
    _users[user] = payload["user"]
    return True


def items_of(body):
    p = d(body)
    if isinstance(p, list):
        return p
    for k in ("items", "data", "results"):
        if isinstance(p, dict) and isinstance(p.get(k), list):
            return p[k]
    return []


# ──────────────────────────────────────────────────────────────────────────────
def main() -> int:
    print("\n=== E2E luồng khám bệnh — TASK-147 ===\n")

    print(f"--- 0. Đăng nhập ({len(CREDS)} role) ---")
    for u in CREDS:
        if not login(u):
            print("\nKhông đăng nhập được — dừng.")
            return 1
        time.sleep(0.3)  # tránh 429
    rec("PASS", "0", f"đăng nhập OK: {', '.join(CREDS)}")

    # ── 1. Bệnh nhân + lượt khám ────────────────────────────────────────────
    print("\n--- 1. Lễ tân: tạo bệnh nhân + lượt khám ---")
    ts = int(time.time())
    code, body = req(
        "POST", "/patients", "recept_anh",
        {"full_name": f"BN TASK147 {ts}", "phone": f"09{ts % 100000000:08d}",
         "date_of_birth": "1990-03-15", "gender": "male"},
        expect=(200, 201),
    )
    if code not in (200, 201):
        fail("1a", f"tạo bệnh nhân → {code}")
        return 1
    patient_id = d(body)["id"]
    rec("PASS", "1a", f"bệnh nhân {patient_id}")

    code, body = req("POST", "/visits", "recept_anh",
                     {"patient_id": patient_id, "priority": 0}, expect=(200, 201))
    if code not in (200, 201):
        fail("1b", f"tạo lượt khám → {code} {json.dumps(body)[:200]}")
        return 1
    visit = d(body)
    visit_id = visit["id"]
    rec("PASS", "1b", f"lượt khám {visit.get('visit_number')} status={visit.get('status')}")

    # ── 2. Bác sĩ bắt đầu khám ──────────────────────────────────────────────
    print("\n--- 2. Bác sĩ: bắt đầu khám ---")
    code, body = req("POST", f"/visits/{visit_id}/start", "dr_nguyen", {}, expect=(200, 201, 204))
    if code not in (200, 201, 204):
        fail("2", f"start → {code} {json.dumps(body)[:200]}")
        return 1
    rec("PASS", "2", f"lượt khám → {d(body).get('status') if isinstance(d(body), dict) else 'IN_PROGRESS'}")

    # ── 3. Chọn thuốc còn tồn kho ───────────────────────────────────────────
    print("\n--- 3. Chọn thuốc nội viện còn tồn ---")
    # GET /medicines là danh mục thuần, không mang tồn kho (in_stock và
    # stock_status trả về None) — tồn kho thật đọc từ /inventory/stock-status.
    code, body = req("GET", "/inventory/stock-status?limit=200", "pharm_cuong", expect=(200,))
    rows = items_of(body)
    med = next((r for r in rows if float(r.get("available_qty") or 0) >= 5), None)
    if med is None:
        fail("3", f"không có thuốc nào còn tồn >=5 trong {len(rows)} dòng tồn kho")
        return 1
    med_id = med["medicine_id"]
    rec("PASS", "3", f"thuoc: {med.get('medicine_name')} ton={med.get('total_qty')} "
                     f"kha_dung={med.get('available_qty')} id={med_id}")

    # ── 4. Kê đơn nội viện ──────────────────────────────────────────────────
    print("\n--- 4. Bác sĩ: kê đơn NỘI VIỆN ---")
    code, body = req(
        "POST", f"/visits/{visit_id}/prescriptions", "dr_nguyen",
        {"doctor_id": _users["dr_nguyen"]["id"],
         "notes": "E2E TASK-147",
         "items": [{
             "medicine_id": med_id,
             "medicine_name": med.get("medicine_name", "Thuốc E2E"),
             "dosage": "1 viên x 2 lần/ngày",
             "quantity": 2,
             "unit": med.get("base_unit") or "viên",
             "dispense_source": "in_house",
         }]},
        expect=(200, 201),
    )
    if code not in (200, 201):
        fail("4", f"kê đơn → {code} {json.dumps(body)[:300]}")
        return 1
    rx = d(body)
    rx_id = rx["id"]
    rx_items = rx.get("items", [])
    src = rx_items[0].get("dispense_source") if rx_items else "?"
    ihs = rx_items[0].get("in_house_status") if rx_items else "?"
    rec("PASS", "4a", f"đơn {rx_id} status={rx.get('status')} source={src} in_house_status={ihs}")
    if rx.get("status") != "draft":
        fail("4b", f"đơn mới phải ở 'draft', thực tế '{rx.get('status')}'")
    else:
        rec("PASS", "4b", "đơn mới ở 'draft' như thiết kế")
    if src != "in_house":
        fail("4c", f"item phải là in_house để test cấp phát, thực tế '{src}'")
        return 1

    # ── 5. GUARD: cấp phát đơn 'draft' phải bị chặn ─────────────────────────
    print("\n--- 5. GUARD TASK-142: cấp phát đơn 'draft' ---")
    code, body = req("POST", f"/pharmacy/dispense/{rx_id}", "pharm_cuong", {})
    err = (body or {}).get("error", {})
    if code == 400 and err.get("code") == "BUSINESS_RULE_VIOLATION":
        rec("PASS", "5", f"bị chặn đúng 400: {err.get('message', '')[:110]}")
    else:
        fail("5", f"đơn 'draft' cấp phát được / sai lỗi → {code} {json.dumps(body)[:250]}")

    # ── 6. GUARD: hàng đợi không chứa đơn draft ─────────────────────────────
    print("\n--- 6. GUARD: hàng đợi Chờ cấp phát khi đơn còn 'draft' ---")
    code, body = req("GET", "/pharmacy/pending-dispense", "pharm_cuong", expect=(200,))
    queue = items_of(body)
    in_queue = [q for q in queue if q.get("prescription_id") == rx_id]
    if in_queue:
        fail("6", f"đơn 'draft' lọt vào hàng đợi ({len(queue)} dòng)")
    else:
        rec("PASS", "6", f"đơn 'draft' không lọt hàng đợi ({len(queue)} dòng khác)")

    # ── 7. MẮT XÍCH TASK-147: bác sĩ GỬI ĐƠN ───────────────────────────────
    print("\n--- 7. TASK-147: bác sĩ GỬI ĐƠN (draft → pending) ---")
    code, body = req("POST", f"/prescriptions/{rx_id}/submit", "dr_nguyen", {}, expect=(200, 201))
    if code not in (200, 201):
        fail("7", f"submit → {code} {json.dumps(body)[:300]}")
        return 1
    if d(body).get("status") != "pending":
        fail("7", f"sau submit phải 'pending', thực tế '{d(body).get('status')}'")
    else:
        rec("PASS", "7", "đơn → 'pending'")

    # ── 8. Hàng đợi bây giờ phải thấy đơn ───────────────────────────────────
    print("\n--- 8. Hàng đợi Chờ cấp phát sau khi gửi ---")
    code, body = req("GET", "/pharmacy/pending-dispense", "pharm_cuong", expect=(200,))
    queue = items_of(body)
    row = next((q for q in queue if q.get("prescription_id") == rx_id), None)
    if row is None:
        fail("8", f"đơn 'pending' KHÔNG xuất hiện trong hàng đợi ({len(queue)} dòng)")
    else:
        rec("PASS", "8", f"hàng đợi thấy đơn: BN={row.get('patient_name')} "
                         f"BS={row.get('doctor_name')} sl_giữ={row.get('total_reserved')}")

    # ── 9. Dược sĩ cấp phát → tồn kho giảm ──────────────────────────────────
    print("\n--- 9. Dược sĩ: cấp phát ---")
    def stock_now():
        c, bd = req("GET", "/inventory/stock-status?limit=200", "pharm_cuong")
        if c != 200:
            return None
        row = next((r for r in items_of(bd) if r.get("medicine_id") == med_id), None)
        return float(row.get("total_qty") or 0) if row else None

    stock_before = stock_now()

    code, body = req("POST", f"/pharmacy/dispense/{rx_id}", "pharm_cuong", {}, expect=(200, 201))
    if code not in (200, 201):
        fail("9a", f"cấp phát → {code} {json.dumps(body)[:300]}")
        return 1
    rec("PASS", "9a", "cấp phát OK")

    code, body = req("GET", f"/prescriptions/{rx_id}", "pharm_cuong", expect=(200,))
    if d(body).get("status") != "dispensed":
        fail("9b", f"sau cấp phát đơn phải 'dispensed', thực tế '{d(body).get('status')}'")
    else:
        rec("PASS", "9b", "đơn → 'dispensed'")

    if stock_before is not None:
        stock_after = stock_now()
        if stock_after is None:
            rec("INFO", "9c", "không đọc lại được tồn kho")
        elif stock_after < stock_before:
            rec("PASS", "9c", f"tồn kho giảm {stock_before} → {stock_after}")
        else:
            fail("9c", f"tồn kho KHÔNG giảm: {stock_before} → {stock_after}")
    else:
        rec("INFO", "9c", "không đọc được tồn kho trước khi cấp phát")

    # Không có endpoint nào expose stock_movement, nên kiểm ở tầng DB.
    # Bỏ qua (INFO) nếu không gọi được docker.
    sql = (
        "SELECT movement_type||' '||quantity_delta||' '||quantity_before"
        "||'->'||quantity_after FROM stock_movement WHERE reference_id='" + rx_id + "';"
    )
    try:
        out = subprocess.run(
            ["docker", "exec", "clinic_e2e_postgres", "psql", "-U", "cms", "-d", "cms",
             "-t", "-A", "-c", sql],
            capture_output=True, text=True, timeout=30,
        )
        rows = [ln.strip() for ln in out.stdout.splitlines() if ln.strip()]
    except Exception as e:
        rows, out = [], None
        rec("INFO", "9d", f"không kiểm được stock_movement qua docker: {e}")
    if rows:
        rec("PASS", "9d", f"stock_movement: {'; '.join(rows)}")
    elif out is not None:
        fail("9d", f"không có stock_movement nào tham chiếu đơn {rx_id}"
                   f"{' — ' + out.stderr.strip()[:120] if out.stderr.strip() else ''}")

    # ── 10. Bác sĩ hoàn tất khám ────────────────────────────────────────────
    print("\n--- 10. Bác sĩ: hoàn tất khám ---")
    code, body = req("POST", f"/visits/{visit_id}/complete-emr", "dr_nguyen", {})
    if code in (200, 201, 204):
        rec("PASS", "10", f"complete-emr OK → {d(body).get('status') if isinstance(d(body), dict) else code}")
    else:
        rec("INFO", "10", f"complete-emr → {code} {json.dumps(body)[:200]}")

    # ── 11. Thu ngân: hóa đơn + thu tiền ────────────────────────────────────
    print("\n--- 11. Thu ngân: hóa đơn + thu tiền ---")
    code, body = req("GET", f"/visits/{visit_id}/invoices", "cashier_em")
    inv = next(iter(items_of(body)), None)
    if inv is None:
        code, body = req("POST", f"/visits/{visit_id}/invoices", "cashier_em", {}, expect=(200, 201))
        inv = d(body) if code in (200, 201) else None
    if inv is None:
        fail("11a", "không lấy/tạo được hóa đơn")
        return 1
    inv_id = inv["id"]
    rec("PASS", "11a", f"hóa đơn {inv_id} status={inv.get('status')} tổng={inv.get('grand_total')}")

    if inv.get("status") == "draft":
        code, body = req("POST", f"/invoices/{inv_id}/submit", "cashier_em", {}, expect=(200, 201))
        if code in (200, 201):
            inv = d(body)
            rec("PASS", "11b", f"phát hành → {inv.get('status')}")
        else:
            fail("11b", f"phát hành → {code} {json.dumps(body)[:200]}")

    balance = float(inv.get("balance_due") or inv.get("grand_total") or 0)
    if balance > 0:
        code, body = req("POST", f"/invoices/{inv_id}/payments", "cashier_em",
                         {"payment_method": "cash", "amount": str(balance)}, expect=(200, 201))
        if code in (200, 201):
            rec("PASS", "11c", f"thu {balance:,.0f}đ OK")
        else:
            fail("11c", f"thu tiền → {code} {json.dumps(body)[:250]}")
    else:
        rec("INFO", "11c", "hóa đơn 0đ — không cần thu")

    # ── 12. Cổng đóng lượt khám ─────────────────────────────────────────────
    print("\n--- 12. Cổng hoàn tất lượt khám ---")
    code, body = req("GET", f"/visits/{visit_id}/completion-blockers", "dr_nguyen")
    blockers = (d(body) or {}).get("blockers", []) if code == 200 else ["(không đọc được)"]
    if blockers:
        rec("INFO", "12a", f"còn chặn: {blockers}")
    else:
        rec("PASS", "12a", "không còn gì chặn")

    code, body = req("GET", f"/visits/{visit_id}", "dr_nguyen", expect=(200,))
    status = d(body).get("status")
    if status == "COMPLETED":
        rec("PASS", "12b", "lượt khám đã COMPLETED (tự đóng)")
    else:
        code2, body2 = req("POST", f"/visits/{visit_id}/complete", "dr_nguyen", {})
        if code2 in (200, 201, 204):
            code, body = req("GET", f"/visits/{visit_id}", "dr_nguyen", expect=(200,))
            status = d(body).get("status")
            if status == "COMPLETED":
                rec("PASS", "12b", "lượt khám → COMPLETED")
            else:
                fail("12b", f"sau complete vẫn '{status}'")
        else:
            fail("12b", f"đóng lượt khám → {code2} {json.dumps(body2)[:250]} (đang '{status}')")

    # ── Tổng kết ────────────────────────────────────────────────────────────
    p = sum(1 for s, _, _ in _results if s == "PASS")
    f = sum(1 for s, _, _ in _results if s == "FAIL")
    i = sum(1 for s, _, _ in _results if s == "INFO")
    print(f"\n=== KẾT QUẢ: {p} PASS / {f} FAIL / {i} INFO ===")
    if f:
        print("\nCác bước FAIL:")
        for s, step, msg in _results:
            if s == "FAIL":
                print(f"  - {step}: {msg}")
    print(f"\nvisit_id={visit_id}  prescription_id={rx_id}")
    return 1 if f else 0


if __name__ == "__main__":
    sys.exit(main())
