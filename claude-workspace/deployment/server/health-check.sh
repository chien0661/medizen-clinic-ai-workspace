#!/bin/bash
#
# Claude Memory Worker - Health Check Script
#
# This script checks the health of the worker service and sends alerts if needed.
# Can be run manually or via cron for monitoring.
#
# Usage: bash health-check.sh [--alert-email email@company.com]
#

WORKER_PORT=37777
WORKER_URL="http://localhost:${WORKER_PORT}"
SERVICE_NAME="claude-memory-worker"
ALERT_EMAIL="${1}"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_ok() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

send_alert() {
    if [ -n "$ALERT_EMAIL" ]; then
        echo "$1" | mail -s "Claude Memory Worker Alert" "$ALERT_EMAIL"
    fi
}

# Check systemd service
check_service() {
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        print_ok "Service is running"
        return 0
    else
        print_error "Service is not running"
        send_alert "Claude Memory Worker service is not running on $(hostname)"
        return 1
    fi
}

# Check health endpoint
check_health() {
    if command -v curl &> /dev/null; then
        RESPONSE=$(curl -s -f "${WORKER_URL}/api/health" 2>&1)
        if [ $? -eq 0 ]; then
            STATUS=$(echo "$RESPONSE" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
            UPTIME=$(echo "$RESPONSE" | grep -o '"uptime":[0-9.]*' | cut -d':' -f2)

            if [ "$STATUS" = "ok" ]; then
                print_ok "Health endpoint responding (uptime: ${UPTIME}s)"
                return 0
            else
                print_error "Health endpoint returned status: $STATUS"
                send_alert "Claude Memory Worker health check failed: status=$STATUS"
                return 1
            fi
        else
            print_error "Health endpoint not responding"
            send_alert "Claude Memory Worker health endpoint not responding on $(hostname)"
            return 1
        fi
    else
        print_warn "curl not found, skipping health check"
        return 0
    fi
}

# Check database
check_database() {
    DB_PATH="/opt/claude-memory/data/memory.db"

    if [ -f "$DB_PATH" ]; then
        DB_SIZE=$(du -h "$DB_PATH" | cut -f1)
        print_ok "Database exists (size: $DB_SIZE)"

        # Check if database is writable
        if [ -w "$DB_PATH" ]; then
            print_ok "Database is writable"
        else
            print_error "Database is not writable"
            send_alert "Claude Memory Worker database not writable on $(hostname)"
            return 1
        fi

        # Check database size (warn if > 1GB)
        DB_SIZE_BYTES=$(stat -c%s "$DB_PATH" 2>/dev/null || stat -f%z "$DB_PATH")
        if [ "$DB_SIZE_BYTES" -gt 1073741824 ]; then
            print_warn "Database is large ($(numfmt --to=iec-i --suffix=B $DB_SIZE_BYTES))"
            print_warn "Consider archiving old data"
        fi

        return 0
    else
        print_error "Database file not found: $DB_PATH"
        return 1
    fi
}

# Check disk space
check_disk() {
    DISK_USAGE=$(df -h /opt/claude-memory | awk 'NR==2 {print $5}' | sed 's/%//')

    if [ "$DISK_USAGE" -lt 80 ]; then
        print_ok "Disk space: ${DISK_USAGE}% used"
    elif [ "$DISK_USAGE" -lt 90 ]; then
        print_warn "Disk space: ${DISK_USAGE}% used (approaching limit)"
    else
        print_error "Disk space: ${DISK_USAGE}% used (critically low)"
        send_alert "Claude Memory Worker disk space critical: ${DISK_USAGE}% on $(hostname)"
        return 1
    fi
    return 0
}

# Check memory usage
check_memory() {
    if command -v ps &> /dev/null; then
        MEMORY_MB=$(ps aux | grep "node dist/services/worker.js" | grep -v grep | awk '{print $6}' | head -1)
        if [ -n "$MEMORY_MB" ]; then
            MEMORY_MB=$((MEMORY_MB / 1024))
            print_ok "Memory usage: ${MEMORY_MB}MB"

            if [ "$MEMORY_MB" -gt 1024 ]; then
                print_warn "Memory usage is high (${MEMORY_MB}MB)"
            fi
        fi
    fi
    return 0
}

# Check logs for errors
check_logs() {
    if command -v journalctl &> /dev/null; then
        ERROR_COUNT=$(journalctl -u "$SERVICE_NAME" --since "1 hour ago" | grep -c "ERROR" || true)

        if [ "$ERROR_COUNT" -eq 0 ]; then
            print_ok "No errors in last hour"
        elif [ "$ERROR_COUNT" -lt 5 ]; then
            print_warn "$ERROR_COUNT errors in last hour"
        else
            print_error "$ERROR_COUNT errors in last hour"
            send_alert "Claude Memory Worker has $ERROR_COUNT errors in the last hour on $(hostname)"
            return 1
        fi
    fi
    return 0
}

# Main health check
main() {
    echo "Claude Memory Worker - Health Check"
    echo "===================================="
    echo "Time: $(date)"
    echo ""

    FAILED=0

    check_service || FAILED=$((FAILED + 1))
    check_health || FAILED=$((FAILED + 1))
    check_database || FAILED=$((FAILED + 1))
    check_disk || FAILED=$((FAILED + 1))
    check_memory
    check_logs || FAILED=$((FAILED + 1))

    echo ""
    if [ $FAILED -eq 0 ]; then
        echo -e "${GREEN}All checks passed!${NC}"
        exit 0
    else
        echo -e "${RED}$FAILED check(s) failed${NC}"
        exit 1
    fi
}

main
