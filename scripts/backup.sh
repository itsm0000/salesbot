#!/bin/bash
# =============================================================================
# Muntazir Database Backup Script
# Creates timestamped backups with rotation
# =============================================================================

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
DATA_DIR="${PROJECT_DIR}/data"
BACKUP_DIR="${PROJECT_DIR}/backups"
DB_FILE="${DATA_DIR}/muntazir.db"
MAX_BACKUPS=7

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=================================================="
echo "🗄️  Muntazir Database Backup"
echo "=================================================="

# Create backup directory if needed
mkdir -p "$BACKUP_DIR"

# Check if database exists
if [ ! -f "$DB_FILE" ]; then
    echo -e "${YELLOW}⚠️  Database not found at: $DB_FILE${NC}"
    echo "Nothing to backup."
    exit 0
fi

# Create timestamped backup
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/muntazir_${TIMESTAMP}.db"

echo "📁 Source: $DB_FILE"
echo "📦 Backup: $BACKUP_FILE"

# Copy database
cp "$DB_FILE" "$BACKUP_FILE"

# Verify backup
if [ -f "$BACKUP_FILE" ]; then
    SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo -e "${GREEN}✅ Backup created successfully ($SIZE)${NC}"
else
    echo -e "${RED}❌ Backup failed!${NC}"
    exit 1
fi

# Rotate old backups
echo ""
echo "🔄 Rotating old backups (keeping last $MAX_BACKUPS)..."
BACKUP_COUNT=$(ls -1 "$BACKUP_DIR"/muntazir_*.db 2>/dev/null | wc -l)

if [ "$BACKUP_COUNT" -gt "$MAX_BACKUPS" ]; then
    DELETE_COUNT=$((BACKUP_COUNT - MAX_BACKUPS))
    ls -1t "$BACKUP_DIR"/muntazir_*.db | tail -n "$DELETE_COUNT" | while read OLD_BACKUP; do
        echo "🗑️  Removing: $(basename "$OLD_BACKUP")"
        rm "$OLD_BACKUP"
    done
fi

echo ""
echo "📊 Current backups:"
ls -lh "$BACKUP_DIR"/muntazir_*.db 2>/dev/null | tail -5 || echo "No backups found"

echo ""
echo -e "${GREEN}✅ Backup complete!${NC}"
