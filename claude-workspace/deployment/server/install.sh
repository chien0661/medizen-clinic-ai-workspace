#!/bin/bash
#
# Claude Memory Worker - Server Installation Script
#
# This script installs and configures the Claude Memory worker service
# on an on-premise server.
#
# Usage: sudo bash install.sh
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
APP_USER="claudemem"
APP_DIR="/opt/claude-memory"
SERVER_DIR="${APP_DIR}/server"
DATA_DIR="${APP_DIR}/data"
LOG_DIR="${APP_DIR}/logs"
BACKUP_DIR="${APP_DIR}/backups"
REPO_URL="https://bitbucket.vissoft.vn/scm/ct/template-ai-team.git"
WORKER_PORT=37777

# Functions
print_header() {
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}$1${NC}"
    echo -e "${GREEN}========================================${NC}"
}

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_root() {
    if [ "$EUID" -ne 0 ]; then
        print_error "This script must be run as root (use sudo)"
        exit 1
    fi
}

check_prerequisites() {
    print_header "Checking Prerequisites"

    # Check Node.js
    if ! command -v node &> /dev/null; then
        print_error "Node.js is not installed"
        print_info "Install Node.js 20 LTS:"
        echo "  curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -"
        echo "  sudo apt install -y nodejs"
        exit 1
    fi

    NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
    if [ "$NODE_VERSION" -lt 18 ]; then
        print_error "Node.js version must be 18 or higher (current: $(node -v))"
        exit 1
    fi
    print_info "Node.js version: $(node -v) ✓"

    # Check npm
    if ! command -v npm &> /dev/null; then
        print_error "npm is not installed"
        exit 1
    fi
    print_info "npm version: $(npm -v) ✓"

    # Check git
    if ! command -v git &> /dev/null; then
        print_error "git is not installed"
        print_info "Install git: sudo apt install -y git"
        exit 1
    fi
    print_info "git version: $(git --version | cut -d' ' -f3) ✓"

    print_info "All prerequisites satisfied"
}

create_user() {
    print_header "Creating Application User"

    if id "$APP_USER" &>/dev/null; then
        print_info "User $APP_USER already exists"
    else
        useradd -r -s /bin/bash -d "$APP_DIR" -m "$APP_USER"
        print_info "Created user: $APP_USER"
    fi
}

create_directories() {
    print_header "Creating Directory Structure"

    mkdir -p "$SERVER_DIR"
    mkdir -p "$DATA_DIR"
    mkdir -p "$LOG_DIR"
    mkdir -p "$BACKUP_DIR"
    mkdir -p "${APP_DIR}/scripts"

    print_info "Created directories:"
    print_info "  - $SERVER_DIR (application)"
    print_info "  - $DATA_DIR (database)"
    print_info "  - $LOG_DIR (logs)"
    print_info "  - $BACKUP_DIR (backups)"
}

install_application() {
    print_header "Installing Application"

    # Clone repository
    if [ -d "${SERVER_DIR}/.git" ]; then
        print_info "Repository already exists, pulling latest changes..."
        cd "$SERVER_DIR"
        sudo -u "$APP_USER" git pull
    else
        print_info "Cloning repository..."
        sudo -u "$APP_USER" git clone "$REPO_URL" "$SERVER_DIR"
    fi

    # Navigate to MCP server directory
    cd "${SERVER_DIR}/mcp-servers/claude-mem-server"

    # Install dependencies
    print_info "Installing dependencies..."
    sudo -u "$APP_USER" npm ci --only=production

    # Build application
    print_info "Building application..."
    sudo -u "$APP_USER" npm run build

    print_info "Application installed successfully"
}

create_env_file() {
    print_header "Creating Environment Configuration"

    ENV_FILE="${SERVER_DIR}/.env"

    if [ -f "$ENV_FILE" ]; then
        print_warn "Environment file already exists: $ENV_FILE"
        print_warn "Please update it manually with your settings"
        return
    fi

    cat > "$ENV_FILE" <<EOF
# Claude Memory Worker - Production Configuration
# Created: $(date)

# ========================================
# REQUIRED SETTINGS
# ========================================

# Anthropic API Key (REQUIRED for observation compression)
# Get your API key from: https://console.anthropic.com/settings/keys
ANTHROPIC_API_KEY=your_api_key_here

# ========================================
# Worker Configuration
# ========================================

# Worker service port
WORKER_PORT=37777

# Environment mode
NODE_ENV=production

# ========================================
# Database Configuration
# ========================================

# Database path (SQLite)
MEMORY_DB_PATH=${DATA_DIR}/memory.db

# ========================================
# Security Settings (IMPORTANT!)
# ========================================

# API Key for authentication (generate with: openssl rand -hex 32)
API_KEY=your-secure-random-key-here

# Allowed origins for CORS (comma-separated)
ALLOWED_ORIGINS=http://localhost,http://10.0.0.0/8,http://192.168.0.0/16

# ========================================
# Logging Configuration
# ========================================

# Log level (error, warn, info, debug)
LOG_LEVEL=info

# Log directory
LOG_PATH=${LOG_DIR}

# ========================================
# Performance Settings
# ========================================

# Maximum observations to process in queue
QUEUE_MAX_SIZE=1000

# Queue processing interval (ms)
QUEUE_INTERVAL=5000

# ========================================
# Optional: PostgreSQL (for high-scale)
# ========================================

# Uncomment to use PostgreSQL instead of SQLite
# DB_TYPE=postgres
# DB_HOST=localhost
# DB_PORT=5432
# DB_NAME=claude_memory
# DB_USER=claudemem
# DB_PASSWORD=your_db_password

EOF

    chown "$APP_USER:$APP_USER" "$ENV_FILE"
    chmod 600 "$ENV_FILE"

    print_info "Created environment file: $ENV_FILE"
    print_warn "⚠️  IMPORTANT: Edit $ENV_FILE and set your ANTHROPIC_API_KEY!"
    print_warn "⚠️  IMPORTANT: Generate and set a secure API_KEY!"
}

install_systemd_service() {
    print_header "Installing Systemd Service"

    SERVICE_FILE="/etc/systemd/system/claude-memory-worker.service"

    cat > "$SERVICE_FILE" <<EOF
[Unit]
Description=Claude Memory Worker Service
Documentation=https://bitbucket.vissoft.vn/scm/ct/template-ai-team
After=network.target

[Service]
Type=simple
User=$APP_USER
Group=$APP_USER
WorkingDirectory=${SERVER_DIR}/mcp-servers/claude-mem-server
EnvironmentFile=${SERVER_DIR}/.env
ExecStart=/usr/bin/node dist/services/worker.js
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=claude-memory

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=${DATA_DIR} ${LOG_DIR} ${BACKUP_DIR}

# Resource limits
LimitNOFILE=65536
TasksMax=4096

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    print_info "Systemd service installed: $SERVICE_FILE"
}

setup_logrotate() {
    print_header "Setting Up Log Rotation"

    LOGROTATE_FILE="/etc/logrotate.d/claude-memory"

    cat > "$LOGROTATE_FILE" <<EOF
${LOG_DIR}/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 $APP_USER $APP_USER
    sharedscripts
    postrotate
        systemctl reload claude-memory-worker > /dev/null 2>&1 || true
    endscript
}
EOF

    print_info "Log rotation configured: $LOGROTATE_FILE"
}

install_scripts() {
    print_header "Installing Utility Scripts"

    SCRIPTS_SRC="$(dirname "$(dirname "$(readlink -f "$0")")")/scripts"

    if [ -d "$SCRIPTS_SRC" ]; then
        cp -r "$SCRIPTS_SRC"/* "${APP_DIR}/scripts/"
        chmod +x "${APP_DIR}/scripts"/*.sh
        print_info "Utility scripts installed to ${APP_DIR}/scripts/"
    else
        print_warn "Scripts directory not found, skipping"
    fi
}

set_permissions() {
    print_header "Setting Permissions"

    chown -R "$APP_USER:$APP_USER" "$APP_DIR"
    chmod 750 "$APP_DIR"
    chmod 750 "$SERVER_DIR"
    chmod 770 "$DATA_DIR"
    chmod 770 "$LOG_DIR"
    chmod 770 "$BACKUP_DIR"

    print_info "Permissions set correctly"
}

create_initial_backup() {
    print_header "Creating Initial Configuration Backup"

    BACKUP_FILE="${BACKUP_DIR}/install-backup-$(date +%Y%m%d-%H%M%S).tar.gz"
    tar -czf "$BACKUP_FILE" -C "$SERVER_DIR" .env mcp-servers/claude-mem-server/package.json
    chown "$APP_USER:$APP_USER" "$BACKUP_FILE"

    print_info "Configuration backed up to: $BACKUP_FILE"
}

print_next_steps() {
    print_header "Installation Complete!"

    echo ""
    print_info "✅ Application installed to: $SERVER_DIR"
    print_info "✅ Database will be created at: ${DATA_DIR}/memory.db"
    print_info "✅ Logs directory: $LOG_DIR"
    print_info "✅ Systemd service installed: claude-memory-worker"
    echo ""

    print_warn "⚠️  NEXT STEPS:"
    echo ""
    echo "1. Edit configuration file:"
    echo "   sudo nano ${SERVER_DIR}/.env"
    echo ""
    echo "2. Set required values:"
    echo "   - ANTHROPIC_API_KEY=your_api_key"
    echo "   - API_KEY=\$(openssl rand -hex 32)"
    echo ""
    echo "3. Start the service:"
    echo "   sudo systemctl start claude-memory-worker"
    echo "   sudo systemctl enable claude-memory-worker"
    echo ""
    echo "4. Check status:"
    echo "   sudo systemctl status claude-memory-worker"
    echo "   sudo journalctl -u claude-memory-worker -f"
    echo ""
    echo "5. Test health endpoint:"
    echo "   curl http://localhost:${WORKER_PORT}/api/health"
    echo ""
    echo "6. Configure firewall (if needed):"
    echo "   sudo ufw allow from <your-network>/24 to any port ${WORKER_PORT}"
    echo ""

    print_info "📚 See ${APP_DIR}/server/README.md for full documentation"
}

# Main installation flow
main() {
    print_header "Claude Memory Worker - Installation"
    echo ""

    check_root
    check_prerequisites
    create_user
    create_directories
    install_application
    create_env_file
    install_systemd_service
    setup_logrotate
    install_scripts
    set_permissions
    create_initial_backup
    print_next_steps
}

# Run installation
main
