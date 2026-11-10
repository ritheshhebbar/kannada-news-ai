import hashlib
import unicodedata
from datetime import datetime, timezone
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.models import (
    Article,
    Sentence,
    Translation,
    SentenceTranslation,
    Summary,
    Entity,
    Category,
    ArticleCategory,
    PipelineJob,
    Source,
)
from app.schemas.schemas import (
    ArticleListItem,
    ArticleDetailResponse,
    SentenceResponse,
    SentenceTranslationResponse,
    TranslationResponse,
    SummaryResponse,
    EntityResponse,
    CategoryResponse,
    ArticleSubmitRequest,
    ArticleSubmitResponse,
    ArticleStatusResponse,
)

def is_predominantly_kannada(text: str, min_ratio: float = 0.4) -> Tuple[bool, float]:
    """Check whether text consists primarily of Kannada Unicode characters."""
    total_alpha = 0
    kannada_chars = 0
    for char in text:
        if char.isalpha():
            total_alpha += 1
            if '\u0C80' <= char <= '\u0CFF':
                kannada_chars += 1
    if total_alpha == 0:
        return False, 0.0
    ratio = kannada_chars / total_alpha
    return ratio >= min_ratio, ratio

class ArticleService:
    @staticmethod
    def list_articles(
        db: Session,
        source_id: Optional[int] = None,
        category_slug: Optional[str] = None,
        status: Optional[str] = None,
        search_query: Optional[str] = None,
        page: int = 1,
        page_size: int = 10,
    ) -> Tuple[List[ArticleListItem], int]:
        query = db.query(Article)

        if source_id:
            query = query.filter(Article.source_id == source_id)
        if status:
            query = query.filter(Article.status == status)
        if category_slug:
            query = query.join(ArticleCategory).join(Category).filter(Category.slug == category_slug)
        if search_query:
            pattern = f"%{search_query.strip()}%"
            query = query.filter(
                (Article.title_kn.ilike(pattern)) |
                (Article.body_kn.ilike(pattern))
            )

        total = query.count()
        articles = query.order_by(desc(Article.published_at), desc(Article.id))\
                        .offset((page - 1) * page_size)\
                        .limit(page_size)\
                        .all()

        items = []
        for a in articles:
            # Active translation headline
            active_trans = next((t for t in a.translations if t.is_active), None)
            active_sum = a.summaries[0] if a.summaries else None

            # Check if any sentence has flags
            has_flags = False
            if active_trans:
                for st in active_trans.sentence_translations:
                    if st.flags and len(st.flags) > 0:
                        has_flags = True
                        break

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
                    has_flags=has_flags or a.status == "needs_review",
                )
            )

        return items, total

    @staticmethod
    def get_article_detail(db: Session, article_id: int) -> Optional[ArticleDetailResponse]:
        article = db.query(Article).filter(Article.id == article_id).first()
        if not article:
            return None

        # Build sentence responses with translation alignment
        active_trans = next((t for t in article.translations if t.is_active), None)
        trans_map = {}
        flags_collected = []
        if active_trans:
            for st in active_trans.sentence_translations:
                trans_map[st.sentence_id] = st
                if st.flags:
                    for f in st.flags:
                        flags_collected.append({
                            "sentence_idx": st.sentence.idx if st.sentence else 0,
                            "type": f.get("type", "flag"),
                            "detail": f.get("detail", ""),
                        })

        sentence_list = []
        for s in article.sentences:
            st = trans_map.get(s.id)
            st_resp = None
            if st:
                st_resp = SentenceTranslationResponse(
                    translation_id=st.translation_id,
                    sentence_id=st.sentence_id,
                    text_en=st.text_en,
                    labse_sim=st.labse_sim,
                    qe_score=st.qe_score,
                    flags=st.flags or [],
                )
            sentence_list.append(
                SentenceResponse(
                    id=s.id,
                    idx=s.idx,
                    paragraph_idx=s.paragraph_idx,
                    text_kn=s.text_kn,
                    translation=st_resp,
                )
            )

        active_sum = article.summaries[0] if article.summaries else None
        active_trans_resp = None
        if active_trans:
            active_trans_resp = TranslationResponse(
                id=active_trans.id,
                article_id=active_trans.article_id,
                backend=active_trans.backend,
                model_version=active_trans.model_version,
                title_en=active_trans.title_en,
                guard_report=active_trans.guard_report,
                is_active=active_trans.is_active,
                created_at=active_trans.created_at,
                sentences=[
                    SentenceTranslationResponse(
                        translation_id=st.translation_id,
                        sentence_id=st.sentence_id,
                        text_en=st.text_en,
                        labse_sim=st.labse_sim,
                        qe_score=st.qe_score,
                        flags=st.flags or [],
                    )
                    for st in active_trans.sentence_translations
                ]
            )

        summary_resp = None
        if active_sum:
            summary_resp = SummaryResponse(
                id=active_sum.id,
                article_id=active_sum.article_id,
                translation_id=active_sum.translation_id,
                model=active_sum.model,
                prompt_version=active_sum.prompt_version,
                method=active_sum.method,
                headline_en=active_sum.headline_en,
                summary_en=active_sum.summary_en,
                key_points=active_sum.key_points,
                key_facts=active_sum.key_facts,
                verification=active_sum.verification,
                created_at=active_sum.created_at,
            )

        entities_resp = [
            EntityResponse(
                id=e.id,
                lang=e.lang,
                text=e.text,
                norm_text=e.norm_text,
                type=e.type,
                sentence_idx=e.sentence_idx,
            )
            for e in article.entities
        ]

        categories_resp = [
            CategoryResponse(
                id=ac.category.id,
                slug=ac.category.slug,
                name_en=ac.category.name_en,
                name_kn=ac.category.name_kn,
            )
            for ac in article.categories if ac.category
        ]

        return ArticleDetailResponse(
            id=article.id,
            source_id=article.source_id,
            source_name=article.source.name if article.source else "Direct User Submission",
            origin=article.origin,
            url=article.url,
            title_kn=article.title_kn,
            title_en=active_trans.title_en if active_trans else None,
            body_kn=article.body_kn,
            section_label=article.section_label,
            published_at=article.published_at,
            status=article.status,
            session_id=article.session_id,
            sentences=sentence_list,
            active_translation=active_trans_resp,
            active_summary=summary_resp,
            entities=entities_resp,
            categories=categories_resp,
            flags=flags_collected,
        )

    @staticmethod
    def submit_article(db: Session, req: ArticleSubmitRequest) -> ArticleSubmitResponse:
        content = (req.text or "").strip()
        if not content:
            raise ValueError("Article text cannot be empty.")

        # Script check
        valid_script, ratio = is_predominantly_kannada(content)
        if not valid_script and not req.url:
            raise ValueError(f"Submitted text does not appear to be Kannada (Kannada character ratio: {ratio:.1%}). Please input Kannada script.")

        # Normalized Unicode NFC
        clean_body = unicodedata.normalize("NFC", content)
        content_hash = hashlib.sha256(clean_body.encode("utf-8")).hexdigest()

        # Deduplication check
        existing = db.query(Article).filter(Article.content_hash == content_hash).first()
        if existing:
            return ArticleSubmitResponse(
                article_id=existing.id,
                job_id=None,
                status=existing.status,
                message="Article already submitted. Showing existing entry.",
            )

        title = req.title.strip() if req.title else clean_body.split("\n")[0][:120]

        article = Article(
            source_id=None,
            origin="user",
            url=req.url,
            title_kn=title,
            body_kn=clean_body,
            content_hash=content_hash,
            section_label=req.section_label or "general",
            published_at=datetime.now(timezone.utc),
            status="new",
            session_id=req.session_id,
        )
        db.add(article)
        db.flush()

        # Enqueue initial processing job
        job = PipelineJob(
            article_id=article.id,
            stage="preprocess",
            state="queued",
            attempts=0,
        )
        db.add(job)
        db.commit()

        return ArticleSubmitResponse(
            article_id=article.id,
            job_id=job.id,
            status="queued",
            message="Article submitted and queued for translation and summarization.",
        )

    @staticmethod
    def get_article_status(db: Session, article_id: int) -> Optional[ArticleStatusResponse]:
        article = db.query(Article).filter(Article.id == article_id).first()
        if not article:
            return None

        # Determine current stage and estimated progress percentage
        progress_map = {
            "new": 10,
            "extracted": 25,
            "translating": 50,
            "translated": 65,
            "summarizing": 80,
            "verified": 95,
            "ready": 100,
            "needs_review": 100,
            "failed": 0,
        }

        latest_job = db.query(PipelineJob).filter(PipelineJob.article_id == article_id)\
                       .order_by(desc(PipelineJob.id)).first()

        current_stage = latest_job.stage if latest_job else article.status
        progress = progress_map.get(article.status, 20)

        return ArticleStatusResponse(
            article_id=article.id,
            status=article.status,
            current_stage=current_stage,
            progress=progress,
            last_error=latest_job.last_error if latest_job else None,
        )

    @staticmethod
    def retry_article_stage(db: Session, article_id: int) -> bool:
        article = db.query(Article).filter(Article.id == article_id).first()
        if not article:
            return False

        article.status = "new"
        job = PipelineJob(
            article_id=article.id,
            stage="preprocess",
            state="queued",
            attempts=0,
            last_error=None,
        )
        db.add(job)
        db.commit()
        return True
