# API Specification: Patient Management Endpoints

**Task:** TASK-005 — Patient Management  
**Date:** 2026-04-27  
**Status:** Final Delivery  

---

## Overview

This document provides endpoint-by-endpoint reference for all 11 patient management APIs. All endpoints require JWT authentication via `Authorization: Bearer {token}` header.

**Base URL:** `/api/v1`

---

## Table of Contents

1. [List Patients](#1-list-patients)
2. [Create Patient](#2-create-patient)
3. [Search Patients](#3-search-patients)
4. [Get Patient Details](#4-get-patient-details)
5. [Update Patient](#5-update-patient)
6. [Delete Patient](#6-delete-patient)
7. [Add Guardian Relation](#7-add-guardian-relation)
8. [List Patient Guardians](#8-list-patient-guardians)
9. [Delete Guardian Relation](#9-delete-guardian-relation)
10. [Merge Patients](#10-merge-patients)
11. [Undo Merge](#11-undo-merge)

---

## 1. List Patients

### Request

```http
GET /api/v1/patients?skip=0&limit=50 HTTP/1.1
Authorization: Bearer {token}
```

### Parameters

| Name | Type | Required | Description | Default |
|------|------|----------|-------------|---------|
| `skip` | integer | No | Number of records to skip (offset) | 0 |
| `limit` | integer | No | Number of records to return (max 200) | 50 |

### Response (200 OK)

```json
{
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "clinic_id": "550e8400-e29b-41d4-a716-446655440002",
      "patient_code": "BN0001",
      "full_name": "Nguyễn Văn An",
      "date_of_birth": "1990-05-15",
      "birth_year": 1990,
      "gender": "male",
      "phone": "0912345678",
      "email": "an@example.com",
      "id_number": null,
      "address_line": "123 Đường Lê Lợi",
      "ward": "Phường 1",
      "district": "Q.1",
      "province": "TP. HCM",
      "blood_type": "O+",
      "allergies": "Cephalosporin",
      "chronic_conditions": "Tiểu đường",
      "occupation": "Kỹ sư",
      "referral_source": "Đặc cách",
      "notes": "Bệnh nhân ưa thích bác sĩ A",
      "created_at": "2026-04-27T10:00:00Z",
      "updated_at": "2026-04-27T10:00:00Z",
      "is_deleted": false
    }
  ],
  "total": 150,
  "cursor": null
}
```

### Error Responses

| Status | Scenario |
|--------|----------|
| 401 | Invalid or missing token |
| 403 | Missing `patient.read` permission |

---

## 2. Create Patient

### Request

```http
POST /api/v1/patients HTTP/1.1
Authorization: Bearer {token}
Content-Type: application/json

{
  "full_name": "Nguyễn Văn An",
  "gender": "male",
  "date_of_birth": "1990-05-15",
  "birth_year": 1990,
  "phone": "0912345678",
  "email": "an@example.com",
  "id_number": null,
  "address_line": "123 Đường Lê Lợi",
  "ward": "Phường 1",
  "district": "Q.1",
  "province": "TP. HCM",
  "blood_type": "O+",
  "allergies": "Cephalosporin",
  "chronic_conditions": "Tiểu đường",
  "occupation": "Kỹ sư",
  "referral_source": "Đặc cách",
  "notes": "Bệnh nhân ưa thích bác sĩ A"
}
```

### Request Body Fields

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `full_name` | string | Yes | 1-200 chars | Patient full name (Vietnamese) |
| `gender` | string | Yes | `male`, `female`, `other` | Gender |
| `date_of_birth` | date | No | YYYY-MM-DD format, not future | Birth date (null if only birth_year provided) |
| `birth_year` | integer | No | 1900-2200 | Birth year (fallback) |
| `phone` | string | No | `0[0-9]{9,10}` | Vietnamese phone number |
| `email` | string | No | max 200 chars | Email address |
| `id_number` | string | No | max 20 chars | CCCD/CMND (excluded from audit log) |
| `address_line` | string | No | max 500 chars | Street address |
| `ward` | string | No | max 100 chars | Ward/subdistrict |
| `district` | string | No | max 100 chars | District |
| `province` | string | No | max 100 chars | Province/city |
| `blood_type` | string | No | max 5 chars | Blood type (O+, AB-, etc.) |
| `allergies` | string | No | no length limit | Allergies (free text) |
| `chronic_conditions` | string | No | no length limit | Chronic conditions (free text) |
| `occupation` | string | No | max 100 chars | Occupation |
| `referral_source` | string | No | max 100 chars | How patient was referred |
| `notes` | string | No | no length limit | General notes |

### Validation Rules

- At least one of `date_of_birth` or `birth_year` must be provided
- If both provided, `date_of_birth.year` must equal `birth_year`
- `date_of_birth` cannot be in the future (BUG-002 fix)
- Phone format must match Vietnamese pattern `0[0-9]{9,10}` if provided
- Gender must be exactly: `male`, `female`, or `other`

### Response (201 Created)

```json
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "clinic_id": "550e8400-e29b-41d4-a716-446655440002",
    "patient_code": "BN0001",
    "full_name": "Nguyễn Văn An",
    "date_of_birth": "1990-05-15",
    "birth_year": 1990,
    "gender": "male",
    "phone": "0912345678",
    "email": "an@example.com",
    "id_number": null,
    "address_line": "123 Đường Lê Lợi",
    "ward": "Phường 1",
    "district": "Q.1",
    "province": "TP. HCM",
    "blood_type": "O+",
    "allergies": "Cephalosporin",
    "chronic_conditions": "Tiểu đường",
    "occupation": "Kỹ sư",
    "referral_source": "Đặc cách",
    "notes": "Bệnh nhân ưa thích bác sĩ A",
    "created_at": "2026-04-27T10:00:00Z",
    "updated_at": "2026-04-27T10:00:00Z",
    "is_deleted": false
  },
  "warnings": [
    "A patient with the same full_name and date_of_birth already exists in this clinic (ID: 550e8400-e29b-41d4-a716-446655440003)"
  ]
}
```

### Error Responses

| Status | Scenario |
|--------|----------|
| 400 | Query string contains null bytes; input format error |
| 401 | Invalid or missing token |
| 403 | Missing `patient.write` permission |
| 422 | Validation error: DOB future, phone format, gender enum, dob/birth_year logic, etc. |

---

## 3. Search Patients

### Request

```http
GET /api/v1/patients/search?q=0912&type=phone&limit=20 HTTP/1.1
Authorization: Bearer {token}
```

### Parameters

| Name | Type | Required | Constraints | Description |
|------|------|----------|-------------|-------------|
| `q` | string | Yes | 1-200 chars, no null bytes | Search query string |
| `type` | string | No | `phone`, `name`, `code` | Search type (default: `name`) |
| `limit` | integer | No | 1-100 | Max results to return (default: 20) |

### Search Type Behavior

| Type | Mechanism | Example |
|------|-----------|---------|
| `phone` | Trigram similarity (p95=46.9ms @100k) | `q="0912"` matches "0912345678", "0912***" (prefix) |
| `name` | Full-text + unaccent fuzzy (p95=180.5ms) | `q="nguyen van an"` matches "Nguyễn Văn An" (diacritics ignored) |
| `code` | Exact match on patient_code | `q="BN0001"` matches exactly "BN0001" |

### Response (200 OK)

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "clinic_id": "550e8400-e29b-41d4-a716-446655440002",
    "patient_code": "BN0001",
    "full_name": "Nguyễn Văn An",
    "date_of_birth": "1990-05-15",
    "birth_year": 1990,
    "gender": "male",
    "phone": "0912345678",
    "email": "an@example.com",
    "address_line": "123 Đường Lê Lợi",
    "created_at": "2026-04-27T10:00:00Z",
    "updated_at": "2026-04-27T10:00:00Z",
    "is_deleted": false
  }
]
```

### Error Responses

| Status | Scenario |
|--------|----------|
| 400 | Query string contains null bytes (BUG-001 fix) |
| 401 | Invalid or missing token |
| 403 | Missing `patient.read` permission |
| 422 | Invalid `type` parameter (must be: phone/name/code) |

---

## 4. Get Patient Details

### Request

```http
GET /api/v1/patients/550e8400-e29b-41d4-a716-446655440001 HTTP/1.1
Authorization: Bearer {token}
```

### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `id` | UUID | Yes (path) | Patient ID |

### Response (200 OK)

Same structure as Create Patient `data` field (see section 2).

### Error Responses

| Status | Scenario |
|--------|----------|
| 401 | Invalid or missing token |
| 403 | Missing `patient.read` permission |
| 404 | Patient not found or belongs to different clinic (RLS enforced) |

---

## 5. Update Patient

### Request

```http
PATCH /api/v1/patients/550e8400-e29b-41d4-a716-446655440001 HTTP/1.1
Authorization: Bearer {token}
Content-Type: application/json

{
  "full_name": "Nguyễn Văn An (Updated)",
  "phone": "0987654321"
}
```

### Request Body

All fields from Create Patient are optional (partial update). Only provided fields are updated.

### Response (200 OK)

Same structure as Create Patient response (updated patient data).

### Error Responses

| Status | Scenario |
|--------|----------|
| 400 | Query string contains null bytes; input format error |
| 401 | Invalid or missing token |
| 403 | Missing `patient.write` permission |
| 404 | Patient not found |
| 422 | Validation error (same rules as Create) |

---

## 6. Delete Patient

### Request

```http
DELETE /api/v1/patients/550e8400-e29b-41d4-a716-446655440001 HTTP/1.1
Authorization: Bearer {token}
```

### Response

**204 No Content** or **200 OK** (implementation may vary)

### Error Responses

| Status | Scenario |
|--------|----------|
| 401 | Invalid or missing token |
| 403 | Missing `patient.delete` permission |
| 404 | Patient not found |

---

## 7. Add Guardian Relation

### Request

```http
POST /api/v1/patients/550e8400-e29b-41d4-a716-446655440001/guardians HTTP/1.1
Authorization: Bearer {token}
Content-Type: application/json

{
  "guardian_patient_id": "550e8400-e29b-41d4-a716-446655440004",
  "relation_type": "parent",
  "is_primary_contact": true
}
```

### Request Body Fields

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `guardian_patient_id` | UUID | Yes | — | ID of guardian/related patient |
| `relation_type` | string | Yes | `parent`, `spouse`, `child`, `other` | Type of relationship |
| `is_primary_contact` | boolean | No | — | Mark as primary contact (default: false) |

### Response (201 Created)

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440003",
  "clinic_id": "550e8400-e29b-41d4-a716-446655440002",
  "patient_id": "550e8400-e29b-41d4-a716-446655440001",
  "guardian_patient_id": "550e8400-e29b-41d4-a716-446655440004",
  "relation_type": "parent",
  "is_primary_contact": true,
  "created_at": "2026-04-27T11:00:00Z"
}
```

### Error Responses

| Status | Scenario |
|--------|----------|
| 401 | Invalid or missing token |
| 403 | Missing `patient.write` permission |
| 404 | Patient or guardian not found; or different clinic |
| 422 | Invalid `relation_type` (must be: parent/spouse/child/other) |

---

## 8. List Patient Guardians

### Request

```http
GET /api/v1/patients/550e8400-e29b-41d4-a716-446655440001/guardians HTTP/1.1
Authorization: Bearer {token}
```

### Response (200 OK)

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440003",
    "clinic_id": "550e8400-e29b-41d4-a716-446655440002",
    "patient_id": "550e8400-e29b-41d4-a716-446655440001",
    "guardian_patient_id": "550e8400-e29b-41d4-a716-446655440004",
    "relation_type": "parent",
    "is_primary_contact": true,
    "created_at": "2026-04-27T11:00:00Z"
  }
]
```

### Error Responses

| Status | Scenario |
|--------|----------|
| 401 | Invalid or missing token |
| 403 | Missing `patient.read` permission |
| 404 | Patient not found |

---

## 9. Delete Guardian Relation

### Request

```http
DELETE /api/v1/patients/guardians/550e8400-e29b-41d4-a716-446655440003 HTTP/1.1
Authorization: Bearer {token}
```

### Response

**204 No Content** or **200 OK**

### Error Responses

| Status | Scenario |
|--------|----------|
| 401 | Invalid or missing token |
| 403 | Missing `patient.write` permission |
| 404 | Relation not found |

---

## 10. Merge Patients

### Request

```http
POST /api/v1/patients/merge HTTP/1.1
Authorization: Bearer {token}
Content-Type: application/json

{
  "keep_id": "550e8400-e29b-41d4-a716-446655440001",
  "drop_id": "550e8400-e29b-41d4-a716-446655440006",
  "reason": "Duplicate records for same person"
}
```

### Request Body Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `keep_id` | UUID | Yes | Patient to retain (receives all related data) |
| `drop_id` | UUID | Yes | Patient to merge away (will be soft-deleted) |
| `reason` | string | No | Reason for merge (max 1000 chars) |

### Validation Rules

- `keep_id` and `drop_id` must be different (BUG-003 fix) — self-merge rejected with 422
- Both patients must belong to same clinic (cross-clinic merge rejected with 404)

### Response (201 Created)

```json
{
  "merge_log_id": "550e8400-e29b-41d4-a716-446655440005",
  "keep_id": "550e8400-e29b-41d4-a716-446655440001",
  "drop_id": "550e8400-e29b-41d4-a716-446655440006",
  "undo_deadline": "2026-05-04T12:00:00Z",
  "message": "Merge successful. The drop_id patient has been soft-deleted. You can undo this merge within 7 days."
}
```

### Error Responses

| Status | Scenario |
|--------|----------|
| 401 | Invalid or missing token |
| 403 | Missing `patient.merge` permission |
| 404 | One or both patients not found; or different clinic |
| 422 | `keep_id == drop_id` (self-merge, BUG-003 fix) |

---

## 11. Undo Merge

### Request

```http
POST /api/v1/patients/merge/550e8400-e29b-41d4-a716-446655440005/undo HTTP/1.1
Authorization: Bearer {token}
```

### Parameters

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `merge_id` | UUID | Yes (path) | ID of merge_log to undo |

### Response (200 OK)

```json
{
  "merge_log_id": "550e8400-e29b-41d4-a716-446655440005",
  "keep_id": "550e8400-e29b-41d4-a716-446655440001",
  "drop_id": "550e8400-e29b-41d4-a716-446655440006",
  "undo_deadline": "2026-05-04T12:00:00Z",
  "message": "Merge undone successfully. Both patient records are now active."
}
```

### Error Responses

| Status | Scenario |
|--------|----------|
| 401 | Invalid or missing token |
| 403 | Missing `patient.merge` permission |
| 404 | Merge log not found; or belongs to different clinic (BUG-004 fix) |
| 409 | Merge has already been undone |
| 410 | Undo deadline has passed (7 days elapsed) |

---

## Permission Matrix

| Endpoint | Method | Required Permission |
|----------|--------|---------------------|
| `/patients` | GET | `patient.read` |
| `/patients` | POST | `patient.write` |
| `/patients/search` | GET | `patient.read` |
| `/patients/{id}` | GET | `patient.read` |
| `/patients/{id}` | PATCH | `patient.write` |
| `/patients/{id}` | DELETE | `patient.delete` |
| `/patients/{id}/guardians` | POST | `patient.write` |
| `/patients/{id}/guardians` | GET | `patient.read` |
| `/patients/guardians/{rel_id}` | DELETE | `patient.write` |
| `/patients/merge` | POST | `patient.merge` |
| `/patients/merge/{merge_id}/undo` | POST | `patient.merge` |

---

## Common Headers

All requests must include:

```
Authorization: Bearer {jwt_token}
Content-Type: application/json (for POST/PATCH requests)
```

---

## Example cURL Commands

### Create Patient

```bash
curl -X POST http://localhost:8000/api/v1/patients \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "Nguyễn Văn An",
    "gender": "male",
    "date_of_birth": "1990-05-15",
    "phone": "0912345678"
  }'
```

### Search by Phone

```bash
curl -X GET "http://localhost:8000/api/v1/patients/search?q=0912&type=phone" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Merge Patients

```bash
curl -X POST http://localhost:8000/api/v1/patients/merge \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "keep_id": "550e8400-e29b-41d4-a716-446655440001",
    "drop_id": "550e8400-e29b-41d4-a716-446655440006",
    "reason": "Duplicate records"
  }'
```

### Undo Merge

```bash
curl -X POST http://localhost:8000/api/v1/patients/merge/550e8400-e29b-41d4-a716-446655440005/undo \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---
