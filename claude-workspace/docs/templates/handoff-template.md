# Handoff: [TASK-ID] [Task Title] → [Next Phase]

**From:** [Current Agent]
**To:** [Next Agent]
**Date:** [YYYY-MM-DD]
**Task:** [TASK-ID] - [Task Description]
**Branch:** [branch-name]

## Summary
[Brief summary of work completed - 2-3 sentences]

## Changes

**Files Added:**
- [path/to/new/file1.java] - [Brief description]
- [path/to/new/file2.java] - [Brief description]

**Files Modified:**
- [path/to/modified/file1.java] - [What changed]
- [path/to/modified/file2.java] - [What changed]

**Files Deleted:**
- [path/to/deleted/file.java] - [Why deleted]
- None

## Tests

### Unit Tests (Implementation Agent)
- **Total Tests:** [count]
- **Status:** [count] passing, [count] failing
- **Coverage:** [percentage]%
- **New Tests Added:** [list new test files]

### Automated Tests (Test Agent)
- **Smoke Tests:** [count]/[count] passed
- **API Contract Tests:** [count]/[count] passed
- **Integration Tests:** [count]/[count] passed
- **Business Rule Tests:** [count]/[count] passed
- **E2E Workflows:** [count]/[count] passed
- **Test Report:** docs/tasks/[TASK-ID]/deliveries/test-reports/test-report.md

## Dependencies
[List any new dependencies added or external services required]
- [dependency-name] version [version-number] - [Why needed]
- None

## Configuration Changes
[List any configuration changes made]
- **Environment Variables:** [NEW_VAR_NAME] - [Description]
- **application.yml:** [Section changed] - [What changed]
- None

## Notes
[Any important notes, warnings, or context for the next agent]
- [Note 1]
- [Note 2]

## Review Focus Areas
[For Code Review Agent: Areas that need special attention]
- [Area 1: e.g., Security implementation in authentication]
- [Area 2: e.g., Performance optimization in query logic]
- [Area 3: e.g., Error handling for external API calls]

## Related Documentation
[Links to relevant specifications and documentation]
- SRS: docs/tasks/[TASK-ID]/refs/[SRS-file.md] - Section [X.Y]
- Detail Design: docs/tasks/[TASK-ID]/refs/[DD-file.md] - Section [X.Y]
- API Spec: docs/tasks/[TASK-ID]/deliveries/api-specs/[endpoint-name].md

---

## Example Usage

```markdown
# Handoff: TASK-001 User Profile API → Code Review

**From:** Code Implementation Agent
**To:** Code Review Agent
**Date:** 2026-01-21
**Task:** TASK-001 - User Profile API
**Branch:** feature/TASK-001-user-profile-api

## Summary
Implemented JWT authentication with refresh tokens for user profile API. Added rate limiting for free tier users (5 requests/day) and unlimited access for premium users.

## Changes

**Files Added:**
- src/main/java/controller/UserProfileController.java - REST controller for profile endpoints
- src/main/java/service/UserProfileService.java - Business logic for profile operations
- src/main/java/service/RateLimitService.java - Rate limiting logic
- src/main/java/dto/UserProfileDTO.java - DTO for profile responses
- src/test/java/controller/UserProfileControllerTest.java - Controller unit tests
- src/test/java/service/UserProfileServiceTest.java - Service unit tests

**Files Modified:**
- src/main/java/config/SecurityConfig.java - Added profile endpoints to security config
- src/main/resources/application.yml - Added rate limit configuration

**Files Deleted:**
- None

## Tests

### Unit Tests
- **Total Tests:** 12 tests
- **Status:** 12 passing, 0 failing
- **Coverage:** 95%
- **New Tests Added:**
  - UserProfileControllerTest.java (6 tests)
  - UserProfileServiceTest.java (6 tests)

## Dependencies
- io.jsonwebtoken:jjwt:0.12.5 - For JWT token generation and validation
- org.springframework.boot:spring-boot-starter-data-redis:2.7.5 - For rate limit tracking

## Configuration Changes
- **Environment Variables:**
  - JWT_SECRET - Secret key for JWT signing (required)
  - PROFILE_RATE_LIMIT_FREE - Free tier limit (default: 5)
  - PROFILE_RATE_LIMIT_WINDOW - Time window in seconds (default: 86400)

- **application.yml:**
  - Added profile.rate-limit section with free-tier and window config

## Notes
- JWT secret must be set in environment or application will fail to start
- Rate limit uses Redis for distributed tracking across instances
- Refresh token expiry set to 7 days (configurable)

## Review Focus Areas
- Security implementation (token generation/validation in UserProfileService)
- Check for token leakage in logs (especially in error handling)
- Verify rate limit logic correctly distinguishes free vs premium users
- Review refresh token rotation implementation

## Related Documentation
- SRS: docs/tasks/TASK-001/refs/SRS-UserManagement.md - Section 3.2 Profile Management
- Detail Design: docs/tasks/TASK-001/refs/DetailDesign.md - Section 4.1 JWT Implementation
- Detail Design: docs/tasks/TASK-001/refs/DetailDesign.md - Section 4.2 Rate Limiting
- API Spec: docs/tasks/TASK-001/deliveries/api-specs/user-profile.md
```
