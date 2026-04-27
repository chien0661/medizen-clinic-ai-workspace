# Thiết Kế Chi Tiết Tính Năng: Tauri Foundation — Shell + Offline Sync Engine + Hardware Integration

**Dự án:** Clinic CMS
**Task:** TASK-016
**Phiên bản:** 1.0
**Ngày:** 2026-04-27
**Người thực hiện:** Implementation & Review Agent (Iteration 2 FIX)
**Trạng thái:** Đã duyệt
**Tài liệu liên quan:** [Clinic Management System Design](../../../../docs/clinic_management_system_design.md#20-offline-sync), [Clinic Management Business Analysis](../../../../docs/clinic_management_business_analysis.md#16-offline-strategy-tauri-client)

---

## Lịch sử thay đổi

| Phiên bản | Ngày | Nội dung thay đổi |
|-----------|------|-------------------|
| 1.0 | 2026-04-27 | Phiên bản đầu tiên — Tauri 2.x foundation hoàn tất, tất cả AC pass (except deferred CI/hardware tests) |

---

## Mục lục

- [1. Tổng quan tính năng](#1-tổng-quan-tính-năng)
- [2. Luồng xử lý tổng thể](#2-luồng-xử-lý-tổng-thể)
- [3. Nguồn dữ liệu đầu vào](#3-nguồn-dữ-liệu-đầu-vào)
- [4. Danh sách API](#4-danh-sách-api)
- [5. Chi tiết từng API](#5-chi-tiết-từng-api)
- [6. Cấu trúc cơ sở dữ liệu](#6-cấu-trúc-cơ-sở-dữ-liệu)
- [7. SQL tổng hợp và truy vấn dữ liệu](#7-sql-tổng-hợp-và-truy-vấn-dữ-liệu)
- [8. Quy tắc nghiệp vụ](#8-quy-tắc-nghiệp-vụ)
- [9. Xử lý lỗi](#9-xử-lý-lỗi)
- [10. Chiến lược cache](#10-chiến-lược-cache)
- [11. Ghi chú và lưu ý khi kiểm thử](#11-ghi-chú-và-lưu-ý-khi-kiểm-thử)

---

## 1. Tổng quan tính năng

### 1.1 Mục đích

Cung cấp nền tảng (foundation) cho ứng dụng desktop Clinic CMS chạy trên Windows/macOS/Linux — máy khách Tauri 2.x (Rust + React) hỗ trợ chế độ offline-first với đồng bộ hóa (sync) tự động với server. Tính năng cho phép các nhân viên y tế (tiếp tân, bác sĩ, dược sĩ) tiếp tục làm việc khi mất kết nối mạng, các thay đổi sẽ được đẩy lên server khi quay lại online.

### 1.2 Phạm vi

**Bao gồm:**
- Vỏ ứng dụng Tauri 2.x (Rust backend + React 18 frontend) trong repo `clinic-cms-web/` độc lập
- Bộ nhớ cache SQLite cục bộ (offline mirror) cho 7 thực thể (Patient, Visit, Vitals, Appointment, VisitService, Prescription, TimeLog)
- Sync engine TypeScript — push (POST/PATCH/DELETE batch 50 entity lên server), pull (GET /api/v1/sync/changes từ server), xử lý conflict version 409
- UUIDv7 client-side để tránh collision khi nhiều client offline tạo entity cùng lúc
- Plugin Tauri: in ESC/POS (POS printer), quét mã vạch (barcode scanner HID), secure storage (JWT)
- Thành phần UI: OnlineStatusIndicator (icon trạng thái + đếm pending sync), ConflictResolutionModal (giải quyết conflict thủ công cho prescription)
- Sample minimal screen (health check + login dummy + trang chủ "Hello clinic-cms") để validate foundation hoạt động end-to-end
- Endpoint BE stub: GET /api/v1/sync/changes (trả về danh sách thay đổi từ timestamp, will be fully implemented in TASK-015)

**Không bao gồm:**
- Giao diện UI chi tiết cho các màn hình nghiệp vụ (Reception, Doctor, Pharmacy, Billing, HR, Admin, Dashboard) — sẽ implement trong TASK-017..024
- Sync cho Inventory deduction (reserve/dispense) — feature này LUÔN yêu cầu online (block UI nếu offline bằng `useOnlineStatus()` hook)
- Win32 OpenPrinter API migration (dùng shell/cmd trên Windows v1) — deferred to post-v1 improvement
- Non-ASCII printer name validation (v1 reject dấu tiếng Việt) — deferred to post-v1 when Win32 API migration done

### 1.3 Các bên liên quan

| Vai trò | Mô tả |
|---------|-------|
| **Người dùng cuối (End User)** | Nhân viên y tế (tiếp tân, bác sĩ, dược sĩ) — sử dụng ứng dụng desktop để quản lý bệnh nhân, lịch hẹn, toa thuốc, hóa đơn. Foundation không cung cấp UI, nhưng cung cấp primitive (hook, store, component, command) để TASK-017..024 xây dựng UI trên. |
| **BE Clinic CMS (clinic-cms repo)** | Cung cấp API endpoint `/api/v1/sync/changes` để client pull danh sách thay đổi. Cung cấp các per-entity REST endpoints (POST /api/v1/patients, PATCH /api/v1/visits/:id, DELETE /api/v1/prescriptions/:id) để client push thay đổi. |
| **FE Foundation (clinic-cms-web repo)** | Chính là task này — Tauri shell, sync engine, database layer, hooks, stores, components tái sử dụng được. |
| **TASK-017..024 teams** | Xây dựng UI các màn hình (Auth, Reception, Doctor, Pharmacy, Billing, HR, Admin, Dashboard) dựa trên foundation primitives (useOnlineStatus, useSync, barcode hook, print_receipt command). |

---

## 2. Luồng xử lý tổng thể

### 2.1 Sơ đồ luồng dữ liệu — Offline-First Sync

```
┌─────────────────────────────────────────────────────────────────────┐
│  Clinic CMS Desktop App (Tauri 2.x — Windows/macOS/Linux)          │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  React UI (TASK-017..024)                                    │  │
│  │  ├─ Auth / Patient / Visit / Prescription / ... screens      │  │
│  │  └─ Uses: useSync(), useOnlineStatus(), useBarcode(), etc.  │  │
│  └────────────────────────┬─────────────────────────────────────┘  │
│                           │                                          │
│                    ▼ sync engine.ts                                 │
│                           │                                          │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Sync Engine (TypeScript)                                    │  │
│  │  ├─ PUSH: batch 50 pending records → POST/PATCH/DELETE       │  │
│  │  ├─ PULL: fetch changes since lastSync via GET /sync/changes │  │
│  │  └─ CONFLICT: 409 response → last-write-wins (non-critical)  │  │
│  │             or manual modal (critical: Prescription)         │  │
│  └────────────┬──────────────────────────┬──────────────────────┘  │
│               │                          │                         │
│         ▼ db.ts          ▼ fetch API                               │
│               │                          │                         │
│  ┌────────────────────────┐  ┌────────────────────────┐            │
│  │  SQLite Local Cache    │  │  Network (fetch/Tauri) │            │
│  │  (7 entity tables +    │  │                        │            │
│  │   sync_status,         │  │  OFFLINE: queued       │            │
│  │   sync_attempted_at,   │  │  ONLINE: real-time     │            │
│  │   sync_error,          │  │                        │            │
│  │   server_version cols) │  │ Returns: {changes,     │            │
│  └────────────────────────┘  │           server_time} │            │
│                               └────────────────────────┘            │
│                                         │                           │
│                                    ▼ HTTP                          │
│                                         │                           │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  Clinic CMS Backend (FastAPI — clinic-cms repo)             │  │
│  │  ├─ GET /api/v1/sync/changes?since={iso}                   │  │
│  │  ├─ POST /api/v1/patients (create)                          │  │
│  │  ├─ PATCH /api/v1/visits/:id (update)                       │  │
│  │  └─ DELETE /api/v1/prescriptions/:id (soft-delete)          │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                               │                                     │
│                           ▼ DB                                      │
│                               │                                     │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  PostgreSQL Server DB (production truth)                     │  │
│  │  └─ Stores all entities + audit trail + version/timestamps  │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  Hardware Integration:                                              │
│  ├─ POS Printer (ESC/POS via Tauri cmd) — print_receipt            │
│  ├─ Barcode Scanner (HID input via useBarcode hook)                │
│  └─ Secure Storage (JWT token persistence)                         │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 Mô tả các bước chính — Chu kỳ Sync đầy đủ

| Bước | Tên bước | Mô tả chi tiết |
|------|---------|----------------|
| 1 | **Khởi động App** | App khởi động, load JWT token từ Tauri secure storage (nếu có). DB local được khởi tạo với schema 7 entity + sync_state table. Hook `useSync()` attach listener "online"/"offline" event. |
| 2 | **Tạo/Cập nhật Entity Offline** | User input form, entity (Patient, Visit, v.v.) được insert/update vào SQLite local. Nếu đang offline: `sync_status = 'pending_create'` hoặc `'pending_update'`, entity không gửi lên server ngay. Nếu đang online: entity có thể gửi lên ngay hoặc queue để batch. |
| 3 | **Online Status Detection** | Hook `useOnlineStatus()` phát hiện thay đổi online/offline từ `navigator.onLine`. UI component `OnlineStatusIndicator` hiển thị icon + pending count. Khi chuyển từ offline → online, trigger sync tự động. |
| 4 | **PUSH Phase — Đẩy Thay Đổi Lên Server** | Sync engine gom `pending_create`, `pending_update`, `pending_delete` records thành batch 50 entity. Cho mỗi batch: **Loop per-entity-type** (Patients batch 50, then Visits batch 50, ...): POST payload → `/api/v1/patients` (hoặc endpoint tương ứng). **Nếu thành công (200):** mark record `sync_status = 'synced'`, lưu `server_version` + clear `sync_error`. **Nếu HTTP 409 (Conflict):** fetch server record, so sánh `server.updated_at` vs `local.updated_at`. Nếu entity non-critical (Vitals, TimeLog): last-write-wins (local > server → force-push, server > local → apply server). Nếu entity critical (Prescription): hiển thị ConflictResolutionModal với 3 button (keep_local, take_server, merge). |
| 5 | **PULL Phase — Kéo Thay Đổi Từ Server** | Gọi `GET /api/v1/sync/changes?since={lastPullAt ISO8601}`. Server trả về `{changes: [{entity, id, op, data, server_version, server_updated_at}, ...], server_time: ISO8601}`. Client iterate changes: **op='create':** INSERT vào local table. **op='update':** UPDATE where id. **op='delete':** SET `is_deleted = 1` (soft-delete). **Nếu record đã tồn tại locally với status='pending_create'/'pending_update':** conflict — apply same last-write-wins / modal logic. Sau pull thành công: update `lastPullAt = server_time`. |
| 6 | **Xử lý Lỗi Sync** | Nếu push/pull fail (network timeout, 500 error, v.v.): log error vào `sync_error` column. Pending count vẫn hiển thị. Khi online lại → retry tự động. Max retry ~ 3 lần (exponential backoff 1s, 5s, 30s) trước khi surface error to user. |
| 7 | **Conflict Resolution Modal** | Nếu user gặp 409 trên Prescription: Modal hiện 3 option: **(keep_local)** — ghi đè server, push lại. **(take_server)** — discard local, apply server. **(merge)** — user edit local record thủ công rồi push. |
| 8 | **Hardware: Print & Barcode** | `print_receipt(content, printer_name)` command → build ESC/POS payload (INIT + text + FEED_CUT) → send to printer Windows via named pipe. Non-Windows: dump to file. Barcode scanner: HID input → `useBarcode()` accumulate keystrokes, detect scanner pattern (burst of fast keys + Enter), emit `barcode-scanned` event → app consume. |
| 9 | **Background Sync** | Hook `useSync()` chạy periodic sync mỗi 30s nếu online + pending. Cũng trigger ngay khi online reconnect sau offline period. |

---

## 3. Nguồn dữ liệu đầu vào

Phần này KHÔNG áp dụng — foundation này không nhận dữ liệu từ message queue hay file import. Dữ liệu đến từ:
- User nhập trực tiếp qua React UI (TASK-017..024 sẽ tạo)
- Server pull về qua `GET /api/v1/sync/changes` endpoint

---

## 4. Danh sách API

**Tất cả API đều yêu cầu xác thực JWT qua header:**
```
Authorization: Bearer {JWT_TOKEN}
```

**Đường dẫn gốc (Base Path):** `/api/v1`

| STT | Phương thức | Đường dẫn | Mô tả tóm tắt |
|-----|------------|-----------|--------------|
| 1 | GET | `/api/v1/sync/changes` | Lấy danh sách thay đổi (create/update/delete) từ server kể từ timestamp đã cho. Hỗ trợ filter theo entity type. |
| 2 | POST | `/api/v1/patients` | Tạo bệnh nhân mới. |
| 3 | PATCH | `/api/v1/patients/{id}` | Cập nhật thông tin bệnh nhân. |
| 4 | DELETE | `/api/v1/patients/{id}` | Xóa mềm (soft-delete) bệnh nhân. |
| 5 | POST | `/api/v1/visits` | Tạo lần khám mới. |
| 6 | PATCH | `/api/v1/visits/{id}` | Cập nhật lần khám. |
| 7 | DELETE | `/api/v1/visits/{id}` | Xóa mềm lần khám. |
| 8 | POST | `/api/v1/vitals` | Tạo chỉ số sức khỏe (nhiệt độ, huyết áp, v.v.). |
| 9 | PATCH | `/api/v1/vitals/{id}` | Cập nhật chỉ số. |
| 10 | DELETE | `/api/v1/vitals/{id}` | Xóa mềm chỉ số. |
| 11 | POST | `/api/v1/appointments` | Tạo lịch hẹn. |
| 12 | PATCH | `/api/v1/appointments/{id}` | Cập nhật lịch hẹn. |
| 13 | DELETE | `/api/v1/appointments/{id}` | Xóa mềm lịch hẹn. |
| 14 | POST | `/api/v1/visit-services` | Tạo dịch vụ khám. |
| 15 | PATCH | `/api/v1/visit-services/{id}` | Cập nhật dịch vụ khám. |
| 16 | DELETE | `/api/v1/visit-services/{id}` | Xóa mềm dịch vụ khám. |
| 17 | POST | `/api/v1/prescriptions` | Tạo toa thuốc. |
| 18 | PATCH | `/api/v1/prescriptions/{id}` | Cập nhật toa thuốc. |
| 19 | DELETE | `/api/v1/prescriptions/{id}` | Xóa mềm toa thuốc. |
| 20 | POST | `/api/v1/time-logs` | Tạo log giờ làm (check-in/out). |
| 21 | PATCH | `/api/v1/time-logs/{id}` | Cập nhật log giờ. |
| 22 | DELETE | `/api/v1/time-logs/{id}` | Xóa mềm log giờ. |

---

## 5. Chi tiết từng API

### 5.1 GET /api/v1/sync/changes — Lấy Danh Sách Thay Đổi (PULL)

#### Thông tin chung

| Thuộc tính | Giá trị |
|------------|--------|
| **Đường dẫn** | `GET /api/v1/sync/changes` |
| **Mô tả** | Trả về danh sách tất cả thay đổi (create/update/soft-delete) từ server kể từ một timestamp cụ thể. Client dùng endpoint này để sync data từ server xuống local cache. Hỗ trợ filter theo entity type (optional). |
| **Xác thực** | Bắt buộc — JWT Bearer token |

#### Tham số đầu vào

| Tham số | Kiểu | Bắt buộc | Mô tả | Giá trị mặc định |
|---------|------|---------|-------|-----------------|
| `since` | String (ISO8601) | Có | Timestamp (UTC) từ lúc lần sync cuối cùng. Ví dụ: `2026-04-27T10:30:00Z`. Server trả về những thay đổi xảy ra SAU timestamp này. | — |
| `entity` | String (enum) | Không | Lọc kết quả theo loại entity. Giá trị hợp lệ: `patient`, `visit`, `vitals`, `appointment`, `visit_service`, `prescription`, `time_log`. Nếu không truyền → trả về tất cả entity type. | — |

#### Quy trình xử lý

| Bước | Mô tả |
|------|-------|
| 1 | Client tính toán `since` = `lastPullAt` (lần sync trước) hoặc epoch nếu lần đầu. Gọi endpoint với `?since={ISO8601}&entity=prescription` (nếu chỉ muốn prescription). |
| 2 | Server kiểm tra token JWT — từ chối nếu invalid hay hết hạn. |
| 3 | Server kiểm tra `since` param — nếu không hợp lệ (không phải ISO8601) trả 422. Nếu thiếu trả 400. |
| 4 | Server truy vấn DB: SELECT changes từ các bảng entity WHERE updated_at > :since (AND entity_type = :entity nếu filtered). Tự động soft-delete cũng được trả về (is_deleted=1). |
| 5 | Server format response: `{changes: [{entity: 'patient', id: '...', op: 'create', data: {...}, server_version: 3, server_updated_at: '...'}, ...], server_time: '2026-04-27T10:35:00Z'}`. |
| 6 | Client nhận response, iterate qua mỗi change: nếu op='create' → INSERT local, nếu op='update' → UPDATE, nếu op='delete' → SET is_deleted=1. Sau xong: update `lastPullAt = server_time`. |

#### Kết quả trả về

**Thành công (200 OK):**

```json
{
  "changes": [
    {
      "entity": "patient",
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "op": "create",
      "data": {
        "name": "Nguyễn Văn A",
        "phone": "0912345678",
        "date_of_birth": "1990-01-15",
        "gender": "male",
        "address": "123 Đường Lê Lợi, TP.HCM",
        "id_card": "123456789",
        "is_deleted": 0,
        "created_at": "2026-04-27T10:20:00Z",
        "updated_at": "2026-04-27T10:20:00Z"
      },
      "server_version": 1,
      "server_updated_at": "2026-04-27T10:20:00Z"
    },
    {
      "entity": "prescription",
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "op": "update",
      "data": {
        "status": "dispensed",
        "dispensed_at": "2026-04-27T10:25:00Z"
      },
      "server_version": 2,
      "server_updated_at": "2026-04-27T10:25:00Z"
    },
    {
      "entity": "vitals",
      "id": "770e8400-e29b-41d4-a716-446655440002",
      "op": "delete",
      "data": null,
      "server_version": 1,
      "server_updated_at": "2026-04-27T10:28:00Z"
    }
  ],
  "server_time": "2026-04-27T10:35:00Z"
}
```

**Mô tả các trường kết quả:**

| Trường | Kiểu | Mô tả ý nghĩa nghiệp vụ |
|--------|------|------------------------|
| `changes[]` | Mảng | Danh sách các thay đổi từ server. Rỗng nếu không có thay đổi mới. |
| `changes[].entity` | String | Loại entity: `patient`, `visit`, `vitals`, `appointment`, `visit_service`, `prescription`, `time_log`. |
| `changes[].id` | UUID | ID của entity. |
| `changes[].op` | String | Phép tính: `create` (tạo mới), `update` (cập nhật), `delete` (xóa mềm). |
| `changes[].data` | Object / null | Dữ liệu entity (op=create/update) hoặc null (op=delete). Chỉ bao gồm các cột đã thay đổi (hoặc toàn bộ nếu create). |
| `changes[].server_version` | Integer | Số hiệu phiên bản entity trên server — dùng để detect conflict (optimistic lock). |
| `changes[].server_updated_at` | ISO8601 | Thời điểm entity được cập nhật lần cuối trên server. |
| `server_time` | ISO8601 | Thời điểm phút server xử lý yêu cầu này — client dùng làm `lastPullAt` cho lần sync tiếp theo. |

**Lỗi:**

| HTTP Code | Tình huống | Phản hồi |
|----------|-----------|---------|
| 400 | Tham số `since` thiếu | `{code: "INVALID_REQUEST", message: "Missing required parameter: since"}` |
| 401 | Token JWT không hợp lệ/hết hạn | `{code: "UNAUTHORIZED", message: "Invalid or expired token"}` |
| 422 | `since` không phải ISO8601 hoặc `entity` không trong enum | `{code: "VALIDATION_ERROR", message: "Parameter 'since' must be ISO8601 format"}` |
| 500 | Lỗi hệ thống (database, v.v.) | `{code: "INTERNAL_ERROR", message: "Server error, please retry"}` |

---

### 5.2 POST /api/v1/{entity} — Tạo Entity Mới (PUSH)

#### Thông tin chung (ví dụ: POST /api/v1/patients)

| Thuộc tính | Giá trị |
|------------|--------|
| **Đường dẫn** | `POST /api/v1/{entity}` (thay {entity} = `patients`, `visits`, `vitals`, v.v.) |
| **Mô tả** | Tạo entity mới trên server. Client gửi dữ liệu entity (đã tạo offline với UUIDv7 client-side). Server kiểm tra conflict version (optimistic lock), nếu OK → INSERT, trả lại server_version mới. |
| **Xác thực** | Bắt buộc — JWT Bearer token |

#### Tham số đầu vào

Request body (JSON):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Nguyễn Văn A",
  "phone": "0912345678",
  "date_of_birth": "1990-01-15",
  "gender": "male",
  "address": "123 Đường Lê Lợi, TP.HCM",
  "id_card": "123456789",
  "created_at": "2026-04-27T10:20:00Z",
  "updated_at": "2026-04-27T10:20:00Z"
}
```

**Ghi chú:** Client tự sinh `id` bằng UUIDv7, không để server auto-increment. Timestamp `created_at`, `updated_at` cũng do client sinh lúc tạo offline. Sync metadata columns (`sync_status`, `sync_attempted_at`, `sync_error`, `server_version`) KHÔNG gửi lên server — chỉ có dữ liệu entity.

#### Quy trình xử lý

| Bước | Mô tả |
|------|-------|
| 1 | Client tạo entity offline (UUIDv7 id, timestamp client), mark `sync_status='pending_create'`. Sau đó gủi POST với dữ liệu entity. |
| 2 | Server kiểm tra JWT. |
| 3 | Server kiểm tra schema: required fields có đủ không. Nếu thiếu → 400 INVALID_REQUEST. |
| 4 | Server check `id` không tồn tại (unique constraint). Nếu tồn tại → 409 conflict hoặc 400 nếu là insert duplicate. |
| 5 | Server INSERT entity vào DB. Set server `version = 1`, `server_updated_at = NOW()`. |
| 6 | Trả response 200 với entity + metadata mới: `{entity, server_version: 1, server_updated_at, server_created_at}`. |

#### Kết quả trả về (200 OK)

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Nguyễn Văn A",
  "phone": "0912345678",
  "date_of_birth": "1990-01-15",
  "gender": "male",
  "address": "123 Đường Lê Lợi, TP.HCM",
  "id_card": "123456789",
  "created_at": "2026-04-27T10:20:00Z",
  "updated_at": "2026-04-27T10:20:00Z",
  "server_version": 1,
  "server_created_at": "2026-04-27T10:25:00Z",
  "server_updated_at": "2026-04-27T10:25:00Z"
}
```

**Lỗi 409 (Conflict):**

```json
{
  "code": "CONFLICT",
  "message": "Entity already exists or version mismatch",
  "server_version": 2,
  "server_record": { ... existing record ... }
}
```

Client nhận 409 → so sánh `local.updated_at` vs `server.updated_at`. Nếu non-critical entity: force-push (PATCH với version override). Nếu critical (Prescription): show modal.

---

### 5.3 PATCH /api/v1/{entity}/{id} — Cập Nhật Entity

Tương tự POST, nhưng yêu cầu request body chỉ bao gồm các field đã thay đổi (partial update).

**Ghi chú về Conflict:** Dùng optimistic lock qua `server_version` — nếu client gửi `version=2` nhưng server có `version=3` → 409 Conflict. Client không phải gửi version (server tự kiểm tra bằng updated_at timestamp comparison).

---

### 5.4 DELETE /api/v1/{entity}/{id} — Xóa Mềm (Soft-Delete)

Đặt `is_deleted = 1` trên server (không xóa vật lý). Trả response 200 với entity + `is_deleted=1`.

---

## 6. Cấu trúc cơ sở dữ liệu

### 6.1 Tổng quan các bảng

| Bảng | Mục đích |
|------|---------|
| `patient` | Thông tin bệnh nhân cơ bản (họ tên, CMND, số điện thoại, địa chỉ, giới tính, ngày sinh) |
| `visit` | Lần khám (liên kết patient, doctor, clinic) |
| `vitals` | Chỉ số sức khỏe (nhiệt độ, huyết áp, nhịp tim, v.v.) — liên kết visit |
| `appointment` | Lịch hẹn khám (patient, doctor, clinic, time, status) |
| `visit_service` | Các dịch vụ/cách chữa trị applied trong 1 lần khám (khám, siêu âm, v.v.) |
| `prescription` | Toa thuốc (liên kết visit, items, status) — CRITICAL entity (manual conflict resolution) |
| `time_log` | Log giờ làm (check-in/out của nhân viên) |
| `sync_state` | Metadata sync: `last_pull_at`, `last_push_at` (toàn global, 1 row) |

### 6.2 Chi tiết bảng

#### Bảng: `patient`

**Mô tả:** Lưu thông tin bệnh nhân cơ bản. Mỗi bệnh nhân có ID là UUIDv7 (client-side generate). Hỗ trợ offline — có các cột `sync_status`, `sync_error`, `server_version` để tracking sync state.

| Tên cột | Kiểu dữ liệu | Bắt buộc | Mô tả |
|---------|-------------|---------|-------|
| `id` | TEXT (UUID) | Có | Khóa chính, UUIDv7 client-side generated |
| `name` | TEXT | Có | Họ tên bệnh nhân |
| `phone` | TEXT | Không | Số điện thoại liên hệ |
| `date_of_birth` | TEXT (ISO8601 date) | Không | Ngày sinh YYYY-MM-DD |
| `gender` | TEXT | Không | Giới tính: `male`, `female`, `other` |
| `address` | TEXT | Không | Địa chỉ đầy đủ |
| `id_card` | TEXT | Không | Số CMND/passport |
| `is_deleted` | INTEGER (0/1) | Có | Soft-delete flag. 0 = active, 1 = deleted |
| `created_at` | TEXT (ISO8601) | Có | Thời điểm tạo (client time) |
| `updated_at` | TEXT (ISO8601) | Có | Thời điểm cập nhật cuối (client time) |
| `sync_status` | TEXT | Có | Trạng thái sync: `synced`, `pending_create`, `pending_update`, `pending_delete`. Default: `pending_create` |
| `sync_attempted_at` | TEXT (ISO8601) | Không | Thời điểm lần sync thử cuối cùng |
| `sync_error` | TEXT | Không | Thông báo lỗi nếu sync fail |
| `server_version` | INTEGER | Không | Version từ server (optimistic lock) |

**Tính duy nhất:** `id` là unique key. `id_card` nên unique nhưng có thể null (tuỳ business rule).

**Script tạo bảng:**

```sql
CREATE TABLE patient (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    phone TEXT,
    date_of_birth TEXT,
    gender TEXT,
    address TEXT,
    id_card TEXT UNIQUE,
    is_deleted INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    sync_status TEXT NOT NULL DEFAULT 'pending_create',
    sync_attempted_at TEXT,
    sync_error TEXT,
    server_version INTEGER
);
```

---

#### Bảng: `visit`

**Mô tả:** Một lần khám của bệnh nhân. Liên kết patient_id, doctor_id, clinic_id, thời gian khám, trạng thái.

| Tên cột | Kiểu dữ liệu | Bắt buộc | Mô tả |
|---------|-------------|---------|-------|
| `id` | TEXT (UUID) | Có | Khóa chính |
| `patient_id` | TEXT | Có | FK → patient.id |
| `doctor_id` | TEXT | Không | FK → user (doctor) |
| `clinic_id` | TEXT | Không | FK → clinic |
| `visit_date` | TEXT (ISO8601) | Có | Ngày/giờ khám |
| `status` | TEXT | Có | `scheduled`, `in_progress`, `completed`, `cancelled` |
| `notes` | TEXT | Không | Ghi chú thêm |
| `is_deleted` | INTEGER | Có | Soft-delete |
| `created_at` | TEXT | Có | Thời điểm tạo |
| `updated_at` | TEXT | Có | Thời điểm cập nhật |
| `sync_status` | TEXT | Có | Trạng thái sync |
| `sync_attempted_at` | TEXT | Không | Lần sync cuối |
| `sync_error` | TEXT | Không | Lỗi nếu có |
| `server_version` | INTEGER | Không | Version từ server |

---

#### Bảng: `vitals`

**Mô tả:** Chỉ số sức khỏe (nhiệt độ, huyết áp, SpO2, v.v.) — non-critical entity (last-write-wins conflict resolution).

| Tên cột | Kiểu dữ liệu | Bắt buộc | Mô tả |
|---------|-------------|---------|-------|
| `id` | TEXT (UUID) | Có | Khóa chính |
| `visit_id` | TEXT | Có | FK → visit.id |
| `temperature` | REAL | Không | Độ C |
| `blood_pressure` | TEXT | Không | Định dạng: `140/90` |
| `heart_rate` | INTEGER | Không | Nhịp tim (bpm) |
| `spo2` | INTEGER | Không | Oxygen saturation (%) |
| `is_deleted` | INTEGER | Có | Soft-delete |
| `created_at` | TEXT | Có | Thời điểm tạo |
| `updated_at` | TEXT | Có | Thời điểm cập nhật |
| `sync_status` | TEXT | Có | Trạng thái sync |
| `sync_attempted_at` | TEXT | Không | Lần sync cuối |
| `sync_error` | TEXT | Không | Lỗi nếu có |
| `server_version` | INTEGER | Không | Version từ server |

---

#### Bảng: `appointment`

**Mô tả:** Lịch hẹn khám trước (patient, doctor, time, status).

Cấu trúc tương tự `visit` + `vitals`.

---

#### Bảng: `visit_service`

**Mô tả:** Các dịch vụ/cách chữa trị apply trong lần khám (khám tổng quát, siêu âm, chụp X-ray, v.v.). Non-critical.

Liên kết `visit_id` + service code/name + cost + status.

---

#### Bảng: `prescription`

**Mô tả:** Toa thuốc — CRITICAL entity (manual conflict modal khi 409). Liên kết `visit_id`, chứa danh sách thuốc (items), trạng thái (pending, dispensed, cancelled).

| Tên cột | Kiểu dữ liệu | Bắt buộc | Mô tả |
|---------|-------------|---------|-------|
| `id` | TEXT (UUID) | Có | Khóa chính |
| `visit_id` | TEXT | Có | FK → visit.id |
| `status` | TEXT | Có | `pending`, `dispensed`, `cancelled` — CRITICAL: nếu conflict 409, show modal |
| `items` | TEXT (JSON) | Không | Danh sách thuốc: `[{medicine_code, quantity, unit_dose, note}, ...]` |
| `notes` | TEXT | Không | Ghi chú toa thuốc |
| `is_deleted` | INTEGER | Có | Soft-delete |
| `created_at` | TEXT | Có | Thời điểm tạo |
| `updated_at` | TEXT | Có | Thời điểm cập nhật |
| `sync_status` | TEXT | Có | Trạng thái sync |
| `sync_attempted_at` | TEXT | Không | Lần sync cuối |
| `sync_error` | TEXT | Không | Lỗi nếu có |
| `server_version` | INTEGER | Không | Version từ server |

---

#### Bảng: `time_log`

**Mô tả:** Log giờ làm (check-in/out nhân viên). Non-critical.

| Tên cột | Kiểu dữ liệu | Bắt buộc | Mô tả |
|---------|-------------|---------|-------|
| `id` | TEXT (UUID) | Có | Khóa chính |
| `employee_id` | TEXT | Có | FK → user.id |
| `check_in_at` | TEXT (ISO8601) | Không | Thời điểm check-in |
| `check_out_at` | TEXT (ISO8601) | Không | Thời điểm check-out |
| `duration_minutes` | INTEGER | Không | Thời gian làm (phút) |
| `is_deleted` | INTEGER | Có | Soft-delete |
| `created_at` | TEXT | Có | Thời điểm tạo |
| `updated_at` | TEXT | Có | Thời điểm cập nhật |
| `sync_status` | TEXT | Có | Trạng thái sync |
| `sync_attempted_at` | TEXT | Không | Lần sync cuối |
| `sync_error` | TEXT | Không | Lỗi nếu có |
| `server_version` | INTEGER | Không | Version từ server |

---

#### Bảng: `sync_state`

**Mô tả:** Metadata global sync — chỉ 1 row, lưu timestamp lần sync cuối cùng.

| Tên cột | Kiểu dữ liệu | Bắt buộc | Mô tả |
|---------|-------------|---------|-------|
| `id` | INTEGER | Có | Always = 1 (single row) |
| `last_pull_at` | TEXT (ISO8601) | Không | Timestamp lần pull cuối cùng từ server |
| `last_push_at` | TEXT (ISO8601) | Không | Timestamp lần push cuối cùng lên server |
| `last_sync_error` | TEXT | Không | Lỗi sync cuối cùng (global) |
| `is_syncing` | INTEGER (0/1) | Có | Flag: đang sync hay không |

**Script tạo bảng:**

```sql
CREATE TABLE sync_state (
    id INTEGER PRIMARY KEY CHECK(id = 1),
    last_pull_at TEXT,
    last_push_at TEXT,
    last_sync_error TEXT,
    is_syncing INTEGER NOT NULL DEFAULT 0
);
INSERT INTO sync_state (id, last_pull_at, last_push_at, is_syncing) VALUES (1, NULL, NULL, 0);
```

---

## 7. SQL tổng hợp và truy vấn dữ liệu

Không áp dụng — task này là foundation infrastructure, không có logic tổng hợp dữ liệu hay aggregation. Tất cả query là CRUD cơ bản (SELECT, INSERT, UPDATE, DELETE). Full data aggregation sẽ implement ở TASK-024 (Dashboard + Reports).

---

## 8. Quy tắc nghiệp vụ

| Mã | Mô tả quy tắc | Hành vi khi vi phạm |
|----|--------------|---------------------|
| BR-1 | **UUIDv7 Client-Side ID Generation** — Khi tạo entity offline, client phải sinh ID là UUIDv7 (time-ordered UUID) thay vì UUID random. Tránh collision khi nhiều client offline tạo entity cùng lúc. | Nếu client gửi ID không phải UUIDv7: server reject với 400 INVALID_REQUEST. Hoặc server chấp nhận nhưng dùng client ID (no auto-increment). |
| BR-2 | **Conflict 409 — Non-Critical Entity (Last-Write-Wins)** — Với entity non-critical (Vitals, TimeLog, Appointment, VisitService), khi client push và server return 409 (version mismatch): client tự động so sánh `local.updated_at` vs `server.updated_at`. Nếu local > server: force-push (PATCH). Nếu server > local: discard local, apply server. Không hiển thị modal. | Lỗi sync được log, pending count vẫn hiển thị cho user. Retry sau ~30s. |
| BR-3 | **Conflict 409 — Critical Entity (Manual Resolution)** — Với entity critical (Prescription, Invoice), khi client push và server return 409: show ConflictResolutionModal với 3 button: **(keep_local)** — ghi đè server, force-push local. **(take_server)** — discard local, apply server record. **(merge)** — user edit local record thủ công. | Nếu user không chọn trong 5 phút: auto-discard local (take_server). Or retry on next sync. |
| BR-4 | **Inventory Deduction ALWAYS Requires Online** — Dùng `useOnlineStatus()` hook để detect online/offline. Nếu offline: block UI (disable button) hoặc show warning "Tính năng này cần kết nối internet". Không cho phép offline inventory deduction (reserve/dispense) để tránh oversell. | Nếu user cố push inventory offline: endpoint reject 403 FORBIDDEN ("Inventory operation requires online"). |
| BR-5 | **Printer Name Validation — ASCII Allowlist Only (v1 Limitation)** — Printer name chỉ chấp nhận ký tự ASCII: `[A-Za-z0-9 _\-:]`. Max 128 ký tự. Reject non-ASCII (dấu tiếng Việt, emoji, v.v.). | Nếu user nhập printer name có dấu: command `print_receipt` raise error "Printer name contains invalid characters". Deferred to v2: Win32 OpenPrinter API (no shell injection, support non-ASCII). |
| BR-6 | **Soft-Delete Only (No Hard Delete)** — DELETE endpoint không xóa vật lý. Chỉ set `is_deleted = 1`. Dữ liệu vẫn giữ trong DB cho audit trail. | Nếu client DELETE sau đó GET: kết quả chỉ include `is_deleted=0` records (filter tự động). |
| BR-7 | **Sync Batching — Max 50 Entity per PUSH** — Khi push changes, sync engine batch 50 entity một lần (per entity type). Nếu có 150 pending patients: chia thành 3 batch x50. Retry nếu batch fail. | Nếu một record trong batch fail 409: xử lý conflict per BR-2/3, sau đó retry whole batch hay skip record? Answer: per-record retry (Sync engine loop). |
| BR-8 | **OptimisticLock via server_version** — Server assign `server_version` (monotonic increment) cho mỗi entity. Client track local `server_version`. Khi PATCH: nếu server has `version > client.server_version` → conflict 409. | Nếu client push stale version: 409. Client apply server record (BR-2/3). |

---

## 9. Xử lý lỗi

### 9.1 Các mã lỗi phổ biến

| Mã HTTP | Mã lỗi | Tình huống xảy ra | Thông báo trả về |
|---------|--------|-------------------|-----------------|
| 400 | INVALID_REQUEST | Tham số không hợp lệ (missing `since`, invalid JSON body, v.v.) | "Yêu cầu không hợp lệ: [chi tiết]" |
| 401 | UNAUTHORIZED | Token JWT không hợp lệ, hết hạn, hoặc thiếu | "Yêu cầu xác thực để truy cập" |
| 409 | CONFLICT | Version mismatch (optimistic lock) khi PATCH/POST duplicate | `{code: "CONFLICT", message: "Version mismatch or entity exists", server_version: X, server_record: {...}}` |
| 422 | VALIDATION_ERROR | Giá trị tham số không hợp lệ (e.g., `entity` param không trong enum) | "Giá trị [param] không hợp lệ. Hợp lệ: [list]" |
| 500 | INTERNAL_ERROR | Lỗi hệ thống (database, network, v.v.) | "Lỗi hệ thống, vui lòng thử lại sau" |

### 9.2 Định dạng phản hồi lỗi

```json
{
  "code": "[MÃ_LỖI]",
  "message": "[MÔ_TẢ_CHI_TIẾT]"
}
```

### 9.3 Xử lý lỗi Sync Engine (FE)

Khi sync fail:
1. **Network timeout (0s timeout):** Set `sync_error` = "Network timeout", keep pending count, retry sau ~30s.
2. **HTTP 500:** Log error, set `sync_error`, retry với exponential backoff (1s → 5s → 30s).
3. **HTTP 409 (Conflict):** Handle per BR-2/3 (auto vs manual resolution).
4. **HTTP 401 (Unauthorized):** Clear JWT token, redirect to Login. User phải re-authenticate.
5. **HTTP 422 (Validation):** Log error, surface to user "Invalid data — check before retry".

**Max retry:** 3 lần per record trước khi mark as "sync_error_fatal".

---

## 10. Chiến lược cache

**Không áp dụng** — Foundation này không dùng HTTP cache. Local SQLite chính là "cache". All queries go directly to SQLite (no in-memory cache layer). Sync engine pulls từ server mỗi 30s (periodic) hoặc khi user reconnect (event-driven).

---

## 11. Ghi chú và lưu ý khi kiểm thử

### 11.1 Điểm quan trọng cần nắm

1. **Offline-first mindset** — App phải hoạt động OFFLINE trước. Tất cả create/update được buffer vào SQLite local với `sync_status = 'pending_*'`. Khi online → tự động push. Tester phải test:
   - Tắt WiFi/Network → tạo entity → kiểm tra SQLite có record không → bật WiFi → verify sync push thành công.

2. **UUIDv7 ordering** — Client-side ID là UUIDv7, có timestamp prefix. Khi merge local + server data, order sẽ dự đoán được (time-ordered). Tester kiểm tra ID format (36 ký tự hex dash-separated).

3. **Conflict resolution là manual** — Prescription conflict 409 KHÔNG auto-resolve. Phải open ConflictResolutionModal, chọn 1 trong 3 button. Tester phải trigger 409 (2 concurrent update trên prescription) và verify modal appear.

4. **Deferred items** — 4 CI items + 2 hardware:
   - D-CI-1: `cargo test` (11 Rust unit tests) — verify in CI with Rust toolchain
   - D-CI-2: `pnpm tauri dev` app window starts — verify in CI (Windows + Rust + WebView2)
   - D-CI-3: `tauri build` → .msi/.dmg/.AppImage — verify in CI (platform-specific runners)
   - D-CI-4: BE pytest (6 tests) — verify in CI with Python 3.11+ (host has 3.10)
   - D-HW-1: POS printer ESC/POS test — requires physical printer or emulator. Connect USB + invoke `print_receipt({ content: "HELLO CLINIC" })` → verify output.
   - D-HW-2: Barcode scanner HID input — requires physical HID scanner. Connect → scan barcode → verify `barcode-scanned` Tauri event fires.

5. **Console logging in v1** — `console.error` / `console.warn` call lại code (engine.ts, useSync.ts, useBarcode.ts). Acceptable for v1. Deferred: route through Tauri `log` plugin in v2.

6. **Non-ASCII printer names blocked** — Vietnamese printer names (tên có dấu, ký tự đặc biệt) bị reject. Ví dụ: "Máy in 01" → error. Only ASCII: "Printer_01" → OK. Deferred to v2: Win32 OpenPrinter API.

7. **Network-only operations** — Inventory deduction (dispense) yêu cầu online. Hook `useOnlineStatus()` đọc `navigator.onLine`. Tester block network → verify UI disable dispense button. Restore network → verify enable.

### 11.2 Gợi ý dữ liệu kiểm thử

| Kịch bản | Giá trị đầu vào | Kết quả kỳ vọng |
|---------|----------------|----------------|
| **Create patient offline** | Name="Nguyễn Văn A", Phone="0912345678" | INSERT local, sync_status='pending_create'. Online → push POST. 200 → sync_status='synced', server_version=1. |
| **Conflict vitals (non-critical)** | Push vitals with local.updated_at=10:20, server.updated_at=10:25 | 409 response. Engine compare: server > local → discard local, apply server. No modal. |
| **Conflict prescription (critical)** | Push prescription with 409 | ConflictResolutionModal appear. User click "keep_local" → force-push PATCH. 200 → synced. |
| **Batch 50 patients** | 150 pending patients | Batch 1: POST x50 → success. Batch 2: POST x50 → success. Batch 3: POST x50 → success. All synced. |
| **Timeout sync** | Network latency >30s | Sync timeout. sync_error="Network timeout". Pending count still visible. Retry after 30s. |
| **Invalid entity filter** | GET /sync/changes?since=...&entity=invalid | 422 VALIDATION_ERROR |
| **Missing JWT token** | GET /sync/changes without Authorization header | 401 UNAUTHORIZED |
| **Printer ESC/POS output** | print_receipt({content: "HELLO CLINIC"}) | Output on physical printer or temp file (Windows vs non-Windows). Verify bytes: ESC @ (INIT), "HELLO CLINIC", ESC m (FEED_CUT). |
| **Barcode scanner** | Scan code from HID scanner | useBarcode hook accumulate keystrokes, detect scanner pattern (burst + Enter), emit "barcode-scanned" event. React component consume → display barcode value. |

### 11.3 Hạn chế hiện tại (v1)

- **Non-ASCII printer names rejected** — Vietnamese characters (dấu) not supported. Workaround: use ASCII printer names only. Win32 API migration post-v1.
- **Console logging** — debug logs via console.error/warn. Should route through Tauri log plugin in v2.
- **No icon branding** — placeholder icons (solid blue color). Replace with real brand icons before production.
- **Rust unit tests deferred** — cargo test cannot run on host (no Rust toolchain). Must verify in CI.
- **Tauri build deferred** — tauri build (.msi/.dmg/.AppImage) requires Rust + platform SDK. Verify in CI.
- **BE sync endpoint stub** — Returns empty `changes: []` until TASK-015 implement full ORM queries.

### 11.4 Hướng phát triển

- **Bluetooth LE integration** — Blood pressure monitor, pulse oximeter (post-v1).
- **CCCD reader** — Vietnamese ID card reader (post-v1).
- **Win32 API printer** — Replace shell/cmd with Win32 OpenPrinter/WritePrinter API (v2, allow non-ASCII printer names).
- **Centralized logging** — Route console logs through Tauri log plugin (v2).
- **Selective sync** — User choose which entities to sync (reduce bandwidth for slow networks).
- **Compression** — Sync payload gzip compression (post-v1).

---

## Danh sách Thư Viện Foundation cho TASK-017+

Các modules/hooks/components đã built vào foundation, tái sử dụng được cho TASK-017..024:

**Sync & Network:**
- `useOnlineStatus()` hook — subscribe online/offline status
- `usePendingSyncCount()` hook — get count of pending changes
- `useSync()` hook — trigger periodic/manual sync
- Sync engine (`engine.ts`) — push/pull/conflict resolution
- Database layer (`database.ts`) — local SQLite queries

**UI Components:**
- `OnlineStatusIndicator` component — display online/offline icon + pending count badge
- `ConflictResolutionModal` component — generic 3-button conflict resolution dialog

**Hardware & Integrations:**
- `print_receipt(content, printer_name)` Tauri command — POS printer ESC/POS output
- `useBarcode()` hook — HID barcode scanner keystroke capture + event emit
- Secure storage (Tauri plugin) — JWT token persistence

**Stores & State:**
- `networkStore` (Zustand) — online status, pending count, isSyncing, syncError, lastSyncAt
- `authStore` (Zustand) — JWT token, user info, login/logout

**Utilities:**
- `generateClientId()` — UUIDv7 generator
- `isValidUuid()` — UUID validation
- `extractTimestampFromUuidv7()` — extract timestamp from UUIDv7

**Database schema:**
- 7 offline-writable entity tables (patient, visit, vitals, appointment, visit_service, prescription, time_log)
- Sync metadata columns (sync_status, sync_error, sync_attempted_at, server_version)
- sync_state table (last_pull_at, last_push_at)

---

**Phê duyệt**

| Vai trò | Họ tên | Ngày |
|---------|--------|------|
| Code Implementation Agent | — | 2026-04-27 |
| Code Review Agent (Iteration 2) | — | 2026-04-27 |
| Test Agent | — | 2026-04-27 |
| Documentation Agent | — | 2026-04-27 |
