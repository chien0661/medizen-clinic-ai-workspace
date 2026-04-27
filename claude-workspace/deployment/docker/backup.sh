#!/bin/bash
#
# Automated Backup Script for Claude Memory Worker (Docker)
#
# This script backs up the SQLite database from the Docker container
# Usage: bash backup.sh
#

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="${SCRIPT_DIR}/backups"
CONTAINER_NAME="claude-memory-worker"
DATE=$(date +%Y%m%d-%H%M%S)
BACKUP_FILE="memory-${DATE}.db"
KEEP_DAYS=30

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

# Create backup directory
mkdir -p "$BACKUP_DIR"

print_info "Starting backup of Claude Memory database..."

# Check if container is running
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    print_error "Container ${CONTAINER_NAME} is not running"
    exit 1
fi

# Create backup inside container first
print_info "Creating backup inside container..."
docker exec $CONTAINER_NAME sh -c "cp /opt/claude-memory/data/memory.db /opt/claude-memory/backups/memory-temp.db 2>/dev/null || echo 'Database may not exist yet'"

# Copy backup from container to host
print_info "Copying backup to host: ${BACKUP_DIR}/${BACKUP_FILE}"
docker cp ${CONTAINER_NAME}:/opt/claude-memory/backups/memory-temp.db "${BACKUP_DIR}/${BACKUP_FILE}" 2>/dev/null || {
    print_warn "No database to backup yet (this is normal for new installations)"
    exit 0
}

# Clean up temp file in container
docker exec $CONTAINER_NAME sh -c "rm -f /opt/claude-memory/backups/memory-temp.db"

# Get backup size
BACKUP_SIZE=$(du -h "${BACKUP_DIR}/${BACKUP_FILE}" | cut -f1)
print_info "Backup created: ${BACKUP_FILE} (${BACKUP_SIZE})"

# Clean up old backups
print_info "Cleaning up backups older than ${KEEP_DAYS} days..."
find "$BACKUP_DIR" -name "memory-*.db" -mtime +${KEEP_DAYS} -delete
REMAINING=$(ls -1 "${BACKUP_DIR}"/memory-*.db 2>/dev/null | wc -l)
print_info "Backups remaining: ${REMAINING}"

# List recent backups
print_info "Recent backups:"
ls -lht "${BACKUP_DIR}"/memory-*.db 2>/dev/null | head -5 || print_warn "No backups found"

print_info "✅ Backup complete!"
