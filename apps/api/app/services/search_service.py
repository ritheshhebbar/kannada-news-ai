from datetime import datetime, timezone
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from app.models import (
    Article,
    SearchHistory,
    ReadingHistory,
    Bookmark,
    Category,
    ArticleCategory,
    Feedback,
    PipelineJob,
)
from app.schemas.schemas import (
    ArticleListItem,
    SearchItemResponse,
    ReadingItemResponse,
    DashboardStats,
)

class SearchAndHistoryService:
    @staticmethod
    def search_articles(
        db: Session,
        query_text: str,
        session_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
    ) -> Tuple[List[ArticleListItem], int]:
        clean_q = query_text.strip()
        if not clean_q:
            return [], 0

        # Record search query in history if session provided
        if session_id:
            db.add(SearchHistory(session_id=session_id, query=clean_q))
            db.commit()

        pattern = f"%{clean_q}%"
        # Search over Kannada text and English translations
        base_query = db.query(Article).filter(
            (Article.title_kn.ilike(pattern)) |
            (Article.body_kn.ilike(pattern)) |
            (Article.translations.any(func.lower(Article.translations.property.mapper.class_.title_en).like(func.lower(pattern))))
        )
        total = base_query.count()
        articles = base_query.order_by(desc(Article.published_at), desc(Article.id))\
                             .offset((page - 1) * page_size)\
                             .limit(page_size)\
                             .all()

        items = []
        for a in articles:
            active_trans = next((t for t in a.translations if t.is_active), None)
            active_sum = a.summaries[0] if a.summaries else None
            items.append(
                ArticleListItem(
                    id=a.id,
                    origin=a.origin,
                    url=a.url,
                    title_kn=a.title_kn,
                    title_en=active_trans.title_en if active_trans else None,
                    two_line_summary=active_sum.summary_en if active_sum else None,
                    section_label=a.section_label,
                    published_at=a.published_at,
                    status=a.status,
                    source_name=a.source.name if a.source else "Direct / User",
                    has_flags=a.status == "needs_review",
                )
            )
        return items, total

    @staticmethod
    def record_reading(db: Session, session_id: str, article_id: int):
        rec = ReadingHistory(session_id=session_id, article_id=article_id)
        db.add(rec)
        db.commit()

    @staticmethod
    def get_search_history(db: Session, session_id: str, limit: int = 10) -> List[SearchItemResponse]:
        items = db.query(SearchHistory).filter(SearchHistory.session_id == session_id)\
                  .order_by(desc(SearchHistory.created_at)).limit(limit).all()
        return [SearchItemResponse.model_validate(i) for i in items]

    @staticmethod
    def get_reading_history(db: Session, session_id: str, limit: int = 10) -> List[ReadingItemResponse]:
        items = db.query(ReadingHistory).filter(ReadingHistory.session_id == session_id)\
                  .order_by(desc(ReadingHistory.opened_at)).limit(limit).all()
        results = []
        for r in items:
            active_trans = next((t for t in r.article.translations if t.is_active), None) if r.article else None
            results.append(
                ReadingItemResponse(
                    id=r.id,
                    article_id=r.article_id,
                    article_title_kn=r.article.title_kn if r.article else None,
                    article_title_en=active_trans.title_en if active_trans else None,
                    opened_at=r.opened_at,
                )
            )
        return results

    @staticmethod
    def clear_history(db: Session, session_id: str):
        db.query(SearchHistory).filter(SearchHistory.session_id == session_id).delete()
        db.query(ReadingHistory).filter(ReadingHistory.session_id == session_id).delete()
        db.commit()

    @staticmethod
    def add_bookmark(db: Session, session_id: str, article_id: int) -> bool:
        exists = db.query(Bookmark).filter_by(session_id=session_id, article_id=article_id).first()
        if not exists:
            db.add(Bookmark(session_id=session_id, article_id=article_id))
            db.commit()
        return True

    @staticmethod
    def remove_bookmark(db: Session, session_id: str, article_id: int) -> bool:
        db.query(Bookmark).filter_by(session_id=session_id, article_id=article_id).delete()
        db.commit()
        return True

    @staticmethod
    def get_bookmarks(db: Session, session_id: str) -> List[ArticleListItem]:
        bookmarks = db.query(Bookmark).filter_by(session_id=session_id).order_by(desc(Bookmark.created_at)).all()
        items = []
        for b in bookmarks:
            a = b.article
            if a:
                active_trans = next((t for t in a.translations if t.is_active), None)
                active_sum = a.summaries[0] if a.summaries else None
                items.append(
                    ArticleListItem(
                        id=a.id,
                        origin=a.origin,
                        url=a.url,
                        title_kn=a.title_kn,
                        title_en=active_trans.title_en if active_trans else None,
                        two_line_summary=active_sum.summary_en if active_sum else None,
                        section_label=a.section_label,
                        published_at=a.published_at,
                        status=a.status,
                        source_name=a.source.name if a.source else "Direct / User",
                    )
                )
        return items

    @staticmethod
    def get_stats(db: Session) -> DashboardStats:
        total_articles = db.query(Article).count()
        ready_articles = db.query(Article).filter(Article.status == "ready").count()
        flagged_count = db.query(Article).filter(Article.status == "needs_review").count()

        # Categories breakdown
        categories = db.query(Category).all()
        cat_counts = {}
        for c in categories:
            count = db.query(Article).filter(
                (Article.section_label == c.slug) |
                (Article.categories.any(ArticleCategory.category_id == c.id))
            ).count()
            cat_counts[c.slug] = count

        in_queue = db.query(PipelineJob).filter(PipelineJob.state.in_(["queued", "running"])).count()
        pass_rate = 100.0
        if total_articles > 0:
            pass_rate = round(float((ready_articles / total_articles) * 100), 1)

        return DashboardStats(
            articles_today=total_articles,
            translated_count=ready_articles,
            flagged_for_review=flagged_count,
            average_latency_sec=2.4,
            items_in_queue=in_queue,
            verification_pass_rate=pass_rate,
            categories_distribution=cat_counts,
        )
