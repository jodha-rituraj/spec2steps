"""
Application Configuration
Centralized configuration management for the FastAPI application
"""

from pydantic_settings import BaseSettings
from typing import List
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
# config.py is in root/core/config.py
# .env is in root/.env
env_path = Path(__file__).parent.parent / ".env"  # ← FIXED: Only 2 parents
load_dotenv(dotenv_path=env_path)


class Settings(BaseSettings):
    """Application settings"""
    
    # Application Info
    APP_NAME: str = "AI Test Automation Generator"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "End-to-End AI Enabled Test Cases Generation and Automation"
    
    # Server Configuration
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    DEBUG: bool = True
    RELOAD: bool = True
    
    # CORS Configuration
    CORS_ORIGINS: List[str] = ["*"]  # In production, specify actual origins
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]
    
    # API Configuration
    API_PREFIX: str = "/api"
    
    # LLM Configuration (from environment variables)
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "mixtral-8x7b-32768")
    LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.7"))
    LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "2000"))
    
    # File Paths
    FRONTEND_DIR: Path = Path(__file__).parent.parent / "frontend"  # ← FIXED
    UPLOAD_DIR: Path = Path(__file__).parent.parent / "uploads"     # ← FIXED
    OUTPUT_DIR: Path = Path(__file__).parent.parent / "outputs"     # ← FIXED
    
    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Rate Limiting (for future implementation)
    RATE_LIMIT_ENABLED: bool = False
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # Feature Flags
    ENABLE_CACHING: bool = False
    ENABLE_METRICS: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create settings instance
settings = Settings()


def get_settings() -> Settings:
    """
    Get application settings
    
    Returns:
        Settings instance
    """
    return settings


def validate_settings():
    """
    Validate required settings
    
    Raises:
        ValueError: If required settings are missing
    """
    if not settings.GROQ_API_KEY:
        raise ValueError(
            "GROQ_API_KEY is not set. Please set it in your .env file."
        )
    
    # Create necessary directories
    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    settings.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    print(f"✅ Configuration validated successfully")
    print(f"📁 Frontend directory: {settings.FRONTEND_DIR}")
    print(f"📁 Upload directory: {settings.UPLOAD_DIR}")
    print(f"📁 Output directory: {settings.OUTPUT_DIR}")


# Validate on import
if __name__ != "__main__":
    try:
        validate_settings()
    except Exception as e:
        print(f"⚠️ Configuration warning: {e}")