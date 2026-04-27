#!/bin/bash
#
# Test Connection to Remote Memory Server
#
# Usage: bash test-connection.sh [server-url]
#

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

# Get server URL
if [ -n "$1" ]; then
    SERVER_URL="$1"
elif [ -f ".env" ]; then
    source .env
    SERVER_URL="${WORKER_URL}"
else
    print_error "No server URL provided"
    echo "Usage: $0 <server-url>"
    echo "   or: Set WORKER_URL in .env"
    exit 1
fi

echo "Testing connection to: $SERVER_URL"
echo ""

FAILED=0

# Test 1: Basic connectivity
echo "[1/5] Testing basic connectivity..."
if command -v curl &> /dev/null; then
    if curl -s -m 5 "$SERVER_URL/api/health" > /dev/null; then
        print_ok "Server is reachable"
    else
        print_error "Cannot reach server"
        FAILED=$((FAILED + 1))
    fi
else
    print_warn "curl not found, skipping connectivity test"
fi

# Test 2: Health endpoint
echo "[2/5] Testing health endpoint..."
if command -v curl &> /dev/null; then
    RESPONSE=$(curl -s -f "$SERVER_URL/api/health" 2>&1)
    if [ $? -eq 0 ]; then
        print_ok "Health endpoint responding"
        echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
    else
        print_error "Health endpoint not responding"
        FAILED=$((FAILED + 1))
    fi
fi

# Test 3: API authentication (if API key is set)
echo "[3/5] Testing API authentication..."
if [ -n "$MEMORY_API_KEY" ]; then
    RESPONSE=$(curl -s -w "\n%{http_code}" -H "X-API-Key: $MEMORY_API_KEY" "$SERVER_URL/api/health")
    HTTP_CODE=$(echo "$RESPONSE" | tail -n1)

    if [ "$HTTP_CODE" = "200" ]; then
        print_ok "Authentication successful"
    elif [ "$HTTP_CODE" = "401" ]; then
        print_error "Authentication failed (check API key)"
        FAILED=$((FAILED + 1))
    else
        print_warn "Unexpected response code: $HTTP_CODE"
    fi
else
    print_warn "MEMORY_API_KEY not set, skipping auth test"
fi

# Test 4: Network latency
echo "[4/5] Testing network latency..."
if command -v curl &> /dev/null; then
    START=$(date +%s%N)
    curl -s -f "$SERVER_URL/api/health" > /dev/null 2>&1
    END=$(date +%s%N)
    LATENCY=$(( (END - START) / 1000000 ))

    if [ $LATENCY -lt 100 ]; then
        print_ok "Latency: ${LATENCY}ms (excellent)"
    elif [ $LATENCY -lt 500 ]; then
        print_ok "Latency: ${LATENCY}ms (good)"
    else
        print_warn "Latency: ${LATENCY}ms (high)"
    fi
fi

# Test 5: DNS resolution
echo "[5/5] Testing DNS resolution..."
SERVER_HOST=$(echo "$SERVER_URL" | sed -e 's|^[^/]*//||' -e 's|[:/].*||')
if command -v nslookup &> /dev/null; then
    if nslookup "$SERVER_HOST" > /dev/null 2>&1; then
        IP=$(nslookup "$SERVER_HOST" | awk '/^Address: / { print $2 }' | tail -1)
        print_ok "DNS resolves to: $IP"
    else
        print_error "DNS resolution failed"
        FAILED=$((FAILED + 1))
    fi
elif command -v host &> /dev/null; then
    if host "$SERVER_HOST" > /dev/null 2>&1; then
        print_ok "DNS resolution successful"
    else
        print_error "DNS resolution failed"
        FAILED=$((FAILED + 1))
    fi
else
    print_warn "DNS tools not found, skipping"
fi

echo ""
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}All tests passed!${NC}"
    echo ""
    echo "Your client is correctly configured for remote memory."
    echo "Restart Claude Code to use remote server."
    exit 0
else
    echo -e "${RED}$FAILED test(s) failed${NC}"
    echo ""
    echo "Troubleshooting:"
    echo "  1. Check server is running: sudo systemctl status claude-memory-worker"
    echo "  2. Check firewall allows connections from this IP"
    echo "  3. Verify WORKER_URL in .env is correct"
    echo "  4. Check API key matches server configuration"
    exit 1
fi
