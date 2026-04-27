# /auto-build - Build Automation

## Usage

```bash
/auto-build build          # Build the project
/auto-build test           # Run all tests
/auto-build test-unit      # Run unit tests only
/auto-build lint           # Run linter
/auto-build run            # Run the application (dev mode)
/auto-build clean          # Clean build artifacts
/auto-build install        # Install dependencies
/auto-build check          # Compile/type-check without building
```

## Purpose

Auto-detect project technology from PROJECT.md and generate a reusable build script on first use. On subsequent calls, execute the existing script.

**Key Principle**: Create once, reuse forever. No hardcoded build commands in agent files.

## How It Works

```
/auto-build <action>
    ├─ scripts/project-build.sh (.cmd) exists?
    │   ├─ YES → Execute directly (fast path)
    │   └─ NO → Auto-detect tech → Generate script → Execute
    └─ Output: Structured result with exit code
```

### Detection

1. Read PROJECT.md "Technology Stack" section
2. Verify by checking for build files in project root
3. Generate `scripts/project-build.sh` (and `.cmd` for Windows)

### Supported Technologies

| Detection Pattern | Technology |
|-------------------|-----------|
| pom.xml, Maven | Java/Maven |
| build.gradle | Java/Gradle |
| package.json, npm/yarn/pnpm | Node.js |
| requirements.txt, pip | Python/pip |
| pyproject.toml, poetry | Python/Poetry |
| Cargo.toml | Rust |
| go.mod | Go |
| *.csproj, *.sln | .NET |

### Generated Script Template (bash)

```bash
#!/bin/bash
# Project Build Script - Auto-generated from PROJECT.md
# Technology: [detected] | Generated: YYYY-MM-DD
ACTION="${1:-build}"
case "$ACTION" in
  build)      [build-cmd] ;;
  test)       [test-cmd] ;;
  test-unit)  [unit-test-cmd] ;;
  lint)       [lint-cmd] ;;
  run)        [run-cmd] ;;
  clean)      [clean-cmd] ;;
  install)    [install-cmd] ;;
  check)      [check-cmd] ;;
  *)          echo "Unknown action: $ACTION"; exit 1 ;;
esac
```

### Technology-Specific Commands

| Action | Maven | Node.js (npm) | Python | Go |
|--------|-------|---------------|--------|-----|
| build | `mvn clean package -q -DskipTests` | `npm run build --silent` | `python -m build` | `go build ./...` |
| test | `mvn clean test -q` | `npm test --silent` | `pytest -q` | `go test ./...` |
| lint | `mvn checkstyle:check -q` | `npm run lint --silent` | `ruff check .` | `golangci-lint run` |
| run | `mvn spring-boot:run -q` | `npm run dev --silent` | `uvicorn app.main:app` | `go run .` |
| clean | `mvn clean -q` | `rm -rf node_modules dist` | `rm -rf __pycache__` | `go clean` |
| install | `mvn clean install -q -DskipTests` | `npm install --silent` | `pip install -r requirements.txt -q` | `go mod download` |

### Windows .cmd Version

Also generates `scripts/project-build.cmd`:
```cmd
@echo off
set ACTION=%1
if "%ACTION%"=="" set ACTION=build
if "%ACTION%"=="build" ( [build-cmd] ) else if "%ACTION%"=="test" ( [test-cmd] ) else ( echo Unknown: %ACTION% && exit /b 1 )
```

### Make Executable (Linux/macOS)
```bash
chmod +x scripts/project-build.sh
```

## Customization

After auto-generation, edit `scripts/project-build.sh` to add:
- Custom environment setup (JAVA_HOME, MAVEN_OPTS)
- Project-specific test profiles
- Custom actions (e.g., `deploy`)

To regenerate: delete scripts and re-run `/auto-build`.

## Error Handling

| Error | Solution |
|-------|----------|
| Cannot detect technology | Configure PROJECT.md "Technology Stack" section |
| No build files found | Verify project source code location |
| Build script fails | Edit `scripts/project-build.sh` or delete and regenerate |

## Related Skills

- `/project-setup` - Configure PROJECT.md first
- `/commit-push-pr` - Commit, push, and create PR after build

---

**Skill Type**: Build Automation
**Supported**: Maven, Gradle, npm/yarn/pnpm, Python, Go, Rust, .NET
