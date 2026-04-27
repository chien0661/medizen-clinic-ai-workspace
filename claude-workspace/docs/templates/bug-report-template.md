# BUG-[ID]: [Bug Title]

**Type:** [API Contract Issue | Integration Issue | Business Logic Bug | Data Integrity Issue | Workflow Issue]
**Severity:** [Critical | High | Medium | Low]
**Status:** [OPEN | IN_PROGRESS | RESOLVED | CLOSED]
**Feature:** [TASK-ID] - [Feature Name]
**Found By:** Test Agent
**Date:** [YYYY-MM-DD]

## SRS Reference
- Section [X.Y.Z] - [Section Title]
- Business Rule BR-[ID]: [Business rule description]

## Detail Design Reference
- Section [X.Y.Z] - [Section Title]
- Implementation: [Implementation details]

## Test Scenario
- **File:** `features/[path]/[filename].feature`
- **Line:** [line-number]
- **Scenario:** [Scenario name]
- **Tag:** @[tag1] @[tag2]

## Expected Behavior
According to [SRS Section X.Y.Z / Detail Design Section X.Y.Z]:
- [What should happen - requirement 1]
- [What should happen - requirement 2]
- [What should happen - requirement 3]

## Actual Behavior
- [What actually happens - observation 1]
- [What actually happens - observation 2]
- [What actually happens - observation 3]

## Steps to Reproduce
1. [Step 1]
2. [Step 2]
3. [Step 3]
4. [Expected result] → [Actual result]

## Test Output
```
[Copy of test output showing failure]
```

## Database State (if applicable)
```sql
[SQL query to check database state]
-- Result: [Actual result vs Expected result]
```

## Impact
- [Business impact]
- [Technical impact]
- [User impact]
- [Compliance/regulatory impact]

## Suggested Fix
[If obvious, suggest where to look or potential fix]
Investigate [component/service/class name]:
- [Suggestion 1]
- [Suggestion 2]

## Related Files
- `[path/to/suspected/file1.java]`
- `[path/to/suspected/file2.java]`

---

## Resolution (filled by Implementation Agent)

**Fixed By:** [Agent Name]
**Fixed Date:** [YYYY-MM-DD]
**Fix Branch:** [branch-name]
**Fix Commit:** [commit-hash]

### Root Cause
[Explanation of what caused the bug]

### Changes Made
- [Change 1]
- [Change 2]

### Verification
- [How fix was verified]
- [Tests added/updated]

---

## Example Usage

```markdown
# BUG-001: Rate Limit Not Enforced

**Type:** Business Logic Bug
**Severity:** High
**Status:** OPEN
**Feature:** TASK-001 - User Profile API
**Found By:** Test Agent
**Date:** 2026-01-21

## SRS Reference
- Section 3.2.1 - User Restrictions
- Business Rule BR-002: Free users limited to 5 profile updates per day

## Detail Design Reference
- Section 4.1.2 - Rate Limiting Logic
- Implementation: profile_update_log table tracks update attempts

## Test Scenario
- **File:** `features/business-rules/rate-limiting.feature`
- **Line:** 45
- **Scenario:** BR-002 - Free user rate limiting
- **Tag:** @business @BR-002

## Expected Behavior
According to SRS Section 3.2.1:
- Free users can update profile maximum 5 times per day (24-hour rolling window)
- 6th update within 24 hours should return HTTP 429 (Too Many Requests)
- Response should include error code "RATE_LIMIT_EXCEEDED"
- Response should include error message: "Free users can update profile 5 times per day"
- Response should include "retryAfter" timestamp indicating when limit resets

## Actual Behavior
- Free user successfully made 6 updates in a row
- All updates returned HTTP 200 (Success)
- No rate limiting was enforced
- profile_update_log table has 0 entries (rate limit tracking not working)

## Steps to Reproduce
1. Login as free user (email: free@example.com, subscriptionType: FREE)
2. Call PUT /users/456/profile with bio: "Update 1"
3. Repeat step 2 with "Update 2", "Update 3", ..., "Update 6"
4. Observe all 6 requests succeed with HTTP 200
5. Expected: 6th request should fail with HTTP 429

## Test Output
```
Scenario: BR-002 - Free user rate limiting
  * def freeUserToken = call read('classpath:common/free-user-login.feature')
  * header Authorization = 'Bearer ' + freeUserToken.token
  ...
  # 6th update should fail with 429
  Given path 'users', 456, 'profile'
  And request { bio: 'Update 6 - Should Fail' }
  When method PUT
  Then status 429
  FAILED: expected status 429 but was 200

  # Error response validation also failed
  And match response.error == 'Rate limit exceeded'
  FAILED: response.error was undefined (no error in response)
```

## Database State
```sql
SELECT COUNT(*) FROM profile_update_log
WHERE user_id = 456
  AND created_at > NOW() - INTERVAL 1 DAY;
-- Result: 0 rows
-- Expected: 6 rows (one for each update attempt)

SELECT subscription_type FROM users WHERE id = 456;
-- Result: 'FREE'
-- Confirmed user is free tier
```

## Impact
- **Business Impact:** Free users can bypass subscription limits, potentially reducing premium upgrade incentives
- **Revenue Impact:** Loss of potential premium subscription revenue
- **Compliance Impact:** SRS requirement BR-002 not implemented, violating business rules
- **User Impact:** Unfair advantage for free users, premium feature available without payment

## Suggested Fix
Investigate rate limiting implementation in these components:
1. Check UserProfileService.updateProfile() method
   - Verify RateLimitService.checkRateLimit() is being called
   - Ensure it's called BEFORE the update logic
2. Check RateLimitService implementation
   - Verify it correctly reads user subscription type
   - Ensure profile_update_log table is being updated
   - Check transaction commit/rollback behavior
3. Check database migration scripts
   - Verify profile_update_log table exists
   - Verify indexes are created for performance

## Related Files
- `src/main/java/service/UserProfileService.java` (likely missing rate limit check)
- `src/main/java/service/RateLimitService.java` (implementation issue)
- `src/main/resources/db/migration/V2__create_profile_update_log.sql` (verify table exists)
- `src/main/java/controller/UserProfileController.java` (check if rate limit exception is handled)

---

## Resolution

**Fixed By:** Code Implementation Agent
**Fixed Date:** 2026-01-22
**Fix Branch:** bugfix/BUG-001-rate-limit-enforcement
**Fix Commit:** abc123def456

### Root Cause
UserProfileService.updateProfile() method was not calling RateLimitService.checkRateLimit() before performing the update. The method was implemented but never invoked in the update flow.

### Changes Made
- Added rate limit check at the beginning of UserProfileService.updateProfile()
- Throws RateLimitExceededException when limit is exceeded
- RateLimitService now properly logs to profile_update_log table
- Added unit test for rate limit enforcement
- Updated integration test to verify database logging

### Verification
- Unit test added: UserProfileServiceTest.testRateLimitEnforcement()
- Re-ran business rule test: BR-002 now PASSES
- Verified in database: profile_update_log entries are created
- Manual testing: 6th update correctly returns 429 with proper error message
```
