# Test Report: [TASK-ID] - [Task Title]

**Test Agent:** Automation Tester
**Date:** [YYYY-MM-DD]
**Status:** [✅ ALL PASSED | ❌ [count] FAILED]

## Test Statistics

| Test Type | Scenarios | Passed | Failed | Success Rate |
|-----------|-----------|--------|--------|--------------|
| Smoke | [count] | [count] | [count] | [%] |
| API Contract | [count] | [count] | [count] | [%] |
| Integration | [count] | [count] | [count] | [%] |
| Business Rules | [count] | [count] | [count] | [%] |
| E2E Workflows | [count] | [count] | [count] | [%] |
| **TOTAL** | **[count]** | **[count]** | **[count]** | **[%]** |

## Business Rules Validated

### SRS Section [X.Y] - [Section Title]
- [✅ | ❌] BR-[ID]: [Business rule description] - [PASSED | FAILED] [Verification method]
- [✅ | ❌] BR-[ID]: [Business rule description] - [PASSED | FAILED] [Verification method]

### SRS Section [X.Y] - [Section Title]
- [✅ | ❌] BR-[ID]: [Business rule description] - [PASSED | FAILED] [Verification method]

[All business requirements VALIDATED ✓ | Issues found - see Failures section below]

## Coverage

### API Endpoints
- [✅ | ❌] [HTTP_METHOD] [/endpoint/path] - Tested ([count] scenarios)
- [✅ | ❌] [HTTP_METHOD] [/endpoint/path] - Tested ([count] scenarios)

**Coverage:** [percentage]% of implemented endpoints

### SRS Requirements
- [✅ | ❌] Section [X.Y] - [Requirement] ([count] scenarios)
- [✅ | ❌] Section [X.Y] - [Requirement] ([count] scenarios)

**Coverage:** [percentage]% of SRS requirements

### Database Operations
- [✅ | ❌] CRUD operations validated
- [✅ | ❌] Audit log verified
- [✅ | ❌] [Other DB operation] verified
- [✅ | ❌] Constraints enforced

## Test Files Created

### API Contract Tests
- `features/api-contracts/[feature-name].feature` ([count] scenarios)

### Integration Tests
- `features/integration/[feature-name]-database.feature` ([count] scenarios)
- `features/integration/[feature-name]-[integration].feature` ([count] scenarios)

### Business Rule Tests
- `features/business-rules/[rule-name].feature` ([count] scenarios)

### E2E Workflows
- `features/workflows/[workflow-name].feature` ([count] scenarios)

### Test Data
- `testdata/[data-file].json`

## Performance

- **Average Response Time:** [X]ms
- **95th Percentile:** [X]ms
- **Max Response Time:** [X]ms
- **Performance Target:** [✅ All below [X]ms | ❌ [count] scenarios exceeded target]

## Failures (if any)

### Failure 1: [Scenario Name]
**File:** `features/[path]/[file].feature:[line]`
**Type:** [API Contract | Integration | Business Logic | Data Integrity | Workflow]
**Severity:** [High | Medium | Low]

**Expected:**
[What was expected to happen]

**Actual:**
[What actually happened]

**Error Message:**
```
[Error output from test]
```

**Bug Report:** docs/tasks/TASK-[ID]/bugs/BUG-[ID].md

---

### Failure 2: [Scenario Name]
...

## Next Steps

[If all pass:]
All tests passed successfully. Ready to proceed to Documentation phase.
**Update docs/tasks/dashboard.md status to "DOCUMENTING"**

[If failures:]
[count] test failures found. Bug reports created in docs/tasks/TASK-[ID]/bugs/.
**Update docs/tasks/dashboard.md status to "IN_PROGRESS"**
**Assign to Code Implementation Agent for fixes**

---

**Test Execution Time:** [X] minutes [Y] seconds
**Total Scenarios:** [count]
**Total Steps:** [count]
**Environment:** [dev | staging | prod]

---

## Example Usage

```markdown
# Test Report: TASK-001 - User Profile API

**Test Agent:** Automation Tester
**Date:** 2026-01-21
**Status:** ✅ ALL PASSED

## Test Statistics

| Test Type | Scenarios | Passed | Failed | Success Rate |
|-----------|-----------|--------|--------|--------------|
| Smoke | 5 | 5 | 0 | 100% |
| API Contract | 8 | 8 | 0 | 100% |
| Integration | 6 | 6 | 0 | 100% |
| Business Rules | 4 | 4 | 0 | 100% |
| E2E Workflows | 2 | 2 | 0 | 100% |
| **TOTAL** | **25** | **25** | **0** | **100%** |

## Business Rules Validated

### SRS Section 3.1 - Profile Management
- ✅ BR-001: Profile updates audited - VERIFIED in database
- ✅ BR-002: Free users 5 updates/day limit - PASSED with 429 on 6th
- ✅ BR-003: Premium users unlimited - PASSED 11 consecutive updates
- ✅ BR-004: Response time < 200ms - VERIFIED (avg 145ms)

### SRS Section 3.2 - Data Integrity
- ✅ BR-005: Foreign key constraints - VERIFIED
- ✅ BR-006: Soft delete preserves history - VERIFIED
- ✅ BR-007: Transaction rollback on errors - VERIFIED

All business requirements VALIDATED ✓

## Coverage

### API Endpoints
- ✅ GET /users/{id}/profile - Tested (5 scenarios)
- ✅ PUT /users/{id}/profile - Tested (8 scenarios)

**Coverage:** 100% of implemented endpoints

### SRS Requirements
- ✅ Section 3.1 - Profile retrieval (4 scenarios)
- ✅ Section 3.2 - Profile updates (6 scenarios)
- ✅ Section 3.3 - Rate limiting (3 scenarios)
- ✅ Section 3.4 - Audit trail (2 scenarios)

**Coverage:** 100% of SRS requirements

### Database Operations
- ✅ CRUD operations validated
- ✅ Audit log verified
- ✅ Rate limit tracking verified
- ✅ Constraints enforced

## Test Files Created

### API Contract Tests
- `features/api-contracts/user-profile.feature` (8 scenarios)

### Integration Tests
- `features/integration/profile-database.feature` (4 scenarios)
- `features/integration/profile-audit.feature` (2 scenarios)

### Business Rule Tests
- `features/business-rules/rate-limiting.feature` (3 scenarios)
- `features/business-rules/audit-trail.feature` (1 scenario)

### E2E Workflows
- `features/workflows/registration-to-profile.feature` (2 scenarios)

### Test Data
- `testdata/users.json`
- `testdata/profile-updates.json`

## Performance

- **Average Response Time:** 145ms
- **95th Percentile:** 178ms
- **Max Response Time:** 203ms
- **Performance Target:** ✅ All below 200ms target

## Next Steps

All tests passed successfully. Ready to proceed to Documentation phase.

**Update docs/tasks/dashboard.md status to "DOCUMENTING"**

---

**Test Execution Time:** 3 minutes 45 seconds
**Total Scenarios:** 25
**Total Steps:** 187
**Environment:** dev
```
