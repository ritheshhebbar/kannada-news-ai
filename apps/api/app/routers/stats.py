from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Category, Source
from app.schemas.schemas import (
    DashboardStats,
    CategoryResponse,
    SourceResponse,
)
from app.services.search_service import SearchAndHistoryService

router = APIRouter(tags=["Stats & Metadata"])

@router.get("/stats", response_model=DashboardStats)
def get_dashboard_stats(db: Session = Depends(get_db)):
    """Retrieve operational metrics, translation quality rates, and category distribution."""
    return SearchAndHistoryService.get_stats(db)

@router.get("/categories", response_model=List[CategoryResponse])
def get_categories(db: Session = Depends(get_db)):
    """List all supported news categories."""
    cats = db.query(Category).all()
    return cats

@router.get("/sources", response_model=List[SourceResponse])
def get_sources(db: Session = Depends(get_db)):
    """List registered Kannada news outlets and their crawling status."""
    sources = db.query(Source).all()
    return sources
