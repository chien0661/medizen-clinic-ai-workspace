#!/bin/bash
#
# Firewall Rules for Claude Memory Worker
#
# This script sets up firewall rules for the memory worker service.
# Adjust the allowed networks according to your company's network.
#

set -e

# Configuration
WORKER_PORT=37777
HTTPS_PORT=443
SSH_PORT=22

# Your company's internal network (CHANGE THIS!)
INTERNAL_NETWORK="10.0.0.0/8"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "This script must be run as root (use sudo)"
    exit 1
fi

print_info "Setting up firewall rules..."

# Check if ufw is installed
if ! command -v ufw &> /dev/null; then
    print_info "Installing ufw..."
    apt-get update
    apt-get install -y ufw
fi

# Reset ufw to defaults (careful!)
# ufw --force reset

# Set default policies
print_info "Setting default policies..."
ufw default deny incoming
ufw default allow outgoing

# Allow SSH (IMPORTANT: don't lock yourself out!)
print_info "Allowing SSH on port $SSH_PORT..."
ufw allow $SSH_PORT/tcp comment 'SSH access'

# Allow worker port from internal network only
print_info "Allowing worker port $WORKER_PORT from $INTERNAL_NETWORK..."
ufw allow from $INTERNAL_NETWORK to any port $WORKER_PORT proto tcp comment 'Claude Memory Worker'

# Allow HTTPS if using nginx
print_info "Allowing HTTPS on port $HTTPS_PORT..."
ufw allow $HTTPS_PORT/tcp comment 'HTTPS for nginx'

# Allow HTTP for Let's Encrypt (optional)
# ufw allow 80/tcp comment 'HTTP for certbot'

# Enable logging
ufw logging on

# Show rules before enabling
print_info "Firewall rules to be applied:"
ufw show added

# Enable firewall
read -p "Enable firewall with these rules? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    ufw --force enable
    print_info "Firewall enabled!"
    ufw status verbose
else
    print_info "Firewall not enabled. Rules are configured but inactive."
fi

print_info "Firewall setup complete!"
echo ""
print_info "To modify allowed networks:"
echo "  1. Edit this script and change INTERNAL_NETWORK"
echo "  2. Re-run: sudo bash firewall-rules.sh"
echo ""
print_info "To allow specific IP:"
echo "  sudo ufw allow from <IP> to any port $WORKER_PORT"
echo ""
print_info "To check status:"
echo "  sudo ufw status verbose"
