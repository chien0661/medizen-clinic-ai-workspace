# MediZen — Security & Sensitive Data Spec

**Cập nhật**: 2026-04-30 (v1)
**Phạm vi**: Bảo mật dữ liệu nhạy cảm (PII / PHI / Credentials / Financial) trong toàn bộ pipeline — collect → store → process → transmit → archive → delete.
**Compliance target**: HIPAA Privacy + Security Rule · Nghị định 13/2023/NĐ-CP · Thông tư 46/2018/TT-BYT (lưu trữ bệnh án) · OWASP ASVS L2.

> Đọc kèm:
> - [TAB_MATRIX.md §Bảo mật & Mã hoá](TAB_MATRIX.md#section-bảo-mật--mã-hóa) — UI cấu hình runtime
> - [README.md §Feature flags](README.md#-feature-flags) — flag cấu hình theo PK
> - `clinic_management_function_list.md §26 NFR` — ngưỡng + status đo lường (NFR-005..NFR-046)

---

## 1. Phân loại dữ liệu (Data Classification)

Hệ thống dùng **4-tier classification**. Mỗi field/column được gán 1 tier. Tier càng cao → control càng nghiêm.

| Tier | Tên | Định nghĩa | Ví dụ field |
|:---:|---|---|---|
| **T0** | **Public** | An toàn để hiển thị công khai. Không có ràng buộc. | `clinic.name` (tên PK), `service.name` (tên DV trong bảng giá), feature flags |
| **T1** | **Internal** | Chỉ user đã đăng nhập trong cùng tenant. Lộ ra → hơi xấu hổ nhưng không nguy hiểm. | `user.full_name` (NV), `appointment.note`, `service.price` |
| **T2** | **Confidential / PII** | Định danh được cá nhân. Lộ ra → vi phạm Nghị định 13. **Yêu cầu encryption + audit + retention rule.** | `patient.full_name`, `patient.phone`, `patient.email`, `patient.address`, `patient.dob`, `user.email`, `user.phone` |
| **T3** | **Restricted / PHI + Credentials** | Y tế nhạy cảm hoặc credential. Lộ ra → vi phạm HIPAA + Nghị định 13 + tổn hại nghiêm trọng. **Yêu cầu encryption + per-row audit + access logging + masking khi display.** | `patient.cccd` (CCCD), `patient.bhyt_card_number`, `patient.medical_history`, `visit.diagnosis`, `prescription.medicines`, `user.password_hash`, `user.mfa_secret`, `audit_log.diff` (chứa PHI trong JSON), `payment.card_last4` |

### 1.1 PII / PHI inventory (full list)

Mọi field **T2/T3** phải nằm trong bảng dưới đây. Khi thêm column mới, audit checklist (PR template) bắt buộc xác định tier.

| Tier | Bảng | Cột | Encryption | Audit | Retention | Quyền xem |
|:---:|---|---|---|---|---|---|
| T3 | `users` | `password_hash` | bcrypt cost 12 | exclude khỏi audit log | dùng cho đến khi đổi MK | Không một ai (chỉ verify) |
| T3 | `users` | `mfa_secret` | AES-256 column-level | exclude | revoke MFA → xoá | Không ai (chỉ verify) |
| T3 | `users` | `refresh_token_hash` | SHA-256 hash | exclude | TTL 7 ngày | Không ai (chỉ verify) |
| T2 | `users` | `email` | TDE | redact (`a***@gmail.com`) | 5 năm sau khi nghỉ việc | Self + Clinic Admin |
| T2 | `users` | `phone` | TDE | redact (`***1234`) | 5 năm | Self + Clinic Admin |
| T2 | `users` | `full_name` | TDE | display | 5 năm | Same clinic users |
| T3 | `patients` | `cccd` | AES-256 column + masking display `***1234` | log access | 30 năm (BYT) | Lễ tân + BS + QT |
| T3 | `patients` | `bhyt_card_number` | AES-256 column + masking | log access | 30 năm | Same |
| T2 | `patients` | `phone` | TDE + masking display | redact | 30 năm | Lễ tân/BS/ĐD/QT |
| T2 | `patients` | `email` | TDE | redact | 30 năm | Same |
| T2 | `patients` | `address` | TDE | redact city only | 30 năm | Same |
| T2 | `patients` | `full_name` | TDE | display | 30 năm | Same |
| T2 | `patients` | `dob` | TDE | display age only | 30 năm | Same |
| T2 | `patients` | `guardian_*` | TDE | redact | 30 năm | Same |
| T3 | `patients` | `allergies` | TDE | display | 30 năm | BS + ĐD + DS + QT |
| T3 | `patients` | `chronic_conditions` | TDE | display | 30 năm | Same |
| T3 | `visits` | `diagnosis` (ICD-10 codes + free text) | TDE | display | 30 năm | BS + QT |
| T3 | `visits` | `soap_note` (Khám LS) | TDE | display | 30 năm | BS + QT |
| T3 | `visits` | `treatment_plan` | TDE | display | 30 năm | Same |
| T3 | `prescriptions` | `medicines[]` (JSON) | TDE | display | 30 năm | BS + DS + QT |
| T3 | `vitals` | `*` (HA, mạch, ...) | TDE | display | 30 năm | BS + ĐD + QT |
| T3 | `cls_results` | `result_data` + DICOM file refs | TDE on DB · S3 server-side encryption on file | display | 30 năm | BS + KTV + QT |
| T2 | `invoices` | `total_amount`, `paid_amount` | TDE | display | 10 năm (kế toán) | Lễ tân + QT |
| T3 | `payments` | `card_last4`, `qr_txn_id` | AES-256 column | redact full card | 10 năm | QT only |
| T3 | `audit_log` | `before_data` + `after_data` (JSON diff) | AES-256 envelope encrypt | append-only · không UPDATE/DELETE | 7 năm (BYT compliance) | QT + auditor role |
| T2 | `notifications` | `body` | TDE | display | 90 ngày | Recipient + sender |
| T2 | `accounts` (auth) | `email` | TDE | redact | unlimited (until revoke) | Self + Platform Admin |

→ Tổng: **~30 columns ở tier T2/T3** cần special handling. Dùng làm input cho code review checklist + audit script.

---

## 2. Chiến lược mã hoá (Encryption Strategy)

3 lớp bảo vệ độc lập, áp dụng đồng thời (defense in depth):

### 2.1 Lớp 1 — Encryption in-transit (NFR-005)

**Mục tiêu**: Chống nghe lén / MITM giữa client ↔ server, server ↔ server.

| Kết nối | Cơ chế | Cipher | Key |
|---|---|---|---|
| Client (Tauri / Web) ↔ FastAPI | TLS 1.3 bắt buộc · cấm 1.2 trở xuống · HSTS preload max-age=1y | TLS_AES_256_GCM_SHA384 (preferred) · TLS_CHACHA20_POLY1305_SHA256 | Let's Encrypt cert · auto-renew certbot · 90 ngày |
| FastAPI ↔ Postgres | mTLS (NFR-036) — server cert + client cert | TLS 1.3 | Cert internal CA (HashiCorp Vault) · 30 ngày rotate |
| FastAPI ↔ Redis | mTLS | TLS 1.3 | Same |
| FastAPI ↔ Arq worker | mTLS via Redis | — | Same |
| FastAPI ↔ S3 (DICOM/backup) | TLS 1.3 + signed request V4 | — | AWS IAM role |
| Outbound webhook | TLS 1.3 + HMAC-SHA256 signature | — | Per-clinic webhook secret |

**Verify**: SSL Labs A+ rating quarterly.

### 2.2 Lớp 2 — Encryption at-rest (NFR-006)

**Mục tiêu**: Chống truy cập trái phép vào storage (disk theft, snapshot leak, S3 bucket misconfig).

#### 2.2.1 Database

| Loại data | Cơ chế | Key management |
|---|---|---|
| Postgres data files | TDE (Transparent Data Encryption) AES-256 toàn bộ DB | Master key trong AWS KMS / HashiCorp Vault |
| WAL (Write-Ahead Log) | Same TDE | Same |
| Backup files | AES-256 trước khi upload S3 | Backup key tách biệt với master DB key |

#### 2.2.2 Application-level encryption (NFR-024, NFR-025)

Cho **Tier T3** columns vốn quá nhạy (CCCD, BHYT card, MFA secret, audit diff): thêm 1 lớp **column-level encryption** trên top TDE.

```python
# Pattern dùng pgcrypto + envelope encryption
from app.core.crypto import encrypt_field, decrypt_field

class Patient(BaseEntity):
    cccd_encrypted = Column(LargeBinary)  # ciphertext
    
    @property
    def cccd(self) -> str:
        return decrypt_field(self.cccd_encrypted, key_alias=f"clinic:{self.clinic_id}:pii")
    
    @cccd.setter
    def cccd(self, value: str):
        self.cccd_encrypted = encrypt_field(value, key_alias=f"clinic:{self.clinic_id}:pii")
```

**Envelope encryption**:
- 1 master key per clinic (`clinic:{id}:pii`) trong KMS
- Mỗi field encrypt với data key (DEK) random, DEK encrypt với master key
- DEK đính kèm ciphertext, master key ở KMS không bao giờ rời KMS
- → leak DB cũng không decrypt được nếu không có quyền KMS

**Lợi ích**:
- Tách quyền DBA và security: DBA query thấy `\xab12...` ciphertext, cần KMS permission để decrypt
- Per-tenant key isolation: leak 1 clinic key không ảnh hưởng clinic khác
- Audit per-decrypt: KMS log mỗi lần decrypt → forensic
- Crypto-shred: revoke KMS key → field forever unreadable (instant data destruction)

#### 2.2.3 File storage (DICOM, backups, exports)

| Loại | Cơ chế |
|---|---|
| DICOM images | S3 SSE-KMS (server-side AES-256) + signed URL TTL 15 phút |
| Backups | Encrypt local AES-256 bằng GnuPG → upload S3 SSE-S3 |
| Exports (CSV/PDF) | AES-256 + password user-provided · TTL 24h trên storage |

### 2.3 Lớp 3 — Field-level masking (display-time)

Ngay cả khi user có quyền xem, **mặc định mask** sensitive fields. User phải click "Hiện" có chủ đích mới load full.

| Field | Default display | Khi click "Hiện" |
|---|---|---|
| CCCD | `***-****-1234` | `0791234567890` (audit log access) |
| Số thẻ BHYT | `HC***1234` | full string (audit) |
| Phone | `***1234` | full (audit) |
| Email | `n***@gmail.com` | full (audit) |
| Card last4 | `**** **** **** 1234` | (không cho show full — chỉ last4 lưu trong DB) |
| MFA secret | (không hiển thị bao giờ) | — |

**Implementation**: Pydantic schema có 2 mode `Display` (mask) và `Reveal` (full). Endpoint `/patients/{id}` mặc định trả Display; `?reveal=true` trả Full + audit access log + require permission `patient.pii.reveal`.

---

## 3. Quản lý khoá mã hoá (Key Management — NFR-026)

### 3.1 Hierarchy keys

```
Master Key (in KMS, never leaves)
  │
  ├── Tenant Key (1 per clinic) — encrypts:
  │     ├── Tenant DEK (data encryption key, used for field-level)
  │     └── Tenant audit key (for audit_log envelope)
  │
  ├── JWT signing key (rotate 30d) — RS256 keypair
  │
  ├── Backup key (rotate 90d)
  │
  └── Webhook signing key (1 per clinic, user-rotatable)
```

### 3.2 Rotation policy

| Key | Rotation cycle | Procedure | Downtime |
|---|---|---|---|
| Master Key (KMS) | 1 năm | KMS auto-rotate (re-encrypt tenant keys) | 0 (transparent) |
| Tenant Key | 1 năm hoặc on-demand (vd: nghi ngờ leak) | Background job re-encrypt all field-level data | 0 (online re-encrypt) |
| JWT signing | 30 ngày | Generate new keypair → publish public key → grace 7d → revoke old | 0 (overlap) |
| Backup key | 90 ngày | Old backups vẫn dùng key cũ (versioned) · backup mới dùng key mới | 0 |
| Webhook signing | User-rotatable bất cứ lúc nào | UI button "Rotate webhook secret" | 0 |
| TLS cert | 90 ngày (Let's Encrypt) | certbot auto | 0 (zero-downtime renewal) |

### 3.3 Crypto-shred (instant data destruction)

Yêu cầu HIPAA + Nghị định 13: khi BN yêu cầu xoá hồ sơ (right to erasure NFR-032), không cần xoá hết data physical (chậm + không reliable). Thay vào đó:

1. Soft delete row (set `deleted_at`)
2. Revoke encryption key dùng cho rows đó (per-tenant per-purpose key)
3. → Ciphertext còn nguyên trên disk nhưng forever unreadable
4. Sau retention period, hard delete physical

**Trade-off**: Không reversible — phải confirm 2 lần. Audit event `crypto.shred.executed`.

---

## 4. Quản lý truy cập (Access Control)

3 lớp combine:

### 4.1 RBAC + RLS (đã có ở TASK-002, TASK-004)

- **RBAC**: 5 system roles + 38 permissions + multi-role + grant/deny override (xem `RBAC` group function list)
- **RLS** (Row-Level Security): Postgres policy enforce `clinic_id = app.current_clinic_id` cho mọi query
- **Middleware**: `app/core/tenancy.py` set RLS session var từ JWT mỗi request

### 4.2 ABAC (Attribute-Based — Phase 2)

Cho các trường hợp RBAC không đủ:

| Scenario | Rule |
|---|---|
| BS chỉ thấy BN của chính mình hôm nay | `visit.doctor_id == current_user.id AND visit.created_at::date == today` |
| Lễ tân không thấy hồ sơ của VIP patients | `patient.tags NOT CONTAINS 'vip' OR current_user.role >= admin` |
| Audit log chứa diff của bệnh án chỉ QT thấy | `audit_log.module != 'visit' OR current_user.role == admin` |

Implementation: Open Policy Agent (OPA) sidecar — policy `.rego` files versioned trong repo.

### 4.3 PII reveal permission (T3 fields)

Mặc định mọi user (kể cả có `patient.read`) chỉ thấy mask. Để xem CCCD/BHYT đầy đủ cần thêm `patient.pii.reveal` permission. Mỗi reveal:
- Audit log với reason field bắt buộc nhập (vd: "Verify danh tính khi bốc số thuốc đặc biệt")
- Rate limit 20 reveals/giờ/user — vượt → alert security team
- Anomaly detection: BS reveal 50 BN/ngày trong khi trung bình 2 BN/ngày → alert + tạm khoá quyền

---

## 5. PII Lifecycle Management

### 5.1 Collect (Thu thập)

**Nguyên tắc data minimization (NFR-031)**:
- Chỉ thu khi cần — không lưu thông tin không dùng đến
- Vd: KHÔNG lưu màu mắt / chiều cao của cha mẹ BN nếu không phải nhi khoa
- Form đăng ký BN có 2 mode: Quick (tên + SĐT + DOB + giới — minimal) và Full (thêm CCCD + BHYT + địa chỉ — khi cần khám BHYT)

**Consent tracking**:
- Lần đầu BN check-in: hiện modal "Chính sách bảo mật" + checkbox đồng ý. Lưu `consent_log` (BN, ngày, version chính sách, IP, signature digital nếu có)
- BN có thể withdraw consent bất cứ lúc nào → trigger Right to Erasure flow

### 5.2 Store (Lưu trữ)

- Tất cả T2/T3 → encryption (xem §2)
- Sao lưu: backup encryption + offsite (NFR-041)
- Index: KHÔNG tạo plain index trên T3 fields. Search bằng deterministic encryption (cùng plaintext → cùng ciphertext) HOẶC blind index (HMAC trên field).

### 5.3 Use (Sử dụng)

- Mọi access T2/T3 ghi audit (NFR-009)
- Display masking (xem §2.3)
- Log redaction: KHÔNG log full email/phone trong structlog. VD `bs.an@hd.vn` → `b***@h***.vn`
- Tránh PII trong URL query string (dễ leak trong access log) — chỉ POST body

### 5.4 Transmit (Truyền)

- TLS 1.3 mọi nơi (xem §2.1)
- Webhook outbound: HMAC-SHA256 signature header + cấm gửi T3 ra ngoài clinic (vd: webhook chỉ chứa IDs, app receiver phải gọi lại để fetch detail)

### 5.5 Archive (Lưu trữ dài hạn)

- BN data: 30 năm theo Thông tư 46/2018 BYT
- Audit log: 7 năm (compliance)
- Sau 5 năm → auto-archive vào S3 Glacier (rẻ hơn 10x, retrieve trong 24h)
- Archive cũng encrypted

### 5.6 Delete (Xoá)

| Loại delete | Khi nào | Cơ chế |
|---|---|---|
| Soft delete | User click "Xoá" thông thường | Set `deleted_at`, ẩn khỏi query mặc định, vẫn restore được trong 30 ngày |
| Hard delete (BN) | BN yêu cầu Right to Erasure (Nghị định 13) hoặc sau retention 30 năm | Hard DELETE row + crypto-shred encryption key + audit event |
| Hard delete (User NV) | User nghỉ việc 5 năm | Same |
| Crypto-shred | Khẩn cấp (data breach detected) | Revoke key — ciphertext remain but unreadable |
| Backup purge | Hard delete xong → next backup không còn data | Sau 7 backup cycles → backup cũ nhất bị purge có data |

---

## 6. Authentication & Session Security

### 6.1 Password (NFR-027)

| Yêu cầu | Implementation |
|---|---|
| Hash | bcrypt cost ≥12 (NFR-027) |
| Min length | 12 ký tự (config được, default 12) |
| Complexity | ≥1 chữ hoa + ≥1 chữ thường + ≥1 số + ≥1 ký tự đặc biệt |
| History | Không cho dùng lại 5 password gần nhất |
| Rotation | 90 ngày (config được) |
| Reset | Email magic link 15 phút TTL · 1-shot · audit |
| Forgot | Public form gửi email link (không tiết lộ user tồn tại — generic message) |
| Bcrypt salt | Auto per-password (built-in bcrypt) |
| Pepper | Optional global pepper trong env (defense in depth) |

### 6.2 MFA (NFR-010 v2)

| Yêu cầu | Implementation |
|---|---|
| Method | TOTP (Google Authenticator, Authy) — primary · SMS backup · Email backup |
| Secret storage | AES-256 column-level (xem §2.2.2) |
| Backup codes | 10 single-use codes generated lần setup, hash bcrypt |
| Recovery | Admin reset MFA → audit + email user |
| Enforcement | Per-role (xem TAB_MATRIX §Bảo mật → MFA): QT bắt buộc, BS bắt buộc, DS khuyến nghị, ĐD/Lễ tân tuỳ chọn |

### 6.3 JWT (NFR-028)

| Yêu cầu | Implementation |
|---|---|
| Algorithm | RS256 (asymmetric) — KHÔNG dùng HS256 trong v2+ vì shared secret nguy hiểm |
| Signing key | Rotate 30 ngày · public key publish ở `/.well-known/jwks.json` cho service verify |
| Access token TTL | 15 phút (NFR-022) |
| Refresh token TTL | 7 ngày · rolling (mỗi refresh sinh refresh mới + revoke cũ) |
| Storage FE | Tauri secure storage (encrypted) — không localStorage |
| Revoke | Blacklist Redis với TTL = remaining lifetime |
| Claims | `sub`, `clinic_id`, `roles[]`, `perms[]`, `applied_role`, `iat`, `exp`, `jti` |

### 6.4 Session fingerprinting (NFR-029)

Mỗi JWT issue đính kèm session fingerprint:
- Device ID (Tauri uniqueId hoặc browser fingerprint)
- IP address (geo-location)
- User-agent
- Time

→ Khi user dùng JWT từ device/IP khác đột ngột → verify lại MFA HOẶC force re-login + alert email "Phiên đăng nhập từ thiết bị mới".

### 6.5 Account lockout (NFR-022 + AUTH-006)

- 5 lần fail liên tiếp trong 15 phút → lock 30 phút
- Notify user qua email
- Admin có thể manual unlock với audit
- IP-based rate limit: 10 login attempts/phút/IP, 100/giờ/IP — block IP nếu vượt 30 phút

---

## 7. Audit & Forensic Logging

### 7.1 Audit log immutable (NFR-009)

| Yêu cầu | Implementation |
|---|---|
| Storage | Bảng `audit_log` Postgres |
| Permission | Postgres role app: GRANT INSERT, REVOKE UPDATE/DELETE (constraint level) |
| Append-only verify | Daily cron check `pg_class.relchecks` có constraint immutable |
| Hash chain | Mỗi row có `hash = SHA256(prev_hash || row_data)` — tamper detection (NFR-044) |
| Retention | 7 năm (BYT) |
| Backup | Riêng biệt với main DB · offsite encrypted (NFR-041) |
| Diff data | Encrypted with audit-specific envelope key (xem §2.2.2) |

### 7.2 Trường ghi cho mỗi event

```json
{
  "id": "uuid",
  "timestamp": "2026-04-30T09:48:23.123Z",
  "actor": {
    "user_id": "uuid",
    "applied_role": "admin",  // RBAC-015
    "device_fingerprint": "...",
    "ip": "192.168.1.42",
    "geo": "VN/HCM",
    "user_agent": "Tauri/2.0.1"
  },
  "action": "config.update",
  "resource": {
    "type": "service",
    "id": "DV-022",
    "clinic_id": "uuid"
  },
  "before_data": "<encrypted JSON>",
  "after_data": "<encrypted JSON>",
  "reason": "Cập nhật giá DV theo Q2/2026",  // user-input cho critical action
  "verdict": "success",
  "duration_ms": 142,
  "request_id": "uuid",
  "trace_id": "uuid",
  "hash_prev": "SHA256...",
  "hash_self": "SHA256(hash_prev || row_data)"
}
```

### 7.3 Anomaly detection (NFR-042)

Background job (Arq) chạy mỗi 15 phút, scan audit log với rules:

| Rule | Trigger | Action |
|---|---|---|
| `failed_login_burst` | ≥10 failed login từ 1 IP trong 5 phút | Block IP 1h + alert |
| `mass_pii_reveal` | 1 user reveal CCCD ≥30 BN trong 1h | Tạm khoá `patient.pii.reveal` + alert SOC |
| `cross_clinic_access` | User truy cập clinic mà không có role pivot | 403 + alert critical |
| `sudden_role_grant` | Role mới được grant + ngay lập tức user dùng critical permission | Force re-MFA + audit |
| `mass_export` | 1 user export ≥100 BN trong 1h | Tạm dừng export + alert |
| `audit_tamper_detected` | Hash chain verify fail | Lockdown clinic + page on-call |
| `key_decrypt_anomaly` | KMS decrypt rate >10× baseline | Alert security team |

### 7.4 Forensic preservation (NFR-044)

Khi nghi ngờ breach/tampering:
- Snapshot DB tại thời điểm phát hiện → preserve "chain of custody"
- Export audit log (last 30 days) signed PGP cho legal
- Lock affected user accounts (không xoá, không phục hồi MFA)
- Document timeline + chain of custody trong incident ticket

---

## 8. Network Security

### 8.1 WAF (NFR-034)

Cloudflare hoặc AWS WAF rules:
- OWASP Top 10 ruleset (auto-update)
- VN-specific: block IP từ countries không serve (configurable per clinic)
- Rate limit per endpoint:
  - `/auth/login`: 10/min/IP
  - `/api/*` write: 60/min/user
  - `/reports/*`: 30/min/user
- Bot detection (challenge / block headless browser unsigned)
- Custom rules: SQL keywords trong query string → block

### 8.2 DDoS protection (NFR-035)

- Cloudflare Pro+ with Always Online
- Rate limit + circuit breaker FastAPI level (slowapi + tenacity)
- Auto-scale infrastructure (k8s HPA cho pod, RDS read replica)

### 8.3 mTLS internal (NFR-036)

Service-to-service không exposed public:
- API ↔ DB ↔ Redis ↔ Worker ↔ S3
- Cert internal CA (HashiCorp Vault), 30d rotate auto
- Cert pinning ở client side (verify subject CN)

### 8.4 Egress control

Outbound từ FastAPI:
- Whitelist domains: VSS API, Twilio, SendGrid, S3, KMS
- Block tất cả khác
- Webhook outbound: chỉ tới URL đã verify (challenge response handshake)

---

## 9. Application Security

### 9.1 Input validation

- Pydantic v2 schema mọi request body
- Type strict (no Any)
- Bounded length (max 10000 chars cho text, 100 chars cho name)
- Whitelist regex cho format (phone, email, code)
- File upload: whitelist mime + scan virus (ClamAV) + max 10MB

### 9.2 Output encoding

- React auto-escape JSX (default)
- DOMPurify cho dangerouslySetInnerHTML (chỉ template email)
- CSP header: `default-src 'self'; script-src 'self' 'wasm-unsafe-eval'`

### 9.3 SQL injection prevention

- SQLAlchemy ORM mọi query — KHÔNG raw SQL trừ migration
- Migration raw SQL: review checklist — no string interp với user input
- Parameterized query 100% — verify qua SAST

### 9.4 CSRF

- SameSite=Strict cookie cho session
- CSRF token cho mutation requests (Double-submit cookie)
- Origin/Referer check

### 9.5 XSS prevention

- React + auto-escape
- CSP strict
- Avoid `dangerouslySetInnerHTML` trừ trusted source
- Sanitize patient note input (markdown allow whitelist tags)

### 9.6 Secret management (NFR-040)

- Không hardcode trong code → enforce git-secrets pre-commit hook + GitHub secret scanning
- Dev: `.env.local` (gitignore)
- Prod: HashiCorp Vault hoặc AWS Secrets Manager
- Tauri config: secrets không bundle, fetch runtime
- Frontend không nhận secret nào (chỉ public config)

### 9.7 SAST + DAST + Dependency scan (NFR-037, NFR-038, NFR-039)

| Tool | Scope | Frequency | Block PR if fail |
|---|---|---|---|
| ruff (Python lint + security) | BE | Pre-commit + CI | Yes |
| Bandit (Python SAST) | BE | CI | Yes (high+) |
| ESLint security plugin | FE | Pre-commit + CI | Yes |
| Semgrep (multi-lang) | All | CI | Yes (high) |
| Safety (Python deps CVE) | BE | CI + dependabot | Yes (critical) |
| npm audit (Node deps) | FE | CI + dependabot | Yes (critical) |
| Trivy (container scan) | Docker images | CI + nightly | Yes (high) |
| OWASP ZAP (DAST) | Pre-prod env | Pre-major-release | Yes (high) |
| Pen test (NFR-046) | Production | Annually by 3rd party | Findings tracked → fix |

---

## 10. Backup & Disaster Recovery Security

### 10.1 Backup security (NFR-041)

| Yêu cầu | Implementation |
|---|---|
| Encryption | AES-256 trước khi upload (gpg encrypt → upload S3 SSE-KMS) |
| Access control | IAM role chỉ Ops + DBA · MFA-required cho restore |
| Network | mTLS cho upload · S3 bucket private · VPC endpoint |
| Integrity | SHA-256 checksum + sign GPG · verify khi restore |
| Retention | 7 daily + 4 weekly + 12 monthly · auto-purge cũ hơn |
| Offsite | Cross-region replication (HCM → SG) · encrypted in transit |
| Test restore | Hàng quý chọn random backup → restore vào staging → verify integrity |

### 10.2 Recovery procedures

| Scenario | RPO | RTO | Procedure |
|---|---|---|---|
| Single corrupted row | 0 | 5 phút | Point-in-time recovery (PITR) WAL |
| Data corruption (partial) | 1 giờ | 2 giờ | Restore latest good backup → replay WAL |
| Full DB loss | 24 giờ | 4 giờ | Restore latest full → replay WAL → switch DNS |
| Region outage | 24 giờ | 8 giờ | Promote read replica trong region khác |
| Ransomware | 24 giờ | 8 giờ | Isolated → restore offsite backup → forensic |

---

## 11. Incident Response

### 11.1 Detection sources

- Anomaly detection (§7.3)
- WAF alerts
- Customer reports (support@medizen.vn — 24/7 monitored)
- External (security researchers, hash leak monitoring)

### 11.2 Severity classification

| Severity | Định nghĩa | SLA respond |
|:---:|---|:---:|
| **P0 — Critical** | PII/PHI breach confirmed · ransomware · service down >1h | 15 phút |
| **P1 — High** | Suspicious activity · high-value bug bounty · degraded service | 1 giờ |
| **P2 — Medium** | Vulnerability không exploit yet · planned maintenance run-over | 4 giờ |
| **P3 — Low** | Cosmetic security issue · low-risk vulnerability | 1 ngày |

### 11.3 Incident playbook (P0 example)

```
T+0:    Alert raised → On-call engineer paged via PagerDuty
T+5min: Triage — confirm severity, classify
T+10min: Form incident channel (#incident-YYYY-MM-DD)
T+15min: Containment — isolate affected resource (firewall block, key revoke, account lockout)
T+30min: Initial customer notification (in-app banner + email if PHI affected)
T+1h:   Forensic snapshot — preserve evidence (DB dump, audit log export, logs)
T+2h:   Eradication — remove threat (patch CVE, revoke compromised credentials, restore from clean backup)
T+4h:   Recovery — restore service · monitor for reoccurrence
T+24h:  Customer post-incident communication (email + status page)
T+72h:  Regulatory notification if applicable (Nghị định 13 — NFR-043)
T+7d:   Post-mortem (blameless) → action items
T+30d:  Verify action items completed
```

### 11.4 Breach notification (NFR-043)

Theo Nghị định 13/2023/NĐ-CP:
- ≤72 giờ từ khi phát hiện → notify Bộ Thông tin & Truyền thông
- Affected users notify "không chậm trễ không lý do"
- Template email + nội dung tối thiểu: nature of breach, data affected, mitigation, contact DPO
- Maintain list contact DPO (Data Protection Officer) — VISSoft default, custom per clinic Enterprise

---

## 12. Compliance Mapping

### 12.1 HIPAA (US — reference cho design baseline)

| Rule | Yêu cầu | MediZen mapping |
|---|---|---|
| Privacy Rule | Minimum necessary disclosure | RBAC § + display masking § + reveal logging § |
| Security Rule — Administrative | Risk analysis, workforce training | Annually pen test (NFR-046) + quarterly review (NFR-021) |
| Security Rule — Physical | Workstation security, device control | Tauri code signing (NFR-045) + secure storage |
| Security Rule — Technical | Access control, audit, encryption, transmission | RBAC/RLS + audit (NFR-009) + encryption (§2) + TLS (NFR-005) |

### 12.2 Nghị định 13/2023/NĐ-CP (VN — bắt buộc)

| Yêu cầu | Implementation |
|---|---|
| Đồng ý của BN trước khi xử lý | Consent log §5.1 |
| Mục đích thu thập rõ ràng | Privacy policy + Terms |
| Quyền truy cập dữ liệu | Self-service portal (Phase 2) |
| Quyền sửa dữ liệu | UI cho BN (Phase 2) |
| Quyền xoá / Right to Erasure | Soft delete + crypto-shred §5.6 |
| Bảo mật khi xử lý | All this doc |
| Thông báo xâm phạm <72h | NFR-043 + §11.4 |

### 12.3 Thông tư 46/2018/TT-BYT (VN — bệnh án)

| Yêu cầu | Implementation |
|---|---|
| Lưu bệnh án 30 năm | NFR-010 |
| Bảo mật + audit | §1 PII inventory + §7 |
| Backup không mất | NFR-011 + §10 |

### 12.4 OWASP ASVS L2 (target Phase 1)

47 verifications — mapping checklist trong `docs/compliance/owasp-asvs-checklist.md` (cần làm).

---

## 13. Threat Model (STRIDE — focus on data)

| Threat | Asset | Likelihood | Impact | Mitigation |
|---|---|:---:|:---:|---|
| **Spoofing** — fake user impersonate BS | JWT | Med | High | RS256 + key rotation (NFR-028) + session fingerprint (NFR-029) |
| **Tampering** — DB row modified bypass app | DB direct access | Low | High | DBA mTLS only · audit on Postgres extension · RLS enforce |
| **Tampering** — audit log altered | audit_log | Low | Critical | Immutable + hash chain (§7.1) |
| **Repudiation** — user deny đã thực hiện action | audit_log | Low | Med | applied_role tracking (RBAC-015) + signed JWT in audit |
| **Info disclosure** — PII leak through log | structlog output | Med | High | Redaction (NFR-030) + log review |
| **Info disclosure** — MitM client-server | TLS | Low | High | TLS 1.3 + HSTS preload (NFR-005) |
| **Info disclosure** — backup snapshot leak | S3 | Low | High | Backup encryption (NFR-041) + private bucket + IAM strict |
| **Info disclosure** — DB stolen | Postgres dump | Med | Critical | TDE + column-level (NFR-006, NFR-024, NFR-025) |
| **DoS** — flood login | API | High | Med | Rate limit + WAF (NFR-022, NFR-034, NFR-035) |
| **DoS** — expensive query | Reports endpoint | Med | Med | Query timeout 30s + read replica + cache |
| **EoP** — privilege escalation | RBAC | Low | Critical | OPA policy verify + RBAC test e2e + SoD (RBAC-016) |
| **EoP** — cross-tenant leak | RLS | Low | Critical | RLS enforce + middleware + e2e test mỗi module |

→ Top 3 priorities (high likelihood × high impact):
1. **Info disclosure DB stolen** — NFR-024 column-level encryption Phase 1
2. **DoS login flood** — NFR-022 + WAF deployed
3. **Info disclosure log leak** — NFR-030 redaction enforced + log review

---

## 14. Sensitive data handling — Code review checklist

Mỗi PR đụng tới T2/T3 fields phải pass checklist (PR template):

```markdown
## Security checklist (T2/T3 data)
- [ ] Field này có trong PII inventory (§1.1)? Nếu không → cập nhật doc
- [ ] Encryption applied? (TDE + column-level cho T3)
- [ ] Audit excluded nếu T3 credential? `__audit_exclude__: ClassVar[frozenset[str]]`
- [ ] Display masking? Default mode = mask, reveal = audit + permission
- [ ] Log redaction? structlog output không lộ full value
- [ ] Index strategy? KHÔNG plain index trên T3 — dùng deterministic encryption hoặc blind index
- [ ] Test DB e2e với encrypted value (NFR-007 không mock encryption)
- [ ] PR description giải thích tại sao field cần thiết (data minimization §5.1)
```

---

## 15. Đo lường + audit

### 15.1 Metrics theo dõi

| Metric | Threshold | Alert |
|---|---|---|
| Failed login rate | >5% in 5min | PD alert |
| KMS decrypt rate | >10× baseline | Slack alert security |
| Audit log insert rate | <1/min for >10min (= app down?) | PD alert |
| Backup success rate | <100% in 24h | Slack alert ops |
| Hash chain verify | 0 mismatch | If any → P0 |
| Time-to-patch CVE high | <7 days | Track in dashboard |
| Pen test findings | 0 critical · ≤3 high | Annual report |

### 15.2 Quarterly review (NFR-021)

Checklist 14 mục review by GĐ PK + Legal mỗi quý:
- [ ] Tất cả PII fields trong inventory đúng?
- [ ] Quyền truy cập (RBAC) reflect đúng vai trò hiện tại của staff?
- [ ] Backup test restore thành công?
- [ ] Audit log không có gap > 1 phút?
- [ ] KMS keys rotated đúng cycle?
- [ ] CVE high-severity ≤7 ngày time-to-patch?
- [ ] Pen test recommendations đã apply?
- [ ] Consent log đầy đủ cho BN mới?
- [ ] Right to Erasure requests xử lý ≤30 ngày?
- [ ] Breach notification process drill (annually)?
- [ ] Staff security training (annually)?
- [ ] DPO contact info up-to-date?
- [ ] Disaster recovery drill (annually)?
- [ ] Compliance documentation up-to-date?

---

## 16. Các trách nhiệm (Roles & Responsibilities)

| Role | Responsibility |
|---|---|
| **Platform Security Team** | Master KMS, cross-tenant security, incident response coordination, pen test |
| **Clinic Admin** | RBAC config, MFA enforce, BN consent verification, breach response trong PK |
| **DBA** | DB encryption verify, backup integrity, restore test, hash chain audit |
| **DevOps** | TLS cert renewal, WAF rules, infrastructure security |
| **Engineers (BE/FE)** | Code security checklist, dependency scan response, secret hygiene |
| **DPO (Data Protection Officer)** | Compliance, breach notification, BN data subject requests |
| **End users (NV)** | Password hygiene, MFA setup, không share credential, report suspicious activity |

---

## 17. Roadmap

### Phase 1 (v1 MVP)
- [x] TLS 1.3 + HSTS (NFR-005)
- [x] RLS multi-tenant (NFR-007)
- [x] Audit log immutable (NFR-009)
- [x] Rate limit (NFR-022)
- [x] WCAG 2.1 AA (NFR-012)
- [ ] **bcrypt cost 12** (NFR-027) — chuyển từ default 10
- [ ] **Column-level encryption cho T3 critical** (NFR-024) — CCCD, BHYT, MFA
- [ ] **Display masking + reveal permission** (§2.3) — UI + BE
- [ ] **PII redaction trong log** (NFR-030)
- [ ] **Hash chain audit** (§7.1)
- [ ] **Anomaly detection cron** (NFR-042) — 7 rules
- [ ] **Backup encryption** (NFR-041)
- [ ] **Secret management Vault** (NFR-040)

### Phase 2
- [ ] MFA TOTP (AUTH-010)
- [ ] JWT RS256 + key rotation (NFR-028)
- [ ] Session fingerprinting (NFR-029)
- [ ] Right to Erasure UI (NFR-032)
- [ ] Data portability export (NFR-033)
- [ ] Crypto-shred (§3.3)
- [ ] mTLS internal (NFR-036)
- [ ] OPA ABAC (§4.2)
- [ ] WAF (NFR-034)
- [ ] DAST OWASP ZAP CI (NFR-038)

### Phase 3
- [ ] ISO 27001 readiness
- [ ] Pen test annual (NFR-046)
- [ ] Bug bounty program

---

## 18. Cross-references

- **App config UI**: [TAB_MATRIX.md §Section: Bảo mật & Mã hóa](TAB_MATRIX.md#section-bảo-mật--mã-hóa)
- **Function codes**: `docs/clinic_management_function_list.md` §26 NFR-005..NFR-046
- **RBAC implementation**: TASK-004 RBAC + RLS infrastructure (TASK-002)
- **Multi-role audit applied_role**: [MULTI_ROLE_UX.md §3.3](MULTI_ROLE_UX.md#33-action-với-role-gốc)
- **Audit pattern code**: `clinic-cms/app/core/audit.py` — `__auditable__` + `__audit_exclude__`
- **PROJECT.md §Audit + §Authorization** — patterns canonical

---

**Status**: v1 spec ✓ — Ready cho:
- Threat modeling workshop (whole-team)
- Security review pre-Phase 1 launch
- Pen test scoping document
- DPA template với customer Enterprise
