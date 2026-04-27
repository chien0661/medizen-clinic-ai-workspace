# PROJECT.md - [Your Project Name]

**This file provides project-specific context for Claude Code when working with this codebase.**
**Always read this file in conjunction with CLAUDE.md for complete guidance.**

---

## Workspace Configuration

> 📋 **TEMPLATE INSTRUCTIONS**: Configure workspace type for this project.
> For **monorepo** or **standalone**: leave default. For **microservice workspace**: set type and list repos.

```yaml
# workspace-type: monorepo        # Single repo with all source code (default)
# workspace-type: microservice    # This repo is a workspace; source code is in separate repos

# repos:                          # Only needed for workspace-type: microservice
#   service-name:
#     path: ../relative-path-to-repo   # Relative path from this workspace root
#     description: Short description
#   another-service:
#     path: ../another-service
#     description: Short description
```

> When `workspace-type: microservice`, `/commit-push-pr TASK-ID` will commit and create PRs
> in each repo listed under `affected-repos` in the task's frontmatter.

---

## Project Identity

> 📋 **TEMPLATE INSTRUCTIONS**: Replace all placeholders below with your actual project details

- **Project Name**: [your-project-name] ([Your Project Display Name])
- **Organization**: [Your Organization] ([your.package.namespace])
- **Application Context**: /[your-app-context] (if web application)
- **Port**:
  - Default: [port-number] (e.g., 8080, 3000, 5000, 8000)
  - [Profile/Environment Name]: [port-number] (configured in [config-file])
- **Language Version**: [Language and version - e.g., Java 17, Node.js 20, Python 3.11, Go 1.21]
- **Framework**: [Framework and version - e.g., Spring Boot 3.2, Express 4.18, FastAPI 0.104, Gin 1.9]

## Architecture Pattern

> 📋 **TEMPLATE INSTRUCTIONS**: Describe your project's architecture pattern. Common options:
> - Hexagonal Architecture (Ports & Adapters)
> - Layered Architecture (Controller → Service → Repository)
> - Clean Architecture
> - Microservices Architecture
> - Event-Driven Architecture

This project follows **[Your Architecture Pattern]** with clear separation of concerns:

```
[your.package.namespace]/
├── [layer-1]/                    # [Description]
│   ├── [component-1]/            # [Description]
│   ├── [component-2]/            # [Description]
│   └── [component-3]/            # [Description]
│
├── [layer-2]/
│   ├── [core or domain]/         # [CORE DOMAIN LAYER or similar]
│   │   ├── entity/               # [Entities/Models]
│   │   ├── dto/                  # [Data Transfer Objects]
│   │   ├── mapper/               # [Object mappers]
│   │   ├── exception/            # [Custom exceptions]
│   │   └── util/                 # [Utilities]
│   │
│   ├── [port or interface]/      # [Interfaces/Contracts]
│   │   ├── repository/           # [Data access ports]
│   │   ├── client/               # [External client ports]
│   │   └── messaging/            # [Messaging ports]
│   │
│   └── service/                  # [Business logic]
│
└── [infrastructure]/             # [Infrastructure implementations]
    ├── repository/               # [Repository implementations]
    ├── client/                   # [HTTP client implementations]
    └── messaging/                # [Messaging implementations]
```

### Architectural Principles

> 📋 **TEMPLATE INSTRUCTIONS**: List your key architectural principles and design decisions

1. **[Principle 1]**: [Description]
2. **[Principle 2]**: [Description]
3. **[Principle 3]**: [Description]
4. **[Principle 4]**: [Description]
5. **[Principle 5]**: [Description]

**Example principles:**
- Core Domain is Independent: Core has no dependencies on infrastructure
- Dependency Inversion: High-level modules don't depend on low-level modules
- Single Responsibility: Each component has one reason to change

## Technology Stack

> 📋 **TEMPLATE INSTRUCTIONS**: List all technologies used in your project. Remove sections that don't apply.

### Core Framework
- **[Framework Name & Version]**: [e.g., Express 4.x, Spring Boot 3.x, FastAPI 0.104, Django 4.2]
- **Language**: [e.g., TypeScript 5.0, Python 3.11, Java 17, Go 1.21]
- **Build Tool**: [e.g., npm, pip, Maven, Gradle, cargo, go build]

### Database
- **[Database Name]**: [e.g., PostgreSQL, MongoDB, MySQL, Redis]
  - Driver/Client: `[driver-library:version]` (e.g., pg, mongoose, mysql2, ioredis)
  - Connection pool: [e.g., pgBouncer, HikariCP, default driver pooling]
  - ORM/ODM: [e.g., Prisma, TypeORM, SQLAlchemy, Hibernate JPA, Mongoose]
  - **IMPORTANT**: Document any database-specific quirks or behaviors

### Authentication & Authorization
- **[Auth Solution]**: [e.g., Keycloak, Auth0, JWT, OAuth2]
  - [Integration details]
  - [Custom implementations]
  - [Permission/role system]
  - Located in: `[package/directory]`

### Messaging
- **[Messaging System]**: [e.g., Kafka, RabbitMQ, AWS SQS, Redis Pub/Sub]
  - [Library/client version]
  - [Topics/queues structure]
  - Producer/consumer location: `[directory]`
  - [Retry/error handling strategy]

### Caching
- **[Cache Solution]**: [e.g., Redis, Memcached, Hazelcast, in-memory]
  - [Client library and version]
  - [Cache strategy: write-through, write-behind, cache-aside]
  - [TTL policies]
  - Implementation location: `[directory]`

### File Storage
- **[Storage Solution]**: [e.g., S3, MinIO, Azure Blob, local filesystem]
  - [Configuration details]
  - [Access patterns]

### Security & Secrets
- **[Secret Management]**: [e.g., Vault, AWS Secrets Manager, Azure Key Vault]
  - [Integration method]
  - [Configuration location]
- **[Encryption]**: [e.g., Jasypt, AWS KMS]
  - [Encryption strategy]

### Object Mapping
- **[Mapper Library]**: [e.g., MapStruct, ModelMapper, Jackson, class-transformer]
  - [Mapping strategy]
  - Mappers location: `[directory]`
  - [Compiler arguments if needed]

### Utilities
- **[Utility Libraries]**: [List key utility libraries]
  - [Library 1]: [Purpose]
  - [Library 2]: [Purpose]
  - [Library 3]: [Purpose]

### Logging
- **[Logging Framework]**: [e.g., Logback, Log4j2, Winston, Pino]
  - Configuration: `[config file path]`
  - [Log levels and patterns]
  - [Log aggregation: e.g., ELK, Splunk, CloudWatch]

## Custom/Internal Libraries

> 📋 **TEMPLATE INSTRUCTIONS**: Document any proprietary, internal, or custom libraries used in this project.
> Remove this section if you don't have custom libraries.

These are custom/internal libraries specific to this organization:

1. **[library-name]** (version)
   - [Purpose and functionality]
   - [Key features]
   - [Location/package]

2. **[library-name]** (version)
   - [Purpose and functionality]
   - [Key features]
   - [Location/package]

**Example:**
- **company-data-access** (1.0.0): Common database utilities and base repositories
- **company-messaging** (2.1.0): Internal messaging abstractions and patterns
- **company-security** (1.5.0): Organization-wide security utilities and auth helpers

## Configuration Management

> 📋 **TEMPLATE INSTRUCTIONS**: Document your configuration file structure and key settings

### Configuration Files Structure
```
[config-directory-path]/
├── [config-file-1]               # [Description - e.g., Base configuration]
├── [config-file-2]               # [Description - e.g., Local development]
├── [config-file-3]               # [Description - e.g., Production environment]
└── [logging-config]              # [Logging configuration]
```

**Example (Spring Boot):**
```
src/main/resources/
├── application.yml               # Base configuration
├── application-dev.yml           # Development environment
├── application-prod.yml          # Production environment
└── logback-spring.xml            # Logging configuration
```

**Example (Node.js):**
```
config/
├── default.json                  # Base configuration
├── development.json              # Development overrides
├── production.json               # Production overrides
└── custom-environment-variables.json  # Environment variable mappings
```

**Example (Python/Django):**
```
project/
├── settings/
│   ├── base.py                   # Base configuration
│   ├── development.py            # Development settings
│   ├── production.py             # Production settings
│   └── __init__.py
└── .env.example                  # Environment variables template
```

**Example (Go):**
```
config/
├── config.yaml                   # Base configuration
├── config.dev.yaml               # Development overrides
├── config.prod.yaml              # Production overrides
└── config.go                     # Config loading logic
```

### Key Configuration Properties

> 📋 **TEMPLATE INSTRUCTIONS**: List important configuration properties and their purposes

**Application Settings:**
```properties
[property.name]=[value]           # [Description]
[property.name]=[value]           # [Description]
```

**Database Settings:**
```properties
[db.property.name]=[value]        # [Description]
```

**Integration Settings:**
```properties
[integration.property]=[value]    # [Description]
```

**Example (YAML - Python, Node.js, Ruby, etc.):**
```yaml
# Application
app:
  name: my-application
  port: 8080
  version: 1.0.0

# Database
database:
  url: postgresql://localhost:5432/mydb
  username: ${DB_USER}
  password: ${DB_PASS}

# Cache
cache:
  type: redis
  host: localhost
  port: 6379
```

**Example (JSON - Node.js, Python, etc.):**
```json
{
  "app": {
    "name": "my-application",
    "port": 8080
  },
  "database": {
    "host": "localhost",
    "port": 5432,
    "name": "mydb"
  }
}
```

**Example (Environment Variables - Universal):**
```bash
APP_NAME=my-application
APP_PORT=8080
DATABASE_URL=postgresql://localhost:5432/mydb
REDIS_HOST=localhost
REDIS_PORT=6379
```

## Package/Module Naming Conventions

> 📋 **TEMPLATE INSTRUCTIONS**: Document your actual package or module structure (NOT generic examples)

### Project-Specific Package Structure

**Document your ACTUAL structure (NOT generic examples):**

**TypeScript/JavaScript Example:**
```typescript
// ✅ Correct - Use YOUR actual module paths
import { UserService } from '@yourapp/modules/users/services';
import { AuthController } from '@yourapp/api/auth/controller';

// ❌ Wrong - Generic placeholder examples
import { Service } from '@company/project/service';
```

**Python Example:**
```python
# ✅ Correct - Use YOUR actual package structure
from yourapp.modules.users.services import UserService
from yourapp.api.auth.controller import AuthController

# ❌ Wrong - Generic examples
from company.project.service import Service
```

**Go Example:**
```go
// ✅ Correct - Use YOUR actual package paths
import "github.com/yourorg/yourapp/internal/users/service"
import "github.com/yourorg/yourapp/api/auth"
```

**Java/Kotlin Example:**
```java
// ✅ Correct - Use YOUR actual package structure
package com.yourcompany.yourapp.domain.entity;
package com.yourcompany.yourapp.service;

// ❌ Wrong - Generic placeholder
package com.company.project.service;
```

**Package/Module Path Patterns:**
- **TypeScript/JavaScript**: `src/modules/[feature]/[component]`
- **Python**: `src.[module].[feature].[component]` or `yourapp/[module]/[feature]`
- **Go**: `github.com/[org]/[project]/[internal|pkg]/[module]`
- **Java/Kotlin**: `com.[company].[project].[module].[component]`
- **C#**: `YourCompany.YourProject.Module.Component`
- **Rust**: `crate::module::feature::component`

### Module Organization

Document how modules/packages are organized:
```
[root-package-or-directory]/
├── [module-1]/                   # [Purpose]
├── [module-2]/                   # [Purpose]
└── [module-3]/                   # [Purpose]
```

## Domain-Specific Features

> 📋 **TEMPLATE INSTRUCTIONS**: Document custom features, patterns, and domain-specific implementations in your project.
> This helps AI agents understand your unique business logic and technical implementations.

### Feature 1: [Feature Name]
- **Purpose**: [What it does]
- **Implementation**: [How it works]
  - Location: `[package/directory]`
  - Key classes/files: `[ClassNames or filenames]`
  - Integration points: [What it connects to]

### Feature 2: [Feature Name]
- **Purpose**: [What it does]
- **Implementation**: [How it works]
  - Location: `[package/directory]`
  - Configuration: `[config location]`
  - Usage pattern: [How to use it]

### Feature 3: [Feature Name]
- **Data flow**: [How data flows through this feature]
- **Key components**:
  - Component 1: [Description and location]
  - Component 2: [Description and location]

**Examples to document:**
- Custom permission/authorization systems
- Audit logging implementations
- Multi-tenancy features
- Custom authentication flows
- Domain-specific business rules
- Integration patterns with external systems
- Custom validation frameworks
- Event sourcing implementations

## Development Workflow

> 📋 **TEMPLATE INSTRUCTIONS**: Document your project's build and development workflow

### Environment Setup

**Prerequisites:**
```bash
# [Runtime/Language] - e.g., Java, Node.js, Python
# Version: [version-number]
# Installation: [instructions or link]

# [Build Tool] - e.g., Maven, Gradle, npm, pip
# Version: [version-number]

# [Other Dependencies] - e.g., Docker, specific CLIs
```

**Environment Variables:**
```bash
# Required environment variables
export [VAR_NAME]=[value]           # [Description]
export [VAR_NAME]=[value]           # [Description]
```

### Package Manager / Repository Configuration

> 📋 **IMPORTANT**: Document if your project uses:
> - Private package repositories (Maven Nexus, npm registry, PyPI)
> - Required authentication or profiles
> - Corporate proxies or mirrors

**If using private repositories:**
```
Configuration file: [path-to-config]
Required profiles: [profile-names]
Authentication: [how to set up credentials]
```

### Build Commands

> 📋 **TEMPLATE INSTRUCTIONS**: Provide actual build commands for your project
>
> **⚡ Token Optimization**: Always use quiet/silent flags to minimize token usage
> - Maven: Add `-q` flag
> - npm/yarn/pnpm: Add `--silent` flag
> - Gradle: Add `-q` or `--quiet` flag
> - Go: Use `-v` flag only when needed
> - Cargo: Use `--quiet` flag

**Development Build:**
```bash
# Build command (token-optimized)
[build-command] [quiet-flag]        # e.g., npm run build --silent, mvn clean install -q, cargo build --quiet

# Examples by platform:
# Maven:    mvn clean install -q
# Gradle:   gradle build -q
# npm:      npm run build --silent
# yarn:     yarn build --silent
# pnpm:     pnpm build --silent
# Go:       go build .
# Cargo:    cargo build --quiet
```

**Production Build:**
```bash
# Production build command (token-optimized)
[build-command] [quiet-flag]        # e.g., npm run build:prod --silent, cargo build --release --quiet

# Examples:
# Maven:    mvn clean package -q -P production
# Gradle:   gradle build -q -Pproduction
# npm:      npm run build:prod --silent
# Docker:   docker build -t app:latest . 2>&1 | grep -v "^Step"
```

**Running the Application:**
```bash
# Development mode
[run-command]                       # e.g., npm run dev, python main.py, go run ., cargo run

# Production mode
[run-command]                       # e.g., node dist/main.js, python -m app, ./binary, docker run

# Examples:
# Spring Boot: mvn spring-boot:run -q
# Express:     npm run dev --silent
# FastAPI:     uvicorn app.main:app --reload
```

**Testing:**
```bash
# Run all tests (token-optimized)
[test-command] [quiet-flag]         # e.g., npm test --silent, pytest -q, mvn test -q

# Examples by platform:
# Maven:    mvn clean test -q
# Gradle:   gradle test -q
# npm:      npm test --silent
# pytest:   pytest -q
# Go:       go test -v ./...
# Cargo:    cargo test --quiet
# JUnit:    mvn test -q -Dtest=TestClass

# Run specific test suite
[test-command] [options]            # e.g., npm test MyTest.spec.ts --silent, pytest tests/unit/ -q
```

**API Testing (Postman/Newman):**
```bash
# Smoke tests (basic endpoint checks)
newman run collections/smoke-tests.json --reporters cli --reporter-cli-no-console

# Integration tests (full API test suite)
newman run collections/integration-tests.json --reporters cli,json --reporter-json-export results.json

# Regression tests (full regression suite)
newman run collections/regression-tests.json --iteration-count 1 --bail
```

### Helper Scripts

> 📋 **TEMPLATE INSTRUCTIONS**: Document any helper scripts in your project

| Script Name | Purpose | Usage |
|-------------|---------|-------|
| `[script-1]` | [What it does] | `[how to run]` |
| `[script-2]` | [What it does] | `[how to run]` |
| `[script-3]` | [What it does] | `[how to run]` |

**Example:**
| Script | Purpose | Usage |
|--------|---------|-------|
| `build.sh` | Clean build with tests | `./build.sh` |
| `start-dev.sh` | Start dev server | `./start-dev.sh` |
| `deploy-staging.sh` | Deploy to staging | `./deploy-staging.sh` |

### Troubleshooting Build Issues

> 📋 **TEMPLATE INSTRUCTIONS**: Document common build issues and their solutions specific to your project

#### Issue: [Common Issue #1]

**Symptoms**: [What the error looks like]

**Cause**: [Why it happens]

**Solution**:
```bash
# Commands to fix the issue
[fix-command-1]
[fix-command-2]
```

**Why this happens**: [Detailed explanation]

#### Issue: [Common Issue #2]

**Symptoms**: [What the error looks like]

**Cause**: [Why it happens]

**Solution**:
```bash
# Commands to fix the issue
[fix-command]
```

**Prevention**: [How to avoid this issue]

**Examples of common build issues:**
- Dependency resolution failures
- Environment variable not set correctly
- Wrong SDK/runtime version
- Network/proxy issues accessing repositories
- Missing required tools or configurations
- Permission issues
- Port conflicts
- Test failures blocking builds

### Database Schema Management

> 📋 **TEMPLATE INSTRUCTIONS**: Document your database migration and schema management strategy

- **Migration Tool**: [e.g., Flyway, Liquibase, Alembic, Prisma Migrate, manual scripts]
- **Script Location**: `[directory-path]`
- **Naming Convention**: `[pattern]` (e.g., `V1__description.sql`, `001_create_users.sql`)
- **Audit Trail**: [How you track schema changes - e.g., Hibernate Envers, custom audit tables]
- **Rollback Strategy**: [How to rollback migrations]

**Example:**
- Migration Tool: Flyway
- Location: `src/main/resources/db/migration`
- Naming: `V{version}__{description}.sql` (e.g., `V1__create_users_table.sql`)
- Applied on: Application startup

### Internationalization (i18n)

> 📋 **TEMPLATE INSTRUCTIONS**: Document i18n support if your application requires it.
> Remove this section if not applicable.

- **Message Files**: `[filenames]` (e.g., `messages_en.properties`, `translations/en.json`)
- **Supported Languages**: [List languages with codes - e.g., English (en), Spanish (es)]
- **Location**: `[directory-path]`
- **Default Language**: [language-code]
- **Fallback Strategy**: [What happens when translation is missing]

**Example (Node.js/i18next):**
- Files: `locales/en/translation.json`, `locales/es/translation.json`
- Location: `src/locales/`
- Default: English (en)
- Usage: `t('message.key')` in code

**Example (Python/Django):**
- Files: `locale/en/LC_MESSAGES/django.po`, `locale/es/LC_MESSAGES/django.po`
- Location: `project/locale/`
- Default: English (en-US)
- Usage: `{% trans "message" %}` in templates, `_("message")` in code

**Example (Go/i18n):**
- Files: `locales/en.json`, `locales/es.json`
- Location: `internal/locales/`
- Default: English (en)
- Usage: `i18n.T("message.key")` in code

## Testing Strategy

> 📋 **TEMPLATE INSTRUCTIONS**: Document your testing approach, frameworks, and standards

### Unit Tests
- **Owner**: [Developer / QA team]
- **Location**: `[test-directory-path]`
- **Framework**: [e.g., Jest, pytest, JUnit, RSpec, XCTest]
- **Naming Convention**: `[pattern]` (e.g., `*.spec.ts`, `test_*.py`, `*Test.java`, `*_test.go`)
- **Target Coverage**: [percentage] (e.g., 80%, 90%+)
- **Mocking Library**: [e.g., Jest (built-in), unittest.mock, Mockito, Sinon]

### Integration Tests
- **Framework**: [e.g., Supertest, pytest fixtures, @SpringBootTest, testing package (Go)]
- **Database**: [How you test with database - e.g., TestContainers, in-memory DB, test database instance]
- **External Services**: [How you test integrations - e.g., WireMock, test containers, mock servers]
- **Location**: `[test-directory-path]`

### End-to-End (E2E) Tests
- **Framework**: [e.g., Playwright, Cypress, Selenium, Puppeteer]
- **Location**: `[test-directory-path]`
- **Scope**: [What's covered by E2E tests]

### API/Contract Tests
- **Framework**: [e.g., Postman/Newman, Pact, REST Assured, Supertest, pytest]
- **Location**: `[test-directory-path]`
- **See**: [Reference to detailed testing documentation]

**Example (Node.js/TypeScript):**
- Unit: Jest in `src/**/*.spec.ts`
- Integration: Supertest + Docker test containers
- E2E: Playwright tests in `e2e/`
- Coverage target: 85%

**Example (Python):**
- Unit: pytest in `tests/unit/`
- Integration: pytest + Docker Compose for dependencies
- E2E: Playwright or Selenium in `tests/e2e/`
- Coverage target: 80%

**Example (Go):**
- Unit: Go testing package in `*_test.go` files
- Integration: testcontainers-go for dependencies
- E2E: Custom test suite in `e2e/`
- Coverage target: 75%

## Code Quality & SonarQube

> 🔧 **NOTE**: SonarQube integration is **OPTIONAL**. Teams can choose to enable or disable it based on their needs.

### Enable/Disable SonarQube Integration

**SonarQube integration is enabled by default in this template.** To disable or enable it:

#### To DISABLE SonarQube (Skip all quality gate checks):

**Option 1: Disable MCP Server (Recommended)**
Edit `.mcp.json` and set `disabled: true`:
```json
{
  "mcpServers": {
    "sonarqube": {
      "disabled": true,  // ← Change to true to disable
      ...
    }
  }
}
```

**Option 2: Remove Project Key**
Remove or comment out the SonarQube configuration section from this PROJECT.md file.

**What happens when disabled:**
- ✅ Code review relies entirely on manual review
- ✅ `/commit-push-pr` pushes code directly without quality gate checks
- ✅ No SonarQube section in review reports
- ✅ All workflows continue to work normally

#### To ENABLE SonarQube:

**Requirements:**
1. SonarQube server access (https://sonarqube.vissoft.vn)
2. Project key from SonarQube
3. SonarQube MCP server enabled in `.mcp.json` (`disabled: false`)
4. Project key configured in this PROJECT.md file (see below)

### SonarQube Configuration (Required if Enabled)

- **Server**: https://sonarqube.vissoft.vn (on-premise)
- **Project Key**: `[INSERT YOUR SONARQUBE PROJECT KEY HERE]`
  - Example: `com.company:my-project` or `org.example:api-service`
  - Find in SonarQube: Go to your project → Project Information → Project Key
  - ⚠️ **REQUIRED**: Must be configured for SonarQube integration to work
- **Quality Gate**: `[INSERT QUALITY GATE NAME]` (e.g., "Sonar way", "Company Standards")
- **Dashboard**: https://sonarqube.vissoft.vn/dashboard?id=[your-project-key]

### Quality Gate Rules (If Enabled)

**If SonarQube is enabled**, code must meet these conditions to be pushed:

1. **New Bugs**: 0 (no new bugs introduced)
2. **New Vulnerabilities**: 0 (no new security vulnerabilities)
3. **New Code Coverage**: ≥ 80% (all new code must be tested)
4. **New Code Smells**: ≤ 5 (minor technical debt acceptable)
5. **Security Hotspots Reviewed**: 100% (all hotspots must be reviewed)

> ⚠️ **These thresholds are enforced automatically by `/commit-push-pr` if SonarQube is enabled. Push will be BLOCKED if quality gate fails.**
>
> 🔧 **If SonarQube is disabled**, code review and quality checks rely entirely on manual review.

### Running SonarQube Analysis

#### Local Analysis (Before Committing)

Run SonarQube analysis locally to validate code quality before committing:

**Maven projects:**
```bash
mvn clean verify sonar:sonar
```

**Gradle projects:**
```bash
./gradlew sonarqube
```

**Node.js projects:**
```bash
npm run sonar
# or
npm run sonar:scan
```

**Python projects:**
```bash
sonar-scanner
# or
python -m pytest --cov --cov-report=xml && sonar-scanner
```

**Other languages:**
```bash
sonar-scanner
```

#### Automatic Validation (During Commit-Push-PR) - If Enabled

**If SonarQube is enabled**, the `/commit-push-pr` command automatically validates against SonarQube:

```bash
/commit-push-pr TASK-001
```

**What happens (if SonarQube enabled):**
1. Code is committed locally
2. SonarQube quality gate is checked
3. If **PASS**: Code is pushed, PR is created
4. If **FAIL**: Push is blocked, detailed report is shown
5. If **ERROR**: Push is blocked (fail-safe mode)

**What happens (if SonarQube disabled):**
1. Code is committed locally
2. Code is pushed directly to remote
3. PR is created

**No manual scan needed before using `/commit-push-pr`** - it automatically validates if SonarQube is configured.

### SonarQube Token Setup

✅ **Already Configured** - The SonarQube token is pre-configured in `.mcp.json` for company-wide use.

**No setup required** - the MCP server is ready to use immediately.

The company-wide token (`squ_fe8873...`) is configured in `.mcp.json` with read-only access to all SonarQube projects.

**Optional: Use Personal Token**

If you prefer to use your own token:

1. Login to https://sonarqube.vissoft.vn
2. Click on your avatar → **My Account**
3. Go to **Security** tab → **Generate Token**
4. Configure token:
   - **Name**: `MCP Server - [Your Name]`
   - **Type**: User Token
5. Copy the token (starts with `squ_`)
6. Update `.mcp.json` line 56 with your personal token

**Verify server works:**
```bash
# Test MCP server
cd mcp-servers/sonarqube-server
node test-connection.js
# Should show: "✅ All tests passed!"
```

### Troubleshooting Quality Gate Failures

If `/commit-push-pr` blocks your push due to quality gate failure:

#### 1. View Detailed Report

Click on the SonarQube dashboard link provided in the error message:
```
📊 View detailed report:
https://sonarqube.vissoft.vn/dashboard?id=your-project&branch=feature/task-001
```

This shows:
- Specific issues (bugs, vulnerabilities, code smells)
- File locations and line numbers
- Coverage gaps
- Security hotspots

#### 2. Fix Issues by Category

**For New Bugs:**
```bash
# Review and fix bugs in SonarQube dashboard
# Example: Null pointer dereference, resource leak, etc.
# Fix the code
git add .
git commit -m "fix: address sonarqube bugs"
```

**For Low Coverage:**
```bash
# Add unit tests for uncovered code
# Check coverage locally: mvn test jacoco:report
# Add tests
git add .
git commit -m "test: add coverage for new code"
```

**For Code Smells:**
```bash
# Refactor code following SonarQube suggestions
# Example: Extract method, reduce complexity, etc.
git add .
git commit -m "refactor: improve code quality"
```

**For Security Hotspots:**
```bash
# Review security concerns in SonarQube
# Mark as reviewed (if false positive) OR fix the issue
git add .
git commit -m "security: address security hotspots"
```

#### 3. Re-validate

```bash
# Optional: Run local analysis to verify fixes
mvn sonar:sonar

# Re-run commit-push-pr
/commit-push-pr TASK-001
```

### Common Issues

**Issue: "Project not found" or "Project never analyzed"**

**Solution**: Run initial analysis
```bash
mvn clean verify sonar:sonar -Dsonar.projectKey=your-project-key
```

**Issue: "Authentication failed" (401 error)**

**Solution**: Check token
```bash
# Verify SONARQUBE_TOKEN is set
echo $SONARQUBE_TOKEN

# Regenerate token if expired
# Follow "SonarQube Token Setup" above
```

**Issue: "SonarQube server unreachable"**

**Solution**: Verify connectivity
```bash
# Check server is accessible
curl https://sonarqube.vissoft.vn/api/system/status

# Check network/VPN connection
# Verify firewall allows access
```

**Issue: "Quality gate too strict for my changes"**

**Solution**: Discuss with team
1. Quality gates exist for a reason - prefer fixing code over relaxing standards
2. If threshold needs adjustment, discuss with team lead
3. Requires SonarQube admin access to modify quality gate

### Emergency Bypass (Not Recommended)

⚠️ **Only use in emergencies** (SonarQube down, critical hotfix):

```bash
# Manual push (bypasses quality gate)
git push --no-verify

# IMPORTANT:
# 1. Document why bypass was needed in PR description
# 2. Fix quality issues immediately after push
# 3. Report bypass to team
```

**Note**: This bypass is logged and should be rare. Quality gates protect code quality and should not be routinely bypassed.

### Integration with Multi-Agent Workflow

SonarQube quality gate is enforced at the **commit-push-pr** stage:

```
[Implementation Agent] → Code + Unit Tests → Commit locally
                                                   ↓
                                        [SonarQube Validation]
                                                   ↓
                                    ✅ PASS → Push → Create PR
                                    ❌ FAIL → Block + Report
                                    ❌ ERROR → Block (fail-safe)
```

**Quality gates ensure:**
- Only high-quality code reaches remote repository
- Code reviews happen on quality-validated code
- Technical debt is controlled proactively
- Security issues are caught before PR creation

## Agent Model Configuration

> **OPTIONAL**: Override the default AI model for each agent. Agents read these values at runtime.
> If not specified, the defaults from each skill's SKILL.md are used.

### Default Model Assignments

| Agent | Default Model | Rationale |
|-------|---------------|-----------|
| Code Implementation | `sonnet` | Code generation performs well with Sonnet, ~60% cost savings vs Opus |
| Code Review | `opus` | Deep reasoning needed for security/logic analysis |
| Test | `sonnet` | Test generation doesn't require Opus-level reasoning |
| Documentation | `haiku` | Simplest task, sufficient quality at ~90% cost savings |
| Manager | `opus` | Orchestration requires strong decision-making |

### Project-Specific Overrides

> 📋 **TEMPLATE INSTRUCTIONS**: Uncomment and modify the lines below to override model assignments for this project.
> Use `opus` for maximum quality, `sonnet` for balanced cost/quality, `haiku` for maximum cost savings.

```yaml
# agent-models:
#   code-implementation: sonnet    # Options: opus, sonnet, haiku
#   code-review: opus              # Options: opus, sonnet, haiku
#   test: sonnet                   # Options: opus, sonnet, haiku
#   documentation: haiku           # Options: opus, sonnet, haiku
#   manager: opus                  # Options: opus, sonnet, haiku
```

**When to override:**
- **All `opus`**: Critical/regulated projects where quality is paramount (e.g., healthcare, finance)
- **All `sonnet`**: Budget-conscious projects with good code quality needs
- **All `haiku`**: Prototype/POC projects where speed and cost matter most
- **Mixed (default)**: Best balance of quality and cost for production projects

---

## Quality Gates Configuration

> **IMPORTANT**: These thresholds are used by all agents (Implementation, Review, Test, Documentation).
> Customize them per project. Agents read these values from PROJECT.md at runtime.

### Code Coverage
- **Minimum Coverage (new code)**: 80%
- **Minimum Coverage (overall)**: 70%

### Code Review
- **Max Review Iterations**: 3 (task flagged as stuck after this)
- **Auto-approve Minor Issues**: false (set to true to auto-approve when only MINOR issues found)

### Testing
- **Required Test Pass Rate**: 100% (all tests must pass before moving to documentation)
- **Unit Tests Required**: true
- **Integration Tests Required**: true (set to false if not applicable)
- **E2E Tests Required**: false (set to true for critical features)

### SonarQube (if enabled)
- **Quality Gate Must Pass**: true
- **Max New Bugs**: 0
- **Max New Vulnerabilities**: 0
- **Max New Code Smells**: 5
- **Security Hotspots Reviewed**: 100%

### Build
- **Build Must Pass Before Review**: true
- **Lint Must Pass Before Review**: true (set to false if no linter configured)

> **How agents use these values:**
> - **Implementation Agent**: Checks coverage threshold before marking IN_REVIEW
> - **Review Agent**: Validates coverage, lint, SonarQube thresholds during review
> - **Test Agent**: Enforces test pass rate before marking DOCUMENTING
> - **Manager Agent**: Detects stuck tasks based on max review iterations

---

## Common Patterns in This Codebase

> 📋 **TEMPLATE INSTRUCTIONS**: Document recurring patterns, conventions, and idioms used throughout your codebase.
> This helps AI agents write code that matches your project's style.

### Pattern 1: [Pattern Name]

**Purpose**: [What problem this pattern solves]

**Implementation**:
```[language]
// Example code showing the pattern
[code-example]
```

**Usage**: [When and how to use this pattern]
**Location**: [Where to find examples in the codebase]

### Pattern 2: [Pattern Name]

**Purpose**: [What problem this pattern solves]

**Implementation**:
```[language]
// Example code showing the pattern
[code-example]
```

**When to use**: [Scenarios where this pattern applies]

### Pattern 3: [Pattern Name]

**Purpose**: [What problem this pattern solves]

**Example**:
```[language]
// Example code
[code-example]
```

**Common Patterns to Document:**
- Dependency injection patterns
- Error handling conventions
- Logging patterns
- Transaction management
- Async/concurrent programming patterns
- API response formatting
- Validation approaches
- Security patterns (authentication, authorization)
- Data mapping/transformation
- Configuration patterns
- Resource management (file handles, connections)
- Retry and circuit breaker patterns

## Environment-Specific Notes

> 📋 **TEMPLATE INSTRUCTIONS**: Document each environment (local, dev, staging, prod) with their specific configurations

### [Environment 1 - e.g., Local Development]
- **Profile/Mode**: `[how-to-activate]` (e.g., `-Dspring.profiles.active=local`, `NODE_ENV=development`)
- **Config File**: `[config-file-name]`
- **Database**: [Database setup - e.g., Local PostgreSQL, SQLite, Docker container]
- **External Services**: [How external services are configured - e.g., mock servers, local instances]
- **Port**: [port-number]
- **Base URL**: `[url]`

### [Environment 2 - e.g., Development/Staging]
- **Profile/Mode**: `[how-to-activate]`
- **Config File**: `[config-file-name]`
- **Database**: [Database connection details or reference]
- **External Services**: [Integration endpoints]
- **Port**: [port-number]
- **Base URL**: `[url]`
- **Deployment**: [How to deploy to this environment]

### [Environment 3 - e.g., Production]
- **Profile/Mode**: `[how-to-activate]`
- **Config File**: `[config-file-name]`
- **Database**: [Connection details - preferably via env vars]
- **External Services**: [Production endpoints]
- **Port**: [port-number]
- **Base URL**: `[url]`
- **Deployment**: [Production deployment process]
- **Monitoring**: [Monitoring/observability tools]

### Verified Configuration Checklist

> 📋 **TEMPLATE INSTRUCTIONS**: Document what gets initialized on startup

**On Startup, Verify:**
- ✅ [Component 1]: [Expected state]
- ✅ [Component 2]: [Expected state]
- ✅ [Component 3]: [Expected state]
- ⚠️ [Component 4]: [Expected warning/info]

**Typical Startup Time**: [duration]

**How to Verify Service is Running**:
```bash
# Check if service is responding
[command-to-check-health]

# Example: curl http://localhost:8080/health
# Example: netstat -ano | findstr :8080
```

## Important Project-Specific Overrides

> 📋 **TEMPLATE INSTRUCTIONS**: Document anything in YOUR project that differs from generic best practices or CLAUDE.md guidelines.
> This prevents AI agents from making incorrect assumptions.

1. **[Technology Choice]**: [Your choice] (not [common alternative])
   - **Reason**: [Why this technology was chosen]

2. **[Architecture Decision]**: [Your pattern] (not [common alternative])
   - **Reason**: [Rationale]

3. **[Package Structure]**: `[your.actual.package]` (not generic examples)
   - **Critical**: Always use actual package names

4. **[Build Tool/Configuration]**: [Your setup]
   - **Special Note**: [Important details]

**Examples:**
- Database: MariaDB (not PostgreSQL) - Legacy system requirement
- Logging: Log4j2 (not Logback) - Organization standard
- Package: `com.acme.projectx` (not `com.company.project`)

## Quick Reference for AI Agents

> 📋 **TEMPLATE INSTRUCTIONS**: Provide quick navigation guide for AI agents working on your codebase

### When Creating New Features

| Component | Location | Notes |
|-----------|----------|-------|
| **[Entities/Models]** | `[directory]` | [Naming convention, base classes] |
| **[DTOs]** | `[directory]` | [Validation, mapping approach] |
| **[Services]** | `[directory]` | [Transaction management, patterns] |
| **[Repositories]** | `[directory]` | [Query patterns, naming] |
| **[Controllers/Handlers]** | `[directory]` | [Response format, error handling] |
| **[Mappers]** | `[directory]` | [Mapping library, conventions] |
| **[Tests]** | `[directory]` | [Test organization] |

### When Reading Code

**Navigation Flow:**
1. Start with `[directory]` for [business logic / main logic]
2. Check `[directory]` for [interface definitions / contracts]
3. Look in `[directory]` for [implementations]
4. Refer to `[directory]` for [external integrations]

### When Writing Tests

**Test Organization:**
- **Unit tests**: [location] - Test [what to focus on]
- **Integration tests**: [location] - Test [what to focus on]
- **E2E tests**: [location] - Test [what to focus on]
- **Mock strategy**: [When to mock, what to mock]

## Known Dependencies to Watch

> 📋 **TEMPLATE INSTRUCTIONS**: Document version constraints, compatibility issues, and technical debt

### Version Constraints
- **[Technology]**: [version] - [Constraint reason]
- **[Technology]**: [version] - [Constraint reason]

### Potential Issues / Technical Debt
1. **[Issue 1]**: [Description]
   - **Impact**: [How it affects development]
   - **Workaround**: [How to work with it]

2. **[Issue 2]**: [Description]
   - **Status**: [Planned fix / known limitation]

**Examples:**
- Node.js 14 only: No modern features (top-level await, optional chaining in older syntax)
- Python 3.7 pinned: Cannot use walrus operator (:=) or positional-only parameters
- Java 8 only: No modern Java features (var, records, pattern matching)
- Legacy library X: Known CVE-2023-XXXX - upgrade planned for Q2
- Test framework Y: Version pinned due to breaking changes in newer versions

## Integration Points

> 📋 **TEMPLATE INSTRUCTIONS**: Document all external systems and services your application integrates with

### External Systems

| System | Purpose | Integration Method | Config Location | Notes |
|--------|---------|-------------------|-----------------|-------|
| **[System 1]** | [Purpose] | [REST API/SDK/Library] | `[config-location]` | [Important notes] |
| **[System 2]** | [Purpose] | [Integration method] | `[config-location]` | [Notes] |

### Internal Services

> 📋 If your application is part of a microservices architecture, document other services it depends on

| Service | Purpose | Communication | Endpoints | Circuit Breaker |
|---------|---------|---------------|-----------|-----------------|
| **[Service 1]** | [Purpose] | [REST/gRPC/messaging] | `[base-url]` | [Yes/No] |
| **[Service 2]** | [Purpose] | [Method] | `[base-url]` | [Yes/No] |

**Examples:**
- **Auth Service**: User authentication - REST API - `https://auth.internal` - Resilience4j enabled
- **Payment Gateway**: Payment processing - SOAP - `https://payments.external.com` - Manual retry

---

## Lessons Learned & Deployment Guide

> 📋 **TEMPLATE INSTRUCTIONS**: This section documents resolved issues, deployment procedures, and team knowledge.
> Use the templates below to document your own project's lessons learned.

### Issue Resolution Template

> 📋 Use this template when documenting resolved issues

**Template Structure:**

---

#### Issue Resolution: [Issue Title] ([Date])

**Problem**: [Brief description of the problem or error message]
```
[Error message or stack trace snippet]
```

**Initial Diagnosis** (if applicable):
- ❌ [What we first thought was wrong but wasn't]
- ❌ [Another incorrect hypothesis]

**Root Cause Analysis**:
1. [First root cause discovered]
2. [Second contributing factor]
3. [Third factor if applicable]
4. [Detailed explanation of why this happened]

**Solution - Step-by-Step Resolution**:

1. **[Step 1 Title]**:
   ```bash
   # Commands or code changes
   [commands-or-config]
   ```
   [Explanation of what this step does]

2. **[Step 2 Title]**:
   ```bash
   # Commands or code changes
   [commands-or-config]
   ```
   [Explanation]

3. **[Additional Steps as Needed]**:
   [Continue with numbered steps...]

**Key Takeaways for Team**:

1. **[Takeaway 1]**:
   - [Lesson learned]
   - [Action item or best practice]
   - [How to prevent this in the future]

2. **[Takeaway 2]**:
   - [Lesson learned]
   - [New practice or tool created]

3. **[Takeaway 3]**:
   - [Lesson learned]
   - [Team decision or policy change]

**Quick Fix for Future Occurrences**:
```bash
# Quick commands to resolve this issue
[fix-command-1]
[fix-command-2]
```

**Deployment/Setup Checklist** (if applicable):
- [ ] [Prerequisite 1]
- [ ] [Prerequisite 2]
- [ ] [Prerequisite 3]
- [ ] [Configuration step]
- [ ] [Verification step]

**Files Modified/Created**:
- `[file-1]`: [What changed]
- `[file-2]`: [What changed]

**Related Documentation**:
- [Link to related docs]
- [Link to protocol or guide created]

**Impact**: [Describe the positive impact of this fix]

---

### Deployment Guide Template

> 📋 Document your deployment process for each environment

#### Deploying to [Environment Name]

**Prerequisites:**
- [ ] [Access/permissions required]
- [ ] [Tools/CLI installed]
- [ ] [Configuration completed]

**Deployment Steps:**
1. [Step 1]
2. [Step 2]
3. [Step 3]
4. [Verification step]

**Rollback Procedure:**
```bash
# Commands to rollback if deployment fails
[rollback-commands]
```

**Post-Deployment Checklist:**
- [ ] [Health check 1]
- [ ] [Smoke test 1]
- [ ] [Monitor metrics]
- [ ] [Update documentation]

---

## Document Maintenance

**Last Updated**: [DATE]
**Maintained By**: [Team/Person responsible]

**Related Files:**
- Main guidelines: `CLAUDE.md`
- Multi-agent orchestration: `docs/guide/workflow/MULTI_AGENT_ORCHESTRATION.md` (if applicable)
- Workflow documentation: `docs/guide/workflow/WORKFLOW.md` (if applicable)
- [Other related documentation]

**Review Schedule**: [How often this document should be reviewed - e.g., monthly, quarterly]

**Update Instructions**:
- Update this document whenever significant project changes occur
- Add lessons learned after major issues are resolved
- Keep environment configurations up to date
- Document new patterns and conventions as they emerge
