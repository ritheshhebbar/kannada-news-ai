from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.services.search_service import SearchAndHistoryService

router = APIRouter(prefix="/search", tags=["Search"])

@router.get("", response_model=dict)
def search_articles(
    q: str = Query(..., min_length=1, description="Kannada or English search query"),
    session_id: Optional[str] = Query(None, description="Client session ID for recording history"),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """Full-text search over articles with search history logging."""
    items, total = SearchAndHistoryService.search_articles(
        db=db,
        query_text=q,
        session_id=session_id,
        page=page,
        page_size=page_size,
    )
    return {
        "query": q,
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }
