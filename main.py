"""
Muntazir - Iraqi Arabic Sales AI Agent
منتظر - وكيل المبيعات العراقي الذكي

Main entry point for the application.
"""

import os
import sys
import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))


def run_migrations():
    """Run database migrations on startup (inside container)"""
    try:
        from alembic.config import Config
        from alembic import command
        
        # Check if alembic.ini exists
        if not os.path.exists("alembic.ini"):
            print("⚠️  alembic.ini not found, skipping migrations")
            return
        
        alembic_cfg = Config("alembic.ini")
        print("🔄 Running database migrations...")
        command.upgrade(alembic_cfg, "head")
        print("✅ Migrations complete")
    except ImportError:
        print("⚠️  Alembic not installed, skipping migrations")
    except Exception as e:
        # Don't fail hard on migration errors - log and continue
        # This allows the app to start even if DB is already migrated
        print(f"⚠️  Migration note: {e}")


def main():
    """Run the Muntazir application"""
    port = int(os.getenv("APP_PORT", 8000))
    debug = os.getenv("DEBUG", "true").lower() == "true"
    
    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║   🤖  منتظر - Muntazir                                   ║
    ║   وكيل المبيعات العراقي الذكي                            ║
    ║   Iraqi Arabic Sales AI Agent                            ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
    """)
    
    # Run migrations before starting (inside container)
    run_migrations()
    
    print(f"🚀 Starting server on http://localhost:{port}")
    print(f"📝 Debug mode: {debug}")
    print(f"🔑 API Key configured: {'Yes' if os.getenv('GEMINI_API_KEY') else 'No'}")
    print()
    
    uvicorn.run(
        "src.web.app:app",
        host="0.0.0.0",
        port=port,
        reload=debug,
    )


if __name__ == "__main__":
    # Force UTF-8 for Windows console
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    main()

