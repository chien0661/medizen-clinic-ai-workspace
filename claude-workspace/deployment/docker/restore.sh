#!/bin/bash
#
# Restore Script for Claude Memory Worker (Docker)
#
# This script restores a SQLite database backup to the Docker container
# Usage: bash restore.sh <backup-file>
# Example: bash restore.sh backups/memory-20260204-100000.db
#

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONTAINER_NAME="claude-memory-worker"

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

# Check arguments
if [ $# -lt 1 ]; then
    print_error "Usage: $0 <backup-file>"
    echo "Example: $0 backups/memory-20260204-100000.db"
    echo ""
    echo "Available backups:"
    ls -lht "${SCRIPT_DIR}/backups"/memory-*.db 2>/dev/null | head -10 || echo "No backups found"
    exit 1
fi

BACKUP_FILE="$1"

# Check if backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    print_error "Backup file not found: $BACKUP_FILE"
    exit 1
fi

# Check if container is running
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    print_error "Container ${CONTAINER_NAME} is not running"
    print_info "Start the container first: cd deployment/docker && docker compose up -d"
    exit 1
fi

# Confirm restore
BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
print_warn "⚠️  This will replace the current database!"
print_info "Backup file: $BACKUP_FILE ($BACKUP_SIZE)"
read -p "Are you sure you want to restore? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    print_info "Restore cancelled"
    exit 0
fi

# Create backup of current database first
print_info "Creating backup of current database before restore..."
CURRENT_BACKUP="backups/memory-before-restore-$(date +%Y%m%d-%H%M%S).db"
mkdir -p "$(dirname "$CURRENT_BACKUP")"
docker cp ${CONTAINER_NAME}:/opt/claude-memory/data/memory.db "$CURRENT_BACKUP" 2>/dev/null || print_warn "No current database to backup"

# Stop the worker service to prevent database locks
print_info "Stopping container..."
docker compose -f "${SCRIPT_DIR}/docker-compose.yml" stop

# Copy backup file to container
print_info "Restoring database from backup..."
docker cp "$BACKUP_FILE" ${CONTAINER_NAME}:/opt/claude-memory/data/memory.db

# Fix permissions
docker compose -f "${SCRIPT_DIR}/docker-compose.yml" run --rm --entrypoint sh claude-memory-worker -c "chown claudemem:claudemem /opt/claude-memory/data/memory.db"

# Start the container
print_info "Starting container..."
docker compose -f "${SCRIPT_DIR}/docker-compose.yml" start

# Wait for container to be ready
print_info "Waiting for container to be ready..."
sleep 3

# Verify restore
print_info "Verifying database..."
if docker exec $CONTAINER_NAME sh -c "test -f /opt/claude-memory/data/memory.db"; then
    print_info "✅ Database restored successfully!"

    # Test health endpoint
    if curl -s -f http://localhost:37777/api/health > /dev/null 2>&1; then
        print_info "✅ Worker service is healthy"
    else
        print_warn "Worker service may not be responding yet, check logs:"
        echo "  docker compose -f ${SCRIPT_DIR}/docker-compose.yml logs -f"
    fi
else
    print_error "❌ Database restore failed"
    print_info "Restoring previous database..."
    docker cp "$CURRENT_BACKUP" ${CONTAINER_NAME}:/opt/claude-memory/data/memory.db
    exit 1
fi

print_info "Current database backup saved to: $CURRENT_BACKUP"
