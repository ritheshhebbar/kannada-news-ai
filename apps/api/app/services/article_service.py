import hashlib
import unicodedata
from datetime import datetime, timezone
from typing import List, Optional, Tuple, Dict, Any
from urllib.parse import urlparse
import httpx
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

# Permitted domains for URL ingestion as per Section 7.1
PERMITTED_DOMAINS = [
    "prajavani.net",
    "kannadaprabha.com",
    "vijaykarnataka.com",
    "udayavani.com",
    "vijayavani.net",
    "samyukthakarnataka.com",
    "pib.gov.in",
    "localhost",
    "127.0.0.1",
]

def is_predominantly_kannada(text: str, min_ratio: float = 0.35) -> Tuple[bool, float]:
    """Check whether text consists primarily of Kannada Unicode characters.
    
    Includes Kannada consonants, independent vowels, dependent vowel signs (matras),
    viramas, anusvara, visarga, and Kannada numerals (U+0C80 - U+0CFF).
    """
    kannada_chars = 0
    non_kannada_letters = 0
    for char in text:
        code = ord(char)
        if 0x0C80 <= code <= 0x0CFF:
            kannada_chars += 1
        elif char.isalpha():
            non_kannada_letters += 1

    total = kannada_chars + non_kannada_letters
    if total == 0:
        return False, 0.0
    ratio = kannada_chars / total
    return ratio >= min_ratio, ratio

def extract_text_from_url(url: str) -> Tuple[str, str]:
    """Extract article title and clean Kannada text from a permitted news URL."""
    domain = urlparse(url).netloc.lower()
    # Strip port or subdomains for check
    clean_domain = domain.split(":")[0]
    is_permitted = any(clean_domain.endswith(p) for p in PERMITTED_DOMAINS)
    if not is_permitted:
        raise ValueError(
            f"Domain '{clean_domain}' is not on the permitted news outlets list. "
            f"Allowed outlets: {', '.join(PERMITTED_DOMAINS[:6])}"
        )

    try:
        import trafilatura
        headers = {
            "User-Agent": "KannadaNewsAI-ResearchBot/1.0 (+academic-research; https://github.com/)"
        }
        downloaded = trafilatura.fetch_url(url, no_ssl=False)
        if not downloaded:
            # Fallback with httpx
            with httpx.Client(timeout=10.0, headers=headers, follow_redirects=True) as client:
                resp = client.get(url)
                resp.raise_for_status()
                downloaded = resp.text

        extracted = trafilatura.extract(
            downloaded,
            include_comments=False,
            include_tables=False,
            favor_precision=True
        )
        metadata = trafilatura.extract_metadata(downloaded)
        title = metadata.title if (metadata and metadata.title) else ""

        if not extracted or len(extracted.strip()) < 50:
            raise ValueError("Could not extract substantial article body text from the provided URL.")

        return title.strip(), extracted.strip()
    except Exception as e:
        if isinstance(e, ValueError):
            raise e
        raise ValueError(f"Failed to fetch or extract content from URL: {str(e)}")

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
            query = query.filter(
                (Article.section_label == category_slug) |
                (Article.categories.any(
                    ArticleCategory.category.has(Category.slug == category_slug)
                ))
            )
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
            active_trans = next((t for t in a.translations if t.is_active), None)
            active_sum = a.summaries[0] if a.summaries else None

            # Check if any sentence has quality flags
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
        title = (req.title or "").strip()
        extracted_from_url = False

        if not content and req.url:
            url_title, content = extract_text_from_url(req.url.strip())
            if not title:
                title = url_title
            extracted_from_url = True

        if not content:
            raise ValueError("Either Kannada article text or a permitted news URL must be provided.")

        # Script check
        valid_script, ratio = is_predominantly_kannada(content)
        if not valid_script:
            raise ValueError(
                f"Submitted content does not appear to be Kannada (Kannada character ratio: {ratio:.1%}). "
                f"Please ensure text is in Kannada script."
            )

        # Unicode NFC Normalization
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

        if not title:
            first_line = clean_body.split("\n")[0].strip()
            title = first_line[:120] if first_line else "ಕನ್ನಡ ವಾರ್ತೆ"

        article = Article(
            source_id=None,
            origin="rss" if extracted_from_url else "user",
            url=req.url.strip() if req.url else None,
            title_kn=title,
            body_kn=clean_body,
            content_hash=content_hash,
            section_label=req.section_label or "karnataka",
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
