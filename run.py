"""
Application Startup Script
Easy way to start the FastAPI backend server
"""

import uvicorn
import webbrowser
import time
import threading
from pathlib import Path
import sys

# Add root directory to path
root_path = Path(__file__).parent
sys.path.insert(0, str(root_path))

from core.config import settings


def open_browser():
    """Open browser after server starts"""
    time.sleep(2)  # Wait for server to start
    url = f"http://{settings.HOST}:{settings.PORT}"
    print(f"\n🌐 Opening browser at {url}")
    webbrowser.open(url)


def main():
    """Main function to start the application"""
    
    print("=" * 60)
    print(f"🚀 Starting {settings.APP_NAME}")
    print(f"📦 Version: {settings.APP_VERSION}")
    print("=" * 60)
    
    # Check if frontend exists
    if settings.FRONTEND_DIR.exists():
        print(f"✅ Frontend directory found: {settings.FRONTEND_DIR}")
    else:
        print(f"⚠️  Frontend directory not found: {settings.FRONTEND_DIR}")
        print("   The API will still run, but no UI will be available")
    
    print(f"\n📡 Starting server on http://{settings.HOST}:{settings.PORT}")
    print(f"📚 API Documentation: http://{settings.HOST}:{settings.PORT}/docs")
    print(f"🔧 Alternative docs: http://{settings.HOST}:{settings.PORT}/redoc")
    print("\n💡 Press Ctrl+C to stop the server\n")
    
    # Open browser in separate thread
    if settings.FRONTEND_DIR.exists():
        browser_thread = threading.Thread(target=open_browser, daemon=True)
        browser_thread.start()
    
    # Start FastAPI server
    try:
        uvicorn.run(
            "main:app",           # ← FIXED: Changed from "backend.main:app"
            host=settings.HOST,
            port=settings.PORT,
            reload=settings.RELOAD,
            log_level=settings.LOG_LEVEL.lower()
        )
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()