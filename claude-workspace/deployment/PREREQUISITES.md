# Prerequisites and Version Requirements

Complete system requirements for deploying and using the Claude Persistent Memory system.

## System Requirements

### Minimum Hardware

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **CPU** | 2 cores | 4+ cores |
| **RAM** | 4 GB | 8+ GB |
| **Disk Space** | 10 GB free | 20+ GB free |
| **Network** | Internet connection for API calls | Stable broadband |

### Storage Breakdown

```
Required Disk Space:
├── Docker images: ~500 MB
├── Node modules: ~200 MB
├── MCP servers: ~100 MB
├── Database storage: Grows with usage (~10-100 MB typical)
└── Logs and backups: ~100 MB
─────────────────────
Total: ~1 GB + database growth
```

## Software Requirements

### Required Software

#### 1. Docker & Docker Compose

**Docker Engine:**
- **Minimum**: 20.10.0
- **Recommended**: 24.0.0+
- **Platform**: Linux, macOS, Windows (with WSL2)

**Docker Compose:**
- **Minimum**: 2.0.0
- **Recommended**: 2.20.0+
- **Note**: Compose V2 is integrated into Docker Desktop

**Verify Installation:**
```bash
docker --version          # Should show 20.10+
docker compose version    # Should show 2.0+
```

**Installation Guides:**
- **Linux**: https://docs.docker.com/engine/install/
- **macOS**: https://docs.docker.com/desktop/install/mac-install/
- **Windows**: https://docs.docker.com/desktop/install/windows-install/

#### 2. Node.js & npm

**Node.js:**
- **Minimum**: 18.0.0
- **Recommended**: 20.0.0+ (LTS)
- **Not supported**: Node.js 16 and below

**npm:**
- **Minimum**: 8.0.0
- **Recommended**: 10.0.0+

**Verify Installation:**
```bash
node --version    # Should show v18.0.0+
npm --version     # Should show 8.0.0+
```

**Installation:**
- Download from: https://nodejs.org/
- Use nvm (recommended): https://github.com/nvm-sh/nvm

```bash
# Using nvm (recommended)
nvm install 20
nvm use 20
```

#### 3. Git

**Version:**
- **Minimum**: 2.25.0
- **Recommended**: 2.40.0+

**Verify Installation:**
```bash
git --version    # Should show 2.25.0+
```

**Installation:**
- **Linux**: `sudo apt install git` or `sudo yum install git`
- **macOS**: Included with Xcode Command Line Tools
- **Windows**: https://git-scm.com/download/win

#### 4. Claude Code CLI

**Version:**
- **Minimum**: Latest stable version
- **Update regularly** for best compatibility

**Installation:**
```bash
# Check if installed
claude --version

# Install/update
npm install -g @anthropic-ai/claude-code
```

### Optional Software

#### 1. curl (for API testing)

**Verify:**
```bash
curl --version
```

**Installation:**
- **Linux**: Usually pre-installed
- **macOS**: Pre-installed
- **Windows**: Available in PowerShell or install via Git Bash

#### 2. jq (for JSON parsing)

**Verify:**
```bash
jq --version
```

**Installation:**
```bash
# Linux
sudo apt install jq

# macOS
brew install jq

# Windows
choco install jq
```

#### 3. openssl (for key generation)

**Verify:**
```bash
openssl version
```

**Note**: Usually pre-installed on Linux/macOS. On Windows, included with Git Bash.

## API Keys and Credentials

### Required

#### 1. Anthropic API Key

**Where to get:**
- Visit: https://console.anthropic.com/
- Navigate to: Settings → API Keys
- Create new key or copy existing

**Format:**
```
sk-ant-api03-...
```

**Cost:**
- Claude Haiku: $0.25 / 1M input tokens, $1.25 / 1M output tokens
- Claude Sonnet: $3 / 1M input tokens, $15 / 1M output tokens
- Typical usage: ~100-500 tokens per observation compression

**Estimated costs:**
- Light usage (50 observations/day): ~$0.10-0.50/day
- Medium usage (200 observations/day): ~$0.50-2.00/day
- Heavy usage (1000 observations/day): ~$2.00-10.00/day

#### 2. Client API Key (Auto-Generated)

**Generation:**
- Automatically generated during `setup.sh`
- Or manually: `openssl rand -hex 32`

**Purpose:**
- Authenticates Claude Code client to memory worker
- Must match between Docker `.env` and `.mcp.json`

### Optional

- **Jira Token**: For Jira MCP integration
- **Confluence Token**: For Confluence MCP integration
- **Figma Token**: For Figma MCP integration
- **SonarQube Token**: For SonarQube MCP integration

## Operating System Support

### Officially Supported

| OS | Version | Status | Notes |
|----|---------|--------|-------|
| **Ubuntu** | 20.04+ | ✅ Fully tested | Recommended for production |
| **Debian** | 11+ | ✅ Fully tested | Production ready |
| **macOS** | 12+ (Monterey) | ✅ Tested | Development and production |
| **Windows 11** | 22H2+ | ✅ Tested | Requires WSL2 for Docker |
| **Windows 10** | 21H2+ | ⚠️ Limited | Requires WSL2 |

### Other Linux Distributions

| OS | Status | Notes |
|----|--------|-------|
| **CentOS/RHEL** 8+ | ✅ Should work | Docker and Node.js required |
| **Fedora** 36+ | ✅ Should work | Docker and Node.js required |
| **Arch Linux** | ✅ Should work | Use AUR for packages |
| **Alpine Linux** | ⚠️ Untested | May have compatibility issues |

### Docker Support

- **Linux**: Native Docker Engine
- **macOS**: Docker Desktop
- **Windows**: Docker Desktop with WSL2 backend

## Network Requirements

### Ports

| Port | Service | Direction | Required | Notes |
|------|---------|-----------|----------|-------|
| **37777** | Memory Worker | Inbound | Yes | Default worker port |
| **443** | Anthropic API | Outbound | Yes | HTTPS for API calls |
| **80/443** | Package registries | Outbound | Yes | npm, Docker Hub |

### Firewall Rules

**If deploying to remote server:**
```bash
# Allow worker port (if needed for remote access)
sudo ufw allow 37777/tcp

# Allow Docker
sudo ufw allow 2375/tcp  # Docker daemon (if remote)
```

**For local development:**
- No firewall changes needed
- Worker binds to localhost by default

### Internet Connectivity

**Required for:**
- Anthropic API calls (compression)
- npm package installation
- Docker image pulls
- MCP server dependencies

**Bandwidth estimates:**
- Initial setup: ~500 MB download
- Runtime: ~10-50 KB per observation (API calls)

## Permissions and Access

### Docker Permissions

**Linux:**
```bash
# Add user to docker group (recommended)
sudo usermod -aG docker $USER

# Or run with sudo (not recommended)
sudo docker compose up
```

**macOS/Windows:**
- Docker Desktop handles permissions automatically

### File System Permissions

**Required write access to:**
```
./deployment/docker/data/      # Database storage
./deployment/docker/logs/      # Worker logs
./deployment/docker/backups/   # Database backups
~/.claude-mem/                 # Local database (if not using Docker)
```

**Set permissions (Linux):**
```bash
# Ensure user can write to Docker volumes
sudo chown -R $USER:$USER deployment/docker/
chmod -R 755 deployment/docker/
```

## Version Compatibility Matrix

### Template Versions

| Template Version | Claude Code | Docker | Node.js | Status |
|-----------------|-------------|---------|---------|--------|
| **1.6.0+** | Latest | 20.10+ | 18+ | ✅ Current |
| **1.5.x** | Latest | 20.10+ | 18+ | ⚠️ No persistent memory |
| **1.4.x** | Latest | - | 16+ | ❌ Upgrade required |

### Component Compatibility

| Component | Minimum | Tested | Latest | Notes |
|-----------|---------|--------|--------|-------|
| **Docker** | 20.10 | 24.0 | 25.0+ | Use stable releases |
| **Compose** | 2.0 | 2.20 | 2.24+ | V2 syntax required |
| **Node.js** | 18.0 | 20.11 | 21.x | LTS recommended |
| **npm** | 8.0 | 10.2 | 10.5+ | Bundled with Node |
| **Claude Code** | Latest | Latest | Latest | Auto-updates |

### MCP Protocol Version

- **Required**: MCP Protocol 1.0+
- **Claude Code support**: Built-in
- **Server compatibility**: All MCP 1.0 compliant servers

## Verification Script

Use this script to check all prerequisites:

```bash
#!/bin/bash
# Save as: check-prerequisites.sh

echo "Checking prerequisites for Claude Persistent Memory..."
echo ""

# Docker
if command -v docker &> /dev/null; then
    DOCKER_VER=$(docker --version | grep -oE '[0-9]+\.[0-9]+' | head -1)
    echo "✅ Docker: $DOCKER_VER"
else
    echo "❌ Docker: Not found"
fi

# Docker Compose
if command -v docker compose &> /dev/null; then
    COMPOSE_VER=$(docker compose version | grep -oE '[0-9]+\.[0-9]+' | head -1)
    echo "✅ Docker Compose: $COMPOSE_VER"
else
    echo "❌ Docker Compose: Not found"
fi

# Node.js
if command -v node &> /dev/null; then
    NODE_VER=$(node --version)
    echo "✅ Node.js: $NODE_VER"
else
    echo "❌ Node.js: Not found"
fi

# npm
if command -v npm &> /dev/null; then
    NPM_VER=$(npm --version)
    echo "✅ npm: $NPM_VER"
else
    echo "❌ npm: Not found"
fi

# Git
if command -v git &> /dev/null; then
    GIT_VER=$(git --version | grep -oE '[0-9]+\.[0-9]+' | head -1)
    echo "✅ Git: $GIT_VER"
else
    echo "❌ Git: Not found"
fi

# Claude Code
if command -v claude &> /dev/null; then
    echo "✅ Claude Code: Installed"
else
    echo "⚠️  Claude Code: Not found (install with: npm install -g @anthropic-ai/claude-code)"
fi

# curl
if command -v curl &> /dev/null; then
    echo "✅ curl: Installed"
else
    echo "⚠️  curl: Not found (optional, for testing)"
fi

# openssl
if command -v openssl &> /dev/null; then
    echo "✅ openssl: Installed"
else
    echo "⚠️  openssl: Not found (needed for key generation)"
fi

echo ""
echo "Checking ports..."
if lsof -i:37777 &> /dev/null || netstat -an | grep -q 37777 &> /dev/null; then
    echo "⚠️  Port 37777: In use"
else
    echo "✅ Port 37777: Available"
fi

echo ""
echo "Checking disk space..."
AVAILABLE=$(df -h . | awk 'NR==2 {print $4}')
echo "Available disk space: $AVAILABLE"

echo ""
echo "Prerequisites check complete!"
```

Usage:
```bash
chmod +x check-prerequisites.sh
./check-prerequisites.sh
```

## Troubleshooting Prerequisites

### Docker Issues

**Error: "docker: command not found"**
```bash
# Install Docker (Ubuntu/Debian)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

**Error: "permission denied while trying to connect to Docker daemon"**
```bash
sudo usermod -aG docker $USER
# Logout and login again
```

### Node.js Issues

**Error: "node: command not found"**
```bash
# Install using nvm (recommended)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
nvm install 20
nvm use 20
```

**Error: "unsupported Node.js version"**
```bash
# Upgrade to Node.js 18+
nvm install 20
nvm alias default 20
```

### Port Conflicts

**Error: "port 37777 already in use"**
```bash
# Find process using port
lsof -i:37777    # Linux/macOS
netstat -ano | findstr :37777    # Windows

# Change port in docker-compose.yml
ports:
  - "37778:37777"  # Use different external port
```

## Getting Help

If you encounter issues with prerequisites:

1. **Check versions**: Run verification script above
2. **Review logs**: Check Docker logs for specific errors
3. **Search issues**: Look for similar problems in template repository
4. **Platform-specific**: Check Docker/Node.js documentation for your OS
5. **Contact support**: Reach out to AI Team with system details

## Summary Checklist

Before deploying persistent memory, verify:

- [ ] Docker 20.10+ installed and running
- [ ] Docker Compose 2.0+ available
- [ ] Node.js 18+ installed
- [ ] npm 8+ installed
- [ ] Git 2.25+ installed
- [ ] Anthropic API key obtained
- [ ] Port 37777 available
- [ ] 10+ GB disk space free
- [ ] Internet connectivity working
- [ ] File permissions configured (Linux)

**All requirements met?** Proceed to [deployment guide](docker/README.md).

**Missing requirements?** Follow installation links above.

---

**Document Version**: 1.0
**Template Version**: 1.6.0+
**Last Updated**: 2026-02-04
**Maintained by**: VISSoft AI Team
