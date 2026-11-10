from typing import List, Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.schemas import (
    SearchItemResponse,
    ReadingItemResponse,
    BookmarkCreate,
    ArticleListItem,
)
from app.services.search_service import SearchAndHistoryService

router = APIRouter(tags=["History & Bookmarks"])

# --- Reading History ---

@router.get("/history/reading", response_model=List[ReadingItemResponse])
def get_reading_history(session_id: str = Query(...), limit: int = 20, db: Session = Depends(get_db)):
    """Fetch recent reading history for the user session."""
    return SearchAndHistoryService.get_reading_history(db, session_id, limit=limit)

@router.post("/history/reading/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
def record_article_read(article_id: int, session_id: str = Query(...), db: Session = Depends(get_db)):
    """Record an article opened by user."""
    SearchAndHistoryService.record_reading(db, session_id, article_id)
    return

# --- Search History ---

@router.get("/history/search", response_model=List[SearchItemResponse])
def get_search_history(session_id: str = Query(...), limit: int = 10, db: Session = Depends(get_db)):
    """Fetch past search queries for the user session."""
    return SearchAndHistoryService.get_search_history(db, session_id, limit=limit)

@router.post("/history/clear", status_code=status.HTTP_204_NO_CONTENT)
def clear_all_history(session_id: str = Query(...), db: Session = Depends(get_db)):
    """Clear reading and search history for the user session."""
    SearchAndHistoryService.clear_history(db, session_id)
    return

# --- Bookmarks ---

@router.get("/bookmarks", response_model=List[ArticleListItem])
def get_bookmarks(session_id: str = Query(...), db: Session = Depends(get_db)):
    """Retrieve bookmarked articles for the session."""
    return SearchAndHistoryService.get_bookmarks(db, session_id)

@router.post("/bookmarks", status_code=status.HTTP_201_CREATED)
def create_bookmark(payload: BookmarkCreate, db: Session = Depends(get_db)):
    """Bookmark an article."""
    SearchAndHistoryService.add_bookmark(db, payload.session_id, payload.article_id)
    return {"status": "bookmarked", "article_id": payload.article_id}

@router.delete("/bookmarks/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_bookmark(article_id: int, session_id: str = Query(...), db: Session = Depends(get_db)):
    """Remove a bookmarked article."""
    SearchAndHistoryService.remove_bookmark(db, session_id, article_id)
    return

