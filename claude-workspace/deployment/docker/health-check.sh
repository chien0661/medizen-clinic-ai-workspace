#!/bin/bash
#
# Health Check and Monitoring Script for Claude Memory Worker (Docker)
#
# This script checks the health of the Docker container and worker service
# Usage: bash health-check.sh
#
# Can be run via cron for automated monitoring:
# */5 * * * * /path/to/health-check.sh >> /var/log/claude-memory-health.log 2>&1
#

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONTAINER_NAME="claude-memory-worker"
WORKER_URL="http://localhost:37777"
ALERT_EMAIL=""  # Set email for alerts (optional)

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

send_alert() {
    local message="$1"
    echo "[$(date)] ALERT: $message"

    # Send email if configured
    if [ -n "$ALERT_EMAIL" ]; then
        echo "$message" | mail -s "Claude Memory Worker Alert" "$ALERT_EMAIL" 2>/dev/null || true
    fi
}

# Print header
echo "========================================"
echo "Claude Memory Worker - Health Check"
echo "Time: $(date)"
echo "========================================"
echo ""

# Check 1: Container running
print_info "Checking if container is running..."
if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    print_info "✓ Container is running"

    # Get container status
    STATUS=$(docker inspect --format='{{.State.Status}}' $CONTAINER_NAME)
    HEALTH=$(docker inspect --format='{{.State.Health.Status}}' $CONTAINER_NAME 2>/dev/null || echo "none")

    print_info "  Status: $STATUS"
    if [ "$HEALTH" != "none" ]; then
        print_info "  Health: $HEALTH"

        if [ "$HEALTH" != "healthy" ]; then
            print_warn "⚠ Container is not healthy!"
            send_alert "Container $CONTAINER_NAME is $HEALTH"
        fi
    fi
else
    print_error "✗ Container is not running!"
    send_alert "Container $CONTAINER_NAME is not running"

    print_info "Attempting to start container..."
    cd "$SCRIPT_DIR"
    docker compose up -d

    print_info "Waiting for container to start..."
    sleep 5
fi

# Check 2: Worker service responding
print_info "Checking worker service..."
if curl -s -f "${WORKER_URL}/api/health" > /dev/null 2>&1; then
    print_info "✓ Worker service is responding"

    # Get service details
    RESPONSE=$(curl -s "${WORKER_URL}/api/health")
    UPTIME=$(echo "$RESPONSE" | grep -o '"uptime":[0-9.]*' | cut -d':' -f2)

    if [ -n "$UPTIME" ]; then
        UPTIME_HOURS=$(echo "$UPTIME / 3600" | bc)
        print_info "  Uptime: ${UPTIME_HOURS}h"
    fi
else
    print_error "✗ Worker service is not responding!"
    send_alert "Worker service at $WORKER_URL is not responding"

    print_info "Checking container logs..."
    docker logs --tail=20 $CONTAINER_NAME

    print_info "Attempting to restart container..."
    cd "$SCRIPT_DIR"
    docker compose restart
fi

# Check 3: Resource usage
print_info "Checking resource usage..."
STATS=$(docker stats $CONTAINER_NAME --no-stream --format "{{.CPUPerc}},{{.MemUsage}}" 2>/dev/null || echo "N/A,N/A")
CPU=$(echo "$STATS" | cut -d',' -f1)
MEM=$(echo "$STATS" | cut -d',' -f2)

print_info "  CPU: $CPU"
print_info "  Memory: $MEM"

# Extract CPU percentage number
CPU_NUM=$(echo "$CPU" | grep -o '[0-9.]*' | head -1)
if [ -n "$CPU_NUM" ]; then
    CPU_CHECK=$(echo "$CPU_NUM > 80" | bc -l 2>/dev/null || echo "0")
    if [ "$CPU_CHECK" = "1" ]; then
        print_warn "⚠ High CPU usage: $CPU"
        send_alert "High CPU usage on $CONTAINER_NAME: $CPU"
    fi
fi

# Check 4: Database size
print_info "Checking database size..."
DB_SIZE=$(docker exec $CONTAINER_NAME sh -c "du -h /opt/claude-memory/data/memory.db 2>/dev/null | cut -f1" || echo "N/A")
print_info "  Database: $DB_SIZE"

# Check 5: Disk space
print_info "Checking disk space..."
DISK_USAGE=$(docker exec $CONTAINER_NAME sh -c "df -h /opt/claude-memory | tail -1 | awk '{print \$5}'" 2>/dev/null || echo "N/A")
print_info "  Disk usage: $DISK_USAGE"

DISK_NUM=$(echo "$DISK_USAGE" | grep -o '[0-9]*' | head -1)
if [ -n "$DISK_NUM" ] && [ "$DISK_NUM" -gt 80 ]; then
    print_warn "⚠ High disk usage: $DISK_USAGE"
    send_alert "High disk usage on $CONTAINER_NAME: $DISK_USAGE"
fi

# Check 6: Log file size
print_info "Checking recent logs..."
ERROR_COUNT=$(docker logs $CONTAINER_NAME --since 1h 2>&1 | grep -i "error" | wc -l)
print_info "  Errors in last hour: $ERROR_COUNT"

if [ "$ERROR_COUNT" -gt 10 ]; then
    print_warn "⚠ High error count: $ERROR_COUNT errors in last hour"
    send_alert "High error count on $CONTAINER_NAME: $ERROR_COUNT errors in last hour"
fi

# Summary
echo ""
echo "========================================"
echo "Health Check Complete"
echo "========================================"

# Exit with appropriate code
if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$" && \
   curl -s -f "${WORKER_URL}/api/health" > /dev/null 2>&1; then
    print_info "✅ All checks passed"
    exit 0
else
    print_error "❌ Some checks failed"
    exit 1
fi
