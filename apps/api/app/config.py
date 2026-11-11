import os
from typing import List
from dotenv import load_dotenv
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Robustly find kannada-news-ai repository root
curr = os.path.dirname(os.path.abspath(__file__))
while curr and os.path.basename(curr) not in ("kannada-news-ai", ""):
    if os.path.exists(os.path.join(curr, ".git")) or os.path.basename(curr) == "kannada-news-ai":
        break
    curr = os.path.dirname(curr)
repo_root = curr or os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# Load .env
load_dotenv(os.path.join(repo_root, ".env"))
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
load_dotenv(".env")

default_db_file = os.path.abspath(os.path.join(repo_root, "kannada_news_local.db")).replace(os.sep, "/")

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI-Powered News Translation from Kannada to English"
    VERSION: str = "1.0.0"
    API_PREFIX: str = "/api/v1"
    
    # Environment
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "info"
    
    # Database
    DATABASE_URL: str = f"sqlite:///{default_db_file}"
    
    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def resolve_sqlite_path(cls, v: str) -> str:
        if v and "sqlite:" in v:
            fname = v.split("sqlite:///")[-1].lstrip("./")
            if not os.path.isabs(fname):
                abs_p = os.path.abspath(os.path.join(repo_root, fname)).replace(os.sep, "/")
                return f"sqlite:///{abs_p}"
        return v
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]
    
    # ML & Translation Configuration
    TRANSLATION_BACKEND: str = os.environ.get("TRANSLATION_BACKEND", "mock")
    LLM_PROVIDER: str = os.environ.get("LLM_PROVIDER", "mock")
    GEMINI_API_KEY: str = os.environ.get("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.environ.get("GEMINI_MODEL", "gemini-3.1-flash-lite")
    
    # Worker Configuration
    WORKER_POLL_INTERVAL: float = 2.0
    MAX_RETRIES: int = 3
    
    model_config = SettingsConfigDict(
        extra="ignore"
    )

settings = Settings()
