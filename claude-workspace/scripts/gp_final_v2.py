#!/usr/bin/env python3
"""Golden Path E2E v2 - correct API schemas and state machine."""
import urllib.request
import json
import urllib.error
import time

BASE = 'http://localhost:8001'
results = {}


def api(method, path, token=None, data=None):
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['Authorization'] = 'Bearer ' + token
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(BASE + path, data=body, headers=headers, method=method)
    try:
        r = urllib.request.urlopen(req)
        return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def login(username, password):
    status, d = api('POST', '/api/v1/auth/login', data={'username': username, 'password': password})
    if status != 200:
        print('LOGIN FAILED: ' + username)
        return None, None
    data = d['data']
    return data['access_token'], data.get('active_clinic_id')


print('=== GP1: Multi-clinic Login + Auto-resolve ===')
admin_tok, admin_clinic = login('admin', 'Demo@1234')
doctor_tok, dr_clinic = login('dr_nguyen', 'Doctor@1234')
recept_tok, rec_clinic = login('recept_anh', 'Recept@1234')
pharm_tok, ph_clinic = login('pharm_cuong', 'Pharm@1234')

s2, body2 = api('GET', '/api/v1/auth/clinics', token=admin_tok)
clinic_list = body2.get('data', [])
clinic_name = clinic_list[0].get('name') if clinic_list else None

gp1_pass = all([admin_tok, doctor_tok, recept_tok, pharm_tok, admin_clinic, s2 == 200])
results['GP1'] = {
    'admin_ok': admin_tok is not None,
    'doctor_ok': doctor_tok is not None,
    'recept_ok': recept_tok is not None,
    'pharm_ok': pharm_tok is not None,
    'auto_clinic_resolved': admin_clinic is not None,
    'clinic_name': clinic_name,
    'verdict': 'PASS' if gp1_pass else 'FAIL'
}
print('GP1: verdict=' + results['GP1']['verdict'] + ', clinic=' + str(clinic_name))

print()
print('=== GP2: Reception Walk-in ===')
_, body = api('GET', '/api/v1/patients?limit=1', token=admin_tok)
patients_list = body.get('data', [])
patient_id = patients_list[0]['id'] if isinstance(patients_list, list) and patients_list else None
patient_name = patients_list[0].get('full_name') if patient_id else None

gp2_id = None
if patient_id:
    s, body = api('POST', '/api/v1/visits', token=recept_tok, data={
        'patient_id': patient_id,
        'visit_type': 'walk_in',
        'visit_date': '2026-05-01',
        'chief_complaint': 'GP2 walk-in triage test'
    })
    walkin_visit = body.get('data', body)
    gp2_id = walkin_visit.get('id')
    walkin_status = walkin_visit.get('status')
    time.sleep(0.8)
    s_get, _ = api('GET', '/api/v1/visits/' + gp2_id, token=recept_tok)
    results['GP2'] = {
        'visit_created': s in (200, 201),
        'visit_visible_after': s_get == 200,
        'visit_status': walkin_status,
        'verdict': 'PASS' if s in (200, 201) and s_get == 200 else 'FAIL'
    }
    print('GP2: create=' + str(s) + ', visible=' + str(s_get) + ', verdict=' + results['GP2']['verdict'])

print()
print('=== GP3: Doctor Consultation Full Flow ===')
gp3_id = None
rx_id = None
if patient_id:
    # Create visit
    s, body = api('POST', '/api/v1/visits', token=recept_tok, data={
        'patient_id': patient_id,
        'visit_type': 'walk_in',
        'visit_date': '2026-05-01',
        'chief_complaint': 'GP3 kham tong quat - cao huyet ap'
    })
    gp3_visit = body.get('data', body)
    gp3_id = gp3_visit.get('id')
    print('  Visit created: ' + str(s) + ', id=' + str(gp3_id))
    time.sleep(1.0)  # Wait for write visibility

    # Start visit (WAITING -> IN_PROGRESS)
    _, dr_info = api('GET', '/api/v1/users/me', token=doctor_tok)
    dr_data = dr_info.get('data', dr_info) if isinstance(dr_info, dict) else {}
    dr_uid = dr_data.get('id') if isinstance(dr_data, dict) else None

    s_start, start_body = api('POST', '/api/v1/visits/' + gp3_id + '/start', token=doctor_tok)
    if s_start >= 400:
        print('  Start error: ' + json.dumps(start_body)[:200])
    print('  Start visit: ' + str(s_start))

    # SOAP
    s1, soap_body = api('POST', '/api/v1/visits/' + gp3_id + '/soap', token=doctor_tok, data={
        'subjective': 'Dau dau met moi 3 ngay',
        'objective': 'HA 130/85 mach 80 nhiet 37.2',
        'assessment': 'Cao huyet ap nhe',
        'plan': 'Ke don amlodipine 5mg 1 vien/ngay x 30 ngay'
    })
    print('  SOAP: ' + str(s1))

    # Diagnosis
    s2, dx_body = api('POST', '/api/v1/visits/' + gp3_id + '/diagnosis', token=doctor_tok, data={
        'items': [{'icd10_code': 'I10', 'diagnosis_type': 'primary', 'notes': 'Cao huyet ap co ban'}]
    })
    print('  Diagnosis: ' + str(s2))

    # ICD10 search
    s3, icd_body = api('GET', '/api/v1/icd10/search?q=gout', token=doctor_tok)
    icd_count = len(icd_body.get('items', []))

    # Get medicines + inventory
    _, meds_resp = api('GET', '/api/v1/medicines?limit=1', token=doctor_tok)
    med_list = meds_resp.get('data', []) if isinstance(meds_resp, dict) else []
    if not isinstance(med_list, list) or not med_list:
        _, meds_resp2 = api('GET', '/api/v1/medicines?limit=1', token=admin_tok)
        med_list = meds_resp2.get('data', meds_resp2.get('items', [])) if isinstance(meds_resp2, dict) else []

    rx_status_code = None
    if med_list and isinstance(med_list, list):
        med = med_list[0]
        med_id = med.get('id')
        med_name = med.get('name', 'Paracetamol 500mg')
        med_unit = med.get('base_unit', 'vien')
        print('  Using medicine: ' + str(med_name))

        s_rx, rx_body = api('POST', '/api/v1/visits/' + gp3_id + '/prescriptions', token=doctor_tok, data={
            'doctor_id': str(dr_uid),
            'items': [{
                'medicine_id': str(med_id),
                'medicine_name': med_name,
                'dosage': '1 vien x 2 lan/ngay',
                'quantity': 10,
                'unit': med_unit,
                'dispense_source': 'in_house'
            }]
        })
        rx_data = rx_body.get('data', rx_body) if isinstance(rx_body, dict) else {}
        rx_id = rx_data.get('id')
        rx_status_code = s_rx
        if s_rx >= 400:
            print('  Rx error: ' + json.dumps(rx_body)[:300])
        print('  Prescription: ' + str(s_rx) + ', id=' + str(rx_id))
    else:
        print('  No medicines available for prescription')

    # Complete visit (IN_PROGRESS -> AWAITING_PAYMENT)
    s_complete, comp_body = api('POST', '/api/v1/visits/' + gp3_id + '/complete', token=doctor_tok)
    if s_complete >= 400:
        print('  Complete error: ' + json.dumps(comp_body)[:200])
    print('  Complete: ' + str(s_complete))

    gp3_pass = s1 == 200 and s2 in (200, 201) and s_start in (200, 201) and s_complete in (200, 201)
    results['GP3'] = {
        'visit_id': gp3_id,
        'start': s_start,
        'soap': s1,
        'diagnosis': s2,
        'icd10_count': icd_count,
        'prescription_id': rx_id,
        'prescription_status': rx_status_code,
        'complete': s_complete,
        'verdict': 'PASS' if gp3_pass else 'PARTIAL'
    }
    print('GP3 verdict: ' + results['GP3']['verdict'])

print()
print('=== GP4: Pharmacy Dispense ===')
rx_id_gp4 = results.get('GP3', {}).get('prescription_id')
if rx_id_gp4:
    s_disp, disp_body = api('POST', '/api/v1/prescriptions/' + rx_id_gp4 + '/dispense', token=pharm_tok)
    if s_disp >= 400:
        print('  Dispense error: ' + json.dumps(disp_body)[:400])
    disp_data = disp_body.get('data', disp_body) if isinstance(disp_body, dict) else {}
    results['GP4'] = {
        'dispense_status': s_disp,
        'success': s_disp in (200, 201),
        'verdict': 'PASS' if s_disp in (200, 201) else 'FAIL'
    }
    print('GP4: dispense=' + str(s_disp) + ', verdict=' + results['GP4']['verdict'])
else:
    results['GP4'] = {'success': False, 'verdict': 'BLOCKED', 'note': 'no_prescription'}
    print('GP4: BLOCKED - no prescription')

print()
print('=== GP5: Billing Invoice + Payment ===')
if gp3_id:
    # Invoice from visit
    s_inv, inv_body = api('POST', '/api/v1/visits/' + gp3_id + '/invoices', token=admin_tok)
    inv_data = inv_body.get('data', inv_body) if isinstance(inv_body, dict) else {}
    invoice_id = inv_data.get('id')
    print('  Invoice create: ' + str(s_inv) + ', id=' + str(invoice_id))

    pay_status = None
    pay_id = None
    if invoice_id:
        # Submit invoice (draft -> confirmed/pending)
        s_submit, sub_body = api('POST', '/api/v1/invoices/' + invoice_id + '/submit', token=admin_tok)
        print('  Submit invoice: ' + str(s_submit))
        if s_submit >= 400:
            print('  Submit error: ' + json.dumps(sub_body)[:200])

        _, inv_detail = api('GET', '/api/v1/invoices/' + invoice_id, token=admin_tok)
        inv = inv_detail.get('data', inv_detail) if isinstance(inv_detail, dict) else {}
        total_raw = inv.get('total_amount', 0)
        total = float(str(total_raw or '0'))
        inv_status = inv.get('status')
        print('  Invoice total=' + str(total) + ', status=' + str(inv_status))

        s_pay, pay_body = api('POST', '/api/v1/invoices/' + invoice_id + '/payments', token=admin_tok, data={
            'amount': max(total, 1.0),
            'payment_method': 'cash'
        })
        pay_data = pay_body.get('data', pay_body) if isinstance(pay_body, dict) else {}
        pay_status = s_pay
        pay_id = pay_data.get('id')
        print('  Payment: ' + str(s_pay) + ', id=' + str(pay_id))
        if s_pay >= 400:
            print('  Pay error: ' + json.dumps(pay_body)[:300])

    gp5_pass = s_inv in (200, 201) and pay_status in (200, 201)
    results['GP5'] = {
        'invoice_status': s_inv,
        'invoice_id': invoice_id,
        'payment_status': pay_status,
        'payment_id': pay_id,
        'verdict': 'PASS' if gp5_pass else ('PARTIAL' if s_inv in (200, 201) else 'FAIL')
    }
    print('GP5 verdict: ' + results['GP5']['verdict'])
else:
    results['GP5'] = {'verdict': 'BLOCKED', 'note': 'no_visit'}

print()
print('=== FINAL GOLDEN PATH SUMMARY ===')
verdicts = {}
for gp, data in results.items():
    verdicts[gp] = data.get('verdict', 'UNKNOWN')
    print(gp + ': ' + verdicts[gp])

overall = 'PASS' if all(v in ('PASS',) for v in verdicts.values()) else \
          'PARTIAL' if any(v in ('PASS', 'PARTIAL') for v in verdicts.values()) else 'FAIL'
print()
print('OVERALL: ' + overall)
print()
print(json.dumps(results, indent=2))
