import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI-Powered News Translation from Kannada to English"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api/v1"
    
    # Environment
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "info"
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/kannada_news_ai"
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
    ]
    
    # ML & Translation Configuration
    TRANSLATION_BACKEND: str = "mock"
    LLM_PROVIDER: str = "mock"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"
    
    # Worker Configuration
    WORKER_POLL_INTERVAL: float = 2.0
    MAX_RETRIES: int = 3
    
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
