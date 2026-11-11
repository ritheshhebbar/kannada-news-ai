import os
import sys
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, status
from sqlalchemy.orm import Session

from app.db import get_db, SessionLocal
from app.models import PipelineJob
from app.schemas.schemas import (
    ArticleListItem,
    ArticleDetailResponse,
    ArticleSubmitRequest,
    ArticleSubmitResponse,
    ArticleStatusResponse,
)
from app.services.article_service import ArticleService

router = APIRouter(prefix="/articles", tags=["Articles"])

def run_article_pipeline_task(article_id: int, job_id: int):
    """Executes the pipeline job for an article in the background."""
    try:
        from services.worker.worker import process_job
    except ImportError:
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        if root_dir not in sys.path:
            sys.path.insert(0, root_dir)
        from services.worker.worker import process_job

    db = SessionLocal()
    try:
        job = db.query(PipelineJob).filter(PipelineJob.id == job_id).first()
        if job and job.state in ("queued", "failed"):
            print(f"[BackgroundTask] Processing Job {job_id} for Article {article_id}...")
            process_job(db, job)
    except Exception as e:
        print(f"[BackgroundTask] Error processing Article {article_id}: {e}")
    finally:
        db.close()

@router.get("", response_model=dict)
def list_articles(
    source_id: Optional[int] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """List news articles with filters (source, category, status, search keyword, page)."""
    items, total = ArticleService.list_articles(
        db=db,
        source_id=source_id,
        category_slug=category,
        status=status,
        search_query=search,
        page=page,
        page_size=page_size,
    )
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size if total > 0 else 1,
    }

@router.get("/{article_id}", response_model=ArticleDetailResponse)
def get_article(article_id: int, db: Session = Depends(get_db)):
    """Retrieve full article detail including Kannada sentences, translations, and summaries."""
    article = ArticleService.get_article_detail(db, article_id)
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Article with ID {article_id} not found."
        )
    return article

@router.post("/submit", response_model=ArticleSubmitResponse, status_code=status.HTTP_201_CREATED)
def submit_article(
    payload: ArticleSubmitRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Submit Kannada text or article URL for translation and summarization."""
    try:
        response = ArticleService.submit_article(db, payload)
        if response.job_id:
            # Trigger background pipeline execution immediately
            background_tasks.add_task(run_article_pipeline_task, response.article_id, response.job_id)
        return response
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/{article_id}/status", response_model=ArticleStatusResponse)
def get_article_status(article_id: int, db: Session = Depends(get_db)):
    """Poll the processing status and progress percentage of an article."""
    stat = ArticleService.get_article_status(db, article_id)
    if not stat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Article with ID {article_id} not found."
        )
    return stat

@router.post("/{article_id}/retry", response_model=dict)
def retry_article_processing(
    article_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Re-queue an article if any AI stage failed."""
    success, job_id = ArticleService.retry_article_stage(db, article_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Article with ID {article_id} not found."
        )
    if job_id:
        background_tasks.add_task(run_article_pipeline_task, article_id, job_id)
    return {"status": "re-queued", "article_id": article_id}
