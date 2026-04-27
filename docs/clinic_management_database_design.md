# Hệ thống Quản lý Phòng khám — Thiết kế Database Chi tiết

> **Phiên bản:** 1.0
> **Database:** PostgreSQL 15+
> **Tài liệu liên quan:**
> - [Phân tích Nghiệp vụ](./clinic_management_business_analysis.md)
> - [Thiết kế Hệ thống](./clinic_management_system_design.md)
> **Mục đích:** DDL đầy đủ, ERD, indexes, constraints, RLS, triggers, sample queries

---

## Mục lục

1. [Tổng quan](#1-tổng-quan)
2. [Conventions](#2-conventions)
3. [ERD tổng quan](#3-erd-tổng-quan)
4. [Database setup](#4-database-setup)
5. [Sequences & Helper functions](#5-sequences--helper-functions)
6. [Core tables — Clinic](#6-core-tables--clinic)
7. [Auth & RBAC tables](#7-auth--rbac-tables)
8. [Patient tables](#8-patient-tables)
9. [Appointment tables](#9-appointment-tables)
10. [Visit tables](#10-visit-tables)
11. [Vitals tables](#11-vitals-tables)
12. [Service tables](#12-service-tables)
13. [Medicine & Inventory tables](#13-medicine--inventory-tables)
14. [Prescription tables](#14-prescription-tables)
15. [Billing tables](#15-billing-tables)
16. [HR tables](#16-hr-tables)
17. [Notification & Audit tables](#17-notification--audit-tables)
18. [Row-Level Security policies](#18-row-level-security-policies)
19. [Triggers](#19-triggers)
20. [Views](#20-views)
21. [Indexes — Tổng kết](#21-indexes--tổng-kết)
22. [Migration order](#22-migration-order)
23. [Seed data](#23-seed-data)
24. [Performance & Maintenance](#24-performance--maintenance)
25. [Sample queries](#25-sample-queries)
26. [Data dictionary](#26-data-dictionary)

---

## 1. Tổng quan

### 1.1. Phạm vi

Tài liệu này định nghĩa **schema database hoàn chỉnh** cho hệ thống quản lý phòng khám đa tenant. Bao gồm:

- 36 bảng nghiệp vụ + 1 bảng audit
- Tất cả constraints (PK, FK, CHECK, UNIQUE)
- Indexes tối ưu cho query thường dùng
- RLS policies đảm bảo tenant isolation
- Triggers cho audit và data integrity
- Views hỗ trợ reporting
- Sequences cho ID generation
- Helper functions

### 1.2. Mục tiêu thiết kế

| Yêu cầu | Hiện thực |
|---|---|
| **Multi-tenant isolation** | Cột `clinic_id` ở mọi bảng nghiệp vụ + RLS policies |
| **Audit trail đầy đủ** | Cột `created_at/by`, `updated_at/by`, `deleted_at/by` + bảng `audit_log` riêng |
| **Soft delete** | Cột `is_deleted` + partial index loại trừ |
| **Optimistic locking** | Cột `version` tăng tự động qua trigger |
| **Time zone aware** | `TIMESTAMP WITH TIME ZONE` (TIMESTAMPTZ) cho mọi thời điểm |
| **High concurrency** | `FOR UPDATE SKIP LOCKED` cho queue, batch reservation |
| **Reporting nhanh** | Indexes có chọn lọc, partial indexes cho hot path |
| **Schema evolution** | Forward-only Alembic migrations, không phá hoại |

### 1.3. PostgreSQL version & extensions

```sql
-- Yêu cầu tối thiểu PostgreSQL 15
-- Extensions cần thiết:
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";       -- uuid_generate_v4()
CREATE EXTENSION IF NOT EXISTS "pgcrypto";        -- gen_random_uuid(), digest()
CREATE EXTENSION IF NOT EXISTS "unaccent";        -- bỏ dấu tiếng Việt cho search
CREATE EXTENSION IF NOT EXISTS "pg_trgm";         -- trigram cho fuzzy search
CREATE EXTENSION IF NOT EXISTS "btree_gin";       -- GIN index trên scalar types
```

---

## 2. Conventions

### 2.1. Naming

| Loại | Quy tắc | Ví dụ |
|---|---|---|
| Bảng | `snake_case`, **số ít** | `patient`, `visit`, `prescription_item` |
| Cột | `snake_case` | `created_at`, `is_active` |
| Foreign key | `<ref_table>_id` | `patient_id`, `clinic_id` |
| Boolean | `is_*` / `has_*` | `is_active`, `has_insurance` |
| Timestamp | `*_at` | `created_at`, `paid_at` |
| Date | `*_date` | `birth_date`, `expiry_date` |
| Primary key constraint | `pk_<table>` | `pk_patient` |
| Foreign key constraint | `fk_<table>_<col>` | `fk_visit_patient_id` |
| Check constraint | `ck_<table>_<col>` | `ck_visit_status` |
| Unique constraint | `uq_<table>_<col>` | `uq_clinic_code` |
| Index thường | `ix_<table>_<col>` | `ix_patient_phone` |
| Partial index | `ix_<table>_<col>_<filter>` | `ix_patient_phone_active` |
| GIN index | `gix_<table>_<col>` | `gix_patient_name_search` |
| Trigger | `tg_<table>_<event>` | `tg_patient_audit` |
| Function | `fn_<purpose>` | `fn_update_version()` |
| Sequence | `seq_<purpose>` | `seq_patient_code` |
| View | `v_<purpose>` | `v_active_queue` |

### 2.2. Data types chuẩn

| Dùng cho | PostgreSQL type | Lý do |
|---|---|---|
| Primary key | `UUID` (default `gen_random_uuid()`) | Distributed-friendly, không sequential leak |
| Money | `NUMERIC(15, 2)` | Chính xác, không float rounding |
| Quantity (thuốc) | `NUMERIC(12, 3)` | 3 chữ số thập phân (vd 0.5 viên) |
| Phone | `VARCHAR(20)` | Đủ cho VN + extension |
| Email | `VARCHAR(200)` | Spec RFC tối đa 254 |
| Text dài | `TEXT` | Không giới hạn |
| Timestamp | `TIMESTAMPTZ` | Always timezone-aware |
| Date | `DATE` | Không cần time |
| Time | `TIME` | Cho start/end của ca |
| JSON | `JSONB` | Indexable, faster than JSON |
| Enum | `VARCHAR(N)` + `CHECK` | Dễ migrate hơn native ENUM |

**Lưu ý về ENUM:** Dùng `VARCHAR + CHECK` thay vì `CREATE TYPE ENUM` vì:
- Thêm value mới vào ENUM cần `ALTER TYPE` — không revert được trong transaction (PostgreSQL < 12 issue, nay đã fix một phần).
- Khó rename/remove value.
- ORM SQLAlchemy compatibility tốt hơn với VARCHAR.

### 2.3. Standard columns (mọi bảng nghiệp vụ)

```sql
-- Primary key
id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

-- Tenancy
clinic_id UUID NOT NULL REFERENCES clinic(id) ON DELETE RESTRICT,

-- Soft delete
is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
deleted_at TIMESTAMPTZ,
deleted_by UUID,

-- Audit
created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
created_by UUID,
updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
updated_by UUID,

-- Optimistic lock
version INTEGER NOT NULL DEFAULT 1,
```

### 2.4. CHECK constraints chuẩn

```sql
-- Soft delete consistency
CONSTRAINT ck_<table>_soft_delete_consistency
  CHECK (
    (is_deleted = FALSE AND deleted_at IS NULL AND deleted_by IS NULL) OR
    (is_deleted = TRUE AND deleted_at IS NOT NULL)
  ),

-- Money không âm
CONSTRAINT ck_<table>_amount_non_negative
  CHECK (amount >= 0),

-- Quantity dương
CONSTRAINT ck_<table>_quantity_positive
  CHECK (quantity > 0),

-- Date logic
CONSTRAINT ck_<table>_date_range
  CHECK (end_date >= start_date),

-- Status enum
CONSTRAINT ck_<table>_status
  CHECK (status IN ('value1', 'value2', ...)),
```

---

## 3. ERD tổng quan

### 3.1. Sơ đồ quan hệ chính

```
                              ┌─────────────────┐
                              │     CLINIC      │
                              │  (tenant root)  │
                              └────────┬────────┘
                                       │ 1
                ┌──────────────────────┼──────────────────────┐
                │                      │                      │
                ▼ N                    ▼ N                    ▼ N
         ┌──────────┐           ┌──────────┐           ┌──────────┐
         │   USER   │           │ PATIENT  │           │ MEDICINE │
         └────┬─────┘           └─────┬────┘           └────┬─────┘
              │                       │                     │
              │ M:N                   │                     │
              ▼                       ▼ 1:N                 ▼ 1:N
         ┌──────────┐           ┌──────────────┐      ┌──────────────┐
         │   ROLE   │           │ APPOINTMENT  │      │ INVENTORY_   │
         └────┬─────┘           └──────┬───────┘      │     ITEM     │
              │ M:N                    │ 1:1          └──────┬───────┘
              ▼                        ▼ optional             │ 1:N
       ┌────────────┐             ┌──────────┐                ▼
       │ PERMISSION │             │  VISIT   │           ┌──────────┐
       └────────────┘             │ (central)│           │  BATCH   │
                                  └─────┬────┘           └──────────┘
                                        │
                ┌─────────┬──────────┬──┴───┬──────────┐
                ▼ 1:N     ▼ 1:N      ▼ 1:N  ▼ 1:N      ▼ 1:1
        ┌────────────┐ ┌─────────┐ ┌──────┐ ┌───────────────┐ ┌─────────┐
        │ VISIT_     │ │  VISIT  │ │PRESC.│ │ PRESCRIPTION  │ │ INVOICE │
        │  VITALS    │ │ SERVICE │ │      │ │ ITEM ─→BATCH  │ │         │
        └────────────┘ └─────────┘ └───┬──┘ └───────────────┘ └────┬────┘
                                       │ 1:N                       │ 1:N
                                       ▼                           ▼
                                ┌──────────────┐            ┌──────────────┐
                                │ PRESCRIPTION │            │ INVOICE_ITEM │
                                │     ITEM     │            │              │
                                └──────────────┘            └──────────────┘
                                                                 ▲ N:1
                                                                 │
                                                            ┌────┴──────┐
                                                            │  PAYMENT  │
                                                            └───────────┘
```

### 3.2. Cluster theo module

**Cluster 1 — Identity & Access (5 bảng)**
- `clinic`, `clinic_settings`, `user`, `role`, `permission`, `role_permission`, `user_role`, `user_extra_permission`

**Cluster 2 — Patient (2 bảng)**
- `patient`, `patient_relation`

**Cluster 3 — Workflow (3 bảng)**
- `appointment`, `visit`, `visit_service`

**Cluster 4 — Vitals (4 bảng)**
- `system_vital_preset`, `vital_field_definition`, `vital_schema_version`, `visit_vitals`

**Cluster 5 — Catalog (2 bảng)**
- `service`, `medicine`

**Cluster 6 — Inventory (4 bảng)**
- `supplier`, `inventory_item`, `batch`, `stock_movement`

**Cluster 7 — Prescription (3 bảng)**
- `prescription`, `prescription_item`, `prescription_item_batch`

**Cluster 8 — Billing (3 bảng)**
- `invoice`, `invoice_item`, `payment`

**Cluster 9 — HR (5 bảng)**
- `shift_template`, `shift`, `recurring_schedule`, `leave_request`, `time_log`

**Cluster 10 — Cross-cutting (2 bảng)**
- `notification`, `audit_log`

**Tổng:** 37 bảng (1 audit_log không có clinic_id ở mức bắt buộc).

---

## 4. Database setup

### 4.1. Tạo database & user

```sql
-- Production
CREATE DATABASE cms_production
  WITH ENCODING = 'UTF8'
       LC_COLLATE = 'en_US.UTF-8'
       LC_CTYPE = 'en_US.UTF-8'
       TEMPLATE = template0;

-- Application user (limited permissions, RLS applies)
CREATE ROLE cms_app WITH LOGIN PASSWORD '<strong-password>';
GRANT CONNECT ON DATABASE cms_production TO cms_app;
GRANT USAGE ON SCHEMA public TO cms_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO cms_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO cms_app;

-- Default cho table mới
ALTER DEFAULT PRIVILEGES IN SCHEMA public
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO cms_app;

-- Migration user (DDL, bypass RLS)
CREATE ROLE cms_migrator WITH LOGIN PASSWORD '<strong-password>' BYPASSRLS;
GRANT ALL PRIVILEGES ON DATABASE cms_production TO cms_migrator;
GRANT ALL PRIVILEGES ON SCHEMA public TO cms_migrator;

-- Read-only user (cho reporting, BI tools)
CREATE ROLE cms_readonly WITH LOGIN PASSWORD '<strong-password>';
GRANT CONNECT ON DATABASE cms_production TO cms_readonly;
GRANT USAGE ON SCHEMA public TO cms_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO cms_readonly;
```

### 4.2. Connection settings (postgresql.conf)

```ini
# Connection
max_connections = 200
shared_buffers = 4GB           # ~25% RAM
effective_cache_size = 12GB    # ~75% RAM
work_mem = 32MB
maintenance_work_mem = 512MB

# WAL & checkpoint
wal_level = replica
max_wal_size = 4GB
min_wal_size = 1GB
checkpoint_completion_target = 0.9

# Query planner
random_page_cost = 1.1         # SSD
effective_io_concurrency = 200 # SSD

# Logging
log_min_duration_statement = 1000   # log query > 1s
log_connections = on
log_disconnections = on
log_lock_waits = on
log_statement = 'ddl'

# Statistics
track_activities = on
track_counts = on
track_io_timing = on

# Autovacuum
autovacuum = on
autovacuum_naptime = 30s
autovacuum_vacuum_scale_factor = 0.1
autovacuum_analyze_scale_factor = 0.05
```

---

## 5. Sequences & Helper functions

### 5.1. Helper function: auto-update updated_at + version

```sql
CREATE OR REPLACE FUNCTION fn_update_audit_columns()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  NEW.version = COALESCE(OLD.version, 0) + 1;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION fn_update_audit_columns() IS
  'Tự động cập nhật updated_at và tăng version khi UPDATE.';
```

### 5.2. Helper function: optimistic lock check

```sql
CREATE OR REPLACE FUNCTION fn_check_version()
RETURNS TRIGGER AS $$
BEGIN
  -- Nếu client truyền version cụ thể, phải khớp với version hiện tại
  -- Logic này thường thực hiện ở app layer, đây là defense
  IF NEW.version IS NOT NULL AND NEW.version != OLD.version + 1 THEN
    -- App layer phải gửi OLD.version + 1
    -- Nếu gửi version cũ → conflict
    NULL;  -- hiện tại để app handle
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

### 5.3. Helper function: generate next code per clinic

```sql
CREATE OR REPLACE FUNCTION fn_next_patient_code(p_clinic_id UUID)
RETURNS VARCHAR AS $$
DECLARE
  v_last_num INTEGER;
  v_next_num INTEGER;
BEGIN
  -- Lock để tránh race
  SELECT COALESCE(MAX(SUBSTRING(patient_code FROM 3)::INTEGER), 0)
    INTO v_last_num
    FROM patient
   WHERE clinic_id = p_clinic_id
     AND patient_code ~ '^BN[0-9]+$';

  v_next_num := v_last_num + 1;
  RETURN 'BN' || LPAD(v_next_num::TEXT, 6, '0');
END;
$$ LANGUAGE plpgsql;

-- Tương tự cho visit_number
CREATE OR REPLACE FUNCTION fn_next_visit_number(p_clinic_id UUID, p_date DATE)
RETURNS VARCHAR AS $$
DECLARE
  v_prefix VARCHAR;
  v_last_num INTEGER;
  v_next_num INTEGER;
BEGIN
  v_prefix := TO_CHAR(p_date, 'YYYYMMDD');

  SELECT COALESCE(MAX(SUBSTRING(visit_number FROM 10)::INTEGER), 0)
    INTO v_last_num
    FROM visit
   WHERE clinic_id = p_clinic_id
     AND visit_number LIKE v_prefix || '-%';

  v_next_num := v_last_num + 1;
  RETURN v_prefix || '-' || LPAD(v_next_num::TEXT, 3, '0');
END;
$$ LANGUAGE plpgsql;

-- Tương tự cho invoice_number
CREATE OR REPLACE FUNCTION fn_next_invoice_number(p_clinic_id UUID, p_date DATE)
RETURNS VARCHAR AS $$
DECLARE
  v_prefix VARCHAR;
  v_last_num INTEGER;
  v_next_num INTEGER;
BEGIN
  v_prefix := 'INV-' || TO_CHAR(p_date, 'YYYYMMDD');

  SELECT COALESCE(MAX(SUBSTRING(invoice_number FROM 14)::INTEGER), 0)
    INTO v_last_num
    FROM invoice
   WHERE clinic_id = p_clinic_id
     AND invoice_number LIKE v_prefix || '-%';

  v_next_num := v_last_num + 1;
  RETURN v_prefix || '-' || LPAD(v_next_num::TEXT, 3, '0');
END;
$$ LANGUAGE plpgsql;
```

**Lưu ý:** App layer nên dùng `SELECT ... FOR UPDATE` ở đầu transaction tạo entity để đảm bảo unique. Function trên là helper, không thay thế lock.

---

## 6. Core tables — Clinic

### 6.1. `clinic` — Tenant root

```sql
CREATE TABLE clinic (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  code VARCHAR(50) NOT NULL,
  name VARCHAR(200) NOT NULL,
  specialty VARCHAR(50) NOT NULL,

  address VARCHAR(500),
  phone VARCHAR(20),
  email VARCHAR(200),
  tax_code VARCHAR(50),
  logo_url VARCHAR(500),

  is_active BOOLEAN NOT NULL DEFAULT TRUE,

  -- Soft delete
  is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
  deleted_at TIMESTAMPTZ,
  deleted_by UUID,

  -- Audit
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_by UUID,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_by UUID,
  version INTEGER NOT NULL DEFAULT 1,

  CONSTRAINT ck_clinic_specialty CHECK (
    specialty IN ('general', 'dental', 'pediatric', 'obstetric', 'dermatology', 'ophthalmology', 'tcm')
  ),
  CONSTRAINT ck_clinic_code_format CHECK (code ~ '^[A-Z0-9_-]{3,50}$'),
  CONSTRAINT ck_clinic_soft_delete CHECK (
    (is_deleted = FALSE AND deleted_at IS NULL) OR
    (is_deleted = TRUE AND deleted_at IS NOT NULL)
  )
);

-- Code phải unique trong các clinic chưa bị xóa
CREATE UNIQUE INDEX uq_clinic_code ON clinic (code) WHERE is_deleted = FALSE;
CREATE INDEX ix_clinic_active ON clinic (is_active) WHERE is_deleted = FALSE;

COMMENT ON TABLE clinic IS 'Tenant root — mỗi phòng khám là 1 tenant.';
COMMENT ON COLUMN clinic.code IS 'Mã clinic dùng khi login (vd: ABC_CLINIC).';
COMMENT ON COLUMN clinic.specialty IS 'Chuyên khoa chính: general/dental/pediatric/obstetric/dermatology/ophthalmology/tcm.';
```

### 6.2. `clinic_settings` — Cấu hình per clinic

```sql
CREATE TABLE clinic_settings (
  clinic_id UUID PRIMARY KEY REFERENCES clinic(id) ON DELETE CASCADE,
  settings JSONB NOT NULL DEFAULT '{}'::jsonb,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_by UUID
);

CREATE INDEX gix_clinic_settings_data ON clinic_settings USING GIN (settings);

COMMENT ON TABLE clinic_settings IS 'Cấu hình mềm per clinic (operating_hours, queue, billing rules...).';
```

---

## 7. Auth & RBAC tables

### 7.1. `user`

```sql
CREATE TABLE "user" (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  clinic_id UUID NOT NULL REFERENCES clinic(id) ON DELETE RESTRICT,

  username VARCHAR(100) NOT NULL,
  email VARCHAR(200),
  phone VARCHAR(20),
  password_hash VARCHAR(255) NOT NULL,
  full_name VARCHAR(200) NOT NULL,

  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  is_locked BOOLEAN NOT NULL DEFAULT FALSE,
  failed_login_count INTEGER NOT NULL DEFAULT 0,
  last_login_at TIMESTAMPTZ,
  password_changed_at TIMESTAMPTZ,

  -- Doctor-specific (nullable)
  license_number VARCHAR(100),
  specialty_subfield VARCHAR(100),

  is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
  deleted_at TIMESTAMPTZ,
  deleted_by UUID,

  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_by UUID,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_by UUID,
  version INTEGER NOT NULL DEFAULT 1,

  CONSTRAINT ck_user_username_format CHECK (username ~ '^[a-zA-Z0-9_.-]{3,100}$'),
  CONSTRAINT ck_user_failed_login CHECK (failed_login_count >= 0)
);

-- Username unique trong clinic (chỉ tính chưa xóa)
CREATE UNIQUE INDEX uq_user_clinic_username
  ON "user" (clinic_id, LOWER(username))
  WHERE is_deleted = FALSE;

-- Email unique trong clinic (nếu có)
CREATE UNIQUE INDEX uq_user_clinic_email
  ON "user" (clinic_id, LOWER(email))
  WHERE is_deleted = FALSE AND email IS NOT NULL;

CREATE INDEX ix_user_clinic_active ON "user" (clinic_id, is_active) WHERE is_deleted = FALSE;

COMMENT ON TABLE "user" IS 'Nhân viên của clinic (admin/doctor/nurse/pharmacist/receptionist).';
```

### 7.2. `role`

```sql
CREATE TABLE role (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  clinic_id UUID REFERENCES clinic(id) ON DELETE CASCADE,
  -- nullable: NULL = system role (apply cho mọi clinic)

  code VARCHAR(50) NOT NULL,
  name VARCHAR(100) NOT NULL,
  description VARCHAR(500),
  is_system BOOLEAN NOT NULL DEFAULT FALSE,

  is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
  deleted_at TIMESTAMPTZ,
  deleted_by UUID,

  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_by UUID,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_by UUID,
  version INTEGER NOT NULL DEFAULT 1,

  CONSTRAINT ck_role_code_format CHECK (code ~ '^[a-z_]{2,50}$')
);

-- System roles (clinic_id NULL): code phải unique
CREATE UNIQUE INDEX uq_role_system_code
  ON role (code)
  WHERE clinic_id IS NULL AND is_deleted = FALSE;

-- Clinic roles: code unique trong clinic
CREATE UNIQUE INDEX uq_role_clinic_code
  ON role (clinic_id, code)
  WHERE clinic_id IS NOT NULL AND is_deleted = FALSE;

COMMENT ON TABLE role IS 'Vai trò. clinic_id NULL = system role.';
```

### 7.3. `permission`

```sql
CREATE TABLE permission (
  code VARCHAR(100) PRIMARY KEY,
  name VARCHAR(200) NOT NULL,
  description VARCHAR(500),
  category VARCHAR(50),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  CONSTRAINT ck_permission_code_format CHECK (code ~ '^[a-z_]+\.[a-z_]+$')
);

CREATE INDEX ix_permission_category ON permission (category);

COMMENT ON TABLE permission IS 'System-level permission catalog. Format: <module>.<action> (vd: patient.read).';
```

### 7.4. `role_permission`

```sql
CREATE TABLE role_permission (
  role_id UUID NOT NULL REFERENCES role(id) ON DELETE CASCADE,
  permission_code VARCHAR(100) NOT NULL REFERENCES permission(code) ON DELETE CASCADE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  PRIMARY KEY (role_id, permission_code)
);

CREATE INDEX ix_role_permission_perm ON role_permission (permission_code);
```

### 7.5. `user_role`

```sql
CREATE TABLE user_role (
  user_id UUID NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
  role_id UUID NOT NULL REFERENCES role(id) ON DELETE CASCADE,
  assigned_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  assigned_by UUID,

  PRIMARY KEY (user_id, role_id)
);

CREATE INDEX ix_user_role_role ON user_role (role_id);

COMMENT ON TABLE user_role IS 'User có thể có nhiều role (multi-role).';
```

### 7.6. `user_extra_permission`

```sql
CREATE TABLE user_extra_permission (
  user_id UUID NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
  permission_code VARCHAR(100) NOT NULL REFERENCES permission(code) ON DELETE CASCADE,
  grant_type VARCHAR(10) NOT NULL,  -- 'grant' | 'deny'
  reason VARCHAR(500),
  granted_by UUID,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  PRIMARY KEY (user_id, permission_code),
  CONSTRAINT ck_extra_perm_grant_type CHECK (grant_type IN ('grant', 'deny'))
);

COMMENT ON TABLE user_extra_permission IS 'Override permission per user (grant thêm hoặc deny dù role có).';
```

---

## 8. Patient tables

### 8.1. `patient`

```sql
CREATE TABLE patient (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  clinic_id UUID NOT NULL REFERENCES clinic(id) ON DELETE RESTRICT,

  patient_code VARCHAR(20) NOT NULL,
  full_name VARCHAR(200) NOT NULL,

  date_of_birth DATE,
  birth_year INTEGER,
  gender VARCHAR(10) NOT NULL,

  phone VARCHAR(20),
  email VARCHAR(200),
  id_number VARCHAR(20),       -- CCCD/CMND

  address_line VARCHAR(500),
  ward VARCHAR(100),
  district VARCHAR(100),
  province VARCHAR(100),

  blood_type VARCHAR(5),
  allergies TEXT,
  chronic_conditions TEXT,

  occupation VARCHAR(100),
  referral_source VARCHAR(100),
  notes TEXT,

  is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
  deleted_at TIMESTAMPTZ,
  deleted_by UUID,

  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_by UUID,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_by UUID,
  version INTEGER NOT NULL DEFAULT 1,

  CONSTRAINT ck_patient_gender CHECK (gender IN ('male', 'female', 'other')),
  CONSTRAINT ck_patient_blood_type CHECK (
    blood_type IS NULL OR blood_type IN ('A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-')
  ),
  CONSTRAINT ck_patient_birth_year CHECK (
    birth_year IS NULL OR (birth_year BETWEEN 1900 AND EXTRACT(YEAR FROM CURRENT_DATE)::INT)
  ),
  CONSTRAINT ck_patient_dob_or_year CHECK (
    date_of_birth IS NOT NULL OR birth_year IS NOT NULL
  ),
  CONSTRAINT ck_patient_dob_consistency CHECK (
    date_of_birth IS NULL OR EXTRACT(YEAR FROM date_of_birth)::INT = birth_year
    OR birth_year IS NULL
  )
);

-- Patient code unique trong clinic
CREATE UNIQUE INDEX uq_patient_clinic_code
  ON patient (clinic_id, patient_code)
  WHERE is_deleted = FALSE;

-- Search theo phone (rất phổ biến) — không unique vì 1 phone có thể nhiều bệnh nhân
CREATE INDEX ix_patient_clinic_phone
  ON patient (clinic_id, phone)
  WHERE is_deleted = FALSE AND phone IS NOT NULL;

-- Full text search trên tên (bỏ dấu)
CREATE INDEX gix_patient_name_search
  ON patient
  USING GIN (clinic_id, to_tsvector('simple', unaccent(full_name)))
  WHERE is_deleted = FALSE;

-- Trigram cho fuzzy search
CREATE INDEX gix_patient_name_trgm
  ON patient
  USING GIN (full_name gin_trgm_ops)
  WHERE is_deleted = FALSE;

-- ID number lookup
CREATE INDEX ix_patient_id_number
  ON patient (clinic_id, id_number)
  WHERE is_deleted = FALSE AND id_number IS NOT NULL;

COMMENT ON TABLE patient IS 'Hồ sơ bệnh nhân. Phone không unique vì có thể chia sẻ.';
COMMENT ON COLUMN patient.patient_code IS 'Mã hiển thị (vd: BN000001), unique trong clinic.';
COMMENT ON COLUMN patient.birth_year IS 'Dùng khi không nhớ ngày tháng cụ thể.';
```

### 8.2. `patient_relation`

```sql
CREATE TABLE patient_relation (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  clinic_id UUID NOT NULL REFERENCES clinic(id) ON DELETE RESTRICT,

  patient_id UUID NOT NULL REFERENCES patient(id) ON DELETE CASCADE,
  guardian_patient_id UUID NOT NULL REFERENCES patient(id) ON DELETE CASCADE,
  relation_type VARCHAR(20) NOT NULL,
  is_primary_contact BOOLEAN NOT NULL DEFAULT FALSE,

  is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
  deleted_at TIMESTAMPTZ,
  deleted_by UUID,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_by UUID,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_by UUID,
  version INTEGER NOT NULL DEFAULT 1,

  CONSTRAINT ck_patient_relation_type CHECK (
    relation_type IN ('parent', 'spouse', 'child', 'sibling', 'other')
  ),
  CONSTRAINT ck_patient_relation_not_self CHECK (patient_id != guardian_patient_id)
);

CREATE INDEX ix_patient_relation_patient
  ON patient_relation (patient_id)
  WHERE is_deleted = FALSE;

CREATE INDEX ix_patient_relation_guardian
  ON patient_relation (guardian_patient_id)
  WHERE is_deleted = FALSE;

-- Một quan hệ giữa 2 patient chỉ tồn tại 1 lần
CREATE UNIQUE INDEX uq_patient_relation
  ON patient_relation (patient_id, guardian_patient_id, relation_type)
  WHERE is_deleted = FALSE;

COMMENT ON TABLE patient_relation IS 'Quan hệ giám hộ giữa các bệnh nhân.';
```

---

## 9. Appointment tables

### 9.1. `appointment`

```sql
CREATE TABLE appointment (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  clinic_id UUID NOT NULL REFERENCES clinic(id) ON DELETE RESTRICT,

  patient_id UUID NOT NULL REFERENCES patient(id) ON DELETE RESTRICT,
  assigned_doctor_id UUID REFERENCES "user"(id) ON DELETE SET NULL,

  scheduled_at TIMESTAMPTZ NOT NULL,
  duration_minutes INTEGER NOT NULL DEFAULT 30,

  status VARCHAR(20) NOT NULL DEFAULT 'scheduled',

  chief_complaint TEXT,
  notes TEXT,

  confirmed_at TIMESTAMPTZ,
  checked_in_at TIMESTAMPTZ,
  cancelled_at TIMESTAMPTZ,
  cancellation_reason TEXT,
  reminder_sent_at TIMESTAMPTZ,

  is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
  deleted_at TIMESTAMPTZ,
  deleted_by UUID,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_by UUID,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_by UUID,
  version INTEGER NOT NULL DEFAULT 1,

  CONSTRAINT ck_appointment_status CHECK (
    status IN ('scheduled', 'confirmed', 'checked_in', 'completed', 'cancelled', 'no_show')
  ),
  CONSTRAINT ck_appointment_duration CHECK (duration_minutes BETWEEN 5 AND 480)
);

-- Lookup theo time slot (capacity check)
CREATE INDEX ix_appointment_clinic_time_active
  ON appointment (clinic_id, scheduled_at)
  WHERE is_deleted = FALSE AND status IN ('scheduled', 'confirmed', 'checked_in');

-- Patient history
CREATE INDEX ix_appointment_patient_time
  ON appointment (patient_id, scheduled_at DESC)
  WHERE is_deleted = FALSE;

-- Doctor assignment
CREATE INDEX ix_appointment_doctor_time
  ON appointment (assigned_doctor_id, scheduled_at)
  WHERE is_deleted = FALSE AND assigned_doctor_id IS NOT NULL;

-- Cron auto-no-show
CREATE INDEX ix_appointment_no_show_check
  ON appointment (scheduled_at)
  WHERE status IN ('scheduled', 'confirmed') AND is_deleted = FALSE;

-- Reminder cron
CREATE INDEX ix_appointment_reminder
  ON appointment (scheduled_at)
  WHERE reminder_sent_at IS NULL AND status IN ('scheduled', 'confirmed') AND is_deleted = FALSE;

COMMENT ON TABLE appointment IS 'Lịch hẹn khám. Status: scheduled→confirmed→checked_in→completed.';
```

---

## 10. Visit tables

### 10.1. `visit`

```sql
CREATE TABLE visit (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  clinic_id UUID NOT NULL REFERENCES clinic(id) ON DELETE RESTRICT,

  patient_id UUID NOT NULL REFERENCES patient(id) ON DELETE RESTRICT,
  appointment_id UUID UNIQUE REFERENCES appointment(id) ON DELETE SET NULL,
  assigned_doctor_id UUID REFERENCES "user"(id) ON DELETE SET NULL,
  doctor_id UUID REFERENCES "user"(id) ON DELETE SET NULL,

  visit_number VARCHAR(30) NOT NULL,

  chief_complaint TEXT,
  notes TEXT,

  status VARCHAR(20) NOT NULL DEFAULT 'WAITING',
  priority INTEGER NOT NULL DEFAULT 0,
  is_follow_up BOOLEAN NOT NULL DEFAULT FALSE,
  is_returning BOOLEAN NOT NULL DEFAULT FALSE,

  check_in_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  consultation_started_at TIMESTAMPTZ,
  consultation_ended_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  cancelled_at TIMESTAMPTZ,
  cancellation_reason TEXT,

  is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
  deleted_at TIMESTAMPTZ,
  deleted_by UUID,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_by UUID,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_by UUID,
  version INTEGER NOT NULL DEFAULT 1,

  CONSTRAINT ck_visit_status CHECK (
    status IN ('WAITING', 'IN_PROGRESS', 'AWAITING_PAYMENT', 'COMPLETED', 'CANCELLED')
  ),
  CONSTRAINT ck_visit_priority CHECK (priority IN (0, 5, 10)),
  CONSTRAINT ck_visit_consultation_times CHECK (
    consultation_ended_at IS NULL OR consultation_started_at IS NULL OR
    consultation_ended_at >= consultation_started_at
  )
);

CREATE UNIQUE INDEX uq_visit_clinic_number
  ON visit (clinic_id, visit_number)
  WHERE is_deleted = FALSE;

-- Queue lookup (HOT PATH)
CREATE INDEX ix_visit_queue
  ON visit (clinic_id, priority DESC, is_returning DESC, check_in_at ASC)
  WHERE status = 'WAITING' AND is_deleted = FALSE;

-- Doctor's active visit
CREATE INDEX ix_visit_doctor_active
  ON visit (doctor_id)
  WHERE status IN ('IN_PROGRESS', 'AWAITING_PAYMENT') AND is_deleted = FALSE;

-- Patient history
CREATE INDEX ix_visit_patient_time
  ON visit (patient_id, check_in_at DESC)
  WHERE is_deleted = FALSE;

-- Reporting (theo ngày)
CREATE INDEX ix_visit_clinic_check_in
  ON visit (clinic_id, check_in_at DESC)
  WHERE is_deleted = FALSE;

-- Status filter
CREATE INDEX ix_visit_clinic_status
  ON visit (clinic_id, status)
  WHERE is_deleted = FALSE;

COMMENT ON TABLE visit IS 'Lượt khám. Entity trung tâm kết nối patient/doctor/services/prescription/invoice.';
```

---

## 11. Vitals tables

### 11.1. `system_vital_preset`

```sql
CREATE TABLE system_vital_preset (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  specialty_code VARCHAR(50) NOT NULL UNIQUE,
  name VARCHAR(100) NOT NULL,
  description VARCHAR(500),
  fields JSONB NOT NULL,
  is_default BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE system_vital_preset IS 'Master data: preset vital schema theo specialty (general/dental/pediatric/...).';
COMMENT ON COLUMN system_vital_preset.fields IS
  'Array of field definitions: [{key, label, data_type, unit, min_value, max_value, ...}]';
```

### 11.2. `vital_field_definition`

```sql
CREATE TABLE vital_field_definition (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  clinic_id UUID NOT NULL REFERENCES clinic(id) ON DELETE RESTRICT,

  key VARCHAR(100) NOT NULL,
  label VARCHAR(200) NOT NULL,
  data_type VARCHAR(20) NOT NULL,

  unit VARCHAR(20),
  min_value NUMERIC(10, 4),
  max_value NUMERIC(10, 4),
  warning_min NUMERIC(10, 4),
  warning_max NUMERIC(10, 4),
  decimal_places INTEGER,
  options JSONB,                    -- cho data_type = 'select'

  is_required BOOLEAN NOT NULL DEFAULT FALSE,
  sort_order INTEGER NOT NULL DEFAULT 0,
  group_name VARCHAR(100),
  placeholder VARCHAR(200),
  help_text VARCHAR(500),

  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  is_system BOOLEAN NOT NULL DEFAULT FALSE,

  is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
  deleted_at TIMESTAMPTZ,
  deleted_by UUID,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_by UUID,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_by UUID,
  version INTEGER NOT NULL DEFAULT 1,

  CONSTRAINT ck_vital_field_data_type CHECK (
    data_type IN ('number', 'integer', 'text', 'boolean', 'select')
  ),
  CONSTRAINT ck_vital_field_key_format CHECK (key ~ '^[a-z][a-z0-9_]{0,99}$'),
  CONSTRAINT ck_vital_field_range CHECK (
    min_value IS NULL OR max_value IS NULL OR min_value <= max_value
  ),
  CONSTRAINT ck_vital_field_warning_range CHECK (
    warning_min IS NULL OR warning_max IS NULL OR warning_min <= warning_max
  ),
  CONSTRAINT ck_vital_field_select_has_options CHECK (
    data_type != 'select' OR (options IS NOT NULL AND jsonb_array_length(options) > 0)
  ),
  CONSTRAINT ck_vital_field_decimal_places CHECK (
    decimal_places IS NULL OR (decimal_places BETWEEN 0 AND 4)
  )
);

CREATE UNIQUE INDEX uq_vital_field_clinic_key
  ON vital_field_definition (clinic_id, key)
  WHERE is_deleted = FALSE;

CREATE INDEX ix_vital_field_clinic_active
  ON vital_field_definition (clinic_id, sort_order)
  WHERE is_active = TRUE AND is_deleted = FALSE;

COMMENT ON TABLE vital_field_definition IS
  'Định nghĩa field vital động per clinic. Key và data_type không cho sửa sau khi tạo.';
```

### 11.3. `vital_schema_version`

```sql
CREATE TABLE vital_schema_version (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  clinic_id UUID NOT NULL REFERENCES clinic(id) ON DELETE RESTRICT,

  version INTEGER NOT NULL,
  field_snapshot JSONB NOT NULL,
  changed_by UUID NOT NULL,
  change_summary VARCHAR(500),
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  CONSTRAINT ck_schema_version_positive CHECK (version > 0)
);

CREATE UNIQUE INDEX uq_vital_schema_clinic_version
  ON vital_schema_version (clinic_id, version);

CREATE INDEX ix_vital_schema_clinic_latest
  ON vital_schema_version (clinic_id, version DESC);

COMMENT ON TABLE vital_schema_version IS
  'Snapshot schema mỗi lần thay đổi. Dùng để giải mã VisitVitals cũ.';
```

### 11.4. `visit_vitals`

```sql
CREATE TABLE visit_vitals (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  clinic_id UUID NOT NULL REFERENCES clinic(id) ON DELETE RESTRICT,

  visit_id UUID NOT NULL REFERENCES visit(id) ON DELETE CASCADE,
  recorded_by UUID NOT NULL REFERENCES "user"(id) ON DELETE RESTRICT,
  recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  schema_version INTEGER NOT NULL,
  values JSONB NOT NULL,
  notes TEXT,
  is_primary BOOLEAN NOT NULL DEFAULT FALSE,

  is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
  deleted_at TIMESTAMPTZ,
  deleted_by UUID,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_by UUID,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_by UUID,
  version INTEGER NOT NULL DEFAULT 1
);

CREATE INDEX ix_visit_vitals_visit
  ON visit_vitals (visit_id, recorded_at DESC)
  WHERE is_deleted = FALSE;

-- GIN cho query trên JSONB (vd: trend huyết áp 6 tháng)
CREATE INDEX gix_visit_vitals_values
  ON visit_vitals
  USING GIN (values jsonb_path_ops)
  WHERE is_deleted = FALSE;

-- Đảm bảo mỗi visit chỉ có 1 vitals primary
CREATE UNIQUE INDEX uq_visit_vitals_primary
  ON visit_vitals (visit_id)
  WHERE is_primary = TRUE AND is_deleted = FALSE;

COMMENT ON TABLE visit_vitals IS 'Bản ghi đo vitals. values là JSONB theo schema_version.';
```

---

## 12. Service tables

### 12.1. `service`

```sql
CREATE TABLE service (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  clinic_id UUID NOT NULL REFERENCES clinic(id) ON DELETE RESTRICT,

  code VARCHAR(50) NOT NULL,
  name VARCHAR(200) NOT NULL,
  description TEXT,
  category VARCHAR(100),

  default_price NUMERIC(15, 2) NOT NULL,
  duration_minutes INTEGER,

  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  sort_order INTEGER NOT NULL DEFAULT 0,

  is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
  deleted_at TIMESTAMPTZ,
  deleted_by UUID,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_by UUID,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_by UUID,
  version INTEGER NOT NULL DEFAULT 1,

  CONSTRAINT ck_service_price CHECK (default_price >= 0),
  CONSTRAINT ck_service_duration CHECK (duration_minutes IS NULL OR duration_minutes > 0)
);

CREATE UNIQUE INDEX uq_service_clinic_code
  ON service (clinic_id, code)
  WHERE is_deleted = FALSE;

CREATE INDEX ix_service_clinic_active
  ON service (clinic_id, sort_order)
  WHERE is_active = TRUE AND is_deleted = FALSE;

CREATE INDEX gix_service_name_search
  ON service
  USING GIN (clinic_id, to_tsvector('simple', unaccent(name)))
  WHERE is_deleted = FALSE;

COMMENT ON TABLE service IS 'Catalog dịch vụ của clinic (khám, thủ thuật, xét nghiệm...).';
```

### 12.2. `visit_service`

```sql
CREATE TABLE visit_service (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  clinic_id UUID NOT NULL REFERENCES clinic(id) ON DELETE RESTRICT,

  visit_id UUID NOT NULL REFERENCES visit(id) ON DELETE CASCADE,
  service_id UUID NOT NULL REFERENCES service(id) ON DELETE RESTRICT,
  performed_by UUID REFERENCES "user"(id) ON DELETE SET NULL,

  quantity NUMERIC(10, 3) NOT NULL DEFAULT 1,
  unit_price NUMERIC(15, 2) NOT NULL,
  discount_amount NUMERIC(15, 2) NOT NULL DEFAULT 0,
  discount_reason VARCHAR(500),
  total_amount NUMERIC(15, 2) NOT NULL,

  notes TEXT,
  status VARCHAR(20) NOT NULL DEFAULT 'ordered',
  performed_at TIMESTAMPTZ,

  is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
  deleted_at TIMESTAMPTZ,
  deleted_by UUID,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_by UUID,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_by UUID,
  version INTEGER NOT NULL DEFAULT 1,

  CONSTRAINT ck_visit_service_status CHECK (
    status IN ('ordered', 'in_progress', 'completed', 'cancelled')
  ),
  CONSTRAINT ck_visit_service_quantity CHECK (quantity > 0),
  CONSTRAINT ck_visit_service_unit_price CHECK (unit_price >= 0),
  CONSTRAINT ck_visit_service_discount CHECK (discount_amount >= 0),
  CONSTRAINT ck_visit_service_total CHECK (total_amount >= 0)
);

CREATE INDEX ix_visit_service_visit
  ON visit_service (visit_id)
  WHERE is_deleted = FALSE;

CREATE INDEX ix_visit_service_service_stats
  ON visit_service (clinic_id, service_id, created_at DESC)
  WHERE status = 'completed' AND is_deleted = FALSE;

-- Báo cáo doanh thu theo bác sĩ
CREATE INDEX ix_visit_service_doctor_stats
  ON visit_service (clinic_id, performed_by, created_at DESC)
  WHERE status = 'completed' AND is_deleted = FALSE;

COMMENT ON TABLE visit_service IS 'Dịch vụ được cung cấp trong 1 visit. Snapshot giá tại thời điểm chỉ định.';
```

---

## 13. Medicine & Inventory tables

### 13.1. `medicine`

```sql
CREATE TABLE medicine (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  clinic_id UUID NOT NULL REFERENCES clinic(id) ON DELETE RESTRICT,

  code VARCHAR(50) NOT NULL,
  name VARCHAR(300) NOT NULL,
  generic_name VARCHAR(300),
  strength VARCHAR(100),
  form VARCHAR(50),
  manufacturer VARCHAR(200),
  atc_code VARCHAR(20),
  registration_number VARCHAR(100),

  base_unit VARCHAR(20) NOT NULL,
  pack_size NUMERIC(10, 3) NOT NULL DEFAULT 1,
  pack_unit VARCHAR(20),

  is_prescription_only BOOLEAN NOT NULL DEFAULT FALSE,
  is_controlled BOOLEAN NOT NULL DEFAULT FALSE,
  storage_condition VARCHAR(200),
  notes TEXT,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,

  is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
  deleted_at TIMESTAMPTZ,
  deleted_by UUID,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_by UUID,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_by UUID,
  version INTEGER NOT NULL DEFAULT 1,

  CONSTRAINT ck_medicine_form CHECK (
    form IS NULL OR form IN (
      'tablet', 'capsule', 'syrup', 'injection', 'cream',
      'ointment', 'drops', 'powder', 'suspension', 'spray', 'patch', 'other'
    )
  ),
  CONSTRAINT ck_medicine_pack_size CHECK (pack_size > 0)
);

CREATE UNIQUE INDEX uq_medicine_clinic_code
  ON medicine (clinic_id, code)
  WHERE is_deleted = FALSE;

CREATE INDEX gix_medicine_name_search
  ON medicine
  USING GIN (clinic_id, to_tsvector('simple', unaccent(name || ' ' || COALESCE(generic_name, ''))))
  WHERE is_deleted = FALSE;

CREATE INDEX gix_medicine_name_trgm
  ON medicine
  USING GIN (name gin_trgm_ops)
  WHERE is_deleted = FALSE;

CREATE INDEX ix_medicine_clinic_active
  ON medicine (clinic_id)
  WHERE is_active = TRUE AND is_deleted = FALSE;

COMMENT ON TABLE medicine IS 'Catalog thuốc per clinic. base_unit (viên/ml), pack_size (vd 100 nếu 1 hộp = 100 viên).';
```

### 13.2. `supplier`

```sql
CREATE TABLE supplier (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  clinic_id UUID NOT NULL REFERENCES clinic(id) ON DELETE RESTRICT,

  code VARCHAR(50) NOT NULL,
  name VARCHAR(200) NOT NULL,
  contact_person VARCHAR(200),
  phone VARCHAR(20),
  email VARCHAR(200),
  address TEXT,
  notes TEXT,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,

  is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
  deleted_at TIMESTAMPTZ,
  deleted_by UUID,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_by UUID,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_by UUID,
  version INTEGER NOT NULL DEFAULT 1
);

CREATE UNIQUE INDEX uq_supplier_clinic_code
  ON supplier (clinic_id, code)
  WHERE is_deleted = FALSE;

CREATE INDEX ix_supplier_clinic_active
  ON supplier (clinic_id, name)
  WHERE is_active = TRUE AND is_deleted = FALSE;
```

### 13.3. `inventory_item`

```sql
CREATE TABLE inventory_item (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  clinic_id UUID NOT NULL REFERENCES clinic(id) ON DELETE RESTRICT,

  medicine_id UUID NOT NULL REFERENCES medicine(id) ON DELETE RESTRICT,

  default_purchase_price NUMERIC(15, 2),
  default_sale_price NUMERIC(15, 2) NOT NULL,
  reorder_point NUMERIC(10, 3),
  reorder_quantity NUMERIC(10, 3),
  location VARCHAR(100),
  is_active BOOLEAN NOT NULL DEFAULT TRUE,

  is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
  deleted_at TIMESTAMPTZ,
  deleted_by UUID,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_by UUID,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_by UUID,
  version INTEGER NOT NULL DEFAULT 1,

  CONSTRAINT ck_inventory_purchase_price CHECK (
    default_purchase_price IS NULL OR default_purchase_price >= 0
  ),
  CONSTRAINT ck_inventory_sale_price CHECK (default_sale_price >= 0),
  CONSTRAINT ck_inventory_reorder_point CHECK (
    reorder_point IS NULL OR reorder_point >= 0
  )
);

CREATE UNIQUE INDEX uq_inventory_clinic_medicine
  ON inventory_item (clinic_id, medicine_id)
  WHERE is_deleted = FALSE;

CREATE INDEX ix_inventory_clinic_active
  ON inventory_item (clinic_id)
  WHERE is_active = TRUE AND is_deleted = FALSE;

COMMENT ON TABLE inventory_item IS
  'Một medicine cụ thể trong kho của clinic. Tồn kho thực tế ở bảng batch.';
```

### 13.4. `batch`

```sql
CREATE TABLE batch (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  clinic_id UUID NOT NULL REFERENCES clinic(id) ON DELETE RESTRICT,

  inventory_item_id UUID NOT NULL REFERENCES inventory_item(id) ON DELETE RESTRICT,
  supplier_id UUID REFERENCES supplier(id) ON DELETE SET NULL,

  batch_number VARCHAR(100) NOT NULL,
  manufacturing_date DATE,
  expiry_date DATE NOT NULL,
  received_date DATE NOT NULL,

  purchase_price NUMERIC(15, 2),

  initial_quantity NUMERIC(12, 3) NOT NULL,
  actual_quantity NUMERIC(12, 3) NOT NULL,
  reserved_quantity NUMERIC(12, 3) NOT NULL DEFAULT 0,

  is_recalled BOOLEAN NOT NULL DEFAULT FALSE,
  notes TEXT,

  is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
  deleted_at TIMESTAMPTZ,
  deleted_by UUID,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_by UUID,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_by UUID,
  version INTEGER NOT NULL DEFAULT 1,

  CONSTRAINT ck_batch_quantities CHECK (
    initial_quantity >= 0 AND
    actual_quantity >= 0 AND
    reserved_quantity >= 0 AND
    reserved_quantity <= actual_quantity
  ),
  CONSTRAINT ck_batch_dates CHECK (
    manufacturing_date IS NULL OR expiry_date >= manufacturing_date
  ),
  CONSTRAINT ck_batch_purchase_price CHECK (
    purchase_price IS NULL OR purchase_price >= 0
  )
);

-- HOT PATH: FEFO query
CREATE INDEX ix_batch_fefo
  ON batch (clinic_id, inventory_item_id, expiry_date ASC, received_date ASC)
  WHERE is_deleted = FALSE
    AND is_recalled = FALSE
    AND actual_quantity > reserved_quantity;

-- Cảnh báo expiry
CREATE INDEX ix_batch_expiry_alert
  ON batch (clinic_id, expiry_date)
  WHERE is_deleted = FALSE AND actual_quantity > 0;

-- Inventory item lookup
CREATE INDEX ix_batch_inventory_item
  ON batch (inventory_item_id, expiry_date ASC)
  WHERE is_deleted = FALSE;

-- Batch number lookup
CREATE INDEX ix_batch_number
  ON batch (clinic_id, batch_number)
  WHERE is_deleted = FALSE;

COMMENT ON TABLE batch IS
  'Lô của 1 inventory item. available = actual_quantity - reserved_quantity.';
```

### 13.5. `stock_movement`

```sql
CREATE TABLE stock_movement (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  clinic_id UUID NOT NULL REFERENCES clinic(id) ON DELETE RESTRICT,
  batch_id UUID NOT NULL REFERENCES batch(id) ON DELETE RESTRICT,

  movement_type VARCHAR(30) NOT NULL,
  quantity_delta NUMERIC(12, 3) NOT NULL,
  quantity_before NUMERIC(12, 3) NOT NULL,
  quantity_after NUMERIC(12, 3) NOT NULL,

  reference_type VARCHAR(50),
  reference_id UUID,
  reason TEXT,

  performed_by UUID NOT NULL REFERENCES "user"(id) ON DELETE RESTRICT,
  performed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  CONSTRAINT ck_stock_movement_type CHECK (
    movement_type IN (
      'purchase_in', 'prescription_out',
      'adjustment_increase', 'adjustment_decrease',
      'transfer_out', 'transfer_in',
      'expiry_writeoff', 'damage_writeoff', 'recall_writeoff',
      'return_in'
    )
  ),
  CONSTRAINT ck_stock_movement_consistency CHECK (
    quantity_after = quantity_before + quantity_delta
  )
);

CREATE INDEX ix_stock_movement_batch
  ON stock_movement (batch_id, performed_at DESC);

CREATE INDEX ix_stock_movement_clinic_time
  ON stock_movement (clinic_id, performed_at DESC);

CREATE INDEX ix_stock_movement_reference
  ON stock_movement (reference_type, reference_id)
  WHERE reference_id IS NOT NULL;

-- Append-only: không cho UPDATE/DELETE bằng RLS hoặc trigger (xem section triggers)

COMMENT ON TABLE stock_movement IS 'Append-only log mọi thay đổi tồn kho. Không cho UPDATE/DELETE.';
```

---

## 14. Prescription tables

### 14.1. `prescription`

```sql
CREATE TABLE prescription (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  clinic_id UUID NOT NULL REFERENCES clinic(id) ON DELETE RESTRICT,

  visit_id UUID NOT NULL REFERENCES visit(id) ON DELETE CASCADE,
  prescribed_by UUID NOT NULL REFERENCES "user"(id) ON DELETE RESTRICT,
  prescribed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  dispense_type VARCHAR(20) NOT NULL,
  status VARCHAR(30) NOT NULL DEFAULT 'pending',

  notes TEXT,
  printed_at TIMESTAMPTZ,

  is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
  deleted_at TIMESTAMPTZ,
  deleted_by UUID,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_by UUID,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_by UUID,
  version INTEGER NOT NULL DEFAULT 1,

  CONSTRAINT ck_prescription_dispense_type CHECK (
    dispense_type IN ('in_house', 'external', 'mixed')
  ),
  CONSTRAINT ck_prescription_status CHECK (
    status IN ('pending', 'partially_dispensed', 'dispensed', 'cancelled')
  )
);

CREATE INDEX ix_prescription_visit
  ON prescription (visit_id)
  WHERE is_deleted = FALSE;

CREATE INDEX ix_prescription_doctor_stats
  ON prescription (clinic_id, prescribed_by, prescribed_at DESC)
  WHERE is_deleted = FALSE;

CREATE INDEX ix_prescription_pharmacy_queue
  ON prescription (clinic_id, prescribed_at)
  WHERE status IN ('pending', 'partially_dispensed')
    AND dispense_type IN ('in_house', 'mixed')
    AND is_deleted = FALSE;
```

### 14.2. `prescription_item`

```sql
CREATE TABLE prescription_item (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  clinic_id UUID NOT NULL REFERENCES clinic(id) ON DELETE RESTRICT,

  prescription_id UUID NOT NULL REFERENCES prescription(id) ON DELETE CASCADE,
  medicine_id UUID REFERENCES medicine(id) ON DELETE RESTRICT,
  medicine_name_text VARCHAR(300),

  quantity NUMERIC(10, 3) NOT NULL,
  dosage_text VARCHAR(500) NOT NULL,
  duration_days INTEGER,
  instructions TEXT,

  dispense_source VARCHAR(20) NOT NULL,
  in_house_status VARCHAR(20),

  unit_price NUMERIC(15, 2),
  total_amount NUMERIC(15, 2),

  sort_order INTEGER NOT NULL DEFAULT 0,

  is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
  deleted_at TIMESTAMPTZ,
  deleted_by UUID,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_by UUID,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_by UUID,
  version INTEGER NOT NULL DEFAULT 1,

  CONSTRAINT ck_prescription_item_quantity CHECK (quantity > 0),
  CONSTRAINT ck_prescription_item_duration CHECK (duration_days IS NULL OR duration_days > 0),
  CONSTRAINT ck_prescription_item_dispense_source CHECK (
    dispense_source IN ('in_house', 'external')
  ),
  CONSTRAINT ck_prescription_item_in_house_status CHECK (
    (dispense_source = 'in_house' AND in_house_status IN ('pending', 'reserved', 'dispensed', 'cancelled'))
    OR (dispense_source = 'external' AND in_house_status IS NULL)
  ),
  CONSTRAINT ck_prescription_item_medicine_required CHECK (
    medicine_id IS NOT NULL OR medicine_name_text IS NOT NULL
  ),
  CONSTRAINT ck_prescription_item_in_house_has_medicine CHECK (
    dispense_source = 'external' OR medicine_id IS NOT NULL
  ),
  CONSTRAINT ck_prescription_item_in_house_has_price CHECK (
    dispense_source = 'external' OR (unit_price IS NOT NULL AND total_amount IS NOT NULL)
  )
);

CREATE INDEX ix_prescription_item_prescription
  ON prescription_item (prescription_id, sort_order)
  WHERE is_deleted = FALSE;

CREATE INDEX ix_prescription_item_medicine_stats
  ON prescription_item (clinic_id, medicine_id, created_at DESC)
  WHERE in_house_status = 'dispensed' AND is_deleted = FALSE;
```

### 14.3. `prescription_item_batch`

```sql
CREATE TABLE prescription_item_batch (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  clinic_id UUID NOT NULL REFERENCES clinic(id) ON DELETE RESTRICT,

  prescription_item_id UUID NOT NULL REFERENCES prescription_item(id) ON DELETE CASCADE,
  batch_id UUID NOT NULL REFERENCES batch(id) ON DELETE RESTRICT,

  quantity NUMERIC(10, 3) NOT NULL,
  status VARCHAR(20) NOT NULL,

  dispensed_at TIMESTAMPTZ,
  dispensed_by UUID REFERENCES "user"(id) ON DELETE SET NULL,

  is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
  deleted_at TIMESTAMPTZ,
  deleted_by UUID,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_by UUID,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_by UUID,
  version INTEGER NOT NULL DEFAULT 1,

  CONSTRAINT ck_pib_quantity CHECK (quantity > 0),
  CONSTRAINT ck_pib_status CHECK (
    status IN ('reserved', 'dispensed', 'cancelled', 'substituted')
  ),
  CONSTRAINT ck_pib_dispensed_consistency CHECK (
    (status = 'dispensed' AND dispensed_at IS NOT NULL AND dispensed_by IS NOT NULL)
    OR status != 'dispensed'
  )
);

CREATE INDEX ix_pib_item
  ON prescription_item_batch (prescription_item_id)
  WHERE is_deleted = FALSE;

CREATE INDEX ix_pib_batch
  ON prescription_item_batch (batch_id, status)
  WHERE is_deleted = FALSE;

COMMENT ON TABLE prescription_item_batch IS
  'Mapping prescription_item ↔ batches đã reserve/dispense. 1 item có thể từ nhiều batch.';
```

---

## 15. Billing tables

### 15.1. `invoice`

```sql
CREATE TABLE invoice (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  clinic_id UUID NOT NULL REFERENCES clinic(id) ON DELETE RESTRICT,

  visit_id UUID NOT NULL REFERENCES visit(id) ON DELETE RESTRICT,
  patient_id UUID NOT NULL REFERENCES patient(id) ON DELETE RESTRICT,

  invoice_number VARCHAR(30) NOT NULL,

  subtotal NUMERIC(15, 2) NOT NULL DEFAULT 0,
  total_discount NUMERIC(15, 2) NOT NULL DEFAULT 0,
  discount_reason VARCHAR(500),
  total_tax NUMERIC(15, 2) NOT NULL DEFAULT 0,
  total_amount NUMERIC(15, 2) NOT NULL DEFAULT 0,
  paid_amount NUMERIC(15, 2) NOT NULL DEFAULT 0,

  status VARCHAR(20) NOT NULL DEFAULT 'draft',

  issued_at TIMESTAMPTZ,
  paid_at TIMESTAMPTZ,
  cancelled_at TIMESTAMPTZ,
  cancellation_reason TEXT,
  voided_by_invoice_id UUID REFERENCES invoice(id) ON DELETE SET NULL,

  notes TEXT,

  is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
  deleted_at TIMESTAMPTZ,
  deleted_by UUID,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_by UUID,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_by UUID,
  version INTEGER NOT NULL DEFAULT 1,

  CONSTRAINT ck_invoice_status CHECK (
    status IN ('draft', 'pending', 'partially_paid', 'paid', 'cancelled', 'refunded')
  ),
  CONSTRAINT ck_invoice_amounts CHECK (
    subtotal >= 0 AND
    total_discount >= 0 AND
    total_tax >= 0 AND
    paid_amount >= 0
  ),
  CONSTRAINT ck_invoice_total_consistency CHECK (
    total_amount = subtotal - total_discount + total_tax
  ),
  CONSTRAINT ck_invoice_paid_not_exceed CHECK (
    paid_amount <= total_amount OR status = 'refunded'
  )
);

CREATE UNIQUE INDEX uq_invoice_clinic_number
  ON invoice (clinic_id, invoice_number)
  WHERE is_deleted = FALSE;

CREATE UNIQUE INDEX uq_invoice_visit
  ON invoice (visit_id)
  WHERE is_deleted = FALSE AND status != 'cancelled';

CREATE INDEX ix_invoice_clinic_status
  ON invoice (clinic_id, status, issued_at DESC)
  WHERE is_deleted = FALSE;

CREATE INDEX ix_invoice_patient
  ON invoice (patient_id, issued_at DESC)
  WHERE is_deleted = FALSE;

-- Báo cáo doanh thu theo ngày
CREATE INDEX ix_invoice_revenue
  ON invoice (clinic_id, paid_at DESC)
  WHERE status = 'paid' AND is_deleted = FALSE;

-- Công nợ
CREATE INDEX ix_invoice_outstanding
  ON invoice (clinic_id, issued_at)
  WHERE status IN ('pending', 'partially_paid') AND is_deleted = FALSE;

COMMENT ON TABLE invoice IS 'Hóa đơn. balance = total_amount - paid_amount.';
```

### 15.2. `invoice_item`

```sql
CREATE TABLE invoice_item (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  clinic_id UUID NOT NULL REFERENCES clinic(id) ON DELETE RESTRICT,

  invoice_id UUID NOT NULL REFERENCES invoice(id) ON DELETE CASCADE,

  item_type VARCHAR(20) NOT NULL,
  reference_type VARCHAR(50),
  reference_id UUID,

  description VARCHAR(500) NOT NULL,
  quantity NUMERIC(10, 3) NOT NULL DEFAULT 1,
  unit_price NUMERIC(15, 2) NOT NULL,
  discount_amount NUMERIC(15, 2) NOT NULL DEFAULT 0,
  discount_reason VARCHAR(500),
  tax_amount NUMERIC(15, 2) NOT NULL DEFAULT 0,
  total NUMERIC(15, 2) NOT NULL,

  sort_order INTEGER NOT NULL DEFAULT 0,

  is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
  deleted_at TIMESTAMPTZ,
  deleted_by UUID,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_by UUID,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_by UUID,
  version INTEGER NOT NULL DEFAULT 1,

  CONSTRAINT ck_invoice_item_type CHECK (
    item_type IN ('service', 'medicine', 'other')
  ),
  CONSTRAINT ck_invoice_item_amounts CHECK (
    quantity > 0 AND
    unit_price >= 0 AND
    discount_amount >= 0 AND
    tax_amount >= 0 AND
    total >= 0
  )
);

CREATE INDEX ix_invoice_item_invoice
  ON invoice_item (invoice_id, sort_order)
  WHERE is_deleted = FALSE;

CREATE INDEX ix_invoice_item_reference
  ON invoice_item (reference_type, reference_id)
  WHERE reference_id IS NOT NULL AND is_deleted = FALSE;
```

### 15.3. `payment`

```sql
CREATE TABLE payment (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  clinic_id UUID NOT NULL REFERENCES clinic(id) ON DELETE RESTRICT,

  invoice_id UUID NOT NULL REFERENCES invoice(id) ON DELETE RESTRICT,

  payment_method VARCHAR(20) NOT NULL,
  amount NUMERIC(15, 2) NOT NULL,
  paid_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  reference_number VARCHAR(100),
  notes TEXT,
  received_by UUID NOT NULL REFERENCES "user"(id) ON DELETE RESTRICT,

  is_refund BOOLEAN NOT NULL DEFAULT FALSE,

  is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
  deleted_at TIMESTAMPTZ,
  deleted_by UUID,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_by UUID,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_by UUID,
  version INTEGER NOT NULL DEFAULT 1,

  CONSTRAINT ck_payment_method CHECK (
    payment_method IN ('cash', 'card', 'bank_transfer', 'ewallet', 'other')
  ),
  CONSTRAINT ck_payment_amount CHECK (amount > 0)
);

CREATE INDEX ix_payment_invoice
  ON payment (invoice_id, paid_at DESC)
  WHERE is_deleted = FALSE;

CREATE INDEX ix_payment_clinic_time
  ON payment (clinic_id, paid_at DESC)
  WHERE is_deleted = FALSE;

-- Báo cáo theo phương thức thanh toán
CREATE INDEX ix_payment_method_stats
  ON payment (clinic_id, payment_method, paid_at DESC)
  WHERE is_deleted = FALSE;
```

---

## 16. HR tables

### 16.1. `shift_template`

```sql
CREATE TABLE shift_template (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  clinic_id UUID NOT NULL REFERENCES clinic(id) ON DELETE RESTRICT,

  name VARCHAR(100) NOT NULL,
  start_time TIME NOT NULL,
  end_time TIME NOT NULL,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,

  is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
  deleted_at TIMESTAMPTZ,
  deleted_by UUID,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_by UUID,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_by UUID,
  version INTEGER NOT NULL DEFAULT 1,

  CONSTRAINT ck_shift_template_time CHECK (start_time < end_time)
);

CREATE UNIQUE INDEX uq_shift_template_clinic_name
  ON shift_template (clinic_id, name)
  WHERE is_deleted = FALSE;
```

### 16.2. `shift`

```sql
CREATE TABLE shift (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  clinic_id UUID NOT NULL REFERENCES clinic(id) ON DELETE RESTRICT,

  user_id UUID NOT NULL REFERENCES "user"(id) ON DELETE RESTRICT,
  shift_template_id UUID REFERENCES shift_template(id) ON DELETE SET NULL,

  shift_date DATE NOT NULL,
  start_time TIME NOT NULL,
  end_time TIME NOT NULL,
  role_in_shift VARCHAR(50),

  status VARCHAR(20) NOT NULL DEFAULT 'scheduled',
  notes TEXT,

  is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
  deleted_at TIMESTAMPTZ,
  deleted_by UUID,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_by UUID,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_by UUID,
  version INTEGER NOT NULL DEFAULT 1,

  CONSTRAINT ck_shift_status CHECK (
    status IN ('scheduled', 'cancelled', 'on_leave', 'completed')
  ),
  CONSTRAINT ck_shift_time CHECK (start_time < end_time)
);

-- Một nhân viên không có 2 shift trùng giờ trong cùng ngày
CREATE UNIQUE INDEX uq_shift_user_date_time
  ON shift (clinic_id, user_id, shift_date, start_time)
  WHERE is_deleted = FALSE AND status != 'cancelled';

-- Capacity check (đếm số bác sĩ đang làm tại slot)
CREATE INDEX ix_shift_clinic_date_active
  ON shift (clinic_id, shift_date, start_time, end_time)
  WHERE status = 'scheduled' AND is_deleted = FALSE;

-- User schedule
CREATE INDEX ix_shift_user_date
  ON shift (user_id, shift_date)
  WHERE is_deleted = FALSE;

COMMENT ON TABLE shift IS 'Ca trực cụ thể. 1 nhân viên/ngày có thể nhiều ca.';
```

### 16.3. `recurring_schedule`

```sql
CREATE TABLE recurring_schedule (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  clinic_id UUID NOT NULL REFERENCES clinic(id) ON DELETE RESTRICT,

  user_id UUID NOT NULL REFERENCES "user"(id) ON DELETE RESTRICT,
  shift_template_id UUID NOT NULL REFERENCES shift_template(id) ON DELETE RESTRICT,
  days_of_week INTEGER[] NOT NULL,

  effective_from DATE NOT NULL,
  effective_to DATE,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,

  is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
  deleted_at TIMESTAMPTZ,
  deleted_by UUID,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_by UUID,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_by UUID,
  version INTEGER NOT NULL DEFAULT 1,

  CONSTRAINT ck_recurring_dates CHECK (
    effective_to IS NULL OR effective_to >= effective_from
  ),
  CONSTRAINT ck_recurring_dow CHECK (
    days_of_week <@ ARRAY[1,2,3,4,5,6,7]
    AND array_length(days_of_week, 1) > 0
  )
);

CREATE INDEX ix_recurring_user_active
  ON recurring_schedule (user_id, effective_from)
  WHERE is_active = TRUE AND is_deleted = FALSE;

COMMENT ON COLUMN recurring_schedule.days_of_week IS
  'ISO weekday: 1=Mon...7=Sun. Vd [1,3,5] = Thứ 2,4,6.';
```

### 16.4. `leave_request`

```sql
CREATE TABLE leave_request (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  clinic_id UUID NOT NULL REFERENCES clinic(id) ON DELETE RESTRICT,

  user_id UUID NOT NULL REFERENCES "user"(id) ON DELETE RESTRICT,
  leave_type VARCHAR(20) NOT NULL,
  start_date DATE NOT NULL,
  end_date DATE NOT NULL,
  reason TEXT NOT NULL,

  status VARCHAR(20) NOT NULL DEFAULT 'pending',
  approved_by UUID REFERENCES "user"(id) ON DELETE SET NULL,
  approved_at TIMESTAMPTZ,
  rejection_reason TEXT,

  is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
  deleted_at TIMESTAMPTZ,
  deleted_by UUID,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_by UUID,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_by UUID,
  version INTEGER NOT NULL DEFAULT 1,

  CONSTRAINT ck_leave_type CHECK (
    leave_type IN ('sick', 'personal', 'vacation', 'maternity', 'other')
  ),
  CONSTRAINT ck_leave_status CHECK (
    status IN ('pending', 'approved', 'rejected', 'cancelled')
  ),
  CONSTRAINT ck_leave_dates CHECK (end_date >= start_date)
);

CREATE INDEX ix_leave_user_status
  ON leave_request (user_id, status, start_date DESC)
  WHERE is_deleted = FALSE;

CREATE INDEX ix_leave_pending
  ON leave_request (clinic_id, created_at DESC)
  WHERE status = 'pending' AND is_deleted = FALSE;

CREATE INDEX ix_leave_approved_dates
  ON leave_request (user_id, start_date, end_date)
  WHERE status = 'approved' AND is_deleted = FALSE;
```

### 16.5. `time_log`

```sql
CREATE TABLE time_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  clinic_id UUID NOT NULL REFERENCES clinic(id) ON DELETE RESTRICT,

  user_id UUID NOT NULL REFERENCES "user"(id) ON DELETE RESTRICT,
  shift_id UUID REFERENCES shift(id) ON DELETE SET NULL,

  check_in_at TIMESTAMPTZ NOT NULL,
  check_out_at TIMESTAMPTZ,
  check_in_method VARCHAR(20) NOT NULL DEFAULT 'manual',
  check_in_location VARCHAR(200),
  notes TEXT,

  is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
  deleted_at TIMESTAMPTZ,
  deleted_by UUID,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  created_by UUID,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_by UUID,
  version INTEGER NOT NULL DEFAULT 1,

  CONSTRAINT ck_time_log_method CHECK (
    check_in_method IN ('manual', 'pin', 'qr', 'biometric')
  ),
  CONSTRAINT ck_time_log_times CHECK (
    check_out_at IS NULL OR check_out_at > check_in_at
  )
);

CREATE INDEX ix_time_log_user_check_in
  ON time_log (user_id, check_in_at DESC)
  WHERE is_deleted = FALSE;

CREATE INDEX ix_time_log_clinic_period
  ON time_log (clinic_id, check_in_at DESC)
  WHERE is_deleted = FALSE;

-- Open time log (chưa check-out)
CREATE INDEX ix_time_log_open
  ON time_log (user_id)
  WHERE check_out_at IS NULL AND is_deleted = FALSE;
```

---

## 17. Notification & Audit tables

### 17.1. `notification`

```sql
CREATE TABLE notification (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  clinic_id UUID NOT NULL REFERENCES clinic(id) ON DELETE RESTRICT,

  user_id UUID NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
  type VARCHAR(50) NOT NULL,
  title VARCHAR(200) NOT NULL,
  body TEXT NOT NULL,

  reference_type VARCHAR(50),
  reference_id UUID,

  is_read BOOLEAN NOT NULL DEFAULT FALSE,
  read_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_notification_user_unread
  ON notification (user_id, created_at DESC)
  WHERE is_read = FALSE;

CREATE INDEX ix_notification_user_all
  ON notification (user_id, created_at DESC);

-- Cleanup old notifications: cron xóa is_read = TRUE older than 30 days
```

### 17.2. `audit_log` (append-only, không soft delete)

```sql
CREATE TABLE audit_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  clinic_id UUID REFERENCES clinic(id) ON DELETE SET NULL,
  user_id UUID,

  action VARCHAR(50) NOT NULL,
  entity_type VARCHAR(100) NOT NULL,
  entity_id UUID NOT NULL,

  old_data JSONB,
  new_data JSONB,
  changed_fields VARCHAR[],

  ip_address VARCHAR(45),
  user_agent VARCHAR(500),

  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  CONSTRAINT ck_audit_action CHECK (
    action IN (
      'create', 'update', 'delete', 'view',
      'login', 'logout', 'failed_login',
      'merge', 'void', 'refund', 'dispense', 'reserve',
      'transition', 'export', 'print', 'substitute_batch'
    )
  )
);

-- Partition theo tháng (optional, khi data lớn)
-- CREATE TABLE audit_log PARTITION BY RANGE (created_at);
-- CREATE TABLE audit_log_2026_04 PARTITION OF audit_log
--   FOR VALUES FROM ('2026-04-01') TO ('2026-05-01');

CREATE INDEX ix_audit_clinic_time ON audit_log (clinic_id, created_at DESC);
CREATE INDEX ix_audit_user_time ON audit_log (user_id, created_at DESC);
CREATE INDEX ix_audit_entity ON audit_log (entity_type, entity_id, created_at DESC);
CREATE INDEX ix_audit_action_time ON audit_log (action, created_at DESC);

COMMENT ON TABLE audit_log IS
  'Append-only log mọi thao tác. KHÔNG soft delete, KHÔNG update. Chỉ INSERT.';
```

---

## 18. Row-Level Security policies

### 18.1. Bật RLS

Bật RLS cho **tất cả bảng có cột `clinic_id`**:

```sql
-- Identity
ALTER TABLE "user" ENABLE ROW LEVEL SECURITY;
ALTER TABLE role ENABLE ROW LEVEL SECURITY;

-- Patient
ALTER TABLE patient ENABLE ROW LEVEL SECURITY;
ALTER TABLE patient_relation ENABLE ROW LEVEL SECURITY;

-- Workflow
ALTER TABLE appointment ENABLE ROW LEVEL SECURITY;
ALTER TABLE visit ENABLE ROW LEVEL SECURITY;
ALTER TABLE visit_service ENABLE ROW LEVEL SECURITY;

-- Vitals
ALTER TABLE vital_field_definition ENABLE ROW LEVEL SECURITY;
ALTER TABLE vital_schema_version ENABLE ROW LEVEL SECURITY;
ALTER TABLE visit_vitals ENABLE ROW LEVEL SECURITY;

-- Service
ALTER TABLE service ENABLE ROW LEVEL SECURITY;

-- Inventory
ALTER TABLE medicine ENABLE ROW LEVEL SECURITY;
ALTER TABLE supplier ENABLE ROW LEVEL SECURITY;
ALTER TABLE inventory_item ENABLE ROW LEVEL SECURITY;
ALTER TABLE batch ENABLE ROW LEVEL SECURITY;
ALTER TABLE stock_movement ENABLE ROW LEVEL SECURITY;

-- Prescription
ALTER TABLE prescription ENABLE ROW LEVEL SECURITY;
ALTER TABLE prescription_item ENABLE ROW LEVEL SECURITY;
ALTER TABLE prescription_item_batch ENABLE ROW LEVEL SECURITY;

-- Billing
ALTER TABLE invoice ENABLE ROW LEVEL SECURITY;
ALTER TABLE invoice_item ENABLE ROW LEVEL SECURITY;
ALTER TABLE payment ENABLE ROW LEVEL SECURITY;

-- HR
ALTER TABLE shift_template ENABLE ROW LEVEL SECURITY;
ALTER TABLE shift ENABLE ROW LEVEL SECURITY;
ALTER TABLE recurring_schedule ENABLE ROW LEVEL SECURITY;
ALTER TABLE leave_request ENABLE ROW LEVEL SECURITY;
ALTER TABLE time_log ENABLE ROW LEVEL SECURITY;

-- Notification (clinic_id NOT NULL)
ALTER TABLE notification ENABLE ROW LEVEL SECURITY;

-- Audit log (clinic_id nullable, áp dụng policy đặc biệt)
ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;
```

### 18.2. Standard tenant policy

```sql
-- Template áp dụng cho mọi bảng nghiệp vụ có clinic_id NOT NULL
DO $$
DECLARE
  t TEXT;
  tables TEXT[] := ARRAY[
    'user', 'role', 'patient', 'patient_relation',
    'appointment', 'visit', 'visit_service',
    'vital_field_definition', 'vital_schema_version', 'visit_vitals',
    'service', 'medicine', 'supplier', 'inventory_item',
    'batch', 'stock_movement',
    'prescription', 'prescription_item', 'prescription_item_batch',
    'invoice', 'invoice_item', 'payment',
    'shift_template', 'shift', 'recurring_schedule',
    'leave_request', 'time_log', 'notification'
  ];
BEGIN
  FOREACH t IN ARRAY tables LOOP
    EXECUTE format($f$
      CREATE POLICY tenant_isolation ON %I
        FOR ALL
        TO cms_app
        USING (clinic_id::text = current_setting('app.current_clinic_id', true))
        WITH CHECK (clinic_id::text = current_setting('app.current_clinic_id', true));
    $f$, t);
  END LOOP;
END $$;
```

### 18.3. Special policies

#### `audit_log` — clinic_id có thể NULL

```sql
CREATE POLICY tenant_isolation ON audit_log
  FOR SELECT
  TO cms_app
  USING (
    clinic_id IS NULL  -- system events
    OR clinic_id::text = current_setting('app.current_clinic_id', true)
  );

-- Chỉ INSERT, không UPDATE/DELETE
CREATE POLICY audit_insert_only ON audit_log
  FOR INSERT
  TO cms_app
  WITH CHECK (true);

-- Không cho UPDATE/DELETE: bằng cách KHÔNG tạo policy cho UPDATE và DELETE
-- Khi RLS bật và không có policy, mặc định BLOCK
```

#### `role` cho system roles (clinic_id NULL)

```sql
DROP POLICY tenant_isolation ON role;

CREATE POLICY tenant_isolation_or_system ON role
  FOR SELECT
  TO cms_app
  USING (
    clinic_id IS NULL  -- system roles visible cho mọi tenant
    OR clinic_id::text = current_setting('app.current_clinic_id', true)
  );

CREATE POLICY tenant_modify ON role
  FOR INSERT
  TO cms_app
  WITH CHECK (clinic_id::text = current_setting('app.current_clinic_id', true));

CREATE POLICY tenant_update ON role
  FOR UPDATE
  TO cms_app
  USING (clinic_id::text = current_setting('app.current_clinic_id', true))
  WITH CHECK (clinic_id::text = current_setting('app.current_clinic_id', true));

CREATE POLICY tenant_delete ON role
  FOR DELETE
  TO cms_app
  USING (clinic_id::text = current_setting('app.current_clinic_id', true));
```

#### `clinic` table — chỉ thấy clinic của mình

```sql
ALTER TABLE clinic ENABLE ROW LEVEL SECURITY;

CREATE POLICY clinic_self_only ON clinic
  FOR ALL
  TO cms_app
  USING (id::text = current_setting('app.current_clinic_id', true))
  WITH CHECK (id::text = current_setting('app.current_clinic_id', true));
```

#### `clinic_settings`

```sql
ALTER TABLE clinic_settings ENABLE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON clinic_settings
  FOR ALL
  TO cms_app
  USING (clinic_id::text = current_setting('app.current_clinic_id', true))
  WITH CHECK (clinic_id::text = current_setting('app.current_clinic_id', true));
```

### 18.4. Junction tables (không có clinic_id)

```sql
-- role_permission: visible nếu có thể access role
ALTER TABLE role_permission ENABLE ROW LEVEL SECURITY;

CREATE POLICY role_permission_access ON role_permission
  FOR ALL
  TO cms_app
  USING (
    EXISTS (
      SELECT 1 FROM role r
      WHERE r.id = role_permission.role_id
        AND (
          r.clinic_id IS NULL
          OR r.clinic_id::text = current_setting('app.current_clinic_id', true)
        )
    )
  );

-- user_role
ALTER TABLE user_role ENABLE ROW LEVEL SECURITY;

CREATE POLICY user_role_access ON user_role
  FOR ALL
  TO cms_app
  USING (
    EXISTS (
      SELECT 1 FROM "user" u
      WHERE u.id = user_role.user_id
        AND u.clinic_id::text = current_setting('app.current_clinic_id', true)
    )
  );

-- user_extra_permission
ALTER TABLE user_extra_permission ENABLE ROW LEVEL SECURITY;

CREATE POLICY user_extra_permission_access ON user_extra_permission
  FOR ALL
  TO cms_app
  USING (
    EXISTS (
      SELECT 1 FROM "user" u
      WHERE u.id = user_extra_permission.user_id
        AND u.clinic_id::text = current_setting('app.current_clinic_id', true)
    )
  );
```

### 18.5. Bypass cho migration / superuser

```sql
-- cms_migrator có BYPASSRLS attribute (set khi create role)
-- Không cần policy đặc biệt, đã bypass tự động

-- Postgres superuser cũng tự bypass RLS
```

---

## 19. Triggers

### 19.1. Auto update `updated_at` + `version`

```sql
-- Áp dụng cho mọi bảng nghiệp vụ
DO $$
DECLARE
  t TEXT;
  tables TEXT[] := ARRAY[
    'clinic', 'user', 'role',
    'patient', 'patient_relation',
    'appointment', 'visit', 'visit_service',
    'vital_field_definition', 'visit_vitals',
    'service',
    'medicine', 'supplier', 'inventory_item', 'batch',
    'prescription', 'prescription_item', 'prescription_item_batch',
    'invoice', 'invoice_item', 'payment',
    'shift_template', 'shift', 'recurring_schedule', 'leave_request', 'time_log'
  ];
BEGIN
  FOREACH t IN ARRAY tables LOOP
    EXECUTE format($f$
      CREATE TRIGGER tg_%s_audit
        BEFORE UPDATE ON %I
        FOR EACH ROW
        EXECUTE FUNCTION fn_update_audit_columns();
    $f$, t, t);
  END LOOP;
END $$;
```

### 19.2. Prevent UPDATE/DELETE trên `audit_log` và `stock_movement`

```sql
CREATE OR REPLACE FUNCTION fn_prevent_modification()
RETURNS TRIGGER AS $$
BEGIN
  RAISE EXCEPTION 'Table % is append-only. % is not allowed.',
    TG_TABLE_NAME, TG_OP;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tg_audit_log_no_update
  BEFORE UPDATE OR DELETE ON audit_log
  FOR EACH ROW
  EXECUTE FUNCTION fn_prevent_modification();

CREATE TRIGGER tg_stock_movement_no_update
  BEFORE UPDATE OR DELETE ON stock_movement
  FOR EACH ROW
  EXECUTE FUNCTION fn_prevent_modification();
```

### 19.3. Auto-update Invoice status

```sql
CREATE OR REPLACE FUNCTION fn_invoice_recalculate_status()
RETURNS TRIGGER AS $$
DECLARE
  v_total_paid NUMERIC(15, 2);
BEGIN
  -- Tính tổng paid từ payments chưa xóa và không refund
  SELECT COALESCE(SUM(amount), 0)
    INTO v_total_paid
    FROM payment
   WHERE invoice_id = COALESCE(NEW.invoice_id, OLD.invoice_id)
     AND is_deleted = FALSE
     AND is_refund = FALSE;

  -- Update invoice
  UPDATE invoice
     SET paid_amount = v_total_paid,
         status = CASE
           WHEN status IN ('cancelled', 'refunded') THEN status
           WHEN v_total_paid >= total_amount THEN 'paid'
           WHEN v_total_paid > 0 THEN 'partially_paid'
           ELSE 'pending'
         END,
         paid_at = CASE
           WHEN v_total_paid >= total_amount AND paid_at IS NULL THEN NOW()
           ELSE paid_at
         END
   WHERE id = COALESCE(NEW.invoice_id, OLD.invoice_id);

  RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tg_payment_update_invoice
  AFTER INSERT OR UPDATE OR DELETE ON payment
  FOR EACH ROW
  EXECUTE FUNCTION fn_invoice_recalculate_status();
```

### 19.4. Visit number auto-generate

```sql
CREATE OR REPLACE FUNCTION fn_visit_set_number()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.visit_number IS NULL OR NEW.visit_number = '' THEN
    NEW.visit_number := fn_next_visit_number(NEW.clinic_id, NEW.check_in_at::DATE);
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tg_visit_set_number
  BEFORE INSERT ON visit
  FOR EACH ROW
  EXECUTE FUNCTION fn_visit_set_number();
```

### 19.5. Patient code auto-generate

```sql
CREATE OR REPLACE FUNCTION fn_patient_set_code()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.patient_code IS NULL OR NEW.patient_code = '' THEN
    NEW.patient_code := fn_next_patient_code(NEW.clinic_id);
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tg_patient_set_code
  BEFORE INSERT ON patient
  FOR EACH ROW
  EXECUTE FUNCTION fn_patient_set_code();
```

### 19.6. Soft delete consistency

```sql
CREATE OR REPLACE FUNCTION fn_soft_delete_check()
RETURNS TRIGGER AS $$
BEGIN
  -- Khi is_deleted chuyển từ FALSE → TRUE
  IF NEW.is_deleted = TRUE AND OLD.is_deleted = FALSE THEN
    NEW.deleted_at := NOW();
    -- deleted_by app phải set
  END IF;

  -- Khi is_deleted chuyển TRUE → FALSE (restore)
  IF NEW.is_deleted = FALSE AND OLD.is_deleted = TRUE THEN
    NEW.deleted_at := NULL;
    NEW.deleted_by := NULL;
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply cho mọi bảng có soft delete
DO $$
DECLARE
  t TEXT;
  tables TEXT[] := ARRAY[
    'clinic', 'user', 'role', 'patient', 'patient_relation',
    'appointment', 'visit', 'visit_service',
    'vital_field_definition', 'visit_vitals',
    'service', 'medicine', 'supplier', 'inventory_item', 'batch',
    'prescription', 'prescription_item', 'prescription_item_batch',
    'invoice', 'invoice_item', 'payment',
    'shift_template', 'shift', 'recurring_schedule', 'leave_request', 'time_log'
  ];
BEGIN
  FOREACH t IN ARRAY tables LOOP
    EXECUTE format($f$
      CREATE TRIGGER tg_%s_soft_delete
        BEFORE UPDATE ON %I
        FOR EACH ROW
        WHEN (NEW.is_deleted IS DISTINCT FROM OLD.is_deleted)
        EXECUTE FUNCTION fn_soft_delete_check();
    $f$, t, t);
  END LOOP;
END $$;
```

### 19.7. Batch reserved_quantity sanity

```sql
CREATE OR REPLACE FUNCTION fn_batch_reserved_check()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.reserved_quantity > NEW.actual_quantity THEN
    RAISE EXCEPTION
      'Reserved quantity (%) cannot exceed actual quantity (%)',
      NEW.reserved_quantity, NEW.actual_quantity;
  END IF;
  IF NEW.reserved_quantity < 0 OR NEW.actual_quantity < 0 THEN
    RAISE EXCEPTION 'Quantities must be non-negative';
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tg_batch_reserved_check
  BEFORE INSERT OR UPDATE ON batch
  FOR EACH ROW
  EXECUTE FUNCTION fn_batch_reserved_check();
```

---

## 20. Views

### 20.1. `v_active_queue` — Queue hiện tại

```sql
CREATE OR REPLACE VIEW v_active_queue AS
SELECT
  v.id AS visit_id,
  v.clinic_id,
  v.visit_number,
  v.priority,
  v.is_returning,
  v.check_in_at,
  v.assigned_doctor_id,
  v.chief_complaint,
  p.id AS patient_id,
  p.patient_code,
  p.full_name AS patient_name,
  p.gender,
  p.date_of_birth,
  p.birth_year,
  -- Tính tuổi
  CASE
    WHEN p.date_of_birth IS NOT NULL THEN
      EXTRACT(YEAR FROM AGE(p.date_of_birth))
    WHEN p.birth_year IS NOT NULL THEN
      EXTRACT(YEAR FROM CURRENT_DATE) - p.birth_year
  END AS age,
  -- Có vitals chưa
  EXISTS(
    SELECT 1 FROM visit_vitals vv
     WHERE vv.visit_id = v.id AND vv.is_deleted = FALSE
  ) AS has_vitals,
  -- Đã chờ bao lâu (phút)
  EXTRACT(EPOCH FROM (NOW() - v.check_in_at)) / 60 AS waiting_minutes
FROM visit v
JOIN patient p ON p.id = v.patient_id
WHERE v.status = 'WAITING'
  AND v.is_deleted = FALSE
ORDER BY
  v.priority DESC,
  v.is_returning DESC,
  v.check_in_at ASC;
```

### 20.2. `v_inventory_status` — Tồn kho hiện tại

```sql
CREATE OR REPLACE VIEW v_inventory_status AS
SELECT
  ii.clinic_id,
  ii.id AS inventory_item_id,
  m.id AS medicine_id,
  m.code AS medicine_code,
  m.name AS medicine_name,
  m.strength,
  m.base_unit,
  ii.default_sale_price,
  ii.reorder_point,
  ii.location,
  -- Aggregate từ batches
  COALESCE(SUM(b.actual_quantity), 0) AS total_actual,
  COALESCE(SUM(b.reserved_quantity), 0) AS total_reserved,
  COALESCE(SUM(b.actual_quantity - b.reserved_quantity), 0) AS total_available,
  -- Lô gần hết hạn nhất
  MIN(b.expiry_date) FILTER (
    WHERE b.actual_quantity > 0 AND b.is_recalled = FALSE AND b.is_deleted = FALSE
  ) AS earliest_expiry,
  -- Số lô đang có
  COUNT(b.id) FILTER (
    WHERE b.actual_quantity > 0 AND b.is_recalled = FALSE AND b.is_deleted = FALSE
  ) AS active_batch_count,
  -- Cảnh báo
  CASE
    WHEN ii.reorder_point IS NOT NULL
      AND COALESCE(SUM(b.actual_quantity - b.reserved_quantity), 0) <= ii.reorder_point
    THEN TRUE ELSE FALSE
  END AS is_low_stock
FROM inventory_item ii
JOIN medicine m ON m.id = ii.medicine_id
LEFT JOIN batch b
  ON b.inventory_item_id = ii.id
 AND b.is_deleted = FALSE
 AND b.expiry_date >= CURRENT_DATE
WHERE ii.is_deleted = FALSE
  AND ii.is_active = TRUE
  AND m.is_deleted = FALSE
GROUP BY ii.id, m.id;
```

### 20.3. `v_daily_revenue` — Doanh thu theo ngày

```sql
CREATE OR REPLACE VIEW v_daily_revenue AS
SELECT
  i.clinic_id,
  DATE(i.paid_at AT TIME ZONE 'Asia/Ho_Chi_Minh') AS revenue_date,
  COUNT(*) AS invoice_count,
  COUNT(DISTINCT i.patient_id) AS unique_patients,
  SUM(i.subtotal) AS total_subtotal,
  SUM(i.total_discount) AS total_discount,
  SUM(i.total_amount) AS total_revenue,
  -- Breakdown theo loại item
  SUM(
    (SELECT COALESCE(SUM(ii.total), 0)
       FROM invoice_item ii
      WHERE ii.invoice_id = i.id
        AND ii.item_type = 'service'
        AND ii.is_deleted = FALSE)
  ) AS service_revenue,
  SUM(
    (SELECT COALESCE(SUM(ii.total), 0)
       FROM invoice_item ii
      WHERE ii.invoice_id = i.id
        AND ii.item_type = 'medicine'
        AND ii.is_deleted = FALSE)
  ) AS medicine_revenue
FROM invoice i
WHERE i.status = 'paid'
  AND i.is_deleted = FALSE
GROUP BY i.clinic_id, DATE(i.paid_at AT TIME ZONE 'Asia/Ho_Chi_Minh');
```

### 20.4. `v_doctor_performance` — Hiệu suất bác sĩ

```sql
CREATE OR REPLACE VIEW v_doctor_performance AS
SELECT
  v.clinic_id,
  v.doctor_id,
  u.full_name AS doctor_name,
  DATE(v.consultation_started_at AT TIME ZONE 'Asia/Ho_Chi_Minh') AS work_date,
  COUNT(DISTINCT v.id) AS visits_completed,
  COUNT(DISTINCT v.patient_id) AS unique_patients,
  AVG(EXTRACT(EPOCH FROM (v.consultation_ended_at - v.consultation_started_at)) / 60)
    AS avg_consultation_minutes,
  SUM(
    (SELECT COALESCE(SUM(vs.total_amount), 0)
       FROM visit_service vs
      WHERE vs.visit_id = v.id
        AND vs.is_deleted = FALSE)
  ) AS service_revenue
FROM visit v
JOIN "user" u ON u.id = v.doctor_id
WHERE v.status IN ('COMPLETED', 'AWAITING_PAYMENT')
  AND v.is_deleted = FALSE
  AND v.doctor_id IS NOT NULL
  AND v.consultation_started_at IS NOT NULL
GROUP BY v.clinic_id, v.doctor_id, u.full_name,
         DATE(v.consultation_started_at AT TIME ZONE 'Asia/Ho_Chi_Minh');
```

### 20.5. `v_outstanding_invoices` — Công nợ

```sql
CREATE OR REPLACE VIEW v_outstanding_invoices AS
SELECT
  i.clinic_id,
  i.id AS invoice_id,
  i.invoice_number,
  i.issued_at,
  i.total_amount,
  i.paid_amount,
  i.total_amount - i.paid_amount AS balance,
  i.status,
  EXTRACT(DAY FROM NOW() - i.issued_at)::INT AS days_outstanding,
  p.id AS patient_id,
  p.patient_code,
  p.full_name AS patient_name,
  p.phone AS patient_phone
FROM invoice i
JOIN patient p ON p.id = i.patient_id
WHERE i.status IN ('pending', 'partially_paid')
  AND i.is_deleted = FALSE
ORDER BY i.issued_at ASC;
```

---

## 21. Indexes — Tổng kết

### 21.1. Index strategy

| Loại | Khi dùng | Ví dụ |
|---|---|---|
| **B-tree** | Equality, range, sort | Mọi lookup thường |
| **Partial** | Filter có điều kiện cố định | `WHERE is_deleted = FALSE` |
| **GIN (jsonb_path_ops)** | JSONB containment | `values @> '{"systolic_bp": 120}'` |
| **GIN (to_tsvector)** | Full text search | Tên bệnh nhân, thuốc |
| **GIN (gin_trgm_ops)** | Fuzzy search | `name ILIKE '%abc%'` |
| **B-tree composite** | Multi-column query, sort | Queue order |

### 21.2. Hot path indexes (critical)

| Bảng | Index | Lý do |
|---|---|---|
| `visit` | `ix_visit_queue` (priority DESC, is_returning DESC, check_in_at ASC) | Mọi lần load queue |
| `batch` | `ix_batch_fefo` (clinic_id, item_id, expiry, received) | Mọi lần kê đơn in_house |
| `appointment` | `ix_appointment_clinic_time_active` | Capacity check khi đặt lịch |
| `patient` | `ix_patient_clinic_phone` | Tra cứu lễ tân |
| `prescription` | `ix_prescription_pharmacy_queue` | Dược sĩ load queue |

### 21.3. Tổng số indexes per bảng (ước tính)

| Bảng | Indexes | Note |
|---|---|---|
| `patient` | 6 | Phone, name FTS, name trgm, code unique, id_number |
| `visit` | 5 | Queue, doctor, patient, time, status |
| `batch` | 4 | FEFO, expiry, item, batch_number |
| `appointment` | 5 | Time, patient, doctor, no-show, reminder |
| `medicine` | 4 | Code, name FTS, name trgm, active |
| `invoice` | 5 | Number, visit, status, revenue, outstanding |

---

## 22. Migration order

### 22.1. Thứ tự tạo bảng (dependency order)

```
0001  CREATE EXTENSION (uuid-ossp, pgcrypto, unaccent, pg_trgm, btree_gin)
0002  CREATE FUNCTION fn_update_audit_columns(), fn_check_version(), ...
0003  CREATE TABLE clinic
0004  CREATE TABLE clinic_settings
0005  CREATE TABLE permission, role, role_permission
0006  CREATE TABLE "user", user_role, user_extra_permission
0007  CREATE TABLE patient, patient_relation
0008  CREATE TABLE appointment
0009  CREATE TABLE visit
0010  CREATE TABLE system_vital_preset, vital_field_definition,
                   vital_schema_version, visit_vitals
0011  CREATE TABLE service, visit_service
0012  CREATE TABLE medicine, supplier, inventory_item, batch
0013  CREATE TABLE stock_movement
0014  CREATE TABLE prescription, prescription_item, prescription_item_batch
0015  CREATE TABLE invoice, invoice_item, payment
0016  CREATE TABLE shift_template, shift, recurring_schedule,
                   leave_request, time_log
0017  CREATE TABLE notification
0018  CREATE TABLE audit_log
0019  CREATE FUNCTIONS (fn_next_patient_code, fn_next_visit_number, ...)
0020  CREATE TRIGGERS (audit, soft_delete, append-only, invoice recalc)
0021  CREATE VIEWS (v_active_queue, v_inventory_status, ...)
0022  ENABLE RLS + CREATE POLICIES (mọi bảng)
0023  GRANT permissions cho cms_app, cms_readonly
0024  SEED system_vital_preset, permission, default roles
```

### 22.2. Quy tắc khi viết migration

- **Forward-only:** không dùng `downgrade` ở production.
- **Atomic:** mỗi migration làm 1 việc, để rollback dễ revert bằng migration mới.
- **Backward-compatible:** thêm column nullable trước, backfill, rồi mới NOT NULL.
- **Schema vs Data:** tách riêng — migration cho schema, script Python cho data.
- **Test trước:** chạy migration trên staging với data thật trước khi production.
- **Lock-free:** dùng `CREATE INDEX CONCURRENTLY` cho index trên bảng lớn.

### 22.3. Migration template

```python
# alembic/versions/0009_create_visit.py

"""Create visit table

Revision ID: 0009
Revises: 0008
Create Date: 2026-04-26 ...
"""

from alembic import op
import sqlalchemy as sa


revision = '0009'
down_revision = '0008'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE visit (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            clinic_id UUID NOT NULL REFERENCES clinic(id) ON DELETE RESTRICT,
            -- ... full DDL
        );
    """)

    op.execute("""
        CREATE UNIQUE INDEX uq_visit_clinic_number
          ON visit (clinic_id, visit_number)
          WHERE is_deleted = FALSE;
    """)

    # ... other indexes


def downgrade():
    # Forward-only: chỉ cho dev environment
    op.execute("DROP TABLE IF EXISTS visit CASCADE;")
```

---

## 23. Seed data

### 23.1. Permissions

```sql
INSERT INTO permission (code, name, description, category) VALUES
-- Patient
('patient.read', 'Xem bệnh nhân', 'Xem hồ sơ bệnh nhân', 'patient'),
('patient.write', 'Tạo/sửa bệnh nhân', 'Tạo và sửa hồ sơ', 'patient'),
('patient.merge', 'Merge hồ sơ', 'Merge hồ sơ trùng lặp', 'patient'),
('patient.delete', 'Xóa bệnh nhân', 'Soft delete hồ sơ', 'patient'),

-- Visit
('visit.read', 'Xem lượt khám', NULL, 'visit'),
('visit.write', 'Tạo lượt khám', NULL, 'visit'),
('visit.cancel', 'Hủy lượt khám', NULL, 'visit'),

-- Vitals
('vital.read', 'Xem vitals', NULL, 'vital'),
('vital.write', 'Nhập vitals', NULL, 'vital'),
('vital.delete', 'Xóa vitals', NULL, 'vital'),
('vital.schema_manage', 'Quản lý vital schema', 'Cấu hình field động', 'vital'),

-- Service
('service.catalog_manage', 'Quản lý service catalog', NULL, 'service'),
('service.perform', 'Thực hiện service', 'Thêm service vào visit', 'service'),

-- Prescription
('prescription.write', 'Kê đơn thuốc', NULL, 'prescription'),
('prescription.cancel', 'Hủy đơn thuốc', NULL, 'prescription'),

-- Pharmacy
('pharmacy.dispense', 'Cấp phát thuốc', NULL, 'pharmacy'),
('pharmacy.substitute_batch', 'Thay batch khi cấp phát', NULL, 'pharmacy'),
('pharmacy.adjust_stock', 'Điều chỉnh tồn kho', NULL, 'pharmacy'),

-- Inventory
('inventory.read', 'Xem kho', NULL, 'inventory'),
('inventory.manage_catalog', 'Quản lý catalog thuốc', NULL, 'inventory'),
('inventory.purchase_in', 'Nhập kho', NULL, 'inventory'),

-- Billing
('invoice.create', 'Tạo hóa đơn', NULL, 'billing'),
('invoice.modify', 'Sửa hóa đơn', NULL, 'billing'),
('invoice.void', 'Hủy hóa đơn', NULL, 'billing'),
('invoice.refund', 'Hoàn tiền', NULL, 'billing'),
('payment.receive', 'Nhận thanh toán', NULL, 'billing'),

-- HR
('shift.manage', 'Quản lý ca trực', NULL, 'hr'),
('attendance.manage', 'Quản lý chấm công', NULL, 'hr'),
('leave.approve', 'Duyệt nghỉ phép', NULL, 'hr'),

-- Users
('user.manage', 'Quản lý nhân viên', NULL, 'admin'),
('role.manage', 'Quản lý roles', NULL, 'admin'),

-- Reports
('report.view', 'Xem báo cáo', NULL, 'report'),
('report.financial', 'Xem báo cáo tài chính', NULL, 'report'),

-- Settings
('settings.clinic', 'Cấu hình clinic', NULL, 'settings'),
('settings.vital_schema', 'Cấu hình vital schema', NULL, 'settings');
```

### 23.2. System roles + role_permission

```sql
-- Tạo system roles (clinic_id = NULL)
INSERT INTO role (id, clinic_id, code, name, description, is_system) VALUES
  ('11111111-1111-1111-1111-111111111111', NULL, 'admin', 'Quản trị viên', 'Toàn quyền', TRUE),
  ('22222222-2222-2222-2222-222222222222', NULL, 'doctor', 'Bác sĩ', NULL, TRUE),
  ('33333333-3333-3333-3333-333333333333', NULL, 'nurse', 'Y tá', NULL, TRUE),
  ('44444444-4444-4444-4444-444444444444', NULL, 'pharmacist', 'Dược sĩ', NULL, TRUE),
  ('55555555-5555-5555-5555-555555555555', NULL, 'receptionist', 'Lễ tân', NULL, TRUE);

-- Admin: tất cả permissions
INSERT INTO role_permission (role_id, permission_code)
SELECT '11111111-1111-1111-1111-111111111111', code FROM permission;

-- Doctor
INSERT INTO role_permission (role_id, permission_code) VALUES
  ('22222222-2222-2222-2222-222222222222', 'patient.read'),
  ('22222222-2222-2222-2222-222222222222', 'patient.write'),
  ('22222222-2222-2222-2222-222222222222', 'visit.read'),
  ('22222222-2222-2222-2222-222222222222', 'visit.write'),
  ('22222222-2222-2222-2222-222222222222', 'vital.read'),
  ('22222222-2222-2222-2222-222222222222', 'vital.write'),
  ('22222222-2222-2222-2222-222222222222', 'service.perform'),
  ('22222222-2222-2222-2222-222222222222', 'prescription.write'),
  ('22222222-2222-2222-2222-222222222222', 'prescription.cancel'),
  ('22222222-2222-2222-2222-222222222222', 'inventory.read'),
  ('22222222-2222-2222-2222-222222222222', 'report.view');

-- Nurse
INSERT INTO role_permission (role_id, permission_code) VALUES
  ('33333333-3333-3333-3333-333333333333', 'patient.read'),
  ('33333333-3333-3333-3333-333333333333', 'patient.write'),
  ('33333333-3333-3333-3333-333333333333', 'visit.read'),
  ('33333333-3333-3333-3333-333333333333', 'visit.write'),
  ('33333333-3333-3333-3333-333333333333', 'vital.read'),
  ('33333333-3333-3333-3333-333333333333', 'vital.write'),
  ('33333333-3333-3333-3333-333333333333', 'service.perform');

-- Pharmacist
INSERT INTO role_permission (role_id, permission_code) VALUES
  ('44444444-4444-4444-4444-444444444444', 'patient.read'),
  ('44444444-4444-4444-4444-444444444444', 'visit.read'),
  ('44444444-4444-4444-4444-444444444444', 'inventory.read'),
  ('44444444-4444-4444-4444-444444444444', 'inventory.manage_catalog'),
  ('44444444-4444-4444-4444-444444444444', 'inventory.purchase_in'),
  ('44444444-4444-4444-4444-444444444444', 'pharmacy.dispense'),
  ('44444444-4444-4444-4444-444444444444', 'pharmacy.substitute_batch'),
  ('44444444-4444-4444-4444-444444444444', 'pharmacy.adjust_stock');

-- Receptionist
INSERT INTO role_permission (role_id, permission_code) VALUES
  ('55555555-5555-5555-5555-555555555555', 'patient.read'),
  ('55555555-5555-5555-5555-555555555555', 'patient.write'),
  ('55555555-5555-5555-5555-555555555555', 'visit.read'),
  ('55555555-5555-5555-5555-555555555555', 'visit.write'),
  ('55555555-5555-5555-5555-555555555555', 'visit.cancel'),
  ('55555555-5555-5555-5555-555555555555', 'invoice.create'),
  ('55555555-5555-5555-5555-555555555555', 'invoice.modify'),
  ('55555555-5555-5555-5555-555555555555', 'payment.receive');
```

### 23.3. Vital presets (system_vital_preset)

```sql
-- General preset
INSERT INTO system_vital_preset (specialty_code, name, fields, is_default) VALUES
('general', 'Đa khoa', '[
  {"key":"systolic_bp","label":"Huyết áp tâm thu","data_type":"integer","unit":"mmHg","min_value":50,"max_value":250,"warning_min":90,"warning_max":140,"is_required":true,"sort_order":1,"group_name":"Sinh hiệu"},
  {"key":"diastolic_bp","label":"Huyết áp tâm trương","data_type":"integer","unit":"mmHg","min_value":30,"max_value":150,"warning_min":60,"warning_max":90,"is_required":true,"sort_order":2,"group_name":"Sinh hiệu"},
  {"key":"pulse","label":"Nhịp tim","data_type":"integer","unit":"lần/phút","min_value":30,"max_value":200,"warning_min":60,"warning_max":100,"is_required":true,"sort_order":3,"group_name":"Sinh hiệu"},
  {"key":"temperature","label":"Nhiệt độ","data_type":"number","unit":"°C","min_value":33,"max_value":43,"warning_min":36,"warning_max":37.5,"decimal_places":1,"is_required":true,"sort_order":4,"group_name":"Sinh hiệu"},
  {"key":"weight","label":"Cân nặng","data_type":"number","unit":"kg","min_value":1,"max_value":300,"decimal_places":1,"is_required":false,"sort_order":5,"group_name":"Nhân trắc"},
  {"key":"height","label":"Chiều cao","data_type":"number","unit":"cm","min_value":30,"max_value":250,"decimal_places":1,"is_required":false,"sort_order":6,"group_name":"Nhân trắc"},
  {"key":"spo2","label":"SpO2","data_type":"integer","unit":"%","min_value":50,"max_value":100,"warning_min":95,"is_required":false,"sort_order":7,"group_name":"Sinh hiệu"}
]'::jsonb, TRUE);

-- Pediatric (thêm vòng đầu)
INSERT INTO system_vital_preset (specialty_code, name, fields) VALUES
('pediatric', 'Nhi khoa', '[
  {"key":"weight","label":"Cân nặng","data_type":"number","unit":"kg","min_value":0.5,"max_value":150,"decimal_places":2,"is_required":true,"sort_order":1,"group_name":"Nhân trắc"},
  {"key":"height","label":"Chiều cao/dài","data_type":"number","unit":"cm","min_value":30,"max_value":200,"decimal_places":1,"is_required":true,"sort_order":2,"group_name":"Nhân trắc"},
  {"key":"head_circumference","label":"Vòng đầu","data_type":"number","unit":"cm","min_value":20,"max_value":60,"decimal_places":1,"is_required":false,"sort_order":3,"group_name":"Nhân trắc"},
  {"key":"temperature","label":"Nhiệt độ","data_type":"number","unit":"°C","min_value":33,"max_value":43,"decimal_places":1,"is_required":true,"sort_order":4,"group_name":"Sinh hiệu"},
  {"key":"pulse","label":"Nhịp tim","data_type":"integer","unit":"lần/phút","min_value":50,"max_value":250,"is_required":true,"sort_order":5,"group_name":"Sinh hiệu"}
]'::jsonb);

-- Obstetric (sản)
INSERT INTO system_vital_preset (specialty_code, name, fields) VALUES
('obstetric', 'Sản khoa', '[
  {"key":"systolic_bp","label":"Huyết áp tâm thu","data_type":"integer","unit":"mmHg","min_value":50,"max_value":250,"is_required":true,"sort_order":1,"group_name":"Sinh hiệu"},
  {"key":"diastolic_bp","label":"Huyết áp tâm trương","data_type":"integer","unit":"mmHg","min_value":30,"max_value":150,"is_required":true,"sort_order":2,"group_name":"Sinh hiệu"},
  {"key":"weight","label":"Cân nặng","data_type":"number","unit":"kg","min_value":30,"max_value":200,"decimal_places":1,"is_required":true,"sort_order":3,"group_name":"Nhân trắc"},
  {"key":"gestational_age_weeks","label":"Tuổi thai (tuần)","data_type":"integer","min_value":1,"max_value":45,"is_required":false,"sort_order":4,"group_name":"Sản khoa"},
  {"key":"fundal_height","label":"Chiều cao tử cung","data_type":"number","unit":"cm","min_value":0,"max_value":50,"decimal_places":1,"is_required":false,"sort_order":5,"group_name":"Sản khoa"},
  {"key":"fetal_heart_rate","label":"Nhịp tim thai","data_type":"integer","unit":"lần/phút","min_value":80,"max_value":200,"warning_min":110,"warning_max":160,"is_required":false,"sort_order":6,"group_name":"Sản khoa"}
]'::jsonb);

-- Dental (RHM)
INSERT INTO system_vital_preset (specialty_code, name, fields) VALUES
('dental', 'Răng hàm mặt', '[
  {"key":"systolic_bp","label":"Huyết áp tâm thu","data_type":"integer","unit":"mmHg","min_value":50,"max_value":250,"is_required":false,"sort_order":1},
  {"key":"diastolic_bp","label":"Huyết áp tâm trương","data_type":"integer","unit":"mmHg","min_value":30,"max_value":150,"is_required":false,"sort_order":2},
  {"key":"pulse","label":"Nhịp tim","data_type":"integer","unit":"lần/phút","min_value":30,"max_value":200,"is_required":false,"sort_order":3}
]'::jsonb);

-- Dermatology (da liễu)
INSERT INTO system_vital_preset (specialty_code, name, fields) VALUES
('dermatology', 'Da liễu', '[
  {"key":"weight","label":"Cân nặng","data_type":"number","unit":"kg","min_value":1,"max_value":300,"decimal_places":1,"is_required":true,"sort_order":1},
  {"key":"systolic_bp","label":"Huyết áp tâm thu","data_type":"integer","unit":"mmHg","min_value":50,"max_value":250,"is_required":false,"sort_order":2},
  {"key":"diastolic_bp","label":"Huyết áp tâm trương","data_type":"integer","unit":"mmHg","min_value":30,"max_value":150,"is_required":false,"sort_order":3}
]'::jsonb);
```

---

## 24. Performance & Maintenance

### 24.1. VACUUM strategy

```sql
-- Bảng có nhiều UPDATE: tăng autovacuum aggressive
ALTER TABLE batch SET (
  autovacuum_vacuum_scale_factor = 0.05,
  autovacuum_analyze_scale_factor = 0.025
);

ALTER TABLE invoice SET (
  autovacuum_vacuum_scale_factor = 0.05
);

-- Bảng append-only: ít vacuum
ALTER TABLE audit_log SET (
  autovacuum_vacuum_scale_factor = 0.2
);

ALTER TABLE stock_movement SET (
  autovacuum_vacuum_scale_factor = 0.2
);
```

### 24.2. Partitioning audit_log (khi data lớn)

```sql
-- Khi audit_log > 100M rows, partition theo tháng
CREATE TABLE audit_log_partitioned (
  LIKE audit_log INCLUDING ALL
) PARTITION BY RANGE (created_at);

-- Tạo partitions
CREATE TABLE audit_log_2026_04 PARTITION OF audit_log_partitioned
  FOR VALUES FROM ('2026-04-01') TO ('2026-05-01');

CREATE TABLE audit_log_2026_05 PARTITION OF audit_log_partitioned
  FOR VALUES FROM ('2026-05-01') TO ('2026-06-01');

-- ... tự động tạo qua cron monthly

-- Migrate data + rename
INSERT INTO audit_log_partitioned SELECT * FROM audit_log;
ALTER TABLE audit_log RENAME TO audit_log_old;
ALTER TABLE audit_log_partitioned RENAME TO audit_log;
DROP TABLE audit_log_old;
```

### 24.3. Bloat monitoring

```sql
-- Check table bloat
SELECT
  schemaname || '.' || tablename AS table_name,
  pg_size_pretty(pg_relation_size(schemaname || '.' || tablename)) AS size,
  n_dead_tup,
  n_live_tup,
  ROUND(n_dead_tup::NUMERIC / NULLIF(n_live_tup, 0) * 100, 2) AS dead_pct
FROM pg_stat_user_tables
WHERE schemaname = 'public'
ORDER BY n_dead_tup DESC;

-- Manual VACUUM nếu dead_pct > 20%
VACUUM (VERBOSE, ANALYZE) batch;
```

### 24.4. Index usage monitoring

```sql
-- Indexes không được dùng (candidate cho drop)
SELECT
  schemaname,
  tablename,
  indexname,
  idx_scan,
  pg_size_pretty(pg_relation_size(indexrelid)) AS size
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
  AND idx_scan = 0
ORDER BY pg_relation_size(indexrelid) DESC;

-- Slow queries
SELECT
  query,
  calls,
  total_exec_time / 1000 AS total_seconds,
  mean_exec_time AS avg_ms,
  rows / NULLIF(calls, 0) AS avg_rows
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 20;
```

### 24.5. Backup strategy

```bash
# Full backup hằng ngày + WAL archiving cho PITR

# Daily base backup
pg_basebackup -D /backup/base/$(date +%Y%m%d) \
              -F tar -z -P \
              -X fetch -h prod-db -U replication

# Archive WAL liên tục
# postgresql.conf:
#   archive_mode = on
#   archive_command = 'cp %p /backup/wal/%f && aws s3 cp /backup/wal/%f s3://...'

# Test restore (monthly)
pg_basebackup -D /tmp/restore_test ...
pg_ctl -D /tmp/restore_test start -o "-p 5433"
psql -h localhost -p 5433 -c "SELECT count(*) FROM patient;"
```

---

## 25. Sample queries

### 25.1. Queue hiện tại

```sql
-- Dùng view
SELECT * FROM v_active_queue
WHERE clinic_id = :cid
ORDER BY priority DESC, is_returning DESC, check_in_at ASC;
```

### 25.2. Tìm bệnh nhân (multi-criteria)

```sql
-- Theo phone
SELECT id, patient_code, full_name, phone
  FROM patient
 WHERE clinic_id = :cid
   AND is_deleted = FALSE
   AND phone = :phone
 ORDER BY created_at DESC
 LIMIT 20;

-- Theo tên (FTS với unaccent)
SELECT id, patient_code, full_name, phone
  FROM patient
 WHERE clinic_id = :cid
   AND is_deleted = FALSE
   AND to_tsvector('simple', unaccent(full_name)) @@ plainto_tsquery('simple', unaccent(:query))
 ORDER BY ts_rank(to_tsvector('simple', unaccent(full_name)), plainto_tsquery('simple', unaccent(:query))) DESC
 LIMIT 20;

-- Fuzzy (typo)
SELECT id, patient_code, full_name, similarity(full_name, :query) AS sim
  FROM patient
 WHERE clinic_id = :cid
   AND is_deleted = FALSE
   AND full_name % :query
 ORDER BY sim DESC
 LIMIT 20;
```

### 25.3. FEFO reservation

```sql
-- Lock + lấy batches available theo FEFO
SELECT id, batch_number, expiry_date, actual_quantity, reserved_quantity,
       (actual_quantity - reserved_quantity) AS available
  FROM batch
 WHERE clinic_id = :cid
   AND inventory_item_id = :iid
   AND is_deleted = FALSE
   AND is_recalled = FALSE
   AND expiry_date >= CURRENT_DATE
   AND actual_quantity > reserved_quantity
 ORDER BY expiry_date ASC, received_date ASC
   FOR UPDATE SKIP LOCKED;
```

### 25.4. Doanh thu theo ngày

```sql
SELECT * FROM v_daily_revenue
WHERE clinic_id = :cid
  AND revenue_date BETWEEN :from_date AND :to_date
ORDER BY revenue_date DESC;
```

### 25.5. Vitals trend (huyết áp 6 tháng)

```sql
SELECT
  vv.recorded_at,
  (vv.values->>'systolic_bp')::INT AS systolic,
  (vv.values->>'diastolic_bp')::INT AS diastolic,
  (vv.values->>'pulse')::INT AS pulse
FROM visit_vitals vv
JOIN visit v ON v.id = vv.visit_id
WHERE v.clinic_id = :cid
  AND v.patient_id = :pid
  AND vv.recorded_at >= NOW() - INTERVAL '6 months'
  AND vv.values ? 'systolic_bp'
  AND vv.is_deleted = FALSE
ORDER BY vv.recorded_at;
```

### 25.6. Tồn kho thấp + sắp hết hạn

```sql
-- Low stock
SELECT * FROM v_inventory_status
WHERE clinic_id = :cid
  AND is_low_stock = TRUE
ORDER BY total_available ASC;

-- Sắp hết hạn (90 ngày)
SELECT * FROM v_inventory_status
WHERE clinic_id = :cid
  AND earliest_expiry <= CURRENT_DATE + INTERVAL '90 days'
  AND total_actual > 0
ORDER BY earliest_expiry ASC;
```

### 25.7. Top dịch vụ doanh thu cao

```sql
SELECT
  s.id,
  s.code,
  s.name,
  COUNT(vs.id) AS times_performed,
  SUM(vs.total_amount) AS total_revenue,
  AVG(vs.unit_price) AS avg_price
FROM service s
JOIN visit_service vs ON vs.service_id = s.id
WHERE vs.clinic_id = :cid
  AND vs.status = 'completed'
  AND vs.is_deleted = FALSE
  AND vs.created_at BETWEEN :from_date AND :to_date
GROUP BY s.id, s.code, s.name
ORDER BY total_revenue DESC
LIMIT 20;
```

### 25.8. Capacity check một slot

```sql
-- Doctors on shift trong slot 9:00-9:30 ngày 26/04
WITH doctors_count AS (
  SELECT COUNT(DISTINCT s.user_id) AS n
    FROM shift s
    JOIN user_role ur ON ur.user_id = s.user_id
    JOIN role r ON r.id = ur.role_id
   WHERE s.clinic_id = :cid
     AND s.shift_date = :date
     AND s.start_time <= :slot_start
     AND s.end_time >= :slot_end
     AND s.status = 'scheduled'
     AND s.is_deleted = FALSE
     AND r.code = 'doctor'
),
booked AS (
  SELECT COUNT(*) AS n
    FROM appointment
   WHERE clinic_id = :cid
     AND scheduled_at >= :slot_start_ts
     AND scheduled_at < :slot_end_ts
     AND status IN ('scheduled', 'confirmed', 'checked_in')
     AND is_deleted = FALSE
)
SELECT
  doctors_count.n AS doctors_available,
  booked.n AS already_booked,
  GREATEST(doctors_count.n - booked.n, 0) AS slots_available
FROM doctors_count, booked;
```

### 25.9. Audit trail của 1 entity

```sql
SELECT
  al.id,
  al.action,
  al.created_at,
  u.full_name AS performed_by_name,
  al.changed_fields,
  al.old_data,
  al.new_data
FROM audit_log al
LEFT JOIN "user" u ON u.id = al.user_id
WHERE al.entity_type = :entity_type
  AND al.entity_id = :entity_id
ORDER BY al.created_at DESC;
```

### 25.10. Stock movement của 1 batch

```sql
SELECT
  sm.performed_at,
  sm.movement_type,
  sm.quantity_delta,
  sm.quantity_before,
  sm.quantity_after,
  sm.reference_type,
  sm.reference_id,
  sm.reason,
  u.full_name AS performed_by
FROM stock_movement sm
LEFT JOIN "user" u ON u.id = sm.performed_by
WHERE sm.batch_id = :batch_id
ORDER BY sm.performed_at DESC;
```

---

## 26. Data dictionary

### 26.1. Per-table summary

| Bảng | Mô tả | Số cột chính | Estimated rows (1 yr, medium clinic) |
|---|---|---|---|
| `clinic` | Tenant | 8 | 1 |
| `clinic_settings` | Settings JSONB | 2 | 1 |
| `user` | Nhân viên | 11 | 5-15 |
| `role` | Vai trò | 5 | 5-10 |
| `permission` | System catalog | 4 | ~40 |
| `role_permission` | M2M | 2 | ~200 |
| `user_role` | M2M | 4 | 5-30 |
| `user_extra_permission` | Override | 5 | 0-20 |
| `patient` | Hồ sơ | 21 | 5K-50K |
| `patient_relation` | Quan hệ | 4 | 100-1K |
| `appointment` | Lịch hẹn | 11 | 10K-100K |
| `visit` | Lượt khám | 14 | 15K-150K |
| `visit_service` | Dịch vụ trong visit | 11 | 30K-500K |
| `system_vital_preset` | Master | 5 | 5-10 |
| `vital_field_definition` | Định nghĩa field | 16 | 10-30 per clinic |
| `vital_schema_version` | Snapshot | 6 | 5-50 per clinic |
| `visit_vitals` | Bản ghi đo | 8 | 15K-150K |
| `service` | Catalog | 9 | 50-300 |
| `medicine` | Catalog | 16 | 200-2K |
| `supplier` | Nhà cung cấp | 8 | 5-50 |
| `inventory_item` | Item trong kho | 8 | 200-2K |
| `batch` | Lô | 13 | 1K-10K |
| `stock_movement` | Movement log | 10 | 10K-100K |
| `prescription` | Đơn thuốc | 9 | 10K-100K |
| `prescription_item` | Item đơn | 14 | 30K-500K |
| `prescription_item_batch` | Reservation | 8 | 30K-500K |
| `invoice` | Hóa đơn | 16 | 15K-150K |
| `invoice_item` | Item hóa đơn | 12 | 50K-1M |
| `payment` | Thanh toán | 11 | 15K-200K |
| `shift_template` | Mẫu ca | 6 | 3-10 |
| `shift` | Ca cụ thể | 9 | 1K-5K |
| `recurring_schedule` | Lịch lặp | 8 | 5-30 |
| `leave_request` | Xin nghỉ | 10 | 50-500 |
| `time_log` | Chấm công | 8 | 1K-5K |
| `notification` | In-app | 8 | 10K-100K |
| `audit_log` | Audit | 10 | 100K-2M |

**Tổng kích thước ước tính 1 năm (medium clinic):** ~5-15 GB.

### 26.2. Foreign key map

```
clinic ←─── (mọi bảng có clinic_id)
     ←─── clinic_settings
     ←─── user

user ←─── user_role
     ←─── user_extra_permission
     ←─── visit (doctor_id, assigned_doctor_id)
     ←─── visit_service (performed_by)
     ←─── prescription (prescribed_by)
     ←─── shift, time_log, leave_request

role ←─── user_role
     ←─── role_permission

permission ←─── role_permission
           ←─── user_extra_permission

patient ←─── appointment
        ←─── visit
        ←─── invoice
        ←─── patient_relation (2 cột)

appointment ←─── visit (1:0..1)

visit ←─── visit_service
      ←─── visit_vitals
      ←─── prescription
      ←─── invoice (1:0..1)

medicine ←─── inventory_item
         ←─── prescription_item

inventory_item ←─── batch

batch ←─── prescription_item_batch
      ←─── stock_movement

prescription ←─── prescription_item
prescription_item ←─── prescription_item_batch

invoice ←─── invoice_item
        ←─── payment

shift_template ←─── shift
               ←─── recurring_schedule

shift ←─── time_log
```

### 26.3. Status values reference

| Bảng | Cột | Values |
|---|---|---|
| `appointment` | status | scheduled, confirmed, checked_in, completed, cancelled, no_show |
| `visit` | status | WAITING, IN_PROGRESS, AWAITING_PAYMENT, COMPLETED, CANCELLED |
| `visit_service` | status | ordered, in_progress, completed, cancelled |
| `prescription` | status | pending, partially_dispensed, dispensed, cancelled |
| `prescription_item` | dispense_source | in_house, external |
| `prescription_item` | in_house_status | pending, reserved, dispensed, cancelled |
| `prescription_item_batch` | status | reserved, dispensed, cancelled, substituted |
| `invoice` | status | draft, pending, partially_paid, paid, cancelled, refunded |
| `payment` | payment_method | cash, card, bank_transfer, ewallet, other |
| `shift` | status | scheduled, cancelled, on_leave, completed |
| `leave_request` | status | pending, approved, rejected, cancelled |
| `leave_request` | leave_type | sick, personal, vacation, maternity, other |
| `stock_movement` | movement_type | purchase_in, prescription_out, adjustment_increase/decrease, transfer_in/out, expiry/damage/recall_writeoff, return_in |
| `time_log` | check_in_method | manual, pin, qr, biometric |
| `vital_field_definition` | data_type | number, integer, text, boolean, select |
| `clinic` | specialty | general, dental, pediatric, obstetric, dermatology, ophthalmology, tcm |
| `audit_log` | action | create, update, delete, view, login, logout, failed_login, merge, void, refund, dispense, reserve, transition, export, print, substitute_batch |

---

## Phụ lục: Checklist deploy database

### Pre-deploy

- [ ] Tạo database `cms_production` với UTF-8
- [ ] Tạo roles: `cms_app`, `cms_migrator`, `cms_readonly`
- [ ] Cài extensions: uuid-ossp, pgcrypto, unaccent, pg_trgm, btree_gin
- [ ] Tune `postgresql.conf` theo hardware
- [ ] Bật `log_min_duration_statement`, `pg_stat_statements`
- [ ] Setup WAL archiving cho PITR
- [ ] Setup streaming replica (HA)

### Deploy

- [ ] Chạy Alembic migrations theo thứ tự (0001 → 0024)
- [ ] Verify tất cả tables, indexes, constraints, RLS policies
- [ ] Seed permissions, system roles, vital presets
- [ ] Tạo clinic đầu tiên + admin user
- [ ] Test RLS với account không phải superuser
- [ ] Test connection pooling (PgBouncer)

### Post-deploy

- [ ] Setup monitoring (Prometheus + postgres_exporter)
- [ ] Setup alerts: disk, connection count, replication lag, slow queries
- [ ] Setup daily backup + test restore
- [ ] Setup log aggregation
- [ ] Document runbook cho ops team
- [ ] Schedule monthly: VACUUM ANALYZE, index review, query review

---

*Tài liệu này là DDL reference đầy đủ cho database CMS. Mọi thay đổi schema phải đi qua Alembic migration và cập nhật tài liệu này tương ứng. Các CHECK constraint, RLS policy, và trigger là phần không thể tách rời của design — không tùy ý disable trên production.*
