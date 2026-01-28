#!/bin/bash
# =============================================================================
# Muntazir Production Deployment Script
# Automated deployment with backup, migration, and health check
# =============================================================================

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="${PROJECT_DIR}/docker-compose.yml"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Functions
log_step() {
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}▶ $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Header
echo "=================================================="
echo "🚀 Muntazir Production Deployment"
echo "=================================================="
echo "Project: $PROJECT_DIR"
echo "Time: $(date)"
echo ""

# Step 1: Pre-flight checks
log_step "Step 1: Pre-flight Checks"

if ! command -v docker &> /dev/null; then
    log_error "Docker is not installed!"
    exit 1
fi
log_success "Docker found"

if ! docker info &> /dev/null; then
    log_error "Docker daemon is not running!"
    exit 1
fi
log_success "Docker daemon running"

cd "$PROJECT_DIR"

# Step 2: Backup database
log_step "Step 2: Database Backup"
if [ -f "${SCRIPT_DIR}/backup.sh" ]; then
    bash "${SCRIPT_DIR}/backup.sh"
else
    log_warning "Backup script not found, skipping..."
fi

# Step 3: Pull latest code (if using git)
log_step "Step 3: Pull Latest Code"
if [ -d ".git" ]; then
    echo "Fetching latest changes..."
    git fetch origin
    
    LOCAL=$(git rev-parse HEAD)
    REMOTE=$(git rev-parse @{u} 2>/dev/null || echo "$LOCAL")
    
    if [ "$LOCAL" != "$REMOTE" ]; then
        echo "Pulling updates..."
        git pull origin main
        log_success "Code updated"
    else
        log_success "Already up to date"
    fi
else
    log_warning "Not a git repository, skipping pull"
fi

# Step 4: Stop existing containers
log_step "Step 4: Stop Existing Containers"
docker compose down --remove-orphans 2>/dev/null || docker-compose down --remove-orphans 2>/dev/null || true
log_success "Containers stopped"

# Step 5: Run database migrations
log_step "Step 5: Database Migrations"
if [ -f "migrate.py" ]; then
    echo "Running migrations..."
    python3 migrate.py upgrade --no-backup || {
        log_warning "Migration via Python failed, trying inside container..."
    }
else
    log_warning "migrate.py not found, skipping migrations"
fi

# Step 6: Build and start containers
log_step "Step 6: Build and Start Containers"
echo "Building image..."
docker compose build --no-cache 2>/dev/null || docker-compose build --no-cache

echo "Starting containers..."
docker compose up -d 2>/dev/null || docker-compose up -d

log_success "Containers started"

# Step 7: Wait for health check
log_step "Step 7: Health Check"
echo "Waiting for application to start..."

MAX_ATTEMPTS=30
ATTEMPT=0

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    ATTEMPT=$((ATTEMPT + 1))
    
    # Check container status
    STATUS=$(docker inspect --format='{{.State.Health.Status}}' muntazir_bot 2>/dev/null || echo "unknown")
    
    if [ "$STATUS" = "healthy" ]; then
        log_success "Application is healthy!"
        break
    elif [ "$STATUS" = "unhealthy" ]; then
        log_error "Application is unhealthy!"
        echo "Checking logs..."
        docker compose logs --tail=50
        exit 1
    fi
    
    echo "  Attempt $ATTEMPT/$MAX_ATTEMPTS - Status: $STATUS"
    sleep 2
done

if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
    log_warning "Health check timed out, checking manually..."
    curl -sf http://localhost:8000/api/health || {
        log_error "Application is not responding!"
        docker compose logs --tail=50
        exit 1
    }
fi

# Step 8: Show status
log_step "Step 8: Deployment Status"
echo ""
docker compose ps
echo ""
echo "=================================================="
log_success "Deployment Complete!"
echo "=================================================="
echo ""
echo "📍 Endpoints:"
echo "   - Web Interface: http://localhost:8000"
echo "   - Dashboard:     http://localhost:8000/dashboard"
echo "   - Operator:      http://localhost:8000/operator"
echo "   - Health:        http://localhost:8000/api/health"
echo ""
echo "📋 Useful commands:"
echo "   - View logs:     docker compose logs -f"
echo "   - Stop:          docker compose down"
echo "   - Restart:       docker compose restart"
echo ""
