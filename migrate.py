#!/usr/bin/env python3
"""
Database Migration Runner
Safely runs Alembic migrations with backup and rollback support
"""
import os
import sys
import shutil
import argparse
from datetime import datetime
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))


def backup_database(db_path: str, backup_dir: str = "backups") -> str:
    """Create timestamped backup of database"""
    db_file = Path(db_path)
    if not db_file.exists():
        print(f"⚠️  Database not found at {db_path}, skipping backup")
        return ""
    
    backup_path = Path(backup_dir)
    backup_path.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = backup_path / f"muntazir_{timestamp}.db"
    
    shutil.copy2(db_file, backup_file)
    print(f"✅ Database backed up to: {backup_file}")
    
    # Rotate old backups (keep last 7)
    backups = sorted(backup_path.glob("muntazir_*.db"))
    if len(backups) > 7:
        for old_backup in backups[:-7]:
            old_backup.unlink()
            print(f"🗑️  Removed old backup: {old_backup.name}")
    
    return str(backup_file)


def run_migrations(direction: str = "upgrade", revision: str = "head"):
    """Run Alembic migrations"""
    from alembic.config import Config
    from alembic import command
    
    alembic_cfg = Config("alembic.ini")
    
    try:
        if direction == "upgrade":
            print(f"⬆️  Upgrading database to: {revision}")
            command.upgrade(alembic_cfg, revision)
        elif direction == "downgrade":
            print(f"⬇️  Downgrading database to: {revision}")
            command.downgrade(alembic_cfg, revision)
        elif direction == "current":
            print("📍 Current database revision:")
            command.current(alembic_cfg)
            return
        elif direction == "history":
            print("📜 Migration history:")
            command.history(alembic_cfg)
            return
        
        print("✅ Migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Database Migration Tool")
    parser.add_argument(
        "command",
        choices=["upgrade", "downgrade", "current", "history", "backup"],
        help="Migration command to run"
    )
    parser.add_argument(
        "--revision", "-r",
        default="head",
        help="Target revision (default: head for upgrade, -1 for downgrade)"
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Skip database backup before migration"
    )
    parser.add_argument(
        "--db-path",
        default="data/muntazir.db",
        help="Path to database file"
    )
    
    args = parser.parse_args()
    
    # Load environment
    from dotenv import load_dotenv
    load_dotenv()
    
    db_path = os.getenv("DATABASE_PATH", args.db_path)
    
    print("=" * 50)
    print("🗄️  Muntazir Database Migration Tool")
    print("=" * 50)
    
    if args.command == "backup":
        backup_database(db_path)
        return
    
    if args.command in ["upgrade", "downgrade"] and not args.no_backup:
        backup_database(db_path)
    
    run_migrations(args.command, args.revision)


if __name__ == "__main__":
    main()
