from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.schemas import (
    ArticleListItem,
    ArticleDetailResponse,
    ArticleSubmitRequest,
    ArticleSubmitResponse,
    ArticleStatusResponse,
)
from app.services.article_service import ArticleService

router = APIRouter(prefix="/articles", tags=["Articles"])

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
def submit_article(payload: ArticleSubmitRequest, db: Session = Depends(get_db)):
    """Submit Kannada text or article URL for translation and summarization."""
    try:
        response = ArticleService.submit_article(db, payload)
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
def retry_article_processing(article_id: int, db: Session = Depends(get_db)):
    """Re-queue an article if any AI stage failed."""
    success = ArticleService.retry_article_stage(db, article_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Article with ID {article_id} not found."
        )
    return {"status": "re-queued", "article_id": article_id}
