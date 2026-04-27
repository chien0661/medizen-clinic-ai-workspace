#!/bin/bash
#
# Configure Client for Remote Memory Server
#
# Usage: bash configure-remote.sh <server-url> [api-key]
# Example: bash configure-remote.sh http://memory.company.com:37777 my-api-key
#

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

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
    print_error "Usage: $0 <server-url> [api-key]"
    echo "Example: $0 http://memory.company.com:37777"
    echo "         $0 http://memory.company.com:37777 my-api-key"
    exit 1
fi

SERVER_URL="$1"
API_KEY="${2:-}"

print_info "Configuring client for remote server: $SERVER_URL"

# Backup current configuration
if [ -f "${PROJECT_ROOT}/.env" ]; then
    cp "${PROJECT_ROOT}/.env" "${PROJECT_ROOT}/.env.backup.$(date +%Y%m%d-%H%M%S)"
    print_info "Backed up current .env file"
fi

# Update or create .env file
ENV_FILE="${PROJECT_ROOT}/.env"

# Read existing values or set defaults
if [ -f "$ENV_FILE" ]; then
    source "$ENV_FILE"
fi

ANTHROPIC_KEY="${ANTHROPIC_API_KEY:-your_api_key_here}"

# Create updated .env
cat > "$ENV_FILE" <<EOF
# Claude Memory - Client Configuration
# Remote Server Mode
# Updated: $(date)

# Remote worker URL
WORKER_URL=$SERVER_URL

# API Key for remote authentication
MEMORY_API_KEY=${API_KEY:-generate-and-set-this}

# Anthropic API Key (required)
ANTHROPIC_API_KEY=$ANTHROPIC_KEY

# Memory features enabled
MEMORY_ENABLED=true
EOF

print_info "Updated .env file"

# Update .mcp.json if it exists
MCP_FILE="${PROJECT_ROOT}/.mcp.json"
if [ ! -f "$MCP_FILE" ] && [ -f "${PROJECT_ROOT}/.mcp.json.example" ]; then
    cp "${PROJECT_ROOT}/.mcp.json.example" "$MCP_FILE"
    print_info "Created .mcp.json from example"
fi

if [ -f "$MCP_FILE" ]; then
    # Backup
    cp "$MCP_FILE" "${MCP_FILE}.backup.$(date +%Y%m%d-%H%M%S)"

    # Update using node to properly handle JSON
    node <<EOF_NODE
const fs = require('fs');
const config = JSON.parse(fs.readFileSync('$MCP_FILE', 'utf8'));

if (config.mcpServers && config.mcpServers['claude-mem']) {
    config.mcpServers['claude-mem'].env.WORKER_URL = '$SERVER_URL';
    if ('$API_KEY') {
        config.mcpServers['claude-mem'].env.API_KEY = '\${MEMORY_API_KEY}';
    }
    fs.writeFileSync('$MCP_FILE', JSON.stringify(config, null, 2));
    console.log('[INFO] Updated .mcp.json configuration');
} else {
    console.log('[WARN] claude-mem server not found in .mcp.json');
}
EOF_NODE
fi

# Test connection
print_info "Testing connection to remote server..."
if command -v curl &> /dev/null; then
    if curl -s -f "${SERVER_URL}/api/health" > /dev/null; then
        print_info "✅ Successfully connected to remote server!"
        curl -s "${SERVER_URL}/api/health" | node -e "const data=require('fs').readFileSync(0); console.log(JSON.stringify(JSON.parse(data), null, 2))"
    else
        print_error "❌ Failed to connect to remote server"
        print_warn "Please check:"
        print_warn "  1. Server URL is correct: $SERVER_URL"
        print_warn "  2. Server is running: sudo systemctl status claude-memory-worker"
        print_warn "  3. Firewall allows connections from this machine"
        print_warn "  4. Network connectivity"
        exit 1
    fi
else
    print_warn "curl not found, skipping connection test"
fi

# Summary
echo ""
print_info "============================================"
print_info "Configuration Complete!"
print_info "============================================"
echo ""
print_info "Settings:"
print_info "  Server URL: $SERVER_URL"
print_info "  Config file: $ENV_FILE"
print_info "  MCP file: $MCP_FILE"
echo ""

if [ -z "$API_KEY" ]; then
    print_warn "⚠️  API Key not set!"
    print_warn "⚠️  Get the API key from your server administrator"
    print_warn "⚠️  Update $ENV_FILE with: MEMORY_API_KEY=your-key"
    echo ""
fi

print_info "Next steps:"
echo "  1. If API key not set, update .env file:"
echo "     nano $ENV_FILE"
echo ""
echo "  2. Restart Claude Code to apply changes:"
echo "     exit"
echo "     claude code"
echo ""
echo "  3. Test memory features:"
echo "     /memory-search \"test\""
echo ""
print_info "To revert to local mode:"
echo "  bash deployment/client/configure-local.sh"
