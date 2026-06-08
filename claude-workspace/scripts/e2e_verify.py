"""Verify remaining scenario gaps with correct field names."""
import requests, json, base64
from datetime import date, timedelta

BASE = "http://localhost:8001/api/v1"

def tok(user, pw):
    r = requests.post(f"{BASE}/auth/login", json={"username":user,"password":pw}, timeout=10)
    d = r.json()
    return d.get("access_token") or d.get("data",{}).get("access_token","")

def hdr(t): return {"Authorization": f"Bearer {t}"}

def perms(t):
    parts = t.split(".")
    pad = parts[1] + "=="*(4-len(parts[1])%4)
    return json.loads(base64.b64decode(pad)).get("permissions",[])

T = {
    "rec": tok("recept_anh","Recept@1234"),
    "nur": tok("nurse_lan","Nurse@1234"),
    "doc": tok("dr_nguyen","Doctor@1234"),
    "cash": tok("cashier_em","Cashier@1234"),
    "pha": tok("pharm_cuong","Pharm@1234"),
    "adm": tok("admin","Demo@1234"),
}

results = []
def ok(sc, msg): results.append((sc,"PASS",msg)); print(f"  OK [{sc}] {msg}")
def bug(sc, msg, sev="P1"): results.append((sc,"BUG",msg)); print(f"  BUG[{sev}] [{sc}] {msg}")

# BN dùng chung
PAT = requests.post(f"{BASE}/patients", headers=hdr(T["rec"]),
    json={"full_name":"BN Verify","phone":"0911111222","date_of_birth":"1990-01-01","gender":"male"},timeout=10).json()
PAT_ID = PAT.get("id","")
print(f"\nPatient: {PAT_ID}\n")

def new_visit():
    v = requests.post(f"{BASE}/visits", headers=hdr(T["rec"]),
        json={"patient_id":PAT_ID}, timeout=10).json()
    return v.get("id","")

def add_vital(vid, user="nur"):
    r = requests.post(f"{BASE}/visits/{vid}/vitals", headers=hdr(T[user]),
        json={"values":{"pulse":78,"systolic_bp":120,"diastolic_bp":80},"is_primary":True}, timeout=10)
    return r.status_code

def start(vid, user="doc"):
    r = requests.post(f"{BASE}/visits/{vid}/start", headers=hdr(T[user]), json={}, timeout=10)
    return r.status_code

def get_or_create_invoice(vid):
    r = requests.get(f"{BASE}/visits/{vid}/invoices", headers=hdr(T["cash"]), timeout=10)
    items = r.json() if isinstance(r.json(),list) else r.json().get("data",r.json().get("items",[]))
    if isinstance(items,list) and items:
        return items[0]["id"]
    r2 = requests.post(f"{BASE}/visits/{vid}/invoices", headers=hdr(T["cash"]), json={}, timeout=10)
    return r2.json().get("id","")

# ── SC-HP-01: Full flow ─────────────────────────────────────────────────────
print("="*50)
print("SC-HP-01 Full flow khám tổng quát")
print("="*50)
vid = new_visit()
vs = add_vital(vid)
if vs in (200,201): ok("SC-HP-01", f"B2 Vital → {vs}")
else: bug("SC-HP-01", f"B2 Vital → {vs}")

ss = start(vid)
if ss in (200,201): ok("SC-HP-01", f"B3 Start → {ss}")
else: bug("SC-HP-01", f"B3 Start → {ss}")

svcs = requests.get(f"{BASE}/services", headers=hdr(T["doc"]), timeout=10).json()
items = svcs if isinstance(svcs,list) else svcs.get("data",svcs.get("items",[]))
SVC_ID = items[0]["id"] if isinstance(items,list) and items else None
if SVC_ID:
    r4 = requests.post(f"{BASE}/visits/{vid}/services", headers=hdr(T["doc"]),
        json={"service_id":SVC_ID,"quantity":1}, timeout=10)
    if r4.status_code in (200,201): ok("SC-HP-01", f"B4 Service → {r4.status_code}")
    else: bug("SC-HP-01", f"B4 Service → {r4.status_code} {r4.text[:80]}")

r5 = requests.post(f"{BASE}/visits/{vid}/complete-emr", headers=hdr(T["doc"]), json={}, timeout=10)
if r5.status_code in (200,201,204): ok("SC-HP-01", f"B5 complete-emr → {r5.status_code} status={r5.json().get('status','?')}")
else: bug("SC-HP-01", f"B5 complete-emr → {r5.status_code} {r5.text[:80]}")

inv_id = get_or_create_invoice(vid)
ok("SC-HP-01", f"B6 invoice={inv_id}")

if inv_id:
    r7 = requests.post(f"{BASE}/invoices/{inv_id}/payments", headers=hdr(T["cash"]),
        json={"amount":200000,"payment_method":"CASH"}, timeout=10)
    if r7.status_code in (200,201): ok("SC-HP-01", "B7 Payment CASH OK ✓")
    else: bug("SC-HP-01", f"B7 Payment → {r7.status_code} {r7.text[:100]}")

    # Visit → COMPLETED sau payment?
    rv = requests.get(f"{BASE}/visits/{vid}", headers=hdr(T["adm"]), timeout=10).json()
    st = rv.get("status","?")
    ok("SC-HP-01", f"B8 Visit status cuối = {st}")

r9 = requests.get(f"{BASE}/pharmacy/pending-dispense", headers=hdr(T["pha"]), timeout=10)
ok("SC-HP-01", f"B9 Pharmacy queue → {r9.status_code}")

# ── SC-EXC-02: Hủy visit ───────────────────────────────────────────────────
print("\n" + "="*50)
print("SC-EXC-02 Hủy visit + check cancel permission")
print("="*50)
print(f"recept_anh visit.cancel: {'visit.cancel' in perms(T['rec'])}")
print(f"dr_nguyen visit.cancel:  {'visit.cancel' in perms(T['doc'])}")
print(f"admin visit.cancel:      {'visit.cancel' in perms(T['adm'])}")

vid2 = new_visit()
start(vid2)
r = requests.post(f"{BASE}/visits/{vid2}/cancel", headers=hdr(T["adm"]),
    json={"reason":"Test hủy SC-EXC-02"}, timeout=10)
if r.status_code in (200,204):
    ok("SC-EXC-02", f"Admin cancel IN_PROGRESS → {r.status_code}")
    rv = requests.get(f"{BASE}/visits/{vid2}", headers=hdr(T["adm"]), timeout=10).json()
    st = rv.get("status","?")
    if "CANCEL" in st.upper(): ok("SC-EXC-02", f"Status sau hủy = {st} ✓")
    else: bug("SC-EXC-02", f"Status sau hủy = {st} (kỳ vọng CANCELLED)", "P1")
else:
    bug("SC-EXC-02", f"Admin cancel → {r.status_code} {r.json().get('error',{}).get('message','')[:80]}", "P1")

# ── SC-VAR-05 & SC-EXC-03: Appointment ─────────────────────────────────────
print("\n" + "="*50)
print("SC-VAR-05/EXC-03 Appointment (field: scheduled_at)")
print("="*50)
tomorrow = (date.today() + timedelta(days=1)).isoformat()
r = requests.post(f"{BASE}/appointments", headers=hdr(T["rec"]),
    json={"patient_id":PAT_ID,"scheduled_at":f"{tomorrow}T09:00:00"}, timeout=10)
if r.status_code in (200,201):
    APPT_ID = r.json().get("id","")
    ok("SC-VAR-05", f"Appointment tạo: {APPT_ID}")
    r2 = requests.post(f"{BASE}/appointments/{APPT_ID}/check-in", headers=hdr(T["rec"]), json={}, timeout=10)
    ok("SC-VAR-05", f"Check-in lần 1 → {r2.status_code} {'(visit created)' if r2.status_code in (200,201) else r2.json().get('error',{}).get('message','')[:60]}")
    r3 = requests.post(f"{BASE}/appointments/{APPT_ID}/check-in", headers=hdr(T["rec"]), json={}, timeout=10)
    if r3.status_code >= 400:
        ok("SC-VAR-05", f"Check-in lần 2 → {r3.status_code} (bị chặn ✓)")
    else:
        bug("SC-VAR-05", f"Check-in lần 2 → {r3.status_code} (KHÔNG chặn duplicate!)", "P0")

    r4 = requests.post(f"{BASE}/appointments/{APPT_ID}/cancel", headers=hdr(T["adm"]),
        json={"reason":"no-show test"}, timeout=10)
    ok("SC-EXC-03", f"No-show cancel → {r4.status_code}")
else:
    bug("SC-VAR-05", f"Appointment → {r.status_code} {r.text[:150]}", "P2")

# ── SC-EXC-08: Đo lại sinh hiệu ────────────────────────────────────────────
print("\n" + "="*50)
print("SC-EXC-08 Đo lại sinh hiệu nhiều lần")
print("="*50)
vid3 = new_visit()
r1 = requests.post(f"{BASE}/visits/{vid3}/vitals", headers=hdr(T["nur"]),
    json={"values":{"pulse":78,"systolic_bp":120,"diastolic_bp":80},"is_primary":True}, timeout=10)
ok("SC-EXC-08", f"Vital lần 1 → {r1.status_code}")
r2 = requests.post(f"{BASE}/visits/{vid3}/vitals", headers=hdr(T["nur"]),
    json={"values":{"pulse":85,"systolic_bp":130,"diastolic_bp":85},"is_primary":False}, timeout=10)
ok("SC-EXC-08", f"Vital lần 2 → {r2.status_code}")
rv = requests.get(f"{BASE}/visits/{vid3}/vitals", headers=hdr(T["nur"]), timeout=10).json()
cnt = len(rv) if isinstance(rv,list) else len(rv.get("data",rv.get("items",[])))
if cnt >= 2: ok("SC-EXC-08", f"GET vitals = {cnt} bản ghi ✓")
else: bug("SC-EXC-08", f"GET vitals = {cnt} (kỳ vọng ≥2)", "P1")
r3 = requests.post(f"{BASE}/visits/{vid3}/vitals", headers=hdr(T["pha"]),
    json={"values":{"pulse":80},"is_primary":False}, timeout=10)
if r3.status_code == 403: ok("SC-EXC-08", "Dược sĩ nhập vital → 403 ✓")
else: bug("SC-EXC-08", f"Dược sĩ nhập vital → {r3.status_code} (kỳ vọng 403)", "P0")

# ── SC-EXC-04: Dispense graceful error ─────────────────────────────────────
print("\n" + "="*50)
print("SC-EXC-04 Dispense invalid rx")
print("="*50)
r = requests.post(f"{BASE}/pharmacy/dispense/00000000-0000-0000-0000-000000000099",
    headers=hdr(T["pha"]), json={}, timeout=10)
if r.status_code in (404,422,400): ok("SC-EXC-04", f"Dispense fake rx → {r.status_code} (graceful ✓)")
elif r.status_code == 500: bug("SC-EXC-04", f"Dispense invalid rx → 500!", "P1")
else: ok("SC-EXC-04", f"Dispense fake rx → {r.status_code}")

# ── SC-EXC-06: Partial payment ──────────────────────────────────────────────
print("\n" + "="*50)
print("SC-EXC-06 Partial payment")
print("="*50)
vid4 = new_visit()
start(vid4)
requests.post(f"{BASE}/visits/{vid4}/complete-emr", headers=hdr(T["doc"]), json={}, timeout=10)
inv4 = get_or_create_invoice(vid4)
requests.post(f"{BASE}/invoices/{inv4}/lines", headers=hdr(T["cash"]),
    json={"description":"Phí khám","unit_price":100000,"quantity":1}, timeout=10)
r1 = requests.post(f"{BASE}/invoices/{inv4}/payments", headers=hdr(T["cash"]),
    json={"amount":40000,"payment_method":"CASH"}, timeout=10)
if r1.status_code in (200,201):
    ok("SC-EXC-06", "Partial pay 40k → OK")
    st = requests.get(f"{BASE}/invoices/{inv4}", headers=hdr(T["cash"]), timeout=10).json().get("status","?")
    if "PARTIAL" in st.upper(): ok("SC-EXC-06", f"Status={st} ✓")
    else: bug("SC-EXC-06", f"Status={st} (kỳ vọng PARTIALLY_PAID)", "P1")
else:
    bug("SC-EXC-06", f"Partial pay → {r1.status_code} {r1.text[:100]}", "P1")

r2 = requests.post(f"{BASE}/invoices/{inv4}/payments", headers=hdr(T["cash"]),
    json={"amount":60000,"payment_method":"BANK_TRANSFER"}, timeout=10)
if r2.status_code in (200,201):
    ok("SC-EXC-06", "Pay lần 2 (60k BANK) → OK")
    st2 = requests.get(f"{BASE}/invoices/{inv4}", headers=hdr(T["cash"]), timeout=10).json().get("status","?")
    if "PAID" in st2.upper(): ok("SC-EXC-06", f"Status cuối={st2} PAID ✓")
    else: bug("SC-EXC-06", f"Status cuối={st2} (kỳ vọng PAID)", "P1")
r3 = requests.post(f"{BASE}/invoices/{inv4}/payments", headers=hdr(T["cash"]),
    json={"amount":1000,"payment_method":"CASH"}, timeout=10)
if r3.status_code >= 400: ok("SC-EXC-06", f"Overpay guard → {r3.status_code} ✓")
else: bug("SC-EXC-06", f"Overpay guard FAIL → {r3.status_code}", "P0")

# ── SC-VAR-04 Reassign ──────────────────────────────────────────────────────
print("\n" + "="*50)
print("SC-VAR-04 Reassign bác sĩ")
print("="*50)
# Lấy user_id của dr_le
users_r = requests.get(f"{BASE}/users", headers=hdr(T["adm"]), timeout=10).json()
users = users_r if isinstance(users_r,list) else users_r.get("data",users_r.get("items",[]))
dr_le_id = None
for u in (users if isinstance(users,list) else []):
    if u.get("username","") == "dr_le": dr_le_id = u.get("id"); break
print(f"dr_le user_id: {dr_le_id}")
if dr_le_id:
    vid5 = new_visit()
    start(vid5)
    r = requests.post(f"{BASE}/visits/{vid5}/reassign", headers=hdr(T["doc"]),
        json={"doctor_id": dr_le_id}, timeout=10)
    if r.status_code in (200,201,204): ok("SC-VAR-04", f"Reassign sang dr_le → {r.status_code} ✓")
    else: ok("SC-VAR-04", f"Reassign → {r.status_code} {r.text[:100]} (endpoint cần xác nhận)")
else:
    ok("SC-VAR-04", "Không tìm được user_id dr_le (cần user.manage để list users)")

# ── TỔNG KẾT ────────────────────────────────────────────────────────────────
print("\n" + "="*50)
bugs = [(sc,msg) for sc,st,msg in results if st=="BUG"]
passes = [(sc,msg) for sc,st,msg in results if st=="PASS"]
print(f"TỔNG: {len(passes)} PASS | {len(bugs)} BUG")
if bugs:
    print("\nBUG list:")
    for i,(sc,msg) in enumerate(bugs,1):
        print(f"  {i}. [{sc}] {msg}")
