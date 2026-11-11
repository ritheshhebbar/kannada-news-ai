import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db import engine, Base
from app.routers import articles, search, history, feedback, stats, collector

logger = logging.getLogger("uvicorn")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure database schema is ready on startup
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database schema initialized successfully.")
    except Exception as e:
        logger.warning(f"Database connection deferred: {e}")
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Backend API for AI-Powered Kannada-to-English News Translation and Summarization with Multi-Layer Verification.",
    lifespan=lifespan,
    docs_url=f"{settings.API_PREFIX}/docs",
    openapi_url=f"{settings.API_PREFIX}/openapi.json",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routers under prefix
app.include_router(articles.router, prefix=settings.API_PREFIX)
app.include_router(search.router, prefix=settings.API_PREFIX)
app.include_router(history.router, prefix=settings.API_PREFIX)
app.include_router(feedback.router, prefix=settings.API_PREFIX)
app.include_router(stats.router, prefix=settings.API_PREFIX)
app.include_router(collector.router, prefix=settings.API_PREFIX)

@app.get("/health", tags=["Health"])
def health_check():
    """System health and operational parameters."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "translation_backend": settings.TRANSLATION_BACKEND,
        "llm_provider": settings.LLM_PROVIDER,
    }

@app.get("/", tags=["Root"])
def root():
    return {
        "message": "AI-Powered Kannada-to-English News Translation API is running.",
        "documentation": f"{settings.API_PREFIX}/docs",
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
