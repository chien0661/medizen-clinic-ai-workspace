---
id: TASK-025
type: feature
title: System Integration + E2E Test Suite (Playwright + Smoke + Regression + Performance)
status: TODO
priority: High
assigned: Unassigned
created: 2026-04-26
updated: 2026-04-26
branch: ""
tags: [integration, e2e, playwright, performance, sprint-16]
affected-repos: [clinic-cms]
refs:
  detail_design: "../../../../docs/clinic_management_system_design.md#22-testing-strategy"
  other:
    - "../../../../docs/clinic_management_business_analysis.md"
---

# TASK-025: System Integration + E2E Test Suite (Final Acceptance)

## Description

Final task: tích hợp toàn bộ FE (TASK-017..024) + BE (TASK-001..015) + Tauri foundation (TASK-016), viết E2E test suite Playwright cover các critical flow, smoke + regression test cases, performance budget validation, prepare release v1.0.

## Requirements

- [ ] **Test infrastructure**
  - Playwright cho Tauri (dùng `@tauri-apps/cli` hoặc webdriver mode)
  - Test data seed scripts: tạo clinic, users, patients, medicines, services qua API
  - Fresh DB per test suite (docker-compose down -v + up + migrate + seed)
  - Parallel execution với workers
  - CI integration (GitHub Actions): chạy E2E khi PR merge vào main
- [ ] **Smoke test suite** (10 critical scenarios, run mỗi PR)
  1. Login flow + lockout sau 5 lần sai
  2. Onboard clinic mới (specialty=general) end-to-end wizard
  3. Đăng ký bệnh nhân + walk-in check-in
  4. Doctor consultation: vitals + service + prescription (in_house) → hoàn tất
  5. Pharmacist dispense → stock decrement đúng
  6. Cashier tạo invoice + thu tiền → status paid
  7. Tạo appointment + check-in → tự động tạo Visit
  8. Multi-tenant isolation: user clinic A không thấy patient clinic B
  9. RBAC: Doctor không gọi được endpoint pharmacy.dispense (403)
  10. Offline mode: tạo patient + walk-in offline → sync khi online
- [ ] **Regression test suite** (~50 test cases per module, run nightly)
  - Patient: search/merge/undo
  - Visit: state machine transitions hợp lệ + invalid
  - Appointment: capacity check, smart queue walk-in vs appointment
  - Vitals: dynamic form validation + schema evolution
  - Inventory: FEFO reservation, substitute batch, adjustment
  - Prescription: mixed dispense source, override
  - Billing: multi-payment, discount with reason, void/refund
  - HR: shift conflict, leave overlap, attendance late/OT calculation
  - Reports: 8 reports với data fixture, validate aggregation đúng
- [ ] **Performance budget tests**
  - API: p95 latency < 200ms cho list endpoint, < 500ms cho complex report
  - DB: query < 100ms (slow query log alert > 1s)
  - FE: First Paint < 2s, TTI < 3s
  - Memory: Tauri app < 300MB RSS
  - Stress test: 50 concurrent user → no error, latency increase < 2x
- [ ] **Security test**
  - SQL injection scan (sqlmap basic)
  - XSS scan
  - JWT tampering rejected
  - RLS bypass attempt blocked
  - Rate limit hit → 429
- [ ] **Acceptance test với stakeholder** (theo BA §19 step 4)
  - Demo cho chủ phòng khám pilot (1 clinic mẫu)
  - User testing feedback collection
  - Bug triage + critical fix
- [ ] **Release artifacts**
  - Tauri build: Windows .msi + macOS .dmg + Linux .AppImage (signed)
  - Backend Docker image push tới registry (versioned tag v1.0.0)
  - Database migration upgrade script + rollback plan
  - Release notes (CHANGELOG.md)
  - User manual (docs/user-guide/) cho 5 role
  - Deployment runbook (docs/ops/)
- [ ] **Monitoring setup** (đã spec ở System Design §23)
  - Prometheus + Grafana dashboards
  - Loki log aggregation
  - OpenTelemetry tracing với clinic_id tag
  - Alert rules: error rate, latency p95, DB pool, disk

## Acceptance Criteria

- [ ] Smoke test suite green trên CI cho 5 PR liên tiếp
- [ ] Regression test pass rate ≥ 98% (chấp nhận 2% flaky cần triage)
- [ ] Performance budget đạt 100% cho API + FE
- [ ] Security scan: 0 critical, 0 high vulnerabilities
- [ ] Pilot clinic chạy 1 tuần production-like → 0 P0 bug, < 5 P1 bug
- [ ] Tauri installer test: install fresh Windows 10/11 + macOS 14 + Ubuntu 22 → app launch OK
- [ ] Backup + restore drill: restore từ backup vào fresh DB → data integrity 100%
- [ ] User manual cover 100% feature, screenshot up-to-date
- [ ] Sign-off từ chủ phòng khám pilot

## Progress Checklist

- [ ] Implementation
- [ ] Code Review
- [ ] Testing
- [ ] Documentation

## Related Files

- **Code**: `clinic-cms/tests/e2e/`, `clinic-cms/tests/integration/`, `clinic-cms/desktop/tests/`
- **Test cases**: `docs/tasks/TASK-025/deliveries/test-cases/`
- **Test reports**: `docs/tasks/TASK-025/deliveries/test-reports/`

## Timestamps

- **Created**: 2026-04-26

## Notes

Đây là task FINAL — tất cả task trước phải IN_REVIEW hoặc DONE. Bug phát sinh trong E2E mở `BUG-XXX` riêng, không bundle vào task này.

Pilot clinic: chọn 1 phòng khám đa khoa nhỏ làm beta tester, 4-6 tuần trước launch chính thức. Hỗ trợ tận nơi tuần đầu.

## Blockers

- TẤT CẢ task TASK-001 → TASK-024
