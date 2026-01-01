"""
FastAPI Application Entry Point
Main application setup with CORS configuration and route inclusion
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import os
from pathlib import Path

from api.routes import router as api_router

# Initialize FastAPI app
app = FastAPI(
    title="AI Test Automation Generator",
    description="End-to-End AI Enabled Test Cases Generation and Automation Dashboard",
    version="1.0.0"
)

# Configure CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api")

# Serve static frontend files
frontend_path = Path(__file__).parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")
    
    @app.get("/", response_class=HTMLResponse)
    async def serve_frontend():
        """Serve the main frontend HTML page"""
        index_path = frontend_path / "index.html"
        if index_path.exists():
            with open(index_path, "r", encoding="utf-8") as f:
                return HTMLResponse(content=f.read())
        return HTMLResponse(content="<h1>Frontend not found</h1>", status_code=404)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "AI Test Automation Generator API is running"}

# Root API info
@app.get("/api")
async def api_info():
    """API information endpoint"""
    return {
        "name": "AI Test Automation Generator API",
        "version": "1.0.0",
        "endpoints": {
            "generate_feature": "/api/generate-feature",
            "verify_feature": "/api/verify-feature",
            "regenerate_feature": "/api/regenerate-feature",
            "generate_scripts": "/api/generate-scripts",
            "merge_scripts": "/api/merge-scripts"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)