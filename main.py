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
