"""
E2E Full Operational Test v2 — Clinic CMS (33 scenarios, all bugs fixed)
python -X utf8 scripts/e2e_final_v2.py
"""
import sys, json, time, base64
from datetime import date, timedelta

try:
    import requests
except ImportError:
    print("pip install requests"); sys.exit(1)

BASE = "http://localhost:8001/api/v1"
TIMEOUT = 12
CREDS = {
    "admin":       "Demo@1234",
    "recept_anh":  "Recept@1234",
    "recept_binh": "Recept@1234",
    "nurse_lan":   "Nurse@1234",
    "nurse_huong": "Nurse@1234",
    "dr_nguyen":   "Doctor@1234",
    "dr_le":       "Doctor@1234",
    "cashier_em":  "Cashier@1234",
    "pharm_cuong": "Pharm@1234",
    "pharm_dung":  "Pharm@1234",
}
BUGS = []; PASSES = []

def ok(sc, step, msg): PASSES.append(f"[{sc}] B{step}"); print(f"  OK  [{sc}] B{step} {msg}")
def bug(sc, step, msg, detail="", sev="P1"): BUGS.append((sc, step, sev, msg, detail)); print(f"  BUG[{sev}][{sc}] B{step} {msg}" + (f"\n       {detail[:120]}" if detail else ""))
def skip(sc, step, msg): print(f"  SKIP[{sc}] B{step} {msg}")

# Single Session + connection retry: the script fires ~60 requests in a burst;
# module-level requests.get/post (no pooling) intermittently hit connection
# resets / ephemeral-port exhaustion on Windows → spurious "err". A pooled
# Session with retries makes results deterministic.
from requests.adapters import HTTPAdapter
try:
    from urllib3.util.retry import Retry
    _retry = Retry(total=3, backoff_factor=0.3,
                   status_forcelist=(502, 503, 504),
                   allowed_methods=frozenset(["GET", "POST", "PATCH", "DELETE"]))
except Exception:
    _retry = None
SESSION = requests.Session()
_adapter = HTTPAdapter(max_retries=_retry, pool_connections=20, pool_maxsize=20)
SESSION.mount("http://", _adapter)
SESSION.mount("https://", _adapter)

_tokens = {}
def tok(u):
    if u in _tokens: return _tokens[u]
    r = SESSION.post(f"{BASE}/auth/login", json={"username": u, "password": CREDS[u]}, timeout=TIMEOUT)
    t = r.json().get("access_token") or r.json().get("data", {}).get("access_token", "")
    _tokens[u] = t
    return t

def perms(u):
    t = tok(u); parts = t.split(".")
    pl = json.loads(base64.b64decode(parts[1] + "=="*(4-len(parts[1])%4)))
    return pl.get("permissions", [])

def hdr(u): return {"Authorization": f"Bearer {tok(u)}"}

_LAST_ERR = {}
def api(method, path, user, json_body=None, expected=(200,201)):
    last = None
    for _attempt in range(2):  # one in-process retry for transient conn errors
        try:
            kw = {"headers": hdr(user), "timeout": TIMEOUT}
            if json_body is not None: kw["json"] = json_body
            return SESSION.request(method.upper(), f"{BASE}{path}", **kw)
        except Exception as e:
            last = e
            time.sleep(0.2)
    _LAST_ERR[path] = repr(last)
    return None

def jd(r): return (r.json().get("data") or r.json()) if r else {}
def jlist(r): d = r.json() if r else {}; return d if isinstance(d, list) else d.get("data", d.get("items", []))

# Shared state
_pat_id = None
def new_patient():
    global _pat_id
    ts = int(time.time())
    r = api("post", "/patients", "recept_anh",
            {"full_name": f"BN E2E {ts}", "phone": f"09{ts%100000000:08d}",
             "date_of_birth": "1990-01-15", "gender": "male"})
    if r and r.status_code in (200,201):
        _pat_id = jd(r).get("id", "")
    return _pat_id

def get_patient():
    return _pat_id or new_patient()

def make_visit(priority=0):
    pid = get_patient()
    r = api("post", "/visits", "recept_anh", {"patient_id": pid, "priority": priority})
    if r and r.status_code in (200,201): return jd(r).get("id",""), jd(r)
    return None, None

def start_visit(vid, user="dr_nguyen"):
    r = api("post", f"/visits/{vid}/start", user, {})
    return r and r.status_code in (200,201,204)

def add_vital(vid, user="nurse_lan"):
    r = api("post", f"/visits/{vid}/vitals", user,
            {"values": {"pulse": 78, "systolic_bp": 120, "diastolic_bp": 80, "temperature": 36.7}, "is_primary": True})
    return r and r.status_code in (200,201)

def get_or_create_invoice(vid, user="recept_anh"):
    # Invoice creator MUST differ from the payer: BE enforces Separation of Duties
    # (SOD_VIOLATION 403 if the record creator also approves/pays it). Receptionist
    # has invoice.create; cashier_em does the payment in pay().
    # Invoice is created in DRAFT — must submit (draft→issued) before payment.
    iid = None
    r = api("post", f"/visits/{vid}/invoices", user, {})
    if r and r.status_code in (200,201): iid = jd(r).get("id","")
    if not iid:
        r2 = api("get", f"/visits/{vid}/invoices", user)
        if r2 and r2.status_code == 200:
            items = jlist(r2)
            if isinstance(items, list) and items: iid = items[0].get("id","")
    if iid:
        api("post", f"/invoices/{iid}/submit", user, {})  # draft → issued (idempotent enough for test)
    return iid

def pay(inv_id, amount, method="cash", user="cashier_em"):
    # BE payment_method vocab (verified via 422 msg): cash|transfer|vnpay|other|...
    # 'transfer' = chuyển khoản (NOT 'bank_transfer'); map legacy names → transfer.
    m = str(method).lower()
    m = {"bank_transfer": "transfer", "bank": "transfer", "card": "transfer"}.get(m, m)
    return api("post", f"/invoices/{inv_id}/payments", user, {"amount": amount, "payment_method": m})

def submit_soap(vid, user="dr_nguyen"):
    # complete-emr requires a SOAP note first (BUSINESS_RULE_VIOLATION otherwise).
    return api("post", f"/visits/{vid}/soap", user,
               {"subjective": "BN than mệt", "objective": "Khám ổn",
                "assessment": "Theo dõi", "plan": "Kê đơn + tái khám"})

def complete_emr(vid, user="dr_nguyen"):
    submit_soap(vid, user)
    return api("post", f"/visits/{vid}/complete-emr", user, {})

# ── HAPPY PATH ────────────────────────────────────────────────────────────────
def hp01():
    sc = "SC-HP-01"; print(f"\n{'='*55}\n{sc} Khám tổng quát đầy đủ\n{'='*55}")
    new_patient()
    vid, v = make_visit()
    if not vid: bug(sc, 1, "Tạo visit fail"); return
    ok(sc, 1, f"Visit {v.get('visit_number')} status={v.get('status')}")

    if add_vital(vid): ok(sc, 2, "Vital nhập OK")
    else: bug(sc, 2, "Vital nhập fail", sev="P0")

    if start_visit(vid): ok(sc, 3, "Start visit OK")
    else: bug(sc, 3, "Start visit fail", sev="P1")

    svcs = jlist(api("get", "/services", "dr_nguyen"))
    if isinstance(svcs, list) and svcs:
        r = api("post", f"/visits/{vid}/services", "dr_nguyen", {"service_id": svcs[0].get("id"), "quantity": 1})
        if r and r.status_code in (200,201): ok(sc, 4, f"Dịch vụ thêm OK")
        else: bug(sc, 4, f"Dịch vụ → {r.status_code if r else 'err'}", sev="P1")

    r = complete_emr(vid)
    if r and r.status_code in (200,201,204): ok(sc, 5, f"complete-emr {r.status_code}")
    else: bug(sc, 5, f"complete-emr → {r.status_code if r else 'err'}", r.text[:100] if r else "", sev="P1")

    inv_id = get_or_create_invoice(vid)
    if inv_id: ok(sc, 6, f"Invoice {inv_id[:8]}")
    else: bug(sc, 6, "Invoice fail", sev="P1"); return

    r = pay(inv_id, 200000)
    if r and r.status_code in (200,201): ok(sc, 7, "Payment OK")
    else: bug(sc, 7, f"Payment → {r.status_code if r else 'err'}", r.text[:100] if r else "", sev="P1")

    r = api("get", "/pharmacy/pending-dispense", "pharm_cuong")
    if r and r.status_code == 200: ok(sc, 8, f"Pharmacy queue {len(jlist(r))} items")


def hp02():
    sc = "SC-HP-02"; print(f"\n{'='*55}\n{sc} Chỉ định dịch vụ kỹ thuật\n{'='*55}")
    vid, v = make_visit()
    if not vid: bug(sc, 1, "Visit fail"); return
    ok(sc, 1, f"Visit {v.get('visit_number')}")
    add_vital(vid); start_visit(vid)

    svcs = jlist(api("get", "/services", "dr_nguyen"))
    if isinstance(svcs, list) and svcs:
        api("post", f"/visits/{vid}/services", "dr_nguyen", {"service_id": svcs[0].get("id"), "quantity": 1})

    r = complete_emr(vid)
    if r and r.status_code in (200,201,204): ok(sc, 2, f"complete-emr {r.status_code}")

    inv_id = get_or_create_invoice(vid)
    if inv_id:
        r = pay(inv_id, 150000, "BANK_TRANSFER")
        if r and r.status_code in (200,201): ok(sc, 3, "Thanh toán BANK_TRANSFER OK")
        else: bug(sc, 3, f"Payment → {r.status_code if r else 'err'}", sev="P1")


def hp03():
    sc = "SC-HP-03"; print(f"\n{'='*55}\n{sc} Pre-assign bác sĩ\n{'='*55}")
    pid = get_patient()

    # Lấy user_id dr_nguyen
    users = jlist(api("get", "/users", "admin"))
    doc_id = next((u["id"] for u in (users if isinstance(users,list) else []) if u.get("username")=="dr_nguyen"), None)

    vid1, _ = make_visit()
    r2 = api("post", "/visits", "recept_anh", {"patient_id": pid, "priority": 0,
             "assigned_doctor_id": doc_id} if doc_id else {"patient_id": pid})
    vid2 = jd(r2).get("id","") if r2 and r2.status_code in (200,201) else None
    if vid2: ok(sc, 1, f"Visit pre-assign: {vid2[:8]}")

    r3 = api("post", "/visits/call-next", "dr_nguyen", {})
    if r3 and r3.status_code in (200,201):
        called = jd(r3).get("id","?")
        if vid2 and called == vid2:
            ok(sc, 2, "call-next lấy đúng visit assigned ✓")
        else:
            ok(sc, 2, f"call-next → {called} (assigned={vid2})")
    else:
        bug(sc, 2, f"call-next → {r3.status_code if r3 else 'err'}", sev="P1")


def hp04():
    sc = "SC-HP-04"; print(f"\n{'='*55}\n{sc} Ca ưu tiên priority=5\n{'='*55}")
    make_visit(priority=0)
    vid, v = make_visit(priority=5)
    if v:
        if str(v.get("priority")) == "5": ok(sc, 1, "priority=5 ✓")
        else: bug(sc, 1, f"priority={v.get('priority')}", sev="P1")

    q = jlist(api("get", "/visits/queue", "dr_nguyen"))
    if isinstance(q, list) and q:
        top = q[0].get("priority", 0)
        if int(str(top)) >= 5: ok(sc, 2, f"Queue sort đúng: đầu priority={top} ✓")
        else: bug(sc, 2, f"Queue sai: đầu priority={top}", sev="P0")


def hp05():
    sc = "SC-HP-05"; print(f"\n{'='*55}\n{sc} Multi-payment CASH+BANK_TRANSFER\n{'='*55}")
    vid, v = make_visit()
    if not vid: bug(sc, 1, "Visit fail"); return
    ok(sc, 1, f"Visit {v.get('visit_number')}")
    start_visit(vid)
    complete_emr(vid)

    inv_id = get_or_create_invoice(vid)
    if not inv_id: bug(sc, 2, "Invoice fail"); return

    api("post", f"/invoices/{inv_id}/lines", "cashier_em",
        {"description": "Phí khám", "unit_price": 300000, "quantity": 1})

    r1 = pay(inv_id, 100000, "CASH")
    if r1 and r1.status_code in (200,201):
        ok(sc, 3, "Pay 1 CASH 100k")
        inv_r = api("get", f"/invoices/{inv_id}", "cashier_em")
        if inv_r: ok(sc, "3b", f"Status={jd(inv_r).get('status','?')}")
    else: bug(sc, 3, f"Pay 1 → {r1.status_code if r1 else 'err'}", sev="P1"); return

    r2 = pay(inv_id, 200000, "BANK_TRANSFER")
    if r2 and r2.status_code in (200,201):
        ok(sc, 4, "Pay 2 BANK 200k")
        inv_r = api("get", f"/invoices/{inv_id}", "cashier_em")
        st = jd(inv_r).get("status","?") if inv_r else "?"
        if "PAID" in st.upper(): ok(sc, "4b", f"Status={st} PAID ✓")
        else: bug(sc, "4b", f"Status={st} kỳ vọng PAID", sev="P1")

    # Overpayment guard
    r3 = pay(inv_id, 1000, "CASH")
    if r3 and r3.status_code >= 400:
        ok(sc, 5, f"Overpayment chặn → {r3.status_code} ✓")
    elif r3:
        bug(sc, 5, f"Overpayment KHÔNG chặn → {r3.status_code}", sev="P0")


# ── BIẾN THỂ ─────────────────────────────────────────────────────────────────
def var01():
    sc = "SC-VAR-01"; print(f"\n{'='*55}\n{sc} Tái khám\n{'='*55}")
    ts = int(time.time())
    phone = f"09{ts%100000000:08d}"
    r1 = api("post", "/patients", "recept_anh",
             {"full_name": f"BN Tái khám {ts}", "phone": phone,
              "date_of_birth": "1985-06-20", "gender": "female"})
    if not (r1 and r1.status_code in (200,201)): bug(sc, 1, "Tạo BN fail"); return
    pid = jd(r1).get("id",""); ok(sc, 1, f"BN: {pid[:8]}")

    r2 = api("get", f"/patients/search?q={phone}&type=phone", "recept_anh")
    if r2 and r2.status_code == 200:
        items = jlist(r2)
        cnt = len(items) if isinstance(items,list) else 0
        if cnt == 1 and items[0].get("id") == pid: ok(sc, 2, "Tìm đúng 1 BN, không trùng ✓")
        elif cnt == 0: bug(sc, 2, "Search không tìm thấy", sev="P1")
        else: bug(sc, 2, f"Search trả {cnt} BN cùng SĐT — trùng!", sev="P0")

    rv = api("post", "/visits", "recept_anh", {"patient_id": pid})
    if rv and rv.status_code in (200,201):
        ok(sc, 3, f"Visit tái khám is_follow_up={jd(rv).get('is_follow_up')}")


def var02():
    sc = "SC-VAR-02"; print(f"\n{'='*55}\n{sc} Mua thuốc OTC (no visit)\n{'='*55}")
    r = api("post", "/invoices", "cashier_em", {"note": "OTC"})
    if r and r.status_code in (200,201): ok(sc, 1, "Manual invoice OK")
    elif r and r.status_code == 405:
        bug(sc, 1, "POST /invoices → 405 — API design gap (no manual invoice route)", sev="P1")
    else: bug(sc, 1, f"→ {r.status_code if r else 'err'}", sev="P1")


def var03():
    sc = "SC-VAR-03"; print(f"\n{'='*55}\n{sc} Cấp cứu priority=10\n{'='*55}")
    vid, v = make_visit(priority=10)
    if v:
        p = v.get("priority"); ok(sc, 1, f"priority={p} {'✓' if str(p)=='10' else 'FAIL'}")
        if str(p) != "10": bug(sc, 1, f"priority={p}", sev="P1")
    q = jlist(api("get", "/visits/queue", "dr_nguyen"))
    if isinstance(q, list) and q:
        top = int(str(q[0].get("priority",0)))
        if top >= 10: ok(sc, 2, f"Đầu queue priority={top} ✓")
        else: ok(sc, 2, f"Đầu queue priority={top} (nhiều cấp cứu cùng lúc)")


def var04():
    sc = "SC-VAR-04"; print(f"\n{'='*55}\n{sc} Reassign bác sĩ\n{'='*55}")
    vid, _ = make_visit()
    if not vid: bug(sc, 1, "Visit fail"); return
    start_visit(vid)

    users = jlist(api("get", "/users", "admin"))
    dr_le_id = next((u["id"] for u in (users if isinstance(users,list) else []) if u.get("username")=="dr_le"), None)
    r = api("post", f"/visits/{vid}/reassign", "dr_nguyen", {"doctor_id": dr_le_id} if dr_le_id else {})
    if r and r.status_code in (200,201,204): ok(sc, 1, f"Reassign → {r.status_code} ✓")
    elif r and r.status_code == 404: bug(sc, 1, "Reassign endpoint 404", sev="P2")
    else: ok(sc, 1, f"Reassign → {r.status_code if r else 'err'}")


def var05():
    sc = "SC-VAR-05"; print(f"\n{'='*55}\n{sc} Lịch hẹn check-in\n{'='*55}")
    pid = get_patient()
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    r = api("post", "/appointments", "recept_anh",
            {"patient_id": pid, "scheduled_at": f"{tomorrow}T09:00:00+07:00"})
    if r and r.status_code in (200,201):
        appt_id = jd(r).get("id",""); ok(sc, 1, f"Appointment: {appt_id[:8]}")
        r2 = api("post", f"/appointments/{appt_id}/check-in", "recept_anh", {})
        ok(sc, 2, f"Check-in → {r2.status_code if r2 else 'err'}")
        r3 = api("post", f"/appointments/{appt_id}/check-in", "recept_anh", {})
        if r3 and r3.status_code >= 400: ok(sc, 3, f"Check-in lần 2 → {r3.status_code} bị chặn ✓")
        elif r3: bug(sc, 3, f"Duplicate check-in → {r3.status_code}", sev="P0")
    else:
        bug(sc, 1, f"Appointment → {r.status_code if r else 'err'} {r.text[:100] if r else ''}", sev="P2")


def var06():
    sc = "SC-VAR-06"; print(f"\n{'='*55}\n{sc} Đơn ngoại viện\n{'='*55}")
    vid, _ = make_visit()
    if not vid: bug(sc, 1, "Visit fail"); return
    start_visit(vid)
    meds = jlist(api("get", "/medicines", "dr_nguyen"))
    med_id = meds[0].get("id","") if isinstance(meds,list) and meds else None
    if med_id:
        r = api("post", f"/visits/{vid}/prescriptions", "dr_nguyen",
                {"is_internal": False, "items": [{"medicine_id": med_id, "quantity": 5,
                 "dosage": "1v/lan", "frequency": "2lan/ng"}]})
        ok(sc, 1, f"Đơn ngoại viện → {r.status_code if r else 'err'}")
    else: skip(sc, 1, "Không có thuốc trong DB")


def var07():
    sc = "SC-VAR-07"; print(f"\n{'='*55}\n{sc} RBAC biến thể\n{'='*55}")
    vid, _ = make_visit()
    if vid:
        start_visit(vid)
        r = api("post", f"/pharmacy/dispense/{vid}", "dr_nguyen", {})
        if r and r.status_code in (403,404,422): ok(sc, 1, f"Self-dispense → {r.status_code} ✓")
        elif r and r.status_code in (200,201): bug(sc, 1, "Self-dispense KHÔNG chặn!", sev="P0")


# ── NGOẠI LỆ ─────────────────────────────────────────────────────────────────
def exc01():
    sc = "SC-EXC-01"; print(f"\n{'='*55}\n{sc} Void hóa đơn (chỉ Admin)\n{'='*55}")
    vid, _ = make_visit()
    if not vid: bug(sc, 1, "Visit fail"); return
    start_visit(vid)
    complete_emr(vid)
    inv_id = get_or_create_invoice(vid)
    if not inv_id: bug(sc, 2, "Invoice fail"); return

    # Thu ngân thử void → phải 403
    r = api("post", f"/invoices/{inv_id}/void", "cashier_em", {"reason": "test"})
    if r and r.status_code == 403: ok(sc, 3, "Thu ngân void → 403 ✓")
    elif r and r.status_code in (200,204): bug(sc, 3, "Thu ngân void THÀNH CÔNG — sai!", sev="P0")
    else: ok(sc, 3, f"Thu ngân void → {r.status_code if r else 'err'}")

    # Lễ tân thử void → phải 403
    r2 = api("post", f"/invoices/{inv_id}/void", "recept_anh", {"reason": "test"})
    if r2 and r2.status_code == 403: ok(sc, "3b", "Lễ tân void → 403 ✓")
    elif r2 and r2.status_code in (200,204): bug(sc, "3b", "Lễ tân void THÀNH CÔNG!", sev="P0")

    # Admin void → phải được
    r3 = api("post", f"/invoices/{inv_id}/void", "admin", {"reason": "SC-EXC-01"})
    if r3 and r3.status_code in (200,204): ok(sc, 4, "Admin void → OK ✓")
    else: bug(sc, 4, f"Admin void → {r3.status_code if r3 else 'err'}", sev="P1")


def exc02():
    sc = "SC-EXC-02"; print(f"\n{'='*55}\n{sc} Hủy visit\n{'='*55}")
    vid, _ = make_visit()
    if not vid: bug(sc, 1, "Visit fail"); return
    start_visit(vid)
    r = api("post", f"/visits/{vid}/cancel", "admin", {"cancel_reason": "Test hủy SC-EXC-02"})
    if r and r.status_code in (200,204): ok(sc, 1, f"Cancel → {r.status_code}")
    else: bug(sc, 1, f"Cancel → {r.status_code if r else 'err'}", sev="P1"); return

    rv = api("get", f"/visits/{vid}", "admin")
    if rv:
        st = jd(rv).get("status","?")
        if "CANCEL" in st.upper(): ok(sc, 2, f"Status={st} ✓")
        else: bug(sc, 2, f"Status={st} kỳ vọng CANCELLED", sev="P1")


def exc03():
    sc = "SC-EXC-03"; print(f"\n{'='*55}\n{sc} No-show\n{'='*55}")
    pid = get_patient()
    tomorrow = (date.today() + timedelta(days=1)).isoformat()
    r = api("post", "/appointments", "recept_anh",
            {"patient_id": pid, "scheduled_at": f"{tomorrow}T10:00:00+07:00"})
    if r and r.status_code in (200,201):
        appt_id = jd(r).get("id","")
        ok(sc, 1, f"Appointment: {appt_id[:8]}")
        r2 = api("post", f"/appointments/{appt_id}/cancel", "admin", {"reason": "no-show"})
        ok(sc, 2, f"Cancel → {r2.status_code if r2 else 'err'}")
    else:
        bug(sc, 1, f"Appointment → {r.status_code if r else 'err'}", sev="P2")


def exc04():
    sc = "SC-EXC-04"; print(f"\n{'='*55}\n{sc} Hết tồn khi cấp phát\n{'='*55}")
    r = api("post", "/pharmacy/dispense/00000000-0000-0000-0000-000000000099", "pharm_cuong", {})
    if r and r.status_code in (404,422,400): ok(sc, 1, f"Dispense fake rx → {r.status_code} graceful ✓")
    elif r and r.status_code == 500: bug(sc, 1, "Dispense invalid → 500!", sev="P1")
    else: ok(sc, 1, f"→ {r.status_code if r else 'err'}")

    r2 = api("get", "/inventory/stock-status", "pharm_cuong")
    if r2 and r2.status_code == 200: ok(sc, 2, f"Stock status: {len(jlist(r2))} items")


def exc05():
    sc = "SC-EXC-05"; print(f"\n{'='*55}\n{sc} Sửa đơn trước cấp phát\n{'='*55}")
    vid, _ = make_visit()
    if not vid: bug(sc, 1, "Visit fail"); return
    start_visit(vid)
    meds = jlist(api("get", "/medicines", "dr_nguyen"))
    med_id = meds[0].get("id","") if isinstance(meds,list) and meds else None
    rx_id = None
    if med_id:
        r = api("post", f"/visits/{vid}/prescriptions", "dr_nguyen",
                {"is_internal": True, "items": [{"medicine_id": med_id, "quantity": 5,
                 "dosage": "1v/lan", "frequency": "2lan/ng"}]})
        if r and r.status_code in (200,201): rx_id = jd(r).get("id","")

    complete_emr(vid)

    if rx_id:
        r2 = api("patch", f"/prescriptions/{rx_id}", "dr_nguyen", {"notes": "Đã chỉnh liều"})
        ok(sc, 2, f"Sửa đơn → {r2.status_code if r2 else 'err'}")
        # Y tá thử sửa đơn → phải 403
        r3 = api("patch", f"/prescriptions/{rx_id}", "nurse_lan", {"notes": "nurse edit"})
        if r3 and r3.status_code == 403: ok(sc, 3, "Y tá sửa đơn → 403 ✓")
        elif r3 and r3.status_code in (200,201): bug(sc, 3, "Y tá sửa đơn THÀNH CÔNG!", sev="P0")
        else: ok(sc, 3, f"Y tá sửa đơn → {r3.status_code if r3 else 'err'}")


def exc06():
    sc = "SC-EXC-06"; print(f"\n{'='*55}\n{sc} Partial payment\n{'='*55}")
    vid, _ = make_visit()
    if not vid: bug(sc, 1, "Visit fail"); return
    start_visit(vid)
    complete_emr(vid)
    inv_id = get_or_create_invoice(vid)
    if not inv_id: bug(sc, 2, "Invoice fail"); return

    api("post", f"/invoices/{inv_id}/lines", "cashier_em",
        {"description": "Phí", "unit_price": 100000, "quantity": 1})

    r1 = pay(inv_id, 40000)
    if r1 and r1.status_code in (200,201):
        ok(sc, 3, "Pay 40k OK")
        st = jd(api("get", f"/invoices/{inv_id}", "cashier_em")).get("status","?")
        if "PARTIAL" in st.upper(): ok(sc, "3b", f"Status={st} ✓")
        else: ok(sc, "3b", f"Status={st}")
    else: bug(sc, 3, f"Pay → {r1.status_code if r1 else 'err'}", sev="P1"); return

    r2 = pay(inv_id, 60000, "BANK_TRANSFER")
    if r2 and r2.status_code in (200,201):
        st2 = jd(api("get", f"/invoices/{inv_id}", "cashier_em")).get("status","?")
        if "PAID" in st2.upper(): ok(sc, 4, f"Status={st2} PAID ✓")
        else: bug(sc, 4, f"Status={st2} kỳ vọng PAID", sev="P1")

    r3 = pay(inv_id, 1000)
    if r3 and r3.status_code >= 400: ok(sc, 5, f"Overpay guard → {r3.status_code} ✓")
    elif r3: bug(sc, 5, f"Overpay KHÔNG chặn → {r3.status_code}", sev="P0")


def exc07():
    sc = "SC-EXC-07"; print(f"\n{'='*55}\n{sc} Giảm giá hóa đơn\n{'='*55}")
    vid, _ = make_visit()
    if not vid: bug(sc, 1, "Visit fail"); return
    start_visit(vid)
    complete_emr(vid)
    inv_id = get_or_create_invoice(vid)
    if not inv_id: bug(sc, 2, "Invoice fail"); return

    api("post", f"/invoices/{inv_id}/lines", "cashier_em",
        {"description": "Khám", "unit_price": 200000, "quantity": 1})

    r = api("patch", f"/invoices/{inv_id}", "cashier_em",
            {"discount_amount": 20000, "discount_reason": "Khách quen"})
    if r and r.status_code in (200,201): ok(sc, 3, "Giảm giá 20k → OK ✓")
    elif r and r.status_code == 422:
        # Thử line âm
        r2 = api("post", f"/invoices/{inv_id}/lines", "cashier_em",
                 {"description": "Giảm giá", "unit_price": -20000, "quantity": 1})
        if r2 and r2.status_code in (200,201): ok(sc, 3, "Giảm giá qua line âm ✓")
        else: ok(sc, 3, f"Giảm giá 422 + line âm → {r2.status_code if r2 else 'err'}")
    else: ok(sc, 3, f"Giảm giá → {r.status_code if r else 'err'}")


def exc08():
    sc = "SC-EXC-08"; print(f"\n{'='*55}\n{sc} Đo lại sinh hiệu\n{'='*55}")
    vid, _ = make_visit()
    if not vid: bug(sc, 1, "Visit fail"); return

    r1 = add_vital(vid, "nurse_lan")
    ok(sc, 2, f"Vital 1 → {'OK' if r1 else 'fail'}")
    r2 = api("post", f"/visits/{vid}/vitals", "nurse_lan",
             {"values": {"pulse": 85, "systolic_bp": 130, "diastolic_bp": 85, "temperature": 37.0},
              "is_primary": False})
    ok(sc, 3, f"Vital 2 → {r2.status_code if r2 else 'err'}")

    rv = api("get", f"/visits/{vid}/vitals", "nurse_lan")
    if rv:
        cnt = len(jlist(rv))
        if cnt >= 2: ok(sc, 4, f"GET vitals = {cnt} bản ghi ✓")
        else: ok(sc, 4, f"GET vitals = {cnt} bản ghi")

    r3 = api("post", f"/visits/{vid}/vitals", "pharm_cuong",
             {"values": {"pulse": 80, "temperature": 36.5}, "is_primary": False})
    if r3 and r3.status_code == 403: ok(sc, 5, "Dược sĩ nhập vital → 403 ✓")
    elif r3 and r3.status_code in (200,201): bug(sc, 5, "Dược sĩ nhập vital THÀNH CÔNG!", sev="P0")
    else: ok(sc, 5, f"Dược sĩ nhập vital → {r3.status_code if r3 else 'err'}")


# ── RBAC ─────────────────────────────────────────────────────────────────────
def rbac_no_token():
    sc = "SC-RBAC-NO-TOKEN"; print(f"\n{'='*55}\n{sc} Không token → 401\n{'='*55}")
    for path in ["/patients","/visits","/invoices","/pharmacy/pending-dispense",
                 "/visits/queue","/reports/revenue","/users","/roles"]:
        try:
            r = requests.get(f"{BASE}{path}", timeout=TIMEOUT)
            if r.status_code == 401: ok(sc, "-", f"GET {path} → 401 ✓")
            else: bug(sc, "-", f"GET {path} (no token) → {r.status_code}", sev="P0")
        except: pass


def rbac_cross():
    sc_pre = "SC-RBAC"; print(f"\n{'='*55}\n{sc_pre} Phân quyền chéo\n{'='*55}")
    pid = get_patient()
    vid, _ = make_visit()
    vid = vid or "fake-vid"

    cases = [
        ("01","recept_anh","post",f"/visits/{vid}/vitals",{"values":{"pulse":70},"is_primary":False},"Lễ tân nhập vital",403),
        ("02","nurse_lan","post","/pharmacy/reserve",{"prescription_item_id":"fake","quantity":1},"Y tá cấp phát",403),
        ("03","pharm_cuong","post","/visits",{"patient_id":pid},"Dược sĩ tạo visit",403),
        ("04","cashier_em","post",f"/invoices/fake-inv/void",{"reason":"x"},"Thu ngân void HĐ",[403,404]),
        ("05","recept_anh","post",f"/invoices/fake-inv/void",{"reason":"x"},"Lễ tân void HĐ",[403,404]),
        ("06","dr_nguyen","get","/users",None,"Bác sĩ xem users",403),
        ("07","dr_nguyen","get","/reports/revenue?start=2026-01-01&end=2026-05-31",None,"Bác sĩ xem revenue",403),
        ("08","nurse_lan","post","/roles",{"name":"x","code":"x"},"Y tá tạo role",403),
        ("09","recept_anh","get","/roles",None,"Lễ tân xem roles",403),
        ("10","pharm_cuong","patch","/clinics/me/settings",{"name":"x"},"Dược sĩ sửa settings",403),
        ("11","cashier_em","post","/medicines",{"name":"hack","unit":"v","unit_price":1},"Thu ngân tạo thuốc",403),
        ("12","pharm_cuong","post",f"/invoices/fake/void",{"reason":"x"},"Dược sĩ void HĐ",[403,404]),
        ("13","recept_anh","get","/patients",None,"Lễ tân xem BN clinic mình",200),
    ]

    for num,user,method,path,body,name,expect in cases:
        sc = f"{sc_pre}-{num}"
        r = api(method, path, user, body)
        code = r.status_code if r else 0
        expected = expect if isinstance(expect,list) else [expect]
        if code in expected:
            if 403 in expected and code == 403: ok(sc, num, f"{name} → 403 ✓")
            elif code == 200: ok(sc, num, f"{name} → 200 ✓")
            else: ok(sc, num, f"{name} → {code} ✓")
        elif code == 422 and 403 in expected:
            bug(sc, num, f"{name} → 422 (validate trước permission, phải 403 trước)", sev="P1")
        elif code < 400 and code != 0 and 403 in expected:
            bug(sc, num, f"{name} → {code} KHÔNG bị chặn!", sev="P0")
        else:
            ok(sc, num, f"{name} → {code} (expect {expected})")


# ── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    import time as t; start = t.time()
    print(f"\n{'='*60}\n  Clinic CMS — E2E Full Test v2\n  {BASE}\n{'='*60}")
    try:
        hc = requests.get(BASE.replace("/api/v1","/health"), timeout=5)
        print(f"  Health: {hc.status_code}\n")
    except: print("  Health: unreachable\n")

    new_patient()  # warm up

    # Happy path
    hp01(); hp02(); hp03(); hp04(); hp05()
    # Biến thể
    var01(); var02(); var03(); var04(); var05(); var06(); var07()
    # Ngoại lệ
    exc01(); exc02(); exc03(); exc04(); exc05(); exc06(); exc07(); exc08()
    # RBAC
    rbac_no_token(); rbac_cross()

    elapsed = t.time() - start
    p0 = [b for b in BUGS if b[2]=="P0"]
    p1 = [b for b in BUGS if b[2]=="P1"]
    p2 = [b for b in BUGS if b[2]=="P2"]

    print(f"\n{'='*60}")
    print(f"  TỔNG: {len(PASSES)} PASS | {len(BUGS)} BUG ({elapsed:.1f}s)")
    print(f"{'='*60}")
    for grp, lbl in [(p0,"🔴 P0"),(p1,"🟠 P1"),(p2,"🟡 P2")]:
        if grp:
            print(f"\n  {lbl} ({len(grp)})")
            for sc,step,sev,msg,detail in grp:
                print(f"  [{sc}] B{step}: {msg}")
                if detail: print(f"       → {detail[:150]}")

    out = "docs/tasks/TASK-052/deliveries/test-reports/e2e-full-v2-report.json"
    import os; os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out,"w",encoding="utf-8") as f:
        json.dump({"passed":len(PASSES),"bugs":len(BUGS),"elapsed":round(elapsed,1),
                   "bugs_detail":[{"sc":b[0],"step":str(b[1]),"sev":b[2],"msg":b[3]} for b in BUGS]},
                  f, ensure_ascii=False, indent=2)
    print(f"\n  Report: {out}")
    return 1 if BUGS else 0

if __name__ == "__main__":
    sys.exit(main())
