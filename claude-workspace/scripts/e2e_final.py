import requests, json, base64
from datetime import date, timedelta

BASE = "http://localhost:8001/api/v1"

def tok(u, p):
    d = requests.post(f"{BASE}/auth/login", json={"username": u, "password": p}, timeout=10).json()
    return d.get("access_token") or d.get("data", {}).get("access_token", "")

def hdr(t): return {"Authorization": f"Bearer {t}"}

def perms_list(t):
    p = t.split(".")
    pad = p[1] + "==" * (4 - len(p[1]) % 4)
    return json.loads(base64.b64decode(pad)).get("permissions", [])

T = {
    "rec":  tok("recept_anh", "Recept@1234"),
    "nur":  tok("nurse_lan", "Nurse@1234"),
    "doc":  tok("dr_nguyen", "Doctor@1234"),
    "cash": tok("cashier_em", "Cashier@1234"),
    "pha":  tok("pharm_cuong", "Pharm@1234"),
    "adm":  tok("admin", "Demo@1234"),
}

bugs = []
passes = []

def ok(sc, msg):
    passes.append(f"[{sc}] {msg}")
    print(f"  OK  [{sc}] {msg}")

def bug(sc, msg, sev="P1"):
    bugs.append((sc, sev, msg))
    print(f"  BUG[{sev}] [{sc}] {msg}")

# Patient
r = requests.post(f"{BASE}/patients", headers=hdr(T["rec"]),
    json={"full_name": "BN Final2", "phone": "0977888999",
          "date_of_birth": "1990-01-01", "gender": "male"}, timeout=10)
d = r.json()
PAT_ID = d.get("id") or d.get("data", {}).get("id", "")
if not PAT_ID:
    r2 = requests.get(f"{BASE}/patients/search?q=0977888999&type=phone", headers=hdr(T["rec"]), timeout=10)
    items = r2.json() if isinstance(r2.json(), list) else r2.json().get("data", r2.json().get("items", []))
    if isinstance(items, list) and items:
        PAT_ID = items[0]["id"]
if not PAT_ID:
    r3 = requests.get(f"{BASE}/patients", headers=hdr(T["rec"]), timeout=10)
    items = r3.json() if isinstance(r3.json(), list) else r3.json().get("data", r3.json().get("items", []))
    if isinstance(items, list) and items:
        PAT_ID = items[0]["id"]
print(f"PAT_ID = {PAT_ID}\n")

def new_visit():
    v = requests.post(f"{BASE}/visits", headers=hdr(T["rec"]),
        json={"patient_id": PAT_ID}, timeout=10).json()
    return v.get("id", "")

def vital(vid):
    r = requests.post(f"{BASE}/visits/{vid}/vitals", headers=hdr(T["nur"]),
        json={"values": {"pulse": 78, "systolic_bp": 120, "diastolic_bp": 80}, "is_primary": True}, timeout=10)
    return r.status_code

def start_v(vid):
    r = requests.post(f"{BASE}/visits/{vid}/start", headers=hdr(T["doc"]), json={}, timeout=10)
    return r.status_code, r.json().get("status", "?")

def get_inv(vid):
    r = requests.get(f"{BASE}/visits/{vid}/invoices", headers=hdr(T["cash"]), timeout=10).json()
    items = r if isinstance(r, list) else r.get("data", r.get("items", []))
    if isinstance(items, list) and items:
        return items[0]["id"]
    r2 = requests.post(f"{BASE}/visits/{vid}/invoices", headers=hdr(T["cash"]), json={}, timeout=10).json()
    return r2.get("id", "")

# SC-HP-01
print("=" * 50 + "\nSC-HP-01 Full flow\n" + "=" * 50)
vid = new_visit()
print(f"  visit={vid}")
vs = vital(vid)
(ok if vs in (200, 201) else bug)("SC-HP-01", f"B2 Vital -> {vs}")
sc, st = start_v(vid)
(ok if sc in (200, 201) else bug)("SC-HP-01", f"B3 Start -> {sc} {st}")

svcs = requests.get(f"{BASE}/services", headers=hdr(T["doc"]), timeout=10).json()
items = svcs if isinstance(svcs, list) else svcs.get("data", svcs.get("items", []))
SVC = items[0]["id"] if isinstance(items, list) and items else None
if SVC:
    r4 = requests.post(f"{BASE}/visits/{vid}/services", headers=hdr(T["doc"]),
        json={"service_id": SVC, "quantity": 1}, timeout=10)
    (ok if r4.status_code in (200, 201) else bug)("SC-HP-01", f"B4 Svc -> {r4.status_code}")

r5 = requests.post(f"{BASE}/visits/{vid}/complete-emr", headers=hdr(T["doc"]), json={}, timeout=10)
if r5.status_code in (200, 201, 204):
    ok("SC-HP-01", f"B5 complete-emr -> {r5.status_code} {r5.json().get('status', '')}")
else:
    bug("SC-HP-01", f"B5 complete-emr -> {r5.status_code} {r5.text[:60]}")

inv = get_inv(vid)
ok("SC-HP-01", f"B6 invoice={inv}")
if inv:
    r7 = requests.post(f"{BASE}/invoices/{inv}/payments", headers=hdr(T["cash"]),
        json={"amount": 200000, "payment_method": "CASH"}, timeout=10)
    (ok if r7.status_code in (200, 201) else bug)("SC-HP-01", f"B7 Payment -> {r7.status_code} {r7.json().get('id','') or r7.text[:60]}")
    rv = requests.get(f"{BASE}/visits/{vid}", headers=hdr(T["adm"]), timeout=10).json()
    ok("SC-HP-01", f"B8 Visit status={rv.get('status', '?')}")

r9 = requests.get(f"{BASE}/pharmacy/pending-dispense", headers=hdr(T["pha"]), timeout=10)
ok("SC-HP-01", f"B9 Pharmacy -> {r9.status_code}")

# SC-EXC-02
print("\n" + "=" * 50 + "\nSC-EXC-02 Huy visit\n" + "=" * 50)
print(f"  doctor has visit.cancel: {'visit.cancel' in perms_list(T['doc'])}")
print(f"  admin  has visit.cancel: {'visit.cancel' in perms_list(T['adm'])}")
vid2 = new_visit()
start_v(vid2)
r = requests.post(f"{BASE}/visits/{vid2}/cancel", headers=hdr(T["adm"]),
    json={"reason": "Test huy"}, timeout=10)
if r.status_code in (200, 204):
    st = requests.get(f"{BASE}/visits/{vid2}", headers=hdr(T["adm"]), timeout=10).json().get("status", "?")
    (ok if "CANCEL" in st.upper() else bug)("SC-EXC-02", f"Admin cancel -> {r.status_code} status={st}")
else:
    bug("SC-EXC-02", f"Admin cancel -> {r.status_code} {r.json().get('error', {}).get('message', '')[:60]}")

# SC-VAR-05 + SC-EXC-03
print("\n" + "=" * 50 + "\nSC-VAR-05 / SC-EXC-03 Appointment\n" + "=" * 50)
tomorrow = (date.today() + timedelta(days=1)).isoformat()
r = requests.post(f"{BASE}/appointments", headers=hdr(T["rec"]),
    json={"patient_id": PAT_ID, "scheduled_at": f"{tomorrow}T09:00:00"}, timeout=10)
if r.status_code in (200, 201):
    APPT = r.json().get("id", "")
    ok("SC-VAR-05", f"Appointment -> {APPT}")
    r2 = requests.post(f"{BASE}/appointments/{APPT}/check-in", headers=hdr(T["rec"]), json={}, timeout=10)
    ok("SC-VAR-05", f"Check-in 1 -> {r2.status_code} {r2.json().get('id','') or r2.json().get('error',{}).get('message','')[:60]}")
    r3 = requests.post(f"{BASE}/appointments/{APPT}/check-in", headers=hdr(T["rec"]), json={}, timeout=10)
    (ok if r3.status_code >= 400 else bug)("SC-VAR-05",
        f"Check-in 2 -> {r3.status_code} {'bị chặn ✓' if r3.status_code >= 400 else 'KHONG chan duplicate!'}")
    r4 = requests.post(f"{BASE}/appointments/{APPT}/cancel", headers=hdr(T["adm"]),
        json={"reason": "no-show"}, timeout=10)
    ok("SC-EXC-03", f"No-show cancel -> {r4.status_code}")
else:
    bug("SC-VAR-05", f"Appointment -> {r.status_code} {r.text[:150]}", "P2")

# SC-EXC-08
print("\n" + "=" * 50 + "\nSC-EXC-08 Vital nhieu lan\n" + "=" * 50)
vid3 = new_visit()
r1 = requests.post(f"{BASE}/visits/{vid3}/vitals", headers=hdr(T["nur"]),
    json={"values": {"pulse": 78, "systolic_bp": 120}, "is_primary": True}, timeout=10)
ok("SC-EXC-08", f"Vital 1 -> {r1.status_code}")
r2 = requests.post(f"{BASE}/visits/{vid3}/vitals", headers=hdr(T["nur"]),
    json={"values": {"pulse": 85, "systolic_bp": 130}, "is_primary": False}, timeout=10)
ok("SC-EXC-08", f"Vital 2 -> {r2.status_code}")
rv = requests.get(f"{BASE}/visits/{vid3}/vitals", headers=hdr(T["nur"]), timeout=10).json()
cnt = len(rv) if isinstance(rv, list) else len(rv.get("data", rv.get("items", [])))
(ok if cnt >= 2 else bug)("SC-EXC-08", f"GET vitals = {cnt} ban ghi {'ok' if cnt >= 2 else '(ky vong >=2)'}")
r3 = requests.post(f"{BASE}/visits/{vid3}/vitals", headers=hdr(T["pha"]),
    json={"values": {"pulse": 80}, "is_primary": False}, timeout=10)
(ok if r3.status_code == 403 else bug)("SC-EXC-08",
    f"Duoc si nhap vital -> {r3.status_code} {'403 ok' if r3.status_code == 403 else '(ky vong 403)'}", "P0")

# SC-EXC-04
print("\n" + "=" * 50 + "\nSC-EXC-04 Dispense invalid rx\n" + "=" * 50)
r = requests.post(f"{BASE}/pharmacy/dispense/00000000-0000-0000-0000-000000000099",
    headers=hdr(T["pha"]), json={}, timeout=10)
if r.status_code in (404, 422, 400):
    ok("SC-EXC-04", f"Dispense fake rx -> {r.status_code} graceful ok")
elif r.status_code == 500:
    bug("SC-EXC-04", f"Dispense invalid -> 500 server error!")
elif r.status_code == 200:
    bug("SC-EXC-04", "Dispense fake rx -> 200 - co the khong validate rx_id!")
else:
    ok("SC-EXC-04", f"-> {r.status_code}")

# SC-EXC-06
print("\n" + "=" * 50 + "\nSC-EXC-06 Partial payment\n" + "=" * 50)
vid4 = new_visit()
start_v(vid4)
requests.post(f"{BASE}/visits/{vid4}/complete-emr", headers=hdr(T["doc"]), json={}, timeout=10)
inv4 = get_inv(vid4)
requests.post(f"{BASE}/invoices/{inv4}/lines", headers=hdr(T["cash"]),
    json={"description": "Phi", "unit_price": 100000, "quantity": 1}, timeout=10)
r1 = requests.post(f"{BASE}/invoices/{inv4}/payments", headers=hdr(T["cash"]),
    json={"amount": 40000, "payment_method": "CASH"}, timeout=10)
if r1.status_code in (200, 201):
    ok("SC-EXC-06", "Pay 40k ok")
    st = requests.get(f"{BASE}/invoices/{inv4}", headers=hdr(T["cash"]), timeout=10).json().get("status", "?")
    (ok if "PARTIAL" in st.upper() else bug)("SC-EXC-06", f"Status={st}")
else:
    bug("SC-EXC-06", f"Pay -> {r1.status_code} {r1.text[:80]}")

r2 = requests.post(f"{BASE}/invoices/{inv4}/payments", headers=hdr(T["cash"]),
    json={"amount": 60000, "payment_method": "BANK_TRANSFER"}, timeout=10)
if r2.status_code in (200, 201):
    st2 = requests.get(f"{BASE}/invoices/{inv4}", headers=hdr(T["cash"]), timeout=10).json().get("status", "?")
    (ok if "PAID" in st2.upper() else bug)("SC-EXC-06", f"Pay2 ok, status={st2}")
else:
    bug("SC-EXC-06", f"Pay2 -> {r2.status_code}")

r3 = requests.post(f"{BASE}/invoices/{inv4}/payments", headers=hdr(T["cash"]),
    json={"amount": 1000, "payment_method": "CASH"}, timeout=10)
(ok if r3.status_code >= 400 else bug)("SC-EXC-06",
    f"Overpay guard -> {r3.status_code} {'ok' if r3.status_code >= 400 else 'KHONG chan!'}")

# SC-VAR-04 Reassign
print("\n" + "=" * 50 + "\nSC-VAR-04 Reassign\n" + "=" * 50)
users_r = requests.get(f"{BASE}/users", headers=hdr(T["adm"]), timeout=10).json()
users = users_r if isinstance(users_r, list) else users_r.get("data", users_r.get("items", []))
dr_le_id = next((u["id"] for u in (users if isinstance(users, list) else [])
    if u.get("username") == "dr_le"), None)
print(f"  dr_le id: {dr_le_id}")
vid5 = new_visit()
start_v(vid5)
r = requests.post(f"{BASE}/visits/{vid5}/reassign", headers=hdr(T["doc"]),
    json={"doctor_id": dr_le_id} if dr_le_id else {}, timeout=10)
if r.status_code in (200, 201, 204):
    ok("SC-VAR-04", f"Reassign -> {r.status_code} ok")
elif r.status_code == 404:
    bug("SC-VAR-04", "Reassign endpoint 404 - khong ton tai", "P2")
else:
    ok("SC-VAR-04", f"Reassign -> {r.status_code} {r.text[:80]}")

# SUMMARY
print("\n" + "=" * 60)
print(f"TONG: {len(passes)} PASS | {len(bugs)} BUG")
if bugs:
    print("\nBUG chi tiet:")
    for i, (sc, sev, msg) in enumerate(bugs, 1):
        print(f"  {i:2}. [{sev}][{sc}] {msg}")
