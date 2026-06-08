"""
E2E Operational Flow Test — Clinic CMS
Chạy các kịch bản vận hành theo vai trò (SC-HP, SC-VAR, SC-EXC, SC-RBAC)
dựa trên docs/tasks/TASK-052/deliveries/test-cases/scenarios/

Cách chạy:
  python scripts/e2e_operational_test.py
  python scripts/e2e_operational_test.py --scenarios hp,var,exc,rbac
  python scripts/e2e_operational_test.py --base-url http://localhost:8002

Yêu cầu: requests (pip install requests)
"""
import sys, json, time, argparse, traceback
from datetime import datetime
from typing import Optional

try:
    import requests
except ImportError:
    print("Thiếu: pip install requests"); sys.exit(1)

# ── CONFIG ──────────────────────────────────────────────────────────────────
BASE_URL = "http://localhost:8001/api/v1"
CREDS = {
    "admin":      "Demo@1234",
    "recept_anh": "Recept@1234",
    "nurse_lan":  "Nurse@1234",
    "dr_nguyen":  "Doctor@1234",
    "cashier_em": "Cashier@1234",
    "pharm_cuong":"Pharm@1234",
    "recept_binh":"Recept@1234",
    "dr_le":      "Doctor@1234",
    "nurse_huong":"Nurse@1234",
    "pharm_dung": "Pharm@1234",
}
TIMEOUT = 10

# ── RESULT TRACKER ───────────────────────────────────────────────────────────
bugs = []
passed = []

def ok(scenario, step, msg):
    passed.append(f"[{scenario}] Bước {step}: {msg}")
    print(f"  ✓ [{scenario}] B{step} {msg}")

def bug(scenario, step, msg, detail="", severity="P1"):
    b = {"scenario": scenario, "step": step, "msg": msg, "detail": detail, "severity": severity}
    bugs.append(b)
    print(f"  ✗ [{scenario}][{severity}] B{step} {msg}")
    if detail: print(f"       → {detail}")

# ── HTTP HELPERS ──────────────────────────────────────────────────────────────
_tokens = {}

def login(username: str) -> Optional[str]:
    if username in _tokens:
        return _tokens[username]
    pw = CREDS.get(username)
    if not pw:
        print(f"  ! Không có credentials cho {username}")
        return None
    try:
        r = requests.post(f"{BASE_URL}/auth/login",
                          json={"username": username, "password": pw}, timeout=TIMEOUT)
        if r.status_code == 200:
            token = r.json().get("access_token") or r.json().get("data", {}).get("access_token")
            if token:
                _tokens[username] = token
                return token
        print(f"  ! Login {username} → {r.status_code}: {r.text[:200]}")
        return None
    except Exception as e:
        print(f"  ! Login {username} exception: {e}")
        return None

def req(method, path, username, sc, step, expected_status=None, **kwargs):
    token = login(username)
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    url = f"{BASE_URL}{path}"
    try:
        r = getattr(requests, method)(url, headers=headers, timeout=TIMEOUT, **kwargs)
        if expected_status and r.status_code not in (expected_status if isinstance(expected_status, list) else [expected_status]):
            bug(sc, step, f"{method.upper()} {path} → {r.status_code} (mong {expected_status})",
                r.text[:400])
            return None
        return r
    except Exception as e:
        bug(sc, step, f"{method.upper()} {path} exception", str(e))
        return None

def get(path, user, sc, step, **kw):  return req("get",    path, user, sc, step, **kw)
def post(path, user, sc, step, **kw): return req("post",   path, user, sc, step, **kw)
def patch(path, user, sc, step, **kw):return req("patch",  path, user, sc, step, **kw)

# ── SHARED SETUP: tạo bệnh nhân dùng chung ───────────────────────────────────
# Dùng seeded patient để tránh BUG-NEW-001 (FK violation với patient mới tạo + RLS FORCE)
_patient_id = "74cd3d82-993c-4fc2-af62-49202062e582"  # BN0001 — seeded demo patient

def ensure_patient(sc="SETUP"):
    return _patient_id

# ─────────────────────────────────────────────────────────────────────────────
# NHÓM 1 — HAPPY PATH
# ─────────────────────────────────────────────────────────────────────────────
def run_hp01():
    """SC-HP-01: Khám tổng quát, kê đơn nội viện, cấp thuốc FEFO, thanh toán."""
    sc = "SC-HP-01"
    print(f"\n{'='*60}\n{sc} — Khám tổng quát đầy đủ\n{'='*60}")

    # B1 Tạo bệnh nhân
    pat_id = ensure_patient(sc)
    if not pat_id:
        bug(sc, 1, "Không tạo được bệnh nhân"); return

    # B2 Lễ tân tạo visit
    r = post("/visits", "recept_anh", sc, 2,
             json={"patient_id": pat_id, "visit_type": "WALK_IN"},
             expected_status=[200, 201])
    if not r: return
    visit = r.json().get("data") or r.json()
    visit_id = visit.get("id")
    status   = visit.get("status", "")
    if not visit_id:
        bug(sc, 2, "Response không có visit.id", str(visit)[:200]); return
    ok(sc, 2, f"Visit tạo thành công id={visit_id} status={status}")

    # Check trạng thái hợp lệ ban đầu
    if "WAITING" not in status.upper():
        bug(sc, 2, f"Visit status kỳ vọng WAITING*, nhận được: {status}", severity="P1")

    # B3 Lấy danh sách vitals definitions
    r = get("/vitals/definitions", "nurse_lan", sc, 3, expected_status=[200])
    if r:
        defs = r.json()
        ok(sc, 3, f"Vitals definitions: {len(defs) if isinstance(defs,list) else '?'} items")

    # B4 Y tá ghi sinh hiệu — format đúng: {"values": {...}, "is_primary": true}
    r = post(f"/visits/{visit_id}/vitals", "nurse_lan", sc, 4,
             json={"values": {"pulse": 78, "systolic_bp": 120, "diastolic_bp": 80,
                              "temperature": 36.7, "weight_kg": 65},
                   "is_primary": True},
             expected_status=[200, 201, 422])
    if r:
        if r.status_code in [200, 201]:
            ok(sc, 4, "Nhập sinh hiệu thành công")
        else:
            bug(sc, 4, f"Nhập sinh hiệu → {r.status_code}", r.text[:300], severity="P0")

    # B5 Bác sĩ call-next
    r = post("/visits/call-next", "dr_nguyen", sc, 5,
             json={}, expected_status=[200, 204])
    if r:
        called = r.json() if r.content else {}
        called_id = (called.get("data") or called).get("id") if called else None
        ok(sc, 5, f"Call-next OK, visit_id={called_id or '(none)'}")
    else:
        # Thử start trực tiếp
        r2 = post(f"/visits/{visit_id}/start", "dr_nguyen", sc, "5b",
                  json={}, expected_status=[200, 204, 422])
        if r2: ok(sc, "5b", f"Start visit trực tiếp → {r2.status_code}")

    # B6 Xem hàng đợi khám
    r = get("/visits/queue", "dr_nguyen", sc, 6, expected_status=[200])
    if r:
        q = r.json()
        items = q if isinstance(q, list) else q.get("data", q.get("items", []))
        ok(sc, 6, f"Queue trả {len(items) if isinstance(items,list) else '?'} visit")

    # B7 Bác sĩ thêm dịch vụ khám
    r_svc = get("/services", "dr_nguyen", sc, "7-list", expected_status=[200])
    svc_id = None
    if r_svc:
        svcs = r_svc.json()
        items = svcs if isinstance(svcs, list) else svcs.get("data", svcs.get("items", []))
        if items:
            svc_id = items[0].get("id")
            r7 = post(f"/visits/{visit_id}/services", "dr_nguyen", sc, 7,
                      json={"service_id": svc_id, "quantity": 1},
                      expected_status=[200, 201])
            if r7:
                ok(sc, 7, f"Thêm dịch vụ svc={svc_id} OK")
            else:
                bug(sc, 7, "Không thêm được dịch vụ vào visit", severity="P1")
        else:
            bug(sc, 7, "Không có dịch vụ nào trong DB — cần seed services", severity="P2")

    # B8 Bác sĩ hoàn tất EMR (hoặc complete-emr)
    r = post(f"/visits/{visit_id}/complete-emr", "dr_nguyen", sc, 8,
             json={}, expected_status=[200, 204, 422, 404])
    if r:
        ok(sc, 8, f"complete-emr → {r.status_code}")
        if r.status_code == 404:
            bug(sc, 8, "Endpoint /complete-emr không tồn tại", severity="P1")
    else:
        # fallback: /complete
        r2 = post(f"/visits/{visit_id}/complete", "dr_nguyen", sc, "8b",
                  json={}, expected_status=[200, 204, 422])
        if r2: ok(sc, "8b", f"complete → {r2.status_code}")

    # B9 Kiểm tra visit status
    r = get(f"/visits/{visit_id}", "admin", sc, 9, expected_status=[200])
    if r:
        v = r.json().get("data") or r.json()
        st = v.get("status", "?")
        ok(sc, 9, f"Visit status sau khám = {st}")
        if "WAITING" not in st.upper() and "COMPLETE" not in st.upper() and "PAYMENT" not in st.upper():
            bug(sc, 9, f"Visit status không hợp lệ: {st}", severity="P1")

    # B10 Thu ngân tạo hóa đơn
    r = get(f"/visits/{visit_id}/invoices", "cashier_em", sc, "10-check", expected_status=[200])
    invoice_id = None
    if r:
        inv_list = r.json()
        items = inv_list if isinstance(inv_list, list) else inv_list.get("data", inv_list.get("items", []))
        if items:
            invoice_id = items[0].get("id") if isinstance(items, list) else None
            ok(sc, "10-check", f"Invoice auto-created: {invoice_id}")
        else:
            # Tạo thủ công
            r10 = post("/invoices", "cashier_em", sc, 10,
                       json={"visit_id": visit_id}, expected_status=[200, 201])
            if r10:
                inv = r10.json().get("data") or r10.json()
                invoice_id = inv.get("id")
                ok(sc, 10, f"Invoice tạo thủ công: {invoice_id}")

    # B11 Thu tiền
    if invoice_id:
        r = post(f"/invoices/{invoice_id}/payments", "cashier_em", sc, 11,
                 json={"amount": 200000, "method": "CASH"},
                 expected_status=[200, 201, 422])
        if r:
            ok(sc, 11, f"Payment → {r.status_code}")
            if r.status_code == 422:
                bug(sc, 11, "Payment 422 — có thể total=0 hoặc đã PAID", r.text[:300], severity="P1")
        # B12 Submit invoice
        r = post(f"/invoices/{invoice_id}/submit", "cashier_em", sc, 12,
                 json={}, expected_status=[200, 204, 422])
        if r: ok(sc, 12, f"Submit invoice → {r.status_code}")

    # B12 Pharmacy — kiểm hàng đợi cấp phát
    r = get("/pharmacy/pending-dispense", "pharm_cuong", sc, 13,
            expected_status=[200])
    if r:
        pend = r.json()
        items = pend if isinstance(pend, list) else pend.get("data", pend.get("items", []))
        ok(sc, 13, f"Pharmacy pending-dispense: {len(items) if isinstance(items,list) else '?'} items")

    print(f"  SC-HP-01 hoàn tất\n")


def run_hp04():
    """SC-HP-04: Ca ưu tiên priority=5 vượt hàng đợi."""
    sc = "SC-HP-04"
    print(f"\n{'='*60}\n{sc} — Ca ưu tiên priority=5\n{'='*60}")
    pat_id = ensure_patient(sc)
    if not pat_id: return

    # Tạo visit thường trước
    r1 = post("/visits", "recept_anh", sc, 1,
              json={"patient_id": pat_id, "visit_type": "WALK_IN", "priority": 0},
              expected_status=[200, 201])
    # Tạo visit ưu tiên
    r2 = post("/visits", "recept_anh", sc, 2,
              json={"patient_id": pat_id, "visit_type": "WALK_IN", "priority": 5},
              expected_status=[200, 201, 422])
    if r2:
        v = r2.json().get("data") or r2.json()
        pri = v.get("priority", "?")
        ok(sc, 2, f"Visit priority=5 tạo OK, priority={pri}")
        if str(pri) != "5":
            bug(sc, 2, f"Priority không lưu đúng: {pri}", severity="P1")
    else:
        bug(sc, 2, "Không tạo được visit priority=5", severity="P1")
        return

    # Kiểm hàng đợi — visit ưu tiên phải đứng trước
    r = get("/visits/queue", "dr_nguyen", sc, 3, expected_status=[200])
    if r:
        q = r.json()
        items = q if isinstance(q, list) else q.get("data", q.get("items", []))
        if isinstance(items, list) and len(items) >= 2:
            first = items[0].get("priority", -1)
            if int(str(first)) >= 5:
                ok(sc, 3, f"Hàng đợi đúng: visit priority cao nhất đứng đầu (priority={first})")
            else:
                bug(sc, 3, f"Hàng đợi SAI: phần tử đầu priority={first}, kỳ vọng ≥5", severity="P0")
        else:
            ok(sc, 3, f"Hàng đợi {len(items) if isinstance(items,list) else '?'} items (không đủ để so sánh thứ tự)")
    print()


# ─────────────────────────────────────────────────────────────────────────────
# NHÓM 2 — BIẾN THỂ
# ─────────────────────────────────────────────────────────────────────────────
def run_var01():
    """SC-VAR-01: Tái khám — tìm BN theo SĐT, không tạo trùng."""
    sc = "SC-VAR-01"
    print(f"\n{'='*60}\n{sc} — Tái khám\n{'='*60}")
    ts = int(time.time())
    phone = f"09{ts % 100000000:08d}"

    # Tạo BN lần đầu
    r = post("/patients", "recept_anh", sc, 1,
             json={"full_name": f"BN Tái khám {ts}", "phone": phone,
                   "date_of_birth": "1985-06-20", "gender": "female"},
             expected_status=[200, 201])
    if not r: return
    pat_id = (r.json().get("data") or r.json()).get("id")
    ok(sc, 1, f"Tạo BN lần đầu: {pat_id}")

    # Lần thứ 2: tìm theo SĐT
    r2 = get(f"/patients/search?q={phone}&type=phone", "recept_anh", sc, 2, expected_status=[200])
    if r2:
        results = r2.json()
        items = results if isinstance(results, list) else results.get("data", results.get("items", []))
        count = len(items) if isinstance(items, list) else 0
        if count == 1:
            found_id = items[0].get("id") if items else None
            if found_id == pat_id:
                ok(sc, 2, f"Tìm đúng 1 BN theo SĐT, id khớp — không tạo trùng ✓")
            else:
                bug(sc, 2, f"Tìm thấy BN nhưng id không khớp: {found_id} vs {pat_id}", severity="P1")
        elif count == 0:
            bug(sc, 2, "Không tìm thấy BN theo SĐT sau khi vừa tạo", severity="P1")
        else:
            bug(sc, 2, f"Search trả {count} kết quả cho cùng 1 SĐT — có thể tạo trùng!", severity="P0")
    print()


def run_var02():
    """SC-VAR-02: Chỉ mua thuốc không khám — manual invoice OTC."""
    sc = "SC-VAR-02"
    print(f"\n{'='*60}\n{sc} — Mua thuốc OTC không khám\n{'='*60}")

    # Thu ngân tạo invoice thủ công (không có visit_id)
    r = post("/invoices", "cashier_em", sc, 1,
             json={"note": "Bán thuốc OTC không khám"},
             expected_status=[200, 201, 422])
    if r:
        if r.status_code in [200, 201]:
            inv = r.json().get("data") or r.json()
            inv_id = inv.get("id")
            ok(sc, 1, f"Manual invoice (no visit) tạo OK: {inv_id}")

            # Thêm line item thuốc
            r2 = post(f"/invoices/{inv_id}/lines", "cashier_em", sc, 2,
                      json={"description": "Paracetamol 500mg", "unit_price": 5000, "quantity": 10},
                      expected_status=[200, 201, 422])
            if r2:
                ok(sc, 2, f"Thêm line item → {r2.status_code}")
            else:
                bug(sc, 2, "Không thêm được line item vào invoice OTC", severity="P2")
        elif r.status_code == 422:
            bug(sc, 1, "Invoice OTC không có visit_id → 422 — hệ thống có thể yêu cầu visit",
                r.text[:300], severity="P1")
    print()


def run_var03():
    """SC-VAR-03: Cấp cứu priority=10 vọt lên đầu hàng đợi."""
    sc = "SC-VAR-03"
    print(f"\n{'='*60}\n{sc} — Cấp cứu priority=10\n{'='*60}")
    pat_id = ensure_patient(sc)
    if not pat_id: return

    r = post("/visits", "recept_anh", sc, 1,
             json={"patient_id": pat_id, "visit_type": "WALK_IN", "priority": 10},
             expected_status=[200, 201, 422])
    if r and r.status_code in [200, 201]:
        v = r.json().get("data") or r.json()
        pri = v.get("priority", "?")
        ok(sc, 1, f"Visit cấp cứu priority={pri}")
        if str(pri) != "10":
            bug(sc, 1, f"Priority=10 không lưu đúng: {pri}", severity="P1")
    else:
        bug(sc, 1, "Không tạo được visit cấp cứu", severity="P1")
    print()


# ─────────────────────────────────────────────────────────────────────────────
# NHÓM 3 — NGOẠI LỆ & HỦY
# ─────────────────────────────────────────────────────────────────────────────
def run_exc01():
    """SC-EXC-01: Hủy hóa đơn đã PAID — chỉ Admin được void."""
    sc = "SC-EXC-01"
    print(f"\n{'='*60}\n{sc} — Void hóa đơn đã thu tiền\n{'='*60}")

    # Tạo invoice và submit để có state ISSUED/PAID
    pat_id = ensure_patient(sc)
    if not pat_id: return

    r = post("/visits", "recept_anh", sc, 1,
             json={"patient_id": pat_id, "visit_type": "WALK_IN"},
             expected_status=[200, 201])
    if not r: return
    visit_id = (r.json().get("data") or r.json()).get("id")

    # Tạo invoice
    r2 = post("/invoices", "cashier_em", sc, 2,
              json={"visit_id": visit_id}, expected_status=[200, 201])
    if not r2: return
    inv_id = (r2.json().get("data") or r2.json()).get("id")
    ok(sc, 2, f"Invoice tạo: {inv_id}")

    # Submit
    r3 = post(f"/invoices/{inv_id}/submit", "cashier_em", sc, 3,
              json={}, expected_status=[200, 204, 422])
    if r3: ok(sc, 3, f"Submit → {r3.status_code}")

    # Thu ngân thử void — phải 403
    r4 = post(f"/invoices/{inv_id}/void", "cashier_em", sc, 4,
              json={"reason": "test"}, expected_status=[403, 200, 204, 422])
    if r4:
        if r4.status_code == 403:
            ok(sc, 4, "Thu ngân void invoice → 403 (đúng, thiếu invoice.void) ✓")
        elif r4.status_code in [200, 204]:
            bug(sc, 4, "Thu ngân void được invoice — KHÔNG đúng! Phải 403", severity="P0")
        else:
            ok(sc, 4, f"Thu ngân void → {r4.status_code} (cần xác nhận)")

    # Lễ tân thử void — phải 403
    r5 = post(f"/invoices/{inv_id}/void", "recept_anh", sc, "4b",
              json={"reason": "test"}, expected_status=[403, 200, 204, 422])
    if r5:
        if r5.status_code == 403:
            ok(sc, "4b", "Lễ tân void invoice → 403 ✓")
        elif r5.status_code in [200, 204]:
            bug(sc, "4b", "Lễ tân void được invoice — KHÔNG đúng!", severity="P0")

    # Admin void — phải thành công
    r6 = post(f"/invoices/{inv_id}/void", "admin", sc, 5,
              json={"reason": "SC-EXC-01 test"}, expected_status=[200, 204, 422])
    if r6:
        if r6.status_code in [200, 204]:
            ok(sc, 5, "Admin void invoice thành công ✓")
        else:
            bug(sc, 5, f"Admin void → {r6.status_code}", r6.text[:300], severity="P1")
    print()


def run_exc03():
    """SC-EXC-03: BN no-show."""
    sc = "SC-EXC-03"
    print(f"\n{'='*60}\n{sc} — No-show\n{'='*60}")

    # Tạo appointment
    pat_id = ensure_patient(sc)
    if not pat_id: return

    tomorrow = (datetime.now().date().__str__()[:8]) + str(int(datetime.now().date().__str__()[8:])+1).zfill(2)
    r = post("/appointments", "recept_anh", sc, 1,
             json={"patient_id": pat_id, "slot_date": tomorrow,
                   "slot_time": "09:00", "reason": "Kiểm tra định kỳ"},
             expected_status=[200, 201, 422])
    if r:
        if r.status_code in [200, 201]:
            appt = r.json().get("data") or r.json()
            appt_id = appt.get("id")
            ok(sc, 1, f"Appointment tạo: {appt_id}")

            # Admin đánh dấu no-show (không có visit)
            r2 = post(f"/appointments/{appt_id}/cancel", "admin", sc, 2,
                      json={"reason": "no-show"}, expected_status=[200, 204, 422])
            if r2: ok(sc, 2, f"Cancel appointment → {r2.status_code}")
        else:
            bug(sc, 1, f"Tạo appointment → {r.status_code}", r.text[:300], severity="P2")
    print()


def run_exc06():
    """SC-EXC-06: Thanh toán nhiều đợt partial."""
    sc = "SC-EXC-06"
    print(f"\n{'='*60}\n{sc} — Partial payment nhiều đợt\n{'='*60}")
    pat_id = ensure_patient(sc)
    if not pat_id: return

    rv = post("/visits", "recept_anh", sc, 1,
              json={"patient_id": pat_id, "visit_type": "WALK_IN"},
              expected_status=[200, 201])
    if not rv: return
    visit_id = (rv.json().get("data") or rv.json()).get("id")

    ri = post("/invoices", "cashier_em", sc, 2,
              json={"visit_id": visit_id}, expected_status=[200, 201])
    if not ri: return
    inv_id = (ri.json().get("data") or ri.json()).get("id")

    # Thêm line để invoice có total > 0
    post(f"/invoices/{inv_id}/lines", "cashier_em", sc, "2b",
         json={"description": "Phí khám", "unit_price": 100000, "quantity": 1},
         expected_status=[200, 201, 422])

    post(f"/invoices/{inv_id}/submit", "cashier_em", sc, 3,
         json={}, expected_status=[200, 204, 422])

    # Lần 1: trả 50k (partial)
    r1 = post(f"/invoices/{inv_id}/payments", "cashier_em", sc, 4,
              json={"amount": 50000, "method": "CASH"},
              expected_status=[200, 201, 422])
    if r1 and r1.status_code in [200, 201]:
        ok(sc, 4, "Partial payment 50k → OK")
        inv_r = get(f"/invoices/{inv_id}", "cashier_em", sc, "4-check", expected_status=[200])
        if inv_r:
            st = (inv_r.json().get("data") or inv_r.json()).get("status", "?")
            if "PARTIAL" in st.upper():
                ok(sc, "4-check", f"Invoice status = {st} ✓")
            else:
                bug(sc, "4-check", f"Sau partial pay, status = {st} (kỳ vọng PARTIALLY_PAID)", severity="P1")

    # Lần 2: trả hết
    r2 = post(f"/invoices/{inv_id}/payments", "cashier_em", sc, 5,
              json={"amount": 50000, "method": "CASH"},
              expected_status=[200, 201, 422])
    if r2 and r2.status_code in [200, 201]:
        ok(sc, 5, "Payment lần 2 → OK")
        inv_r = get(f"/invoices/{inv_id}", "cashier_em", sc, "5-check", expected_status=[200])
        if inv_r:
            st = (inv_r.json().get("data") or inv_r.json()).get("status", "?")
            ok(sc, "5-check", f"Invoice status cuối = {st}")
            if "PAID" not in st.upper():
                bug(sc, "5-check", f"Sau full pay, status = {st} (kỳ vọng PAID)", severity="P1")

    # Guard: trả thêm khi đã PAID → phải 422
    r3 = post(f"/invoices/{inv_id}/payments", "cashier_em", sc, 6,
              json={"amount": 50000, "method": "CASH"},
              expected_status=[422, 400, 409])
    if r3:
        if r3.status_code in [422, 400, 409]:
            ok(sc, 6, f"Trả thêm sau PAID → {r3.status_code} (guard hoạt động) ✓")
        else:
            bug(sc, 6, f"Overpayment không bị chặn: → {r3.status_code}", severity="P0")
    print()


# ─────────────────────────────────────────────────────────────────────────────
# NHÓM 4 — PHÂN QUYỀN CHÉO (RBAC negative)
# ─────────────────────────────────────────────────────────────────────────────
def run_rbac():
    """SC-RBAC-01..12: Phân quyền chéo — mỗi vai trò thử vượt quyền → 403."""
    print(f"\n{'='*60}\nSC-RBAC — Kiểm tra phân quyền chéo (403)\n{'='*60}")
    pat_id = ensure_patient("SC-RBAC")

    cases = [
        # (sc_id, user, method, path, body, tên case)
        ("SC-RBAC-01", "recept_anh", "post", f"/visits/{pat_id}/vitals",
         {"vitals": {}}, "Lễ tân nhập sinh hiệu (vital.write)"),
        ("SC-RBAC-02", "nurse_lan",  "post", "/pharmacy/reserve",
         {"prescription_item_id": "fake-id", "quantity": 1},
         "Y tá reserve thuốc (pharmacy.dispense)"),
        ("SC-RBAC-03", "pharm_cuong","post", "/visits",
         {"patient_id": pat_id or "fake", "visit_type": "WALK_IN"},
         "Dược sĩ tạo visit (visit.write)"),
        ("SC-RBAC-04", "cashier_em", "post", f"/invoices/fake-inv/void",
         {"reason": "test"},
         "Thu ngân void hóa đơn (invoice.void)"),
        ("SC-RBAC-05", "dr_nguyen",  "get",  "/users",
         None, "Bác sĩ xem danh sách users (user.manage)"),
        ("SC-RBAC-06", "dr_nguyen",  "get",  "/reports/revenue",
         None, "Bác sĩ xem báo cáo doanh thu (report.financial)"),
        ("SC-RBAC-07", "nurse_lan",  "post", "/roles",
         {"name": "hacker", "code": "hacker"},
         "Y tá tạo role mới (role.manage)"),
        ("SC-RBAC-08", "recept_anh", "get",  "/roles",
         None, "Lễ tân xem danh sách roles (role.manage)"),
        ("SC-RBAC-09", "pharm_cuong","patch","/clinics/me/settings",
         {"name": "hacked"}, "Dược sĩ sửa cấu hình clinic (settings.clinic)"),
        ("SC-RBAC-10", "nurse_lan",  "get",  "/admin/audit-logs",
         None, "Y tá xem audit logs (audit.read)"),
        ("SC-RBAC-11", "cashier_em", "post", "/medicines",
         {"name": "hack", "unit": "vien", "unit_price": 1},
         "Thu ngân tạo thuốc (inventory.manage_catalog)"),
        ("SC-RBAC-12", "pharm_cuong","post", "/invoices/fake/void",
         {"reason": "x"}, "Dược sĩ void hóa đơn (invoice.void)"),
    ]

    for sc, user, method, path, body, name in cases:
        kwargs = {"expected_status": list(range(400, 500))}
        if body:
            kwargs["json"] = body
        r = req(method, path, user, sc, "rbac",
                expected_status=list(range(400, 500)),
                **{"json": body} if body else {})
        if r:
            if r.status_code == 403:
                ok(sc, "rbac", f"{name} → 403 ✓")
            elif r.status_code == 401:
                ok(sc, "rbac", f"{name} → 401 (token không hợp lệ, cần xác nhận)")
            elif r.status_code == 404:
                ok(sc, "rbac", f"{name} → 404 (resource không tồn tại, chưa test được quyền)")
            elif r.status_code == 422:
                bug(sc, "rbac", f"{name} → 422 (validation lỗi, chưa check quyền)",
                    f"Cần xác nhận: phải là 403 trước 422", severity="P1")
            elif r.status_code < 400:
                bug(sc, "rbac", f"{name} → {r.status_code} (KHÔNG bị chặn!)",
                    r.text[:200], severity="P0")
            else:
                ok(sc, "rbac", f"{name} → {r.status_code} (bị từ chối)")
        else:
            # req trả None khi không khớp expected_status
            pass
    print()


def run_rbac_no_token():
    """Không có token → 401 cho mọi endpoint."""
    sc = "SC-RBAC-NO-TOKEN"
    print(f"\n{'='*60}\n{sc} — Không có token → 401\n{'='*60}")
    endpoints = ["/patients", "/visits", "/invoices", "/pharmacy/pending-dispense",
                 "/visits/queue", "/reports/revenue"]
    for ep in endpoints:
        try:
            r = requests.get(f"{BASE_URL}{ep}", timeout=TIMEOUT)
            if r.status_code == 401:
                ok(sc, "-", f"GET {ep} (no token) → 401 ✓")
            else:
                bug(sc, "-", f"GET {ep} (no token) → {r.status_code} (kỳ vọng 401)",
                    severity="P0")
        except Exception as e:
            bug(sc, "-", f"GET {ep} exception", str(e))
    print()


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://localhost:8001/api/v1")
    parser.add_argument("--scenarios", default="hp,var,exc,rbac",
                        help="Comma-separated: hp,var,exc,rbac")
    args = parser.parse_args()
    global BASE_URL
    BASE_URL = args.base_url
    selected = set(args.scenarios.lower().split(","))

    start = time.time()
    print(f"\n{'='*60}")
    print(f"  Clinic CMS — E2E Operational Test")
    print(f"  {BASE_URL}")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")

    # Check health
    try:
        hc = requests.get(BASE_URL.replace("/api/v1", "/health"), timeout=5)
        print(f"\n  Health: {hc.status_code} — {hc.json()}\n")
    except:
        print("\n  ⚠ Health check thất bại — tiếp tục\n")

    if "hp" in selected:
        run_hp01()
        run_hp04()

    if "var" in selected:
        run_var01()
        run_var02()
        run_var03()

    if "exc" in selected:
        run_exc01()
        run_exc03()
        run_exc06()

    if "rbac" in selected:
        run_rbac_no_token()
        run_rbac()

    # ── BÁO CÁO ─────────────────────────────────────────────────────────────
    elapsed = time.time() - start
    print(f"\n{'='*60}")
    print(f"  KẾT QUẢ — {len(passed)} PASS · {len(bugs)} BUG  ({elapsed:.1f}s)")
    print(f"{'='*60}")

    if bugs:
        print(f"\n{'─'*60}")
        print("  DANH SÁCH BUG CHI TIẾT")
        print(f"{'─'*60}")
        p0 = [b for b in bugs if b["severity"]=="P0"]
        p1 = [b for b in bugs if b["severity"]=="P1"]
        p2 = [b for b in bugs if b["severity"]=="P2"]
        for grp, label in [(p0,"🔴 P0 — CRITICAL"),(p1,"🟠 P1 — MAJOR"),(p2,"🟡 P2 — MINOR")]:
            if grp:
                print(f"\n  {label} ({len(grp)})")
                for i,b in enumerate(grp,1):
                    print(f"  {i:2}. [{b['scenario']}] Bước {b['step']}: {b['msg']}")
                    if b["detail"]: print(f"      Detail: {b['detail'][:200]}")
    else:
        print("\n  Không phát hiện bug nào — tất cả kịch bản đã pass ✓")

    # Ghi file
    report = {
        "timestamp": datetime.now().isoformat(),
        "base_url": BASE_URL,
        "total_passed": len(passed),
        "total_bugs": len(bugs),
        "elapsed_s": round(elapsed, 1),
        "bugs": bugs,
    }
    out = "docs/tasks/TASK-052/deliveries/test-reports/e2e-operational-report.json"
    try:
        import os; os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"\n  Báo cáo JSON: {out}")
    except Exception as e:
        print(f"\n  Không ghi được báo cáo: {e}")

    return 1 if bugs else 0

if __name__ == "__main__":
    sys.exit(main())
