#!/bin/bash
#
# Claude Memory Worker - Backup Script
#
# This script creates a backup of the database and configuration.
# Can be run manually or via cron for automated backups.
#
# Usage: bash backup.sh [--retention-days 30]
#

set -e

# Configuration
APP_DIR="/opt/claude-memory"
DATA_DIR="${APP_DIR}/data"
BACKUP_DIR="${APP_DIR}/backups"
DB_FILE="${DATA_DIR}/memory.db"
RETENTION_DAYS=30

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --retention-days)
            RETENTION_DAYS="$2"
            shift 2
            ;;
        *)
            print_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

print_info "Starting backup process..."

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Generate backup filename
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BACKUP_NAME="memory-backup-${TIMESTAMP}"
BACKUP_PATH="${BACKUP_DIR}/${BACKUP_NAME}"

# Check if database exists
if [ ! -f "$DB_FILE" ]; then
    print_error "Database file not found: $DB_FILE"
    exit 1
fi

# Get database size
DB_SIZE=$(du -h "$DB_FILE" | cut -f1)
print_info "Database size: $DB_SIZE"

# Create temporary directory for backup
TMP_DIR=$(mktemp -d)
trap "rm -rf $TMP_DIR" EXIT

# Copy database
print_info "Copying database..."
cp "$DB_FILE" "${TMP_DIR}/memory.db"

# Copy configuration
if [ -f "${APP_DIR}/server/.env" ]; then
    cp "${APP_DIR}/server/.env" "${TMP_DIR}/config.env"
fi

# Create metadata file
cat > "${TMP_DIR}/backup-info.txt" <<EOF
Backup Information
==================
Timestamp: $(date)
Hostname: $(hostname)
Database Size: $DB_SIZE
Database Path: $DB_FILE
EOF

# Create compressed archive
print_info "Creating compressed archive..."
tar -czf "${BACKUP_PATH}.tar.gz" -C "$TMP_DIR" .

# Calculate backup size
BACKUP_SIZE=$(du -h "${BACKUP_PATH}.tar.gz" | cut -f1)
print_info "Backup created: ${BACKUP_PATH}.tar.gz ($BACKUP_SIZE)"

# Clean up old backups
print_info "Cleaning up old backups (retention: $RETENTION_DAYS days)..."
find "$BACKUP_DIR" -name "memory-backup-*.tar.gz" -type f -mtime +$RETENTION_DAYS -delete
REMAINING=$(find "$BACKUP_DIR" -name "memory-backup-*.tar.gz" | wc -l)
print_info "Retained backups: $REMAINING"

# Calculate total backup size
TOTAL_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)
print_info "Total backup directory size: $TOTAL_SIZE"

print_info "Backup completed successfully!"
echo ""
print_info "Backup file: ${BACKUP_PATH}.tar.gz"
print_info "To restore: bash deployment/server/restore.sh ${BACKUP_PATH}.tar.gz"
