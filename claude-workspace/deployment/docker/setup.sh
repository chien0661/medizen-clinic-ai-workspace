#!/bin/bash

# Claude Memory Worker - Easy Setup Script
# This script helps you set up the persistent memory system quickly

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check if running from correct directory
if [ ! -f "docker-compose.yml" ]; then
    print_error "Please run this script from deployment/docker/ directory"
    exit 1
fi

print_header "Claude Persistent Memory - Setup Wizard"

echo "This script will help you set up the persistent memory system."
echo "You'll need:"
echo "  • Docker & Docker Compose installed"
echo "  • Anthropic API key"
echo ""
read -p "Press Enter to continue..."
echo ""

# Step 1: Check Docker
print_header "Step 1: Checking Prerequisites"

if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version)
    print_success "Docker found: $DOCKER_VERSION"
else
    print_error "Docker not found. Please install Docker first."
    echo "  Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

if command -v docker compose &> /dev/null || command -v docker-compose &> /dev/null; then
    print_success "Docker Compose found"
else
    print_error "Docker Compose not found. Please install Docker Compose."
    exit 1
fi

echo ""

# Step 2: Create .env file
print_header "Step 2: Configuring Environment"

if [ -f ".env" ]; then
    print_warning ".env file already exists"
    read -p "Overwrite it? (y/n): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Keeping existing .env file"
        ENV_EXISTS=true
    fi
fi

if [ "$ENV_EXISTS" != "true" ]; then
    if [ ! -f ".env.example" ]; then
        print_error ".env.example not found!"
        exit 1
    fi

    cp .env.example .env
    print_success "Created .env file from template"
    echo ""

    # Get Anthropic API key
    print_info "You need an Anthropic API key for memory compression"
    echo "  Get it from: https://console.anthropic.com/"
    echo ""
    read -p "Enter your Anthropic API key (sk-ant-...): " ANTHROPIC_KEY
    
    if [ -z "$ANTHROPIC_KEY" ]; then
        print_error "API key is required!"
        exit 1
    fi

    # Generate client API key
    print_info "Generating client API key for authentication..."
    CLIENT_API_KEY=$(openssl rand -hex 32)
    print_success "Generated: $CLIENT_API_KEY"
    echo ""

    # Update .env file
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s|ANTHROPIC_API_KEY=.*|ANTHROPIC_API_KEY=$ANTHROPIC_KEY|" .env
        sed -i '' "s|API_KEY=.*|API_KEY=$CLIENT_API_KEY|" .env
    else
        # Linux
        sed -i "s|ANTHROPIC_API_KEY=.*|ANTHROPIC_API_KEY=$ANTHROPIC_KEY|" .env
        sed -i "s|API_KEY=.*|API_KEY=$CLIENT_API_KEY|" .env
    fi

    print_success "Updated .env file with your keys"
    echo ""
    print_warning "IMPORTANT: Save these credentials securely!"
    echo "  Anthropic API Key: $ANTHROPIC_KEY"
    echo "  Client API Key: $CLIENT_API_KEY"
    echo ""
    read -p "Press Enter when you've saved them..."
    echo ""
fi

# Step 3: Build Docker image
print_header "Step 3: Building Docker Image"

print_info "This may take 2-3 minutes..."
if docker compose build; then
    print_success "Docker image built successfully"
else
    print_error "Failed to build Docker image"
    exit 1
fi
echo ""

# Step 4: Start container
print_header "Step 4: Starting Container"

if docker compose up -d; then
    print_success "Container started successfully"
else
    print_error "Failed to start container"
    exit 1
fi

# Wait for health check
print_info "Waiting for health check..."
sleep 5

if docker compose ps | grep -q "healthy"; then
    print_success "Container is healthy"
else
    print_warning "Container started but health check pending"
    print_info "Check status with: docker compose ps"
fi
echo ""

# Step 5: Test API
print_header "Step 5: Testing API"

if command -v curl &> /dev/null; then
    if curl -s -f http://localhost:37777/api/health > /dev/null; then
        print_success "API is responding"
        curl -s http://localhost:37777/api/health | python -m json.tool 2>/dev/null || cat
    else
        print_warning "API not responding yet (may need more time)"
    fi
else
    print_warning "curl not found, skipping API test"
fi
echo ""

# Step 6: Configure client
print_header "Step 6: Next Steps"

echo "✓ Docker container is running"
echo "✓ Memory worker is ready at http://localhost:37777"
echo ""
echo "To complete setup:"
echo ""
echo "1. Configure Claude Code settings:"
echo "   Run: bash ../client/configure-remote.sh http://localhost:37777 $CLIENT_API_KEY"
echo ""
echo "2. Restart Claude Code:"
echo "   exit"
echo "   claude code"
echo ""
echo "3. Test memory search:"
echo "   /memory-search \"test\""
echo ""
echo "Useful commands:"
echo "  • View logs: docker compose logs -f"
echo "  • Check status: docker compose ps"
echo "  • Stop: docker compose down"
echo "  • Restart: docker compose restart"
echo ""
print_success "Setup complete! 🎉"

