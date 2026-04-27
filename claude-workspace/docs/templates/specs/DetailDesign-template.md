# Detail Design Document Template

**Project:** [Project Name]
**Feature:** [Feature Name]
**Version:** [Version Number]
**Date:** [YYYY-MM-DD]
**Author:** [Author Name]
**Status:** [Draft | Review | Approved]
**SRS Reference:** [SRS document name and version]

---

## 1. Introduction

### 1.1 Purpose
[Purpose of this detail design document]

### 1.2 Scope
[What aspects of the system this design covers]

### 1.3 References
- **SRS:** [SRS document reference]
- **Architecture:** [Architecture document reference]
- **Related Designs:** [Related design documents]

---

## 2. Architecture Overview

### 2.1 System Context
```
[ASCII diagram showing where this component fits in the overall system]

┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│   Client    │──────│   API       │──────│  Database   │
└─────────────┘      └─────────────┘      └─────────────┘
                            │
                            ▼
                     ┌─────────────┐
                     │   Service   │
                     └─────────────┘
```

### 2.2 Component Diagram
[Detailed component diagram showing major components and their relationships]

### 2.3 Technology Stack
- **Backend:** [e.g., Java 8, Spring Boot 2.7.5]
- **Database:** [e.g., MariaDB 10.6]
- **Cache:** [e.g., Redis 7.0]
- **Message Queue:** [e.g., Kafka 3.3]
- **Other:** [Additional technologies]

---

## 3. Detailed Component Design

### 3.1 [Component Name 1]

#### 3.1.1 Responsibility
[What this component is responsible for]

#### 3.1.2 Class Diagram
```
[Class diagram showing classes, attributes, and relationships]

┌─────────────────────────┐
│   UserProfileController │
├─────────────────────────┤
│ - userProfileService    │
├─────────────────────────┤
│ + getUserProfile(id)    │
│ + updateProfile(id, dto)│
└─────────────────────────┘
           │
           ▼
┌─────────────────────────┐
│   UserProfileService    │
├─────────────────────────┤
│ - userRepository        │
│ - rateLimitService      │
├─────────────────────────┤
│ + getUserProfile(id)    │
│ + updateProfile(id, dto)│
└─────────────────────────┘
```

#### 3.1.3 Key Classes

**Class: UserProfileController**
```java
@RestController
@RequestMapping("/api/users")
public class UserProfileController {
    private final UserProfileService userProfileService;

    @GetMapping("/{id}/profile")
    public ResponseEntity<UserProfileDTO> getUserProfile(@PathVariable Long id) {
        // Implementation
    }
}
```

**Responsibilities:**
- Handle HTTP requests for user profile operations
- Validate input parameters
- Return appropriate HTTP status codes

**Dependencies:**
- UserProfileService

---

**Class: UserProfileService**
```java
@Service
public class UserProfileService {
    private final UserRepository userRepository;
    private final RateLimitService rateLimitService;

    public UserProfileDTO getUserProfile(Long userId) {
        // Implementation
    }
}
```

**Responsibilities:**
- Implement business logic for profile operations
- Enforce rate limiting
- Coordinate with repository layer

**Dependencies:**
- UserRepository
- RateLimitService

---

#### 3.1.4 Sequence Diagram

```
[Sequence diagram showing interaction flow]

Client          Controller      Service         Repository      Database
  │                │               │                 │              │
  │─getUserProfile─>│               │                 │              │
  │                │               │                 │              │
  │                │─getUserProfile>│                 │              │
  │                │               │                 │              │
  │                │               │─checkRateLimit─>│              │
  │                │               │<────OK──────────│              │
  │                │               │                 │              │
  │                │               │─findById────────>│              │
  │                │               │                 │──SELECT──────>│
  │                │               │                 │<─result──────│
  │                │               │<────user────────│              │
  │                │               │                 │              │
  │                │<──userDTO─────│                 │              │
  │<───200 OK──────│               │                 │              │
```

---

### 3.2 [Component Name 2]

[Continue pattern for each major component...]

---

## 4. Database Design

### 4.1 Entity Relationship Diagram

```
[ER diagram showing tables and relationships]

┌─────────────────┐         ┌──────────────────┐
│     users       │         │  user_profiles   │
├─────────────────┤         ├──────────────────┤
│ id (PK)         │────────<│ user_id (FK)     │
│ email           │         │ bio              │
│ subscription    │         │ location         │
│ created_at      │         │ updated_at       │
└─────────────────┘         └──────────────────┘
        │
        │
        ▼
┌─────────────────────────┐
│ profile_update_log      │
├─────────────────────────┤
│ id (PK)                 │
│ user_id (FK)            │
│ updated_at              │
│ created_at              │
└─────────────────────────┘
```

### 4.2 Table Specifications

#### Table: users
**Description:** Stores user account information

| Column | Type | Null | Default | Description |
|--------|------|------|---------|-------------|
| id | BIGINT | NOT NULL | AUTO_INCREMENT | Primary key |
| email | VARCHAR(255) | NOT NULL | - | User email (unique) |
| subscription_type | VARCHAR(50) | NOT NULL | 'FREE' | FREE or PREMIUM |
| created_at | TIMESTAMP | NOT NULL | CURRENT_TIMESTAMP | Creation timestamp |
| updated_at | TIMESTAMP | NOT NULL | CURRENT_TIMESTAMP ON UPDATE | Last update timestamp |

**Indexes:**
- PRIMARY KEY (id)
- UNIQUE KEY (email)
- INDEX (subscription_type)

**Constraints:**
- CHECK (subscription_type IN ('FREE', 'PREMIUM'))

---

#### Table: user_profiles
**Description:** Stores user profile information

[Continue pattern for each table...]

---

### 4.3 Database Migration Scripts

**File:** `V1__create_users_table.sql`
```sql
CREATE TABLE users (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    subscription_type VARCHAR(50) NOT NULL DEFAULT 'FREE',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CHECK (subscription_type IN ('FREE', 'PREMIUM'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX idx_users_subscription ON users(subscription_type);
```

---

## 5. API Design

### 5.1 API Endpoints

#### GET /users/{id}/profile

**Description:** Retrieve user profile information

**Authentication:** Required (Bearer token)

**Rate Limiting:**
- Free users: 5 requests per day
- Premium users: Unlimited

**Request:**
- **Path Parameters:**
  - `id` (Long, required): User ID, must be > 0

- **Headers:**
  ```
  Authorization: Bearer {jwt_token}
  Accept: application/json
  ```

**Response:**

**Success (200 OK):**
```json
{
  "id": 123,
  "name": "John Doe",
  "email": "john@example.com",
  "bio": "Software Developer",
  "location": "Hanoi, Vietnam",
  "subscriptionType": "PREMIUM"
}
```

**Error Responses:**

**400 Bad Request:**
```json
{
  "error": "INVALID_REQUEST",
  "message": "User ID must be greater than 0",
  "timestamp": "2026-01-21T10:30:00Z"
}
```

**401 Unauthorized:**
```json
{
  "error": "UNAUTHORIZED",
  "message": "Authentication required",
  "timestamp": "2026-01-21T10:30:00Z"
}
```

**404 Not Found:**
```json
{
  "error": "USER_NOT_FOUND",
  "message": "User not found with ID: 123",
  "timestamp": "2026-01-21T10:30:00Z"
}
```

**429 Too Many Requests:**
```json
{
  "error": "RATE_LIMIT_EXCEEDED",
  "message": "Free users can access profile 5 times per day",
  "retryAfter": 1706270400,
  "timestamp": "2026-01-21T10:30:00Z"
}
```

---

### 5.2 [Additional Endpoints]

[Continue pattern for each endpoint...]

---

## 6. Business Logic Implementation

### 6.1 Rate Limiting Logic (BR-002)

**Requirement:** Free users limited to 5 profile updates per day
**SRS Reference:** Section 3.2.1 - BR-002

**Implementation:**

```java
public class RateLimitService {

    public void checkRateLimit(Long userId, String subscriptionType) {
        // Skip for premium users
        if ("PREMIUM".equals(subscriptionType)) {
            return;
        }

        // Count updates in last 24 hours
        long count = profileUpdateLogRepository
            .countByUserIdAndCreatedAtAfter(
                userId,
                LocalDateTime.now().minusHours(24)
            );

        // Enforce limit
        if (count >= 5) {
            throw new RateLimitExceededException(
                "Free users can update profile 5 times per day"
            );
        }

        // Log this access attempt
        profileUpdateLogRepository.save(
            new ProfileUpdateLog(userId, LocalDateTime.now())
        );
    }
}
```

**Algorithm:**
1. Check if user is PREMIUM → skip rate limit
2. Query profile_update_log for entries in last 24 hours
3. If count ≥ 5 → throw RateLimitExceededException
4. If count < 5 → log this access and allow

**Database Impact:**
- SELECT query on profile_update_log (indexed on user_id + created_at)
- INSERT into profile_update_log

---

### 6.2 [Additional Business Logic]

[Continue pattern for each business rule...]

---

## 7. Security Design

### 7.1 Authentication
[How authentication is implemented]

### 7.2 Authorization
[How authorization is implemented]

### 7.3 Data Protection
[How sensitive data is protected]

### 7.4 Input Validation
[How inputs are validated]

---

## 8. Performance Considerations

### 8.1 Caching Strategy
- **User Profiles:** Cache for 1 hour, invalidate on update
- **Rate Limit Counters:** Use Redis for distributed tracking

### 8.2 Database Optimization
- **Indexes:** Added on user_id, created_at for rate limit queries
- **Connection Pooling:** HikariCP with 20 connections

### 8.3 Query Optimization
[Specific query optimizations]

---

## 9. Error Handling

### 9.1 Exception Hierarchy
```
Exception
└── RuntimeException
    └── BusinessException
        ├── UserNotFoundException
        ├── RateLimitExceededException
        └── ValidationException
```

### 9.2 Global Exception Handler
```java
@ControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(RateLimitExceededException.class)
    public ResponseEntity<ErrorResponse> handleRateLimitExceeded(
            RateLimitExceededException e) {
        return ResponseEntity
            .status(HttpStatus.TOO_MANY_REQUESTS)
            .body(new ErrorResponse("RATE_LIMIT_EXCEEDED", e.getMessage()));
    }
}
```

---

## 10. Testing Strategy

### 10.1 Unit Tests
- UserProfileServiceTest: Test business logic
- RateLimitServiceTest: Test rate limiting logic
- Target coverage: 90%+

### 10.2 Integration Tests (Karate)
- API contract tests: Verify status codes, schemas
- Database integration tests: Verify data persistence
- Rate limit integration tests: Verify BR-002 enforcement

### 10.3 Business Rule Tests (Karate)
- BR-001: Audit trail test
- BR-002: Rate limit test (5 updates, 6th fails with 429)
- BR-003: Premium unlimited test

---

## 11. Configuration

### 11.1 Application Configuration

**application.yml:**
```yaml
profile:
  rate-limit:
    free-tier: 5
    window: 86400  # 24 hours in seconds
  cache:
    enabled: true
    ttl: 3600  # 1 hour
```

### 11.2 Environment Variables
- `PROFILE_RATE_LIMIT_FREE` - Free tier limit (default: 5)
- `PROFILE_RATE_LIMIT_WINDOW` - Time window in seconds (default: 86400)

---

## 12. Deployment Considerations

### 12.1 Database Migrations
Run Flyway migrations in order: V1, V2, V3...

### 12.2 Configuration
Set environment variables before deployment

### 12.3 Rollback Plan
[Rollback procedure if deployment fails]

---

## 13. Appendices

### 13.1 Business Rules Mapping

| BR ID | SRS Section | Implementation | Class/Method |
|-------|------------|----------------|--------------|
| BR-001 | 3.1.1 | Audit logging | AuditService.logAccess() |
| BR-002 | 3.2.1 | Rate limiting | RateLimitService.checkRateLimit() |

### 13.2 Change Log

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | [Date] | [Author] | Initial version |

---

**Approval**

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Technical Lead | | | |
| Architect | | | |
| QA Lead | | | |
