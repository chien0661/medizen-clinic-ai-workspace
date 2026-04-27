# Code Review: [TASK-ID] - [Task Title]

**Reviewer:** Code Review Agent
**Date:** [YYYY-MM-DD]
**Branch:** [branch-name]
**Status:** [APPROVED | CHANGES_REQUESTED]

## Review Summary

- **Files Reviewed:** [count]
- **Issues Found:** [count]
  - Critical: [count]
  - Major: [count]
  - Minor: [count]
- **Test Coverage:** [percentage]%
- **Code Quality:** [Excellent | Good | Fair | Needs Improvement]

## Issues Found

### Issue [N]: [Issue Title]
**File:** `[relative/path/to/file.java]:[line-number]`
**Severity:** [Critical | Major | Minor]
**Description:** [Clear description of the issue]

**Current Code:**
```java
// Copy of problematic code
```

**Suggestion:**
```java
// Suggested fix
```

**Rationale:**
[Explain why this is an issue and why the suggestion is better]

---

### Issue [N]: [Issue Title]
...

## Code Quality Metrics

- **SonarQube Rating:** [A | B | C | D | E]
- **Maintainability:** [Good | Fair | Needs Work]
- **Complexity:** [Low | Medium | High]
- **Duplications:** [None | count] instances found
- **Test Coverage:** [percentage]% (Target: 80%+) [✅ | ❌]

## Positive Observations

[List things done well]
✅ [Positive aspect 1]
✅ [Positive aspect 2]
✅ [Positive aspect 3]

## Decision

**[APPROVED | CHANGES_REQUESTED]**

[Brief explanation of decision]

## Next Steps

[If APPROVED:]
1. Proceed to automated testing phase
2. Update docs/tasks/dashboard.md status to "IN_TESTING"

[If CHANGES_REQUESTED:]
1. [Action item 1: e.g., Fix Issue 1 - Add input validation]
2. [Action item 2: e.g., Fix Issue 2 - Update error handling]
3. [Action item 3: e.g., Re-run unit tests]
4. [Action item 4: e.g., Update docs/tasks/dashboard.md status to "IN_REVIEW"]

---

**Review Time:** [duration]
**Recommendations:** [Any process or tooling recommendations]

---

## Example Usage

```markdown
# Code Review: TASK-001 - User Profile API

**Reviewer:** Code Review Agent
**Date:** 2026-01-21
**Branch:** feature/TASK-001-user-profile-api
**Status:** CHANGES_REQUESTED

## Review Summary

- **Files Reviewed:** 5
- **Issues Found:** 3
  - Critical: 0
  - Major: 1
  - Minor: 2
- **Test Coverage:** 95%
- **Code Quality:** Good

## Issues Found

### Issue 1: Missing Swagger Documentation
**File:** `src/main/java/controller/UserProfileController.java:30`
**Severity:** Major
**Description:** Missing @Operation and @ApiResponse annotations for API endpoint. This is required for auto-generated API documentation.

**Current Code:**
```java
@GetMapping("/{id}/profile")
public ResponseEntity<UserProfileDTO> getUserProfile(@PathVariable Long id) {
```

**Suggestion:**
```java
@Operation(summary = "Get user profile", description = "Retrieve user profile by ID")
@ApiResponses({
    @ApiResponse(responseCode = "200", description = "Profile retrieved successfully"),
    @ApiResponse(responseCode = "404", description = "User not found"),
    @ApiResponse(responseCode = "401", description = "Unauthorized"),
    @ApiResponse(responseCode = "429", description = "Rate limit exceeded")
})
@GetMapping("/{id}/profile")
public ResponseEntity<UserProfileDTO> getUserProfile(@PathVariable Long id) {
```

**Rationale:**
Swagger annotations are required per CLAUDE.md for all public APIs. This enables automatic API documentation generation and improves API discoverability.

---

### Issue 2: Missing Input Validation
**File:** `src/main/java/controller/UserProfileController.java:45`
**Severity:** Minor
**Description:** Missing @Valid and @Min annotations on path variable for input validation.

**Current Code:**
```java
public ResponseEntity<UserProfileDTO> getUserProfile(@PathVariable Long id) {
```

**Suggestion:**
```java
public ResponseEntity<UserProfileDTO> getUserProfile(
        @PathVariable @Valid @Min(1) Long id) {
```

**Rationale:**
Input validation should be at the controller level. User ID must be positive (> 0). This prevents invalid requests from reaching the service layer.

---

### Issue 3: Log Message Could Be More Informative
**File:** `src/main/java/service/UserProfileService.java:67`
**Severity:** Minor
**Description:** Log message lacks context, making debugging harder.

**Current Code:**
```java
log.info("Profile retrieved");
```

**Suggestion:**
```java
log.info("Retrieved profile for user: {}", userId);
```

**Rationale:**
Adding user ID to log message provides context for debugging and monitoring. Helps trace user-specific issues in production.

## Code Quality Metrics

- **SonarQube Rating:** A
- **Maintainability:** Good
- **Complexity:** Low
- **Duplications:** None found
- **Test Coverage:** 95% (Target: 80%+) ✅

## Positive Observations

✅ Clean code structure following Spring Boot patterns
✅ Excellent test coverage with meaningful tests
✅ Proper error handling with custom exceptions
✅ Good separation of concerns (controller/service/repository)
✅ No security vulnerabilities detected
✅ Proper use of DTOs instead of exposing entities
✅ Constructor-based dependency injection used correctly

## Decision

**CHANGES_REQUESTED**

Please address 1 major and 2 minor issues identified above. Once fixed, resubmit for review. The changes are straightforward and should not take long.

## Next Steps

1. Add Swagger documentation annotations (Issue 1) - Major priority
2. Add input validation annotations (Issue 2)
3. Improve log message clarity (Issue 3)
4. Re-run unit tests to ensure everything still passes
5. Update docs/tasks/dashboard.md status to "IN_REVIEW"
6. Create new handoff document

---

**Review Time:** 15 minutes
**Recommendations:** Consider setting up automated linting rules (e.g., Checkstyle) to catch missing Swagger annotations earlier in the development process.
```
