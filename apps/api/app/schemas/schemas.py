from datetime import datetime
from typing import List, Optional, Any, Dict, Union
from pydantic import BaseModel, Field, ConfigDict

# --- Reference Schemas ---

class SourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    base_url: str
    feed_url: Optional[str] = None
    robots_checked: bool
    terms_note: Optional[str] = None
    active: bool


class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    name_en: str
    name_kn: str


# --- Sentence & Translation Schemas ---

class FlagItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    type: str  # 'number_mismatch', 'low_similarity', 'entity_mismatch', etc.
    detail: str
    severity: Optional[str] = "warning"


class SentenceTranslationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    translation_id: int
    sentence_id: int
    text_en: str
    labse_sim: Optional[float] = None
    qe_score: Optional[float] = None
    flags: List[Any] = Field(default_factory=list)


class SentenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    idx: int
    paragraph_idx: int
    text_kn: str
    translation: Optional[SentenceTranslationResponse] = None


class TranslationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    article_id: int
    backend: str
    model_version: str
    title_en: Optional[str] = None
    guard_report: Optional[Dict[str, Any]] = None
    is_active: bool
    created_at: Optional[datetime] = None
    sentences: List[SentenceTranslationResponse] = Field(default_factory=list)


# --- Summary & Verification Schemas ---

class KeyPointItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    text: str
    evidence: List[int] = Field(default_factory=list)


class KeyFacts(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    who: List[str] = Field(default_factory=list)
    what: List[str] = Field(default_factory=list)
    where: List[str] = Field(default_factory=list)
    when: List[str] = Field(default_factory=list)
    numbers: List[str] = Field(default_factory=list)


class SummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    article_id: int
    translation_id: Optional[int] = None
    model: str
    prompt_version: str
    method: str
    headline_en: Optional[str] = None
    summary_en: Optional[str] = None
    key_points: Optional[List[Union[KeyPointItem, Dict[str, Any]]]] = None
    key_facts: Optional[Union[KeyFacts, Dict[str, Any]]] = None
    verification: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None


# --- Entity Schema ---

class EntityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    lang: str
    text: str
    norm_text: Optional[str] = None
    type: str
    sentence_idx: Optional[int] = None


# --- Article Schemas ---

class ArticleListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    origin: str
    url: Optional[str] = None
    title_kn: Optional[str] = None
    title_en: Optional[str] = None
    two_line_summary: Optional[str] = None
    section_label: Optional[str] = None
    published_at: Optional[datetime] = None
    status: str
    source_name: Optional[str] = None
    has_flags: bool = False


class ArticleDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source_id: Optional[int] = None
    source_name: Optional[str] = None
    origin: str
    url: Optional[str] = None
    title_kn: Optional[str] = None
    title_en: Optional[str] = None
    body_kn: str
    section_label: Optional[str] = None
    published_at: Optional[datetime] = None
    status: str
    session_id: Optional[str] = None
    
    sentences: List[SentenceResponse] = Field(default_factory=list)
    active_translation: Optional[TranslationResponse] = None
    active_summary: Optional[SummaryResponse] = None
    entities: List[EntityResponse] = Field(default_factory=list)
    categories: List[CategoryResponse] = Field(default_factory=list)
    flags: List[Dict[str, Any]] = Field(default_factory=list)


class ArticleSubmitRequest(BaseModel):
    text: Optional[str] = None
    url: Optional[str] = None
    title: Optional[str] = None
    section_label: Optional[str] = "general"
    session_id: Optional[str] = None


class ArticleSubmitResponse(BaseModel):
    article_id: int
    job_id: Optional[int] = None
    status: str
    message: str


class ArticleStatusResponse(BaseModel):
    article_id: int
    status: str
    current_stage: Optional[str] = None
    progress: int
    last_error: Optional[str] = None


# --- Feedback & History Schemas ---

class FeedbackCreate(BaseModel):
    article_id: int
    sentence_id: Optional[int] = None
    kind: str
    comment: Optional[str] = None


class FeedbackResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    article_id: int
    sentence_id: Optional[int] = None
    kind: Optional[str] = None
    comment: Optional[str] = None
    created_at: Optional[datetime] = None


class BookmarkCreate(BaseModel):
    article_id: int
    session_id: str


class SearchItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    query: str
    created_at: Optional[datetime] = None


class ReadingItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    article_id: int
    article_title_kn: Optional[str] = None
    article_title_en: Optional[str] = None
    opened_at: Optional[datetime] = None


# --- Stats & Dashboard Schemas ---

class DashboardStats(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    articles_today: int
    translated_count: int
    flagged_for_review: int
    average_latency_sec: float
    items_in_queue: int
    verification_pass_rate: float
    categories_distribution: Dict[str, int]


# --- Grounded Q&A Schemas ---

class ArticleAskRequest(BaseModel):
    question: str
    session_id: Optional[str] = None


class ArticleAskResponse(BaseModel):
    article_id: int
    question: str
    answer: str
    cited_sentences: List[int] = []
    grounded: bool = True

