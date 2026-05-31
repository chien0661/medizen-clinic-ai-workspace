# TASK-052 — API ↔ Function Mapping (v2, source-verified)

> **Deliverable**: ánh xạ từng function code → endpoint backend đã ship.
> **Nguồn function list**: `scripts/function_list_data.py` (461 function, 28 nhóm).
> **Codebase đối chiếu**: `../clinic-cms-merge` (main worktree) — 207 REST endpoints.
> **Ngày lập**: 2026-05-30 · **v2 2026-05-30**: 8 cụm DRIFT/GAP/nghi-ngờ đã được **xác minh trực tiếp trong source** (file:line) qua 8 sub-agent đọc code. Nhiều mục v1 đánh MAPPED đã hạ xuống GAP/DRIFT.

## Quy ước trạng thái (Legend)

| Ký hiệu | Nghĩa |
|---|---|
| ✅ **MAPPED** | Có endpoint backend hiện thực đúng chức năng |
| ⚠️ **DRIFT** | Có endpoint/code nhưng lệch hoặc chỉ phủ một phần spec |
| ❌ **GAP** | Chức năng cần API nhưng **chưa có** (gồm cả code "dead" chưa nối route) |
| ➖ **N/A** | Ngoài phạm vi REST: FE-only, Tauri-native, infra/middleware, Arq job, hoặc Phase 2/3 (💡) |

> Các ghi chú có tiền tố **"VERIFIED"** = đã đọc source xác nhận, kèm `file:line`. Một số chức năng ship vượt function list (MFA, multi-clinic, substitutes, erasure) → MAPPED dù fn list còn ⬜/💡.

## Tổng kết

**Tổng: 461 function** — ✅ 200 MAPPED · ⚠️ 24 DRIFT · ❌ 85 GAP · ➖ 152 N/A

| Nhóm | Tổng | ✅ MAPPED | ⚠️ DRIFT | ❌ GAP | ➖ N/A |
|---|---:|---:|---:|---:|---:|
| AUTH | 22 | 15 | 0 | 2 | 5 |
| RBAC | 18 | 13 | 2 | 0 | 3 |
| TENT | 14 | 3 | 3 | 7 | 1 |
| SUB | 25 | 0 | 3 | 18 | 4 |
| PAT | 22 | 19 | 0 | 1 | 2 |
| VIS | 14 | 13 | 0 | 1 | 0 |
| VTL | 14 | 11 | 0 | 1 | 2 |
| DIAG | 9 | 7 | 0 | 0 | 2 |
| SVC | 9 | 6 | 1 | 1 | 1 |
| RX | 16 | 11 | 0 | 1 | 4 |
| MED | 18 | 13 | 0 | 2 | 3 |
| PHRM | 13 | 9 | 0 | 2 | 2 |
| APPT | 17 | 6 | 2 | 4 | 5 |
| BILL | 23 | 11 | 4 | 4 | 4 |
| HR | 22 | 18 | 0 | 1 | 3 |
| RPT | 18 | 5 | 1 | 9 | 3 |
| NOTI | 15 | 5 | 1 | 4 | 5 |
| AUDIT | 15 | 10 | 0 | 2 | 3 |
| CFG | 17 | 8 | 2 | 5 | 2 |
| PLT | 24 | 6 | 5 | 12 | 1 |
| JOB | 14 | 1 | 0 | 0 | 13 |
| DATA | 11 | 0 | 0 | 4 | 7 |
| INT | 20 | 1 | 0 | 4 | 15 |
| I18N | 7 | 0 | 0 | 0 | 7 |
| A11Y | 7 | 0 | 0 | 0 | 7 |
| THEME | 3 | 0 | 0 | 0 | 3 |
| NAV | 8 | 4 | 0 | 0 | 4 |
| NFR | 46 | 5 | 0 | 0 | 41 |
| **TỔNG** | **461** | **200** | **24** | **85** | **152** |

## Chi tiết theo nhóm

### AUTH — Authentication & Session

| Code | Chức năng | Fn status | Mapping | Endpoint / Ghi chú |
|---|---|:--:|:--:|---|
| AUTH-001 | Đăng nhập email/password | 🔄 | ✅ MAPPED | POST /auth/login — fn 🔄: spec drops clinic_code — verify migration |
| AUTH-002 | Refresh token | ✅ | ✅ MAPPED | POST /auth/refresh |
| AUTH-003 | Logout | ✅ | ✅ MAPPED | POST /auth/logout |
| AUTH-004 | Đổi mật khẩu | ✅ | ✅ MAPPED | POST /auth/change-password |
| AUTH-005 | Forced change password | ✅ | ✅ MAPPED | POST /auth/change-password — forced via must_change_password flag |
| AUTH-006 | Account lockout | ✅ | ✅ MAPPED | POST /auth/login — lockout in login (lockout_service) |
| AUTH-007 | Rate limit | ✅ | ✅ MAPPED | POST /auth/login — slowapi rate-limit middleware |
| AUTH-008 | Reset password (admin gen) | ⬜ | ❌ GAP | VERIFIED GAP — no clinic-admin staff-password reset (users/api/routes.py only POST /users create; only platform superadmin reset-password) |
| AUTH-009 | Forgot password (self-service) | ⬜ | ❌ GAP | forgot-password self-service — not built (TASK-027) |
| AUTH-010 | MFA TOTP | 💡 | ✅ MAPPED | POST /auth/mfa/{enroll,verify,disable,challenge,backup-codes/regenerate} — shipped TASK-038; fn list still 💡 |
| AUTH-011 | MFA bắt buộc cho super admin | 💡 | ➖ N/A | MFA-mandatory-superadmin = policy (💡) |
| AUTH-012 | Session timeout | ✅ | ✅ MAPPED | (JWT TTL) — session timeout = token TTL |
| AUTH-013 | Show password toggle | ✅ | ➖ N/A | show-password toggle — FE |
| AUTH-014 | Remember me | ✅ | ➖ N/A | remember-me — Tauri secure storage (FE) |
| AUTH-015 | Last login tracking | ✅ | ✅ MAPPED | POST /auth/login — last_login updated in login |
| AUTH-016 | IP whitelist (super admin) | 💡 | ➖ N/A | IP whitelist — policy (💡) |
| AUTH-017 | Re-authentication | 💡 | ➖ N/A | re-authentication — future (💡) |
| AUTH-018 | Account ↔ Multi-clinic mapping | ⬜ | ✅ MAPPED | GET /auth/clinics, POST /auth/select-clinic — multi-clinic (TASK-033); fn ⬜ |
| AUTH-019 | Default clinic per account | ⬜ | ✅ MAPPED | PATCH /auth/clinics/{clinic_id}/default |
| AUTH-020 | Auto-resolve clinic post-login | ⬜ | ✅ MAPPED | POST /auth/login + /auth/select-clinic — auto-resolve clinic |
| AUTH-021 | Switch-clinic flow + JWT reset | ⬜ | ✅ MAPPED | POST /auth/select-clinic — switch-clinic + JWT reset |
| AUTH-022 | Last-active clinic remembered | ⬜ | ✅ MAPPED | POST /auth/login — last-active clinic (Redis) |

### RBAC — Authorization

| Code | Chức năng | Fn status | Mapping | Endpoint / Ghi chú |
|---|---|:--:|:--:|---|
| RBAC-001 | 5 system roles | ✅ | ✅ MAPPED | GET /roles — system roles seeded |
| RBAC-002 | Permission catalog (38 perms) | ✅ | ✅ MAPPED | GET /permissions |
| RBAC-003 | Multi-role per user | ✅ | ✅ MAPPED | GET/POST /users/{id}/roles, DELETE .../roles/{role_id} |
| RBAC-004 | Extra grant per user | ✅ | ✅ MAPPED | POST /users/{id}/extra-permissions — grant |
| RBAC-005 | Extra deny per user | ✅ | ✅ MAPPED | POST /users/{id}/extra-permissions — deny (effect=deny) |
| RBAC-006 | Permission cache | ✅ | ✅ MAPPED | (JWT 15m + Redis 5m) — permission cache — infra |
| RBAC-007 | Cache invalidation | ✅ | ✅ MAPPED | (role/perm mutation endpoints) — cache invalidation — infra |
| RBAC-008 | Clone system role | ✅ | ⚠️ DRIFT | POST /roles — VERIFIED DRIFT — POST /roles creates BLANK role; real clone_system_role() (rbac_service.py:527) copies perms but is NOT wired to any route (onboarding-only/dead). Clone via API unreachable |
| RBAC-009 | System role immutable | ✅ | ✅ MAPPED | PATCH/DELETE /roles/{id} — system-role immutability guard |
| RBAC-010 | Custom role CRUD | ⬜ | ✅ MAPPED | POST/PATCH/DELETE /roles — custom role CRUD |
| RBAC-011 | Permission group UI | ⬜ | ➖ N/A | permission-group UI — FE |
| RBAC-012 | Role description | ⬜ | ✅ MAPPED | POST/PATCH /roles — role.description field |
| RBAC-013 | Audit role changes | ✅ | ✅ MAPPED | (audit infra) — audit on role/perm endpoints |
| RBAC-014 | Platform RBAC tách biệt | ⬜ | ✅ MAPPED | GET /superadmin/roles, GET /superadmin/permissions — platform RBAC (read) |
| RBAC-015 | Applied role trong audit | ⬜ | ✅ MAPPED | (audit applied_role) — TASK-035 |
| RBAC-016 | Separation of Duties (SoD) | ⬜ | ⚠️ DRIFT | POST /invoices/{id}/payments, POST /pharmacy/dispense/{id} — VERIFIED DRIFT — SoD enforced at exactly 2 sites (sod.py:108 check_no_self_approval @ pharmacy routes.py:129 + billing payment_service.py:88); make_sod_dep factory wired to 0 routes; Rx-approve & price self-approve NOT gated |
| RBAC-017 | Merge sidebar cho multi-role | ⬜ | ➖ N/A | merge-sidebar multi-role — FE |
| RBAC-018 | Multi-role chip ở avatar | ⬜ | ➖ N/A | multi-role avatar chip — FE |

### TENANT — Clinic Signup & Onboarding

| Code | Chức năng | Fn status | Mapping | Endpoint / Ghi chú |
|---|---|:--:|:--:|---|
| TENT-001 | Self-signup form | ⬜ | ❌ GAP | public self-signup form — no public endpoint |
| TENT-002 | Email verification | ⬜ | ❌ GAP | email verification — not built |
| TENT-003 | Tạo clinic + admin user | ⬜ | ⚠️ DRIFT | POST /admin/clinics — VERIFIED DRIFT — clinic_service.create_clinic (clinic_service.py:26-94) creates Clinic+Settings+OnboardingState only; admin user NOT provisioned in same flow (separate /onboarding/users). Not atomic clinic+admin |
| TENT-004 | Clone system roles cho clinic mới | ⬜ | ⚠️ DRIFT | (unwired) — VERIFIED DRIFT — clone_system_role() (rbac_service.py:527) exists but is never called by create_clinic/onboarding (dead code) |
| TENT-005 | First-time login wizard | ⬜ | ✅ MAPPED | POST /onboarding/{start,info,users,shifts,inventory-csv,services,complete}, GET /onboarding/state — wizard real; shifts/services/inventory steps degrade to stubs |
| TENT-006 | Chọn vital preset | ⬜ | ⚠️ DRIFT | POST /onboarding/start — VERIFIED DRIFT — admin picks specialty (general/pediatric/ob_gyn/dermatology/dental) → vital_fields derived implicitly; NO TCM, has dermatology instead; no explicit preset step |
| TENT-007 | Cấu hình prefix code | ⬜ | ❌ GAP | VERIFIED GAP — only invoice_prefix configurable (settings_schemas.py:96); patient/visit prefix absent; no prefix step in onboarding wizard |
| TENT-008 | Lead form (Liên hệ tư vấn) | ⬜ | ❌ GAP | lead form — not built (TASK-026) |
| TENT-009 | Sales-led tạo clinic | ⬜ | ✅ MAPPED | POST /superadmin/clinics — sales-led clinic create |
| TENT-010 | Convert lead → clinic | ⬜ | ❌ GAP | convert lead→clinic — not built |
| TENT-011 | Email verify token TTL 24h | ⬜ | ❌ GAP | email-verify token TTL — not built |
| TENT-012 | Invite resend | ⬜ | ❌ GAP | invite resend — not built |
| TENT-013 | Clinic code uniqueness | ⬜ | ✅ MAPPED | POST /admin/clinics — clinic_code uniqueness (clinic_service.py:53 + DB unique) |
| TENT-014 | reCAPTCHA on signup | ⬜ | ➖ N/A | reCAPTCHA — FE/integration |

### SUB — Subscription & Billing (provider)

| Code | Chức năng | Fn status | Mapping | Endpoint / Ghi chú |
|---|---|:--:|:--:|---|
| SUB-001 | Subscription type | ⬜ | ❌ GAP | VERIFIED GAP — no subscription model/table/service anywhere in app/ (grep 0) |
| SUB-002 | Billing cycle | ⬜ | ❌ GAP | billing cycle — no subscription module |
| SUB-003 | Trial 14 ngày default | ⬜ | ❌ GAP | trial 14d — no subscription module |
| SUB-004 | Grace period | ⬜ | ❌ GAP | grace period — no subscription module |
| SUB-005 | Subscription state machine | ⬜ | ❌ GAP | subscription state machine — no subscription module |
| SUB-006 | SubscriptionGuard middleware | ⬜ | ❌ GAP | VERIFIED GAP — no SubscriptionGuard middleware (grep 0); only require_feature/require_superuser exist |
| SUB-007 | Behavior matrix per status | ⬜ | ❌ GAP | behavior matrix — not built |
| SUB-008 | Read-only mode khi expired | ⬜ | ❌ GAP | read-only-when-expired — not built |
| SUB-009 | Banner cảnh báo trial/grace | ⬜ | ❌ GAP | trial/grace banner — needs subscription data (not built) |
| SUB-010 | Subscription event audit | ⬜ | ❌ GAP | subscription event audit — not built |
| SUB-011 | Renewal manual (super admin) | ⬜ | ❌ GAP | manual renewal — not built |
| SUB-012 | Convert trial → paid | ⬜ | ❌ GAP | convert trial→paid — not built |
| SUB-013 | Upgrade plan | ⬜ | ❌ GAP | upgrade plan — not built |
| SUB-014 | Suspend clinic | ⬜ | ⚠️ DRIFT | PATCH /superadmin/clinics/{id} — VERIFIED DRIFT — only toggles is_active boolean (service.py:104); no suspend status/state machine |
| SUB-015 | Reactivate clinic | ⬜ | ⚠️ DRIFT | PATCH /superadmin/clinics/{id} — VERIFIED DRIFT — only is_active=true; no reactivate transition |
| SUB-016 | Archive clinic | ⬜ | ❌ GAP | VERIFIED GAP — no archive action; is_deleted exists on model but SuperClinicUpdate cannot set it; no archive endpoint |
| SUB-017 | Auto export trước hard delete | ⬜ | ❌ GAP | auto export before hard delete — not built |
| SUB-018 | Hard delete sau 90d | ⬜ | ❌ GAP | hard delete after 90d — not built |
| SUB-019 | Reminder D-14/-7/-3/-1/0 | ⬜ | ❌ GAP | reminder D-14..0 — not built |
| SUB-020 | Daily reminder trong grace | ⬜ | ❌ GAP | daily grace reminder — not built |
| SUB-021 | Subscription metrics dashboard | ⬜ | ⚠️ DRIFT | GET /superadmin/stats — VERIFIED DRIFT — stats (service.py:343) returns only total/active clinics+users, locked_users; NO MRR/ARR/churn/conversion |
| SUB-022 | Auto-renew payment integration | 💡 | ➖ N/A | auto-renew payment — future (💡) |
| SUB-023 | E-invoice integration | 💡 | ➖ N/A | e-invoice — future (💡) |
| SUB-024 | Subscription tiers | 💡 | ➖ N/A | subscription tiers — future (💡) |
| SUB-025 | Free tier vĩnh viễn | 💡 | ➖ N/A | free tier — future (💡) |

### PATIENT — Patient Management

| Code | Chức năng | Fn status | Mapping | Endpoint / Ghi chú |
|---|---|:--:|:--:|---|
| PAT-001 | Tạo bệnh nhân mới | ✅ | ✅ MAPPED | POST /patients |
| PAT-002 | Auto-gen patient_code | ✅ | ✅ MAPPED | POST /patients — auto patient_code |
| PAT-003 | Xem hồ sơ chi tiết | ✅ | ✅ MAPPED | GET /patients/{id} |
| PAT-004 | Sửa thông tin BN | ✅ | ✅ MAPPED | PATCH /patients/{id} |
| PAT-005 | Soft-delete BN | ✅ | ✅ MAPPED | DELETE /patients/{id} — soft-delete |
| PAT-006 | Search theo SĐT | ✅ | ✅ MAPPED | GET /patients/search — phone |
| PAT-007 | Search theo tên (fuzzy) | ✅ | ✅ MAPPED | GET /patients/search — fuzzy name (trigram+unaccent) |
| PAT-008 | Search theo mã BN | ✅ | ✅ MAPPED | GET /patients/search — patient_code |
| PAT-009 | Performance: 100k record <100ms | ✅ | ✅ MAPPED | GET /patients/search — perf — NFR-019 indexes |
| PAT-010 | Guardian relationship | ✅ | ✅ MAPPED | POST/GET /patients/{id}/guardians |
| PAT-011 | Primary contact flag | ✅ | ✅ MAPPED | POST /patients/{id}/guardians — primary contact flag |
| PAT-012 | Merge duplicate BN | ✅ | ✅ MAPPED | POST /patients/merge |
| PAT-013 | Undo merge (7 ngày) | ✅ | ✅ MAPPED | POST /patients/merge/{merge_id}/undo |
| PAT-014 | BHYT info | ✅ | ✅ MAPPED | POST/PATCH /patients — BHYT fields |
| PAT-015 | Allergies tracking | ✅ | ✅ MAPPED | POST/PATCH /patients — allergies field |
| PAT-016 | Chronic conditions | ✅ | ✅ MAPPED | POST/PATCH /patients — chronic conditions |
| PAT-017 | Blood type | ✅ | ✅ MAPPED | POST/PATCH /patients — blood type |
| PAT-018 | DOB hoặc birth_year | ✅ | ✅ MAPPED | POST/PATCH /patients — dob / birth_year |
| PAT-019 | Đính kèm tài liệu | ⬜ | ❌ GAP | attach documents — S3 (INT-010) not wired |
| PAT-020 | Audit patient.read | ✅ | ✅ MAPPED | GET /patients/{id} — audit patient.read |
| PAT-021 | Export hồ sơ BN | 💡 | ➖ N/A | export PDF — future (💡) |
| PAT-022 | Bulk import CSV | 💡 | ➖ N/A | bulk import — future (💡) |

### VISIT — Visit / Encounter

| Code | Chức năng | Fn status | Mapping | Endpoint / Ghi chú |
|---|---|:--:|:--:|---|
| VIS-001 | Tạo visit | ✅ | ✅ MAPPED | POST /visits |
| VIS-002 | Auto-gen visit_number | ✅ | ✅ MAPPED | POST /visits — auto visit_number |
| VIS-003 | Visit state machine | ✅ | ✅ MAPPED | POST /visits/{id}/{start,complete,cancel} — state machine |
| VIS-004 | NO_SHOW status | ✅ | ✅ MAPPED | PATCH /visits/{id} — NO_SHOW status |
| VIS-005 | CANCELLED status | ✅ | ✅ MAPPED | POST /visits/{id}/cancel |
| VIS-006 | PAUSED status | ✅ | ✅ MAPPED | PATCH /visits/{id} — PAUSED status |
| VIS-007 | Resume visit | ✅ | ✅ MAPPED | PATCH /visits/{id} — resume |
| VIS-008 | Lịch sử visit của BN | ✅ | ✅ MAPPED | GET /visits?patient_id — visit history |
| VIS-009 | Visit doctor assignment | ✅ | ✅ MAPPED | POST/PATCH /visits — doctor assignment |
| VIS-010 | Reassign doctor | ✅ | ✅ MAPPED | PATCH /visits/{id} — reassign doctor |
| VIS-011 | Visit reason | ✅ | ✅ MAPPED | POST/PATCH /visits — visit reason |
| VIS-012 | Concurrent call-next safe | ✅ | ✅ MAPPED | POST /visits/call-next — concurrency-safe |
| VIS-013 | Visit completion auto-trigger | ✅ | ✅ MAPPED | POST /visits/{id}/complete — auto-trigger invoice/Rx |
| VIS-014 | Tài liệu đính kèm visit | ⬜ | ❌ GAP | attach documents — storage not wired |

### VITAL — Vital Signs

| Code | Chức năng | Fn status | Mapping | Endpoint / Ghi chú |
|---|---|:--:|:--:|---|
| VTL-001 | 5 specialty preset | ⬜ | ✅ MAPPED | GET /vitals/definitions — presets shipped; fn ⬜ |
| VTL-002 | Dynamic field schema | ⬜ | ✅ MAPPED | GET/POST /vitals/definitions — dynamic schema |
| VTL-003 | Field types: number/text/select/bool | ⬜ | ✅ MAPPED | POST /vitals/definitions — field types |
| VTL-004 | Range bình thường | ⬜ | ✅ MAPPED | POST /vitals/definitions — normal range |
| VTL-005 | Auto-calc fields | ⬜ | ✅ MAPPED | POST /visits/{id}/vitals — auto-calc (BMI) |
| VTL-006 | Vital trends chart | ⬜ | ❌ GAP | vital trends chart — cross-visit aggregation endpoint missing (only per-visit GET) |
| VTL-007 | Schema editor (admin) | ⬜ | ✅ MAPPED | POST/PATCH/DELETE /vitals/definitions — schema editor |
| VTL-008 | Schema versioning | ⬜ | ✅ MAPPED | GET /vitals/definitions/version/{n} — schema versioning |
| VTL-009 | Pediatric percentile chart | 💡 | ➖ N/A | pediatric percentile — future (💡) |
| VTL-010 | OBGYN tuần thai tracker | 💡 | ➖ N/A | OBGYN tracker — future (💡) |
| VTL-011 | TCM mạch/lưỡi | ⬜ | ✅ MAPPED | POST /vitals/definitions — TCM preset fields |
| VTL-012 | Required field per preset | ⬜ | ✅ MAPPED | POST /vitals/definitions — required field per preset |
| VTL-013 | Vital input by nurse | ⬜ | ✅ MAPPED | POST /visits/{id}/vitals — nurse input |
| VTL-014 | Vital alert thresholds | ⬜ | ✅ MAPPED | POST /vitals/definitions — alert thresholds (range) |

### DIAG — Diagnosis & EMR

| Code | Chức năng | Fn status | Mapping | Endpoint / Ghi chú |
|---|---|:--:|:--:|---|
| DIAG-001 | Chẩn đoán chính + phụ | ✅ | ✅ MAPPED | POST/GET /visits/{id}/diagnosis — primary + secondary |
| DIAG-002 | Khám lâm sàng (free text) | ✅ | ✅ MAPPED | POST/GET /visits/{id}/soap — clinical exam free text |
| DIAG-003 | ICD-10 autocomplete | ✅ | ✅ MAPPED | GET /icd10/search — autocomplete |
| DIAG-004 | ICD-10 catalog (Vietnamese) | ✅ | ✅ MAPPED | GET /icd10/search — ICD-10 catalog (VN) seeded |
| DIAG-005 | Diagnosis history | ✅ | ✅ MAPPED | GET /visits/{id}/diagnosis — diagnosis history |
| DIAG-006 | Lời dặn cuối visit | ✅ | ✅ MAPPED | POST /visits/{id}/complete-emr — end-of-visit instructions |
| DIAG-007 | Lịch tái khám | ✅ | ✅ MAPPED | POST /visits/{id}/complete-emr — follow-up date |
| DIAG-008 | Diagnosis templates | 💡 | ➖ N/A | diagnosis templates — future (💡) |
| DIAG-009 | Voice-to-text input | 💡 | ➖ N/A | voice-to-text — future (💡) |

### SVC — Medical Services

| Code | Chức năng | Fn status | Mapping | Endpoint / Ghi chú |
|---|---|:--:|:--:|---|
| SVC-001 | Service catalog CRUD | ⬜ | ✅ MAPPED | GET/POST/PATCH/DELETE /services — catalog CRUD |
| SVC-002 | Service phân loại | ⬜ | ✅ MAPPED | POST /services — category field |
| SVC-003 | Multi-price (BHYT vs trực tiếp) | ⬜ | ✅ MAPPED | POST /services — multi-price (BHYT vs direct) |
| SVC-004 | Service-doctor mapping | ⬜ | ⚠️ DRIFT | (none) — VERIFIED DRIFT — no service↔doctor capability map (service.py:28); only VisitService.performed_by_user_id records actual performer after-the-fact |
| SVC-005 | Service packages | 💡 | ➖ N/A | service packages — future (💡) |
| SVC-006 | Add service vào visit | ⬜ | ✅ MAPPED | POST /visits/{id}/services — add service to visit |
| SVC-007 | VisitService tracking | ⬜ | ✅ MAPPED | GET /visits/{id}/services, PATCH /visit-services/{id} — VisitService tracking |
| SVC-008 | Service revenue report | ⬜ | ❌ GAP | VERIFIED GAP — revenue_service groups invoice totals by date only; no per-service revenue join (visit_service/service not joined) |
| SVC-009 | Service price history | ✅ | ✅ MAPPED | PATCH /visit-services/{id}/price — price history (audit) |

### RX — Prescriptions

| Code | Chức năng | Fn status | Mapping | Endpoint / Ghi chú |
|---|---|:--:|:--:|---|
| RX-001 | Tạo đơn thuốc | ⬜ | ✅ MAPPED | POST /visits/{id}/prescriptions |
| RX-002 | Auto-gen Rx number | ⬜ | ✅ MAPPED | POST /visits/{id}/prescriptions — auto Rx number |
| RX-003 | Internal vs External | ⬜ | ✅ MAPPED | POST /prescriptions/{id}/items — internal vs external |
| RX-004 | Liều dùng (sáng/trưa/tối) | ⬜ | ✅ MAPPED | POST /prescriptions/{id}/items — dosage (sáng/trưa/tối) |
| RX-005 | Số ngày → auto qty | ⬜ | ✅ MAPPED | POST /prescriptions/{id}/items — days → auto qty |
| RX-006 | Cảnh báo dị ứng | ⬜ | ❌ GAP | VERIFIED GAP — no server-side allergy check; create/add-item (prescription_service.py:281) never reads patient.allergies. Only stock warning returned, unrelated |
| RX-007 | Drug interaction warning | 💡 | ➖ N/A | drug interaction — future (💡) |
| RX-008 | Drug-condition warning | 💡 | ➖ N/A | drug-condition — future (💡) |
| RX-009 | In đơn thuốc | ⬜ | ✅ MAPPED | GET /prescriptions/{id}/print |
| RX-010 | QR code in đơn | 💡 | ➖ N/A | QR on Rx — future (💡) |
| RX-011 | Edit đơn (trước dispense) | ⬜ | ✅ MAPPED | PATCH /prescriptions/{id}, PATCH /prescription-items/{id} — edit before dispense |
| RX-012 | Cancel đơn | ⬜ | ✅ MAPPED | POST /prescriptions/{id}/cancel |
| RX-013 | Lịch sử đơn của BN | ⬜ | ✅ MAPPED | GET /prescriptions/{id} — Rx history (via visits) |
| RX-014 | Đơn template | 💡 | ➖ N/A | Rx template — future (💡) |
| RX-015 | Reserve stock | ⬜ | ✅ MAPPED | POST /pharmacy/reserve — reserve stock on internal Rx |
| RX-016 | Hiển thị stock thuốc khi kê đơn | ⬜ | ✅ MAPPED | GET /medicines/search, GET /medicines/{id}/lots — live stock display |

### MED — Medicine & Inventory

| Code | Chức năng | Fn status | Mapping | Endpoint / Ghi chú |
|---|---|:--:|:--:|---|
| MED-001 | Medicine catalog CRUD | ⬜ | ✅ MAPPED | GET/POST/PATCH/DELETE /medicines — catalog CRUD |
| MED-002 | Phân loại thuốc | ⬜ | ✅ MAPPED | POST /medicines — category field |
| MED-003 | Multi-unit conversion | ⬜ | ✅ MAPPED | POST /medicines — multi-unit conversion |
| MED-004 | Min/max stock alert | ⬜ | ✅ MAPPED | GET /inventory/stock-status — min/max alert |
| MED-005 | Lot/batch tracking | ⬜ | ✅ MAPPED | GET/POST/PATCH/DELETE /inventory/batches — lot/batch tracking |
| MED-006 | Stock movement audit | ⬜ | ✅ MAPPED | POST /inventory/purchase-in, POST /inventory/adjustments — stock movement audit |
| MED-007 | Expiry tracking | ⬜ | ✅ MAPPED | GET /inventory/stock-status, GET /medicines/{id}/lots — expiry tracking |
| MED-008 | FEFO suggestion | ⬜ | ✅ MAPPED | GET /medicines/{id}/lots — FEFO (ORDER BY expiry ASC) — verified |
| MED-009 | Stock import (PO) | ⬜ | ✅ MAPPED | POST /inventory/purchase-in — stock import (PO) |
| MED-010 | Stock adjustment | ⬜ | ✅ MAPPED | POST /inventory/adjustments — stock adjustment |
| MED-011 | Adjustment approval | ⬜ | ❌ GAP | VERIFIED GAP — adjust_stock (adjustment_service.py:46) applies immediately + writes movement; no status pending→approved, no approve endpoint |
| MED-012 | Reorder suggestion | 💡 | ➖ N/A | reorder suggestion — future (💡) |
| MED-013 | Substitute medicine | 💡 | ✅ MAPPED | GET /medicines/{id}/substitutes — by active_ingredient; shipped; fn 💡 |
| MED-014 | Supplier catalog | ⬜ | ✅ MAPPED | GET/POST/PATCH/DELETE /inventory/suppliers — supplier catalog |
| MED-015 | Cost tracking | ⬜ | ✅ MAPPED | POST /inventory/purchase-in — cost tracking (batch.unit_cost) |
| MED-016 | Margin report | ⬜ | ❌ GAP | VERIFIED GAP — no margin/profit report; batch.unit_cost (batch.py:47) exists but never queried by any report |
| MED-017 | Barcode scan | 💡 | ➖ N/A | barcode scan — future (💡) |
| MED-018 | Bulk import CSV catalog | 💡 | ➖ N/A | bulk import — future (💡) |

### PHRM — Pharmacy Dispense

| Code | Chức năng | Fn status | Mapping | Endpoint / Ghi chú |
|---|---|:--:|:--:|---|
| PHRM-001 | Pending dispense queue | ⬜ | ✅ MAPPED | GET /pharmacy/pending-dispense |
| PHRM-002 | Dispense screen | ⬜ | ✅ MAPPED | POST /pharmacy/dispense/{prescription_id} |
| PHRM-003 | Lot selection | ⬜ | ✅ MAPPED | POST /pharmacy/reserve, POST /pharmacy/substitute-batch — FEFO reserve (reservation_service.py:82) + manual override via substitute-batch |
| PHRM-004 | Multi-lot dispense | ⬜ | ✅ MAPPED | POST /pharmacy/reserve→dispense — multi-lot (one PIB per batch) — verified |
| PHRM-005 | Partial dispense | ⬜ | ❌ GAP | VERIFIED GAP — dispense is all-or-nothing (dispense_service.py:70 deducts full reserved qty); no partial-qty input; shortage handled upstream by flipping item to external |
| PHRM-006 | Stock auto-decrement | ⬜ | ✅ MAPPED | POST /pharmacy/dispense/{id} — stock auto-decrement + StockMovement |
| PHRM-007 | Cảnh báo HSD lô | ⬜ | ✅ MAPPED | GET /medicines/{id}/lots — HSD warning data |
| PHRM-008 | Cảnh báo thiếu hàng | ⬜ | ✅ MAPPED | POST /pharmacy/reserve, POST /pharmacy/release/{id} — shortage raises 409 / release returns qty |
| PHRM-009 | Dispense audit | ✅ | ✅ MAPPED | (audit infra) — dispense audit |
| PHRM-010 | In nhãn thuốc | 💡 | ➖ N/A | drug label print — future (💡) |
| PHRM-011 | Auto add to invoice | ⬜ | ✅ MAPPED | POST /visits/{id}/invoices — internal medicine → invoice (create_from_visit pulls Rx rows) |
| PHRM-012 | Reverse dispense | ⬜ | ❌ GAP | VERIFIED GAP — no reverse/void-dispense; release endpoint is for reservations only, not dispensed stock; dispense is one-way |
| PHRM-013 | Substitute confirm | 💡 | ➖ N/A | substitute confirm — future (💡) |

### APPT — Appointments & Queue

| Code | Chức năng | Fn status | Mapping | Endpoint / Ghi chú |
|---|---|:--:|:--:|---|
| APPT-001 | Tạo hẹn | ⬜ | ✅ MAPPED | POST /appointments — create + capacity check + SCHEDULED |
| APPT-002 | Slot capacity per doctor | ⬜ | ⚠️ DRIFT | GET /appointments/slots — VERIFIED DRIFT — capacity is hardcoded stub _STUB_DOCTORS_ON_SHIFT=2 (slot_service.py:18); not per-doctor, not from HR shifts, no hourly cap (TODO TASK-014) |
| APPT-003 | Calendar view | ⬜ | ✅ MAPPED | GET /appointments — list w/ filters (flat, not grid) |
| APPT-004 | Confirm appointment | ⬜ | ✅ MAPPED | POST /appointments/{id}/confirm |
| APPT-005 | Check-in appointment | ⬜ | ✅ MAPPED | POST /appointments/{id}/check-in — atomically creates Visit |
| APPT-006 | Reschedule | ⬜ | ❌ GAP | VERIFIED GAP — PATCH /appointments/{id} cannot change scheduled_at (AppointmentUpdate has no such field); no reschedule capability |
| APPT-007 | Cancel appointment | ⬜ | ✅ MAPPED | POST /appointments/{id}/cancel — mandatory cancel_reason |
| APPT-008 | NO_SHOW tracking | ⬜ | ⚠️ DRIFT | Arq cron auto_no_show_appointments — VERIFIED DRIFT — auto no-show cron exists (every 5min) but grace = 15min (DEFAULT_NO_SHOW_MINUTES), spec says 30min |
| APPT-009 | Smart queue priority | ⬜ | ❌ GAP | VERIFIED GAP — smart_queue.py priority fns exist but unwired (only test imports); no queue/priority API |
| APPT-010 | Walk-in registration | ⬜ | ✅ MAPPED | POST /visits — walk-in implemented in visits module (not appointments) |
| APPT-011 | Queue board (TV mode) | ⬜ | ➖ N/A | queue board TV — FE |
| APPT-012 | Sound chime gọi STT | ⬜ | ➖ N/A | sound chime — FE |
| APPT-013 | Privacy mask name | ⬜ | ➖ N/A | privacy name mask — FE |
| APPT-014 | SMS reminder trước hẹn | 💡 | ➖ N/A | SMS reminder — future (💡) |
| APPT-015 | Patient self-book | 💡 | ➖ N/A | self-book — future (💡) |
| APPT-016 | Block schedule | ⬜ | ❌ GAP | VERIFIED GAP — no block-schedule endpoint/model; operating hours are hardcoded constants (slot_service.py:19) |
| APPT-017 | Conflict với HR shift | ⬜ | ❌ GAP | VERIFIED GAP — create validates slot capacity only; HR shift/leave cross-check is a TODO stub (slot_service.py:28) |

### BILL — Billing & Invoices

| Code | Chức năng | Fn status | Mapping | Endpoint / Ghi chú |
|---|---|:--:|:--:|---|
| BILL-001 | Auto-gen invoice | ⬜ | ✅ MAPPED | POST /visits/{id}/invoices — auto-gen on visit complete |
| BILL-002 | Auto-gen invoice number | ⬜ | ✅ MAPPED | POST /visits/{id}/invoices — auto invoice number |
| BILL-003 | Manual invoice | ⬜ | ⚠️ DRIFT | POST /visits/{id}/invoices — VERIFIED DRIFT — model allows visit_id NULL (invoice.py:33) but NO creation path for standalone/retail invoice; only create_from_visit exists |
| BILL-004 | Add/remove line item | ⬜ | ✅ MAPPED | POST /invoices/{id}/lines, DELETE /invoice-lines/{id} — add/remove line |
| BILL-005 | Multi-payment method | ⬜ | ✅ MAPPED | POST /invoices/{id}/payments — multi-payment (cash/card/transfer/momo/vnpay/other) |
| BILL-006 | Cash payment | ⬜ | ❌ GAP | VERIFIED GAP — cash accepted but NO change-due calc; overpayment rejected (payment_service.py:97); no tendered/change field |
| BILL-007 | Card payment | ⬜ | ✅ MAPPED | POST /invoices/{id}/payments — card (method label + ref) |
| BILL-008 | QR payment | ⬜ | ❌ GAP | VERIFIED GAP — no VietQR generation; vnpay/transfer are plain method labels only |
| BILL-009 | Bank transfer | ⬜ | ✅ MAPPED | POST /invoices/{id}/payments — bank transfer (method label) |
| BILL-010 | BHYT | ⬜ | ❌ GAP | VERIFIED GAP — no BHYT/insurance split on invoice (billing grep 0); bhyt module = VSS integration, separate |
| BILL-011 | Discount % hoặc số tiền | ⬜ | ✅ MAPPED | POST /invoices/{id}/lines — discount line / per-line discount_amount |
| BILL-012 | VAT | ⬜ | ❌ GAP | VERIFIED GAP — tax_total hardcoded 0 (invoice_service.py:84 "Phase 1: no tax"); field exists, no VAT calc |
| BILL-013 | Partial payment | ⬜ | ✅ MAPPED | POST /invoices/{id}/payments — partial payment → partially_paid |
| BILL-014 | Outstanding balance | ⬜ | ✅ MAPPED | GET /invoices, GET /invoices/{id} — balance_due computed |
| BILL-015 | Void invoice | ⬜ | ✅ MAPPED | POST /invoices/{id}/void, POST /payments/{id}/void |
| BILL-016 | Void → reverse stock | ⬜ | ⚠️ DRIFT | POST /invoices/{id}/void — VERIFIED DRIFT — void does NOT reverse stock (invoice_service.py:478 docstring confirms); only refund releases pharmacy reservations |
| BILL-017 | Refund | ⬜ | ✅ MAPPED | POST /invoices/{id}/refund — releases pharmacy stock; only paid invoices refundable |
| BILL-018 | In hóa đơn POS | ⬜ | ⚠️ DRIFT | GET /invoices/{id}/print — VERIFIED DRIFT — single generic HTML payload (max-width:400px); no format param to select 58/80mm |
| BILL-019 | In hóa đơn A4 | ⬜ | ⚠️ DRIFT | GET /invoices/{id}/print — VERIFIED DRIFT — no A4 variant; same single POS-style payload, no format distinction |
| BILL-020 | Email hóa đơn | 💡 | ➖ N/A | email invoice — future (💡) |
| BILL-021 | Loyalty program | 💡 | ➖ N/A | loyalty — future (💡) |
| BILL-022 | Promotion code | 💡 | ➖ N/A | promotion code — future (💡) |
| BILL-023 | E-invoice | 💡 | ➖ N/A | e-invoice — future (💡) |

### HR — Human Resources

| Code | Chức năng | Fn status | Mapping | Endpoint / Ghi chú |
|---|---|:--:|:--:|---|
| HR-001 | User CRUD (clinic) | ⬜ | ✅ MAPPED | GET/POST/PATCH/DELETE /users — clinic user CRUD |
| HR-002 | Temp password gen | ⬜ | ✅ MAPPED | POST /users — temp password on create |
| HR-003 | Magic link invite | ⬜ | ➖ N/A | magic-link invite — future (TASK-027) |
| HR-004 | Reset password (admin) | ⬜ | ❌ GAP | VERIFIED GAP — admin reset staff password: no endpoint (= AUTH-008) |
| HR-005 | Disable/enable user | ⬜ | ✅ MAPPED | PATCH /users/{id} — disable/enable (is_active) |
| HR-006 | License number | ⬜ | ✅ MAPPED | POST/PATCH /users — license number field |
| HR-007 | Specialty per doctor | ⬜ | ✅ MAPPED | POST/PATCH /users — specialty field |
| HR-008 | Shift CRUD | ✅ | ✅ MAPPED | GET/POST/PATCH/DELETE /shifts — shift CRUD |
| HR-009 | Recurring schedule | ✅ | ✅ MAPPED | GET/POST/PATCH/DELETE /recurring-schedules |
| HR-010 | Apply recurring → shifts | ✅ | ✅ MAPPED | POST /recurring-schedules/{id}/generate-shifts |
| HR-011 | Calendar view | ⬜ | ✅ MAPPED | GET /shifts — calendar data |
| HR-012 | Drag to reschedule | 💡 | ➖ N/A | drag-to-reschedule — future (💡) |
| HR-013 | Attendance check-in | ✅ | ✅ MAPPED | POST /attendance/check-in |
| HR-014 | Attendance check-out | ✅ | ✅ MAPPED | POST /attendance/check-out |
| HR-015 | OT calculation | ✅ | ✅ MAPPED | POST /attendance/check-out — OT calc |
| HR-016 | Late/early tracking | ✅ | ✅ MAPPED | POST /attendance/check-in — late/early |
| HR-017 | Leave request | ✅ | ✅ MAPPED | POST /leave-requests |
| HR-018 | Leave approval | ✅ | ✅ MAPPED | POST /leave-requests/{id}/approve, .../reject |
| HR-019 | Leave balance | ✅ | ✅ MAPPED | GET /leave-requests — leave balance |
| HR-020 | Attendance report | ⬜ | ✅ MAPPED | GET /attendance/export, GET /hr/timesheet — attendance report |
| HR-021 | Payroll integration | 💡 | ➖ N/A | payroll — future (💡) |
| HR-022 | Multi-role user | ✅ | ✅ MAPPED | POST /users/{id}/roles — multi-role user |

### RPT — Reports & Analytics

| Code | Chức năng | Fn status | Mapping | Endpoint / Ghi chú |
|---|---|:--:|:--:|---|
| RPT-001 | Doanh thu theo ngày/tuần/tháng | ⬜ | ✅ MAPPED | GET /reports/revenue — by day/week/month (date_trunc) |
| RPT-002 | Doanh thu theo bác sĩ | ⬜ | ✅ MAPPED | GET /reports/doctor-performance — per-doctor revenue/visits |
| RPT-003 | Doanh thu theo phương thức | ⬜ | ❌ GAP | VERIFIED GAP — revenue report has no payment-method dimension |
| RPT-004 | Số visit theo specialty | ⬜ | ⚠️ DRIFT | GET /reports/visit-volume — VERIFIED DRIFT — groups by period+STATUS, not by specialty |
| RPT-005 | Top thuốc dùng | ⬜ | ✅ MAPPED | GET /reports/prescription-breakdown — top-10 medicines (DESC) |
| RPT-006 | Thuốc ít dùng | ⬜ | ❌ GAP | VERIFIED GAP — only top/most-used (ORDER BY DESC); no least-used query |
| RPT-007 | Tồn kho theo giá vốn | ⬜ | ❌ GAP | VERIFIED GAP — inventory-status returns qty only; batch.unit_cost exists but not surfaced; no cost valuation |
| RPT-008 | Thuốc sắp hết hạn | ⬜ | ✅ MAPPED | GET /inventory/stock-status (+ check_near_expiry cron) — expiring medicines |
| RPT-009 | No-show rate | ⬜ | ❌ GAP | no-show rate report — absent |
| RPT-010 | Demographic BN | ⬜ | ❌ GAP | patient demographics report — absent |
| RPT-011 | Visit duration | ⬜ | ❌ GAP | visit duration report — absent (doctor-performance has avg_consultation_minutes only) |
| RPT-012 | Wait time | ⬜ | ❌ GAP | wait-time report — absent |
| RPT-013 | Custom date range | ⬜ | ✅ MAPPED | GET /reports/* — custom date range (start/end query params) |
| RPT-014 | Export CSV | ⬜ | ❌ GAP | report CSV export — all endpoints JSON-only, no format param |
| RPT-015 | Export PDF | ⬜ | ❌ GAP | report PDF export — not built |
| RPT-016 | Scheduled email reports | ⬜ | ➖ N/A | scheduled email reports — future (TASK-027) |
| RPT-017 | Patient retention | 💡 | ➖ N/A | patient retention — future (💡) |
| RPT-018 | Clinical KPIs | 💡 | ➖ N/A | clinical KPIs — future (💡) |

### NOTI — Notifications

| Code | Chức năng | Fn status | Mapping | Endpoint / Ghi chú |
|---|---|:--:|:--:|---|
| NOTI-001 | In-app notification | ⬜ | ✅ MAPPED | GET /notifications, GET /notifications/unread-count — in-app |
| NOTI-002 | Mark as read | ⬜ | ✅ MAPPED | POST /notifications/{id}/read |
| NOTI-003 | Mark all as read | ⬜ | ✅ MAPPED | POST /notifications/mark-all-read |
| NOTI-004 | Notification categories | ⬜ | ✅ MAPPED | GET /notifications — categories via severity field (info/warning/critical/success); no separate "category" field |
| NOTI-005 | Visit completion notify | ⬜ | ❌ GAP | VERIFIED GAP — no notification created on visit complete (visit_service.py:348 sets AWAITING_PAYMENT, no create_notification); VISIT_QUEUE_ALERT enum defined but never emitted |
| NOTI-006 | Stock low alert | ⬜ | ⚠️ DRIFT | Arq cron check_low_stock — VERIFIED DRIFT — stock-low only via hourly cron broadcast (user_id=None, not pharmacist-targeted); no event-driven trigger on threshold |
| NOTI-007 | Subscription expiring | ⬜ | ❌ GAP | subscription-expiring notify — SUB not built |
| NOTI-008 | Email transactional | ⬜ | ❌ GAP | transactional email — INT-001 not built |
| NOTI-009 | Email templates | ⬜ | ❌ GAP | email templates — not built |
| NOTI-010 | SMS notifications | 💡 | ➖ N/A | SMS — future (💡) |
| NOTI-011 | Zalo OA push | 💡 | ➖ N/A | Zalo OA — future (💡) |
| NOTI-012 | Push notification (web) | 💡 | ➖ N/A | web push — future (💡) |
| NOTI-013 | Tauri desktop notification | ✅ | ➖ N/A | Tauri desktop notification — FE |
| NOTI-014 | User preference | 💡 | ✅ MAPPED | POST /notifications/{id}/dismiss — dismiss (soft via dismissed_at) |
| NOTI-015 | Reminder schedule cron | ⬜ | ➖ N/A | reminder cron — appointment_reminder Arq cron BUILT (every 30min); background, not REST |

### AUDIT — Audit & Compliance

| Code | Chức năng | Fn status | Mapping | Endpoint / Ghi chú |
|---|---|:--:|:--:|---|
| AUDIT-001 | Audit mọi INSERT/UPDATE/DELETE | ✅ | ✅ MAPPED | GET /admin/audit-logs — auto capture (infra) + viewer |
| AUDIT-002 | PII redaction | ✅ | ✅ MAPPED | (audit infra) — PII redaction |
| AUDIT-003 | __auditable__ flag | ✅ | ✅ MAPPED | (audit infra) — __auditable__ flag |
| AUDIT-004 | __audit_exclude__ | ✅ | ✅ MAPPED | (audit infra) — __audit_exclude__ |
| AUDIT-005 | RLS row-level security | ✅ | ✅ MAPPED | (tenancy/RLS infra) — row-level security |
| AUDIT-006 | Tenancy middleware | ✅ | ✅ MAPPED | (tenancy middleware) — app.current_clinic_id |
| AUDIT-007 | Audit patient.read | ✅ | ✅ MAPPED | GET /patients/{id} — audit patient.read |
| AUDIT-008 | Audit log viewer (clinic) | ⬜ | ✅ MAPPED | GET /admin/audit-logs — clinic audit viewer |
| AUDIT-009 | Audit log viewer (super admin) | ⬜ | ✅ MAPPED | GET /superadmin/audit-logs — super-admin cross-clinic viewer |
| AUDIT-010 | Data export (PDPA) | ⬜ | ❌ GAP | PDPA data export — DATA-004/007 not built |
| AUDIT-011 | ToS + Privacy versioning | ⬜ | ❌ GAP | ToS/Privacy versioning — not built |
| AUDIT-012 | Consent tracking | 💡 | ➖ N/A | consent tracking — future (💡) |
| AUDIT-013 | Right to be forgotten | 💡 | ✅ MAPPED | POST /patients/{id}/erase/request, DELETE /patients/{id}/erase — right-to-be-forgotten shipped (TASK-038); fn 💡 |
| AUDIT-014 | DPA template | ⬜ | ➖ N/A | DPA template — document (TASK-029) |
| AUDIT-015 | Cookie consent banner | ⬜ | ➖ N/A | cookie consent banner — FE/landing |

### CFG — Clinic Configuration

| Code | Chức năng | Fn status | Mapping | Endpoint / Ghi chú |
|---|---|:--:|:--:|---|
| CFG-001 | Clinic info | ⬜ | ✅ MAPPED | PATCH /admin/clinics/{id}, POST /onboarding/info — clinic info on Clinic row (name/address/phone/email/tax_code) |
| CFG-002 | Logo upload | ⬜ | ❌ GAP | VERIFIED GAP — no logo/logo_url field or upload endpoint (grep 0) |
| CFG-003 | Working hours | ⬜ | ✅ MAPPED | PATCH /clinics/me/settings — working hours (per-weekday open/close) |
| CFG-004 | Holiday list | ⬜ | ❌ GAP | VERIFIED GAP — no holiday field or auto-import (grep 0) |
| CFG-005 | Lunch break | ⬜ | ❌ GAP | VERIFIED GAP — operating-hours model (DayHours) has no lunch/break window |
| CFG-006 | Invoice prefix | ⬜ | ✅ MAPPED | PATCH /clinics/me/settings — invoice_prefix (BillingSettings) |
| CFG-007 | Patient code prefix | ⬜ | ❌ GAP | VERIFIED GAP — no patient_prefix in settings |
| CFG-008 | Visit number prefix | ⬜ | ❌ GAP | VERIFIED GAP — no visit_prefix in settings |
| CFG-009 | VAT rate | ⬜ | ✅ MAPPED | PATCH /clinics/me/settings — VAT (tax_rate_percent) |
| CFG-010 | Currency | ✅ | ✅ MAPPED | PATCH /clinics/me/settings — currency (BillingSettings.currency=VND) |
| CFG-011 | Timezone | ✅ | ⚠️ DRIFT | (system default) — VERIFIED DRIFT — system default Asia/Ho_Chi_Minh only; no per-clinic timezone settings field |
| CFG-012 | Default language | ✅ | ⚠️ DRIFT | (system default) — VERIFIED DRIFT — system default vi/en only; no per-clinic default_language settings field |
| CFG-013 | Vital schema editor | ⬜ | ✅ MAPPED | POST/PATCH /vitals/definitions — vital schema editor |
| CFG-014 | Service category management | ⬜ | ✅ MAPPED | POST/PATCH /services — service category mgmt |
| CFG-015 | Discount policy | 💡 | ➖ N/A | discount policy — future (💡) |
| CFG-016 | Medicine warning rules | 💡 | ➖ N/A | medicine warning rules — future (💡) |
| CFG-017 | Toggle BHYT bật/tắt | ⬜ | ✅ MAPPED | GET/PATCH /settings/bhyt — BHYT feature toggle |

### PLT — Platform Admin (Super Admin)

| Code | Chức năng | Fn status | Mapping | Endpoint / Ghi chú |
|---|---|:--:|:--:|---|
| PLT-001 | Platform user CRUD | ⬜ | ✅ MAPPED | GET/POST/PATCH /superadmin/accounts — platform user CRUD (no hard delete) |
| PLT-002 | Platform role CRUD | ⬜ | ⚠️ DRIFT | GET /superadmin/roles — VERIFIED DRIFT — read-only list; no create/update/delete platform role |
| PLT-003 | Clinic list + filter | ⬜ | ✅ MAPPED | GET /superadmin/clinics — clinic list + filter |
| PLT-004 | Clinic detail panel | ⬜ | ❌ GAP | VERIFIED GAP — no GET /superadmin/clinics/{id} detail endpoint; only list |
| PLT-005 | Tạo clinic + admin | ⬜ | ✅ MAPPED | POST /superadmin/clinics — create clinic + DEK |
| PLT-006 | Convert trial → paid | ⬜ | ❌ GAP | convert trial→paid — subscription not built |
| PLT-007 | Renew subscription | ⬜ | ❌ GAP | renew subscription — not built |
| PLT-008 | Suspend clinic | ⬜ | ⚠️ DRIFT | PATCH /superadmin/clinics/{id} — suspend = is_active=false only (no status machine) |
| PLT-009 | Reactivate clinic | ⬜ | ⚠️ DRIFT | PATCH /superadmin/clinics/{id} — reactivate = is_active=true only |
| PLT-010 | Archive clinic | ⬜ | ❌ GAP | VERIFIED GAP — no archive action (cannot set is_deleted via PATCH) |
| PLT-011 | Reset clinic admin password | ⬜ | ✅ MAPPED | POST /superadmin/accounts/{id}/reset-password |
| PLT-012 | Lead management | ⬜ | ❌ GAP | lead management — no lead entity/endpoint |
| PLT-013 | Convert lead → clinic | ⬜ | ❌ GAP | convert lead→clinic — not built |
| PLT-014 | Platform metrics dashboard | ⬜ | ⚠️ DRIFT | GET /superadmin/stats — metrics partial — counts only, no MRR/ARR/churn |
| PLT-015 | Subscription expiring view | ⬜ | ❌ GAP | subscription-expiring view — not built |
| PLT-016 | Cross-clinic audit log | ⬜ | ✅ MAPPED | GET /superadmin/audit-logs — cross-clinic forensic |
| PLT-017 | System config | ⬜ | ❌ GAP | system config (rate limits/flags/JWT rotation) — no superadmin endpoint |
| PLT-018 | Feature flag UI | ⬜ | ⚠️ DRIFT | PATCH /superadmin/clinics/{id} — feature-flag primitive exists ({flag}_enabled, only bhyt) but SuperClinicUpdate does NOT expose it; no global flag UI |
| PLT-019 | PHI access prohibited | ⬜ | ✅ MAPPED | (RLS + no-PHI superadmin) — PHI-access-prohibited — infra |
| PLT-020 | Impersonate clinic | 💡 | ➖ N/A | impersonate — future (💡) |
| PLT-021 | Data export per clinic | ⬜ | ❌ GAP | data export per clinic — no endpoint |
| PLT-022 | Internal notes | ⬜ | ❌ GAP | internal notes — no entity/endpoint |
| PLT-023 | Activity feed platform-wide | ⬜ | ❌ GAP | VERIFIED GAP — no activity-feed endpoint (audit-logs is distinct) |
| PLT-024 | Email super admin team | ⬜ | ❌ GAP | email super-admin team — INT-001 not built |

### JOB — Background Jobs (Arq)

| Code | Chức năng | Fn status | Mapping | Endpoint / Ghi chú |
|---|---|:--:|:--:|---|
| JOB-001 | Subscription expiration check | ⬜ | ➖ N/A | subscription expiration check — NOT BUILT (no subscription module) |
| JOB-002 | Grace transition | ⬜ | ➖ N/A | grace transition — NOT BUILT |
| JOB-003 | Expired transition | ⬜ | ➖ N/A | expired transition — NOT BUILT |
| JOB-004 | Reminder dispatch | ⬜ | ➖ N/A | subscription reminder dispatch — NOT BUILT (appointment_reminder cron is for appointments, not subscription) |
| JOB-005 | Hard delete archived | ⬜ | ➖ N/A | hard-delete archived — NOT BUILT (pii_archive only soft-deletes) |
| JOB-006 | Recurring shift generation | ✅ | ✅ MAPPED | POST /recurring-schedules/{id}/generate-shifts — Arq cron generate_recurring_shifts (01:00) BUILT + on-demand endpoint |
| JOB-007 | Stock alert generation | ⬜ | ➖ N/A | stock alert — BUILT (check_low_stock cron, hourly) |
| JOB-008 | Expiry alert generation | ⬜ | ➖ N/A | expiry alert — BUILT (check_near_expiry cron, 08:00) |
| JOB-009 | NO_SHOW marker | ⬜ | ➖ N/A | no-show marker — BUILT (auto_no_show_appointments, every 5min) |
| JOB-010 | Refresh permission cache | ✅ | ➖ N/A | permission cache refresh — NOT BUILT as cron (invalidate-on-write only) |
| JOB-011 | Daily backup | ⬜ | ➖ N/A | daily backup — NOT BUILT |
| JOB-012 | Weekly report email | 💡 | ➖ N/A | weekly report email — future (💡) |
| JOB-013 | Patient birthday SMS | 💡 | ➖ N/A | birthday SMS — future (💡) |
| JOB-014 | Audit log retention | 💡 | ➖ N/A | audit log retention — future (💡) |

### DATA — Import / Export / Backup

| Code | Chức năng | Fn status | Mapping | Endpoint / Ghi chú |
|---|---|:--:|:--:|---|
| DATA-001 | Patient import CSV | 💡 | ➖ N/A | patient import CSV — future (💡) |
| DATA-002 | Medicine catalog import CSV | 💡 | ➖ N/A | medicine import CSV — future (💡) |
| DATA-003 | Service catalog import | 💡 | ➖ N/A | service import CSV — future (💡) |
| DATA-004 | Patient export | ⬜ | ❌ GAP | patient export — no endpoint |
| DATA-005 | Visit export | ⬜ | ❌ GAP | visit export — no endpoint |
| DATA-006 | Invoice export | ⬜ | ❌ GAP | invoice export — no endpoint |
| DATA-007 | Full clinic export | ⬜ | ❌ GAP | full clinic export — no endpoint |
| DATA-008 | Daily DB backup | ⬜ | ➖ N/A | daily DB backup — NOT BUILT (Arq/ops job absent) |
| DATA-009 | Point-in-time recovery | 💡 | ➖ N/A | PITR — future (💡) |
| DATA-010 | Tauri offline SQLite mirror | ✅ | ➖ N/A | Tauri offline SQLite mirror — FE |
| DATA-011 | Sync conflict resolution | ✅ | ➖ N/A | sync conflict resolution — FE |

### INT — Integrations

| Code | Chức năng | Fn status | Mapping | Endpoint / Ghi chú |
|---|---|:--:|:--:|---|
| INT-001 | Email provider | ⬜ | ❌ GAP | email provider (SES/SendGrid) — not wired |
| INT-002 | SMS provider | 💡 | ➖ N/A | SMS provider — future (💡) |
| INT-003 | VietQR generator | ⬜ | ❌ GAP | VietQR — no QR generation (see BILL-008) |
| INT-004 | VNPay webhook | 💡 | ➖ N/A | VNPay webhook — future (💡) |
| INT-005 | MoMo webhook | 💡 | ➖ N/A | MoMo webhook — future (💡) |
| INT-006 | E-invoice (VNPT/Viettel) | 💡 | ➖ N/A | e-invoice VNPT/Viettel — future (💡) |
| INT-007 | reCAPTCHA | ⬜ | ➖ N/A | reCAPTCHA — FE/landing |
| INT-008 | Google Analytics (landing) | ⬜ | ➖ N/A | Google Analytics — landing FE |
| INT-009 | Sentry error tracking | ⬜ | ➖ N/A | Sentry — infra/ops |
| INT-010 | S3-compatible storage | ⬜ | ❌ GAP | S3 storage — not wired (blocks PAT-019/VIS-014/CFG-002) |
| INT-011 | Zalo OA Push | 💡 | ➖ N/A | Zalo OA — future (💡) |
| INT-012 | ICD-10 master data | ✅ | ✅ MAPPED | GET /icd10/search — ICD-10 master data (seeded) |
| INT-013 | VN address API | ⬜ | ❌ GAP | VN address API — not wired |
| INT-014 | Drug master data | 💡 | ➖ N/A | drug master data — future (💡) |
| INT-015 | Lab system integration | 💡 | ➖ N/A | lab integration — future (💡) |
| INT-016 | Imaging system (PACS) | 💡 | ➖ N/A | PACS — future (💡) |
| INT-017 | National Health Insurance API | 💡 | ➖ N/A | national health insurance API — future (💡) |
| INT-018 | POS printer driver | ⬜ | ➖ N/A | POS printer — Tauri FE |
| INT-019 | Barcode scanner (Tauri) | ✅ | ➖ N/A | barcode scanner — Tauri FE |
| INT-020 | Card reader (Tauri) | 💡 | ➖ N/A | card reader — future (💡) |

### I18N — Localization

| Code | Chức năng | Fn status | Mapping | Endpoint / Ghi chú |
|---|---|:--:|:--:|---|
| I18N-001 | Vietnamese (default) | ✅ | ➖ N/A | Frontend i18n (i18next) — no backend endpoint |
| I18N-002 | English | ✅ | ➖ N/A | Frontend i18n (i18next) — no backend endpoint |
| I18N-003 | Date format VN/EN | ✅ | ➖ N/A | Frontend i18n (i18next) — no backend endpoint |
| I18N-004 | Number format | ✅ | ➖ N/A | Frontend i18n (i18next) — no backend endpoint |
| I18N-005 | Currency format | ✅ | ➖ N/A | Frontend i18n (i18next) — no backend endpoint |
| I18N-006 | Time format | ✅ | ➖ N/A | Frontend i18n (i18next) — no backend endpoint |
| I18N-007 | Language switcher | ✅ | ➖ N/A | Frontend i18n (i18next) — no backend endpoint |

### A11Y — Accessibility

| Code | Chức năng | Fn status | Mapping | Endpoint / Ghi chú |
|---|---|:--:|:--:|---|
| A11Y-001 | ARIA labels | ✅ | ➖ N/A | Frontend accessibility — no backend endpoint |
| A11Y-002 | Keyboard navigation | ✅ | ➖ N/A | Frontend accessibility — no backend endpoint |
| A11Y-003 | Focus rings | ✅ | ➖ N/A | Frontend accessibility — no backend endpoint |
| A11Y-004 | WCAG AA contrast | ✅ | ➖ N/A | Frontend accessibility — no backend endpoint |
| A11Y-005 | Screen reader support | ✅ | ➖ N/A | Frontend accessibility — no backend endpoint |
| A11Y-006 | High contrast mode | 💡 | ➖ N/A | Frontend accessibility — no backend endpoint |
| A11Y-007 | Font size adjuster | 💡 | ➖ N/A | Frontend accessibility — no backend endpoint |

### THEME — Theming

| Code | Chức năng | Fn status | Mapping | Endpoint / Ghi chú |
|---|---|:--:|:--:|---|
| THEME-001 | Light mode | ✅ | ➖ N/A | Frontend theming — no backend endpoint |
| THEME-002 | Dark mode | ✅ | ➖ N/A | Frontend theming — no backend endpoint |
| THEME-003 | System theme detection | ✅ | ➖ N/A | Frontend theming — no backend endpoint |

### NAV — Navigation & Search

| Code | Chức năng | Fn status | Mapping | Endpoint / Ghi chú |
|---|---|:--:|:--:|---|
| NAV-001 | Global command palette (Ctrl+K / ⌘K) | ⬜ | ✅ MAPPED | GET /search — global command palette backend |
| NAV-002 | Clinic switcher dropdown (topbar) | ⬜ | ✅ MAPPED | GET /auth/clinics, POST /auth/select-clinic — clinic switcher (data) |
| NAV-003 | Quick search bệnh nhân | ⬜ | ✅ MAPPED | GET /patients/search, GET /search — quick patient search |
| NAV-004 | Quick search thuốc | ⬜ | ✅ MAPPED | GET /medicines/search, GET /search — quick medicine search |
| NAV-005 | Quick search feature/màn | ⬜ | ➖ N/A | feature/route search — FE client-side |
| NAV-006 | Recent items pin | 💡 | ➖ N/A | recent items pin — future (💡) |
| NAV-007 | Keyboard shortcuts cheatsheet | ⬜ | ➖ N/A | shortcuts cheatsheet — FE |
| NAV-008 | Breadcrumb navigation (topbar) | ✅ | ➖ N/A | breadcrumb — FE |

### NFR — Non-functional Requirements

| Code | Chức năng | Fn status | Mapping | Endpoint / Ghi chú |
|---|---|:--:|:--:|---|
| NFR-001 | API response time | 🔄 | ➖ N/A | Non-functional / cross-cutting infra — no dedicated endpoint |
| NFR-002 | Page load time | 🔄 | ➖ N/A | Non-functional / cross-cutting infra — no dedicated endpoint |
| NFR-003 | Concurrent users | ⬜ | ➖ N/A | Non-functional / cross-cutting infra — no dedicated endpoint |
| NFR-004 | Uptime SLA | ⬜ | ➖ N/A | Non-functional / cross-cutting infra — no dedicated endpoint |
| NFR-005 | Encryption in-transit | ✅ | ➖ N/A | Non-functional / cross-cutting infra — no dedicated endpoint |
| NFR-006 | Encryption at-rest | 🔄 | ➖ N/A | Non-functional / cross-cutting infra — no dedicated endpoint |
| NFR-007 | Multi-tenant isolation (RLS) | ✅ | ➖ N/A | Non-functional / cross-cutting infra — no dedicated endpoint |
| NFR-008 | OWASP Top 10 protection | 🔄 | ➖ N/A | Non-functional / cross-cutting infra — no dedicated endpoint |
| NFR-009 | Audit log immutable | ✅ | ➖ N/A | Non-functional / cross-cutting infra — no dedicated endpoint |
| NFR-010 | Data retention BN | ⬜ | ➖ N/A | Non-functional / cross-cutting infra — no dedicated endpoint |
| NFR-011 | Backup & DR | ⬜ | ➖ N/A | Non-functional / cross-cutting infra — no dedicated endpoint |
| NFR-012 | Accessibility WCAG 2.1 AA | ✅ | ➖ N/A | Non-functional / cross-cutting infra — no dedicated endpoint |
| NFR-013 | Browser support | ✅ | ➖ N/A | Non-functional / cross-cutting infra — no dedicated endpoint |
| NFR-014 | OS support (Tauri) | ✅ | ➖ N/A | Non-functional / cross-cutting infra — no dedicated endpoint |
| NFR-015 | Responsive (web fallback) | ⬜ | ➖ N/A | Non-functional / cross-cutting infra — no dedicated endpoint |
| NFR-016 | Localization vi/en | ✅ | ➖ N/A | Non-functional / cross-cutting infra — no dedicated endpoint |
| NFR-017 | Code coverage | 🔄 | ➖ N/A | Non-functional / cross-cutting infra — no dedicated endpoint |
| NFR-018 | Observability | 🔄 | ➖ N/A | Non-functional / cross-cutting infra — no dedicated endpoint |
| NFR-019 | Search performance | ✅ | ✅ MAPPED | GET /patients/search — search performance — indexes |
| NFR-020 | Offline capability (Tauri) | 🔄 | ➖ N/A | Non-functional / cross-cutting infra — no dedicated endpoint |
| NFR-021 | Compliance HIPAA + Nghị định 13/2023 | 🔄 | ➖ N/A | Non-functional / cross-cutting infra — no dedicated endpoint |
| NFR-022 | Rate limiting | ✅ | ✅ MAPPED | (slowapi middleware) — rate limiting |
| NFR-023 | Data classification 4-tier | ⬜ | ➖ N/A | Non-functional / cross-cutting infra — no dedicated endpoint |
| NFR-024 | Column-level encryption T3 | ⬜ | ➖ N/A | Non-functional / cross-cutting infra — no dedicated endpoint |
| NFR-025 | Per-tenant encryption keys | ⬜ | ➖ N/A | Non-functional / cross-cutting infra — no dedicated endpoint |
| NFR-026 | Key rotation policy | 🔄 | ➖ N/A | Non-functional / cross-cutting infra — no dedicated endpoint |
| NFR-027 | Bcrypt cost ≥12 | 🔄 | ➖ N/A | Non-functional / cross-cutting infra — no dedicated endpoint |
| NFR-028 | JWT RS256 + key rotation | ⬜ | ➖ N/A | Non-functional / cross-cutting infra — no dedicated endpoint |
| NFR-029 | Session fingerprinting | ⬜ | ✅ MAPPED | GET /auth/fingerprints — session fingerprinting (TASK-038) |
| NFR-030 | PII redaction trong log | 🔄 | ➖ N/A | Non-functional / cross-cutting infra — no dedicated endpoint |
| NFR-031 | Data minimization | ⬜ | ➖ N/A | Non-functional / cross-cutting infra — no dedicated endpoint |
| NFR-032 | Right to Erasure (Nghị định 13) | ⬜ | ✅ MAPPED | POST /patients/{id}/erase/request, DELETE /patients/{id}/erase — right to erasure (TASK-038) |
| NFR-033 | Data portability | ⬜ | ➖ N/A | Non-functional / cross-cutting infra — no dedicated endpoint |
| NFR-034 | WAF (Web Application Firewall) | ⬜ | ➖ N/A | Non-functional / cross-cutting infra — no dedicated endpoint |
| NFR-035 | DDoS protection | ⬜ | ➖ N/A | Non-functional / cross-cutting infra — no dedicated endpoint |
| NFR-036 | mTLS internal service-to-service | ⬜ | ➖ N/A | Non-functional / cross-cutting infra — no dedicated endpoint |
| NFR-037 | SAST static analysis | 🔄 | ➖ N/A | Non-functional / cross-cutting infra — no dedicated endpoint |
| NFR-038 | DAST dynamic analysis | ⬜ | ➖ N/A | Non-functional / cross-cutting infra — no dedicated endpoint |
| NFR-039 | Dependency scanning | 🔄 | ➖ N/A | Non-functional / cross-cutting infra — no dedicated endpoint |
| NFR-040 | Secret management | 🔄 | ➖ N/A | Non-functional / cross-cutting infra — no dedicated endpoint |
| NFR-041 | Backup encryption + ACL | ⬜ | ➖ N/A | Non-functional / cross-cutting infra — no dedicated endpoint |
| NFR-042 | Anomaly detection audit log | ⬜ | ➖ N/A | anomaly detection — BUILT (anomaly_detection_run cron, every 15min) |
| NFR-043 | Breach notification ≤72h | ⬜ | ➖ N/A | Non-functional / cross-cutting infra — no dedicated endpoint |
| NFR-044 | Forensic logging + hash chain | ⬜ | ✅ MAPPED | POST /admin/audit/verify-chain — forensic hash-chain (TASK-037); audit_chain_verify cron also built |
| NFR-045 | Tauri code signing + secure storage | 🔄 | ➖ N/A | Non-functional / cross-cutting infra — no dedicated endpoint |
| NFR-046 | Pen test annual | ⬜ | ➖ N/A | Non-functional / cross-cutting infra — no dedicated endpoint |

## Báo cáo GAP (chức năng thiếu API — backlog, KHÔNG build trong TASK-052)

| Code | Chức năng | Ghi chú (verified) |
|---|---|---|
| AUTH-008 | Reset password (admin gen) | VERIFIED GAP — no clinic-admin staff-password reset (users/api/routes.py only POST /users create; only platform superadmin reset-password) |
| AUTH-009 | Forgot password (self-service) | forgot-password self-service — not built (TASK-027) |
| TENT-001 | Self-signup form | public self-signup form — no public endpoint |
| TENT-002 | Email verification | email verification — not built |
| TENT-007 | Cấu hình prefix code | VERIFIED GAP — only invoice_prefix configurable (settings_schemas.py:96); patient/visit prefix absent; no prefix step in onboarding wizard |
| TENT-008 | Lead form (Liên hệ tư vấn) | lead form — not built (TASK-026) |
| TENT-010 | Convert lead → clinic | convert lead→clinic — not built |
| TENT-011 | Email verify token TTL 24h | email-verify token TTL — not built |
| TENT-012 | Invite resend | invite resend — not built |
| SUB-001 | Subscription type | VERIFIED GAP — no subscription model/table/service anywhere in app/ (grep 0) |
| SUB-002 | Billing cycle | billing cycle — no subscription module |
| SUB-003 | Trial 14 ngày default | trial 14d — no subscription module |
| SUB-004 | Grace period | grace period — no subscription module |
| SUB-005 | Subscription state machine | subscription state machine — no subscription module |
| SUB-006 | SubscriptionGuard middleware | VERIFIED GAP — no SubscriptionGuard middleware (grep 0); only require_feature/require_superuser exist |
| SUB-007 | Behavior matrix per status | behavior matrix — not built |
| SUB-008 | Read-only mode khi expired | read-only-when-expired — not built |
| SUB-009 | Banner cảnh báo trial/grace | trial/grace banner — needs subscription data (not built) |
| SUB-010 | Subscription event audit | subscription event audit — not built |
| SUB-011 | Renewal manual (super admin) | manual renewal — not built |
| SUB-012 | Convert trial → paid | convert trial→paid — not built |
| SUB-013 | Upgrade plan | upgrade plan — not built |
| SUB-016 | Archive clinic | VERIFIED GAP — no archive action; is_deleted exists on model but SuperClinicUpdate cannot set it; no archive endpoint |
| SUB-017 | Auto export trước hard delete | auto export before hard delete — not built |
| SUB-018 | Hard delete sau 90d | hard delete after 90d — not built |
| SUB-019 | Reminder D-14/-7/-3/-1/0 | reminder D-14..0 — not built |
| SUB-020 | Daily reminder trong grace | daily grace reminder — not built |
| PAT-019 | Đính kèm tài liệu | attach documents — S3 (INT-010) not wired |
| VIS-014 | Tài liệu đính kèm visit | attach documents — storage not wired |
| VTL-006 | Vital trends chart | vital trends chart — cross-visit aggregation endpoint missing (only per-visit GET) |
| SVC-008 | Service revenue report | VERIFIED GAP — revenue_service groups invoice totals by date only; no per-service revenue join (visit_service/service not joined) |
| RX-006 | Cảnh báo dị ứng | VERIFIED GAP — no server-side allergy check; create/add-item (prescription_service.py:281) never reads patient.allergies. Only stock warning returned, unrelated |
| MED-011 | Adjustment approval | VERIFIED GAP — adjust_stock (adjustment_service.py:46) applies immediately + writes movement; no status pending→approved, no approve endpoint |
| MED-016 | Margin report | VERIFIED GAP — no margin/profit report; batch.unit_cost (batch.py:47) exists but never queried by any report |
| PHRM-005 | Partial dispense | VERIFIED GAP — dispense is all-or-nothing (dispense_service.py:70 deducts full reserved qty); no partial-qty input; shortage handled upstream by flipping item to external |
| PHRM-012 | Reverse dispense | VERIFIED GAP — no reverse/void-dispense; release endpoint is for reservations only, not dispensed stock; dispense is one-way |
| APPT-006 | Reschedule | VERIFIED GAP — PATCH /appointments/{id} cannot change scheduled_at (AppointmentUpdate has no such field); no reschedule capability |
| APPT-009 | Smart queue priority | VERIFIED GAP — smart_queue.py priority fns exist but unwired (only test imports); no queue/priority API |
| APPT-016 | Block schedule | VERIFIED GAP — no block-schedule endpoint/model; operating hours are hardcoded constants (slot_service.py:19) |
| APPT-017 | Conflict với HR shift | VERIFIED GAP — create validates slot capacity only; HR shift/leave cross-check is a TODO stub (slot_service.py:28) |
| BILL-006 | Cash payment | VERIFIED GAP — cash accepted but NO change-due calc; overpayment rejected (payment_service.py:97); no tendered/change field |
| BILL-008 | QR payment | VERIFIED GAP — no VietQR generation; vnpay/transfer are plain method labels only |
| BILL-010 | BHYT | VERIFIED GAP — no BHYT/insurance split on invoice (billing grep 0); bhyt module = VSS integration, separate |
| BILL-012 | VAT | VERIFIED GAP — tax_total hardcoded 0 (invoice_service.py:84 "Phase 1: no tax"); field exists, no VAT calc |
| HR-004 | Reset password (admin) | VERIFIED GAP — admin reset staff password: no endpoint (= AUTH-008) |
| RPT-003 | Doanh thu theo phương thức | VERIFIED GAP — revenue report has no payment-method dimension |
| RPT-006 | Thuốc ít dùng | VERIFIED GAP — only top/most-used (ORDER BY DESC); no least-used query |
| RPT-007 | Tồn kho theo giá vốn | VERIFIED GAP — inventory-status returns qty only; batch.unit_cost exists but not surfaced; no cost valuation |
| RPT-009 | No-show rate | no-show rate report — absent |
| RPT-010 | Demographic BN | patient demographics report — absent |
| RPT-011 | Visit duration | visit duration report — absent (doctor-performance has avg_consultation_minutes only) |
| RPT-012 | Wait time | wait-time report — absent |
| RPT-014 | Export CSV | report CSV export — all endpoints JSON-only, no format param |
| RPT-015 | Export PDF | report PDF export — not built |
| NOTI-005 | Visit completion notify | VERIFIED GAP — no notification created on visit complete (visit_service.py:348 sets AWAITING_PAYMENT, no create_notification); VISIT_QUEUE_ALERT enum defined but never emitted |
| NOTI-007 | Subscription expiring | subscription-expiring notify — SUB not built |
| NOTI-008 | Email transactional | transactional email — INT-001 not built |
| NOTI-009 | Email templates | email templates — not built |
| AUDIT-010 | Data export (PDPA) | PDPA data export — DATA-004/007 not built |
| AUDIT-011 | ToS + Privacy versioning | ToS/Privacy versioning — not built |
| CFG-002 | Logo upload | VERIFIED GAP — no logo/logo_url field or upload endpoint (grep 0) |
| CFG-004 | Holiday list | VERIFIED GAP — no holiday field or auto-import (grep 0) |
| CFG-005 | Lunch break | VERIFIED GAP — operating-hours model (DayHours) has no lunch/break window |
| CFG-007 | Patient code prefix | VERIFIED GAP — no patient_prefix in settings |
| CFG-008 | Visit number prefix | VERIFIED GAP — no visit_prefix in settings |
| PLT-004 | Clinic detail panel | VERIFIED GAP — no GET /superadmin/clinics/{id} detail endpoint; only list |
| PLT-006 | Convert trial → paid | convert trial→paid — subscription not built |
| PLT-007 | Renew subscription | renew subscription — not built |
| PLT-010 | Archive clinic | VERIFIED GAP — no archive action (cannot set is_deleted via PATCH) |
| PLT-012 | Lead management | lead management — no lead entity/endpoint |
| PLT-013 | Convert lead → clinic | convert lead→clinic — not built |
| PLT-015 | Subscription expiring view | subscription-expiring view — not built |
| PLT-017 | System config | system config (rate limits/flags/JWT rotation) — no superadmin endpoint |
| PLT-021 | Data export per clinic | data export per clinic — no endpoint |
| PLT-022 | Internal notes | internal notes — no entity/endpoint |
| PLT-023 | Activity feed platform-wide | VERIFIED GAP — no activity-feed endpoint (audit-logs is distinct) |
| PLT-024 | Email super admin team | email super-admin team — INT-001 not built |
| DATA-004 | Patient export | patient export — no endpoint |
| DATA-005 | Visit export | visit export — no endpoint |
| DATA-006 | Invoice export | invoice export — no endpoint |
| DATA-007 | Full clinic export | full clinic export — no endpoint |
| INT-001 | Email provider | email provider (SES/SendGrid) — not wired |
| INT-003 | VietQR generator | VietQR — no QR generation (see BILL-008) |
| INT-010 | S3-compatible storage | S3 storage — not wired (blocks PAT-019/VIS-014/CFG-002) |
| INT-013 | VN address API | VN address API — not wired |

## Báo cáo DRIFT (có API/code nhưng lệch — cần bổ sung)

| Code | Chức năng | Endpoint | Lý do (verified) |
|---|---|---|---|
| RBAC-008 | Clone system role | POST /roles | VERIFIED DRIFT — POST /roles creates BLANK role; real clone_system_role() (rbac_service.py:527) copies perms but is NOT wired to any route (onboarding-only/dead). Clone via API unreachable |
| RBAC-016 | Separation of Duties (SoD) | POST /invoices/{id}/payments, POST /pharmacy/dispense/{id} | VERIFIED DRIFT — SoD enforced at exactly 2 sites (sod.py:108 check_no_self_approval @ pharmacy routes.py:129 + billing payment_service.py:88); make_sod_dep factory wired to 0 routes; Rx-approve & price self-approve NOT gated |
| TENT-003 | Tạo clinic + admin user | POST /admin/clinics | VERIFIED DRIFT — clinic_service.create_clinic (clinic_service.py:26-94) creates Clinic+Settings+OnboardingState only; admin user NOT provisioned in same flow (separate /onboarding/users). Not atomic clinic+admin |
| TENT-004 | Clone system roles cho clinic mới | (unwired) | VERIFIED DRIFT — clone_system_role() (rbac_service.py:527) exists but is never called by create_clinic/onboarding (dead code) |
| TENT-006 | Chọn vital preset | POST /onboarding/start | VERIFIED DRIFT — admin picks specialty (general/pediatric/ob_gyn/dermatology/dental) → vital_fields derived implicitly; NO TCM, has dermatology instead; no explicit preset step |
| SUB-014 | Suspend clinic | PATCH /superadmin/clinics/{id} | VERIFIED DRIFT — only toggles is_active boolean (service.py:104); no suspend status/state machine |
| SUB-015 | Reactivate clinic | PATCH /superadmin/clinics/{id} | VERIFIED DRIFT — only is_active=true; no reactivate transition |
| SUB-021 | Subscription metrics dashboard | GET /superadmin/stats | VERIFIED DRIFT — stats (service.py:343) returns only total/active clinics+users, locked_users; NO MRR/ARR/churn/conversion |
| SVC-004 | Service-doctor mapping | (none) | VERIFIED DRIFT — no service↔doctor capability map (service.py:28); only VisitService.performed_by_user_id records actual performer after-the-fact |
| APPT-002 | Slot capacity per doctor | GET /appointments/slots | VERIFIED DRIFT — capacity is hardcoded stub _STUB_DOCTORS_ON_SHIFT=2 (slot_service.py:18); not per-doctor, not from HR shifts, no hourly cap (TODO TASK-014) |
| APPT-008 | NO_SHOW tracking | Arq cron auto_no_show_appointments | VERIFIED DRIFT — auto no-show cron exists (every 5min) but grace = 15min (DEFAULT_NO_SHOW_MINUTES), spec says 30min |
| BILL-003 | Manual invoice | POST /visits/{id}/invoices | VERIFIED DRIFT — model allows visit_id NULL (invoice.py:33) but NO creation path for standalone/retail invoice; only create_from_visit exists |
| BILL-016 | Void → reverse stock | POST /invoices/{id}/void | VERIFIED DRIFT — void does NOT reverse stock (invoice_service.py:478 docstring confirms); only refund releases pharmacy reservations |
| BILL-018 | In hóa đơn POS | GET /invoices/{id}/print | VERIFIED DRIFT — single generic HTML payload (max-width:400px); no format param to select 58/80mm |
| BILL-019 | In hóa đơn A4 | GET /invoices/{id}/print | VERIFIED DRIFT — no A4 variant; same single POS-style payload, no format distinction |
| RPT-004 | Số visit theo specialty | GET /reports/visit-volume | VERIFIED DRIFT — groups by period+STATUS, not by specialty |
| NOTI-006 | Stock low alert | Arq cron check_low_stock | VERIFIED DRIFT — stock-low only via hourly cron broadcast (user_id=None, not pharmacist-targeted); no event-driven trigger on threshold |
| CFG-011 | Timezone | (system default) | VERIFIED DRIFT — system default Asia/Ho_Chi_Minh only; no per-clinic timezone settings field |
| CFG-012 | Default language | (system default) | VERIFIED DRIFT — system default vi/en only; no per-clinic default_language settings field |
| PLT-002 | Platform role CRUD | GET /superadmin/roles | VERIFIED DRIFT — read-only list; no create/update/delete platform role |
| PLT-008 | Suspend clinic | PATCH /superadmin/clinics/{id} | suspend = is_active=false only (no status machine) |
| PLT-009 | Reactivate clinic | PATCH /superadmin/clinics/{id} | reactivate = is_active=true only |
| PLT-014 | Platform metrics dashboard | GET /superadmin/stats | metrics partial — counts only, no MRR/ARR/churn |
| PLT-018 | Feature flag UI | PATCH /superadmin/clinics/{id} | feature-flag primitive exists ({flag}_enabled, only bhyt) but SuperClinicUpdate does NOT expose it; no global flag UI |

## Phụ lục — Inventory 207 endpoint backend (`clinic-cms-merge`)

> Trích tự động từ `app/modules/*/api/*.py`. Permission = `require_permission(...)` (rỗng = chỉ cần đăng nhập).

### `admin` (13)

| Method | Path | Permission |
|---|---|---|
| POST | `/api/v1/admin/clinics` | clinic.create |
| GET | `/api/v1/admin/clinics/{clinic_id}` | clinic.read,clinic.update |
| PATCH | `/api/v1/admin/clinics/{clinic_id}` | clinic.update |
| GET | `/api/v1/clinics/me/settings` | clinic.settings.update |
| PATCH | `/api/v1/clinics/me/settings` | clinic.settings.update |
| POST | `/api/v1/onboarding/start` | clinic.onboard |
| GET | `/api/v1/onboarding/state` | clinic.onboard |
| POST | `/api/v1/onboarding/info` | clinic.onboard |
| POST | `/api/v1/onboarding/users` | clinic.onboard |
| POST | `/api/v1/onboarding/shifts` | clinic.onboard |
| POST | `/api/v1/onboarding/inventory-csv` | clinic.onboard |
| POST | `/api/v1/onboarding/services` | clinic.onboard |
| POST | `/api/v1/onboarding/complete` | clinic.onboard |

### `appointments` (8)

| Method | Path | Permission |
|---|---|---|
| GET | `/api/v1/appointments/slots` | appointment.read |
| GET | `/api/v1/appointments` | appointment.read |
| POST | `/api/v1/appointments` | appointment.write |
| GET | `/api/v1/appointments/{appointment_id}` | appointment.read,appointment.write |
| PATCH | `/api/v1/appointments/{appointment_id}` | appointment.write |
| POST | `/api/v1/appointments/{appointment_id}/confirm` | appointment.write |
| POST | `/api/v1/appointments/{appointment_id}/check-in` | appointment.write |
| POST | `/api/v1/appointments/{appointment_id}/cancel` | appointment.cancel |

### `audit` (2)

| Method | Path | Permission |
|---|---|---|
| POST | `/api/v1/admin/audit/verify-chain` | audit:verify |
| GET | `/api/v1/admin/audit-logs` | audit.read |

### `auth` (13)

| Method | Path | Permission |
|---|---|---|
| POST | `/api/v1/auth/login` | — |
| POST | `/api/v1/auth/mfa/challenge` | — |
| POST | `/api/v1/auth/refresh` | — |
| POST | `/api/v1/auth/logout` | — |
| POST | `/api/v1/auth/change-password` | — |
| POST | `/api/v1/auth/select-clinic` | — |
| GET | `/api/v1/auth/clinics` | — |
| PATCH | `/api/v1/auth/clinics/{clinic_id}/default` | — |
| POST | `/api/v1/auth/mfa/enroll` | — |
| POST | `/api/v1/auth/mfa/verify` | — |
| POST | `/api/v1/auth/mfa/disable` | — |
| POST | `/api/v1/auth/mfa/backup-codes/regenerate` | — |
| GET | `/api/v1/auth/fingerprints` | — |

### `bhyt` (5)

| Method | Path | Permission |
|---|---|---|
| GET | `/api/v1/settings/bhyt` | — |
| PATCH | `/api/v1/settings/bhyt` | bhyt:config |
| GET | `/api/v1/bhyt/funnel` | bhyt:reports |
| GET | `/api/v1/bhyt/sync-status` | vss:read |
| GET | `/api/v1/reports/bhyt/summary` | bhyt:reports |

### `billing` (13)

| Method | Path | Permission |
|---|---|---|
| POST | `/api/v1/visits/{visit_id}/invoices` | invoice.create |
| GET | `/api/v1/invoices` | invoice.read |
| GET | `/api/v1/invoices/{invoice_id}` | invoice.modify,invoice.read |
| PATCH | `/api/v1/invoices/{invoice_id}` | invoice.modify |
| POST | `/api/v1/invoices/{invoice_id}/lines` | invoice.modify |
| DELETE | `/api/v1/invoice-lines/{line_id}` | invoice.modify |
| POST | `/api/v1/invoices/{invoice_id}/submit` | invoice.create,invoice.void |
| POST | `/api/v1/invoices/{invoice_id}/void` | invoice.void |
| POST | `/api/v1/invoices/{invoice_id}/refund` | invoice.refund |
| GET | `/api/v1/invoices/{invoice_id}/print` | invoice.read |
| POST | `/api/v1/invoices/{invoice_id}/payments` | payment.receive |
| GET | `/api/v1/invoices/{invoice_id}/payments` | invoice.read,invoice.void |
| POST | `/api/v1/payments/{payment_id}/void` | invoice.void |

### `hr` (23)

| Method | Path | Permission |
|---|---|---|
| GET | `/api/v1/shift-templates` | shift.manage |
| POST | `/api/v1/shift-templates` | shift.manage |
| PATCH | `/api/v1/shift-templates/{template_id}` | shift.manage |
| DELETE | `/api/v1/shift-templates/{template_id}` | shift.manage |
| GET | `/api/v1/shifts` | shift.manage |
| POST | `/api/v1/shifts` | shift.manage |
| PATCH | `/api/v1/shifts/{shift_id}` | shift.manage |
| DELETE | `/api/v1/shifts/{shift_id}` | shift.manage |
| GET | `/api/v1/recurring-schedules` | shift.manage |
| POST | `/api/v1/recurring-schedules` | shift.manage |
| PATCH | `/api/v1/recurring-schedules/{schedule_id}` | shift.manage |
| DELETE | `/api/v1/recurring-schedules/{schedule_id}` | shift.manage |
| POST | `/api/v1/recurring-schedules/{schedule_id}/generate-shifts` | leave.approve,shift.manage |
| GET | `/api/v1/leave-requests` | leave.approve |
| POST | `/api/v1/leave-requests` | — |
| POST | `/api/v1/leave-requests/{leave_id}/approve` | leave.approve |
| POST | `/api/v1/leave-requests/{leave_id}/reject` | leave.approve |
| POST | `/api/v1/attendance/check-in` | attendance.manage |
| POST | `/api/v1/attendance/check-out` | attendance.manage |
| GET | `/api/v1/attendance/me` | — |
| GET | `/api/v1/attendance` | attendance.manage |
| GET | `/api/v1/attendance/export` | attendance.manage |
| GET | `/api/v1/hr/timesheet` | attendance.manage |

### `integrations` (4)

| Method | Path | Permission |
|---|---|---|
| POST | `/api/v1/integrations/vss/eligibility-check` | vss:read |
| POST | `/api/v1/integrations/vss/submit-claim` | vss:sync |
| GET | `/api/v1/integrations/vss/sync-log` | vss:read |
| GET | `/api/v1/integrations/vss/status` | vss:read |

### `inventory` (20)

| Method | Path | Permission |
|---|---|---|
| GET | `/api/v1/medicines` | medicine.manage,medicine.read |
| POST | `/api/v1/medicines` | medicine.manage,medicine.read |
| GET | `/api/v1/medicines/{medicine_id}` | medicine.manage,medicine.read |
| PATCH | `/api/v1/medicines/{medicine_id}` | medicine.manage |
| DELETE | `/api/v1/medicines/{medicine_id}` | inventory.read,medicine.manage |
| GET | `/api/v1/inventory/suppliers` | inventory.manage_catalog,inventory.read |
| POST | `/api/v1/inventory/suppliers` | inventory.manage_catalog |
| PATCH | `/api/v1/inventory/suppliers/{supplier_id}` | inventory.manage_catalog |
| DELETE | `/api/v1/inventory/suppliers/{supplier_id}` | inventory.manage_catalog,inventory.read |
| GET | `/api/v1/inventory/items` | inventory.manage_catalog,inventory.read |
| POST | `/api/v1/inventory/items` | inventory.manage_catalog |
| PATCH | `/api/v1/inventory/items/{item_id}` | inventory.manage_catalog |
| DELETE | `/api/v1/inventory/items/{item_id}` | inventory.manage_catalog,inventory.read |
| GET | `/api/v1/inventory/batches` | inventory.read |
| POST | `/api/v1/inventory/batches` | inventory.manage_catalog |
| PATCH | `/api/v1/inventory/batches/{batch_id}` | inventory.manage_catalog |
| DELETE | `/api/v1/inventory/batches/{batch_id}` | inventory.manage_catalog,inventory.purchase_in |
| POST | `/api/v1/inventory/purchase-in` | inventory.purchase_in |
| POST | `/api/v1/inventory/adjustments` | inventory.adjust |
| GET | `/api/v1/inventory/stock-status` | inventory.read |

### `notifications` (5)

| Method | Path | Permission |
|---|---|---|
| GET | `/api/v1/notifications` | — |
| GET | `/api/v1/notifications/unread-count` | — |
| POST | `/api/v1/notifications/{notification_id}/read` | — |
| POST | `/api/v1/notifications/mark-all-read` | — |
| POST | `/api/v1/notifications/{notification_id}/dismiss` | — |

### `patients` (13)

| Method | Path | Permission |
|---|---|---|
| POST | `/api/v1/patients/{patient_id}/erase/request` | patient.erase |
| DELETE | `/api/v1/patients/{patient_id}/erase` | patient.erase |
| GET | `/api/v1/patients` | patient.read |
| GET | `/api/v1/patients/search` | patient.read |
| POST | `/api/v1/patients` | patient.write |
| GET | `/api/v1/patients/{patient_id}` | patient.read |
| PATCH | `/api/v1/patients/{patient_id}` | patient.write |
| DELETE | `/api/v1/patients/{patient_id}` | patient.delete,patient.write |
| POST | `/api/v1/patients/{patient_id}/guardians` | patient.write |
| GET | `/api/v1/patients/{patient_id}/guardians` | patient.read |
| DELETE | `/api/v1/patients/guardians/{rel_id}` | patient.merge,patient.write |
| POST | `/api/v1/patients/merge` | patient.merge |
| POST | `/api/v1/patients/merge/{merge_id}/undo` | patient.merge |

### `pharmacy` (5)

| Method | Path | Permission |
|---|---|---|
| POST | `/api/v1/pharmacy/reserve` | pharmacy.dispense |
| POST | `/api/v1/pharmacy/release/{prescription_item_id}` | pharmacy.dispense |
| POST | `/api/v1/pharmacy/dispense/{prescription_id}` | pharmacy.dispense |
| POST | `/api/v1/pharmacy/substitute-batch` | pharmacy.dispense,pharmacy.substitute_batch |
| GET | `/api/v1/pharmacy/pending-dispense` | pharmacy.dispense |

### `prescriptions` (12)

| Method | Path | Permission |
|---|---|---|
| GET | `/api/v1/medicines/search` | medicine.read |
| GET | `/api/v1/medicines/{medicine_id}/substitutes` | medicine.read |
| GET | `/api/v1/medicines/{medicine_id}/lots` | medicine.read |
| POST | `/api/v1/visits/{visit_id}/prescriptions` | prescription.write |
| GET | `/api/v1/prescriptions/{prescription_id}` | prescription.read,prescription.write |
| PATCH | `/api/v1/prescriptions/{prescription_id}` | prescription.write |
| POST | `/api/v1/prescriptions/{prescription_id}/items` | prescription.write |
| PATCH | `/api/v1/prescription-items/{item_id}` | prescription.write |
| DELETE | `/api/v1/prescription-items/{item_id}` | prescription.write |
| POST | `/api/v1/prescriptions/{prescription_id}/submit` | prescription.write |
| POST | `/api/v1/prescriptions/{prescription_id}/cancel` | prescription.cancel |
| GET | `/api/v1/prescriptions/{prescription_id}/print` | prescription.print |

### `reports` (6)

| Method | Path | Permission |
|---|---|---|
| GET | `/api/v1/reports/revenue` | report.financial |
| GET | `/api/v1/reports/inventory-status` | report.view |
| GET | `/api/v1/reports/doctor-performance` | report.financial |
| GET | `/api/v1/reports/visit-volume` | report.view |
| GET | `/api/v1/reports/prescription-breakdown` | report.view |
| GET | `/api/v1/reports/snapshots` | report.view |

### `search` (1)

| Method | Path | Permission |
|---|---|---|
| GET | `/api/v1/search` | — |

### `services` (10)

| Method | Path | Permission |
|---|---|---|
| GET | `/api/v1/services` | service.read |
| POST | `/api/v1/services` | service.manage |
| GET | `/api/v1/services/{service_id}` | service.manage,service.read |
| PATCH | `/api/v1/services/{service_id}` | service.manage |
| DELETE | `/api/v1/services/{service_id}` | service.manage |
| POST | `/api/v1/visits/{visit_id}/services` | service.write |
| GET | `/api/v1/visits/{visit_id}/services` | service.read |
| PATCH | `/api/v1/visit-services/{vs_id}` | service.write |
| POST | `/api/v1/visit-services/{vs_id}/cancel` | service.price_override,service.write |
| PATCH | `/api/v1/visit-services/{vs_id}/price` | service.price_override |

### `superadmin` (11)

| Method | Path | Permission |
|---|---|---|
| GET | `/api/v1/superadmin/stats` | — |
| GET | `/api/v1/superadmin/clinics` | — |
| POST | `/api/v1/superadmin/clinics` | — |
| PATCH | `/api/v1/superadmin/clinics/{clinic_id}` | — |
| GET | `/api/v1/superadmin/accounts` | — |
| POST | `/api/v1/superadmin/accounts` | — |
| PATCH | `/api/v1/superadmin/accounts/{account_id}` | — |
| POST | `/api/v1/superadmin/accounts/{account_id}/reset-password` | — |
| GET | `/api/v1/superadmin/roles` | — |
| GET | `/api/v1/superadmin/permissions` | — |
| GET | `/api/v1/superadmin/audit-logs` | — |

### `users` (20)

| Method | Path | Permission |
|---|---|---|
| GET | `/api/v1/users` | user.manage |
| POST | `/api/v1/users` | user.manage |
| GET | `/api/v1/users/{user_id}` | user.manage |
| PATCH | `/api/v1/users/{user_id}` | user.manage |
| DELETE | `/api/v1/users/{user_id}` | user.manage |
| GET | `/api/v1/users/{user_id}/roles` | user.manage |
| POST | `/api/v1/users/{user_id}/roles` | role.manage |
| DELETE | `/api/v1/users/{user_id}/roles/{role_id}` | role.manage |
| GET | `/api/v1/users/{user_id}/extra-permissions` | user.manage |
| POST | `/api/v1/users/{user_id}/extra-permissions` | role.manage |
| DELETE | `/api/v1/users/{user_id}/extra-permissions/{ep_id}` | role.manage |
| GET | `/api/v1/roles` | role.manage |
| POST | `/api/v1/roles` | role.manage |
| GET | `/api/v1/roles/{role_id}` | role.manage |
| PATCH | `/api/v1/roles/{role_id}` | role.manage |
| DELETE | `/api/v1/roles/{role_id}` | role.manage |
| GET | `/api/v1/roles/{role_id}/permissions` | role.manage |
| POST | `/api/v1/roles/{role_id}/permissions` | role.manage |
| DELETE | `/api/v1/roles/{role_id}/permissions/{permission_code}` | role.manage |
| GET | `/api/v1/permissions` | — |

### `visits` (16)

| Method | Path | Permission |
|---|---|---|
| POST | `/api/v1/visits/{visit_id}/soap` | visit.read,visit.write |
| GET | `/api/v1/visits/{visit_id}/soap` | visit.read,visit.write |
| POST | `/api/v1/visits/{visit_id}/diagnosis` | visit.read,visit.write |
| GET | `/api/v1/visits/{visit_id}/diagnosis` | visit.read,visit.write |
| POST | `/api/v1/visits/{visit_id}/complete-emr` | visit.write |
| GET | `/api/v1/icd10/search` | visit.read |
| GET | `/api/v1/visits/queue` | visit.read,visit.write |
| POST | `/api/v1/visits/call-next` | visit.write |
| GET | `/api/v1/visits` | visit.read |
| POST | `/api/v1/visits` | visit.write |
| GET | `/api/v1/visits/{visit_id}` | visit.read,visit.write |
| PATCH | `/api/v1/visits/{visit_id}` | visit.write |
| POST | `/api/v1/visits/{visit_id}/start` | visit.write |
| POST | `/api/v1/visits/{visit_id}/complete` | visit.cancel,visit.write |
| POST | `/api/v1/visits/{visit_id}/cancel` | payment.receive,visit.cancel |
| POST | `/api/v1/visits/{visit_id}/mark-paid` | payment.receive |

### `vitals` (7)

| Method | Path | Permission |
|---|---|---|
| GET | `/api/v1/vitals/definitions` | vital.manage,vital.read |
| POST | `/api/v1/vitals/definitions` | vital.manage,vital.read |
| GET | `/api/v1/vitals/definitions/version/{version_number}` | vital.manage,vital.read |
| PATCH | `/api/v1/vitals/definitions/{definition_id}` | vital.manage |
| DELETE | `/api/v1/vitals/definitions/{definition_id}` | vital.manage,vital.write |
| POST | `/api/v1/visits/{visit_id}/vitals` | vital.read,vital.write |
| GET | `/api/v1/visits/{visit_id}/vitals` | vital.read |
