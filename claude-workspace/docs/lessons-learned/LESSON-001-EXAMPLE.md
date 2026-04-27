---
id: LESSON-001
date: 2026-02-03
category: Database
severity: High
author: AI Agent
tags: [postgresql, connection-pool, performance, production]
confluence_page: 147621793
---

# LESSON-001: PostgreSQL Connection Pool Exhaustion

## Problem

Application experienced intermittent 500 errors during peak traffic hours. Users reported:
- Slow response times (>5 seconds)
- Random connection refused errors
- Some requests timing out completely

Error logs showed:
```
PSQLException: FATAL: remaining connection slots are reserved for non-replication superuser connections
FATAL: sorry, too many clients already
```

**Impact**: 15% of user requests failing during peak hours, significant user complaints.

## Root Cause

After investigation, we found:
1. **Connection pool size too small**: Default HikariCP pool size was 10 connections
2. **High concurrent load**: Application had 20-30 concurrent threads making database calls during peak traffic
3. **Connection leak**: Some database operations weren't properly closing connections in error scenarios
4. **No connection timeout**: Connections waited indefinitely, blocking new requests

**Why it wasn't caught earlier:**
- Load testing only simulated 10 concurrent users (below threshold)
- Connection leaks accumulated slowly over days
- No monitoring on connection pool metrics

## Solution

### 1. Increased Connection Pool Size
Updated `application.properties`:
```java
# HikariCP Configuration
spring.datasource.hikari.maximum-pool-size=50
spring.datasource.hikari.minimum-idle=10
spring.datasource.hikari.connection-timeout=30000
spring.datasource.hikari.idle-timeout=600000
spring.datasource.hikari.max-lifetime=1800000
spring.datasource.hikari.validation-timeout=5000
spring.datasource.hikari.leak-detection-threshold=60000
```

**Rationale**: 50 connections supports up to 50 concurrent DB operations with buffer for spikes.

### 2. Fixed Connection Leaks
Added proper try-with-resources for all JDBC operations:

```java
// Before (prone to leaks on exception)
Connection conn = dataSource.getConnection();
PreparedStatement stmt = conn.prepareStatement(sql);
ResultSet rs = stmt.executeQuery();
// ... processing
conn.close(); // Might not execute if exception thrown

// After (guaranteed cleanup)
try (Connection conn = dataSource.getConnection();
     PreparedStatement stmt = conn.prepareStatement(sql);
     ResultSet rs = stmt.executeQuery()) {
    // ... processing
} // Auto-closes even on exception
```

### 3. Added Connection Pool Monitoring
Implemented Prometheus metrics:
```java
@Bean
public MeterBinder hikariMetrics(HikariDataSource dataSource) {
    return new HikariDataSourcePoolMetrics(dataSource, "hikari", Collections.emptyList());
}
```

Grafana dashboard now tracks:
- Active connections
- Idle connections
- Pending connection requests
- Connection creation time
- Connection acquisition time

### 4. Improved Load Testing
Updated load test to simulate realistic peak traffic:
- 50 concurrent users (previously 10)
- 5-minute sustained load (previously 1 minute)
- Database connection monitoring during test

## Key Takeaways

1. **Always size connection pools for peak load + buffer**
   - Don't rely on defaults (usually too small for production)
   - Formula: `max_pool_size ≥ (concurrent_threads × 1.5)`
   - Add 20% buffer for traffic spikes

2. **Use try-with-resources for ALL database operations**
   - Prevents connection leaks on exceptions
   - Makes code cleaner and safer
   - Java compiler enforces cleanup

3. **Monitor connection pool metrics in production**
   - Active/idle connection count
   - Connection wait time
   - Connection creation rate
   - Leak detection alerts

4. **Load test with realistic scenarios**
   - Match production concurrent user count
   - Sustained load (not just quick bursts)
   - Monitor database connections during test

5. **Set appropriate timeouts**
   - Connection timeout prevents indefinite waits
   - Idle timeout reclaims unused connections
   - Max lifetime prevents stale connections

6. **Enable leak detection in non-production**
   - HikariCP `leak-detection-threshold` helps identify problem areas
   - Log warnings when connections held too long
   - Fix leaks before they reach production

## References

- **Task**: [TASK-042](../tasks/TASK-042.md)
- **Code Review**: [TASK-042-review.md](../reviews/TASK-042-review.md)
- **Test Report**: [TASK-042-test-report.md](../test-reports/TASK-042-test-report.md)
- **HikariCP Documentation**: https://github.com/brettwooldridge/HikariCP
- **PostgreSQL Connection Limits**: https://www.postgresql.org/docs/current/runtime-config-connection.html

---

**Published to Confluence**: 2026-02-03 14:30:00
**Page**: [Lessons Learned](https://vissoft.atlassian.net/wiki/spaces/TECH/pages/147621793)
